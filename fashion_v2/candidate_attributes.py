"""Outer-garment and weather attributes for active candidates, with provenance (#188 PR-2).

Every value carries where it came from, so a rule is never mistaken for a review:
- owner_policy      : a rule the owner confirmed (e.g. short puffer below 5°C apparent).
- asset_observed    : seen in the shipped drawing (flat-lay art; body-relative length is
                      not measured).
- legacy_behaviour  : what current code already does (e.g. rain swaps suede shoes).
- unknown           : not reviewed / not decided. Never treated as suitable.

A policy rule says when an outer *type* may appear. Whether a particular candidate
is actually suitable at that temperature is a separate review (`suitability_review`),
which is `not_reviewed` for every candidate in this stage.

Nothing in the live recommendation path imports this module.
"""
from __future__ import annotations

from fashion_v2.candidate_registry import active_candidates, observed_illustrations
from fashion_v2.illustration_assets import load_registry

POLICY_SOURCE = "owner_policy_2026-10-15"
OBSERVED_SOURCE = "asset_observed_2026-10-17"

# Outermost worn layer decides the temperature rule. Carry layers are not worn.
LAYER_ORDER = ("coat", "outer", "mid")

# Label -> outer type. Order matters: more specific words first.
OUTER_TYPE_PATTERNS = (
    ("패딩", "puffer"), ("무스탕", "shearling"), ("코트", "coat"), ("수트 재킷", "suit_jacket"), ("정장 재킷", "suit_jacket"),
    ("플리스", "fleece"), ("퀼팅", "quilted"),
    ("가디건", "cardigan"), ("블레이저", "blazer"), ("바람막이", "windbreaker"),
    ("데님 재킷", "denim_jacket"), ("필드", "field_jacket"), ("워크 재킷", "work_jacket"),
    ("해링턴", "harrington"), ("블루종", "blouson"), ("경량 재킷", "light_jacket"),
)

# Drawings whose outer length was checked by eye in the shipped art.
OBSERVED_OUTER_LENGTH = {
    "all-018": "short", "all-021": "short", "all-023": "short",
    "all-045": "short", "all-048": "short", "all-054": "short", "all-055": "short",
    # #188 fleece pilot (stored-only drawings), decided 2026-10-19: both end around the hip.
    "all-064": "short", "all-065": "short",
    # #188 winter set, checked by eye 2026-10-20: long padding reaches below the knee,
    # shearling and quilted jackets end around the hip.
    "all-066": "short", "all-067": "long", "all-068": "short", "all-071": "long",
    "all-073": "long", "all-075": "short",
}
# Where each observation came from (default OBSERVED_SOURCE).
OBSERVED_OUTER_LENGTH_SOURCE = {"all-064": "asset_observed_2026-10-19", "all-065": "asset_observed_2026-10-19",
                                **{d: "asset_observed_2026-10-20" for d in
                                   ("all-066", "all-067", "all-068", "all-071", "all-073", "all-075")}}


def observed_length_source(drawing_id: str) -> str:
    return OBSERVED_OUTER_LENGTH_SOURCE.get(drawing_id, OBSERVED_SOURCE)

# Confirmed temperature rules (apparent °C). Only these are owner policy.
TEMPERATURE_POLICY = (
    {"outer_type": "puffer", "outer_length": "short", "max_exclusive": 5},
    {"outer_type": "puffer", "outer_length": "long", "max_exclusive": 0},
    {"outer_type": "fleece", "outer_length": None, "min_inclusive": 5},
    {"outer_type": "quilted", "outer_length": None, "min_inclusive": 5},
)

LABEL_CONFLICTS = {
    "male-winter-business_formal-trend": "template label '비즈니스 롱 패딩' but drawing all-023 is a short puffer",
}


def outer_type(label: str) -> str:
    for word, kind in OUTER_TYPE_PATTERNS:
        if word in label:
            return kind
    return "unknown"


def _value(value, source):
    return {"value": value, "source": source}


def _outermost(components):
    worn = [c for c in components if c["slot"] in LAYER_ORDER and c["wear_mode"] != "carry"]
    worn.sort(key=lambda c: LAYER_ORDER.index(c["slot"]))
    return worn[0] if worn else None


def policy_rule(kind: str, length: str | None):
    for rule in TEMPERATURE_POLICY:
        if rule["outer_type"] == kind and rule["outer_length"] in (None, length):
            return {**rule, "source": POLICY_SOURCE}
    return None


def drawing_outer_type(shape: dict) -> str:
    """Outermost outer in a registered drawing (overOuter sits on top of outer)."""
    name = (shape.get("overOuter") or {}).get("name") or shape.get("outer") or ""
    if not name or shape.get("outerMode") == "carry" and not shape.get("overOuter"):
        return "none"
    return outer_type(name)


def build_attributes(candidates=None, observed=None) -> dict:
    candidates = active_candidates() if candidates is None else candidates
    observed = observed_illustrations() if observed is None else observed
    shapes = {e["id"]: e["shape"] for e in load_registry()}
    shapes.setdefault("10", shapes.get("06", {}))
    result = {}
    for cand in candidates:
        outer = _outermost(cand["components"])
        kind = outer_type(outer["source_label"]) if outer else "none"
        drawings = {i for ids in observed.get(cand["candidate_id"], {}).values() for i in ids}
        # Selector-only candidates are deliberately absent from live coverage. Their
        # reviewed direct drawing is still an observed source for static attributes.
        if cand.get("illustration_id") and cand["illustration_id"] in shapes:
            drawings.add(cand["illustration_id"])
        drawings = sorted(drawings)
        drawn_types = {d: drawing_outer_type(shapes[d]) for d in drawings}
        same_type = [d for d, t in drawn_types.items() if t == kind]
        lengths = {OBSERVED_OUTER_LENGTH.get(d) for d in same_type} if same_type else {None}
        if outer is None:
            length = _value(None, "not_applicable")
        elif len(lengths) == 1 and None not in lengths:
            sources = {observed_length_source(d) for d in same_type}
            length = _value(lengths.pop(), sources.pop() if len(sources) == 1 else OBSERVED_SOURCE)
        else:
            length = _value("unknown", "unknown")
        rule = policy_rule(kind, length["value"]) if outer else None
        result[cand["candidate_id"]] = {
            "outer_slot": outer["slot"] if outer else None,
            "outer_label": outer["source_label"] if outer else None,
            "outer_type": _value(kind, "label_mapping" if outer else "not_applicable"),
            "outer_length": length,
            "temperature_rule": rule,  # None = no confirmed rule (not "allowed")
            "suitability_review": "not_reviewed",
            "rain": {"value": "unknown", "source": "unknown",
                     "legacy_handling": "suede/sandal swapped to leather shoes (weather_catalog._rain_safe)"},
            "snow": _value("unknown", "unknown"),
            "drawings": drawings,
            # Review-preference branches can swap the outer (e.g. coat -> puffer).
            "drawing_outer_types": dict(sorted(drawn_types.items())),
            "outer_varies_by_branch": len(set(drawn_types.values())) > 1,
            "label_conflict": LABEL_CONFLICTS.get(cand["candidate_id"]),
        }
    return result


ATTRIBUTES = build_attributes()
