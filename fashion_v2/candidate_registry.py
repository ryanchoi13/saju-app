"""Candidate records for the A-method outfit catalogue (structure only, stage 1).

Each existing whole-outfit template becomes one explicit *candidate* record that
names its role, its source, its components and the illustrations it was observed
to render. This is a data layer for later rotation work. **Nothing in the live
recommendation path reads it yet**: `templates_for`, `weather_templates_for` and
`build_svg_catalog_contexts` are unchanged, so current outputs are unchanged.

Terms kept deliberately separate (see issue #188):
- role: basic / trendy. In this stage it is only the legacy daily/trend slot carried
  over (`role_basis`), not an editorial judgement.
- geometry: the renderer's exact-match shape (catalog.js). Used for drawing lookup
  and colour-only duplicate checks. It is not a style formula.
- editorial_formula_id: the reviewed style formula. Unassigned here.
- reference_item_id: a reviewable reference garment (e.g. one particular coat) that
  can later be shared across candidates. Unassigned here. It is never a garment the
  user owns.

Known legacy issues are recorded, not fixed, in this stage: the cold (5–11°C) band
reuses winter templates that contain puffers, and "비즈니스 롱 패딩" renders the short
puffer drawing all-023.
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from fashion_v2.template_catalog import TEMPLATES
from fashion_v2.weather_catalog import WARM_TRANSITION_LOOKS

OBSERVED_FILE = Path(__file__).with_name("candidate_illustrations.json")

ROLE_FROM_LEGACY = {"daily": "basic", "trend": "trendy"}
ROLES = ("basic", "trendy")
STATUSES = ("active", "review_pending")

KNOWN_LEGACY_ISSUES = {
    "male-winter-business_formal-trend": [
        "label '비즈니스 롱 패딩' renders the short puffer drawing all-023 (canonical_name folds every 패딩)",
    ],
}
WINTER_PUFFER_NOTE = "winter template also serves the cold (5–11°C apparent) band; puffer shown above 5°C"


def _component(item: dict) -> dict:
    return {
        "slot": item["category"],
        "source_label": item["label"],
        "source_color": item["color"],
        "material": item.get("material"),
        "wear_mode": item.get("wear_mode", "worn"),
        "suit_group": item.get("suit_group"),
        # Reviewable reference garment shared across candidates. Not mapped yet.
        "reference_item_id": None,
        # Colours actually applied are decided per day by apply_colors();
        # they live in the look's color_strategy, never in this static record.
        "applied_color_source": "runtime:color_strategy.placements",
    }


def _record(template: dict, source: str) -> dict:
    legacy_role = template["look_role"]
    issues = list(KNOWN_LEGACY_ISSUES.get(template["id"], []))
    if template["season"] == "winter" and any("패딩" in i["label"] for i in template["items"]):
        issues.append(WINTER_PUFFER_NOTE)
    return {
        "candidate_id": template["id"],
        "status": "active",
        "source": source,
        "gender": template["gender"],
        "tpo": template["tpo"],
        "scope": template["season"],
        "legacy_role": legacy_role,
        "role": ROLE_FROM_LEGACY[legacy_role],
        "role_basis": "legacy_daily_trend_slot",
        "editorial_formula_id": None,
        "form": template["form"],
        "components": [_component(i) for i in template["items"]],
        "known_issues": issues,
    }


# Already drawn, not linked to any template on the live colour path. Data only:
# inactive until temperature/material review and per-colour QA (issue #188).
REVIEW_PENDING = (
    {
        "candidate_id": "pending-female-winter-casual-puffer-denim-sneaker",
        "illustration_id": "all-054", "gender": "female", "tpo": "casual", "scope": "winter",
        "role_draft": "basic", "role_basis": "chatgpt_draft_2026-10-17",
        "observed_shape": "숏패딩 / 니트 / 롤업 데님 / 러닝화",
        "reached_by": "review_preference teen-winter-blue-pink only (pair not live-possible since 2026-10-13)",
    },
    {
        "candidate_id": "pending-female-winter-casual-puffer-denim-ankleboot",
        "illustration_id": "all-055", "gender": "female", "tpo": "casual", "scope": "winter",
        "role_draft": "basic", "role_basis": "chatgpt_draft_2026-10-17",
        "observed_shape": "숏패딩 / 니트 / 롤업 데님 / 앵클부츠",
        "reached_by": "review_preference teen-winter-blue-pink only (pair not live-possible since 2026-10-13)",
    },
    {
        "candidate_id": "pending-male-winter-casual-coat-turtleneck",
        "illustration_id": "all-056", "gender": "male", "tpo": "casual", "scope": "winter",
        "role_draft": "basic", "role_basis": "chatgpt_draft_2026-10-17",
        "observed_shape": "코트 / 터틀넥 니트 / 면바지 / 레이스업 부츠",
        "reached_by": ("review_preference fifties-winter-red-blue in the trendy slot of "
                       "male-winter-casual-trend; red+sky is still live-possible"),
    },
)
PENDING_BLOCKERS = ("temperature_material_review", "per_colour_qa", "template_items_undefined")


def _pending(spec: dict) -> dict:
    return {**deepcopy(spec), "status": "review_pending", "source": "existing_illustration",
            "role": None, "editorial_formula_id": None, "components": [],
            "activation_blockers": list(PENDING_BLOCKERS), "known_issues": []}


# Newly drawn for the #188 fleece pilot (2026-10-18) and stored as PENDING drawings
# (illustration_assets.PENDING_FILES): not in catalog-data.js, so never selectable.
# Components are the planned outfit; colours and materials are not decided yet.
# All four blockers must be cleared, in this order, before a record may become active.
PENDING_ASSET_BLOCKERS = ("owner_review_record", "temperature_upper_bound_undecided",
                          "catalog_registration", "live_template")
PENDING_DRAWN = (
    {
        "candidate_id": "pending-female-winter-casual-fleece", "plan_id": "art-017",
        "illustration_id": "all-064", "gender": "female", "tpo": "casual", "scope": "winter",
        "role_draft": "basic", "role_basis": "owner_decision_2026-10-18", "form": "pants",
        "items": (("outer", "플리스 집업"), ("top", "긴팔 티셔츠"), ("bottom", "청바지"), ("shoes", "운동화")),
    },
    {
        "candidate_id": "pending-male-winter-casual-fleece", "plan_id": "art-001",
        "illustration_id": "all-065", "gender": "male", "tpo": "casual", "scope": "winter",
        "role_draft": "basic", "role_basis": "owner_decision_2026-10-18", "form": "pants",
        "items": (("outer", "플리스 집업"), ("top", "긴팔 캐주얼 셔츠"), ("bottom", "면바지"), ("shoes", "운동화")),
    },
)


def _pending_drawn(spec: dict) -> dict:
    record = {k: deepcopy(v) for k, v in spec.items() if k != "items"}
    components = [{**_component({"category": slot, "label": label, "color": None}), "material": None}
                  for slot, label in spec["items"]]
    return {**record, "status": "review_pending", "source": "pending_drawing", "role": None,
            "editorial_formula_id": None, "components": components,
            "activation_blockers": list(PENDING_ASSET_BLOCKERS), "known_issues": []}


def build_candidates() -> tuple[dict, ...]:
    records = [_record(t, "season_catalog") for t in TEMPLATES]
    records += [_record(t, "weather_transition") for t in WARM_TRANSITION_LOOKS]
    records += [_pending(spec) for spec in REVIEW_PENDING]
    records += [_pending_drawn(spec) for spec in PENDING_DRAWN]
    return tuple(records)


CANDIDATES = build_candidates()


def active_candidates() -> tuple[dict, ...]:
    return tuple(c for c in CANDIDATES if c["status"] == "active")


def observed_illustrations(path: Path = OBSERVED_FILE) -> dict:
    """candidate_id -> {group: [illustration ids]} from the coverage script."""
    return json.loads(path.read_text(encoding="utf-8"))["candidates"]


def validate_candidates(candidates=CANDIDATES, observed=None, registry_ids=None, file_ids=None,
                        pending_ids=None) -> list[str]:
    """Structural checks. Returns problems; an empty list means the registry is consistent.
    pending_ids: stored-only drawing id -> owning candidate id (default PENDING_FILES)."""
    if pending_ids is None:
        from fashion_v2.illustration_assets import PENDING_FILES
        pending_ids = PENDING_FILES
    problems = []
    ids = [c["candidate_id"] for c in candidates]
    if len(ids) != len(set(ids)):
        problems.append("candidate ids must be unique")
    for c in candidates:
        if c["status"] not in STATUSES:
            problems.append(f"{c['candidate_id']}: unknown status")
        drawing = c.get("illustration_id")
        if drawing in pending_ids:
            # A stored-only drawing can never back a selectable candidate (always checked).
            if c["status"] == "active":
                problems.append(f"{c['candidate_id']}: active candidate points at pending drawing {drawing}")
            if pending_ids[drawing] != c["candidate_id"]:
                problems.append(f"{c['candidate_id']}: pending drawing {drawing} belongs to {pending_ids[drawing]}")
        if c["status"] == "active":
            if c["role"] not in ROLES:
                problems.append(f"{c['candidate_id']}: active candidate needs a role")
            if not c["components"]:
                problems.append(f"{c['candidate_id']}: active candidate needs components")
        else:
            if not c.get("activation_blockers"):
                problems.append(f"{c['candidate_id']}: pending candidate must list blockers")
    if observed is not None:
        for c in candidates:
            if c["status"] != "active":
                continue
            live = observed.get(c["candidate_id"], {}).get("live_sample", [])
            if not live:
                problems.append(f"{c['candidate_id']}: no illustration observed on the live sample")
        unknown = set(observed) - set(ids)
        if unknown:
            problems.append(f"observed ids without a candidate: {sorted(unknown)}")
    if registry_ids is not None and file_ids is not None:
        for c in candidates:
            linked = set()
            if c["status"] == "active" and observed is not None:
                for group_ids in observed.get(c["candidate_id"], {}).values():
                    linked.update(group_ids)
            if c.get("illustration_id"):
                linked.add(c["illustration_id"])
            missing = sorted(linked - set(file_ids))
            if missing:
                problems.append(f"{c['candidate_id']}: linked illustrations without files {missing}")
            drawing = c.get("illustration_id")
            if drawing and drawing not in registry_ids and drawing not in pending_ids:
                problems.append(f"{c['candidate_id']}: illustration not registered")
    return problems
