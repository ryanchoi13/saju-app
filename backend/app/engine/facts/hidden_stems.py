"""Canonical hidden-stem facts for the twelve earthly branches.

This module records presence and traditional role only. It deliberately does
not assign force scores or decide whether a hidden stem is usable.
"""

from __future__ import annotations

from collections.abc import Mapping

from app.engine.constants import GAN_WUXING
from app.engine.core.models import (
    BranchHiddenStems,
    HiddenStemFact,
    HiddenStemRole,
    PillarFact,
)


HIDDEN_STEM_RULE_VERSION = "hidden-stems-v1"

_HIDDEN_STEM_TABLE: dict[str, tuple[tuple[str, HiddenStemRole], ...]] = {
    "子": (("癸", HiddenStemRole.MAIN),),
    "丑": (
        ("己", HiddenStemRole.MAIN),
        ("癸", HiddenStemRole.MIDDLE),
        ("辛", HiddenStemRole.RESIDUAL),
    ),
    "寅": (
        ("甲", HiddenStemRole.MAIN),
        ("丙", HiddenStemRole.MIDDLE),
        ("戊", HiddenStemRole.RESIDUAL),
    ),
    "卯": (("乙", HiddenStemRole.MAIN),),
    "辰": (
        ("戊", HiddenStemRole.MAIN),
        ("乙", HiddenStemRole.MIDDLE),
        ("癸", HiddenStemRole.RESIDUAL),
    ),
    "巳": (
        ("丙", HiddenStemRole.MAIN),
        ("戊", HiddenStemRole.MIDDLE),
        ("庚", HiddenStemRole.RESIDUAL),
    ),
    "午": (
        ("丁", HiddenStemRole.MAIN),
        ("己", HiddenStemRole.MIDDLE),
    ),
    "未": (
        ("己", HiddenStemRole.MAIN),
        ("丁", HiddenStemRole.MIDDLE),
        ("乙", HiddenStemRole.RESIDUAL),
    ),
    "申": (
        ("庚", HiddenStemRole.MAIN),
        ("壬", HiddenStemRole.MIDDLE),
        ("戊", HiddenStemRole.RESIDUAL),
    ),
    "酉": (("辛", HiddenStemRole.MAIN),),
    "戌": (
        ("戊", HiddenStemRole.MAIN),
        ("辛", HiddenStemRole.MIDDLE),
        ("丁", HiddenStemRole.RESIDUAL),
    ),
    "亥": (
        ("壬", HiddenStemRole.MAIN),
        ("甲", HiddenStemRole.MIDDLE),
    ),
}


def get_hidden_stems(branch: str) -> BranchHiddenStems:
    """Return versioned hidden-stem facts for one earthly branch."""

    try:
        entries = _HIDDEN_STEM_TABLE[branch]
    except KeyError as exc:
        raise ValueError(f"지원하지 않는 지지입니다: {branch}") from exc

    return BranchHiddenStems(
        branch=branch,
        stems=[
            HiddenStemFact(stem=stem, element=GAN_WUXING[stem], role=role)
            for stem, role in entries
        ],
        rule_version=HIDDEN_STEM_RULE_VERSION,
    )


def calculate_hidden_stems(
    pillars: Mapping[str, PillarFact | None],
) -> dict[str, BranchHiddenStems]:
    """Calculate hidden-stem facts for available natal pillars.

    Missing pillars, including an unknown hour pillar, remain absent instead of
    being replaced with a fabricated value.
    """

    return {
        pillar_name: get_hidden_stems(pillar.branch)
        for pillar_name, pillar in pillars.items()
        if pillar is not None
    }
