from unittest import TestCase

from app.engine.constants import GAN_WUXING
from app.engine.core.models import PillarFact, TenGod
from app.engine.facts.hidden_stems import calculate_hidden_stems
from app.engine.facts.ten_gods import (
    TEN_GOD_RULE_VERSION,
    calculate_ten_gods,
    get_ten_god,
)


STEMS = "甲乙丙丁戊己庚辛壬癸"
EXPECTED_BY_DAY_MASTER = {
    "甲": "peer rob_wealth eating_god hurting_officer indirect_wealth direct_wealth seven_killings direct_officer indirect_resource direct_resource",
    "乙": "rob_wealth peer hurting_officer eating_god direct_wealth indirect_wealth direct_officer seven_killings direct_resource indirect_resource",
    "丙": "indirect_resource direct_resource peer rob_wealth eating_god hurting_officer indirect_wealth direct_wealth seven_killings direct_officer",
    "丁": "direct_resource indirect_resource rob_wealth peer hurting_officer eating_god direct_wealth indirect_wealth direct_officer seven_killings",
    "戊": "seven_killings direct_officer indirect_resource direct_resource peer rob_wealth eating_god hurting_officer indirect_wealth direct_wealth",
    "己": "direct_officer seven_killings direct_resource indirect_resource rob_wealth peer hurting_officer eating_god direct_wealth indirect_wealth",
    "庚": "indirect_wealth direct_wealth seven_killings direct_officer indirect_resource direct_resource peer rob_wealth eating_god hurting_officer",
    "辛": "direct_wealth indirect_wealth direct_officer seven_killings direct_resource indirect_resource rob_wealth peer hurting_officer eating_god",
    "壬": "eating_god hurting_officer indirect_wealth direct_wealth seven_killings direct_officer indirect_resource direct_resource peer rob_wealth",
    "癸": "hurting_officer eating_god direct_wealth indirect_wealth direct_officer seven_killings direct_resource indirect_resource rob_wealth peer",
}


def _pillar(stem: str, branch: str) -> PillarFact:
    return PillarFact(
        stem=stem,
        branch=branch,
        ganji=f"{stem}{branch}",
        stem_element=GAN_WUXING[stem],
        stem_yin_yang="yang" if stem in "甲丙戊庚壬" else "yin",
        branch_element="木",
        branch_yin_yang="yang",
    )


class TenGodTests(TestCase):
    def test_all_one_hundred_stem_pairs(self):
        for day_master, expected_values in EXPECTED_BY_DAY_MASTER.items():
            for target, expected in zip(STEMS, expected_values.split()):
                with self.subTest(day_master=day_master, target=target):
                    self.assertEqual(get_ten_god(day_master, target).value, expected)

    def test_visible_and_hidden_stems_are_connected(self):
        pillars = {
            "year": _pillar("庚", "申"),
            "month": _pillar("丙", "寅"),
            "day": _pillar("甲", "辰"),
            "hour": None,
        }
        result = calculate_ten_gods("甲", pillars, calculate_hidden_stems(pillars))

        self.assertEqual(result.rule_version, TEN_GOD_RULE_VERSION)
        self.assertEqual([item.ten_god for item in result.visible], [
            TenGod.SEVEN_KILLINGS,
            TenGod.EATING_GOD,
            TenGod.DAY_MASTER,
        ])
        self.assertEqual(len(result.hidden), 9)
        self.assertEqual(result.hidden[0].hidden_role.value, "main")

    def test_unknown_hour_is_not_fabricated(self):
        pillars = {"day": _pillar("甲", "辰"), "hour": None}
        result = calculate_ten_gods("甲", pillars, calculate_hidden_stems(pillars))
        self.assertNotIn("hour", {item.pillar for item in result.visible + result.hidden})

    def test_invalid_stem_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "지원하지 않는 천간"):
            get_ten_god("甲", "X")
