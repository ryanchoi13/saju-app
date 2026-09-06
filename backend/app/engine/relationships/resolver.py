"""Conservative v1 resolver for natal relationship candidates."""

from __future__ import annotations

from collections.abc import Mapping

from app.engine.constants import ZHI_WUXING
from app.engine.core.models import (
    ConfidenceLevel,
    Evidence,
    EvidenceLayer,
    ExposedStemFacts,
    PillarFact,
    RelationshipCandidate,
    RelationshipCandidates,
    RelationshipCandidateType,
    RelationshipResult,
    RootFacts,
    TransformationResult,
    TransformationStatus,
)


RELATIONSHIP_RESOLVER_VERSION = "relationship-resolver-v1"
_PILLAR_ORDER = {"year": 0, "month": 1, "day": 2, "hour": 3}
_COMBINATIONS = {
    RelationshipCandidateType.STEM_COMBINATION,
    RelationshipCandidateType.BRANCH_SIX_COMBINATION,
    RelationshipCandidateType.BRANCH_THREE_COMBINATION,
    RelationshipCandidateType.BRANCH_HALF_COMBINATION,
    RelationshipCandidateType.BRANCH_DIRECTIONAL_COMBINATION,
}
_COMPLETE_GROUPS = {
    RelationshipCandidateType.BRANCH_THREE_COMBINATION,
    RelationshipCandidateType.BRANCH_DIRECTIONAL_COMBINATION,
}
_DIRECT_INTERACTIONS = {
    RelationshipCandidateType.STEM_CONTROL,
    RelationshipCandidateType.BRANCH_CLASH,
    RelationshipCandidateType.BRANCH_PUNISHMENT,
    RelationshipCandidateType.BRANCH_HARM,
    RelationshipCandidateType.BRANCH_BREAK,
}


def _member_keys(candidate: RelationshipCandidate) -> set[tuple[str, str]]:
    return {(member.position, member.pillar) for member in candidate.members}


def _is_adjacent(candidate: RelationshipCandidate) -> bool:
    positions = [_PILLAR_ORDER.get(member.pillar) for member in candidate.members]
    if any(position is None for position in positions):
        return False
    ordered = sorted(set(positions))
    return len(ordered) > 1 and all(right - left == 1 for left, right in zip(ordered, ordered[1:]))


def resolve_relationships(
    candidates: RelationshipCandidates,
    pillars: Mapping[str, PillarFact | None],
    roots: RootFacts,
    exposed_stems: ExposedStemFacts,
) -> tuple[list[RelationshipResult], list[Evidence]]:
    """Resolve candidate state while preserving uncertainty and evidence.

    V1 never declares a transformation established. That stronger conclusion
    requires the later structure and strength diagnostics.
    """

    rooted_pillars = {item.stem_pillar for item in roots.items}
    exposed_pillars = {item.visible_pillar for item in exposed_stems.items}
    month_branch = pillars.get("month").branch if pillars.get("month") is not None else None
    results: list[RelationshipResult] = []
    evidence: list[Evidence] = []

    for candidate in candidates.items:
        member_keys = _member_keys(candidate)
        competitors = [
            other.id
            for other in candidates.items
            if other.id != candidate.id
            and member_keys & _member_keys(other)
            and other.type != candidate.type
        ]
        adjacent = _is_adjacent(candidate)
        supported = any(
            member.pillar in rooted_pillars or member.pillar in exposed_pillars
            for member in candidate.members
            if member.position == "visible_stem"
        )
        month_support = bool(
            candidate.target_element
            and month_branch
            and ZHI_WUXING.get(month_branch) == candidate.target_element
        )

        reasons = ["후보 구성원이 원국에 존재함"]
        if adjacent:
            reasons.append("인접한 주 사이의 관계임")
        if supported:
            reasons.append("관계 천간에 통근 또는 투간 연결이 있음")
        if month_support:
            reasons.append("월지 오행이 관계의 목표 오행과 같음")

        if competitors:
            action_status = "competing"
            reasons.append("동일 위치를 공유하는 다른 종류의 관계 후보가 있음")
            confidence = ConfidenceLevel.MEDIUM
        elif candidate.type in _COMPLETE_GROUPS and month_support:
            action_status = "active"
            confidence = ConfidenceLevel.HIGH
        elif candidate.type in _DIRECT_INTERACTIONS and adjacent:
            action_status = "active"
            confidence = ConfidenceLevel.MEDIUM
        else:
            action_status = "conditional"
            confidence = ConfidenceLevel.MEDIUM if adjacent or supported else ConfidenceLevel.LOW

        transformation = None
        if candidate.type in _COMBINATIONS and candidate.target_element:
            transformation_status = (
                TransformationStatus.CONDITIONAL
                if month_support or supported or competitors
                else TransformationStatus.POSSIBLE
            )
            transformation = TransformationResult(
                target_element=candidate.target_element,
                status=transformation_status,
                reasons=["합의 존재와 합화의 성립은 별도 판단함"],
            )

        evidence_id = f"evidence:{candidate.id}"
        evidence.append(
            Evidence(
                id=evidence_id,
                layer=EvidenceLayer.RULE,
                source_module=RELATIONSHIP_RESOLVER_VERSION,
                rule_code=candidate.rule_code,
                description="관계 후보의 위치·지원·경쟁 조건 판정",
                source_values={
                    "adjacent": adjacent,
                    "root_or_exposure_support": supported,
                    "month_element_support": month_support,
                    "competing_candidate_ids": competitors,
                },
                supports=[candidate.id],
                reliability=confidence,
            )
        )
        results.append(
            RelationshipResult(
                id=candidate.id,
                type=candidate.type.value,
                members=[member.model_dump(mode="json") for member in candidate.members],
                existence="confirmed",
                action_status=action_status,
                transformation=transformation,
                supporting_conditions=[reason for reason in reasons if "있음" in reason or "같음" in reason],
                competing_relationship_ids=competitors,
                reasons=reasons,
                evidence_ids=[evidence_id],
                confidence=confidence,
            )
        )

    return results, evidence
