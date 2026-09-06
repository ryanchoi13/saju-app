from datetime import date
from unittest import TestCase

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services import build_lifetime_overall_report


class LifetimeServiceTests(TestCase):
    def test_report_uses_actual_core_and_all_luck_cycles(self):
        core = calculate_myeongri_core(
            BirthInput(
                name="검증",
                gender="male",
                birth_date=date(1990, 5, 15),
                time_unknown=True,
            ),
            target_date=date(2026, 9, 7),
        )
        report = build_lifetime_overall_report(core, "검증")
        self.assertIn("庚(金)", report["content"])
        self.assertIn("甲申", report["content"])
        self.assertIn("출생시간 미상 분석", report["content"])
        self.assertNotIn("자수성가형 귀격", report["content"])
        self.assertNotIn("황금기", report["content"])

    def test_every_cycle_preserves_relationship_reassessment(self):
        core = calculate_myeongri_core(
            BirthInput(
                name="검증", gender="male", birth_date=date(1978, 8, 13),
                time_unknown=True,
            ),
            target_date=date(2026, 9, 7),
        )
        cycles = core.timing.luck_cycle["cycles"]
        self.assertTrue(cycles)
        self.assertTrue(all("relationship_changes" in cycle for cycle in cycles))

    def test_root_report_generator_is_wired_to_new_core(self):
        from main import generate_detailed_report

        user = {
            "name": "검증",
            "gender": "male",
            "birth_year": 1990,
            "birth_month": 5,
            "birth_day": 15,
            "calendar_type": "solar",
            "sijin_index": -1,
        }
        report = generate_detailed_report(
            "daewoon", "기본", "상대방", "선택안함", "검증", user=user
        )
        self.assertIn("정통 명리 평생운세", report["title"])
        self.assertIn("庚(金)", report["content"])
        self.assertNotIn("자수성가형 귀격", report["content"])
