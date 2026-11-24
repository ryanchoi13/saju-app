"""오늘의 행운 색 — 같은 날 사람마다 색이 갈리는지 (2026-11-24).

11/20 일진 기반 톤 선택(ganji_tone_pair)이 사람마다 다른 수(salt)를 쓰지 않아,
같은 날 오행 조합이 같은 사람끼리는 두 색이 늘 같았다(40명 × 30일: 두 사람 두 색까지 같음 60%).
11/11 결정 때 측정값은 3.3%였다. salt를 되살린 뒤 9%대. 이 테스트는 다시 크게 오르는 것을 막는다.
"""
import datetime as dt
import itertools
import random

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services.daily import build_daily_fortune
from fashion_v2.daily_colors import ganji_tone_pair, todays_lucky_tones

START = dt.date(2026, 11, 25)


def _colors(gender, birth, hour, day):
    core = calculate_myeongri_core(BirthInput(
        name="검사", gender=gender, birth_date=birth, calendar_type="solar", is_leap_month=False,
        birth_time=dt.time(hour, 0), time_unknown=False), target_date=day)
    fortune = build_daily_fortune(core, "검사", day, current_hour=8, account_key=None, include_menu=False)
    lk = todays_lucky_tones(core, fortune, day.toordinal(), birth.year * 372 + birth.month * 31 + birth.day)
    return lk["tone_a"]["id"], lk["tone_b"]["id"]


def test_same_day_colors_differ_between_people():
    rng = random.Random(20261124)
    people = [(rng.choice(["male", "female"]), dt.date(rng.randint(1960, 2006), rng.randint(1, 12), rng.randint(1, 28)),
               rng.randint(0, 23)) for _ in range(12)]
    same = total = 0
    for i in range(10):
        day = START + dt.timedelta(days=i)
        pairs = [_colors(g, b, h, day) for g, b, h in people]
        for a, b in itertools.combinations(pairs, 2):
            total += 1
            same += a == b
    assert same / total < 0.2, f"같은 날 두 사람 두 색까지 같음 {same}/{total}"


def test_salt_keeps_light_dark_half():
    """salt는 절반 안의 시작 칸만 민다. 양의 날 1칸은 밝은 절반, 음의 날은 어두운 절반 그대로."""
    for ganji in ("甲子", "乙丑"):
        base = {ganji_tone_pair("金", "水", ganji, s)[0]["id"] for s in range(12)}
        other = {ganji_tone_pair("金", "水", "乙丑" if ganji == "甲子" else "甲子", s)[0]["id"] for s in range(12)}
        assert base and not (base & other)
