"""Translate core judgments into stable, non-narrative semantic tokens."""

from __future__ import annotations

from collections.abc import Sequence

from app.engine.core.models import (
    ActivatedState,
    ConfidenceLevel,
    Evidence,
    EvidenceLayer,
    RelationshipResult,
    SemanticState,
    ShenshaResult,
    SynthesisResult,
)


SEMANTIC_ENGINE_VERSION = "semantic-state-v1"

_TEN_GOD_TOPICS = {
    "day_master": "self_direction",
    "peer": "peers_and_independence",
    "rob_wealth": "competition_and_shared_resources",
    "eating_god": "creation_and_output",
    "hurting_officer": "expression_and_change",
    "direct_wealth": "managed_resources_and_results",
    "indirect_wealth": "variable_resources_and_opportunity",
    "direct_officer": "role_and_responsibility",
    "seven_killings": "pressure_and_decisive_action",
    "direct_resource": "learning_and_recovery",
    "indirect_resource": "insight_and_reframing",
}


def _elements(operations: Sequence[dict]) -> list[str]:
    return list(dict.fromkeys(
        element
        for operation in operations
        for element in operation.get("elements", [])
    ))


def build_semantic_state(
    synthesis: SynthesisResult,
    activated: ActivatedState | None = None,
    relationships: Sequence[RelationshipResult] = (),
    shensha: Sequence[ShenshaResult] = (),
) -> tuple[SemanticState, list[Evidence]]:
    """Build a renderer-neutral state; do not generate fortune prose or scores."""

    activated = activated or ActivatedState()
    favorable_operations = [
        item["operation"]
        for item in synthesis.favorable_operations
        if item.get("operation")
    ]
    caution_operations = [
        item["operation"]
        for item in synthesis.caution_operations
        if item.get("operation")
    ]
    interaction_ids = [
        item.id
        for item in relationships
        if item.action_status in {"active", "competing", "resolved"}
    ]
    interaction_ids.extend(
        item.get("relationship_id")
        for item in activated.relationship_changes
        if item.get("relationship_id")
    )
    topics = list(dict.fromkeys(
        _TEN_GOD_TOPICS[god]
        for god in activated.activated_ten_gods
        if god in _TEN_GOD_TOPICS
    ))
    active_shensha = [
        item.name for item in shensha if item.activation != "observed"
    ]
    evidence_id = "evidence:semantic:state-projection"
    evidence_ids = list(dict.fromkeys(
        list(synthesis.evidence_ids)
        + [evidence_id]
        + [eid for item in shensha for eid in item.evidence_ids]
    ))
    state = SemanticState(
        overall_flow=synthesis.summary,
        energy_direction=",".join(favorable_operations) if favorable_operations else None,
        favorable_elements=_elements(synthesis.favorable_operations),
        caution_elements=_elements(synthesis.caution_operations),
        activated_ten_gods=list(activated.activated_ten_gods),
        strongest_interactions=list(dict.fromkeys(interaction_ids)),
        opportunity_topics=list(dict.fromkeys(activated.opportunity_signals)),
        caution_topics=list(dict.fromkeys(activated.pressure_signals)),
        action_tendencies=favorable_operations,
        emotional_tendencies=[],
        indicators={
            "ordinary_structure": str(synthesis.overall_structure.get("ordinary")),
            "special_structure": str(synthesis.overall_structure.get("special")),
            "strength": str(synthesis.strength_state),
            "climate": str(synthesis.climate_state.get("state")),
            "activated_topics": ",".join(topics),
            "caution_operations": ",".join(caution_operations),
            "active_shensha_support": ",".join(active_shensha),
            "score_used": "false",
        },
        evidence_ids=evidence_ids,
        confidence=synthesis.confidence,
    )
    evidence = Evidence(
        id=evidence_id,
        layer=EvidenceLayer.TRANSLATION,
        source_module=SEMANTIC_ENGINE_VERSION,
        rule_code="renderer-neutral-projection-v1",
        description="종합판단과 활성 상태를 점수·운세 문구 없이 의미 토큰으로 투영",
        source_values={
            "favorable_operations": favorable_operations,
            "caution_operations": caution_operations,
            "activated_topics": topics,
            "active_shensha": active_shensha,
            "shensha_can_override_core": False,
            "score_used": False,
        },
        supports=["semantic_state"],
        reliability=synthesis.confidence,
    )
    return state, [evidence]
