"""Wardrobe storage using the existing users/wardrobe_items tables.

DATABASE_URL selects Postgres. SQLite is for local development only; a Render
process must never acknowledge a save to its ephemeral filesystem or memory.
"""
from contextlib import contextmanager
import json
import logging
import os
from pathlib import Path
import sqlite3


class StorageUnavailable(Exception):
    pass


def _owner(user_id):
    if not user_id.startswith("user_") or not 1 <= len(user_id[5:]) <= 50:
        raise ValueError("올바른 계정으로 다시 로그인해 주세요.")
    return user_id[5:]


@contextmanager
def _connection():
    conn = None
    try:
        url = os.getenv("DATABASE_URL")
        if url:
            import psycopg2
            conn = psycopg2.connect(url, connect_timeout=5,
                                    options="-c statement_timeout=8000")
        else:
            if os.getenv("RENDER") or os.getenv("RENDER_SERVICE_ID"):
                raise StorageUnavailable("Postgres is not configured")
            path = Path(os.getenv("DALHA_WARDROBE_DB", ".data/wardrobe.sqlite"))
            path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(path, timeout=8)
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, kakao_id VARCHAR(50) UNIQUE)")
            conn.execute("""CREATE TABLE IF NOT EXISTS wardrobe_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER REFERENCES users(id),
                nickname VARCHAR(100), category VARCHAR(50), colors VARCHAR(150), materials VARCHAR(150))""")
            conn.commit()
        yield conn, bool(url)
        conn.commit()
    except (KeyError, ValueError):
        if conn:
            conn.rollback()
        raise
    except Exception as exc:
        if conn:
            conn.rollback()
        # Never log DSNs, database exception strings, or item/profile data.
        logging.getLogger(__name__).warning("Wardrobe storage unavailable (%s)", type(exc).__name__)
        raise StorageUnavailable() from None
    finally:
        if conn:
            conn.close()


def _execute(conn, pg, sql, params=()):
    cur = conn.cursor()
    cur.execute(sql if pg else sql.replace("%s", "?"), params)
    return cur


def _decode(value):
    if not value:
        return []
    try:
        decoded = json.loads(value)
        if isinstance(decoded, list) and all(isinstance(v, str) for v in decoded):
            return decoded
    except (TypeError, ValueError):
        pass
    # Original production rows use commas; slashes belong to one material/color.
    return [v.strip() for v in value.split(",") if v.strip()]


def _items(conn, pg, kakao_id):
    rows = _execute(conn, pg, """SELECT w.id, w.category, w.nickname, w.colors, w.materials
        FROM wardrobe_items w JOIN users u ON w.user_id = u.id
        WHERE u.kakao_id = %s ORDER BY w.id""", (kakao_id,)).fetchall()
    return [dict(id=r[0], category=r[1], nickname=r[2] or "",
                 colors=_decode(r[3]), materials=_decode(r[4])) for r in rows]


def list_items(user_id):
    kakao_id = _owner(user_id)
    with _connection() as (conn, pg):
        return _items(conn, pg, kakao_id)


def mutate(user_id, operation, item_id=None, item=None):
    kakao_id = _owner(user_id)
    if operation not in {"add", "edit", "delete"}:
        raise ValueError("Unknown wardrobe operation")
    values = None
    if item is not None:
        nickname = item.get("nickname") or f"{item['colors'][0]} {item['category']}"
        colors = json.dumps(item["colors"], ensure_ascii=False, separators=(",", ":"))
        materials = json.dumps(item["materials"], ensure_ascii=False, separators=(",", ":"))
        if len(nickname) > 100 or len(colors) > 150 or len(materials) > 150:
            raise ValueError("이름이나 선택한 색상·소재가 너무 깁니다. 조금 줄여 주세요.")
        values = (item["category"], nickname, colors, materials)
    with _connection() as (conn, pg):
        if not pg:
            conn.execute("BEGIN IMMEDIATE")
        if operation == "add":
            _execute(conn, pg, "INSERT INTO users (kakao_id) VALUES (%s) ON CONFLICT (kakao_id) DO NOTHING", (kakao_id,))
        # Serialize changes per account, so parallel additions cannot replace a list.
        row = _execute(conn, pg, "SELECT id FROM users WHERE kakao_id = %s" + (" FOR UPDATE" if pg else ""), (kakao_id,)).fetchone()
        if not row:
            raise KeyError(item_id)
        owner_id = row[0]
        if operation == "add":
            _execute(conn, pg, "INSERT INTO wardrobe_items (category, nickname, colors, materials, user_id) VALUES (%s, %s, %s, %s, %s)", (*values, owner_id))
        elif operation == "edit":
            cur = _execute(conn, pg, "UPDATE wardrobe_items SET category=%s, nickname=%s, colors=%s, materials=%s WHERE id=%s AND user_id=%s", (*values, item_id, owner_id))
            if cur.rowcount != 1:
                raise KeyError(item_id)
        else:
            _execute(conn, pg, "DELETE FROM wardrobe_items WHERE id=%s AND user_id=%s", (item_id, owner_id))
        return _items(conn, pg, kakao_id)


def health():
    with _connection() as (conn, pg):
        _execute(conn, pg, "SELECT u.kakao_id, w.id, w.category, w.nickname, w.colors, w.materials FROM users u LEFT JOIN wardrobe_items w ON w.user_id=u.id LIMIT 0")
        return "postgresql" if pg else "local_sqlite"
