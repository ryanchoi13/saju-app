"""Account/day menu snapshots in the same durable Postgres as the wardrobe.

One row per account and KST date freezes the ranking through reloads/deploys.
Locks plus compare-and-advance counters make duplicate requests idempotent.
SQLite is only the existing local-development adapter, never a Render fallback.
"""
import hashlib
import json
import secrets
from threading import Lock
from datetime import datetime, timedelta, timezone
from wardrobe_store import _connection, _execute, _owner, StorageUnavailable

LIMITS = {'general': 10, 'diet': 5}
_SCHEMA_LOCK = Lock()
_READY = False


def today():
    return datetime.now(timezone(timedelta(hours=9))).date()


def _key(user_id):
    return hashlib.sha256(_owner(user_id).encode()).hexdigest()


def initialize():
    global _READY
    with _SCHEMA_LOCK, _connection() as (conn, pg):
        if pg:
            _execute(conn, pg, 'SELECT pg_advisory_xact_lock(74201931)')
        _execute(conn, pg, '''CREATE TABLE IF NOT EXISTS menu_recommendation_days (
            owner_key VARCHAR(64) NOT NULL, day VARCHAR(10) NOT NULL,
            token VARCHAR(64) NOT NULL UNIQUE, payload TEXT NOT NULL,
            general_seen INTEGER NOT NULL DEFAULT 0 CHECK (general_seen BETWEEN 0 AND 10),
            diet_seen INTEGER NOT NULL DEFAULT 0 CHECK (diet_seen BETWEEN 0 AND 5),
            mode VARCHAR(10) NOT NULL CHECK (mode IN ('general', 'diet')),
            PRIMARY KEY (owner_key, day))''')
    _READY = True


def _row(conn, pg, owner, day, lock=False):
    return _execute(conn, pg, '''SELECT token,payload,general_seen,diet_seen,mode
        FROM menu_recommendation_days WHERE owner_key=%s AND day=%s'''
        + (' FOR UPDATE' if pg and lock else ''), (owner, str(day))).fetchone()


def _limit(payload, mode):
    return min(LIMITS[mode], len(payload['rankings'][mode]) // 2)


def _view(row, day, display_set=1):
    token, raw, general_seen, diet_seen, mode = row
    payload = json.loads(raw)
    seen = {'general': general_seen, 'diet': diet_seen}
    count, limit = seen[mode], _limit(payload, mode)
    index = min(max(1, display_set), max(1, count))
    history = payload['rankings'][mode][:count*2]
    return dict(date=str(day), token=token, mode=mode,
                seen_sets=count, set_limit=limit, mode_counts=seen,
                exhausted=count >= limit, display_set=index,
                items=history[(index-1)*2:index*2], history=history,
                basis=payload['basis'], basis_text=payload['basis_text'])


def _create(conn, pg, owner, day, build):
    row = _row(conn, pg, owner, day, lock=True)
    if row:
        return row
    previous = _execute(conn, pg, '''SELECT mode FROM menu_recommendation_days
        WHERE owner_key=%s AND day<%s ORDER BY day DESC LIMIT 1''', (owner, str(day))).fetchone()
    mode = previous[0] if previous else 'general'
    payload = build()
    counts = {m: int(m == mode and _limit(payload, m) > 0) for m in LIMITS}
    _execute(conn, pg, '''INSERT INTO menu_recommendation_days
        (owner_key,day,token,payload,general_seen,diet_seen,mode)
        VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (owner_key,day) DO NOTHING''',
        (owner, str(day), secrets.token_hex(32), json.dumps(payload, ensure_ascii=False),
         counts['general'], counts['diet'], mode))
    return _row(conn, pg, owner, day, lock=True)


def load(user_id, day, build):
    owner = _key(user_id)
    if not _READY:
        initialize()
    with _connection() as (conn, pg):
        if not pg:
            conn.execute('BEGIN IMMEDIATE')
        return _view(_create(conn, pg, owner, day, build), day)


def explore(user_id, day, build, *, token, mode, action, expected_day, expected_seen):
    if mode not in LIMITS or action not in {'open', 'next'}:
        raise ValueError('올바른 메뉴 선택이 아닙니다.')
    owner = _key(user_id)
    if not _READY:
        initialize()
    with _connection() as (conn, pg):
        if not pg:
            conn.execute('BEGIN IMMEDIATE')
        authorized = _execute(conn, pg, '''SELECT day FROM menu_recommendation_days
            WHERE owner_key=%s AND token=%s''', (owner, token)).fetchone()
        if not authorized:
            raise KeyError('menu session')
        # A stale request opens today's first set; it never spends today's next set.
        rollover = expected_day != str(day)
        row = _create(conn, pg, owner, day, build)
        payload = json.loads(row[1])
        counts = {'general': row[2], 'diet': row[3]}
        if rollover:
            mode = row[4]
        limit = _limit(payload, mode)
        count = counts[mode]
        if count == 0 and limit:
            count = 1
        elif action == 'next' and not rollover:
            if expected_seen > count:
                raise ValueError('추천 기록을 다시 불러와 주세요.')
            if expected_seen == count and count < limit:
                count += 1
        counts[mode] = count
        _execute(conn, pg, '''UPDATE menu_recommendation_days
            SET general_seen=%s,diet_seen=%s,mode=%s WHERE owner_key=%s AND day=%s''',
            (counts['general'], counts['diet'], mode, owner, str(day)))
        row = (row[0], row[1], counts['general'], counts['diet'], mode)
        return _view(row, day, count if action == 'next' and not rollover else 1)


def health():
    with _connection() as (conn, pg):
        _execute(conn, pg, 'SELECT owner_key,day,general_seen,diet_seen FROM menu_recommendation_days LIMIT 0')
        return 'postgresql' if pg else 'local_sqlite'
