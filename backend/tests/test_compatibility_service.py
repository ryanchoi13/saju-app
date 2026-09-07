import datetime
import unittest

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services.compatibility import _cross_interactions, build_compatibility_report


class CompatibilityReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.left = calculate_myeongri_core(
            BirthInput(name="테스트A", gender="male", birth_date=datetime.date(1988, 4, 12), birth_time=datetime.time(10, 30)),
            target_date=datetime.date(2026, 9, 7),
        )
        cls.right = calculate_myeongri_core(
            BirthInput(name="테스트B", gender="female", birth_date=datetime.date(1992, 6, 18), time_unknown=True),
            target_date=datetime.date(2026, 9, 7),
        )

    def test_report_uses_both_calculated_charts(self):
        report = build_compatibility_report(self.left, self.right, "테스트A", "테스트B", "연인 / 결혼")
        for marker in ["정통 사주 궁합", "두 사람의 궁합, 먼저 답하면", "서로를 어떻게 느끼는가", "관계에서 눈여겨볼 신살", "사랑이 깊어지는 방식", "사랑이 식을 수 있는 지점", "결혼하면 어떤가", "함께 돈을 만들고 지키는 힘", "자녀와 부모 역할", "판단 근거 보기", "생시 미상 안내"]:
            self.assertIn(marker, report["title"] + report["content"])

    def test_report_rejects_fixed_score_and_deterministic_claims(self):
        report = build_compatibility_report(self.left, self.right, "테스트A", "테스트B", "동업 / 비즈니스")
        self.assertIn("사랑의 크기", report["content"])
        self.assertIn("확정하지 않으며", report["content"])
        self.assertNotIn("완벽하게 채워주는", report["content"])
        self.assertNotIn("최상의 인연 배합", report["content"])

    def test_technical_terms_are_kept_in_one_collapsed_evidence_section(self):
        report = build_compatibility_report(self.left, self.right, "테스트A", "테스트B", "연인 / 결혼")
        self.assertIn("<details", report["content"])
        self.assertIn("명리 용어 포함", report["content"])
        self.assertNotIn("후보 하나만으로 관계의 결론을 정하지 않습니다", report["content"])

    def test_day_branch_wonjin_is_a_high_importance_relationship_signal(self):
        left = self.left.model_copy(deep=True)
        right = self.right.model_copy(deep=True)
        left_day = left.natal_facts.pillars["day"]
        right_day = right.natal_facts.pillars["day"]
        left_month = left.natal_facts.pillars["month"]
        right_month = right.natal_facts.pillars["month"]
        left.natal_facts.pillars["day"] = left_day.model_copy(update={"branch": "子"})
        right.natal_facts.pillars["day"] = right_day.model_copy(update={"branch": "未"})
        left.natal_facts.pillars["month"] = left_month.model_copy(update={"branch": "寅"})
        right.natal_facts.pillars["month"] = right_month.model_copy(update={"branch": "申"})
        items = _cross_interactions(left, right)
        self.assertTrue(any(item["kind"] == "원진살" and item["importance"] == 3 for item in items))
        report = build_compatibility_report(left, right, "테스트A", "테스트B", "연인 / 결혼")
        self.assertIn("두 사람의 일지에 <strong>원진살</strong>이 성립합니다", report["content"])
        self.assertIn("이 궁합은 서운함을 오래 쌓아 두면 안 됩니다", report["content"])

    def test_day_branch_can_activate_cross_chart_peach_blossom(self):
        left = self.left.model_copy(deep=True)
        right = self.right.model_copy(deep=True)
        left_day = left.natal_facts.pillars["day"]
        right_day = right.natal_facts.pillars["day"]
        left.natal_facts.pillars["day"] = left_day.model_copy(update={"branch": "申"})
        right.natal_facts.pillars["day"] = right_day.model_copy(update={"branch": "酉"})
        items = _cross_interactions(left, right)
        self.assertTrue(any(item["kind"] == "도화살" and item["importance"] == 3 for item in items))

    def test_main_generator_requires_and_uses_partner_birth_data(self):
        from main import generate_detailed_report
        user = {"name": "테스트A", "gender": "male", "birth_year": 1988, "birth_month": 4, "birth_day": 12, "calendar_type": "solar", "sijin_index": 5}
        partner = {"name": "테스트B", "gender": "female", "birth_year": 1992, "birth_month": 6, "birth_day": 18, "calendar_type": "solar", "sijin_index": -1}
        report = generate_detailed_report("gunghap", "기본", "테스트B", "연인 / 결혼", "테스트A", user=user, partner=partner)
        self.assertIn("테스트A님 & 테스트B님", report["title"])
        self.assertIn("지금 두 사람에게 필요한 것", report["content"])


if __name__ == "__main__":
    unittest.main()
