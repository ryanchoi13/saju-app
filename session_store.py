"""Revocable opaque sessions. Only a digest is persisted; never a Kakao token."""
import hashlib
import secrets
import time
from wardrobe_store import _connection, _execute

COOKIE = 'dalha_session'
TTL = 30 * 24 * 60 * 60

def initialize():
    with _connection() as (conn, pg):
        _execute(conn, pg, '''CREATE TABLE IF NOT EXISTS account_sessions (
            token_hash VARCHAR(64) PRIMARY KEY, user_id VARCHAR(55) NOT NULL,
            expires_at BIGINT NOT NULL)''')

def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()

def issue(user_id):
    initialize()
    token = secrets.token_urlsafe(32)
    with _connection() as (conn, pg):
        _execute(conn, pg, 'DELETE FROM account_sessions WHERE expires_at<=%s', (int(time.time()),))
        _execute(conn, pg, 'INSERT INTO account_sessions VALUES(%s,%s,%s)',
                 (digest(token), user_id, int(time.time()) + TTL))
    return token

def resolve(token):
    if not token or not 40 <= len(token) <= 100:
        return None
    initialize()
    with _connection() as (conn, pg):
        row = _execute(conn, pg, 'SELECT user_id FROM account_sessions WHERE token_hash=%s AND expires_at>%s',
                       (digest(token), int(time.time()))).fetchone()
        return row[0] if row else None

def revoke(token):
    if not token:
        return
    initialize()
    with _connection() as (conn, pg):
        _execute(conn, pg, 'DELETE FROM account_sessions WHERE token_hash=%s', (digest(token),))
