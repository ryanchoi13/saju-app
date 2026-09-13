"""Durable account profile storage backed by DALHA's existing database."""
import hashlib
import json
from datetime import date

from wardrobe_store import StorageUnavailable, _connection, _execute, _owner


def owner_key(user_id):
    return hashlib.sha256(_owner(user_id).encode()).hexdigest()


def initialize():
    with _connection() as (conn, pg):
        _execute(conn, pg, """CREATE TABLE IF NOT EXISTS account_profiles (
            owner_key VARCHAR(64) PRIMARY KEY,
            payload TEXT NOT NULL,
            confirmed INTEGER NOT NULL DEFAULT 0
        )""")


def _legacy(conn, pg, user_id):
    if not pg:
        return None
    row = _execute(conn, pg, """SELECT name, gender, birth_year, birth_month,
        birth_day, calendar_type, sijin_index FROM users WHERE kakao_id=%s""",
        (_owner(user_id),)).fetchone()
    if not row:
        return None
    profile = dict(zip(("name", "gender", "birth_year", "birth_month", "birth_day",
                        "calendar_type", "sijin_index"), row))
    try:
        date(profile["birth_year"], profile["birth_month"], profile["birth_day"])
    except (TypeError, ValueError):
        return None
    if not profile["name"] or profile["gender"] not in {"male", "female"}:
        return None
    profile["calendar_type"] = profile["calendar_type"] or "solar"
    profile["sijin_index"] = profile["sijin_index"] if profile["sijin_index"] is not None else -1
    return {"profile": profile, "confirmed": True, "source": "legacy_sql"}


def load(user_id):
    initialize()
    with _connection() as (conn, pg):
        row = _execute(conn, pg,
                       "SELECT payload, confirmed FROM account_profiles WHERE owner_key=%s",
                       (owner_key(user_id),)).fetchone()
        if row:
            return {"profile": json.loads(row[0]), "confirmed": bool(row[1]),
                    "source": "database"}
        return _legacy(conn, pg, user_id)


def save(user_id, profile, *, confirmed):
    initialize()
    payload = json.dumps(profile, ensure_ascii=False)
    with _connection() as (conn, pg):
        _execute(conn, pg, """INSERT INTO account_profiles(owner_key, payload, confirmed)
            VALUES(%s,%s,%s) ON CONFLICT(owner_key) DO UPDATE SET
            payload=excluded.payload, confirmed=excluded.confirmed""",
            (owner_key(user_id), payload, int(confirmed)))
        if pg and confirmed:
            # Update legacy rows when they exist; account_profiles is authoritative.
            _execute(conn, pg, """UPDATE users SET name=%s, gender=%s, birth_year=%s,
                birth_month=%s, birth_day=%s, calendar_type=%s, sijin_index=%s
                WHERE kakao_id=%s""",
                (*(profile.get(k) for k in ("name", "gender", "birth_year", "birth_month",
                                             "birth_day", "calendar_type", "sijin_index")),
                 _owner(user_id)))
