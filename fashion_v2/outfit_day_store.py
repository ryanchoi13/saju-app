"""Per-day outfit storage (#188).

One row per (owner, KST day, TPO, context revision) holds BOTH roles, so a pair is
written atomically. The first writer wins; a same-day revisit returns the stored row.
A newer forecast changes the row only when a stored role now breaks a hard rule (then
only that role is re-chosen), or when an empty role can now be filled because the
re-evaluation basis changed (weather inputs, reviews, catalogue). Revision += 1 only
when a look changes; same inputs are never recomputed. Mode is part of the context key.

History = previous days only, same TPO and same MODE, last 7 days, one row per day (the
most recently updated context of that mode). The mode is a stored column, so a study row
saved later on the same day can never replace or join the strict history. It is an exposure history, not a record of what was worn.
Retention: rows older than 30 days are deleted on write. Other data (wardrobe, saved
items) is untouched.

Storage adapters:
- ``OutfitDayStore`` is the isolated SQLite adapter retained for focused tests.
- ``DurableOutfitDayStore`` uses the application's PostgreSQL connection in production
  and its local SQLite connection in development. PostgreSQL first-insert races are
  serialized with an advisory transaction lock.
- `context_rev` hashes the caller's region, profile, season, colour and selector-version
  context. The first rollout still uses the existing fixed-Gyeongju weather source.
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
    mode TEXT NOT NULL, revision INTEGER NOT NULL, payload TEXT NOT NULL, updated_at TEXT NOT NULL,
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

    def insert_if_absent(self, owner, day, tpo, ctx, payload, now_utc, mode):
        """Atomic first write. Returns (revision, stored payload, created)."""
        with self._conn() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                row = conn.execute("SELECT revision, payload FROM outfit_days_v1 WHERE owner_key=? AND day=? AND tpo=? AND context_rev=?",
                                   (owner, str(day), tpo, ctx)).fetchone()
                if row:
                    conn.execute("COMMIT")
                    return row[0], json.loads(row[1]), False
                if mode not in outfit_selector.MODES:
                    raise ValueError("mode must be strict or study")
                conn.execute("INSERT INTO outfit_days_v1 VALUES (?,?,?,?,?,?,?,?)",
                             (owner, str(day), tpo, ctx, mode, 0, json.dumps(payload, ensure_ascii=False), now_utc.isoformat()))
                conn.execute("DELETE FROM outfit_days_v1 WHERE day < ?", (str(day - timedelta(days=RETENTION_DAYS)),))
                conn.execute("COMMIT")
                return 0, payload, True
            except Exception:
                conn.execute("ROLLBACK")
                raise

    def replace_if_revision(self, owner, day, tpo, ctx, expected_revision, payload, now_utc, bump=True):
        """Compare-and-swap update. Returns (revision, stored payload, updated).
        bump=False keeps the revision (used when only the re-evaluation basis changed)."""
        with self._conn() as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                cur = conn.execute("UPDATE outfit_days_v1 SET revision=?, payload=?, updated_at=? WHERE owner_key=? AND day=? AND tpo=? AND context_rev=? AND revision=?",
                                   (expected_revision + (1 if bump else 0), json.dumps(payload, ensure_ascii=False), now_utc.isoformat(),
                                    owner, str(day), tpo, ctx, expected_revision))
                row = conn.execute("SELECT revision, payload FROM outfit_days_v1 WHERE owner_key=? AND day=? AND tpo=? AND context_rev=?",
                                   (owner, str(day), tpo, ctx)).fetchone()
                conn.execute("COMMIT")
                return row[0], json.loads(row[1]), cur.rowcount == 1
            except Exception:
                conn.execute("ROLLBACK")
                raise

    def history(self, owner, tpo, day, mode):
        """Previous days of THIS mode only (study rows never feed strict, and vice versa).
        Within a mode, several contexts on one day collapse to the latest updated row."""
        if mode not in outfit_selector.MODES:
            raise ValueError("mode must be strict or study")
        start = str(day - timedelta(days=HISTORY_DAYS))
        with self._conn() as conn:
            rows = conn.execute("SELECT day, payload, updated_at FROM outfit_days_v1 WHERE owner_key=? AND tpo=? AND mode=? AND day>=? AND day<? ORDER BY day, updated_at",
                                (owner, tpo, mode, start, str(day))).fetchall()
        per_day = {}
        for d, payload, _ in rows:      # later updated_at overwrites: one row per day
            per_day[d] = json.loads(payload)
        return [per_day[d] for d in sorted(per_day)]

    def count(self):
        with self._conn() as conn:
            return conn.execute("SELECT COUNT(*) FROM outfit_days_v1").fetchone()[0]


class DurableOutfitDayStore:
    """Application storage adapter; never falls back to ephemeral storage on Render."""

    def __init__(self):
        self._ready = False

    @staticmethod
    def _db():
        from wardrobe_store import _connection
        return _connection()

    @staticmethod
    def _execute(conn, pg, sql, params=()):
        from wardrobe_store import _execute
        return _execute(conn, pg, sql, params)

    def initialize(self):
        with self._db() as (conn, pg):
            if pg:
                self._execute(conn, pg, "SELECT pg_advisory_xact_lock(74201933)")
            self._execute(conn, pg, SCHEMA)
        self._ready = True

    def _ensure(self):
        if not self._ready:
            self.initialize()

    def _lock(self, conn, pg, owner, day, tpo, ctx):
        if pg:
            key = "|".join((owner, str(day), tpo, ctx))
            self._execute(conn, pg, "SELECT pg_advisory_xact_lock(hashtext(%s))", (key,))
        else:
            conn.execute("BEGIN IMMEDIATE")

    def get(self, owner, day, tpo, ctx):
        self._ensure()
        with self._db() as (conn, pg):
            row = self._execute(
                conn, pg,
                "SELECT revision,payload FROM outfit_days_v1 WHERE owner_key=%s AND day=%s AND tpo=%s AND context_rev=%s",
                (owner, str(day), tpo, ctx),
            ).fetchone()
        return (row[0], json.loads(row[1])) if row else None

    def insert_if_absent(self, owner, day, tpo, ctx, payload, now_utc, mode):
        if mode not in outfit_selector.MODES:
            raise ValueError("mode must be strict or study")
        self._ensure()
        with self._db() as (conn, pg):
            self._lock(conn, pg, owner, day, tpo, ctx)
            row = self._execute(
                conn, pg,
                "SELECT revision,payload FROM outfit_days_v1 WHERE owner_key=%s AND day=%s AND tpo=%s AND context_rev=%s",
                (owner, str(day), tpo, ctx),
            ).fetchone()
            if row:
                return row[0], json.loads(row[1]), False
            self._execute(
                conn, pg,
                "INSERT INTO outfit_days_v1(owner_key,day,tpo,context_rev,mode,revision,payload,updated_at) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
                (owner, str(day), tpo, ctx, mode, 0, json.dumps(payload, ensure_ascii=False), now_utc.isoformat()),
            )
            self._execute(conn, pg, "DELETE FROM outfit_days_v1 WHERE day < %s",
                          (str(day - timedelta(days=RETENTION_DAYS)),))
            return 0, payload, True

    def replace_if_revision(self, owner, day, tpo, ctx, expected_revision, payload, now_utc, bump=True):
        self._ensure()
        with self._db() as (conn, pg):
            self._lock(conn, pg, owner, day, tpo, ctx)
            next_revision = expected_revision + (1 if bump else 0)
            cur = self._execute(
                conn, pg,
                "UPDATE outfit_days_v1 SET revision=%s,payload=%s,updated_at=%s WHERE owner_key=%s AND day=%s AND tpo=%s AND context_rev=%s AND revision=%s",
                (next_revision, json.dumps(payload, ensure_ascii=False), now_utc.isoformat(),
                 owner, str(day), tpo, ctx, expected_revision),
            )
            row = self._execute(
                conn, pg,
                "SELECT revision,payload FROM outfit_days_v1 WHERE owner_key=%s AND day=%s AND tpo=%s AND context_rev=%s",
                (owner, str(day), tpo, ctx),
            ).fetchone()
            return row[0], json.loads(row[1]), cur.rowcount == 1

    def history(self, owner, tpo, day, mode):
        if mode not in outfit_selector.MODES:
            raise ValueError("mode must be strict or study")
        self._ensure()
        start = str(day - timedelta(days=HISTORY_DAYS))
        with self._db() as (conn, pg):
            rows = self._execute(
                conn, pg,
                "SELECT day,payload,updated_at FROM outfit_days_v1 WHERE owner_key=%s AND tpo=%s AND mode=%s AND day>=%s AND day<%s ORDER BY day,updated_at",
                (owner, tpo, mode, start, str(day)),
            ).fetchall()
        per_day = {}
        for raw_day, payload, _ in rows:
            per_day[raw_day] = json.loads(payload)
        return [per_day[raw_day] for raw_day in sorted(per_day)]

    def count(self):
        self._ensure()
        with self._db() as (conn, pg):
            return self._execute(conn, pg, "SELECT COUNT(*) FROM outfit_days_v1").fetchone()[0]

    def health(self):
        self._ensure()
        with self._db() as (conn, pg):
            self._execute(conn, pg, "SELECT owner_key,day,tpo,revision FROM outfit_days_v1 LIMIT 0")
            return "postgresql" if pg else "local_sqlite"


production_store = DurableOutfitDayStore()


_CATALOG_FP = {}


def catalog_fingerprint() -> str:
    """Candidates' material definitions + drawing registry + drawing files (computed once)."""
    if "value" not in _CATALOG_FP:
        from fashion_v2.candidate_registry import CANDIDATES
        from fashion_v2.candidate_reviews import _candidate_definition, drawing_version
        from fashion_v2.illustration_assets import load_registry
        registry = load_registry()
        ids = sorted({e["id"] for e in registry} | {"10"})
        value = {"candidates": [_candidate_definition(c["candidate_id"]) for c in CANDIDATES],
                 "registry": registry, "files": {i: drawing_version(i) for i in ids}}
        _CATALOG_FP["value"] = hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]
    return _CATALOG_FP["value"]


