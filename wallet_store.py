"""Authoritative wallet and report archive; account row is locked for every write."""
from contextlib import contextmanager
import json
from account_store import owner_key
from wardrobe_store import _connection, _execute, StorageUnavailable

def initialize():
    with _connection() as (conn, pg):
        _execute(conn, pg, '''CREATE TABLE IF NOT EXISTS account_assets (
            owner_key VARCHAR(64) PRIMARY KEY, balance INTEGER NOT NULL CHECK(balance>=0),
            reports TEXT NOT NULL DEFAULT '[]')''')

@contextmanager
def locked(user_id, *, initial_balance=1000, initial_reports=None):
    initialize()
    with _connection() as (conn, pg):
        if not pg:
            conn.execute('BEGIN IMMEDIATE')
        key = owner_key(user_id)
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
        if not any(r['report_key'] == key for r in state['reports']):
            if state['balance'] < cost:
                raise ValueError('insufficient_coins')
            state['balance'] -= cost
            state['reports'].append(report)
        return state
