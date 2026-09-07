from datetime import date
from unittest import TestCase

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services import build_annual_overall_report, build_lifetime_overall_report


class SecondTabReportTests(TestCase):
    def setUp(self):
        self.core = calculate_myeongri_core(
            BirthInput(
                name="최정오",
                gender="male",
                birth_date=date(1978, 3, 13),
                birth_time=__import__("datetime").time(10, 30),
            ),
            target_date=date(2026, 9, 7),
        )

    def test_lifetime_report_groups_cycles_and_explains_them(self):
        report = build_lifetime_overall_report(self.core, "최정오")
        for phase in ("초년기", "청년기", "중장년기", "말년기"):
            self.assertIn(phase, report["content"])
        self.assertIn("현재 대운", report["content"])
        self.assertIn("중심 주제로", report["content"])
        self.assertNotIn("원국 관계 변화 후보", report["content"])

    def test_annual_report_has_hierarchy_and_twelve_richer_months(self):
        report = build_annual_overall_report(self.core, "최정오", 2026)
        self.assertIn("올해 총운", report["content"])
        self.assertIn("재물운", report["content"])
        self.assertIn("직장·사업운", report["content"])
        self.assertEqual(report["content"].count("border-left:4px solid #2D6A4F"), 12)
        self.assertNotIn("Chapter", report["content"])
        self.assertNotIn("토정비결", report["title"])

    def test_main_saju_surface_uses_real_hour_and_hidden_stem_composition(self):
        from main import get_saju_pillars_and_analysis

        result = get_saju_pillars_and_analysis(
            "최정오", "male", 1978, 3, 13, "solar", 5
        )
        self.assertEqual(result["saju_data"]["pillars_detail"]["hour"]["cg"], "기")
        self.assertEqual(result["saju_data"]["pillars_detail"]["hour"]["jj"], "사")
        self.assertEqual(
            result["saju_data"]["elements"],
            {"wood": 37.5, "fire": 19.2, "earth": 39.1, "metal": 4.2, "water": 0.0},
        )
        self.assertIn("지장간", result["saju_data"]["elements_note"])
        self.assertIn("사(巳)시생", result["saju_profile_detail"])

    def test_unknown_hour_is_not_fabricated(self):
        from main import get_saju_pillars_and_analysis

        result = get_saju_pillars_and_analysis(
            "검증", "female", 1990, 5, 15, "solar", -1
        )
        self.assertEqual(result["saju_data"]["pillars_detail"]["hour"]["cg"], "")
        self.assertEqual(result["saju_data"]["pillars_detail"]["hour"]["jj"], "")
        self.assertAlmostEqual(sum(result["saju_data"]["elements"].values()), 100.0)
        self.assertIn("생시 미상", result["saju_profile_detail"])
