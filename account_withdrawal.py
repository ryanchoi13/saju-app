"""Member withdrawal: 7-day grace period, then full deletion of the account's data.

Policy (see project doc decisions-2026-11-16-account-withdrawal):
- A withdrawal request only marks the account; logging in again and cancelling restores it.
- After GRACE_SECONDS every per-account row is deleted from all stores.
- A one-way hash of the account id is kept REJOIN_LIMIT_SECONDS so that deleting and
  re-creating an account cannot be used to collect the welcome coins again.
- There is no real payment record to retain yet (charging is test-only). When real
  payments exist, keep a separate, access-restricted ledger for 5 years (e-commerce act).
"""
import hashlib
import logging
import threading
import time

from account_store import owner_key
from wardrobe_store import StorageUnavailable, _connection, _execute

GRACE_SECONDS = 7 * 24 * 60 * 60
REJOIN_LIMIT_SECONDS = 30 * 24 * 60 * 60
_LOG = logging.getLogger(__name__)
_SWEEP_LOCK = threading.Lock()


def initialize():
    with _connection() as (conn, pg):
        _execute(conn, pg, '''CREATE TABLE IF NOT EXISTS account_withdrawals (
            owner_key VARCHAR(64) PRIMARY KEY, user_id VARCHAR(55) NOT NULL,
            requested_at BIGINT NOT NULL)''')
        _execute(conn, pg, '''CREATE TABLE IF NOT EXISTS withdrawn_accounts (
            owner_key VARCHAR(64) PRIMARY KEY, withdrawn_at BIGINT NOT NULL)''')


def _state(requested_at):
    return {'requested_at': int(requested_at), 'delete_at': int(requested_at) + GRACE_SECONDS}


def request(user_id, now=None):
    """Mark the account for deletion. Repeating the request keeps the first date."""
    initialize()
    now = int(now if now is not None else time.time())
    key = owner_key(user_id)
    with _connection() as (conn, pg):
        _execute(conn, pg, '''INSERT INTO account_withdrawals(owner_key,user_id,requested_at)
            VALUES(%s,%s,%s) ON CONFLICT(owner_key) DO NOTHING''', (key, user_id, now))
        row = _execute(conn, pg, 'SELECT requested_at FROM account_withdrawals WHERE owner_key=%s',
                       (key,)).fetchone()
    return _state(row[0])


def pending(user_id):
    initialize()
    with _connection() as (conn, pg):
        row = _execute(conn, pg, 'SELECT requested_at FROM account_withdrawals WHERE owner_key=%s',
                       (owner_key(user_id),)).fetchone()
    return _state(row[0]) if row else None


def cancel(user_id):
    initialize()
    with _connection() as (conn, pg):
        cur = _execute(conn, pg, 'DELETE FROM account_withdrawals WHERE owner_key=%s', (owner_key(user_id),))
        return cur.rowcount > 0


def recently_withdrawn(conn, pg, key, now=None):
    """True when this account was deleted within REJOIN_LIMIT_SECONDS (no welcome coins)."""
    now = int(now if now is not None else time.time())
    row = _execute(conn, pg, 'SELECT withdrawn_at FROM withdrawn_accounts WHERE owner_key=%s',
                   (key,)).fetchone()
    return bool(row and now - row[0] < REJOIN_LIMIT_SECONDS)


def _ensure_stores():
    import menu_store, meal_set_store, tarot_store, session_store, wallet_store, account_store
    from fashion_v2.outfit_day_store import production_store
    for module in (account_store, wallet_store, session_store, menu_store, meal_set_store, tarot_store):
        module.initialize()
    production_store.initialize()


def purge_account(user_id, now=None):
    """Delete every row of one account. Returns False if the request was cancelled meanwhile."""
    _ensure_stores()
    initialize()
    now = int(now if now is not None else time.time())
    key = owner_key(user_id)
    with _connection() as (conn, pg):
        # Claim the request first: a concurrent cancel or a second sweep leaves rowcount 0.
        claimed = _execute(conn, pg, 'DELETE FROM account_withdrawals WHERE owner_key=%s AND requested_at<=%s',
                           (key, now - GRACE_SECONDS))
        if claimed.rowcount == 0:
            return False
        for table in ('account_profiles', 'account_assets', 'menu_recommendation_days',
                      'meal_set_days_v2', 'tarot_days', 'outfit_days_v1'):
            _execute(conn, pg, f'DELETE FROM {table} WHERE owner_key=%s', (key,))
        _execute(conn, pg, 'DELETE FROM account_sessions WHERE user_id=%s', (user_id,))
        kakao_id = user_id[5:]
        _execute(conn, pg, 'DELETE FROM wardrobe_items WHERE user_id IN (SELECT id FROM users WHERE kakao_id=%s)',
                 (kakao_id,))
        _execute(conn, pg, 'DELETE FROM users WHERE kakao_id=%s', (kakao_id,))
        _execute(conn, pg, '''INSERT INTO withdrawn_accounts(owner_key,withdrawn_at) VALUES(%s,%s)
            ON CONFLICT(owner_key) DO UPDATE SET withdrawn_at=excluded.withdrawn_at''', (key, now))
    _purge_meal_feedback(user_id)
    return True


def _purge_meal_feedback(user_id):
    """Feedback lives in the menu-history SQLite file, keyed by sha256(account id)."""
    try:
        from app.engine.services import meal_feedback
        with meal_feedback.meal_history._LOCK:
            db = meal_feedback._db()
            db.execute('DELETE FROM meal_plan_feedback WHERE owner=?',
                       (hashlib.sha256(user_id.encode()).hexdigest(),))
            db.commit()
    except Exception as exc:  # best effort: the row holds no profile data, only plan tokens
        _LOG.warning('meal feedback cleanup skipped (%s)', type(exc).__name__)


def purge_due(now=None):
    """Delete every account whose grace period is over. Returns the accounts deleted."""
    if not _SWEEP_LOCK.acquire(blocking=False):
        return []
    try:
        initialize()
        now = int(now if now is not None else time.time())
        with _connection() as (conn, pg):
            due = [r[0] for r in _execute(conn, pg,
                   'SELECT user_id FROM account_withdrawals WHERE requested_at<=%s',
                   (now - GRACE_SECONDS,)).fetchall()]
            _execute(conn, pg, 'DELETE FROM withdrawn_accounts WHERE withdrawn_at<%s',
                     (now - REJOIN_LIMIT_SECONDS,))
        done = []
        for user_id in due:
            try:
                if purge_account(user_id, now):
                    done.append(user_id)
            except Exception as exc:  # keep the request so the next sweep retries
                _LOG.warning('withdrawal purge failed (%s)', type(exc).__name__)
        return done
    finally:
        _SWEEP_LOCK.release()


def start_sweeper(on_purged=None, interval=3600):
    """Hourly background sweep; the process is single-instance on Render."""
    def loop():
        while True:
            try:
                for user_id in purge_due():
                    if on_purged:
                        on_purged(user_id)
            except Exception as exc:
                _LOG.warning('withdrawal sweep failed (%s)', type(exc).__name__)
            time.sleep(interval)
    threading.Thread(target=loop, name='withdrawal-sweeper', daemon=True).start()
