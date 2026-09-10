"""Lunch followed by dinner. Editorial food mapping, not dietary prescriptions."""
from collections import Counter
from datetime import date, timedelta
import hashlib
import json
import math
from .daily_menu import MENU_POOL
from .menu_categories import menu_category
from app.engine.korean import josa

VERSION = "simple-menu-v5-lunch-dinner"
DINNER_CHICKEN = frozenset({'후라이드치킨', '양념치킨', '간장치킨', '오븐구이 치킨', '탄두리치킨'})


def suitable_for_meal(menu, period):
    return period in menu.periods and not (period == 'lunch' and menu.name in DINNER_CHICKEN)


def meal_comment(names):
    descriptions = {'김치찌개': '칼칼한 김치찌개', '된장찌개': '구수한 된장찌개',
                    '후라이드치킨': '바삭한 후라이드치킨', '양념치킨': '매콤달콤한 양념치킨',
                    '간장치킨': '짭짤한 간장치킨', '콩나물국밥': '따뜻한 콩나물국밥',
                    '해물칼국수': '따뜻한 해물칼국수', '잔치국수': '따뜻한 잔치국수'}
    lunch, dinner = (descriptions.get(name, name) for name in names)
    return f"오늘 점심에는 {josa(lunch, '을/를')}, 저녁에는 {josa(dinner, '을/를')} 즐겨 보세요."

def variation(seed, key, scale=2):
    value = int(hashlib.sha256(f"{seed}|{key}".encode()).hexdigest()[:12], 16)
    uniform = (value + 1) / (16**12 + 1)
    return -math.log(-math.log(uniform)) * scale


def eligible_menus():
    """Food ideas for any time of day, not prescribed complete meals.

    Familiarity and frequency affect ranking, never pool membership.
    Keep the separately stored diet-only pool out of this general-food pool.
    """
    return list(MENU_POOL)


def select_menus(*, day, seed, weights, history=(), saju_scale=0.5):
    pool = eligible_menus()
    recent = Counter(m.name for pair in history for m in pair)
    categories = Counter(menu_category(m.name) for pair in history[-3:] for m in pair)
    yesterday = {m.name for m in history[-1]} if history else set()
    candidates = [m for m in pool if m.name not in yesterday]

    def score(m):
        return ((m.familiarity - 3) + (m.popularity - 3) * 2 + weights.get(m.element, 0) * saju_scale
                - recent[m.name] * 4 - categories[menu_category(m.name)])

    selected = []
    for period in ('lunch', 'dinner'):
        used_categories = {menu_category(m.name) for m in selected}
        groups = {}
        for m in candidates:
            category = menu_category(m.name)
            if suitable_for_meal(m, period) and category not in used_categories:
                groups.setdefault(category, []).append(m)
        meal_seed = f'{seed}|{period}'
        category = max(groups, key=lambda c: (
            max(score(m) for m in groups[c]) + variation(meal_seed, c), c))
        selected.append(max(groups[category], key=lambda m: (
            score(m) + variation(meal_seed, m.name, 1), m.name)))
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
            "meals": [{"period": period, "label": label, "menu": name}
                      for (period, label), name in zip((('lunch', '점심'), ('dinner', '저녁')), names)],
            "reason": meal_comment(names), "season": None, "meal_period": "lunch_dinner"}
