"""Cross-chart shensha facts used by relationship services.

This module only detects whether a documented positional rule is present and
how close it is to the two day pillars.  It does not turn a shensha into a
standalone relationship verdict.
"""

from __future__ import annotations

from collections.abc import Mapping

from app.engine.core.models import PillarFact


WONJIN_PAIRS = {frozenset(pair) for pair in ("子未", "丑午", "寅酉", "卯申", "辰亥", "巳戌")}

PEACH_BLOSSOM_TARGET = {
    "申": "酉", "子": "酉", "辰": "酉",
    "寅": "卯", "午": "卯", "戌": "卯",
    "巳": "午", "酉": "午", "丑": "午",
    "亥": "子", "卯": "子", "未": "子",
}


def _importance(left_position: str, right_position: str) -> int:
    if left_position == right_position == "day":
        return 3
    if "day" in {left_position, right_position}:
        return 2
    return 1


def calculate_relationship_shensha(
    left_pillars: Mapping[str, PillarFact | None],
    right_pillars: Mapping[str, PillarFact | None],
) -> list[dict]:
    """Detect modern Korean wonjin and classical hamji/peach cross-signals."""

    left = [(key, pillar) for key, pillar in left_pillars.items() if pillar]
    right = [(key, pillar) for key, pillar in right_pillars.items() if pillar]
    found = []

    for left_key, left_pillar in left:
        for right_key, right_pillar in right:
            if frozenset((left_pillar.branch, right_pillar.branch)) in WONJIN_PAIRS:
                found.append({
                    "kind": "원진살",
                    "left": left_key,
                    "right": right_key,
                    "symbols": left_pillar.branch + right_pillar.branch,
                    "importance": _importance(left_key, right_key),
                    "meaning": "가까운 관계에서 말하지 않은 서운함과 원망이 쌓이기 쉬운 신호",
                    "rule_code": "relationship-wonjin-modern-korean-v1",
                })

    seen = set()
    for owner, source_pillars, target_pillars in (
        ("left", left, right),
        ("right", right, left),
    ):
        for basis_key, basis_pillar in source_pillars:
            if basis_key not in {"year", "day"}:
                continue
            target = PEACH_BLOSSOM_TARGET[basis_pillar.branch]
            for match_key, match_pillar in target_pillars:
                if match_pillar.branch != target:
                    continue
                left_key, right_key = ((basis_key, match_key) if owner == "left" else (match_key, basis_key))
                dedupe = (owner, basis_key, match_key, basis_pillar.branch, target)
                if dedupe in seen:
                    continue
                seen.add(dedupe)
                found.append({
                    "kind": "도화살",
                    "left": left_key,
                    "right": right_key,
                    "symbols": basis_pillar.branch + "→" + target,
                    "importance": _importance(left_key, right_key),
                    "meaning": "상대에게 매력과 관심이 쉽게 활성화될 수 있는 신호",
                    "rule_code": "relationship-peach-blossom-hamji-v1",
                })

    return sorted(found, key=lambda item: (-item["importance"], item["kind"], item["symbols"]))
