import datetime
import unittest

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services.compatibility import build_compatibility_report


class CompatibilityReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.left = calculate_myeongri_core(
            BirthInput(name="최정오", gender="male", birth_date=datetime.date(1978, 3, 13), birth_time=datetime.time(10, 30)),
            target_date=datetime.date(2026, 9, 7),
        )
        cls.right = calculate_myeongri_core(
            BirthInput(name="상대방", gender="female", birth_date=datetime.date(1990, 5, 15), time_unknown=True),
            target_date=datetime.date(2026, 9, 7),
        )

    def test_report_uses_both_calculated_charts(self):
        report = build_compatibility_report(self.left, self.right, "최정오", "상대방", "연인 / 결혼")
        for marker in ["정통 사주 궁합", "두 명식의 핵심 관계", "서로를 받아들이는 방식", "상호 보완 가능성", "두 명식 사이의 주요 관계 후보", "생시 미상 안내"]:
            self.assertIn(marker, report["title"] + report["content"])

    def test_report_rejects_fixed_score_and_deterministic_claims(self):
        report = build_compatibility_report(self.left, self.right, "최정오", "상대방", "동업 / 비즈니스")
        self.assertIn("궁합 점수", report["content"])
        self.assertIn("확정하지 않으며", report["content"])
        self.assertNotIn("완벽하게 채워주는", report["content"])
        self.assertNotIn("최상의 인연 배합", report["content"])

    def test_main_generator_requires_and_uses_partner_birth_data(self):
        from main import generate_detailed_report
        user = {"name": "최정오", "gender": "male", "birth_year": 1978, "birth_month": 3, "birth_day": 13, "calendar_type": "solar", "sijin_index": 5}
        partner = {"name": "상대방", "gender": "female", "birth_year": 1990, "birth_month": 5, "birth_day": 15, "calendar_type": "solar", "sijin_index": -1}
        report = generate_detailed_report("gunghap", "기본", "상대방", "연인 / 결혼", "최정오", user=user, partner=partner)
        self.assertIn("최정오님 & 상대방님", report["title"])
        self.assertIn("연인 / 결혼 관계에서의 활용", report["content"])


if __name__ == "__main__":
    unittest.main()
