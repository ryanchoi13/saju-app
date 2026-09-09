"""Evidence distinctions; synthetic inputs are not historical birth claims."""

from unittest import TestCase

from app.engine.diagnostics.root_support import describe_root_support
from app.engine.facts.hidden_stems import calculate_hidden_stems
from app.engine.facts.rooting import calculate_roots
from app.engine.timing.engine import _pillar


def _contexts(stems):
    pillars = {key: _pillar(value) for key, value in stems.items()}
    roots = calculate_roots(pillars, calculate_hidden_stems(pillars))
    return describe_root_support(roots, pillars, [])


class RootSupportTests(TestCase):
    def test_hidden_stem_role_does_not_replace_root_category(self):
        contexts = _contexts({"year": "癸亥", "month": "戊辰", "day": "甲申", "hour": "辛未"})
        day = {r["branch_pillar"]: r for r in contexts if r["stem_pillar"] == "day"}
        # Both are middle hidden stems, but one is a growth root and the other
        # residual wood. Hidden-stem rank alone cannot distinguish them.
        self.assertEqual(day["year"]["hidden_role"], day["month"]["hidden_role"])
        self.assertEqual(day["year"]["category"], "growth")
        self.assertEqual(day["month"]["category"], "residual")
        self.assertEqual(day["hour"]["category"], "storage")
        self.assertTrue(all(r["effectiveness"] == "undetermined" for r in day.values()))

    def test_resource_branch_is_not_fabricated_as_same_element_root(self):
        contexts = _contexts({"month": "壬子", "day": "甲午"})
        self.assertFalse(any(r["stem_pillar"] == "day" for r in contexts))
        self.assertTrue(any(r["stem_pillar"] == "month" for r in contexts))

    def test_summer_metal_growth_exception_retains_the_observed_root(self):
        summer = _contexts({"month": "丙午", "day": "庚巳"})
        autumn = _contexts({"month": "辛酉", "day": "庚巳"})
        summer_root = next(r for r in summer if r["stem_pillar"] == r["branch_pillar"] == "day")
        autumn_root = next(r for r in autumn if r["stem_pillar"] == r["branch_pillar"] == "day")
        self.assertEqual(summer_root["hidden_stem"], "庚")
        self.assertEqual(summer_root["category"], autumn_root["category"])
        self.assertTrue(summer_root["seasonal_qualifications"])
        self.assertFalse(autumn_root["seasonal_qualifications"])
        self.assertEqual(summer_root["effectiveness"], autumn_root["effectiveness"])

    def test_earth_interpretation_difference_does_not_delete_hidden_presence(self):
        contexts = _contexts({"month": "乙卯", "day": "戊寅"})
        root = next(r for r in contexts if r["stem_pillar"] == "day")
        self.assertEqual(root["hidden_stem"], "戊")
        self.assertEqual(root["category"], "earth_source_dependent")
        self.assertEqual(root["ordinary_support"], "unrated")
        self.assertTrue(root["seasonal_qualifications"])

    def test_yin_life_stage_does_not_invent_absent_wood_root(self):
        contexts = _contexts({"month": "丙午", "day": "乙酉"})
        self.assertFalse(any(r["stem_pillar"] == "day" for r in contexts))

    def test_changing_position_preserves_category_without_scoring_force(self):
        contexts = _contexts({"year": "壬寅", "month": "丙寅", "day": "甲寅", "hour": "戊寅"})
        day = {r["branch_pillar"]: r for r in contexts if r["stem_pillar"] == "day"}
        self.assertEqual({r["category"] for r in day.values()}, {"vigorous"})
        self.assertEqual([day[p]["position"] for p in ("month", "day", "hour", "year")],
                         ["month", "own_branch", "hour", "year"])
        self.assertTrue(all(r["effectiveness"] == "undetermined" for r in day.values()))

