"""Recommendation history, separate from actual food consumption.

Set DALHA_MENU_HISTORY_DB to a persistent disk path before production deployment.
Without it this uses a local .data SQLite file. A production persistent mount
is still required for survival across container replacements.
"""
import hashlib
import json
import os
import sqlite3
import threading
from pathlib import Path
from datetime import timedelta

_LOCK = threading.RLock()
_DB = None
VERSION = "meal-personal-v4"


def _connection():
    global _DB
    if _DB is None:
        path = os.getenv("DALHA_MENU_HISTORY_DB", str(Path(__file__).resolve().parents[4] / ".data" / "menu-history.sqlite"))
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        _DB = sqlite3.connect(path,
                              check_same_thread=False, timeout=15)
        _DB.execute("""CREATE TABLE IF NOT EXISTS meal_history (
            profile TEXT NOT NULL, version TEXT NOT NULL, day TEXT NOT NULL,
            plans TEXT NOT NULL, PRIMARY KEY(profile, version, day))""")
        _DB.commit()
    return _DB


def stored_plans(birth, target_date, build, account_key=None):
    # Names are irrelevant to recommendations; store a fingerprint, not birthdays.
    identity = birth.model_dump(mode="json", exclude={"name"})
    if account_key:
        identity["account_key"] = account_key
    profile = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    with _LOCK:
        db = _connection()
        db.execute("BEGIN IMMEDIATE")
        try:
            saved = db.execute(
                "SELECT plans FROM meal_history WHERE profile=? AND version=? AND day=?",
                (profile, VERSION, target_date.isoformat())).fetchone()
            if saved:
                db.commit()
                return json.loads(saved[0])
            rows = db.execute(
                "SELECT plans FROM meal_history WHERE profile=? AND version=? AND day>=? AND day<? ORDER BY day",
                (profile, VERSION, (target_date - timedelta(days=9)).isoformat(),
                 target_date.isoformat())).fetchall()
            histories = [json.loads(row[0]) for row in rows]
            plans = build(tuple(p["general"] for p in histories),
                          tuple(p["diet"] for p in histories))
            for plan in plans.values():
                plan["history_storage"] = "configured_file" if os.getenv("DALHA_MENU_HISTORY_DB", "local_file") != ":memory:" else "process_memory"
            db.execute("INSERT INTO meal_history VALUES (?, ?, ?, ?)",
                       (profile, VERSION, target_date.isoformat(), json.dumps(plans, ensure_ascii=False)))
            db.commit()
            return plans
        except Exception:
            db.rollback()
            raise
