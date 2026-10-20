"""Whole-outfit templates for reviewed selector-only candidates (#188 PR-4A).

This module is deliberately outside ``template_catalog.TEMPLATES``. The legacy
builder keeps its fixed 48 season templates and eight transition looks; the guarded
selector bridge imports these additional templates without changing that fallback.
"""
from __future__ import annotations

from copy import deepcopy

from fashion_v2.candidate_registry import SELECTOR_SOURCE, active_candidates
from fashion_v2.weather_catalog import _rain_safe, _weather_fit

LOOK_ROLE = {"basic": "daily", "trendy": "trend"}


def candidate_templates(candidates=None) -> tuple[dict, ...]:
    records = active_candidates() if candidates is None else candidates
    result = []
    for candidate in records:
        if candidate["status"] != "active" or candidate["source"] != SELECTOR_SOURCE:
            continue
        items = []
        for component in candidate["components"]:
            item = {
                "category": component["slot"],
                "label": component["source_label"],
                "color": component["source_color"],
                "material": component["material"],
                "wear_mode": component["wear_mode"],
            }
            if component.get("suit_group"):
                item["suit_group"] = component["suit_group"]
            items.append(item)
        result.append({
            "id": candidate["candidate_id"],
            "gender": candidate["gender"],
            "season": candidate["scope"],
            "tpo": candidate["tpo"],
            "look_role": LOOK_ROLE[candidate["role"]],
            "form": candidate["form"],
            "formal_variant": None,
            "status": "owner_approved",
            "selection_mode": "whole_template_only",
            # The owner reviewed this exact garment geometry. Colour placement and
            # sneaker colours may vary, but the generic denim/cotton alternative may not.
            "lock_garment_geometry": True,
            "age_policy": "soft_preference_no_exclusion",
            "items": items,
        })
    return tuple(result)


def templates_for_selector(gender: str, tpo: str, weather: dict,
                           calendar_season: str) -> tuple[dict, ...]:
    """Return reviewed candidates only when their thermal catalogue scope applies."""
    profile = weather.get("legacy_profile") or {}
    scope = profile.get("catalog_season_hint") or calendar_season
    selected = [t for t in candidate_templates()
                if (t["gender"], t["tpo"], t["season"]) == (gender, tpo, scope)]
    result = []
    for original in selected:
        look = deepcopy(original)
        if profile.get("avoid_suede"):
            _rain_safe(look, calendar_season)
        if profile:
            look["weather_fit"] = _weather_fit(profile, f"selector_{scope}")
        result.append(look)
    return tuple(result)


def template_ids() -> set[str]:
    return {t["id"] for t in candidate_templates()}
