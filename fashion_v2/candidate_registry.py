"""Candidate records for the A-method outfit catalogue (structure only, stage 1).

Each existing whole-outfit template becomes one explicit *candidate* record that
names its role, its source, its components and the illustrations it was observed
to render. The guarded selector rollout reads active `selector_candidate` records;
`templates_for`, `weather_templates_for` and `build_svg_catalog_contexts` remain the
unchanged two-look fallback.

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
SELECTOR_SOURCE = "selector_candidate"

KNOWN_LEGACY_ISSUES = {
    "male-winter-business_formal-trend": [
        "label '비즈니스 롱 패딩' renders the short puffer drawing all-023 (canonical_name folds every 패딩)",
    ],
}
WINTER_PUFFER_NOTE = "winter template also serves the cold (5–11°C apparent) band; puffer shown above 5°C"


def _component(item: dict) -> dict:
    extra = {"neck": item["neck"]} if item.get("neck") else {}  # only when drawn (keeps old hashes)
    return extra | {
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


# Newly drawn for the #188 fleece pilot (2026-10-18). PR-4A registers the drawings and
# activates these records for the selector. PR-4B's guarded bridge may expose them;
# the legacy builder stays independent and remains the two-look fallback.
# Components are the planned outfit. Materials decided on #188 (2026-10-19) from the
# vocabulary the live templates already use (the shoe is the same running-shoe drawing
# the live templates call suede_mesh). Base colours decided on #188 (2026-10-19) reproduce
# the live winter-casual daily colour rules; runtime luck-colour placement may still vary them.
DRAWN_CANDIDATES = (
    {
        "candidate_id": "pending-female-winter-casual-fleece", "plan_id": "art-017",
        "illustration_id": "all-064", "gender": "female", "tpo": "casual", "scope": "winter",
        "role_draft": "basic", "role_basis": "owner_decision_2026-10-18", "form": "pants",
        "items": (("outer", "플리스 집업", "ivory", "fleece"),
                  ("top", "긴팔 티셔츠", "white", "cotton"),
                  ("bottom", "청바지", "navy", "denim"),
                  ("shoes", "운동화", "white", "suede_mesh")),
    },
    {
        "candidate_id": "pending-male-winter-casual-fleece", "plan_id": "art-001",
        "illustration_id": "all-065", "gender": "male", "tpo": "casual", "scope": "winter",
        "role_draft": "basic", "role_basis": "owner_decision_2026-10-18", "form": "pants",
        "items": (("outer", "플리스 집업", "ivory", "fleece"),
                  ("top", "긴팔 캐주얼 셔츠", "white", "cotton"),
                  ("bottom", "면바지", "charcoal", "cotton"),
                  ("shoes", "운동화", "white", "suede_mesh")),
    },
) + (
    # #188 winter set (2026-10-20). Drawn in one batch under the owner's new workflow: scope at
    # the start (codi-drawing-list-final-2026-10-15, P1 winter), owner check on the comparison
    # sheet at the end. Base colours/materials follow the live winter templates of the same
    # gender/TPO; runtime luck-colour placement still varies them. Roles: owner-approved list.
    {
        "candidate_id": "pending-female-winter-casual-shearling", "plan_id": "art-016",
        "illustration_id": "all-066", "gender": "female", "tpo": "casual", "scope": "winter",
        "role_draft": "trendy", "role_basis": "owner_scope_2026-10-20", "form": "pants",
        "items": (("outer", "무스탕", "camel", "shearling"),
                  ("top", "크루넥 니트", "cream", "wool_knit"),
                  ("bottom", "청바지", "navy", "denim"),
                  ("shoes", "앵클부츠", "dark_brown", "leather")),
    },
    {
        "candidate_id": "pending-male-winter-casual-longpadding", "plan_id": "art-002",
        "illustration_id": "all-067", "gender": "male", "tpo": "casual", "scope": "winter",
        "role_draft": "basic", "role_basis": "owner_scope_2026-10-20", "form": "pants",
        "items": (("outer", "롱패딩", "navy", "down"),
                  ("top", "후드 티셔츠", "gray", "fleece_cotton"),
                  ("bottom", "기모 캐주얼 팬츠", "black", "fleece_cotton"),
                  ("shoes", "운동화", "black", "leather")),
    },
    {
        "candidate_id": "pending-male-winter-casual-shearling", "plan_id": "art-003",
        "illustration_id": "all-068", "gender": "male", "tpo": "casual", "scope": "winter",
        "role_draft": "trendy", "role_basis": "owner_scope_2026-10-20", "form": "pants",
        "items": (("outer", "무스탕", "dark_brown", "shearling"),
                  ("top", "크루넥 니트", "burgundy", "wool_knit"),
                  ("bottom", "진청바지", "dark_denim", "denim"),
                  ("shoes", "첼시 부츠", "dark_brown", "leather")),
    },
    {
        "candidate_id": "pending-male-winter-business_casual-turtleneck", "plan_id": "art-005",
        "illustration_id": "all-069", "gender": "male", "tpo": "business_casual", "scope": "winter",
        "role_draft": "trendy", "role_basis": "owner_scope_2026-10-20", "form": "pants",
        "items": (("coat", "울 코트", "charcoal", "wool"),
                  ("outer", "블레이저", "navy", "wool"),
                  ("top", "터틀넥 니트", "gray", "wool_knit", {"neck": "turtleneck"}),
                  ("bottom", "슬랙스", "charcoal", "wool"),
                  ("shoes", "옥스퍼드 구두", "black", "leather")),
    },
    {
        "candidate_id": "pending-male-winter-business_casual-halfzip", "plan_id": "art-004",
        "illustration_id": "all-070", "gender": "male", "tpo": "business_casual", "scope": "winter",
        "role_draft": "basic", "role_basis": "owner_scope_2026-10-20", "form": "pants",
        "items": (("coat", "울 코트", "navy", "wool"),
                  ("top", "하프집업 니트", "gray", "wool_knit"),
                  ("bottom", "슬랙스", "charcoal", "wool"),
                  ("shoes", "로퍼", "dark_brown", "leather")),
    },
    {
        "candidate_id": "pending-male-winter-business_formal-longpadding", "plan_id": "art-007",
        "illustration_id": "all-071", "gender": "male", "tpo": "business_formal", "scope": "winter",
        "role_draft": "trendy", "role_basis": "owner_scope_2026-10-20", "form": "pants",
        "items": (("coat", "롱패딩", "black", "down"),
                  ("outer", "수트 재킷", "charcoal", "winter_wool", {"suit_group": "charcoal_winter"}),
                  ("top", "드레스 셔츠", "white", "cotton"),
                  ("bottom", "수트 바지", "charcoal", "winter_wool", {"suit_group": "charcoal_winter"}),
                  ("tie", "솔리드 타이", "navy", "silk"),
                  ("shoes", "더비 구두", "black", "leather")),
    },
    {
        "candidate_id": "pending-male-winter-business_formal-coat-derby", "plan_id": "art-039",
        "illustration_id": "all-072", "gender": "male", "tpo": "business_formal", "scope": "winter",
        "role_draft": "basic", "role_basis": "owner_scope_2026-10-20", "form": "pants",
        "items": (("coat", "울 코트", "charcoal", "wool"),
                  ("outer", "수트 재킷", "navy", "winter_wool", {"suit_group": "navy_winter"}),
                  ("top", "드레스 셔츠", "white", "cotton"),
                  ("bottom", "수트 바지", "navy", "winter_wool", {"suit_group": "navy_winter"}),
                  ("tie", "솔리드 타이", "burgundy", "silk"),
                  ("shoes", "더비 구두", "black", "leather")),
    },
    {
        "candidate_id": "pending-female-winter-casual-longpadding", "plan_id": "art-018",
        "illustration_id": "all-073", "gender": "female", "tpo": "casual", "scope": "winter",
        "role_draft": "basic", "role_basis": "owner_scope_2026-10-20", "form": "pants",
        "items": (("outer", "롱패딩", "navy", "down"),
                  ("top", "크루넥 니트", "cream", "wool_knit"),
                  ("bottom", "기모 캐주얼 팬츠", "charcoal", "fleece_cotton"),
                  ("shoes", "운동화", "black", "leather")),
    },
    {
        "candidate_id": "pending-female-winter-business_formal-knit", "plan_id": "art-021",
        "illustration_id": "all-074", "gender": "female", "tpo": "business_formal", "scope": "winter",
        "role_draft": "trendy", "role_basis": "owner_scope_2026-10-20", "form": "pants",
        "items": (("coat", "울 코트", "navy", "wool"),
                  ("outer", "수트 재킷", "charcoal", "winter_wool", {"suit_group": "charcoal_winter"}),
                  ("top", "파인 니트", "ivory", "wool_knit"),
                  ("bottom", "수트 바지", "charcoal", "winter_wool", {"suit_group": "charcoal_winter"}),
                  ("shoes", "펌프스", "black", "leather"),
                  ("bag", "핸드백", "black", "leather")),
    },
    {
        "candidate_id": "pending-female-winter-business_casual-quilted", "plan_id": "art-020",
        "illustration_id": "all-075", "gender": "female", "tpo": "business_casual", "scope": "winter",
        "role_draft": "trendy", "role_basis": "owner_scope_2026-10-20", "form": "pants",
        "items": (("outer", "퀼팅 재킷", "navy", "quilted_nylon"),
                  ("top", "크루넥 니트", "cream", "wool_knit"),
                  ("bottom", "슬랙스", "charcoal", "wool"),
                  ("shoes", "앵클부츠", "black", "leather")),
    },
    {
        "candidate_id": "pending-female-winter-casual-coat-dress", "plan_id": "art-T1",
        "illustration_id": "all-076", "gender": "female", "tpo": "casual", "scope": "winter",
        "role_draft": "trendy", "role_basis": "owner_scope_2026-10-20", "form": "dress",
        "items": (("coat", "울 코트", "camel", "wool"),
                  ("dress", "니트 원피스", "burgundy", "wool_knit"),
                  ("shoes", "앵클부츠", "dark_brown", "leather"),
                  ("bag", "크로스백", "black", "leather")),
    },
)


def _drawn_candidate(spec: dict) -> dict:
    record = {k: deepcopy(v) for k, v in spec.items() if k != "items"}
    components = [_component({"category": item[0], "label": item[1], "color": item[2], "material": item[3],
                              **(item[4] if len(item) > 4 else {})})
                  for item in spec["items"]]
    return {**record, "status": "active", "source": SELECTOR_SOURCE,
            "role": record["role_draft"], "editorial_formula_id": None,
            "components": components, "known_issues": []}


def build_candidates() -> tuple[dict, ...]:
    records = [_record(t, "season_catalog") for t in TEMPLATES]
    records += [_record(t, "weather_transition") for t in WARM_TRANSITION_LOOKS]
    records += [_pending(spec) for spec in REVIEW_PENDING]
    records += [_drawn_candidate(spec) for spec in DRAWN_CANDIDATES]
    return tuple(records)


CANDIDATES = build_candidates()


def active_candidates() -> tuple[dict, ...]:
    return tuple(c for c in CANDIDATES if c["status"] == "active")


def observed_illustrations(path: Path = OBSERVED_FILE) -> dict:
    """candidate_id -> {group: [illustration ids]} from the coverage script."""
    return json.loads(path.read_text(encoding="utf-8"))["candidates"]


def _review_policy_intersects(record: dict, drawing_id: str) -> bool:
    """A reviewed interval must leave at least one temperature allowed by policy."""
    from fashion_v2.illustration_resolver import drawing_attributes
    low = float("-inf") if record["temp_range"]["min"] == "open" else float(record["temp_range"]["min"])
    high = (float("inf") if record["temp_range"]["max_exclusive"] == "open"
            else float(record["temp_range"]["max_exclusive"]))
    rule = drawing_attributes(drawing_id).get("temperature_rule") or {}
    policy_low = float(rule.get("min_inclusive", float("-inf")))
    policy_high = float(rule.get("max_exclusive", float("inf")))
    return max(low, policy_low) < min(high, policy_high)


def validate_candidates(candidates=CANDIDATES, observed=None, registry_ids=None, file_ids=None,
                        pending_ids=None, reviews=None, template_ids=None,
                        selector_drawings=None) -> list[str]:
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
            if c.get("activation_blockers"):
                problems.append(f"{c['candidate_id']}: active candidate still has blockers")
            if c["source"] == SELECTOR_SOURCE and any(not x.get("source_color") for x in c["components"]):
                problems.append(f"{c['candidate_id']}: selector candidate needs base colours")
        else:
            if not c.get("activation_blockers"):
                problems.append(f"{c['candidate_id']}: pending candidate must list blockers")
    if observed is not None:
        for c in candidates:
            if c["status"] != "active":
                continue
            if c["source"] == SELECTOR_SOURCE:
                continue  # exact selector rendering is checked below, not in live coverage
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
    selector = [c for c in candidates if c["status"] == "active" and c["source"] == SELECTOR_SOURCE]
    if reviews is not None:
        from fashion_v2.candidate_reviews import find_review
        for c in selector:
            record = find_review(reviews, c["candidate_id"], c.get("illustration_id"))
            if record is None:
                problems.append(f"{c['candidate_id']}: current owner review required")
            elif not _review_policy_intersects(record, c["illustration_id"]):
                problems.append(f"{c['candidate_id']}: review and temperature policy do not overlap")
    if template_ids is not None:
        for c in selector:
            if c["candidate_id"] not in template_ids:
                problems.append(f"{c['candidate_id']}: selector template required")
    if selector_drawings is not None:
        for c in selector:
            rendered = selector_drawings.get(c["candidate_id"])
            if rendered != c.get("illustration_id"):
                problems.append(
                    f"{c['candidate_id']}: selector rendered {rendered!r}, expected {c.get('illustration_id')!r}")
    return problems
