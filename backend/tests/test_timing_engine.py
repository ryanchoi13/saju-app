from datetime import date
from unittest import TestCase

from app.engine.constants import GAN_WUXING, ZHI_WUXING
from app.engine.core.models import BirthInput, PillarFact
from app.engine.timing.engine import calculate_timing


def _pillar(stem, branch):
    return PillarFact(
        stem=stem, branch=branch, ganji=stem + branch,
        stem_element=GAN_WUXING[stem], stem_yin_yang="yang",
        branch_element=ZHI_WUXING[branch], branch_yin_yang="yang",
    )


def _birth(gender="male"):
    return BirthInput(
        name="테스트", gender=gender, birth_date=date(1990, 5, 15),
        calendar_type="solar", time_unknown=True,
    )


NATAL = {
    "year": _pillar("庚", "午"),
    "month": _pillar("辛", "巳"),
    "day": _pillar("庚", "辰"),
}


class TimingEngineTests(TestCase):
    def test_exact_calendar_overlays_are_preserved_separately(self):
        timing, activated, evidence = calculate_timing(
            _birth(), NATAL, target_date=date(2026, 9, 7)
        )
        self.assertEqual(timing.annual["pillar"]["ganji"], "丙午")
        self.assertEqual(timing.monthly["pillar"]["ganji"], "丙申")
        self.assertEqual(timing.daily["pillar"]["ganji"], "甲申")
        self.assertTrue(activated.activated_ten_gods)
        self.assertFalse(evidence[0].source_values["fixed_weight_used"])

    def test_yang_year_male_uses_forward_daeyun(self):
        timing, _, _ = calculate_timing(
            _birth("male"), NATAL, target_date=date(2026, 9, 7)
        )
        self.assertEqual(timing.luck_cycle["direction"], "forward")
        self.assertEqual(timing.luck_cycle["cycles"][0]["pillar"]["ganji"], "壬午")

    def test_yang_year_female_uses_reverse_daeyun(self):
        timing, _, _ = calculate_timing(
            _birth("female"), NATAL, target_date=date(2026, 9, 7)
        )
        self.assertEqual(timing.luck_cycle["direction"], "reverse")
        self.assertEqual(timing.luck_cycle["cycles"][0]["pillar"]["ganji"], "庚辰")

    def test_current_cycle_is_selected_for_target_year(self):
        timing, _, _ = calculate_timing(
            _birth(), NATAL, target_date=date(2026, 9, 7)
        )
        current = timing.luck_cycle["current"]
        self.assertLessEqual(current["start_year"], 2026)
        self.assertGreaterEqual(current["end_year"], 2026)

    def test_timing_relations_are_candidates_for_reassessment(self):
        timing, activated, _ = calculate_timing(
            _birth(), NATAL, target_date=date(2026, 9, 7)
        )
        self.assertTrue(timing.relationship_changes)
        self.assertTrue(all(item["requires_reassessment"] for item in timing.relationship_changes))
        self.assertEqual(timing.relationship_changes, activated.relationship_changes)

    def test_target_before_birth_is_rejected(self):
        with self.assertRaises(ValueError):
            calculate_timing(_birth(), NATAL, target_date=date(1989, 1, 1))
