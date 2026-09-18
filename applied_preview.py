import json
import os
import sys
from collections import Counter, defaultdict
from datetime import date, time, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from fastapi import FastAPI, Query

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.semantic.queries import build_service_query
from app.engine.services.daily_menu import MENU_POOL, DIET_MENU_POOL
from app.engine.services.ranked_menu import build_rankings
from tests import test_applied_myeongri_state as applied_tests
from tests import test_menu_applied_state as menu_tests

app = FastAPI(title="DALHA Applied State Preview")


def _birth(y: int, m: int, d: int, gender: str, hour: int, minute: int) -> BirthInput:
    return BirthInput(
        name="preview",
        gender=gender,
        birth_date=date(y, m, d),
        calendar_type="solar",
        is_leap_month=False,
        birth_time=time(hour, minute),
        time_unknown=False,
    )


def _run_targeted_tests() -> dict:
    passed = []
    modules = (applied_tests, menu_tests)
    for module in modules:
        for name in sorted(dir(module)):
            if not name.startswith("test_"):
                continue
            fn = getattr(module, name)
            if callable(fn):
                fn()
                passed.append(f"{module.__name__}.{name}")
    return {"passed": len(passed), "tests": passed}


def _pool_map(pool):
    return {item.name: item for item in pool}


def _top_counts(counter: Counter, limit: int = 15):
    return [{"menu": name, "count": count} for name, count in counter.most_common(limit)]


def _distribution(rows, mapping, attr):
    counts = Counter()
    for name in rows:
        item = mapping.get(name)
        if item:
            counts[str(getattr(item, attr))] += 1
    return dict(counts)


def _simulate_mode(days_data, mode, pool):
    mapping = _pool_map(pool)
    exposure = Counter()
    day_sets = []
    element_exposure = Counter()
    group_exposure = Counter()
    cuisine_exposure = Counter()
    candidate_excluded_by_caution = set()
    state_days = defaultdict(Counter)
    meal_slots = {period: Counter() for period in ("breakfast", "lunch", "dinner")}

    for row in days_data:
        ranking = row["ranking"]
        ranked = ranking["rankings"][mode]
        names = [item["menu"] for item in ranked]
        day_sets.append(set(names))
        exposure.update(names)

        for item in ranked:
            candidate = mapping[item["menu"]]
            element_exposure[candidate.element] += 1
            group_exposure[candidate.group] += 1
            cuisine_exposure[candidate.cuisine] += 1

        for element, state in ranking["element_states"].items():
            state_days[element][state] += 1
            if state == "caution":
                candidate_excluded_by_caution.update(
                    item.name for item in pool if item.element == element
                )

        if mode == "general":
            for period in meal_slots:
                eligible = [
                    item["menu"]
                    for item in ranked
                    if period in mapping[item["menu"]].periods
                ]
                meal_slots[period].update(eligible[:2])

    pool_names = {item.name for item in pool}
    shown = set(exposure)
    never_shown = sorted(pool_names - shown)
    shown_counts = sorted(exposure.values(), reverse=True)
    repeated_every_day = sorted(name for name, count in exposure.items() if count == len(days_data))
    top10_exposure = sum(count for _, count in exposure.most_common(10))
    total_exposure = sum(exposure.values())

    result = {
        "days": len(days_data),
        "pool_size": len(pool),
        "total_exposure": total_exposure,
        "distinct_shown": len(shown),
        "never_shown_count": len(never_shown),
        "never_shown": never_shown,
        "top_repeated": _top_counts(exposure),
        "shown_every_day": repeated_every_day,
        "max_exposure": shown_counts[0] if shown_counts else 0,
        "top10_share": round(top10_exposure / total_exposure, 4) if total_exposure else 0,
        "element_exposure": dict(element_exposure),
        "element_pool": dict(Counter(item.element for item in pool)),
        "group_exposure": dict(group_exposure),
        "group_pool": dict(Counter(item.group for item in pool)),
        "cuisine_exposure": dict(cuisine_exposure),
        "caution_excluded_menu_count": len(candidate_excluded_by_caution),
        "caution_excluded_menus": sorted(candidate_excluded_by_caution),
        "element_state_days": {element: dict(counter) for element, counter in state_days.items()},
    }
    if mode == "general":
        result["meal_period_slots"] = {
            period: {
                "total": sum(counter.values()),
                "distinct": len(counter),
                "top_repeated": _top_counts(counter, 10),
            }
            for period, counter in meal_slots.items()
        }
    return result


def _simulation(start: date, days: int, birth: BirthInput) -> dict:
    rows = []
    for offset in range(days):
        target = start + timedelta(days=offset)
        core = calculate_myeongri_core(birth, target_date=target)
        query = build_service_query(core, "daily_overall")
        ranking = build_rankings(core.input, target, query["applied_state"])
        rows.append({
            "date": target.isoformat(),
            "basis": ranking["basis"],
            "confidence": ranking["confidence"],
            "element_states": ranking["element_states"],
            "ranking": ranking,
        })

    basis_days = Counter(row["basis"] for row in rows)
    return {
        "profile": {
            "birth_date": birth.birth_date.isoformat(),
            "gender": birth.gender,
            "birth_time": birth.birth_time.isoformat(timespec="minutes") if birth.birth_time else None,
        },
        "period": {
            "start": start.isoformat(),
            "days": days,
            "end": (start + timedelta(days=days - 1)).isoformat(),
        },
        "basis_days": dict(basis_days),
        "general": _simulate_mode(rows, "general", MENU_POOL),
        "diet": _simulate_mode(rows, "diet", DIET_MENU_POOL),
    }


@app.on_event("startup")
def startup_checks():
    checks = _run_targeted_tests()
    print("APPLIED_MENU_TESTS=" + json.dumps(checks, ensure_ascii=False, separators=(",", ":")), flush=True)
    birth = _birth(1978, 3, 13, "male", 10, 30)
    sim = _simulation(date(2026, 9, 18), 30, birth)
    print("MENU_30D_SIM=" + json.dumps(sim, ensure_ascii=False, separators=(",", ":")), flush=True)


@app.get("/menu-sim")
def menu_sim(
    start: date = Query(date(2026, 9, 18)),
    days: int = Query(30, ge=1, le=60),
    y: int = 1978,
    m: int = 3,
    d: int = 13,
    gender: str = "male",
    hour: int = 10,
    minute: int = 30,
):
    return _simulation(start, days, _birth(y, m, d, gender, hour, minute))
