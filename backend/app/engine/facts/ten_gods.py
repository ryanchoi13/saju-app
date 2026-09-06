"""Ten-god facts derived from the day master and heavenly stems."""

from __future__ import annotations

from collections.abc import Mapping

from app.engine.constants import GAN_WUXING
from app.engine.core.models import (
    BranchHiddenStems,
    PillarFact,
    TenGod,
    TenGodFact,
    TenGodFacts,
)


TEN_GOD_RULE_VERSION = "ten-gods-v1"
_YANG_STEMS = frozenset({"甲", "丙", "戊", "庚", "壬"})
_GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
_CONTROLS = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}


def _validate_stem(stem: str) -> None:
    if stem not in GAN_WUXING:
        raise ValueError(f"지원하지 않는 천간입니다: {stem}")


def get_ten_god(day_master: str, target_stem: str) -> TenGod:
    """Return the ten-god relation of one stem to the day master."""

    _validate_stem(day_master)
    _validate_stem(target_stem)
    day_element = GAN_WUXING[day_master]
    target_element = GAN_WUXING[target_stem]
    same_polarity = (day_master in _YANG_STEMS) == (target_stem in _YANG_STEMS)

    if day_element == target_element:
        return TenGod.PEER if same_polarity else TenGod.ROB_WEALTH
    if _GENERATES[day_element] == target_element:
        return TenGod.EATING_GOD if same_polarity else TenGod.HURTING_OFFICER
    if _CONTROLS[day_element] == target_element:
        return TenGod.INDIRECT_WEALTH if same_polarity else TenGod.DIRECT_WEALTH
    if _CONTROLS[target_element] == day_element:
        return TenGod.SEVEN_KILLINGS if same_polarity else TenGod.DIRECT_OFFICER
    return TenGod.INDIRECT_RESOURCE if same_polarity else TenGod.DIRECT_RESOURCE


def calculate_ten_gods(
    day_master: str,
    pillars: Mapping[str, PillarFact | None],
    hidden_stems: Mapping[str, BranchHiddenStems],
) -> TenGodFacts:
    """Calculate visible and hidden ten-god facts for available pillars."""

    _validate_stem(day_master)
    visible: list[TenGodFact] = []
    hidden: list[TenGodFact] = []

    for pillar_name, pillar in pillars.items():
        if pillar is None:
            continue
        visible.append(
            TenGodFact(
                pillar=pillar_name,
                position="visible_stem",
                stem=pillar.stem,
                ten_god=(
                    TenGod.DAY_MASTER
                    if pillar_name == "day"
                    else get_ten_god(day_master, pillar.stem)
                ),
            )
        )

        branch_facts = hidden_stems.get(pillar_name)
        if branch_facts is None:
            continue
        for item in branch_facts.stems:
            hidden.append(
                TenGodFact(
                    pillar=pillar_name,
                    position="hidden_stem",
                    stem=item.stem,
                    ten_god=get_ten_god(day_master, item.stem),
                    hidden_role=item.role,
                )
            )

    return TenGodFacts(
        visible=visible,
        hidden=hidden,
        rule_version=TEN_GOD_RULE_VERSION,
    )
