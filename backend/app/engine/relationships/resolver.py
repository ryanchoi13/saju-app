"""Conservative v1 resolver for natal relationship candidates."""

from __future__ import annotations

from collections.abc import Mapping

from app.engine.constants import ZHI_WUXING
from app.engine.facts.ten_gods import get_ten_god
from app.engine.relationships.functions import describe_function_targets
from app.engine.relationships.assessment import assess_natal_functions, REFERENCE_ONLY_TYPES
from app.engine.relationships.transformation import assess_transformations
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


RELATIONSHIP_RESOLVER_VERSION = "relationship-resolver-v6-scoped-transformation"
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


def _flanking_stem_partners(candidate: RelationshipCandidate, other: RelationshipCandidate) -> bool:
    """Narrow positional contention rule, not a winner or function-loss verdict.

    Ziping Zhenquan Pingzhu, section 5: two 壬 immediately flank 丁.
    Separated partners do not satisfy this rule; no rule for their winner is inferred.
    """
    if candidate.type != RelationshipCandidateType.STEM_COMBINATION or other.type != candidate.type:
        return False
    if candidate.id == other.id or not (_is_adjacent(candidate) and _is_adjacent(other)):
        return False
    shared = _member_keys(candidate) & _member_keys(other)
    if len(shared) != 1:
        return False
    center = _PILLAR_ORDER.get(next(iter(shared))[1])
    partners = [m for c in (candidate, other) for m in c.members
                if (m.position, m.pillar) not in shared]
    return (center is not None and len(partners) == 2
            and partners[0].symbol == partners[1].symbol
            and {_PILLAR_ORDER.get(m.pillar) for m in partners} == {center - 1, center + 1})


def resolve_relationships(
    candidates: RelationshipCandidates,
    pillars: Mapping[str, PillarFact | None],
    roots: RootFacts,
    exposed_stems: ExposedStemFacts,
) -> tuple[list[RelationshipResult], list[Evidence]]:
    """Resolve candidate state while preserving uncertainty and evidence.

    Pair conversion and day-master structure classification have separate
    scopes. Neither is a completed prescription or overall valence judgment.
    """

    rooted_pillars = {item.stem_pillar for item in roots.items}
    exposed_pillars = {item.visible_pillar for item in exposed_stems.items}
    month_branch = pillars.get("month").branch if pillars.get("month") is not None else None
    results: list[RelationshipResult] = []
    evidence: list[Evidence] = []

    for candidate in candidates.items:
        member_keys = _member_keys(candidate)
        overlaps = [
            other.id
            for other in candidates.items
            if other.id != candidate.id
            and member_keys & _member_keys(other)
        ]
        adjacent = _is_adjacent(candidate)
        is_stem_combination = candidate.type == RelationshipCandidateType.STEM_COMBINATION
        # Shared input is context, not proof of competing effects.
        competitors = [other.id for other in candidates.items
                       if _flanking_stem_partners(candidate, other)]
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

        if is_stem_combination and competitors:
            action_status = "competing"
            reasons.append("동일한 두 합 상대가 공유 천간의 바로 양옆에 있어 위치상 경쟁 조건을 충족함")
            confidence = ConfidenceLevel.MEDIUM
        elif [r for r in candidates.items if r.id in overlaps and r.type.value not in REFERENCE_ONLY_TYPES]:
            action_status = "conditional"
            reasons.append("구성원을 공유하는 관계가 있으나 작용의 경쟁 여부는 미확정임")
            confidence = ConfidenceLevel.LOW
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
        function_targets = describe_function_targets(candidate.type.value,
            [m.model_dump(mode="json") for m in candidate.members], pillars, roots)
        function_assessments = []
        if is_stem_combination:
            day = pillars.get("day")
            includes_day = any(member.pillar == "day" for member in candidate.members)
            for member in candidate.members:
                member_roots = [root.model_dump(mode="json") for root in roots.items
                                if root.stem_pillar == member.pillar]
                function_assessments.append({
                    "pillar": member.pillar,
                    "stem": member.symbol,
                    "role_to_day_master": ("day_master" if member.pillar == "day" else
                        get_ten_god(day.stem, member.symbol).value if day else None),
                    "root_connections": member_roots,
                    "function_state": "undetermined",
                    "scope": "day_master_combination" if includes_day else "other_stems_combination",
                    "reasons": [
                        "합의 존재만으로 역할 유지나 제약을 확정하지 않음",
                        "통근의 존재와 실제 작용 능력은 별도 판단함",
                    ] + (["일간과의 합에는 다른 천간끼리 합하는 규칙을 그대로 적용하지 않음"]
                         if includes_day else []),
                    "evidence_ids": [evidence_id],
                })
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
                    "overlapping_candidate_ids": overlaps,
                    "competition_rule": ("immediate-identical-partners-flanking-v1"
                        if is_stem_combination and competitors else None),
                    "member_function_assessments": function_assessments,
                    "function_targets": function_targets,
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
                overlapping_relationship_ids=overlaps,
                member_function_assessments=function_assessments,
                function_targets=function_targets,
                reasons=reasons,
                evidence_ids=[evidence_id],
                confidence=confidence,
            )
        )

    evidence.extend(assess_natal_functions(results, pillars, roots))
    evidence.extend(assess_transformations(results, pillars, roots))
    return results, evidence
