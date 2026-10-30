"""자동 검사: 가상 사용자 × 여러 날의 코디 색을 만들어 반복·근거를 잰다.

화면에 코디를 다시 켜려면 checks.json 기준을 모두 넘어야 한다(공개 관문: 근거 없는 칸 0).
"""
import datetime as dt
import json
from collections import Counter
from pathlib import Path

from fashion_v2.color_plan.planner import plan_outfit_colors, tone_class
from fashion_v2.svg_recommendation import PALETTE

CHECKS_PATH = Path(__file__).with_name("checks.json")

# 첫 조사 집단(20대 여성·40대 남성)을 중심으로, 다른 나이대도 조금 섞는다.
VIRTUAL_USERS = [
    ("female", (2002, 4, 11), 10), ("female", (2000, 9, 3), 7), ("female", (2004, 1, 27), 15),
    ("female", (1999, 12, 19), 21), ("female", (2001, 6, 30), None),
    ("male", (1984, 2, 8), 9), ("male", (1981, 7, 14), 13), ("male", (1986, 11, 2), 22),
    ("male", (1979, 5, 25), 6), ("male", (1983, 10, 9), None),
    ("female", (1990, 8, 17), 11), ("male", (1995, 3, 3), 18),
]


def outfit_slots(season):
    """칸 구성(틀). 실제 도안 구성은 나중에 연결한다."""
    slots = [{"slot": "top", "area": "medium"}, {"slot": "bottom", "area": "large"},
             {"slot": "shoes", "area": "small"}, {"slot": "bag", "area": "small"}]
    if season in {"autumn", "winter", "spring"}:
        slots.insert(0, {"slot": "outer", "area": "large"})
    return slots


def season_of(day):
    return {12: "winter", 1: "winter", 2: "winter", 3: "spring", 4: "spring", 5: "spring",
            6: "summer", 7: "summer", 8: "summer"}.get(day.month, "autumn")


def simulate(start, days, users=VIRTUAL_USERS):
    """실제 엔진으로 오늘의 행운 색을 구하고 planner 로 칸을 채운다. 사용자당 하루 하나의 결과."""
    from app.engine.core.models import BirthInput
    from app.engine.orchestrator import calculate_myeongri_core
    from app.engine.services.daily import build_daily_fortune
    from fashion_v2.daily_colors import todays_lucky_tones

    runs = []
    for gender, (y, m, d), hour in users:
        heroes = []
        for i in range(days):
            day = start + dt.timedelta(days=i)
            core = calculate_myeongri_core(BirthInput(
                name="검사", gender=gender, birth_date=dt.date(y, m, d), calendar_type="solar",
                is_leap_month=False, birth_time=dt.time(hour, 0) if hour is not None else None,
                time_unknown=hour is None), target_date=day)
            fortune = build_daily_fortune(core, "검사", day, current_hour=8, account_key=None, include_menu=False)
            lucky = todays_lucky_tones(core, fortune, day.toordinal(), y * 372 + m * 31 + d)
            plan = plan_outfit_colors(outfit_slots(season_of(day)), [lucky["tone_a"], lucky["tone_b"]],
                                      recent_heroes=heroes[-3:])
            heroes.append(plan["hero"])
            runs.append(dict(user=f"{gender}-{y}", day=day.isoformat(), plan=plan))
    return runs


def measure(runs):
    by_user = {}
    for r in runs:
        by_user.setdefault(r["user"], []).append(r["plan"])
    repeats = days = 0
    worst_14 = 0
    for plans in by_user.values():
        heroes = [p["hero"] for p in plans]
        repeats += sum(a == b for a, b in zip(heroes, heroes[1:]))
        days += max(len(heroes) - 1, 0)
        for i in range(len(heroes)):
            worst_14 = max(worst_14, max(Counter(heroes[i:i + 14]).values()))
    slots = [s for r in runs for s in r["plan"]["slots"].values()]
    with_evidence = sum(s["evidence"] is not None for s in slots)
    vivid_pairs = sum(
        sum(tone_class(PALETTE[s["color"]]) == "vivid" for s in r["plan"]["slots"].values() if s["source"] == "lucky") >= 2
        for r in runs)
    gaps = Counter(g for r in runs for g in r["plan"]["gaps"])
    unplaced = sum(len(r["plan"]["unplaced"]) for r in runs)
    return dict(
        outfits=len(runs),
        hero_consecutive_repeat_rate=round(repeats / days, 4) if days else 0.0,
        max_same_hero_in_14_days=worst_14,
        vivid_pair_violations=vivid_pairs,
        evidence_share=round(with_evidence / len(slots), 4) if slots else 0.0,
        slots_without_evidence=dict(gaps.most_common()),
        lucky_colors_not_placed=unplaced,
    )


def evaluate(metrics, checks=None):
    """기준별 통과 여부. release_ready 는 모두 통과일 때만 True."""
    checks = checks or json.loads(CHECKS_PATH.read_text(encoding="utf-8"))
    result = {
        "hero_repeat": metrics["hero_consecutive_repeat_rate"] <= checks["max_hero_consecutive_repeat_rate"],
        "hero_14_days": metrics["max_same_hero_in_14_days"] <= checks["max_same_hero_in_14_days"],
        "vivid_pairs": metrics["vivid_pair_violations"] <= checks["max_vivid_pair_violations"],
        "evidence": metrics["evidence_share"] >= checks["min_evidence_share_for_release"],
    }
    result["release_ready"] = all(result.values())
    return result
