"""Five-element mediation (通關) diagnosis for active controlling conflicts."""

from __future__ import annotations

from collections.abc import Sequence

from app.engine.constants import GAN_WUXING
from app.engine.core.models import (
    ConfidenceLevel,
    DiagnosticResult,
    ElementInventory,
    Evidence,
    EvidenceLayer,
    RelationshipResult,
    RootFacts,
)


MEDIATION_DIAGNOSTIC_VERSION = "mediation-diagnostic-v1"
MEDIATION_RULE_VERSION = "control-generation-bridge-v1"
_GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
_CONTROLS = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}


def _element_state(element: str, inventory: ElementInventory, roots: RootFacts) -> dict:
    occurrences = [item for item in inventory.occurrences if item.element == element]
    visible = {item.pillar for item in occurrences if item.position == "visible_stem"}
    rooted = {
        item.stem_pillar for item in roots.items
        if item.element == element and item.stem_pillar in visible
    }
    if rooted:
        availability = "visible_and_rooted"
    elif visible:
        availability = "visible"
    elif occurrences:
        availability = "present"
    else:
        availability = "absent"
    return {
        "availability": availability,
        "positions": sorted({f"{item.pillar}:{item.position}:{item.symbol}" for item in occurrences}),
        "rooted_visible_pillars": sorted(rooted),
    }


def _day_effect(day_element: str, mediator: str) -> str:
    if mediator == day_element:
        return "same_element_support"
    if _GENERATES[mediator] == day_element:
        return "generates_day_master"
    if _GENERATES[day_element] == mediator:
        return "drains_day_master"
    if _CONTROLS[mediator] == day_element:
        return "pressures_day_master"
    return "consumes_day_master"


def diagnose_mediation(
    day_master: str,
    inventory: ElementInventory,
    roots: RootFacts,
    relationships: Sequence[RelationshipResult],
    strength: DiagnosticResult,
    climate: DiagnosticResult,
) -> tuple[DiagnosticResult, list[Evidence]]:
    """Find a generating bridge between controller and controlled elements."""

    if day_master not in GAN_WUXING or strength.status == "insufficient" or climate.status == "insufficient":
        return (
            DiagnosticResult(
                module="mediation", status="insufficient",
                summary="일간 또는 선행 진단 정보가 부족해 통관을 진단할 수 없음",
                confidence=ConfidenceLevel.UNDETERMINED,
            ),
            [],
        )

    conflicts = [
        item for item in relationships
        if item.type == "stem_control"
        and item.action_status in {"active", "conditional", "competing"}
    ]
    signals: list[dict] = []
    for conflict in conflicts:
        elements = [GAN_WUXING.get(member.get("symbol")) for member in conflict.members]
        if len(elements) != 2 or None in elements:
            continue
        left, right = elements
        if _CONTROLS.get(left) == right:
            controller, controlled = left, right
        elif _CONTROLS.get(right) == left:
            controller, controlled = right, left
        else:
            continue
        mediator = _GENERATES[controller]
        state = _element_state(mediator, inventory, roots)
        if conflict.action_status == "active" and state["availability"] == "visible_and_rooted":
            mediation_status = "established"
        elif conflict.action_status == "active" and state["availability"] == "absent":
            mediation_status = "not_established"
        else:
            mediation_status = "conditional"
        signals.append({
            "conflict_id": conflict.id,
            "conflict_status": conflict.action_status,
            "controller_element": controller,
            "controlled_element": controlled,
            "mediator_element": mediator,
            "mediation_status": mediation_status,
            "mediator_supply": state,
            "day_master_effect": _day_effect(GAN_WUXING[day_master], mediator),
        })

    established = [item for item in signals if item["mediation_status"] == "established"]
    conditional = [item for item in signals if item["mediation_status"] == "conditional"]
    if established:
        conclusion = "mediation_available"
    elif conditional:
        conclusion = "mediation_conditional"
    elif signals:
        conclusion = "mediation_absent"
    else:
        conclusion = "no_controlling_conflict"

    side_effects = []
    for item in signals:
        if strength.conclusion == "extremely_strong" and item["day_master_effect"] in {
            "same_element_support", "generates_day_master"
        }:
            side_effects.append(f"{item['mediator_element']} 통관은 극왕 상태를 더 강화할 수 있음")
        if strength.conclusion == "extremely_weak" and item["day_master_effect"] in {
            "drains_day_master", "pressures_day_master", "consumes_day_master"
        }:
            side_effects.append(f"{item['mediator_element']} 통관은 극약 일간을 더 소모시킬 수 있음")

    climate_elements = {
        item.get("element") for item in climate.recommended_operations
        if item.get("urgency") == "high" and item.get("element")
    }
    for item in signals:
        if climate_elements and item["mediator_element"] not in climate_elements:
            side_effects.append("통관 요소가 긴급한 조후 작용과 일치하지 않아 병렬 검토가 필요함")

    status = "conditional" if conditional or any(
        item["conflict_status"] == "competing" for item in signals
    ) else "completed"
    confidence = (
        ConfidenceLevel.HIGH if established and not side_effects
        else ConfidenceLevel.LOW if status == "conditional"
        else ConfidenceLevel.MEDIUM
    )
    evidence_id = "evidence:mediation:control-bridge"
    evidence = Evidence(
        id=evidence_id,
        layer=EvidenceLayer.JUDGMENT,
        source_module=MEDIATION_DIAGNOSTIC_VERSION,
        rule_code=MEDIATION_RULE_VERSION,
        description="상극 관계 사이 생생 연결 오행과 실제 사용 가능성 판정",
        source_values={
            "signals": signals,
            "side_effects": side_effects,
            "fixed_score_used": False,
        },
        supports=[f"mediation:{conclusion}"],
        reliability=confidence,
    )
    return (
        DiagnosticResult(
            module="mediation", status=status, conclusion=conclusion,
            summary="상극 관계와 중재 오행의 노출·통근·부작용을 함께 확인함",
            signals=signals,
            recommended_operations=[{
                "operation": "mediate_control_conflict",
                "conflict_id": item["conflict_id"],
                "element": item["mediator_element"],
                "availability": item["mediator_supply"]["availability"],
            } for item in signals],
            counter_evidence=sorted(set(side_effects)),
            confidence=confidence,
            evidence_ids=[evidence_id],
        ),
        [evidence],
    )
