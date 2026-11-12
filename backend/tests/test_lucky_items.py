"""오늘의 행운 아이템·숫자·방위·부적 — 2026-11-12 정오님 결정.

결정 문서: 프로젝트 claude/decisions-2026-11-12-lucky-item.md
- 오행은 행운 색 1칸과 같다(피함 오행은 나오지 않는다).
- 아이템은 십성 10칸 × 오행별 재질·색. 계절·성별로 거르고, 같은 종류가 일주일 안에 다시 나오지 않는다.
"""
import datetime as dt
import random
from collections import Counter

import pytest

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services import lucky_items
from app.engine.services.daily import _ELEMENT_GUIDE, _TALISMAN, build_daily_fortune
from app.engine.services.element_balance import ELEMENTS, TIER_AVOID, element_tiers
from fashion_v2.daily_colors import todays_lucky_tones

START = dt.date(2026, 11, 12)
DAYS = 30


def test_ten_god_slots_do_not_share_items_and_every_item_is_used():
    seen = Counter(k for _, keys in lucky_items.BY_TEN_GOD.values() for k in keys)
    assert all(n == 1 for n in seen.values()), [k for k, n in seen.items() if n > 1]
    assert set(seen) == set(lucky_items.CATALOG)
    assert len(lucky_items.CATALOG) >= 36


def test_every_slot_has_a_candidate_for_every_element_month_and_gender():
    for god in lucky_items.BY_TEN_GOD:
        for element in ELEMENTS:
            for month in range(1, 13):
                for gender in ("male", "female"):
                    keys = lucky_items.candidates(god, element, month, gender)
                    assert keys, (god, element, month, gender)
                    for key in keys:
                        season, _, names = lucky_items.CATALOG[key]
                        assert element in names and lucky_items.season_fits(season, month)


def test_seasonal_items_stay_in_season():
    winter = {k for k, (s, _, _) in lucky_items.CATALOG.items() if s == "winter"}
    summer = {k for k, (s, _, _) in lucky_items.CATALOG.items() if s == "summer"}
    for god in lucky_items.BY_TEN_GOD:
        assert not winter & set(lucky_items.candidates(god, "水", 7, "female"))
        assert not summer & set(lucky_items.candidates(god, "水", 1, "female"))


@pytest.fixture(scope="module")
def runs():
    rng = random.Random(20261112)
    people = [("male", dt.date(1978, 3, 13), 11)]
    while len(people) < 6:
        people.append((rng.choice(["male", "female"]),
                       dt.date(rng.randint(1960, 2004), rng.randint(1, 12), rng.randint(1, 28)), rng.randint(0, 23)))
    out = []
    for i, (gender, birth, hour) in enumerate(people):
        days = []
        for k in range(DAYS):
            target = START + dt.timedelta(days=k)
            core = calculate_myeongri_core(BirthInput(
                name="검사", gender=gender, birth_date=birth, calendar_type="solar", is_leap_month=False,
                birth_time=dt.time(hour, 0), time_unknown=False), target_date=target)
            fortune = build_daily_fortune(core, "검사", target, account_key=f"p{i}", include_menu=False)
            colors = todays_lucky_tones(core, fortune, target.toordinal(), birth.year * 372 + birth.month * 31 + birth.day)
            days.append((core, target, fortune, colors))
        out.append(days)
    return out


def test_luck_card_uses_the_same_element_as_the_first_lucky_color(runs):
    for days in runs:
        for core, target, fortune, colors in days:
            element = fortune["luck_element"]
            assert element == colors["element_a"], target
            card = fortune["evidence_summary"]["luck_card"]
            if card["source"] == "element_tiers_daily":
                assert element_tiers(core)["tiers"][element] != TIER_AVOID
            guide = _ELEMENT_GUIDE[element]
            assert fortune["lucky_number"] == guide["numbers"]
            assert fortune["lucky_direction"].startswith(guide["direction"])
            assert fortune["talisman"]["talisman_type"] == _TALISMAN[element][2]
            assert fortune["lucky_item"] == lucky_items.CATALOG[card["item_key"]][2][element]


def test_items_vary_and_do_not_repeat_within_a_week(runs):
    repeats = total = 0
    for days in runs:
        keys = [d[2]["evidence_summary"]["luck_card"]["item_key"] for d in days]
        names = Counter(d[2]["lucky_item"] for d in days)
        assert len(names) >= 18, names
        assert max(names.values()) <= 3, names
        for i, key in enumerate(keys):
            total += 1
            repeats += key in keys[max(0, i - 6):i]
    assert repeats == 0, (repeats, total)


def test_every_item_name_has_its_own_icon_and_color_dot():
    """화면(assets/reading-polish.js)의 아이콘·색 점 규칙이 모든 아이템 이름을 잡는다(기본 별 모양으로 빠지지 않게)."""
    import pathlib
    import re

    js = (pathlib.Path(__file__).resolve().parents[2] / "assets" / "reading-polish.js").read_text(encoding="utf-8")
    block = lambda name: js[js.index(f"const {name} = ["):js.index("];", js.index(f"const {name} = ["))]
    icons = [re.compile(src) for src in re.findall(r"\[/(.+?)/,", block("ITEM_ICONS"))]
    tints = [re.compile(src) for src in re.findall(r"\[/(.+?)/,", block("ITEM_TINT"))]
    assert len(icons) >= 40
    for key, (_, _, names) in lucky_items.CATALOG.items():
        hits = {next((i for i, rx in enumerate(icons) if rx.search(n)), None) for n in names.values()}
        assert None not in hits, (key, names)
        for name in names.values():
            assert any(rx.search(name) for rx in tints), name
