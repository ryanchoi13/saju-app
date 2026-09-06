"""Evidence-preserving synthesis of the six independent diagnostics."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping

from app.engine.core.models import (
    ConfidenceLevel,
    DiagnosticResult,
    Evidence,
    EvidenceLayer,
    SynthesisResult,
)


SYNTHESIS_ENGINE_VERSION = "diagnostic-synthesis-v1"
SYNTHESIS_PRIORITY_VERSION = "special-urgent-common-conflict-v1"

_REQUIRED_MODULES = (
    "structure",
    "strength",
    "climate",
    "pathology",
    "mediation",
    "special_structure",
)
_PURPOSES = {
    "warming": "warm",
    "cooling": "cool",
    "moistening": "moisten",
    "drying": "dry",
    "stabilizing": "stabilize",
    "stabilize_root_or_support": "support",
    "restore_supporting_capacity": "support",
    "moderate_excess_force": "drain",
    "mediate_control_conflict": "mediate",
    "restore_or_mediate_flow": "mediate",
    "protect_or_restore_structure": "protect",
    "resolve_relationship_competition": "resolve_conflict",
    "verify_or_release_binding": "release_binding",
    "preserve_balance": "preserve_balance",
}
_META_OPERATIONS = {
    "verify_formation",
    "preserve_alternatives",
    "recheck_after_relationship_changes",
    "prioritize_special_structure_in_synthesis",
    "preserve_ordinary_diagnosis",
}
_OPPOSITES = {
    frozenset(("warm", "cool")),
    frozenset(("moisten", "dry")),
    frozenset(("support", "drain")),
    frozenset(("support", "restrain")),
}
_URGENCY_ORDER = {"high": 0, "medium": 1, "low": 2, "unspecified": 3}
_PRIORITY_ORDER = {
    "special_structure": 0,
    "urgent": 1,
    "cross_diagnostic": 2,
    "supporting": 3,
}


def _origin_for(module: str, operation: Mapping) -> str:
    """Return the independent source behind an operation, avoiding double counts."""

    if module != "pathology":
        return module
    bottleneck = operation.get("bottleneck_id")
    if bottleneck == "bottleneck:climate_extreme":
        return "climate"
    if bottleneck in {
        "bottleneck:unstable_root",
        "bottleneck:deficiency",
        "bottleneck:excess",
    }:
        return "strength"
    if bottleneck in {
        "bottleneck:conflict",
        "bottleneck:blocked_flow",
        "bottleneck:bound_element",
    }:
        return "relationships"
    return "pathology"


def _operation_urgency(module: str, operation: Mapping, diagnostic: DiagnosticResult) -> str:
    urgency = operation.get("urgency")
    if urgency in _URGENCY_ORDER:
        return urgency
    bottleneck_id = operation.get("bottleneck_id")
    if bottleneck_id:
        signal = next(
            (item for item in diagnostic.signals if item.get("id") == bottleneck_id),
            {},
        )
        if signal.get("urgency") in _URGENCY_ORDER:
            return signal["urgency"]
    return "unspecified"


def _raw_operations(diagnostics: Mapping[str, DiagnosticResult]) -> tuple[list[dict], list[dict]]:
    operations: list[dict] = []
    cautions: list[dict] = []
    for module, diagnostic in diagnostics.items():
        for item in diagnostic.recommended_operations:
            name = item.get("operation")
            if not name or name in _META_OPERATIONS:
                continue
            if item.get("when") is False or item.get("required") is False:
                continue
            purpose = _PURPOSES.get(name, name)
            record = {
                "operation": purpose,
                "source_operation": name,
                "source_module": module,
                "evidence_origin": _origin_for(module, item),
                "urgency": _operation_urgency(module, item, diagnostic),
                "availability": item.get("availability"),
                "element": item.get("element"),
                "side_effects": list(item.get("side_effects", [])),
                "evidence_ids": list(diagnostic.evidence_ids),
            }
            operations.append(record)

        for item in diagnostic.recommended_operations:
            name = item.get("operation")
            if name not in _META_OPERATIONS:
                continue
            if item.get("when") is False or item.get("required") is False:
                continue
            cautions.append({
                "operation": name,
                "reason": "diagnostic_follow_up",
                "source_modules": [module],
                "evidence_ids": list(diagnostic.evidence_ids),
            })

    strength = diagnostics.get("strength")
    if strength and strength.status != "insufficient":
        if strength.conclusion in {"weak", "extremely_weak"}:
            operations.append({
                "operation": "support",
                "source_operation": "strength_support_direction",
                "source_module": "strength",
                "evidence_origin": "strength",
                "urgency": "medium" if strength.conclusion == "extremely_weak" else "low",
                "availability": None,
                "element": None,
                "side_effects": [],
                "evidence_ids": list(strength.evidence_ids),
            })
        elif strength.conclusion in {"strong", "extremely_strong"}:
            operations.append({
                "operation": "drain",
                "source_operation": "strength_drain_direction",
                "source_module": "strength",
                "evidence_origin": "strength",
                "urgency": "medium" if strength.conclusion == "extremely_strong" else "low",
                "availability": None,
                "element": None,
                "side_effects": [],
                "evidence_ids": list(strength.evidence_ids),
            })
    return operations, cautions


def _group_operations(raw: list[dict]) -> list[dict]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for item in raw:
        grouped[item["operation"]].append(item)

    results = []
    for operation, items in grouped.items():
        urgency = min(
            (item["urgency"] for item in items),
            key=lambda value: _URGENCY_ORDER[value],
        )
        origins = sorted({item["evidence_origin"] for item in items})
        if operation == "preserve_special_structure":
            priority_reason = "special_structure"
        elif urgency == "high":
            priority_reason = "urgent"
        elif len(origins) > 1:
            priority_reason = "cross_diagnostic"
        else:
            priority_reason = "supporting"
        results.append({
            "operation": operation,
            "priority_reason": priority_reason,
            "urgency": urgency,
            "source_operations": sorted({item["source_operation"] for item in items}),
            "source_modules": sorted({item["source_module"] for item in items}),
            "independent_evidence_sources": origins,
            "elements": sorted({item["element"] for item in items if item["element"]}),
            "availability_states": sorted({
                item["availability"] for item in items if item["availability"]
            }),
            "side_effects": sorted({
                effect for item in items for effect in item["side_effects"]
            }),
            "evidence_ids": sorted({
                evidence_id for item in items for evidence_id in item["evidence_ids"]
            }),
        })
    return sorted(
        results,
        key=lambda item: (
            _PRIORITY_ORDER[item["priority_reason"]],
            _URGENCY_ORDER[item["urgency"]],
            item["operation"],
        ),
    )


def _established_special(diagnostic: DiagnosticResult | None) -> str | None:
    if diagnostic is None or diagnostic.status != "completed":
        return None
    if diagnostic.conclusion in {
        None,
        "ordinary_structure_preferred",
        "special_structure_possible",
        "multiple_special_structure_candidates",
    }:
        return None
    return diagnostic.conclusion


def _apply_special_precedence(
    raw: list[dict],
    cautions: list[dict],
    special: DiagnosticResult | None,
) -> tuple[list[dict], list[dict], list[dict]]:
    conflicts = []
    established = _established_special(special)
    if not established or special is None:
        if special and special.status == "conditional":
            cautions.append({
                "operation": "verify_special_structure",
                "reason": "special_structure_is_conditional",
                "source_modules": ["special_structure"],
                "evidence_ids": list(special.evidence_ids),
            })
        return raw, cautions, conflicts

    raw.append({
        "operation": "preserve_special_structure",
        "source_operation": "special_structure_precedence",
        "source_module": "special_structure",
        "evidence_origin": "special_structure",
        "urgency": "high",
        "availability": None,
        "element": None,
        "side_effects": [],
        "evidence_ids": list(special.evidence_ids),
    })
    blocked_purpose = "support" if established.startswith("follow_") else (
        "drain" if established.startswith("dominant_") else None
    )
    if blocked_purpose:
        kept = []
        for item in raw:
            if item["operation"] != blocked_purpose:
                kept.append(item)
                continue
            cautions.append({
                "operation": blocked_purpose,
                "reason": "may_break_established_special_structure",
                "special_structure": established,
                "source_modules": [item["source_module"]],
                "evidence_ids": item["evidence_ids"],
            })
        if len(kept) != len(raw):
            conflicts.append({
                "type": "special_structure_precedence",
                "operations": ["preserve_special_structure", blocked_purpose],
                "resolution": "prioritize_established_special_structure",
                "special_structure": established,
            })
        raw = kept
    return raw, cautions, conflicts


def _resolve_directional_conflicts(
    operations: list[dict],
    cautions: list[dict],
) -> tuple[list[dict], list[dict], list[dict]]:
    by_name = {item["operation"]: item for item in operations}
    conflicts = []
    moved = set()
    for pair in _OPPOSITES:
        if not pair.issubset(by_name):
            continue
        left_name, right_name = sorted(pair)
        left = by_name[left_name]
        right = by_name[right_name]
        left_rank = _URGENCY_ORDER[left["urgency"]]
        right_rank = _URGENCY_ORDER[right["urgency"]]
        if left_rank < right_rank:
            preferred, deferred = left, right
            resolution = "prioritize_more_urgent"
            moved.add(deferred["operation"])
        elif right_rank < left_rank:
            preferred, deferred = right, left
            resolution = "prioritize_more_urgent"
            moved.add(deferred["operation"])
        else:
            preferred = None
            resolution = "preserve_as_unresolved"
            moved.update(pair)
        conflicts.append({
            "type": "directional_conflict",
            "operations": [left_name, right_name],
            "resolution": resolution,
            "preferred_operation": preferred["operation"] if preferred else None,
            "source_modules": sorted(set(left["source_modules"] + right["source_modules"])),
            "evidence_ids": sorted(set(left["evidence_ids"] + right["evidence_ids"])),
        })

    favorable = [item for item in operations if item["operation"] not in moved]
    for operation in operations:
        if operation["operation"] not in moved:
            continue
        cautions.append({
            **operation,
            "reason": "directional_conflict_requires_context",
        })
    return favorable, cautions, conflicts


def synthesize_diagnostics(
    diagnostics: Mapping[str, DiagnosticResult],
) -> tuple[SynthesisResult, list[Evidence]]:
    """Combine diagnostics without scores, fixed weights, or majority voting."""

    missing = [module for module in _REQUIRED_MODULES if module not in diagnostics]
    insufficient = [
        module
        for module in _REQUIRED_MODULES
        if module in diagnostics and diagnostics[module].status in {"insufficient", "failed"}
    ]
    conditional = [
        module
        for module in _REQUIRED_MODULES
        if module in diagnostics and diagnostics[module].status == "conditional"
    ]

    raw, cautions = _raw_operations(diagnostics)
    raw, cautions, special_conflicts = _apply_special_precedence(
        raw, cautions, diagnostics.get("special_structure")
    )
    grouped = _group_operations(raw)
    favorable, cautions, directional_conflicts = _resolve_directional_conflicts(
        grouped, cautions
    )
    diagnostic_conflicts = special_conflicts + directional_conflicts
    if missing or insufficient:
        diagnostic_conflicts.append({
            "type": "incomplete_diagnostics",
            "missing_modules": missing,
            "insufficient_modules": insufficient,
            "resolution": "preserve_partial_result",
        })

    special = diagnostics.get("special_structure")
    structure = diagnostics.get("structure")
    strength = diagnostics.get("strength")
    climate = diagnostics.get("climate")
    established_special = _established_special(special)
    overall_structure = {
        "ordinary": structure.conclusion if structure else None,
        "ordinary_status": structure.status if structure else "missing",
        "special": special.conclusion if special else None,
        "special_status": special.status if special else "missing",
        "special_precedence": bool(established_special),
        "ordinary_alternative_preserved": not bool(established_special) or bool(diagnostic_conflicts),
    }
    climate_state = {
        "state": climate.conclusion if climate else None,
        "status": climate.status if climate else "missing",
        "urgent_operations": [
            item["operation"] for item in favorable if item["urgency"] == "high"
        ],
    }

    unresolved_conflicts = [
        item
        for item in diagnostic_conflicts
        if item.get("resolution") in {"preserve_as_unresolved", "preserve_partial_result"}
    ]
    directional_conflicts_present = any(
        item.get("type") == "directional_conflict" for item in diagnostic_conflicts
    )
    if missing or insufficient:
        confidence = ConfidenceLevel.UNDETERMINED
        summary = "일부 독립 진단이 부족해 사용 가능한 결과만 보존한 부분 종합"
    elif conditional or unresolved_conflicts or directional_conflicts_present:
        confidence = ConfidenceLevel.LOW
        summary = "진단 간 조건과 충돌을 보존하며 우선 작용을 정리한 조건부 종합"
    elif established_special:
        confidence = ConfidenceLevel.HIGH
        summary = (
            "확정 특수구조를 우선하고 나머지 진단의 부작용을 "
            "교차 확인한 종합"
        )
    else:
        confidence = ConfidenceLevel.MEDIUM
        summary = "긴급성과 독립 근거의 공통 방향에 따라 작용 목적을 정리한 종합"

    source_evidence_ids = sorted({
        evidence_id
        for diagnostic in diagnostics.values()
        for evidence_id in diagnostic.evidence_ids
    })
    evidence_id = "evidence:synthesis:diagnostic-priority"
    evidence = Evidence(
        id=evidence_id,
        layer=EvidenceLayer.JUDGMENT,
        source_module=SYNTHESIS_ENGINE_VERSION,
        rule_code=SYNTHESIS_PRIORITY_VERSION,
        description="특수구조·긴급성·독립 근거·충돌 순서로 여섯 진단을 종합",
        source_values={
            "required_modules": list(_REQUIRED_MODULES),
            "missing_modules": missing,
            "insufficient_modules": insufficient,
            "conditional_modules": conditional,
            "favorable_operations": favorable,
            "caution_operations": cautions,
            "diagnostic_conflicts": diagnostic_conflicts,
            "fixed_weight_used": False,
            "score_sum_used": False,
            "majority_vote_used": False,
        },
        supports=["synthesis:overall_direction"],
        reliability=confidence,
    )
    return (
        SynthesisResult(
            overall_structure=overall_structure,
            strength_state=strength.conclusion if strength else None,
            climate_state=climate_state,
            favorable_operations=favorable,
            caution_operations=cautions,
            diagnostic_conflicts=diagnostic_conflicts,
            summary=summary,
            evidence_ids=source_evidence_ids + [evidence_id],
            confidence=confidence,
        ),
        [evidence],
    )
