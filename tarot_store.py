"""Account/day draw receipts survive restart and serialize concurrent draws."""
from contextlib import contextmanager
import json
from account_store import owner_key
from wardrobe_store import _connection, _execute, StorageUnavailable


def initialize():
    with _connection() as (conn, pg):
        _execute(conn, pg, '''CREATE TABLE IF NOT EXISTS tarot_days (
            owner_key VARCHAR(64) NOT NULL, day VARCHAR(10) NOT NULL,
            receipts TEXT NOT NULL DEFAULT '{}', PRIMARY KEY(owner_key,day))''')


def read(user_id, day):
    initialize()
    with _connection() as (conn, pg):
        row = _execute(conn, pg, 'SELECT receipts FROM tarot_days WHERE owner_key=%s AND day=%s',
                       (owner_key(user_id),day)).fetchone()
        return json.loads(row[0]) if row else {}


@contextmanager
def locked(user_id, day, connection=None):
    if connection is not None:
        with _receipts(*connection, user_id, day) as receipts:
            yield receipts
        return
    initialize()
    with _connection() as (conn, pg):
        if not pg:
            conn.execute('BEGIN IMMEDIATE')
        with _receipts(conn, pg, user_id, day) as receipts:
            yield receipts


@contextmanager
def _receipts(conn, pg, user_id, day):
    key = owner_key(user_id)
    _execute(conn, pg, '''INSERT INTO tarot_days(owner_key,day) VALUES(%s,%s)
        ON CONFLICT(owner_key,day) DO NOTHING''', (key,day))
    row = _execute(conn, pg, 'SELECT receipts FROM tarot_days WHERE owner_key=%s AND day=%s'+
                   (' FOR UPDATE' if pg else ''), (key,day)).fetchone()
    receipts = json.loads(row[0])
    yield receipts
    _execute(conn, pg, 'UPDATE tarot_days SET receipts=%s WHERE owner_key=%s AND day=%s',
             (json.dumps(receipts,ensure_ascii=False),key,day))
