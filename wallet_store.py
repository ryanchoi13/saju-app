"""Authoritative wallet and report archive; account row is locked for every write."""
from contextlib import contextmanager
import json
import account_withdrawal
from account_store import owner_key
from wardrobe_store import _connection, _execute, StorageUnavailable

def initialize():
    with _connection() as (conn, pg):
        _execute(conn, pg, '''CREATE TABLE IF NOT EXISTS account_assets (
            owner_key VARCHAR(64) PRIMARY KEY, balance INTEGER NOT NULL CHECK(balance>=0),
            reports TEXT NOT NULL DEFAULT '[]')''')
    account_withdrawal.initialize()

@contextmanager
def locked(user_id, *, initial_balance=1000, initial_reports=None):
    initialize()
    with _connection() as (conn, pg):
        if not pg:
            conn.execute('BEGIN IMMEDIATE')
        key = owner_key(user_id)
        if account_withdrawal.recently_withdrawn(conn, pg, key):
            initial_balance, initial_reports = 0, []  # a deleted account gets no welcome coins back
        _execute(conn, pg, '''INSERT INTO account_assets(owner_key,balance,reports) VALUES(%s,%s,%s)
            ON CONFLICT(owner_key) DO NOTHING''',
            (key, max(0, int(initial_balance)), json.dumps(initial_reports or [], ensure_ascii=False)))
        row = _execute(conn, pg, 'SELECT balance,reports FROM account_assets WHERE owner_key=%s' +
                       (' FOR UPDATE' if pg else ''), (key,)).fetchone()
        state = dict(balance=row[0], reports=json.loads(row[1]))
        yield conn, pg, state
        if state['balance'] < 0:
            raise ValueError('insufficient_coins')
        _execute(conn, pg, 'UPDATE account_assets SET balance=%s,reports=%s WHERE owner_key=%s',
                 (state['balance'], json.dumps(state['reports'], ensure_ascii=False), key))

def load(user_id, **seed):
    with locked(user_id, **seed) as (_, _, state):
        return state

def buy_report(user_id, key, cost, report):
    with locked(user_id) as (_, _, state):
        # Repeated delivery/clicks must never spend twice or lose the first report.
        # 궁합은 상대마다(partner_key), 나머지는 산 사주마다(saju_key) 종류당 하나.
        partner_key, saju_key = report.get('partner_key'), report.get('saju_key')
        if not any(r['report_key'] == key and (partner_key is None or r.get('partner_key') == partner_key)
                   and (saju_key is None or r.get('saju_key') == saju_key)
                   for r in state['reports']):
            if state['balance'] < cost:
                raise ValueError('insufficient_coins')
            state['balance'] -= cost
            state['reports'].append(report)
        return state


def stamp_reports(user_id, stamps):
    """옛 풀이에 '산 사주' 기록을 붙인다. 본문·버전·결제일·잔액은 건드리지 않는다."""
    with locked(user_id) as (_, _, state):
        for expected, fields in stamps:
            report = next((r for r in state['reports'] if r == expected), None)
            if report is not None and not report.get('saju_key'):
                report.update(fields)
        return state


def delete_report(user_id, key, index, expected_title):
    """보관함의 풀이 하나를 지운다(복채는 돌려주지 않는다).

    화면이 본 목록과 서버 목록이 어긋나면(다른 기기에서 먼저 지웠거나 새로 샀을 때) 엉뚱한 풀이를 지우지 않도록
    자리·종류·제목이 모두 맞을 때만 지운다.
    """
    with locked(user_id) as (_, _, state):
        reports = state['reports']
        if not 0 <= index < len(reports) or reports[index].get('report_key') != key \
                or reports[index].get('report_title') != expected_title:
            raise ValueError('report_changed')
        del reports[index]
        return state


def refresh_owned_annual(user_id, expected, replacement):
    return refresh_owned_report(user_id, 'sinnian', expected, replacement)


def refresh_owned_report(user_id, report_key, expected, replacement):
    """Replace an owned reading without debit; retain every previous original.

    Generation happens outside the wallet lock. Compare-and-swap prevents two
    requests (or another write) from discarding an intervening update.
    """
    from copy import deepcopy
    with locked(user_id) as (_, _, state):
        # 같은 종류를 사주마다 따로 가질 수 있으므로, 같은 사주(saju_key)의 풀이만 본다.
        mine = [r for r in state['reports'] if r['report_key'] == report_key
                and r.get('saju_key') == expected.get('saju_key')]
        if not mine:
            raise ValueError('not_owned')
        report = next((r for r in mine if r == expected), None)
        if report is None:
            if any(r.get('narrative_version') == replacement['narrative_version'] for r in mine):
                return state
            raise ValueError('report_changed')
        if report.get('narrative_version') == replacement['narrative_version']:
            return state
        history = report.setdefault('previous_versions', [])
        history.append(deepcopy({k:v for k,v in expected.items() if k != 'previous_versions'}))
        for field in ('report_title', 'report_content', 'narrative_version', 'report_year',
                      'refreshed_at', 'profile_basis', 'reading_context'):
            if field in replacement:
                report[field] = replacement[field]
        # Original purchase date, other reports, balance and receipts are intact.
        return state
