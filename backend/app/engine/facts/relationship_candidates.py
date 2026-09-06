"""Detect natal stem/branch relationship candidates without resolving effects."""

from __future__ import annotations

from collections.abc import Mapping
from itertools import combinations

from app.engine.constants import GAN_WUXING
from app.engine.core.models import (
    PillarFact,
    RelationshipCandidate,
    RelationshipCandidateMember,
    RelationshipCandidates,
    RelationshipCandidateType,
)


RELATIONSHIP_CANDIDATE_RULE_VERSION = "relationship-candidates-v1"
_CONTROLS = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}
_STEM_COMBINATIONS = {frozenset(pair): element for pair, element in {
    "甲己": "土", "乙庚": "金", "丙辛": "水", "丁壬": "木", "戊癸": "火"
}.items()}
_SIX_COMBINATIONS = {frozenset(pair) for pair in ("子丑", "寅亥", "卯戌", "辰酉", "巳申", "午未")}
_CLASHES = {frozenset(pair) for pair in ("子午", "丑未", "寅申", "卯酉", "辰戌", "巳亥")}
_HARMS = {frozenset(pair) for pair in ("子未", "丑午", "寅巳", "卯辰", "申亥", "酉戌")}
_BREAKS = {frozenset(pair) for pair in ("子酉", "丑辰", "寅亥", "卯午", "巳申", "未戌")}
_HALF_COMBINATIONS = {
    frozenset(pair): element for pair, element in {
        "申子": "水", "子辰": "水", "亥卯": "木", "卯未": "木",
        "寅午": "火", "午戌": "火", "巳酉": "金", "酉丑": "金",
    }.items()
}
_THREE_COMBINATIONS = {
    frozenset(group): element for group, element in {
        "申子辰": "水", "亥卯未": "木", "寅午戌": "火", "巳酉丑": "金"
    }.items()
}
_DIRECTIONAL_COMBINATIONS = {
    frozenset(group): element for group, element in {
        "亥子丑": "水", "寅卯辰": "木", "巳午未": "火", "申酉戌": "金"
    }.items()
}
_PAIR_PUNISHMENTS = {frozenset(pair) for pair in ("子卯", "寅巳", "巳申", "申寅", "丑戌", "戌未", "未丑")}
_SELF_PUNISHMENTS = frozenset("辰午酉亥")


def _member(pillar: str, position: str, symbol: str) -> RelationshipCandidateMember:
    return RelationshipCandidateMember(pillar=pillar, position=position, symbol=symbol)


def _candidate(kind, members, rule_code, target_element=None):
    key = "-".join(f"{item.pillar}:{item.symbol}" for item in members)
    return RelationshipCandidate(
        id=f"{kind.value}:{key}", type=kind, members=members,
        target_element=target_element, rule_code=rule_code,
    )


def calculate_relationship_candidates(
    pillars: Mapping[str, PillarFact | None],
) -> RelationshipCandidates:
    """Return observable candidates only; activation belongs to the resolver."""

    available = [(name, pillar) for name, pillar in pillars.items() if pillar is not None]
    items: list[RelationshipCandidate] = []

    for (left_name, left), (right_name, right) in combinations(available, 2):
        stem_pair = frozenset((left.stem, right.stem))
        stem_members = [_member(left_name, "visible_stem", left.stem), _member(right_name, "visible_stem", right.stem)]
        if stem_pair in _STEM_COMBINATIONS:
            items.append(_candidate(RelationshipCandidateType.STEM_COMBINATION, stem_members, "stem-combination", _STEM_COMBINATIONS[stem_pair]))
        left_element, right_element = GAN_WUXING[left.stem], GAN_WUXING[right.stem]
        if _CONTROLS[left_element] == right_element or _CONTROLS[right_element] == left_element:
            items.append(_candidate(RelationshipCandidateType.STEM_CONTROL, stem_members, "stem-control"))

        branch_pair = frozenset((left.branch, right.branch))
        branch_members = [_member(left_name, "branch", left.branch), _member(right_name, "branch", right.branch)]
        for table, kind, code in (
            (_SIX_COMBINATIONS, RelationshipCandidateType.BRANCH_SIX_COMBINATION, "branch-six-combination"),
            (_CLASHES, RelationshipCandidateType.BRANCH_CLASH, "branch-clash"),
            (_HARMS, RelationshipCandidateType.BRANCH_HARM, "branch-harm"),
            (_BREAKS, RelationshipCandidateType.BRANCH_BREAK, "branch-break"),
            (_PAIR_PUNISHMENTS, RelationshipCandidateType.BRANCH_PUNISHMENT, "branch-punishment"),
        ):
            if branch_pair in table:
                items.append(_candidate(kind, branch_members, code))
        if branch_pair in _HALF_COMBINATIONS:
            items.append(_candidate(RelationshipCandidateType.BRANCH_HALF_COMBINATION, branch_members, "branch-half-combination", _HALF_COMBINATIONS[branch_pair]))
        if left.branch == right.branch and left.branch in _SELF_PUNISHMENTS:
            items.append(_candidate(RelationshipCandidateType.BRANCH_PUNISHMENT, branch_members, "branch-self-punishment"))

    for selected in combinations(available, 3):
        branch_set = frozenset(pillar.branch for _, pillar in selected)
        members = [_member(name, "branch", pillar.branch) for name, pillar in selected]
        if branch_set in _THREE_COMBINATIONS:
            items.append(_candidate(RelationshipCandidateType.BRANCH_THREE_COMBINATION, members, "branch-three-combination", _THREE_COMBINATIONS[branch_set]))
        if branch_set in _DIRECTIONAL_COMBINATIONS:
            items.append(_candidate(RelationshipCandidateType.BRANCH_DIRECTIONAL_COMBINATION, members, "branch-directional-combination", _DIRECTIONAL_COMBINATIONS[branch_set]))

    return RelationshipCandidates(items=items, rule_version=RELATIONSHIP_CANDIDATE_RULE_VERSION)
