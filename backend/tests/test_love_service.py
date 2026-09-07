import datetime
import unittest

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services.love import build_lifetime_love_report


class LifetimeLoveReportTests(unittest.TestCase):
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

    def test_report_uses_natal_relationships_and_all_cycles(self):
        report = build_lifetime_love_report(self.core, "최정오", "솔로")
        self.assertIn("평생 애정·관계운", report["title"])
        for marker in [
            "평생 관계의 구조 · 솔로", "원국의 관계 작용",
            "현재 애정·관계 흐름", "48~57세", "庚申",
            "초년기", "청년기", "중장년기", "말년기",
        ]:
            self.assertIn(marker, report["content"])
        self.assertIn("관계 후보", report["content"])
        self.assertIn("특정 인연, 결혼, 재회, 이별을 확정", report["content"])
        self.assertNotIn("최상의 인연", report["content"])
        self.assertNotIn("100점", report["content"])

    def test_status_selects_matching_guidance(self):
        cases = {
            "솔로": "새 인연을 볼 때의 기준",
            "썸/짝사랑": "관계를 확인하는 방법",
            "연애중": "현재 관계에서의 활용",
            "기혼": "부부 관계에서의 활용",
        }
        for status, marker in cases.items():
            with self.subTest(status=status):
                report = build_lifetime_love_report(self.core, "최정오", status)
                self.assertIn(marker, report["content"])

    def test_main_report_generator_is_connected(self):
        from main import generate_detailed_report

        user = {
            "name": "최정오", "gender": "male", "birth_year": 1978,
            "birth_month": 3, "birth_day": 13, "calendar_type": "solar",
            "sijin_index": 5,
        }
        report = generate_detailed_report(
            "love", "연애중", "상대방", "선택안함", "최정오", user=user
        )
        self.assertIn("정통 명리 평생 애정·관계운", report["title"])
        self.assertIn("현재 관계에서의 활용", report["content"])


if __name__ == "__main__":
    unittest.main()
