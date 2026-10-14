"""Engine → consumer handoff ("오늘의 기운") contract. See project doc part-engine.

The engine hands consumers (outfit, food card, talisman, story) one daily outlook.
These tests pin its shape and the rules consumers rely on, so an engine change
that breaks a consumer fails here instead of on screen.
"""
from datetime import date, time, timedelta

import pytest

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services.daily import _day_ganji, build_daily_fortune

ELEMENTS = {"木", "火", "土", "金", "水"}
PROFILES = [
    ("female", date(1990, 6, 2), time(7, 0)),
    ("male", date(1985, 12, 24), time(23, 10)),
    ("female", date(1972, 2, 29), time(13, 45)),
    ("male", date(2001, 9, 9), time(4, 30)),
]
START = date(2026, 10, 1)
DAYS = 21


def _days():
    for gender, birth, hour in PROFILES:
        for offset in range(0, DAYS, 3):
            target = START + timedelta(days=offset)
            core = calculate_myeongri_core(
                BirthInput(name="계약", gender=gender, birth_date=birth, birth_time=hour),
                target_date=target,
            )
            yield core, target, build_daily_fortune(core, "계약", target)


@pytest.fixture(scope="module")
def outlooks():
    return list(_days())


def test_outlook_fields_have_the_promised_shape(outlooks):
    for core, target, result in outlooks:
        assert result["lucky_element"] in ELEMENTS
        assert result["natal_balance_element"] in ELEMENTS
        tongguan = result["tongguan"]
        if tongguan is not None:
            assert tongguan["element"] in ELEMENTS
            assert tongguan["position"] in {"day", "month"}
            assert len(tongguan["between"]) == 2


def test_tongguan_day_sets_the_lucky_element_when_no_confirmed_direction(outlooks):
    for core, target, result in outlooks:
        favorable = (core.semantic_state or {}).get("favorable_elements") if isinstance(core.semantic_state, dict) else getattr(core.semantic_state, "favorable_elements", None)
        if result["tongguan"] and not favorable:
            assert result["lucky_element"] == result["tongguan"]["element"]


def test_food_cards_speak_for_the_same_element_as_the_day(outlooks):
    for core, target, result in outlooks:
        for card in result["menu_curation"]:
            assert card["element"] == result["lucky_element"], (target, card["mode"])


def test_calendar_day_pillar_agrees_with_timing_engine(outlooks):
    for core, target, result in outlooks:
        pillar = core.timing["daily"]["pillar"] if isinstance(core.timing, dict) else core.timing.daily["pillar"]
        assert _day_ganji(target) == pillar["ganji"], target
