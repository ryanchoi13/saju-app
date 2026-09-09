"""Month-command based structure diagnosis with alternatives preserved."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from app.engine.relationships.assessment import is_reference_only

from app.engine.core.models import (
    BranchHiddenStems,
    ConfidenceLevel,
    DiagnosticResult,
    Evidence,
    EvidenceLayer,
    ExposedStemFacts,
    HiddenStemRole,
    PillarFact,
    RelationshipResult,
    RootFacts,
    TenGod,
    TenGodFacts,
)


STRUCTURE_DIAGNOSTIC_VERSION = "structure-diagnostic-v2-natal-observation-policy"
_ROLE_ORDER = {HiddenStemRole.MAIN: 0, HiddenStemRole.MIDDLE: 1, HiddenStemRole.RESIDUAL: 2}
_DISRUPTIVE_RELATIONSHIPS = {
    "branch_clash", "branch_punishment", "branch_harm", "branch_break"
}
_SUPPORT_SIGNALS = {
    TenGod.DIRECT_OFFICER: {TenGod.DIRECT_WEALTH, TenGod.INDIRECT_WEALTH, TenGod.DIRECT_RESOURCE, TenGod.INDIRECT_RESOURCE},
    TenGod.SEVEN_KILLINGS: {TenGod.EATING_GOD, TenGod.DIRECT_RESOURCE, TenGod.INDIRECT_RESOURCE},
    TenGod.DIRECT_WEALTH: {TenGod.EATING_GOD, TenGod.HURTING_OFFICER, TenGod.DIRECT_OFFICER},
    TenGod.INDIRECT_WEALTH: {TenGod.EATING_GOD, TenGod.HURTING_OFFICER, TenGod.SEVEN_KILLINGS},
    TenGod.DIRECT_RESOURCE: {TenGod.DIRECT_OFFICER, TenGod.SEVEN_KILLINGS},
    TenGod.INDIRECT_RESOURCE: {TenGod.DIRECT_OFFICER, TenGod.SEVEN_KILLINGS},
    TenGod.EATING_GOD: {TenGod.DIRECT_WEALTH, TenGod.INDIRECT_WEALTH},
    TenGod.HURTING_OFFICER: {TenGod.DIRECT_WEALTH, TenGod.INDIRECT_WEALTH},
}
_COUNTER_SIGNALS = {
    TenGod.DIRECT_OFFICER: {TenGod.HURTING_OFFICER, TenGod.SEVEN_KILLINGS},
    TenGod.SEVEN_KILLINGS: {TenGod.DIRECT_OFFICER},
    TenGod.DIRECT_WEALTH: {TenGod.PEER, TenGod.ROB_WEALTH},
    TenGod.INDIRECT_WEALTH: {TenGod.PEER, TenGod.ROB_WEALTH},
    TenGod.DIRECT_RESOURCE: {TenGod.DIRECT_WEALTH, TenGod.INDIRECT_WEALTH},
    TenGod.INDIRECT_RESOURCE: {TenGod.DIRECT_WEALTH, TenGod.INDIRECT_WEALTH},
    TenGod.EATING_GOD: {TenGod.INDIRECT_RESOURCE},
    TenGod.HURTING_OFFICER: {TenGod.DIRECT_OFFICER},
}


def _insufficient(reason: str) -> tuple[DiagnosticResult, list[Evidence]]:
    return (
        DiagnosticResult(
            module="structure", status="insufficient", summary=reason,
            confidence=ConfidenceLevel.UNDETERMINED,
        ),
        [],
    )


def diagnose_structure(
    pillars: Mapping[str, PillarFact | None],
    hidden_stems: Mapping[str, BranchHiddenStems],
    ten_gods: TenGodFacts,
    exposed_stems: ExposedStemFacts,
    roots: RootFacts,
    relationships: Sequence[RelationshipResult],
) -> tuple[DiagnosticResult, list[Evidence]]:
    """Diagnose ordinary structure candidates without handling special structures."""

    month = pillars.get("month")
    month_hidden = hidden_stems.get("month")
    if month is None or month_hidden is None:
        return _insufficient("월주 또는 월지 지장간 정보가 없어 구조를 진단할 수 없음")

    month_ten_gods = {
        (item.stem, item.hidden_role): item.ten_god
        for item in ten_gods.hidden
        if item.pillar == "month"
    }
    if not month_ten_gods:
        return _insufficient("월지 지장간의 십성 정보가 없음")

    exposed_by_stem: dict[str, list[str]] = {}
    for item in exposed_stems.items:
        if item.hidden_pillar == "month":
            exposed_by_stem.setdefault(item.stem, []).append(item.visible_pillar)

    rooted_visible = {item.stem_pillar for item in roots.items}
    present_ten_gods = {
        item.ten_god for item in ten_gods.visible + ten_gods.hidden
        if item.ten_god is not TenGod.DAY_MASTER
    }
    month_interference = [
        relation for relation in relationships
        if relation.type in _DISRUPTIVE_RELATIONSHIPS
        and not is_reference_only(relation)
        and relation.action_status in {"active", "competing", "conditional"}
        and any(member.get("pillar") == "month" and member.get("position") == "branch" for member in relation.members)
    ]

    candidates = []
    for hidden in sorted(month_hidden.stems, key=lambda item: _ROLE_ORDER[item.role]):
        ten_god = month_ten_gods.get((hidden.stem, hidden.role))
        if ten_god is None:
            continue
        exposed = sorted(set(exposed_by_stem.get(hidden.stem, [])))
        support = sorted(god.value for god in _SUPPORT_SIGNALS.get(ten_god, set()) & present_ten_gods)
        counters = sorted(god.value for god in _COUNTER_SIGNALS.get(ten_god, set()) & present_ten_gods)
        candidates.append({
            "ten_god": ten_god.value,
            "source_stem": hidden.stem,
            "source_role": hidden.role.value,
            "exposed_pillars": exposed,
            "exposed_and_rooted": any(pillar in rooted_visible for pillar in exposed),
            "supporting_ten_gods_present": support,
            "counter_ten_gods_present": counters,
        })

    if not candidates:
        return _insufficient("월지에서 구조 후보를 만들 수 없음")

    exposed_candidates = [candidate for candidate in candidates if candidate["exposed_pillars"]]
    primary = exposed_candidates[0] if exposed_candidates else candidates[0]
    for candidate in candidates:
        candidate["role_in_diagnosis"] = "primary" if candidate is primary else "alternative"

    counter_evidence = []
    if len(exposed_candidates) > 1:
        counter_evidence.append("월지의 복수 지장간이 천간에 드러나 대안 구조가 함께 존재함")
    if month_interference:
        counter_evidence.append("월지에 충 관계가 있어 해당 역할의 실제 변화를 추가 확인해야 함")
    counter_evidence.extend(
        f"{value} 구조에 대응하는 견제 십성 {counter}이 원국에 존재함"
        for value in [primary["ten_god"]]
        for counter in primary["counter_ten_gods_present"]
    )

    is_clear = bool(primary["exposed_pillars"]) and len(exposed_candidates) == 1 and not month_interference
    confidence = ConfidenceLevel.HIGH if is_clear and primary["source_role"] == "main" else (
        ConfidenceLevel.MEDIUM if primary["exposed_pillars"] else ConfidenceLevel.LOW
    )
    status = "completed" if is_clear else "conditional"
    evidence_id = "evidence:structure:month-command"
    evidence = Evidence(
        id=evidence_id,
        layer=EvidenceLayer.JUDGMENT,
        source_module=STRUCTURE_DIAGNOSTIC_VERSION,
        rule_code="month-command-candidate-selection",
        description="월지 지장간의 역할·투간·통근·관계 변화를 함께 본 구조 후보 판정",
        source_values={
            "month_branch": month.branch,
            "candidates": candidates,
            "month_interference_ids": [item.id for item in month_interference],
        },
        supports=[f"structure:{primary['ten_god']}"],
        reliability=confidence,
    )
    return (
        DiagnosticResult(
            module="structure",
            status=status,
            conclusion=primary["ten_god"],
            summary="월령 구조 후보를 투간과 관계 변화까지 교차 확인함",
            signals=candidates,
            recommended_operations=[
                {"operation": "verify_formation", "target": primary["ten_god"]},
                {"operation": "preserve_alternatives", "count": len(candidates) - 1},
            ],
            counter_evidence=counter_evidence,
            confidence=confidence,
            evidence_ids=[evidence_id],
        ),
        [evidence],
    )
