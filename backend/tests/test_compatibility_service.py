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
        text = report["title"] + report["content"]
        for marker in ["정통 사주 궁합", "한눈에 보기", "겉궁합 · 처음 만났을 때", "속궁합", "다툰 뒤 풀리는 법", "오래 함께할 때 · 앞으로 10년", "이 풀이의 근거", "출생 시간을 모르는"]:
            self.assertIn(marker, text)

    def test_report_has_no_fixed_score_or_old_boilerplate(self):
        report = build_compatibility_report(self.left, self.right, "테스트A", "테스트B", "동업 / 비즈니스")
        for old in ["결혼하면 어떤가", "자녀와 부모 역할", "완벽하게 채워주는", "최상의 인연 배합"]:
            self.assertNotIn(old, report["content"])

    def test_technical_terms_are_kept_in_one_collapsed_evidence_section(self):
        report = build_compatibility_report(self.left, self.right, "테스트A", "테스트B", "연인 / 결혼")
        self.assertEqual(report["content"].count("<details"), 1)
        body = report["content"].split("<details")[0]
        for term in ("원진살", "도화살", "천간합", "일간"):
            self.assertNotIn(term, body)

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
        self.assertIn("서운함을 말하지 않고 쌓아 두면", report["content"].split("<details")[0])

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
        self.assertIn("오래 함께할 때 · 앞으로 10년", report["content"])


class CompatibilityVerdictTests(unittest.TestCase):
    def test_summary_has_score_tier_and_is_first(self):
        import re
        from app.engine.services import compat_copy as cc
        def core(y, m, d, h, g):
            return calculate_myeongri_core(
                BirthInput(name="x", gender=g, birth_date=datetime.date(y, m, d), birth_time=datetime.time(h, 30)),
                target_date=datetime.date(2026, 11, 20))
        me, other = core(1978, 3, 13, 10, "male"), core(1984, 9, 2, 21, "female")
        labels = {t[1] for t in cc.TIERS}
        for relation in ["연인 / 결혼", "친구 / 지인", "동업 / 비즈니스"]:
            html = build_compatibility_report(me, other, "가", "나", relation)["content"]
            self.assertLess(html.index('data-compat-section="summary"'), html.index('data-compat-section="outer"'))
            m = re.search(r'<strong>(\d+)점</strong> · ([^<]+)</p>', html)
            self.assertTrue(m and 25 <= int(m.group(1)) <= 95 and m.group(2) in labels, relation)
            self.assertIn("앞날을 정하는 숫자는 아니에요", html)


class CompatibilityIntimacyTests(unittest.TestCase):
    def test_intimacy_only_for_lovers(self):
        def core(y, m, d, h, g):
            return calculate_myeongri_core(
                BirthInput(name="x", gender=g, birth_date=datetime.date(y, m, d), birth_time=datetime.time(h, 30)),
                target_date=datetime.date(2026, 11, 20))
        me, other = core(1978, 3, 13, 10, "male"), core(1984, 9, 2, 21, "female")
        lover = build_compatibility_report(me, other, "가", "나", "연인 / 결혼")["content"]
        self.assertIn('data-compat-section="intimacy"', lover)
        self.assertIn("속궁합 · 끌림과 스킨십", lover)
        for relation in ["친구 / 지인", "동업 / 비즈니스"]:
            self.assertNotIn("intimacy", build_compatibility_report(me, other, "가", "나", relation)["content"])


