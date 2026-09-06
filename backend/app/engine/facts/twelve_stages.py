"""Traditional twelve-stage facts using the yin-stem reverse convention."""

from __future__ import annotations

from collections.abc import Mapping

from app.engine.constants import GAN_WUXING
from app.engine.core.models import PillarFact, TwelveStage, TwelveStageFact, TwelveStageFacts


TWELVE_STAGE_RULE_VERSION = "twelve-stages-v1"
TWELVE_STAGE_CONVENTION = "traditional-yin-reverse"

_STAGES = (
    TwelveStage.BIRTH,
    TwelveStage.BATH,
    TwelveStage.CROWN_BELT,
    TwelveStage.OFFICIAL,
    TwelveStage.PROSPERITY,
    TwelveStage.DECLINE,
    TwelveStage.SICKNESS,
    TwelveStage.DEATH,
    TwelveStage.TOMB,
    TwelveStage.EXTINCTION,
    TwelveStage.EMBRYO,
    TwelveStage.NOURISHMENT,
)

_BRANCH_ORDER_BY_STEM = {
    "甲": "亥子丑寅卯辰巳午未申酉戌",
    "乙": "午巳辰卯寅丑子亥戌酉申未",
    "丙": "寅卯辰巳午未申酉戌亥子丑",
    "丁": "酉申未午巳辰卯寅丑子亥戌",
    "戊": "寅卯辰巳午未申酉戌亥子丑",
    "己": "酉申未午巳辰卯寅丑子亥戌",
    "庚": "巳午未申酉戌亥子丑寅卯辰",
    "辛": "子亥戌酉申未午巳辰卯寅丑",
    "壬": "申酉戌亥子丑寅卯辰巳午未",
    "癸": "卯寅丑子亥戌酉申未午巳辰",
}

_TABLE = {
    stem: dict(zip(branches, _STAGES))
    for stem, branches in _BRANCH_ORDER_BY_STEM.items()
}


def get_twelve_stage(day_master: str, branch: str) -> TwelveStage:
    """Return one stage without converting it into a strength judgment."""

    if day_master not in GAN_WUXING:
        raise ValueError(f"지원하지 않는 천간입니다: {day_master}")
    try:
        return _TABLE[day_master][branch]
    except KeyError as exc:
        raise ValueError(f"지원하지 않는 지지입니다: {branch}") from exc


def calculate_twelve_stages(
    day_master: str,
    pillars: Mapping[str, PillarFact | None],
) -> TwelveStageFacts:
    """Calculate stages for available natal branches only."""

    if day_master not in GAN_WUXING:
        raise ValueError(f"지원하지 않는 천간입니다: {day_master}")
    return TwelveStageFacts(
        day_master=day_master,
        items=[
            TwelveStageFact(
                pillar=pillar_name,
                branch=pillar.branch,
                stage=get_twelve_stage(day_master, pillar.branch),
            )
            for pillar_name, pillar in pillars.items()
            if pillar is not None
        ],
        convention=TWELVE_STAGE_CONVENTION,
        rule_version=TWELVE_STAGE_RULE_VERSION,
    )
