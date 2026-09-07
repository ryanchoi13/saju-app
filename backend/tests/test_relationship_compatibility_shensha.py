from unittest import TestCase

from app.engine.constants import GAN_WUXING, ZHI_WUXING
from app.engine.core.models import PillarFact
from app.engine.relationships.compatibility_shensha import calculate_relationship_shensha


YANG_STEMS = set("甲丙戊庚壬")
YANG_BRANCHES = set("子寅辰午申戌")


def _pillar(stem: str, branch: str) -> PillarFact:
    return PillarFact(
        stem=stem,
        branch=branch,
        ganji=stem + branch,
        stem_element=GAN_WUXING[stem],
        stem_yin_yang="yang" if stem in YANG_STEMS else "yin",
        branch_element=ZHI_WUXING[branch],
        branch_yin_yang="yang" if branch in YANG_BRANCHES else "yin",
    )


class RelationshipShenshaTests(TestCase):
    def test_day_to_day_wonjin_has_highest_positional_importance(self):
        items = calculate_relationship_shensha(
            {"day": _pillar("甲", "子")},
            {"day": _pillar("乙", "未")},
        )
        wonjin = next(item for item in items if item["kind"] == "원진살")
        self.assertEqual(wonjin["importance"], 3)
        self.assertEqual(wonjin["rule_code"], "relationship-wonjin-modern-korean-v1")

    def test_peach_blossom_is_directional_and_keeps_its_basis(self):
        items = calculate_relationship_shensha(
            {"day": _pillar("甲", "申")},
            {"day": _pillar("乙", "酉")},
        )
        peach = next(item for item in items if item["kind"] == "도화살")
        self.assertEqual(peach["symbols"], "申→酉")
        self.assertEqual(peach["importance"], 3)

    def test_non_day_positions_remain_supporting_only(self):
        items = calculate_relationship_shensha(
            {"year": _pillar("甲", "子")},
            {"year": _pillar("乙", "未")},
        )
        wonjin = next(item for item in items if item["kind"] == "원진살")
        self.assertEqual(wonjin["importance"], 1)
