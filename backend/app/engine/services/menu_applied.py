"""Translate Applied Myeongri State into menu-service ordering hints.

This module is a service adapter, not a Myeongri judgment layer. It never reads
raw timing pillars, semantic_state, or a standalone daily element. The numeric
values are compatibility bands for the existing menu sorter, not fortune scores.
"""

from __future__ import annotations

ELEMENTS = "木火土金水"

_STATE_WEIGHT = {
    "confirmed": 3,
    "conditional": 1,
    "neutral": 0,
    "conflicted": 0,
    "caution": -3,
}


def project_menu_direction(applied_state: dict | None) -> dict:
    """Project the common applied contract into explicit menu element states."""

    applied_state = applied_state or {}
    confirmed = set(applied_state.get("confirmed_elements", []))
    conditional = set(applied_state.get("conditional_elements", []))
    caution = set(applied_state.get("caution_elements", []))

    states: dict[str, str] = {}
    weights: dict[str, int] = {}
    for element in ELEMENTS:
        memberships = sum((
            element in confirmed,
            element in conditional,
            element in caution,
        ))
        if memberships > 1:
            state = "conflicted"
        elif element in confirmed:
            state = "confirmed"
        elif element in conditional:
            state = "conditional"
        elif element in caution:
            state = "caution"
        else:
            state = "neutral"
        states[element] = state
        weights[element] = _STATE_WEIGHT[state]

    if any(state == "confirmed" for state in states.values()):
        basis = "applied_confirmed"
        basis_text = "사주의 확정 보완 방향을 우선 참고해 추천 순서를 정했습니다."
    elif any(state == "conditional" for state in states.values()):
        basis = "applied_conditional"
        basis_text = "사주의 조건부 보완 방향은 약하게 참고하고, 실제 식사 적합성을 함께 반영했습니다."
    elif any(state == "caution" for state in states.values()):
        basis = "applied_caution"
        basis_text = "사주에서 주의가 필요한 방향은 추천 우선순위에서 낮게 반영했습니다."
    else:
        basis = "applied_neutral"
        basis_text = "확정된 보완 방향을 억지로 만들지 않고, 실제 식사 적합성을 중심으로 골랐습니다."

    return {
        "version": "menu-applied-direction-v1",
        "basis": basis,
        "basis_text": basis_text,
        "confidence": applied_state.get("confidence", "undetermined"),
        "element_states": states,
        "element_weights": weights,
        "policy": {
            "daily_element_fallback": False,
            "conditional_is_not_confirmed": True,
            "caution_is_not_positive": True,
            "conflict_is_not_resolved_by_service": True,
        },
    }
