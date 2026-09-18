from datetime import date

from app.engine.core.models import BirthInput
from app.engine.services.menu_applied import project_menu_direction
from app.engine.services.ranked_menu import build_rankings


def _birth():
    return BirthInput(
        name="테스트",
        gender="male",
        birth_date=date(1978, 3, 13),
    )


def test_daily_observation_never_becomes_menu_direction():
    applied = {
        "overall_status": "neutral",
        "confidence": "undetermined",
        "confirmed_elements": [],
        "conditional_elements": [],
        "caution_elements": [],
        "timing": {
            "observations": [{
                "axis": "daily",
                "stem_element": "火",
                "branch_element": "土",
                "recommendation_status": "observation_only",
            }]
        },
    }

    direction = project_menu_direction(applied)

    assert direction["basis"] == "applied_neutral"
    assert direction["element_weights"]["火"] == 0
    assert direction["element_states"]["火"] == "neutral"
    assert direction["policy"]["daily_element_fallback"] is False


def test_conditional_is_kept_separate_from_confirmed():
    applied = {
        "confidence": "low",
        "confirmed_elements": [],
        "conditional_elements": ["火"],
        "caution_elements": [],
    }

    direction = project_menu_direction(applied)

    assert direction["basis"] == "applied_conditional"
    assert direction["element_states"]["火"] == "conditional"
    assert direction["element_weights"]["火"] == 1
    assert not any(
        state == "confirmed"
        for state in direction["element_states"].values()
    )


def test_caution_is_never_positive():
    applied = {
        "confidence": "low",
        "confirmed_elements": [],
        "conditional_elements": [],
        "caution_elements": ["水"],
    }

    direction = project_menu_direction(applied)

    assert direction["element_states"]["水"] == "caution"
    assert direction["element_weights"]["水"] < 0
    assert direction["policy"]["caution_is_not_positive"] is True


def test_service_does_not_resolve_cross_status_conflict():
    applied = {
        "confidence": "low",
        "confirmed_elements": ["火"],
        "conditional_elements": [],
        "caution_elements": ["火"],
    }

    direction = project_menu_direction(applied)

    assert direction["element_states"]["火"] == "conflicted"
    assert direction["element_weights"]["火"] == 0
    assert direction["policy"]["conflict_is_not_resolved_by_service"] is True


def test_ranked_menu_has_no_daily_symbol_fallback():
    applied = {
        "overall_status": "neutral",
        "confidence": "undetermined",
        "confirmed_elements": [],
        "conditional_elements": [],
        "caution_elements": [],
        "timing": {
            "observations": [{
                "axis": "daily",
                "stem_element": "木",
                "recommendation_status": "observation_only",
            }]
        },
    }

    ranking = build_rankings(_birth(), date(2026, 9, 18), applied)

    assert ranking["basis"] == "applied_neutral"
    assert ranking["applied_policy"]["daily_element_fallback"] is False
    assert set(ranking["element_scores"].values()) == {0}
    assert all(
        item["element_state"] == "neutral"
        for item in ranking["rankings"]["general"]
    )
