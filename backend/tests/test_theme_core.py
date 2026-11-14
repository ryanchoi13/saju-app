"""테마운 공용 판정 엔진 — 다섯 테마가 같은 십성 세기·관계표를 쓰는지."""
import datetime
import unittest

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.semantic.queries import profile_ten_gods
from app.engine.services import career, health, love, love_depth, study, wealth
from app.engine.services import career_copy, love_copy, theme_core


def _core():
    return calculate_myeongri_core(
        BirthInput(name="최정오", gender="male", birth_date=datetime.date(1978, 3, 13), birth_time=datetime.time(11, 0)),
        target_date=datetime.date(2026, 11, 13))


class ThemeCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.core = _core()

    def test_eight_characters_main_qi_only(self):
        # 戊午 乙卯 甲戌 己巳: 천간 戊·乙·己 + 지지 본기 丁·乙·戊·丙 → 관성은 겉면에 없다
        counts = theme_core.natal_counts(self.core)
        self.assertEqual(sum(len(v) for v in counts.values()), 7)
        self.assertNotIn("direct_officer", counts)
        self.assertNotIn("seven_killings", counts)
        self.assertEqual(counts["rob_wealth"], ["month_stem", "month_branch"])
        self.assertTrue(theme_core.rob_heavy(counts))

    def test_tally_filters_by_theme(self):
        t = theme_core.tally(self.core, profile_ten_gods("career"))
        self.assertNotIn("rob_wealth", t)
        self.assertEqual(sum(t.values()), 5)

    def test_hidden_tally_breaks_ties_only(self):
        self.assertEqual(career_copy.lead_group({"direct_officer": 1, "eating_god": 1}, {"eating_god": 1}), "output")
        self.assertEqual(career_copy.lead_group({"direct_officer": 2, "eating_god": 1}, {"eating_god": 5}), "officer")
        self.assertEqual(love_copy.lead_group({}, {"peer": 3}), "balanced")

    def test_themes_share_tables(self):
        self.assertIs(love_depth.CLASH, theme_core.CLASH)
        for mod in (career, love, health):
            self.assertIs(mod.CLASH, theme_core.CLASH)
        for mod in (career, love, wealth, study):
            self.assertFalse(hasattr(mod, "_CLASH"))


if __name__ == "__main__":
    unittest.main()
