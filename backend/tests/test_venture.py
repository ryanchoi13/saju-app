"""사업운 테마 (2026-11-25): 무료 2칸 + 유료 8칸, 220복채, 다른 테마운과 같은 잠금 원칙."""
import datetime
import html
import re
import sys
import unittest
from pathlib import Path

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services import venture_sections as sec
from app.engine.services.annual_copy import find_banned
from app.engine.services.venture import build_venture_report

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import report_access  # noqa: E402

PAID = ("kind", "industry", "partner", "capital", "cycle", "years", "open", "actions")


def _core(birth=datetime.date(1978, 3, 13), time=datetime.time(11, 0), gender="male"):
    return calculate_myeongri_core(
        BirthInput(name="t", gender=gender, birth_date=birth, birth_time=time, time_unknown=time is None),
        target_date=datetime.date(2026, 11, 25))


def _text(content: str) -> str:
    content = re.sub(r'<details class="reading-evidence">.*?</details>', "", content, flags=re.S)
    return html.unescape(re.sub(r"<[^>]+>", " ", content))


class VentureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.core = _core()
        cls.paid = build_venture_report(cls.core, "최정오", is_unlocked=True)
        cls.free = build_venture_report(cls.core, "최정오")

    def test_bank_has_no_banned_words_or_hedges(self):
        for s in sec.all_sentences():
            self.assertEqual(find_banned(s), [], s)
            self.assertIsNone(re.search(r"수 있어요|수 있습니다|일지도", s), s)

    def test_paid_has_all_sections(self):
        c = self.paid["content"]
        for key in ("nature", "traps", *PAID):
            self.assertIn(f'data-venture-section="{key}"', c)
        self.assertEqual(len(re.findall(r'data-venture-trap="\d"', c)), 3)
        self.assertEqual(len(re.findall(r'data-venture-year="\d{4}"', c)), 5)
        self.assertEqual(find_banned(_text(c)), [])
        self.assertIsNone(re.search(r"수 있어요|수 있습니다", _text(c)))

    def test_locked_carries_no_paid_body(self):
        c = self.free["content"]
        for key in PAID:
            self.assertNotIn(f'data-venture-section="{key}"', c)
        self.assertNotIn("v1", self.free["evidence_summary"])
        self.assertIn('data-paywall-cta="theme-venture"', c)
        # 문자열 'true' 같은 값으로는 열리지 않는다
        self.assertFalse(build_venture_report(self.core, "t", is_unlocked="true")["is_unlocked"])

    def test_repeatable(self):
        self.assertEqual(self.paid["content"], build_venture_report(self.core, "최정오", is_unlocked=True)["content"])

    def test_same_price_and_rules_as_other_themes(self):
        self.assertEqual(report_access.REPORT_PRICES["venture"], report_access.REPORT_PRICES["wealth"])
        self.assertIn("venture", report_access.TIERED_REPORTS)
        self.assertEqual("venture" in report_access.SOON_REPORTS, "wealth" in report_access.SOON_REPORTS)

    def test_other_people_render(self):
        for b, t, g in ((datetime.date(1995, 7, 2), datetime.time(4, 10), "female"),
                        (datetime.date(1988, 12, 24), datetime.time(22, 0), "female"),
                        (datetime.date(2001, 1, 9), None, "male"),
                        (datetime.date(1965, 10, 30), datetime.time(13, 0), "male")):
            r = build_venture_report(_core(b, t, g), "t", is_unlocked=True)
            self.assertEqual(len(re.findall(r'data-venture-section="', r["content"])), 10)
            self.assertEqual(find_banned(_text(r["content"])), [])


if __name__ == "__main__":
    unittest.main()
