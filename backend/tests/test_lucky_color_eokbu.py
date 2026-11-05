"""오늘의 행운 색 = 오늘 필요한 기운 1·2순위, 점수 카드와 같은 억부 방향 (2026-11-05 정오님 결정).

결정 문서: 프로젝트 claude/decisions-2026-11-05-lucky-color.md
- 강약 방향이 있는 사람은 점수 카드(daily_score.yong_item)가 '억부 기신'이라 부르는 오행을
  보완 1순위·행운 색으로 내지 않는다(통관 날 첫 칸만 예외).
- 두 색은 서로 다른 오행이다.
"""
import datetime as dt
import random

import pytest

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services.daily import build_daily_fortune
from app.engine.services.daily_score import _god_group, yong_direction
from app.engine.services.element_balance import ELEMENTS, eokbu_avoid, natal_balance
from fashion_v2.daily_colors import todays_lucky_tones

START = dt.date(2026, 11, 5)
DAYS = 60   # 60갑자 한 바퀴


def _core(gender, birth, hour, target):
    return calculate_myeongri_core(BirthInput(
        name="검사", gender=gender, birth_date=birth, calendar_type="solar", is_leap_month=False,
        birth_time=dt.time(hour, 0), time_unknown=False), target_date=target)


@pytest.fixture(scope="module")
def users():
    """강약 방향이 있는 사람 6명(신강 3·신약 3) + 보류 3명. 무작위지만 고정 시드."""
    rng = random.Random(20261105)
    want = {"strong": 3, "weak": 3, None: 3}
    picked = []
    while any(want.values()):
        birth = dt.date(rng.randint(1960, 2004), rng.randint(1, 12), rng.randint(1, 28))
        hour, gender = rng.randint(0, 23), rng.choice(["male", "female"])
        direction = yong_direction(_core(gender, birth, hour, START))
        if want.get(direction):
            want[direction] -= 1
            picked.append((gender, birth, hour, direction))
    return picked


def test_avoid_set_is_the_score_cards_gisin():
    """점수 카드의 억부 기신과 보완 오행의 기신이 같은 정의여야 한다(한 화면 안의 모순 방지)."""
    for dm_stem, dm in (("甲", "木"), ("丙", "火"), ("戊", "土"), ("庚", "金"), ("壬", "水")):
        for state, favorable in (("strong", {"output", "wealth", "officer"}),
                                 ("weak", {"peer", "resource"})):
            expected = {e for e in ELEMENTS if _god_group(dm_stem, e) not in favorable}
            assert eokbu_avoid(dm, state) == expected, (dm, state)
        assert eokbu_avoid(dm, "undetermined") == set()


def test_natal_primary_never_gisin(users):
    for gender, birth, hour, direction in users:
        core = _core(gender, birth, hour, START)
        nb = natal_balance(core)
        assert nb["primary"] not in nb["eokbu_avoid"]
        assert bool(nb["eokbu_avoid"]) == bool(direction)


def test_two_lucky_colors_are_different_elements_and_not_gisin(users):
    for gender, birth, hour, direction in users:
        for i in range(DAYS):
            day = START + dt.timedelta(days=i)
            core = _core(gender, birth, hour, day)
            fortune = build_daily_fortune(core, "검사", day, current_hour=8, account_key=None, include_menu=False)
            lucky = todays_lucky_tones(core, fortune, day.toordinal(), birth.year * 372 + birth.month * 31 + birth.day)
            a, b = lucky["element_a"], lucky["element_b"]
            assert a != b, (birth, day, a, b)
            assert lucky["tone_a"]["id"] != lucky["tone_b"]["id"]
            if direction:
                avoid = eokbu_avoid(core.natal_facts.pillars["day"].stem_element, direction)
                assert b not in avoid, (birth, day, b)
                if not lucky["tongguan"]:
                    assert a not in avoid, (birth, day, a)
