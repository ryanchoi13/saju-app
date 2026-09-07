from datetime import date, time
from unittest import TestCase

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services import build_lifetime_wealth_report


class LifetimeWealthServiceTests(TestCase):
    def setUp(self):
        self.core = calculate_myeongri_core(
            BirthInput(
                name="최정오",
                gender="male",
                birth_date=date(1978, 3, 13),
                birth_time=time(10, 30),
            ),
            target_date=date(2026, 9, 7),
        )

    def test_report_uses_natal_wealth_facts_and_all_cycles(self):
        report = build_lifetime_wealth_report(self.core, "최정오")
        self.assertIn("평생 재물 구조", report["content"])
        self.assertIn("정재", report["content"])
        self.assertIn("편재", report["content"])
        self.assertIn("庚申", report["content"])
        for phase in ("초년기", "청년기", "중장년기", "말년기"):
            self.assertIn(phase, report["content"])

    def test_report_avoids_guaranteed_investment_claims_and_scores(self):
        report = build_lifetime_wealth_report(self.core, "최정오")
        self.assertNotIn("대박", report["content"])
        self.assertNotIn("수익 보장", report["content"])
        self.assertNotIn("점수", report["content"])
        self.assertIn("수익이나 손실을 보장하지 않습니다", report["content"])

    def test_main_report_generator_is_connected(self):
        from main import generate_detailed_report

        user = {
            "name": "최정오", "gender": "male", "birth_year": 1978,
            "birth_month": 3, "birth_day": 13, "calendar_type": "solar",
            "sijin_index": 5,
        }
        report = generate_detailed_report(
            "wealth", "기본", "상대방", "선택안함", "최정오", user=user
        )
        self.assertIn("정통 명리 평생 재물운", report["title"])
        self.assertIn("48~57세", report["content"])
