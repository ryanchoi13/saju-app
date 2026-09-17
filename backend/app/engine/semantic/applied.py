"""Project core judgments into one service-neutral current-direction layer.

This module does not loosen the Myeongri core or invent a favorable element.
Confirmed synthesis results stay confirmed, pending results stay conditional,
and timing observations are only described as support/opposition when the
existing temporal comparison has established that relationship conditionally.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from app.engine.core.models import ConfidenceLevel, MyeongriCoreResult


APPLIED_STATE_VERSION = "applied-myeongri-state-v1"
_URGENCY_ORDER = {"high": 0, "medium": 1, "low": 2, "unspecified": 3, None: 4}
_AXES = {
    "temperature": ("warm", "cool"),
    "moisture": ("moisten", "dry"),
    "strength_balance": ("support", "drain"),
    "stability_flow": (
        "stabilize", "mediate", "protect", "resolve_conflict", "release_binding",
        "preserve_balance", "preserve_special_structure",
    ),
}


def _timing_axes_for_scope(scope: str) -> set[str]:
    # Lifetime surfaces keep the natal direction separate from transient timing.
    if "all_luck_cycles" in scope:
        return set()
    axes = set()
    if "luck_cycle" in scope:
        axes.add("luck_cycle")
    if "annual" in scope:
        axes.add("annual")
    if "monthly" in scope:
        axes.add("monthly")
    if "daily" in scope:
        axes.add("daily")
    return axes


def _elements(item: dict) -> list[str]:
    values = []
    if item.get("element"):
        values.append(item["element"])
    values.extend(item.get("elements", []))
    return list(dict.fromkeys(value for value in values if value))


def _best_urgency(values: Iterable[str | None]) -> str:
    return min(values, key=lambda value: _URGENCY_ORDER.get(value, 99)) or "unspecified"


def _confirmed_directions(core: MyeongriCoreResult) -> list[dict]:
    results = []
    for item in core.synthesis.favorable_operations:
        results.append({
            **item,
            "status": "confirmed",
            "confidence": core.synthesis.confidence.value,
        })
    return results


def _conditional_directions(core: MyeongriCoreResult) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in core.synthesis.pending_operations:
        operation = item.get("operation")
        if operation:
            grouped[operation].append(item)

    results = []
    for operation, items in grouped.items():
        results.append({
            "operation": operation,
            "elements": sorted({element for item in items for element in _elements(item)}),
            "status": "conditional",
            "confidence": ConfidenceLevel.LOW.value,
            "urgency": _best_urgency(item.get("urgency") for item in items),
            "source_modules": sorted({item.get("source_module") for item in items if item.get("source_module")}),
            "evidence_origins": sorted({item.get("evidence_origin") for item in items if item.get("evidence_origin")}),
            "reasons": sorted({item.get("reason") for item in items if item.get("reason")}),
            "unresolved_requirements": sorted({
                requirement
                for item in items
                for requirement in item.get("unresolved_requirements", [])
            }),
            "evidence_ids": sorted({
                evidence_id
                for item in items
                for evidence_id in item.get("evidence_ids", [])
            }),
        })
    return sorted(results, key=lambda item: (_URGENCY_ORDER.get(item["urgency"], 99), item["operation"]))


def _caution_directions(core: MyeongriCoreResult) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in core.synthesis.caution_operations:
        operation = item.get("operation")
        if operation:
            grouped[operation].append(item)

    results = []
    for operation, items in grouped.items():
        results.append({
            "operation": operation,
            "elements": sorted({element for item in items for element in _elements(item)}),
            "status": "caution",
            "confidence": ConfidenceLevel.LOW.value,
            "reasons": sorted({item.get("reason") for item in items if item.get("reason")}),
            "source_modules": sorted({
                module
                for item in items
                for module in item.get("source_modules", [])
            }),
            "evidence_ids": sorted({
                evidence_id
                for item in items
                for evidence_id in item.get("evidence_ids", [])
            }),
        })
    return sorted(results, key=lambda item: item["operation"])


def _condition_timing_axes(record: dict) -> set[str]:
    return {
        member["pillar"].split(":", 1)[1]
        for member in record.get("members", [])
        if str(member.get("pillar", "")).startswith("timing:")
    }


def _timing_relations(core: MyeongriCoreResult, allowed_axes: set[str]) -> list[dict]:
    if not allowed_axes:
        return []

    conditions = {
        record.get("relationship_id"): record
        for record in core.activated_state.temporal_conditions.get("records", [])
        if record.get("relationship_id")
    }
    grouped: dict[tuple[str | None, str | None], dict] = {}

    for record in core.activated_state.temporal_direction.get("records", []):
        relationship_id = record.get("relationship_id")
        condition = conditions.get(relationship_id, {})
        timing_axes = _condition_timing_axes(condition)
        if not timing_axes or not timing_axes.issubset(allowed_axes):
            continue

        comparisons = [
            item for item in record.get("comparisons", [])
            if item.get("status") == "conditional"
            and item.get("relation") in {
                "matches_requested_direction", "opposes_requested_direction"
            }
        ]
        if not comparisons:
            grouped[(relationship_id, None)] = {
                "relationship_id": relationship_id,
                "operation": None,
                "element": None,
                "timing_axes": sorted(timing_axes),
                "relation": "unresolved",
                "evidence_ids": list(record.get("evidence_ids", [])),
            }
            continue

        by_target: dict[tuple[str | None, str | None], list[dict]] = defaultdict(list)
        for item in comparisons:
            by_target[(item.get("operation"), item.get("element"))].append(item)
        for (operation, element), items in by_target.items():
            relations = {item["relation"] for item in items}
            relation = (
                "mixed" if len(relations) > 1
                else "supports" if "matches_requested_direction" in relations
                else "opposes"
            )
            key = (relationship_id, f"{operation}:{element}")
            grouped[key] = {
                "relationship_id": relationship_id,
                "operation": operation,
                "element": element,
                "timing_axes": sorted(timing_axes),
                "relation": relation,
                "evidence_ids": sorted({
                    evidence_id
                    for item in items
                    for evidence_id in item.get("evidence_ids", [])
                }),
            }
    return list(grouped.values())


def _timing_observations(core: MyeongriCoreResult, allowed_axes: set[str]) -> list[dict]:
    observations = []
    for axis in ("luck_cycle", "annual", "monthly", "daily"):
        if axis not in allowed_axes:
            continue
        value = (
            core.timing.luck_cycle.get("current") if axis == "luck_cycle"
            else getattr(core.timing, axis)
        ) or {}
        pillar = value.get("pillar") or {}
        if not pillar:
            continue
        observations.append({
            "axis": axis,
            "ganji": pillar.get("ganji"),
            "stem_element": pillar.get("stem_element"),
            "branch_element": pillar.get("branch_element"),
            "ten_god": value.get("ten_god"),
            "recommendation_status": "observation_only",
        })
    return observations


def _axis_summary(directions: list[dict]) -> dict[str, dict]:
    result = {}
    for axis, operations in _AXES.items():
        by_status = {
            status: sorted({
                item["operation"] for item in directions
                if item.get("status") == status and item.get("operation") in operations
            })
            for status in ("confirmed", "conditional", "caution")
        }
        present = [status for status, values in by_status.items() if values]
        result[axis] = {
            **by_status,
            "status": (
                "confirmed" if by_status["confirmed"]
                else "conditional" if by_status["conditional"]
                else "caution" if by_status["caution"]
                else "neutral"
            ),
            "has_competing_directions": any(
                set(by_status[status]) >= set(operations[:2])
                for status in present
                if len(operations) >= 2
            ),
        }
    return result


def build_applied_state(core: MyeongriCoreResult, scope: str) -> dict:
    """Return one common applied-state contract for every DALHA service.

    The layer deliberately distinguishes confirmed, conditional and observed
    information. A daily/annual element is never promoted merely because it is
    present in the timing pillar.
    """

    confirmed = _confirmed_directions(core)
    conditional = _conditional_directions(core)
    cautions = _caution_directions(core)
    directions = confirmed + conditional + cautions
    allowed_axes = _timing_axes_for_scope(scope)
    timing_relations = _timing_relations(core, allowed_axes)

    confirmed_elements = list(dict.fromkeys(
        element for item in confirmed for element in item.get("elements", [])
    ))
    conditional_elements = list(dict.fromkeys(
        element for item in conditional for element in item.get("elements", [])
    ))
    caution_elements = list(dict.fromkeys(
        element for item in cautions for element in item.get("elements", [])
    ))

    unresolved_conflict = any(
        item.get("resolution") in {"preserve_as_unresolved", "preserve_partial_result"}
        for item in core.synthesis.diagnostic_conflicts
    )
    overall_status = (
        "confirmed" if confirmed
        else "conditional" if conditional
        else "unresolved" if unresolved_conflict
        else "neutral"
    )
    confidence = (
        core.synthesis.confidence.value if confirmed
        else ConfidenceLevel.LOW.value if conditional or unresolved_conflict
        else ConfidenceLevel.UNDETERMINED.value
    )

    return {
        "version": APPLIED_STATE_VERSION,
        "scope": scope,
        "overall_status": overall_status,
        "confidence": confidence,
        "directions": directions,
        "confirmed_elements": confirmed_elements,
        "conditional_elements": conditional_elements,
        "caution_elements": caution_elements,
        "axes": _axis_summary(directions),
        "timing": {
            "axes_used": sorted(allowed_axes),
            "observations": _timing_observations(core, allowed_axes),
            "relations": timing_relations,
            "strength_shift": core.activated_state.strength_shift if allowed_axes else None,
            "effect_assessment_complete": bool(
                core.activated_state.temporal_conditions.get("effect_assessment_complete", False)
            ),
        },
        "policy": {
            "conditional_is_not_confirmed": True,
            "timing_observation_is_not_recommendation": True,
            "timing_does_not_invent_favorable_element": True,
            "fixed_score_used": False,
        },
        "evidence_ids": list(dict.fromkeys(
            core.synthesis.evidence_ids
            + [evidence_id for item in directions for evidence_id in item.get("evidence_ids", [])]
            + [evidence_id for item in timing_relations for evidence_id in item.get("evidence_ids", [])]
        )),
    }
