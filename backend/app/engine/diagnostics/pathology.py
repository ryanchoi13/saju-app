"""Structural bottleneck (病) and resolving operation (藥) diagnosis.

The terms pathology and remedy are Myeongri structure concepts here. This
module does not infer diseases, accidents, lifespan, or medical conditions.
"""

from __future__ import annotations

from collections.abc import Sequence
from app.engine.relationships.assessment import is_reference_only

from app.engine.core.models import (
    ConfidenceLevel,
    DiagnosticResult,
    Evidence,
    EvidenceLayer,
    RelationshipResult,
)


PATHOLOGY_DIAGNOSTIC_VERSION = "pathology-diagnostic-v4-scoped-role-judgments"
PATHOLOGY_PRIORITY_VERSION = "pathology-priority-v2-review"
_URGENCY_ORDER = {"high": 0, "medium": 1, "low": 2}
_TYPE_ORDER = {
    "structural_damage": 0,
    "climate_extreme": 1,
    "conflict": 2,
    "blocked_flow": 3,
    "bound_element": 4,
    "unstable_root": 5,
    "deficiency": 6,
    "excess": 7,
    "structural_review": 8,
    "relationship_review": 9,
}


def _candidate(kind: str, urgency: str, basis: list[str], remedies: list[dict]) -> dict:
    return {
        "id": f"bottleneck:{kind}",
        "type": kind,
        "urgency": urgency,
        "basis": basis,
        "remedies": remedies,
        "health_interpretation": False,
    }


