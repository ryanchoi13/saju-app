"""Single activation guard for selector-only outfit candidates (#188 PR-4A)."""
from __future__ import annotations

from fashion_v2.candidate_registry import CANDIDATES, observed_illustrations, validate_candidates
from fashion_v2.candidate_reviews import load_reviews
from fashion_v2.candidate_templates import candidate_templates, template_ids
from fashion_v2.illustration_assets import inspect_assets, load_registry
from fashion_v2.illustration_resolver import select_illustration
from fashion_v2.svg_recommendation import PALETTE


def _colour(key: str) -> dict:
    return {"hex": PALETTE[key]["hex"], "name": key, "name_ko": PALETTE[key]["name"]}


def representative_drawings() -> dict[str, str | None]:
    """Render each extra template through the real selector pipeline once."""
    from fashion_v2.outfit_selector import render
    profile = {
        "thermal_band": "cold", "thermal_label": "추운 날", "daytime_apparent_high": 8,
        "evening_apparent_low": 4, "carry_light_outer": False, "rainy": False,
        "guidance": "", "base_layer": "warm_knit", "catalog_season_hint": "winter",
        "avoid_suede": False,
    }
    weather = {"apparent_c": 8, "rain": False, "snow": False, "legacy_profile": profile}
    result = {}
    for template in candidate_templates():
        user = {"id": "activation_guard", "gender": template["gender"], "age": 40}
        look = render(template, "basic", user, (_colour("navy"), _colour("beige")), weather, "winter")
        result[template["id"]] = select_illustration(look)
    return result


def activation_problems() -> list[str]:
    """Return every reason the current registry is not safe to activate."""
    assets = inspect_assets()
    registry_ids = {entry["id"] for entry in load_registry()}
    problems = list(assets["problems"])
    problems.extend(validate_candidates(
        CANDIDATES,
        observed=observed_illustrations(),
        registry_ids=registry_ids,
        file_ids=set(assets["sizes"]),
        reviews=load_reviews(),
        template_ids=template_ids(),
        selector_drawings=representative_drawings(),
    ))
    return problems
