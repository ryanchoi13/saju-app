"""Independent hard-constraint oracle for outfit candidates (#188 PR-2).

Kept separate from any future selector so that a selector cannot grade itself.
It only answers "is this outer allowed at this apparent temperature / in snow?"
using the owner-confirmed rules, and answers "unknown" whenever a rule, an
attribute, or the weather itself is missing. "unknown" is never "allowed".

Also reproduces the legacy behaviour that violates the confirmed rule today
(puffers on 5–11°C days), so that the known failure stays visible in CI instead of
being silently excepted.
"""
from __future__ import annotations

ALLOWED, BLOCKED, UNKNOWN, NOT_APPLICABLE = "allowed", "blocked", "unknown", "not_applicable"


def temperature_verdict(attributes: dict, apparent_c) -> str:
    """attributes: one entry of candidate_attributes.ATTRIBUTES (or the same shape)."""
    if attributes.get("outer_slot") is None:
        return NOT_APPLICABLE
    if apparent_c is None:
        return UNKNOWN  # weather unavailable
    rule = attributes.get("temperature_rule")
    if rule is None:
        return UNKNOWN  # no confirmed rule for this outer
    if rule.get("outer_length") and attributes["outer_length"]["value"] != rule["outer_length"]:
        return UNKNOWN
    t = float(apparent_c)
    if "max_exclusive" in rule and not t < rule["max_exclusive"]:
        return BLOCKED
    if "min_inclusive" in rule and not t >= rule["min_inclusive"]:
        return BLOCKED
    return ALLOWED


def snow_verdict(attributes: dict, snowing) -> str:
    if snowing is None:
        return UNKNOWN
    if not snowing:
        return NOT_APPLICABLE
    value = (attributes.get("snow") or {}).get("value", "unknown")
    return ALLOWED if value == "suitable" else BLOCKED if value == "unsuitable" else UNKNOWN


# Legacy reproduction --------------------------------------------------------------

# What the live builder shows today on a cold-band day (apparent daytime high 5–11°C),
# which the confirmed rule blocks. Expected to stay exactly this set until the
# selector work fixes it; a change in either direction should be looked at.
KNOWN_LEGACY_VIOLATIONS = frozenset({
    ("male", "casual", 1, "male-winter-casual-daily"),
    ("male", "business_casual", 2, "male-winter-business_casual-trend"),
    ("male", "business_formal", 2, "male-winter-business_formal-trend"),
    ("female", "casual", 1, "female-winter-casual-daily"),
    ("female", "business_casual", 2, "female-winter-business_casual-trend"),
})


def legacy_cold_band_violations(apparent_high: float = 8.0) -> set:
    """Run the real builder at one cold-band day and list blocked outers.

    Legacy basis = daytime apparent high (weather_outfit.classify_weather)."""
    from fashion_v2.candidate_attributes import ATTRIBUTES
    from fashion_v2.svg_recommendation import PALETTE, build_svg_catalog_contexts
    from fashion_v2.weather_outfit import thermal_band

    band = thermal_band(apparent_high)
    profile = dict(thermal_band=band["key"], thermal_label=band["label"],
                   daytime_apparent_high=apparent_high, evening_apparent_low=apparent_high - 4,
                   carry_light_outer=False, rainy=False, guidance="", base_layer=band["base_layer"],
                   catalog_season_hint=band["catalog_season_hint"], avoid_suede=False)
    a = {"hex": PALETTE["navy"]["hex"], "name": "navy", "name_ko": PALETTE["navy"]["name"]}
    b = {"hex": PALETTE["beige"]["hex"], "name": "beige", "name_ko": PALETTE["beige"]["name"]}
    found = set()
    for gender in ("male", "female"):
        contexts = build_svg_catalog_contexts(gender, "winter", a, b, weather_profile=profile, age=40)
        for tpo, payload in contexts.items():
            for look in payload["looks"]:
                attrs = ATTRIBUTES[look["id"]]
                if temperature_verdict(attrs, apparent_high) == BLOCKED:
                    found.add((gender, tpo, look["recommendation_number"], look["id"]))
    return found
