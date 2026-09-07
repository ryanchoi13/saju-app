import datetime
import unittest

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.semantic import build_service_query
from app.engine.services.study import build_lifetime_study_report


class LifetimeStudyReportTests(unittest.TestCase):
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

    def test_query_includes_resource_output_and_officer_gods(self):
        profile = build_service_query(self.core, "study")
        allowed = {
            "direct_resource", "indirect_resource", "eating_god",
            "hurting_officer", "direct_officer", "seven_killings",
        }
        self.assertTrue(profile["natal"]["focused_ten_gods"])
        self.assertTrue(all(item["ten_god"] in allowed for item in profile["natal"]["focused_ten_gods"]))

    def test_report_uses_actual_core_and_all_cycles(self):
        report = build_lifetime_study_report(self.core, "최정오")
        for marker in [
            "평생 학업·시험운", "평생 학습 구조", "시험 준비의 세 축",
            "현재 학업·시험 흐름", "48~57세", "庚申",
            "초년기", "청년기", "중장년기", "말년기",
        ]:
            self.assertIn(marker, report["title"] + report["content"])
        self.assertIn("중장년기 · 48~67세", report["content"])
        self.assertIn("말년기 · 68~97세", report["content"])
        self.assertNotIn("98~107세", report["content"])

    def test_report_does_not_claim_score_or_pass_result(self):
        report = build_lifetime_study_report(self.core, "최정오")
        self.assertIn("합격·불합격을 확정하지 않습니다", report["content"])
        self.assertIn("지능이나 합격 점수가 아닙니다", report["content"])

    def test_main_report_generator_is_connected(self):
        from main import generate_detailed_report

        user = {
            "name": "최정오", "gender": "male", "birth_year": 1978,
            "birth_month": 3, "birth_day": 13, "calendar_type": "solar",
            "sijin_index": 5,
        }
        report = generate_detailed_report(
            "study", "기본", "상대방", "선택안함", "최정오", user=user
        )
        self.assertIn("정통 명리 평생 학업·시험운", report["title"])


if __name__ == "__main__":
    unittest.main()
