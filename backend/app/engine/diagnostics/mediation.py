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


MEDIATION_DIAGNOSTIC_VERSION = "mediation-diagnostic-v3-path-context"
MEDIATION_RULE_VERSION = "control-generation-bridge-v2-observation-and-use"
_GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
_CONTROLS = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}
_PILLAR_ORDER = {"year": 0, "month": 1, "day": 2, "hour": 3}
_SOURCE = {
    "work": "滴天髓闡微",
    "chapter": "通神論 二十 通關",
    "commentator": "任鐵樵",
    "url": "https://zh.wikisource.org/zh-hant/滴天髓闡微",
    "scope": "natal_mediation_conditions",
}


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


def _touching_relationship_ids(pillar, position, relationships):
    # A hidden stem is carried by its branch. A stem interaction at the same
    # pillar is not itself a branch interaction or proof of root damage.
    member_position = "branch" if position == "hidden_stem" else position
    return sorted({
        relation.id for relation in relationships
        if any(member.get("pillar") == pillar and member.get("position") == member_position
               for member in relation.members)
    })


def _node_context(node, roots, relationships):
    contexts = []
    if node["position"] == "visible_stem":
        for root in roots.items:
            if root.stem_pillar != node["pillar"] or root.visible_stem != node["symbol"]:
                continue
            contexts.append({
                **root.model_dump(mode="json"),
                "related_relationship_ids": _touching_relationship_ids(
                    root.branch_pillar, "branch", relationships),
                "effectiveness": "undetermined",
            })
    return {
        **node,
        "relationship_ids": _touching_relationship_ids(
            node["pillar"], node["position"], relationships),
        "root_contexts": contexts,
    }


def _leg_context(start, end, inventory):
    start_index = _PILLAR_ORDER.get(start["pillar"])
    end_index = _PILLAR_ORDER.get(end["pillar"])
    between = []
    if start_index is not None and end_index is not None:
        left, right = sorted((start_index, end_index))
        between = [
            {"pillar": item.pillar, "symbol": item.symbol, "element": item.element}
            for item in inventory.occurrences
            if item.position == "visible_stem"
            and left < _PILLAR_ORDER.get(item.pillar, -1) < right
        ]
        between.sort(key=lambda item: _PILLAR_ORDER[item["pillar"]])
    return {
        "channel": ("visible_to_visible" if start["position"] == end["position"] == "visible_stem"
                    else "cross_visible_hidden"),
        "intervening_visible_stems": between,
        "position_known": start_index is not None and end_index is not None,
    }


def _potential_paths(conflict, controller, mediator, inventory, roots, relationships):
    """Record exposed/hidden carriers, placement and root context.

    Ren's 通關 commentary distinguishes exposure, hidden carriers, separation
    and intervening relationships. These are observed conditions, not automatic
    blockage or proof that an element ought to be recommended.
    """
    source = next(m for m in conflict.members if GAN_WUXING[m['symbol']] == controller)
    target = next(m for m in conflict.members if m != source)
    paths = []
    for occurrence in inventory.occurrences:
        if occurrence.element != mediator or occurrence.position not in {'visible_stem', 'hidden_stem'}:
            continue
        middle = {'pillar': occurrence.pillar, 'symbol': occurrence.symbol,
                  'position': occurrence.position}
        if occurrence.hidden_role is not None:
            middle['hidden_role'] = occurrence.hidden_role.value
        middle_context = _node_context(middle, roots, relationships)
        source_index = _PILLAR_ORDER.get(source['pillar'])
        middle_index = _PILLAR_ORDER.get(middle['pillar'])
        target_index = _PILLAR_ORDER.get(target['pillar'])
        position_known = all(index is not None for index in (source_index, middle_index, target_index))
        between = (min(source_index, target_index) < middle_index < max(source_index, target_index)
                   if position_known else None)
        paths.append({
            'source': dict(source),
            'mediator': middle,
            'target': dict(target),
            'generation_legs': [[source['symbol'], occurrence.symbol],
                                [occurrence.symbol, target['symbol']]],
            'mediator_relationship_ids': middle_context['relationship_ids'],
            'node_contexts': {
                'source': _node_context(source, roots, relationships),
                'mediator': middle_context,
                'target': _node_context(target, roots, relationships),
            },
            'placement': {
                'same_visible_channel': occurrence.position == 'visible_stem',
                'mediator_between_endpoints': between,
                'legs': [_leg_context(source, middle, inventory),
                         _leg_context(middle, target, inventory)],
            },
            'effectiveness': 'undetermined',
        })
    return paths


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
        if state["availability"] == "absent":
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
            "potential_paths": _potential_paths(conflict, controller, mediator, inventory, roots, relationships),
            "effectiveness_reason": "중재 요소의 존재·투출·통근만으로 실제 중재 성립을 확정하지 않음",
            "recommendation_status": "conditional",
            "unresolved_requirements": [
                "상극이 실제로 불리한 역할을 하는지 확인",
                "중재 요소가 해당 경로에서 기능할 수 있는지 확인",
                "원국 전체에서 중재 작용이 필요한지 확인",
            ],
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
            "source": _SOURCE,
            "observation_completion_is_not_recommendation_approval": True,
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
                "assessment_status": item["recommendation_status"],
                "unresolved_requirements": item["unresolved_requirements"],
            } for item in signals],
            counter_evidence=sorted(set(side_effects)),
            confidence=confidence,
            evidence_ids=[evidence_id],
        ),
        [evidence],
    )
