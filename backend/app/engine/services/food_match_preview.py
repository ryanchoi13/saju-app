"""Preview-only food matching against Applied Myeongri State.

No numeric score, no majority vote, and no production ranking behavior.
A held/conflicted direction is never a reason to penalize a food. It only means
that direction cannot currently be used as positive recommendation evidence.
"""

from __future__ import annotations

from .food_profile_testset import FOOD_TESTSET, element_signals


def _direction_for_element(applied_state: dict, element: str) -> list[dict]:
    return [
        direction
        for direction in applied_state.get("directions", [])
        if direction.get("status") in {"confirmed", "conditional"}
        and element in direction.get("elements", [])
    ]


def _direction_usability(direction: dict) -> str:
    relation = (direction.get("timing_assessment") or {}).get("relation", "unresolved")
    status = direction.get("status")

    if status == "confirmed":
        if relation == "opposes":
            return "conflicted"
        if relation == "mixed":
            return "mixed"
        if relation == "unresolved":
            return "usable"
        return "supported"

    # Conditional directions are positive food evidence only when timing
    # explicitly supports them. Other states stay visible but neutral.
    if relation == "supports":
        return "supported"
    if relation == "opposes":
        return "conflicted"
    if relation == "mixed":
        return "mixed"
    return "unresolved"


def match_food(profile, applied_state: dict) -> dict:
    signals = element_signals(profile)
    signal_elements = {
        item["element"]
        for group in ("foundation", "flavor")
        for item in signals[group]
    }

    matches = []
    held = []
    for element in sorted(signal_elements):
        for direction in _direction_for_element(applied_state, element):
            usability = _direction_usability(direction)
            record = {
                "element": element,
                "operation": direction.get("operation"),
                "direction_status": direction.get("status"),
                "timing_relation": (direction.get("timing_assessment") or {}).get("relation"),
                "usability": usability,
            }
            if usability == "supported":
                matches.append(record)
            else:
                held.append(record)

    if matches:
        foundation_match = any(
            item["element"] == match["element"]
            for item in signals["foundation"]
            for match in matches
        )
        classification = "foundation_match" if foundation_match else "flavor_match"
    else:
        # Held directions never make a food unfavorable. They simply cannot be
        # used as a positive recommendation reason on this date.
        classification = "neutral"

    return {
        "menu": profile.name,
        "classification": classification,
        "signals": signals,
        "matched_directions": matches,
        "held_directions": held,
        "food_profile": {
            "foundations": list(profile.foundations),
            "identity_ingredients": list(profile.identity_ingredients),
            "secondary_ingredients": list(profile.secondary_ingredients),
            "five_flavors": sorted(profile.five_flavors),
            "cooking_modifiers": list(profile.cooking_modifiers),
            "serving_temperature": profile.serving_temperature,
            "thermal_nature": profile.thermal_nature,
            "thermal_confidence": profile.thermal_confidence,
        },
    }


def match_testset(applied_state: dict) -> dict:
    rows = [match_food(profile, applied_state) for profile in FOOD_TESTSET]
    return {
        "foundation_matches": [
            row["menu"] for row in rows if row["classification"] == "foundation_match"
        ],
        "flavor_matches": [
            row["menu"] for row in rows if row["classification"] == "flavor_match"
        ],
        "held_signal": [
            row["menu"] for row in rows if row["held_directions"]
        ],
        "neutral": [
            row["menu"] for row in rows if row["classification"] == "neutral"
        ],
        "rows": rows,
    }
