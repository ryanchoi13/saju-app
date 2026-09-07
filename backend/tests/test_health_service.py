import datetime
import unittest

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services.health import build_lifetime_health_report


class LifetimeHealthReportTests(unittest.TestCase):
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

    def test_report_uses_climate_strength_bottleneck_and_all_cycles(self):
        report = build_lifetime_health_report(self.core, "최정오")
        self.assertIn("평생 건강 생활흐름", report["title"])
        for marker in [
            "평생 생활 리듬의 구조", "신강", "한난조습이 비교적 고른 환경",
            "먼저 관리할 생활 병목", "현재 건강 생활흐름",
            "48~57세", "庚申", "초년기", "청년기", "중장년기", "말년기",
        ]:
            self.assertIn(marker, report["content"])
        self.assertIn("중장년기 · 48~67세", report["content"])
        self.assertIn("말년기 · 68~97세", report["content"])
        self.assertNotIn("98~107세", report["content"])

    def test_report_blocks_medical_and_deterministic_claims(self):
        report = build_lifetime_health_report(self.core, "최정오")
        self.assertIn("질병이 아니라", report["content"])
        self.assertIn("의료 진단을 대신하지 않습니다", report["content"])
        self.assertNotIn("약한 신체 부위", report["content"])
        self.assertNotIn("반드시 발병", report["content"])
        self.assertNotIn("수명은", report["content"])

    def test_main_report_generator_is_connected(self):
        from main import generate_detailed_report

        user = {
            "name": "최정오", "gender": "male", "birth_year": 1978,
            "birth_month": 3, "birth_day": 13, "calendar_type": "solar",
            "sijin_index": 5,
        }
        report = generate_detailed_report(
            "health", "기본", "상대방", "선택안함", "최정오", user=user
        )
        self.assertIn("정통 명리 평생 건강 생활흐름", report["title"])
        self.assertIn("활동과 회복의 균형", report["content"])


if __name__ == "__main__":
    unittest.main()
