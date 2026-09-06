from unittest import TestCase

from app.engine.constants import GAN_WUXING
from app.engine.core.models import PillarFact, TwelveStage
from app.engine.facts.twelve_stages import (
    TWELVE_STAGE_CONVENTION,
    TWELVE_STAGE_RULE_VERSION,
    calculate_twelve_stages,
    get_twelve_stage,
)


STAGE_VALUES = (
    "birth bath crown_belt official prosperity decline sickness death "
    "tomb extinction embryo nourishment"
).split()
BRANCH_ORDER_BY_STEM = {
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


def _pillar(branch: str) -> PillarFact:
    return PillarFact(
        stem="甲",
        branch=branch,
        ganji=f"甲{branch}",
        stem_element=GAN_WUXING["甲"],
        stem_yin_yang="yang",
        branch_element="木",
        branch_yin_yang="yang",
    )


class TwelveStageTests(TestCase):
    def test_all_one_hundred_twenty_stem_branch_pairs(self):
        for stem, branches in BRANCH_ORDER_BY_STEM.items():
            for branch, expected in zip(branches, STAGE_VALUES):
                with self.subTest(stem=stem, branch=branch):
                    self.assertEqual(get_twelve_stage(stem, branch).value, expected)

    def test_yin_stems_follow_reverse_sequence(self):
        self.assertIs(get_twelve_stage("乙", "午"), TwelveStage.BIRTH)
        self.assertIs(get_twelve_stage("乙", "巳"), TwelveStage.BATH)
        self.assertIs(get_twelve_stage("癸", "辰"), TwelveStage.NOURISHMENT)

    def test_convention_and_rule_version_are_preserved(self):
        pillars = {"year": _pillar("午"), "day": _pillar("辰"), "hour": None}
        result = calculate_twelve_stages("甲", pillars)
        self.assertEqual(result.convention, TWELVE_STAGE_CONVENTION)
        self.assertEqual(result.rule_version, TWELVE_STAGE_RULE_VERSION)
        self.assertEqual([item.pillar for item in result.items], ["year", "day"])

    def test_unknown_hour_is_not_fabricated(self):
        result = calculate_twelve_stages("甲", {"day": _pillar("辰"), "hour": None})
        self.assertNotIn("hour", {item.pillar for item in result.items})

    def test_invalid_values_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "지원하지 않는 천간"):
            get_twelve_stage("X", "子")
        with self.assertRaisesRegex(ValueError, "지원하지 않는 지지"):
            get_twelve_stage("甲", "X")
