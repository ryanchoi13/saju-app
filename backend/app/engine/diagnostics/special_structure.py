"""Conservative detection of follow, dominant, and transformation structures."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from app.engine.constants import GAN_WUXING, ZHI_WUXING
from app.engine.core.models import (
    ConfidenceLevel,
    DiagnosticResult,
    ElementInventory,
    Evidence,
    EvidenceLayer,
    HiddenStemRole,
    PillarFact,
    RelationshipResult,
    RootFacts,
    TenGod,
    TenGodFacts,
    TransformationStatus,
)


SPECIAL_STRUCTURE_DIAGNOSTIC_VERSION = "special-structure-diagnostic-v3-scoped-classification"
SPECIAL_STRUCTURE_RULE_VERSION = "special-structure-conservative-v1"

_SUPPORTING_GODS = {
    TenGod.PEER,
    TenGod.ROB_WEALTH,
    TenGod.DIRECT_RESOURCE,
    TenGod.INDIRECT_RESOURCE,
}
_FOLLOW_FAMILIES = {
    TenGod.EATING_GOD: "follow_output",
    TenGod.HURTING_OFFICER: "follow_output",
    TenGod.DIRECT_WEALTH: "follow_wealth",
    TenGod.INDIRECT_WEALTH: "follow_wealth",
    TenGod.DIRECT_OFFICER: "follow_officer",
    TenGod.SEVEN_KILLINGS: "follow_officer",
}
_DOMINANT_SUBTYPES = {
    "木": "dominant_wood",
    "火": "dominant_fire",
    "土": "dominant_earth",
    "金": "dominant_metal",
    "水": "dominant_water",
}
_UNSTABLE_RELATIONSHIP_STATES = {"blocked", "competing"}


def _visible_gods(ten_gods: TenGodFacts) -> set[TenGod]:
    return {
        item.ten_god
        for item in ten_gods.visible
        if item.pillar != "day" and item.ten_god is not TenGod.DAY_MASTER
    }


def _touches_day_or_month(relation: RelationshipResult) -> bool:
    return any(member.get("pillar") in {"day", "month"} for member in relation.members)


def _element_supply(element: str, inventory: ElementInventory, roots: RootFacts) -> dict:
    occurrences = [item for item in inventory.occurrences if item.element == element]
    visible_pillars = {
        item.pillar for item in occurrences if item.position == "visible_stem"
    }
    rooted_visible = {
        item.stem_pillar
        for item in roots.items
        if item.element == element and item.stem_pillar in visible_pillars
    }
    if rooted_visible:
        availability = "visible_and_rooted"
    elif visible_pillars:
        availability = "visible"
    elif occurrences:
        availability = "present"
    else:
        availability = "absent"
    return {
        "element": element,
        "availability": availability,
        "visible_pillars": sorted(visible_pillars),
        "rooted_visible_pillars": sorted(rooted_visible),
    }


def _follow_candidate(
    day_roots: list,
    ten_gods: TenGodFacts,
    strength: DiagnosticResult,
    unstable_ids: list[str],
) -> dict:
    visible = _visible_gods(ten_gods)
    visible_support = sorted(god.value for god in visible & _SUPPORTING_GODS)
    hidden_main_support = sorted({
        item.ten_god.value
        for item in ten_gods.hidden
        if item.hidden_role is HiddenStemRole.MAIN and item.ten_god in _SUPPORTING_GODS
    })
    families = sorted({_FOLLOW_FAMILIES[god] for god in visible if god in _FOLLOW_FAMILIES})

    supports = []
    breakers = []
    if strength.conclusion == "extremely_weak":
        supports.append("강약 진단이 극약 구간임")
    else:
        breakers.append("강약 진단이 극약 구간이 아님")
    if not day_roots:
        supports.append("일간의 통근이 확인되지 않음")
    else:
        breakers.append("일간의 통근이 존재함")
    if not visible_support:
        supports.append("천간에 일간 생조 세력이 드러나지 않음")
    else:
        breakers.append("천간에 일간 생조 세력이 존재함")
    if hidden_main_support:
        breakers.append("지지 본기에 일간 생조 세력이 존재함")
    if len(families) == 1:
        supports.append("천간의 종속 방향이 하나의 십성 계열로 모임")
    elif len(families) > 1:
        breakers.append("천간의 종속 방향이 복수 십성 계열로 갈림")
    else:
        breakers.append("따를 대상이 되는 천간 십성 계열이 확인되지 않음")
    if unstable_ids:
        breakers.append("일주 또는 월주 관계가 경쟁·방해 상태임")

    core_formed = (
        strength.conclusion == "extremely_weak"
        and not day_roots
        and not visible_support
        and not hidden_main_support
        and len(families) == 1
    )
    if core_formed and not unstable_ids and strength.status == "completed":
        formation_status = "established"
    elif strength.conclusion == "extremely_weak" and not day_roots:
        formation_status = "conditional"
    else:
        formation_status = "not_established"
    return {
        "type": "follow_structure",
        "subtype": families[0] if len(families) == 1 else "mixed_follow",
        "formation_status": formation_status,
        "supporting_conditions": supports,
        "breaking_conditions": breakers,
        "visible_follow_families": families,
        "visible_supporting_ten_gods": visible_support,
        "hidden_main_supporting_ten_gods": hidden_main_support,
    }


def _dominant_candidate(
    day_element: str,
    day_roots: list,
    ten_gods: TenGodFacts,
    strength: DiagnosticResult,
    unstable_ids: list[str],
) -> dict:
    visible = _visible_gods(ten_gods)
    visible_drain = sorted(god.value for god in visible - _SUPPORTING_GODS)
    main_month_root = any(
        item.branch_pillar == "month" and item.hidden_role is HiddenStemRole.MAIN
        for item in day_roots
    )
    supports = []
    breakers = []
    if strength.conclusion == "extremely_strong":
        supports.append("강약 진단이 극왕 구간임")
    else:
        breakers.append("강약 진단이 극왕 구간이 아님")
    if day_roots:
        supports.append("일간이 지지에 통근함")
    else:
        breakers.append("일간의 통근이 확인되지 않음")
    if main_month_root:
        supports.append("월지 본기에 일간의 뿌리가 있음")
    else:
        breakers.append("월지 본기의 전왕 지지가 확인되지 않음")
    if visible_drain:
        breakers.append("천간에 설기·재성·관성 계열이 존재함")
    else:
        supports.append("천간의 기세가 비겁·인성 계열로 모임")
    if unstable_ids:
        breakers.append("일주 또는 월주 관계가 경쟁·방해 상태임")

    core_formed = (
        strength.conclusion == "extremely_strong"
        and bool(day_roots)
        and main_month_root
        and not visible_drain
    )
    if core_formed and not unstable_ids and strength.status == "completed":
        formation_status = "established"
    elif strength.conclusion == "extremely_strong" and day_roots:
        formation_status = "conditional"
    else:
        formation_status = "not_established"
    return {
        "type": "dominant_structure",
        "subtype": _DOMINANT_SUBTYPES[day_element],
        "formation_status": formation_status,
        "supporting_conditions": supports,
        "breaking_conditions": breakers,
        "visible_draining_ten_gods": visible_drain,
        "main_month_root": main_month_root,
    }


def _transformation_candidates(
    day_element: str,
    month_element: str,
    day_roots: list,
    inventory: ElementInventory,
    roots: RootFacts,
    relationships: Sequence[RelationshipResult],
) -> list[dict]:
    results = []
    for relation in relationships:
        if relation.type != "stem_combination" or relation.transformation is None:
            continue
        if not any(
            member.get("pillar") == "day" and member.get("position") == "visible_stem"
            for member in relation.members
        ):
            continue

        target = relation.transformation.target_element
        supply = _element_supply(target, inventory, roots)
        assessment = relation.transformation.assessment
        if (relation.transformation.scope == 'day_master_structure'
                and relation.transformation.kind in {'true', 'fake'}
                and assessment.get('classification_status') == 'established'):
            results.append({
                'type': 'transformation_structure',
                'subtype': f'{relation.transformation.kind}_transform_to_{target}',
                'formation_status': 'conditional', 'classification_status': 'established',
                'transformation_kind': relation.transformation.kind,
                'relationship_id': relation.id, 'target_element': target,
                'target_supply': supply, 'source_assessment': assessment,
                'prescription_status': 'unresolved',
                'evidence_ids': list(relation.evidence_ids),
                'supporting_conditions': ['선행 원국 판정에서 일간이 참여하는 변화의 종류를 구별함'],
                'breaking_conditions': ['변화 종류의 판정과 세력·조절 방향의 판정은 별도임'],
            })
            continue

        supports = ["일간이 천간합의 구성원임"]
        breakers = []
        if month_element == target:
            supports.append("월지 오행이 합화 목표 오행과 일치함")
        else:
            breakers.append("월지 오행이 합화 목표 오행을 지지하지 않음")
        if supply["availability"] == "visible_and_rooted":
            supports.append("합화 목표 오행이 천간에 드러나고 통근함")
        elif supply["availability"] == "visible":
            supports.append("합화 목표 오행이 천간에 드러남")
        else:
            breakers.append("합화 목표 오행이 천간에 드러나 통근하지 못함")
        if day_roots:
            breakers.append("원래 일간 오행의 통근이 남아 있음")
        else:
            supports.append("원래 일간 오행의 통근이 확인되지 않음")
        if relation.action_status in _UNSTABLE_RELATIONSHIP_STATES or relation.competing_relationship_ids:
            breakers.append("천간합이 다른 관계와 경쟁하거나 방해받음")
        if relation.transformation.status.value in {"possible", "not_established"}:
            breakers.append("선행 관계 판정에서 합화 조건이 충분하지 않음")

        core_formed = (
            relation.action_status in {"active", "resolved"}
            and relation.transformation.status is TransformationStatus.ESTABLISHED
            and month_element == target
            and supply["availability"] == "visible_and_rooted"
            and not day_roots
            and not relation.competing_relationship_ids
        )
        if relation.transformation.status is TransformationStatus.NOT_ESTABLISHED:
            formation_status = "not_established"
        elif core_formed:
            formation_status = "established"
        elif relation.action_status != "blocked" and target != day_element:
            formation_status = "conditional"
        else:
            formation_status = "not_established"
        results.append({
            "type": "transformation_structure",
            "subtype": f"transform_to_{target}",
            "formation_status": formation_status,
            "relationship_id": relation.id,
            "target_element": target,
            "target_supply": supply,
            "supporting_conditions": supports,
            "breaking_conditions": breakers,
        })
    return results


def diagnose_special_structure(
    day_master: str,
    pillars: Mapping[str, PillarFact | None],
    inventory: ElementInventory,
    roots: RootFacts,
    ten_gods: TenGodFacts,
    relationships: Sequence[RelationshipResult],
    strength: DiagnosticResult,
) -> tuple[DiagnosticResult, list[Evidence]]:
    """Detect special structures while preserving ordinary alternatives."""

    month = pillars.get("month")
    if day_master not in GAN_WUXING or month is None or strength.status == "insufficient":
        return (
            DiagnosticResult(
                module="special_structure",
                status="insufficient",
                summary="일간·월주 또는 강약 진단 정보가 없어 특수구조를 진단할 수 없음",
                confidence=ConfidenceLevel.UNDETERMINED,
            ),
            [],
        )

    day_element = GAN_WUXING[day_master]
    month_element = ZHI_WUXING[month.branch]
    day_roots = [item for item in roots.items if item.stem_pillar == "day"]
    unstable_ids = [
        item.id
        for item in relationships
        if item.action_status in _UNSTABLE_RELATIONSHIP_STATES and _touches_day_or_month(item)
    ]
    signals = [
        _follow_candidate(day_roots, ten_gods, strength, unstable_ids),
        _dominant_candidate(day_element, day_roots, ten_gods, strength, unstable_ids),
        *_transformation_candidates(
            day_element, month_element, day_roots, inventory, roots, relationships
        ),
    ]

    established = [item for item in signals if item["formation_status"] == "established"]
    conditional = [item for item in signals if item["formation_status"] == "conditional"]
    if len(established) == 1:
        conclusion = established[0]["subtype"]
        status = "completed"
        confidence = ConfidenceLevel.HIGH
    elif len(established) > 1:
        conclusion = "multiple_special_structure_candidates"
        status = "conditional"
        confidence = ConfidenceLevel.LOW
    elif conditional:
        classified = [item for item in conditional if item.get('classification_status') == 'established']
        conclusion = classified[0]['subtype'] if len(classified) == 1 else "special_structure_possible"
        status = "conditional"
        confidence = ConfidenceLevel.LOW
    else:
        conclusion = "ordinary_structure_preferred"
        status = "completed"
        confidence = ConfidenceLevel.MEDIUM

    counter_evidence = sorted({
        reason
        for item in established + conditional
        for reason in item["breaking_conditions"]
    })
    evidence_id = "evidence:special-structure:conservative-detection"
    evidence = Evidence(
        id=evidence_id,
        layer=EvidenceLayer.JUDGMENT,
        source_module=SPECIAL_STRUCTURE_DIAGNOSTIC_VERSION,
        rule_code=SPECIAL_STRUCTURE_RULE_VERSION,
        description="종격·전왕격·화격의 성립과 파괴 조건을 일반 구조와 분리해 보수적으로 판정",
        source_values={
            "day_element": day_element,
            "month_element": month_element,
            "candidates": signals,
            "unstable_relationship_ids": unstable_ids,
            "fixed_score_used": False,
        },
        supports=[f"special_structure:{conclusion}"],
        reliability=confidence,
    )
    operations = [{
        "operation": "prioritize_special_structure_in_synthesis",
        "required": bool(established),
    }]
    if status == "conditional" or not established:
        operations.append({
            "operation": "preserve_ordinary_diagnosis",
            "required": True,
        })
    return (
        DiagnosticResult(
            module="special_structure",
            status=status,
            conclusion=conclusion,
            summary="특수구조를 고정 점수 없이 성립·파괴 조건과 일반격 병행 가능성으로 판정함",
            signals=signals,
            recommended_operations=operations,
            counter_evidence=counter_evidence,
            confidence=confidence,
            evidence_ids=[evidence_id],
        ),
        [evidence],
    )
