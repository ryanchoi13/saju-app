"""Two daily choices. Editorial food mapping, not nutritional or medical advice."""
from collections import Counter
from datetime import date, timedelta
import hashlib
import json
import math
from .daily_menu import MENU_POOL
from .menu_categories import menu_category

VERSION = "simple-menu-v1"

def variation(seed, key, scale=2):
    value = int(hashlib.sha256(f"{seed}|{key}".encode()).hexdigest()[:12], 16)
    uniform = (value + 1) / (16**12 + 1)
    return -math.log(-math.log(uniform)) * scale


def eligible_menus():
    excluded = {"drink", "snack", "smoothie", "bread", "breakfast_bowl", "vegetable_meal", "raw_fish", "western_soup"}
    side_only = {"해파리냉채", "청경채볶음과 두부구이", "두부채소볶음", "콩밥", "검은콩밥", "톳밥", "홍합탕", "매운 어묵탕"}
    pool = [m for m in MENU_POOL if m.periods & {"lunch", "dinner"} and m.name not in side_only
            and m.familiarity >= 3 and m.accessibility >= 3 and menu_category(m.name) not in excluded]
    return pool


def select_menus(*, day, seed, weights, history=(), saju_scale=0.5):
    pool = eligible_menus()
    recent = Counter(m.name for pair in history for m in pair)
    categories = Counter(menu_category(m.name) for pair in history[-3:] for m in pair)
    yesterday = {m.name for m in history[-1]} if history else set()
    candidates = [m for m in pool if m.name not in yesterday]

    def score(m):
        return ((m.familiarity - 3) + (m.popularity - 3) * 2 + weights.get(m.element, 0) * saju_scale
                - recent[m.name] * 4 - categories[menu_category(m.name)])

    groups = {}
    for m in candidates:
        groups.setdefault(menu_category(m.name), []).append(m)
    ranked = sorted(groups, key=lambda c: (
        max(score(m) for m in groups[c]) + variation(seed, c), c), reverse=True)
    selected = [max(groups[c], key=lambda m: (
        score(m) + variation(seed, m.name, 1), m.name)) for c in ranked[:2]]
    assert len(selected) == 2 and len({m.name for m in selected}) == 2
    assert not yesterday & {m.name for m in selected}
    return [m.name for m in selected]

def daily_choices(birth, target_date, weights, account_key=None):
    from .meal_history import _LOCK, _connection
    from app.engine.calendar import to_solar
    identity = birth.model_dump(mode="json", exclude={"name"})
    if account_key:
        identity["account_key"] = account_key
    profile = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    birthday = to_solar(birth.birth_date, birth.calendar_type, birth.is_leap_month)
    clock = birth.birth_time.strftime("%H:%M") if birth.birth_time and not birth.time_unknown else "unknown"
    seed = f"simple-preview-v1|{birthday}|{clock}|{target_date}"
    lookup = {m.name: m for m in MENU_POOL}
    with _LOCK:
        db = _connection()
        db.execute("CREATE TABLE IF NOT EXISTS simple_menu_history (profile TEXT, version TEXT, day TEXT, menus TEXT, PRIMARY KEY(profile, version, day))")
        db.execute("BEGIN IMMEDIATE")
        try:
            saved = db.execute("SELECT menus FROM simple_menu_history WHERE profile=? AND version=? AND day=?", (profile, VERSION, str(target_date))).fetchone()
            if saved:
                names = json.loads(saved[0])
            else:
                prior = dict(db.execute("SELECT day, menus FROM simple_menu_history WHERE profile=? AND version=? AND day>=? AND day<?", (profile, VERSION, str(target_date-timedelta(days=7)), str(target_date))).fetchall())
                history = [tuple(lookup[n] for n in json.loads(prior.get(str(target_date-timedelta(days=offset)), "[]")) if n in lookup) for offset in range(7,0,-1)]
                names = select_menus(day=target_date, seed=seed, weights=weights, history=history)
                db.execute("INSERT INTO simple_menu_history VALUES (?, ?, ?, ?)", (profile, VERSION, str(target_date), json.dumps(names, ensure_ascii=False)))
            db.commit()
        except Exception:
            db.rollback()
            raise
    return {"menus": names, "pool_size": len(eligible_menus()), "pool_version": VERSION,
            "reason": "익숙한 음식에 사주 원국과 오늘의 흐름을 참고한 메뉴 제안입니다. 두 가지 중 하나를 골라보세요.",
            "season": None, "meal_period": "any"}