def reevaluation_basis(weather: dict, reviews, mode: str) -> dict:
    """Everything that can change which candidates are eligible. If it is unchanged, a
    stored shortage is returned as-is without recomputing."""
    from fashion_v2.candidate_reviews import reviews_fingerprint
    snapshot = weather_snapshot(weather)
    snapshot.pop("fetched_at", None)
    return {"weather": snapshot, "legacy_band": (weather.get("legacy_profile") or {}).get("thermal_band"),
            "reviews": reviews_fingerprint(reviews), "catalog": catalog_fingerprint(), "mode": mode}


def recommend_for_day(store: OutfitDayStore, user: dict, tpo: str, now_utc: datetime, context: dict,
                      colors, weather: dict, *, calendar_season: str, mode: str = "strict", reviews=()):
    """Return the stored (or newly chosen) pair for this user/TPO/KST day.

    - A stored role that breaks a hard rule under the new inputs is re-chosen (only it).
    - An EMPTY role (shortage / no_candidate) is re-evaluated only when the re-evaluation
      basis changed (weather inputs, reviews, catalogue, mode). Valid roles are kept.
    - Same basis -> the stored row is returned without recomputing.
    Revision increases only when a stored look actually changes. The mode is part of the
    context key, so study results are never reused as strict results.
    """
    day = today_kst(now_utc)
    owner, ctx = owner_key(user["id"]), context_rev({**context, "mode": mode})
    basis = reevaluation_basis(weather, reviews, mode)
    stored = store.get(owner, day, tpo, ctx)
    if stored is None:
        result = outfit_selector.select(user, tpo, str(day), colors, weather, calendar_season=calendar_season,
                                        history=store.history(owner, tpo, day, mode), mode=mode, reviews=reviews)
        result.update(weather=weather_snapshot(weather), basis=basis)
        revision, payload, created = store.insert_if_absent(owner, day, tpo, ctx, result, now_utc, mode)
        return {**payload, "revision": revision, "source": "created" if created else "stored"}

    revision, payload = stored
    roles = outfit_selector.ROLES
    bad = [r for r in roles if payload.get(r) and not outfit_selector.still_valid(payload[r], weather, reviews, mode)]
    empty = [r for r in roles if not payload.get(r)]
    if not bad and (not empty or payload.get("basis") == basis):
        return {**payload, "revision": revision, "source": "stored"}

    keep = {r: payload[r] for r in roles if payload.get(r) and r not in bad}
    result = outfit_selector.select(user, tpo, str(day), colors, weather, calendar_season=calendar_season,
                                    history=store.history(owner, tpo, day, mode), mode=mode, reviews=reviews, keep=keep)
    result.update(weather=weather_snapshot(weather), basis=basis)
    looks_changed = any((result.get(r) or {}).get("candidate_id") != (payload.get(r) or {}).get("candidate_id")
                        or (result.get(r) or {}).get("drawing_id") != (payload.get(r) or {}).get("drawing_id")
                        for r in roles)
    if not looks_changed:
        # Same looks, new basis: remember the basis so the same inputs are not recomputed.
        new_revision, stored_payload, _ = store.replace_if_revision(owner, day, tpo, ctx, revision,
                                                                    {**payload, "basis": basis}, now_utc, bump=False)
        return {**stored_payload, "revision": new_revision, "source": "stored"}
    new_revision, stored_payload, updated = store.replace_if_revision(owner, day, tpo, ctx, revision, result, now_utc)
    return {**stored_payload, "revision": new_revision, "source": "revised" if updated else "stored"}


def weather_snapshot(weather: dict) -> dict:
    return {k: weather.get(k) for k in ("apparent_c", "basis", "rain", "snow", "fetched_at")}
