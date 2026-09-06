"""Qualitative day-master strength diagnosis without a fixed score."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from app.engine.constants import GAN_WUXING, ZHI_WUXING
from app.engine.core.models import (
    ConfidenceLevel,
    DiagnosticResult,
    Evidence,
    EvidenceLayer,
    HiddenStemRole,
    PillarFact,
    RelationshipResult,
    RootFacts,
    StrengthState,
    TenGod,
    TenGodFacts,
)


STRENGTH_DIAGNOSTIC_VERSION = "strength-diagnostic-v1"
_GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
_CONTROLS = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}
_SUPPORTING_GODS = {
    TenGod.PEER, TenGod.ROB_WEALTH, TenGod.DIRECT_RESOURCE, TenGod.INDIRECT_RESOURCE
}
_DRAINING_GODS = {
    TenGod.EATING_GOD, TenGod.HURTING_OFFICER,
    TenGod.DIRECT_WEALTH, TenGod.INDIRECT_WEALTH,
    TenGod.DIRECT_OFFICER, TenGod.SEVEN_KILLINGS,
}


def _season_relation(day_element: str, month_element: str) -> str:
    if day_element == month_element:
        return "same_element"
    if _GENERATES[month_element] == day_element:
        return "month_generates_day"
    if _GENERATES[day_element] == month_element:
        return "day_generates_month"
    if _CONTROLS[month_element] == day_element:
        return "month_controls_day"
    return "day_controls_month"


def _touches_day_or_month(relation: RelationshipResult) -> bool:
    return any(member.get("pillar") in {"day", "month"} for member in relation.members)


def diagnose_strength(
    day_master: str,
    pillars: Mapping[str, PillarFact | None],
    roots: RootFacts,
    ten_gods: TenGodFacts,
    relationships: Sequence[RelationshipResult],
) -> tuple[DiagnosticResult, list[Evidence]]:
    """Apply ordered qualitative checks; never total them into a strength score."""

    month = pillars.get("month")
    if day_master not in GAN_WUXING or month is None:
        return (
            DiagnosticResult(
                module="strength", status="insufficient",
                summary="일간 또는 월주 정보가 없어 강약을 진단할 수 없음",
                confidence=ConfidenceLevel.UNDETERMINED,
            ),
            [],
        )

    day_element = GAN_WUXING[day_master]
    month_element = ZHI_WUXING[month.branch]
    season_relation = _season_relation(day_element, month_element)
    season_supportive = season_relation in {"same_element", "month_generates_day"}

    day_roots = [item for item in roots.items if item.stem_pillar == "day"]
    month_roots = [item for item in day_roots if item.branch_pillar == "month"]
    strong_month_root = any(item.hidden_role is HiddenStemRole.MAIN for item in month_roots)
    exact_main_month_root = any(
        item.hidden_role is HiddenStemRole.MAIN and item.exact_stem for item in month_roots
    )

    visible_gods = {
        item.ten_god for item in ten_gods.visible
        if item.pillar != "day" and item.ten_god is not TenGod.DAY_MASTER
    }
    visible_support = visible_gods & _SUPPORTING_GODS
    visible_drain = visible_gods & _DRAINING_GODS
    unstable_relations = [
        item for item in relationships
        if _touches_day_or_month(item) and item.action_status in {"competing", "blocked"}
    ]

    signals = [
        {"step": "season", "relation": season_relation, "supportive": season_supportive},
        {
            "step": "rooting", "root_count": len(day_roots),
            "month_root": bool(month_roots), "main_month_root": strong_month_root,
            "exact_main_month_root": exact_main_month_root,
        },
        {
            "step": "support", "visible_ten_gods": sorted(god.value for god in visible_support),
        },
        {
            "step": "drain_pressure", "visible_ten_gods": sorted(god.value for god in visible_drain),
        },
        {
            "step": "relationship_change",
            "unstable_relationship_ids": [item.id for item in unstable_relations],
        },
    ]

    if season_relation == "same_element" and exact_main_month_root and visible_support and not visible_drain:
        state = StrengthState.EXTREMELY_STRONG
    elif season_supportive and strong_month_root and visible_support:
        state = StrengthState.STRONG
    elif not season_supportive and not day_roots and not visible_support:
        state = StrengthState.EXTREMELY_WEAK
    elif not season_supportive and not (day_roots and visible_support):
        state = StrengthState.WEAK
    else:
        state = StrengthState.BALANCED

    counter_evidence = []
    if season_supportive and visible_drain:
        counter_evidence.append("득령 신호와 함께 설기·소모·압박 십성이 천간에 존재함")
    if not season_supportive and day_roots:
        counter_evidence.append("월령은 비우호적이지만 일간의 통근이 존재함")
    if not season_supportive and visible_support:
        counter_evidence.append("월령은 비우호적이지만 생조 십성이 천간에 존재함")
    if unstable_relations:
        counter_evidence.append("일주 또는 월주에 경쟁·방해 상태의 관계가 있어 결론이 변할 수 있음")

    mixed = bool(counter_evidence)
    status = "conditional" if unstable_relations else "completed"
    confidence = (
        ConfidenceLevel.LOW if unstable_relations
        else ConfidenceLevel.MEDIUM if mixed or state is StrengthState.BALANCED
        else ConfidenceLevel.HIGH
    )
    evidence_id = "evidence:strength:ordered-diagnosis"
    evidence = Evidence(
        id=evidence_id,
        layer=EvidenceLayer.JUDGMENT,
        source_module=STRENGTH_DIAGNOSTIC_VERSION,
        rule_code="season-root-support-drain-relationship-order",
        description="득령·통근·생조·극설소모·관계 변화 순서의 정성 강약 판정",
        source_values={"signals": signals, "fixed_score_used": False},
        supports=[f"strength:{state.value}"],
        reliability=confidence,
    )
    return (
        DiagnosticResult(
            module="strength", status=status, conclusion=state.value,
            summary="고정 점수 없이 순차 근거로 일간의 강약 구간을 판정함",
            signals=signals,
            recommended_operations=[
                {"operation": "preserve_balance", "when": state is StrengthState.BALANCED},
                {"operation": "recheck_after_relationship_changes", "required": bool(unstable_relations)},
            ],
            counter_evidence=counter_evidence,
            confidence=confidence,
            evidence_ids=[evidence_id],
        ),
        [evidence],
    )
