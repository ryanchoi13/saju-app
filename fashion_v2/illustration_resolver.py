"""Server-side port of the client illustration matcher (#188 PR-3/PR-4B).

`assets/dalha-illustrations/catalog.js::selectIllustration` decides in the browser
which drawing a look renders. The selector needs the same answer on the server so
it can judge the *drawn* outer (a review-preference branch can turn a coat into a
puffer). This is a line-by-line port; a test compares it with the real JS on the
PR-2 manifest and must agree on every look.

PR-4B reaches this matcher through the guarded selector bridge. The legacy SVG
builder remains independent and is the fallback whenever selection is unavailable.
"""
from __future__ import annotations

import json
import re

from fashion_v2.candidate_attributes import (OBSERVED_OUTER_LENGTH, drawing_outer_type, observed_length_source,
                                             policy_rule)
from fashion_v2.illustration_assets import load_registry

RENDERER = "approved-svg-5"
BASIC_KEYS = ("gender", "top", "bottom", "dress", "outer", "shoe", "bag", "outerMode", "tuck", "knitNeck")
_HEX = re.compile(r"^#[a-f0-9]{6}$", re.IGNORECASE)
_REGISTRY = load_registry()
SHAPES = {e["id"]: e["shape"] for e in _REGISTRY}
SHAPES["10"] = SHAPES["06"]


def _is_hex(value) -> bool:
    return isinstance(value, str) and bool(_HEX.match(value))


def _s(value) -> str:
    return value or ""


def geometry_matches(spec: dict, shape: dict) -> bool:
    over = spec.get("overOuter")
    if over and not isinstance(over, dict):
        return False
    if any(_s(spec.get(k)) != _s(shape.get(k)) for k in BASIC_KEYS):
        return False
    if (spec.get("outerOpen") is not False) != (shape.get("outerOpen") is not False):
        return False
    if _s((over or {}).get("name")) != _s((shape.get("overOuter") or {}).get("name")):
        return False
    if over and (over.get("open") is not False) != ((shape.get("overOuter") or {}).get("open") is not False):
        return False
    return json.dumps(spec.get("accessories") or []) == json.dumps(shape.get("accessories") or [])


def _age_at_least_50(age) -> bool:
    try:
        return float(age) >= 50  # JS Number(undefined) is NaN -> false
    except (TypeError, ValueError):
        return False


def select_illustration(look: dict):
    """Return the drawing id the client would render, or None ("이미지를 준비하고 있습니다")."""
    spec = (look or {}).get("garment_spec")
    if not spec or look.get("renderer") != RENDERER:
        return None
    items = spec.get("accessoryItems") or []
    tie = next((i for i in items if i.get("name") == "넥타이"), None)
    watch = next((i for i in items if i.get("name") == "시계"), None)
    if tie and (tie.get("pattern") or "solid") not in ("solid", "stripe"):
        return None
    if any(i.get("color_parts") and i.get("label") not in ("넥타이", "시계") for i in look.get("items") or []):
        return None
    for entry in _REGISTRY:
        if not geometry_matches(spec, entry["shape"]):
            continue
        if entry.get("linkedSuit"):
            bottom, outer = spec.get("bottomColor"), spec.get("outerColor")
            if (bottom.lower() if isinstance(bottom, str) else bottom) != (outer.lower() if isinstance(outer, str) else outer):
                continue
        colours = []
        for slot in entry["slots"]:
            if slot == "tie.body":
                tie = tie or {}
                colours.append(((tie.get("parts") or {}).get("body") or {}).get("hex") or tie.get("color") or spec.get("accessoryColor"))
            elif slot.startswith("watch."):
                colours.append((((watch or {}).get("parts") or {}).get(slot[6:]) or {}).get("hex"))
            elif slot == "overOuter.color":
                colours.append((spec.get("overOuter") or {}).get("color"))
            else:
                colours.append(spec.get(slot))
        if not all(_is_hex(c) for c in colours):
            continue
        if tie and tie.get("pattern") == "stripe":
            if not _is_hex(((tie.get("parts") or {}).get("pattern") or {}).get("hex")):
                continue
            if "tie.body" not in entry["slots"]:
                continue
        return "10" if entry["id"] == "06" and _age_at_least_50(look.get("age")) else entry["id"]
    return None


def drawing_attributes(drawing_id: str) -> dict:
    """Outer facts read from the drawing itself, in the shape the constraint oracle expects."""
    return attributes_for_shape(drawing_id, SHAPES[drawing_id])


def attributes_for_shape(drawing_id: str, shape: dict) -> dict:
    """Same facts for a given shape. Used for stored-only (pending) drawings, which are
    deliberately absent from SHAPES so they can never be selected."""
    kind = drawing_outer_type(shape)
    if kind == "none":
        return {"outer_slot": None, "outer_type": {"value": "none", "source": "drawing_shape"},
                "outer_length": {"value": None, "source": "not_applicable"}, "temperature_rule": None}
    length = OBSERVED_OUTER_LENGTH.get(drawing_id)
    length_value = length or "unknown"
    return {"outer_slot": "outer", "outer_type": {"value": kind, "source": "drawing_shape"},
            "outer_length": {"value": length_value, "source": observed_length_source(drawing_id) if length else "unknown"},
            "temperature_rule": policy_rule(kind, length_value)}


def composition_key(drawing_id: str) -> str:
    """Colour-free composition = the drawing's geometry (10 shares 06's geometry)."""
    shape = SHAPES[drawing_id]
    return json.dumps({k: shape.get(k) for k in sorted(shape)}, ensure_ascii=False, sort_keys=True)
