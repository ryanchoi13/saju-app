import re
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


class LifetimeNextCycleNoLinkTests(TestCase):
    def test_next_cycle_has_no_lock_note_or_paywall_link(self):
        """11/20 정오님 요청: '다음 구간' 아래 잠금 안내와 '대운 전체 풀이 열어보기' 링크를 지운다."""
        core = calculate_myeongri_core(
            BirthInput(name="검증", gender="male", birth_date=date(1978, 3, 13), birth_time="10:30"),
            target_date=date(2026, 11, 20),
        )
        content = build_lifetime_overall_report(core, "검증")["content"]
        self.assertIn('data-lifetime-section="upcoming"', content)
        self.assertNotIn("data-paywall-cta", content)
        self.assertNotIn("열어보기", content)
        self.assertNotIn("따로 열립니다", content)
