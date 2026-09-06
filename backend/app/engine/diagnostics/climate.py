"""Seasonal climate diagnosis kept independent from day-master strength."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from app.engine.core.models import (
    ConfidenceLevel,
    DiagnosticResult,
    ElementInventory,
    Evidence,
    EvidenceLayer,
    PillarFact,
    RelationshipResult,
    RootFacts,
)


CLIMATE_DIAGNOSTIC_VERSION = "climate-diagnostic-v1"
CLIMATE_BASELINE_VERSION = "seasonal-climate-baseline-v1"

_MONTH_CLIMATE = {
    "寅": ("cool", "balanced", "moderate"),
    "卯": ("mild", "balanced", "low"),
    "辰": ("mild", "wet", "moderate"),
    "巳": ("hot", "dry", "moderate"),
    "午": ("very_hot", "dry", "high"),
    "未": ("hot", "dry", "moderate"),
    "申": ("warm", "dry", "moderate"),
    "酉": ("cool", "dry", "moderate"),
    "戌": ("cool", "dry", "moderate"),
    "亥": ("cold", "wet", "high"),
    "子": ("very_cold", "wet", "high"),
    "丑": ("cold", "wet", "moderate"),
}


def _supply_state(
    element: str,
    inventory: ElementInventory,
    roots: RootFacts,
) -> dict[str, object]:
    occurrences = [item for item in inventory.occurrences if item.element == element]
    visible_pillars = {
        item.pillar for item in occurrences if item.position == "visible_stem"
    }
    rooted_visible = {
        item.stem_pillar for item in roots.items
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
        "positions": sorted(
            {f"{item.pillar}:{item.position}:{item.symbol}" for item in occurrences}
        ),
        "rooted_visible_pillars": sorted(rooted_visible),
    }


def diagnose_climate(
    pillars: Mapping[str, PillarFact | None],
    inventory: ElementInventory,
    roots: RootFacts,
    relationships: Sequence[RelationshipResult],
) -> tuple[DiagnosticResult, list[Evidence]]:
    """Diagnose cold/heat/dryness/wetness and required operations, not one yongshin."""

    month = pillars.get("month")
    if month is None or month.branch not in _MONTH_CLIMATE:
        return (
            DiagnosticResult(
                module="climate", status="insufficient",
                summary="월령 정보가 없어 조후 환경을 진단할 수 없음",
                confidence=ConfidenceLevel.UNDETERMINED,
            ),
            [],
        )

    temperature, moisture, baseline_urgency = _MONTH_CLIMATE[month.branch]
    operations: list[dict[str, object]] = []
    if temperature in {"cold", "very_cold", "cool"}:
        operations.append({"operation": "warming", **_supply_state("火", inventory, roots)})
    elif temperature in {"hot", "very_hot", "warm"}:
        operations.append({"operation": "cooling", **_supply_state("水", inventory, roots)})
    if moisture == "dry" and not any(item["operation"] == "cooling" for item in operations):
        operations.append({"operation": "moistening", **_supply_state("水", inventory, roots)})
    elif moisture == "wet":
        operations.append({"operation": "stabilizing", **_supply_state("土", inventory, roots)})

    unstable = [
        relation for relation in relationships
        if relation.action_status in {"competing", "blocked"}
        and any(member.get("pillar") == "month" for member in relation.members)
    ]
    missing_operations = [
        item["operation"] for item in operations if item["availability"] == "absent"
    ]
    available_operations = [
        item["operation"] for item in operations
        if item["availability"] in {"visible", "visible_and_rooted"}
    ]
    urgency = baseline_urgency
    if baseline_urgency == "high" and not missing_operations:
        urgency = "moderate"
    elif baseline_urgency == "moderate" and missing_operations:
        urgency = "high"

    conclusion = f"{temperature}_{moisture}"
    signals = [
        {
            "baseline_version": CLIMATE_BASELINE_VERSION,
            "month_branch": month.branch,
            "temperature": temperature,
            "moisture": moisture,
            "baseline_urgency": baseline_urgency,
        },
        {"operation_supplies": operations},
        {"relationship_change_ids": [item.id for item in unstable]},
    ]
    counter_evidence = []
    if available_operations:
        counter_evidence.append("필요한 조후 작용 일부가 천간에 드러나 있어 계절 극단을 완화할 수 있음")
    if unstable:
        counter_evidence.append("월주 관계의 경쟁·방해로 조절 요소의 사용 가능성이 달라질 수 있음")

    confidence = ConfidenceLevel.LOW if unstable else ConfidenceLevel.MEDIUM
    status = "conditional" if unstable else "completed"
    evidence_id = "evidence:climate:seasonal-environment"
    evidence = Evidence(
        id=evidence_id,
        layer=EvidenceLayer.JUDGMENT,
        source_module=CLIMATE_DIAGNOSTIC_VERSION,
        rule_code=CLIMATE_BASELINE_VERSION,
        description="월령 한난조습과 조절 요소의 존재·노출·통근을 분리한 조후 판정",
        source_values={
            "temperature": temperature,
            "moisture": moisture,
            "operations": operations,
            "urgency": urgency,
            "single_yongshin_selected": False,
        },
        supports=[f"climate:{conclusion}"],
        reliability=confidence,
    )
    return (
        DiagnosticResult(
            module="climate", status=status, conclusion=conclusion,
            summary="월령 환경과 실제 조절 가능성을 구분해 조후 상태를 판정함",
            signals=signals,
            recommended_operations=[
                {**item, "urgency": urgency} for item in operations
            ],
            counter_evidence=counter_evidence,
            confidence=confidence,
            evidence_ids=[evidence_id],
        ),
        [evidence],
    )
