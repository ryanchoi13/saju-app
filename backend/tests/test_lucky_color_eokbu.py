"""오늘의 행운 색 — 2026-11-05 억부 방향 정합 + 2026-11-11 3단계 원칙(B안).\n\n11/11: 행운 색은 억부·조후·비율 세 틀로 오행을 좋음·무난·피함으로 나누고, 피함만 뺀다.\n결정 문서: 프로젝트 claude/decisions-2026-11-11-lucky-color-tiers.md\n아래 11/5 내용 중 '점수 카드 기신은 색으로 내지 않는다'는 3단계 원칙으로 바뀌었다(점수 카드 정합은 정오님 검토 중).

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
from app.engine.services.element_balance import ELEMENTS, TIER_AVOID, element_tiers, eokbu_avoid, natal_balance
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


def _lucky(gender, birth, hour, day):
    core = _core(gender, birth, hour, day)
    fortune = build_daily_fortune(core, "검사", day, current_hour=8, account_key=None, include_menu=False)
    return core, todays_lucky_tones(core, fortune, day.toordinal(), birth.year * 372 + birth.month * 31 + birth.day)


def test_two_lucky_colors_are_different_elements_and_never_avoid_tier(users):
    """2026-11-11 3단계 원칙: '피함' 오행은 색으로 내지 않는다(통관 날 포함). 두 색은 서로 다른 오행."""
    for gender, birth, hour, direction in users:
        tiers = None
        for i in range(DAYS):
            day = START + dt.timedelta(days=i)
            core, lucky = _lucky(gender, birth, hour, day)
            tiers = tiers or element_tiers(core)["tiers"]
            a, b = lucky["element_a"], lucky["element_b"]
            assert a != b, (birth, day, a, b)
            assert lucky["tone_a"]["id"] != lucky["tone_b"]["id"]
            assert tiers[a] != TIER_AVOID and tiers[b] != TIER_AVOID, (birth, day, a, b, tiers)


def test_no_one_gets_the_same_pair_all_month(users):
    """11/11 발단: 억부 기신을 다 빼면 오행 두 개만 남아 한 달 내내 같은 조합이 나왔다."""
    for gender, birth, hour, direction in users:
        pairs = {frozenset((l["element_a"], l["element_b"]))
                 for l in (_lucky(gender, birth, hour, START + dt.timedelta(days=i))[1] for i in range(30))}
        assert len(pairs) >= 3, (birth, pairs)


def test_tiers_rules():
    """좋음 = 찬성 있고 반대 없음 / 피함 = 반대 둘 이상, 찬성 없음 / 무난 = 그 밖."""
    core = _core("male", dt.date(1978, 3, 13), 11, START)   # 정오님 사례(문서에 기록된 원국)
    info = element_tiers(core)
    assert info["tiers"] == {"木": "avoid", "火": "good", "土": "ok", "金": "good", "水": "ok"}, info


def test_jungoh_month_mixes_four_elements():
    """정오님 30일: 금·화 28일 고정(11/5 방식) → 금·토·화·수가 섞이고 목은 나오지 않는다."""
    seen = []
    for i in range(30):
        _, lucky = _lucky("male", dt.date(1978, 3, 13), 11, dt.date(2026, 11, 11) + dt.timedelta(days=i))
        seen += [lucky["element_a"], lucky["element_b"]]
    counts = {e: seen.count(e) for e in ELEMENTS}
    assert counts["木"] == 0
    assert all(counts[e] >= 5 for e in ("火", "土", "金", "水")), counts
    assert max(counts.values()) <= 24, counts
