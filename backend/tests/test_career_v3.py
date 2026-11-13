"""직업운 v3 (2026-11-13 정오님: 분량 3배 · 칸 10개 · 12달 등급)."""
import datetime
import html
import re
import unittest

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services import career_sections as sec
from app.engine.services.annual_copy import find_banned
from app.engine.services.career import build_lifetime_career_report

PAID = ("workplace", "jobs", "money", "people", "cycle", "months", "move", "actions")


def _core(birth=datetime.date(1978, 3, 13), time=datetime.time(11, 0), today=datetime.date(2026, 11, 13)):
    return calculate_myeongri_core(
        BirthInput(name="최정오", gender="male", birth_date=birth, birth_time=time), target_date=today)


def _text(content: str) -> str:
    content = re.sub(r'<details class="reading-evidence">.*?</details>', "", content, flags=re.S)
    return html.unescape(re.sub(r"<[^>]+>", "", content))


class CareerV3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.core = _core()
        cls.paid = build_lifetime_career_report(cls.core, "최정오", "직장인", is_unlocked=True)
        cls.free = build_lifetime_career_report(cls.core, "최정오", "직장인")

    def test_bank_has_no_banned_words_or_hedges(self):
        for s in sec.all_sentences():
            self.assertEqual(find_banned(s), [], s)
            self.assertIsNone(re.search(r"수 있어요|수 있습니다|일지도", s), s)

    def test_paid_report_has_all_sections_and_three_times_the_old_length(self):
        c = self.paid["content"]
        for key in ("nature", "traps", *PAID):
            self.assertIn(f'data-career-section="{key}"', c)
        self.assertGreaterEqual(len(_text(c)), 2214)          # 옛 직업운 738자의 3배
        self.assertEqual(len(re.findall(r'data-career-month="\d{4}-\d{2}"', c)), 12)
        self.assertLessEqual(len(re.findall(r'data-career-key-month="\d{4}', c)), 3)
        self.assertEqual(len(re.findall(r'data-career-action="\d"', c)), 5)
        self.assertEqual(len(re.findall(r'data-career-trap="\d"', c)), 3)
        self.assertEqual(find_banned(_text(c)), [])

    def test_locked_report_carries_no_paid_body_and_computes_no_months(self):
        c = self.free["content"]
        for key in PAID:
            self.assertNotIn(f'data-career-section="{key}"', c)
        self.assertNotIn('data-paywall="unlocked"', c)
        self.assertNotIn("months", self.free["evidence_summary"])
        self.assertIn('data-paywall-cta="theme-career"', c)

    def test_months_start_from_viewing_month(self):
        months = re.findall(r'data-career-month="(\d{4}-\d{2})"', self.paid["content"])
        self.assertEqual(months[0], "2026-11")
        self.assertEqual(months[-1], "2027-10")

    def test_report_is_repeatable(self):
        again = build_lifetime_career_report(self.core, "최정오", "직장인", is_unlocked=True)
        self.assertEqual(again["content"], self.paid["content"])

    def test_status_changes_track_and_move_advice(self):
        biz = build_lifetime_career_report(self.core, "최정오", "사업가", is_unlocked=True)["content"]
        self.assertIn(sec.WORKPLACE["wealth"]["business"], biz)
        self.assertNotEqual(biz, self.paid["content"])

    def test_money_type_tie_goes_to_the_strongest_single_god(self):
        # 정오님: 편재 3 · 정재 2 · 상관 2 … 세 묶음이 3으로 같고, 가장 많은 편재가 든 사업형
        counts = {"indirect_wealth": 3, "direct_wealth": 2, "hurting_officer": 2,
                  "direct_officer": 1, "eating_god": 1, "seven_killings": 1}
        self.assertEqual(sec.money_type(counts), "venture")
        self.assertEqual(sec.money_type({}), "salary")

    def test_unknown_birth_time_still_renders(self):
        core = calculate_myeongri_core(
            BirthInput(name="a", gender="female", birth_date=datetime.date(1995, 7, 2), birth_time=None,
                       time_unknown=True), target_date=datetime.date(2026, 11, 13))
        r = build_lifetime_career_report(core, "a", "창업", is_unlocked=True)
        self.assertIn('data-career-section="actions"', r["content"])


if __name__ == "__main__":
    unittest.main()