def diagnose_pathology(
    structure: DiagnosticResult,
    strength: DiagnosticResult,
    climate: DiagnosticResult,
    relationships: Sequence[RelationshipResult],
) -> tuple[DiagnosticResult, list[Evidence]]:
    """Preserve multiple structural bottlenecks and remedy side effects."""

    if any(item.status == "insufficient" for item in (structure, strength, climate)):
        return (
            DiagnosticResult(
                module="pathology", status="insufficient",
                summary="선행 독립 진단 정보가 부족해 병약 후보를 만들 수 없음",
                confidence=ConfidenceLevel.UNDETERMINED,
            ),
            [],
        )

    candidates: list[dict] = []
    if structure.status == "conditional" and structure.counter_evidence:
        candidates.append(_candidate(
            "structural_review", "low", list(structure.counter_evidence),
            [{
                "operation": "verify_formation",
                "side_effects": ["구조가 미확정이라는 사실만으로 손상이나 복구 필요를 추론하지 않음"],
            }],
        ))

    climate_high = [
        item for item in climate.recommended_operations if item.get("urgency") == "high"
    ]
    if climate_high:
        candidates.append(_candidate(
            "climate_extreme", "high",
            [f"월령 기준 {item.get('operation')} 후보; 개인별 필요·실효 판단을 함께 확인" for item in climate_high],
            [{
                "operation": item.get("operation"),
                "element": item.get("element"),
                "availability": item.get("availability"),
                "assessment_status": item.get("assessment_status"),
                "unresolved_requirements": list(item.get("unresolved_requirements", [])),
                "side_effects": ["신강·신약 방향과 충돌하는지 종합 단계에서 확인"],
            } for item in climate_high],
        ))

    # A relation's occurrence/action label does not establish damaged function.
    # See interpretation-evidence-criteria.md R04/R06 and 滴天髓闡微 通關.
    # Preserve facts for review without prescribing removal or restoration.
    relation_reviews = [
        item for item in relationships
        if item.action_status not in {"inactive", "resolved"}
        and not is_reference_only(item)
        and item.type in {
            "branch_clash", "branch_punishment", "branch_harm", "branch_break",
            "stem_control", "stem_combination",
        }
    ]
    if relation_reviews:
        review = _candidate(
            "relationship_review", "low",
            [f"작용의 대상과 효과를 확인할 관계 {item.id}" for item in relation_reviews],
            [{
                "operation": "verify_relationship_effect",
                "side_effects": ["관계의 존재·경쟁만으로 손상이나 해소 필요를 추론하지 않음"],
            }],
        )
        review["relationship_observations"] = [{
            "id": item.id,
            "type": item.type,
            "action_status": item.action_status,
            "members": item.members,
            "member_function_assessments": item.member_function_assessments,
            "function_targets": item.function_targets,
            "role_assessment": item.effect_assessment,
            # Function reduction does not establish harmful overall valence.
            "effect": "undetermined",
        } for item in relation_reviews]
        candidates.append(review)

    rooting_signal = next(
        (item for item in strength.signals if item.get("step") == "rooting"), {}
    )
    if strength.conclusion in {"weak", "extremely_weak"} and not rooting_signal.get("root_count"):
        candidates.append(_candidate(
            "unstable_root", "high" if strength.conclusion == "extremely_weak" else "medium",
            ["일간의 통근이 확인되지 않음", f"강약 진단: {strength.conclusion}"],
            [{
                "operation": "stabilize_root_or_support",
                "side_effects": ["특수구조 가능성이 있으면 일반 생조 처방을 보류"],
            }],
        ))
    if strength.conclusion == "extremely_weak":
        candidates.append(_candidate(
            "deficiency", "high", ["강약 진단이 극약 구간임"],
            [{
                "operation": "restore_supporting_capacity",
                "side_effects": ["종격 후보일 경우 보강 방향이 반대가 될 수 있음"],
            }],
        ))
    elif strength.conclusion == "extremely_strong":
        candidates.append(_candidate(
            "excess", "medium", ["강약 진단이 극왕 구간임"],
            [{
                "operation": "moderate_excess_force",
                "side_effects": ["전왕격 후보일 경우 설기·제어 방향을 재검토"],
            }],
        ))

    candidates.sort(key=lambda item: (_URGENCY_ORDER[item["urgency"]], _TYPE_ORDER[item["type"]]))
    for index, item in enumerate(candidates):
        item["role_in_diagnosis"] = "primary" if index == 0 else "secondary"

    primary = candidates[0]["type"] if candidates else "no_critical_bottleneck"
    conditional_inputs = [
        item.module for item in (structure, strength, climate) if item.status == "conditional"
    ]
    status = "conditional" if conditional_inputs or relation_reviews else "completed"
    confidence = (
        ConfidenceLevel.LOW if conditional_inputs or relation_reviews
        else ConfidenceLevel.MEDIUM if candidates
        else ConfidenceLevel.UNDETERMINED
    )
    evidence_id = "evidence:pathology:bottleneck-remedy"
    evidence = Evidence(
        id=evidence_id,
        layer=EvidenceLayer.JUDGMENT,
        source_module=PATHOLOGY_DIAGNOSTIC_VERSION,
        rule_code=PATHOLOGY_PRIORITY_VERSION,
        description="독립 진단과 관계 작용에서 구조적 병목과 해결 작용을 분리한 판정",
        source_values={
            "candidates": candidates,
            "conditional_input_modules": conditional_inputs,
            "medical_inference_performed": False,
            "fixed_score_used": False,
            "relationship_occurrence_is_not_damage": True,
        },
        supports=[f"pathology:{primary}"],
        reliability=confidence,
    )
    return (
        DiagnosticResult(
            module="pathology", status=status, conclusion=primary,
            summary="질병 예측 없이 원국의 구조적 병목과 해결 작용을 분리함",
            signals=candidates,
            recommended_operations=[
                {"bottleneck_id": item["id"], **remedy}
                for item in candidates for remedy in item["remedies"]
            ],
            counter_evidence=[
                "후속 특수구조·통관 진단에 따라 해결 작용이 변경될 수 있음"
            ] if candidates else [],
            confidence=confidence,
            evidence_ids=[evidence_id],
        ),
        [evidence],
    )
