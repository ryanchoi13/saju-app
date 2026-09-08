"""Whole-plan feedback: no per-dish likes, no inferred dislikes or consumption.

Opaque random tokens authorize only the returned plan, never an arbitrary user ID.
Account identity comes from the existing account response pipeline. That pipeline's
existing authentication limitations are unchanged by this module.
"""
import hashlib
import json
import secrets
from collections import Counter
from . import meal_history
from .menu_categories import menu_category


def _db():
    db = meal_history._connection()
    db.execute("""CREATE TABLE IF NOT EXISTS meal_plan_feedback (
        owner TEXT NOT NULL, version TEXT NOT NULL, day TEXT NOT NULL,
        mode TEXT NOT NULL, signature TEXT NOT NULL, token TEXT UNIQUE NOT NULL, plan TEXT NOT NULL,
        seen INTEGER NOT NULL DEFAULT 0, liked INTEGER NOT NULL DEFAULT 0,
        PRIMARY KEY(owner,version,day,mode,signature))""")
    return db


def owner_key(account):
    return hashlib.sha256(account.encode()).hexdigest()


def attach(account, plan):
    with meal_history._LOCK:
        db = _db()
        signature = hashlib.sha256(json.dumps(plan["meals"],sort_keys=True).encode()).hexdigest()
        key = (owner_key(account), meal_history.VERSION, plan["date"], plan["mode"], signature)
        row = db.execute("SELECT token,liked FROM meal_plan_feedback WHERE owner=? AND version=? AND day=? AND mode=? AND signature=?",key).fetchone()
        if row is None:
            token = secrets.token_urlsafe(32)
            db.execute("INSERT INTO meal_plan_feedback(owner,version,day,mode,signature,token,plan) VALUES(?,?,?,?,?,?,?)",(*key,token,json.dumps(plan,ensure_ascii=False)))
            db.commit()
            row = (token,0)
        return {**plan,"feedback":{"token":row[0],"liked":bool(row[1])}}


def update(token, *, liked=None, seen=False):
    with meal_history._LOCK:
        db = _db()
        if db.execute("SELECT 1 FROM meal_plan_feedback WHERE token=?",(token,)).fetchone() is None:
            raise KeyError("unknown plan")
        # Idempotent state, not event-count increments. Unliking undoes its signal.
        if liked is not None:
            db.execute("UPDATE meal_plan_feedback SET liked=?,seen=1 WHERE token=?",(int(liked),token))
        elif seen:
            db.execute("UPDATE meal_plan_feedback SET seen=1 WHERE token=?",(token,))
        db.commit()
        row = db.execute("SELECT liked FROM meal_plan_feedback WHERE token=?",(token,)).fetchone()
        return {"liked":bool(row[0])}


def preference_context(account, mode, before_date):
    if not account:
        return {}
    with meal_history._LOCK:
        rows = _db().execute("SELECT day,plan,liked FROM meal_plan_feedback WHERE owner=? AND mode=? AND seen=1 AND day<? ORDER BY day DESC,rowid DESC LIMIT 90",(owner_key(account),mode,before_date.isoformat())).fetchall()
    # At most one signal per date even after an engine-version change.
    days=set(); exposures=Counter(); positives=Counter(); liked_days=0
    for day,raw,liked in rows:
        if day in days: continue
        days.add(day)
        plan=json.loads(raw)
        liked_days += liked
        for dimension in ("category","ingredient","cuisine"):
            features=Counter(meal.get(dimension,"unknown") for meal in plan["meals"])
            for feature,count in features.items():
                weight=count/max(1,len(plan["meals"]))
                key=dimension+":"+feature
                exposures[key]+=weight
                positives[key]+=weight*liked
    if liked_days < 3:
        return {"liked_plans":liked_days,"weights":{},"unit":"whole_plan"}
    # Positive-only, exposure-normalized, conservative composition similarity.
    confidence=min(1,liked_days/10)
    weights={k:round(max(0,(positives[k]+1)/(n+4)-.25)*6*confidence,3) for k,n in exposures.items()}
    return {"liked_plans":liked_days,"weights":weights,"unit":"whole_plan"}


def preference_bonus(candidate, context):
    weights=(context or {}).get("weights",{})
    return min(4,sum(weights.get(d+":"+getattr(candidate,d),0) for d in ("ingredient","cuisine")) + weights.get("category:"+menu_category(candidate.name),0))