class CompatibilityV2Tests(unittest.TestCase):
    """2026-11-20 궁합 v2: 신호가 있는 만큼만 쓰고, 관계별 어휘가 다르고, 같은 문장이 두 번 나오지 않는다."""

    @classmethod
    def setUpClass(cls):
        import random
        random.seed(11)

        def core(y, m, d, h, g, unknown=False):
            return calculate_myeongri_core(
                BirthInput(name="x", gender=g, birth_date=datetime.date(y, m, d),
                           birth_time=None if unknown else datetime.time(h, 30), time_unknown=unknown),
                target_date=datetime.date(2026, 11, 20))
        cls.me = core(1978, 3, 13, 10, "male")
        def rnd(unknown=False):
            return core(random.randint(1965, 2005), random.randint(1, 12), random.randint(1, 28),
                        random.randint(0, 23), random.choice(["male", "female"]), unknown=unknown)
        cls.pairs = [rnd(unknown=(i % 4 == 0)) for i in range(24)]
        cls.others = [rnd() for _ in range(24)]

    @staticmethod
    def _sentences(content):
        import re
        body = content.split("<details")[0]
        text = re.sub(r"<[^>]+>", "\n", body)
        return [s.strip() for s in re.split(r"\n|(?<=[.!?])\s+", text) if len(s.strip()) > 12]

    def test_no_sentence_repeats_and_no_flagged_words(self):
        from app.engine.services.love_copy import find_flagged
        for i, other in enumerate(self.pairs):
            relation = ["연인 / 결혼", "동업 / 비즈니스", "친구 / 지인"][i % 3]
            content = build_compatibility_report(self.me, other, "가", "나", relation)["content"]
            sentences = self._sentences(content)
            self.assertEqual(len(sentences), len(set(sentences)), relation)
            self.assertEqual(find_flagged(" ".join(sentences)), [])  # 속성값(관계 이름)이 아니라 화면에 보이는 글만 본다

    def test_work_and_close_use_different_vocabulary(self):
        other = self.pairs[1]
        close = build_compatibility_report(self.me, other, "가", "나", "연인 / 결혼")["content"]
        work = build_compatibility_report(self.me, other, "가", "나", "동업 / 비즈니스")["content"]
        self.assertNotEqual(close, work)
        self.assertIn("처음에 문서로 남길 약속", work)
        self.assertNotIn("처음에 문서로 남길 약속", close)
        self.assertIn("함께 정해 두면 편한 약속", close)

    def test_most_text_is_pair_specific(self):
        from collections import Counter
        sets = [set(self._sentences(build_compatibility_report(a, b, "가", "나", "연인 / 결혼")["content"]))
                for a, b in zip(self.others, self.pairs)]
        counts = Counter(s for st in sets for s in st)
        total = sum(len(s) * n for s, n in counts.items())
        shared = sum(len(s) * n for s, n in counts.items() if n >= len(sets) / 2)
        self.assertLess(shared / total, 0.3)  # v1은 92%가 공통 문단이었다

    def test_unknown_birth_time_still_builds_and_says_so(self):
        unknown = self.pairs[0]  # i % 4 == 0 → 시간 미상
        self.assertTrue(unknown.uncertainty.time_unknown)
        content = build_compatibility_report(self.me, unknown, "가", "나", "연인 / 결혼")["content"]
        self.assertIn("출생 시간을 모르는 쪽", content)
        self.assertIn("오래 함께할 때 · 앞으로 10년", content)

    def test_six_combination_state_distinguishes_clash_and_contest(self):
        from types import SimpleNamespace as P
        from app.engine.services.compat_signals import six_state
        left = {"day": P(branch="卯"), "month": P(branch="巳")}
        right = {"day": P(branch="戌"), "month": P(branch="午")}
        self.assertEqual(six_state(left, right, "day", "day"), "intact")
        right_clash = {"day": P(branch="戌"), "month": P(branch="酉")}   # 酉가 卯를 충
        self.assertEqual(six_state(left, right_clash, "day", "day"), "disturbed")
        left_two = {"day": P(branch="卯"), "month": P(branch="戌")}        # 짝 戌가 한 번 더
        self.assertEqual(six_state(left_two, right, "day", "day"), "contested")

    def test_empty_signal_sections_are_not_padded(self):
        from app.engine.services import compat_copy as cc
        # 신호가 없을 때 쓰는 문장은 한 줄뿐이고, 풀이 칸을 채우는 공통 문단 은행은 없다.
        self.assertFalse(hasattr(cc, "PAIR_CHAPTERS"))


if __name__ == "__main__":
    unittest.main()
