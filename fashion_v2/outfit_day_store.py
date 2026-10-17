"""Per-day outfit storage (#188 PR-3, NON-PRODUCTION, SQLite only).

One row per (owner, KST day, TPO, context revision) holds BOTH roles, so a pair is
written atomically. The first writer wins; a same-day revisit returns the stored row.
A newer forecast changes the row only when a stored role now breaks a hard rule, and
then only that role is re-chosen (revision += 1, same day).

History = previous days only (same TPO, last 7 days, one row per day: the most recently
updated context). It is an exposure history, not a record of what was worn.
Retention: rows older than 30 days are deleted on write. Other data (wardrobe, saved
items) is untouched.

Scope limits, stated on purpose:
- SQLite only. This module never opens the application database and is not called by
  any app start-up path. Passing the SQLite concurrency tests says nothing about
  PostgreSQL; a PostgreSQL version needs its own lock (pg_advisory_xact_lock) and tests.
- `context_rev` currently hashes the region marker "gyeongju_fixed": that only labels
  the test context. It is not a decision about user regions.
- Members only (owner key = menu_store._key, which requires a "user_" account id).
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone

from fashion_v2 import outfit_selector

KST = timezone(timedelta(hours=9))
HISTORY_DAYS = 7
RETENTION_DAYS = 30
SCHEMA = """CREATE TABLE IF NOT EXISTS outfit_days_v1 (
    owner_key TEXT NOT NULL, day TEXT NOT NULL, tpo TEXT NOT NULL, context_rev TEXT NOT NULL,
    revision INTEGER NOT NULL, payload TEXT NOT NULL, updated_at TEXT NOT NULL,
    PRIMARY KEY (owner_key, day, tpo, context_rev))"""


def today_kst(now_utc: datetime) -> date:
    if now_utc.tzinfo is None:
        raise ValueError("now_utc must be timezone-aware")
    return now_utc.astimezone(KST).date()


def owner_key(user_id: str) -> str:
    from menu_store import _key  # same account hashing as the menu/meal stores
    return _key(user_id)


def context_rev(context: dict) -> str:
    payload = json.dumps(context, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


class OutfitDayStore:
    def __init__(self, path: str):
        self.path = path
        with self._conn() as conn:
            conn.execute(SCHEMA)

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        try:
            yield conn
        finally:
            conn.close()

    def get(self, owner, day, tpo, ctx):
        with self._conn() as conn:
            row = conn.execute("SELECT revision, payload FROM outfit_days_v1 WHERE owner_key=? AND day=? AND tpo=? AND context_rev=?",
                               (owner, str(day), tpo, ctx)).fetchone()
        return (row[0], json.loads(row[1])) if row else None

    def insert_if_absent(self, owner, day, tpo, ctx, payload, now_utc):
        """Atomic first write. Returns (revision, stored payload, created)."""
        with self._conn() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                row = conn.execute("SELECT revision, payload FROM outfit_days_v1 WHERE owner_key=? AND day=? AND tpo=? AND context_rev=?",
                                   (owner, str(day), tpo, ctx)).fetchone()
                if row:
                    conn.execute("COMMIT")
                    return row[0], json.loads(row[1]), False
                conn.execute("INSERT INTO outfit_days_v1 VALUES (?,?,?,?,?,?,?)",
                             (owner, str(day), tpo, ctx, 0, json.dumps(payload, ensure_ascii=False), now_utc.isoformat()))
                conn.execute("DELETE FROM outfit_days_v1 WHERE day < ?", (str(day - timedelta(days=RETENTION_DAYS)),))
                conn.execute("COMMIT")
                return 0, payload, True
            except Exception:
                conn.execute("ROLLBACK")
                raise

    def replace_if_revision(self, owner, day, tpo, ctx, expected_revision, payload, now_utc):
        """Compare-and-swap update. Returns (revision, stored payload, updated)."""
        with self._conn() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                cur = conn.execute("UPDATE outfit_days_v1 SET revision=?, payload=?, updated_at=? WHERE owner_key=? AND day=? AND tpo=? AND context_rev=? AND revision=?",
                                   (expected_revision + 1, json.dumps(payload, ensure_ascii=False), now_utc.isoformat(),
                                    owner, str(day), tpo, ctx, expected_revision))
                row = conn.execute("SELECT revision, payload FROM outfit_days_v1 WHERE owner_key=? AND day=? AND tpo=? AND context_rev=?",
                                   (owner, str(day), tpo, ctx)).fetchone()
                conn.execute("COMMIT")
                return row[0], json.loads(row[1]), cur.rowcount == 1
            except Exception:
                conn.execute("ROLLBACK")
                raise

    def history(self, owner, tpo, day):
        start = str(day - timedelta(days=HISTORY_DAYS))
        with self._conn() as conn:
            rows = conn.execute("SELECT day, payload, updated_at FROM outfit_days_v1 WHERE owner_key=? AND tpo=? AND day>=? AND day<? ORDER BY day, updated_at",
                                (owner, tpo, start, str(day))).fetchall()
        per_day = {}
        for d, payload, _ in rows:      # later updated_at overwrites: one row per day
            per_day[d] = json.loads(payload)
        return [per_day[d] for d in sorted(per_day)]

    def count(self):
        with self._conn() as conn:
            return conn.execute("SELECT COUNT(*) FROM outfit_days_v1").fetchone()[0]


def recommend_for_day(store: OutfitDayStore, user: dict, tpo: str, now_utc: datetime, context: dict,
                      colors, weather: dict, *, calendar_season: str, mode: str = "strict", reviews=()):
    """Return the stored (or newly chosen) pair for this user/TPO/KST day."""
    day = today_kst(now_utc)
    owner, ctx = owner_key(user["id"]), context_rev(context)
    stored = store.get(owner, day, tpo, ctx)
    if stored:
        revision, payload = stored
        bad = [r for r in outfit_selector.ROLES
               if payload.get(r) and not outfit_selector.still_valid(payload[r], weather, reviews, mode)]
        if not bad:
            return {**payload, "revision": revision, "source": "stored"}
        keep = {r: payload[r] for r in outfit_selector.ROLES if payload.get(r) and r not in bad}
        result = outfit_selector.select(user, tpo, str(day), colors, weather, calendar_season=calendar_season,
                                        history=store.history(owner, tpo, day), mode=mode, reviews=reviews, keep=keep)
        result["weather"] = weather_snapshot(weather)
        revision, payload, updated = store.replace_if_revision(owner, day, tpo, ctx, revision, result, now_utc)
        return {**payload, "revision": revision, "source": "revised" if updated else "stored"}
    result = outfit_selector.select(user, tpo, str(day), colors, weather, calendar_season=calendar_season,
                                    history=store.history(owner, tpo, day), mode=mode, reviews=reviews)
    result["weather"] = weather_snapshot(weather)
    revision, payload, created = store.insert_if_absent(owner, day, tpo, ctx, result, now_utc)
    return {**payload, "revision": revision, "source": "created" if created else "stored"}


def weather_snapshot(weather: dict) -> dict:
    return {k: weather.get(k) for k in ("apparent_c", "basis", "rain", "snow", "fetched_at")}
