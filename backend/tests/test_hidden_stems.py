from unittest import TestCase

from app.engine.core.models import HiddenStemRole, PillarFact
from app.engine.facts.hidden_stems import (
    HIDDEN_STEM_RULE_VERSION,
    calculate_hidden_stems,
    get_hidden_stems,
)


EXPECTED_STEMS = {
    "子": [("癸", "main")],
    "丑": [("己", "main"), ("癸", "middle"), ("辛", "residual")],
    "寅": [("甲", "main"), ("丙", "middle"), ("戊", "residual")],
    "卯": [("乙", "main")],
    "辰": [("戊", "main"), ("乙", "middle"), ("癸", "residual")],
    "巳": [("丙", "main"), ("戊", "middle"), ("庚", "residual")],
    "午": [("丁", "main"), ("己", "middle")],
    "未": [("己", "main"), ("丁", "middle"), ("乙", "residual")],
    "申": [("庚", "main"), ("壬", "middle"), ("戊", "residual")],
    "酉": [("辛", "main")],
    "戌": [("戊", "main"), ("辛", "middle"), ("丁", "residual")],
    "亥": [("壬", "main"), ("甲", "middle")],
}


def _pillar(branch: str) -> PillarFact:
    return PillarFact(
        stem="甲",
        branch=branch,
        ganji=f"甲{branch}",
        stem_element="木",
        stem_yin_yang="yang",
        branch_element="木",
        branch_yin_yang="yang",
    )


class HiddenStemTests(TestCase):
    def test_all_twelve_branches_match_v1_table(self):
        for branch, expected in EXPECTED_STEMS.items():
            with self.subTest(branch=branch):
                result = get_hidden_stems(branch)
                actual = [(item.stem, item.role.value) for item in result.stems]
                self.assertEqual(actual, expected)
                self.assertEqual(result.rule_version, HIDDEN_STEM_RULE_VERSION)

    def test_elements_come_from_canonical_stem_constants(self):
        result = get_hidden_stems("辰")
        self.assertEqual(
            [(item.stem, item.element) for item in result.stems],
            [("戊", "土"), ("乙", "木"), ("癸", "水")],
        )

    def test_unknown_hour_is_not_fabricated(self):
        result = calculate_hidden_stems(
            {
                "year": _pillar("午"),
                "month": _pillar("巳"),
                "day": _pillar("辰"),
                "hour": None,
            }
        )
        self.assertEqual(set(result), {"year", "month", "day"})
        self.assertNotIn("hour", result)

    def test_roles_are_typed(self):
        result = get_hidden_stems("申")
        self.assertIs(result.stems[0].role, HiddenStemRole.MAIN)

    def test_invalid_branch_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "지원하지 않는 지지"):
            get_hidden_stems("X")
