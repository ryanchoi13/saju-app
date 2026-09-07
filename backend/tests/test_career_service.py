import datetime
import unittest

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services.career import build_lifetime_career_report


class LifetimeCareerReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.core = calculate_myeongri_core(
            BirthInput(
                name="최정오", gender="male",
                birth_date=datetime.date(1978, 3, 13),
                birth_time=datetime.time(10, 30),
            ),
            target_date=datetime.date(2026, 9, 7),
        )

    def test_business_report_uses_natal_and_all_cycles(self):
        report = build_lifetime_career_report(self.core, "최정오", "사업가")
        self.assertIn("평생 직업·사업운", report["title"])
        for marker in [
            "평생 일의 구조 · 사업가", "사업 운영에서의 활용",
            "현재 직업·사업 흐름", "48~57세", "庚申",
            "초년기", "청년기", "중장년기", "말년기",
        ]:
            self.assertIn(marker, report["content"])
        self.assertIn("성공을 보장하지 않습니다", report["content"])
        self.assertNotIn("정관·편관 0곳", report["content"])
        self.assertNotIn("대박", report["content"])
        self.assertNotIn("100점", report["content"])

    def test_status_selects_career_or_business_language(self):
        employee = build_lifetime_career_report(self.core, "최정오", "직장인")
        changing = build_lifetime_career_report(self.core, "최정오", "취업/이직")
        startup = build_lifetime_career_report(self.core, "최정오", "창업")
        self.assertIn("현재 역할에서의 활용", employee["content"])
        self.assertIn("취업·이직에서의 활용", changing["content"])
        self.assertIn("창업 준비에서의 활용", startup["content"])

    def test_main_report_generator_is_connected(self):
        from main import generate_detailed_report

        user = {
            "name": "최정오", "gender": "male", "birth_year": 1978,
            "birth_month": 3, "birth_day": 13, "calendar_type": "solar",
            "sijin_index": 5,
        }
        report = generate_detailed_report(
            "business", "사업가", "상대방", "선택안함", "최정오", user=user
        )
        self.assertIn("정통 명리 평생 직업·사업운", report["title"])
        self.assertIn("사업 운영에서의 활용", report["content"])


if __name__ == "__main__":
    unittest.main()
