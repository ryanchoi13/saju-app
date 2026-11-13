"""재물운 v3 (2026-11-13 정오님: 돈 그릇·새는 습관·들어오는 길·재테크·돈과 사람·지나온 흐름·모이는 나이·큰돈의 해 등 재물운에서 주로 보는 것)."""
import datetime
import html
import random
import re
import unittest

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services import wealth_sections as sec
from app.engine.services.annual_copy import find_banned
from app.engine.services.wealth import build_lifetime_wealth_report

PAID = ("path", "invest", "people", "past", "age", "big", "months", "kaiun", "actions")


def _core(birth=datetime.date(1978, 3, 13), gender="male", hour=10, minute=30):
    return calculate_myeongri_core(BirthInput(name="t", gender=gender, birth_date=birth,
                                              birth_time=datetime.time(hour, minute)), target_date=datetime.date(2026, 11, 13))


def _text(content: str) -> str:
    content = re.sub(r'<details class="reading-evidence">.*?</details>', "", content, flags=re.S)
    return html.unescape(re.sub(r"<[^>]+>", "\n", content))


class WealthV3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.core = _core()
        cls.paid = build_lifetime_wealth_report(cls.core, "최정오", is_unlocked=True)
        cls.free = build_lifetime_wealth_report(cls.core, "최정오")

    def test_bank_has_no_banned_words_or_hedges(self):
        for s in sec.all_sentences():
            self.assertEqual(find_banned(s), [], s)
            self.assertIsNone(re.search(r"수 있어요|수 있습니다|일지도|대박|수익 보장", s), s)

    def test_paid_sections_and_volume(self):
        c = self.paid["content"]
        self.assertEqual(self.paid["narrative_version"], "wealth-v3")
        for key in PAID:
            self.assertIn(f'data-wealth-section="{key}"', c)
        self.assertGreaterEqual(len(_text(c).replace("\n", "")), 2900)
        self.assertEqual(len(re.findall(r'data-wealth-month="\d{4}-\d{2}"', c)), 12)
        self.assertIn("수익이나 손실을 보장하지 않습니다", c)

    def test_free_part_and_locked_body(self):
        c = self.free["content"]
        self.assertIn('data-wealth-section="vessel"', c)
        self.assertIn('data-wealth-section="leaks"', c)
        self.assertIn('data-paywall-cta="theme-wealth"', c)
        for key in PAID:
            self.assertNotIn(f'data-wealth-section="{key}"', c)
        self.assertNotIn("months", self.free["evidence_summary"])
        self.assertFalse(self.free["is_unlocked"])

    def test_truthy_non_bool_does_not_unlock(self):
        r = build_lifetime_wealth_report(self.core, "최정오", is_unlocked=1)
        self.assertNotIn('data-wealth-section="path"', r["content"])

    def test_reference_person(self):
        # 정오님 甲戌 일주: 식상(午·巳) + 재성(戊·己·戌) → 식상생재 그릇, 일지 재성, 辰년이 재물 자리 충
        ev = self.paid["evidence_summary"]["v3"]
        self.assertEqual(ev["vessel"], "output")
        self.assertEqual(ev["moves"], [2000, 2012, 2024])
        self.assertIn(2025, ev["outs"])
        t = _text(self.paid["content"])
        self.assertIn("배우자 자리(일지)에 재물의 별이 있어서", t)
        self.assertIn("2027년·2028년·2029년이에요", t)

    def test_no_sentence_repeats(self):
        sents = [x.strip() for line in _text(self.paid["content"]).split("\n")
                 for x in re.split(r"(?<=[.!?])\s+", line) if len(x.strip()) > 12 and "월 · " not in x]
        self.assertEqual(len(sents), len(set(sents)), [s for s in sents if sents.count(s) > 1])

    def test_many_charts(self):
        rnd = random.Random(5)
        for _ in range(40):
            birth = datetime.date(1950, 1, 1) + datetime.timedelta(days=rnd.randrange(0, 20000))
            r = build_lifetime_wealth_report(_core(birth, rnd.choice(["male", "female"]), rnd.randrange(24), 0),
                                             "t", is_unlocked=True)
            t = _text(r["content"])
            self.assertIn('data-wealth-section="kaiun"', r["content"])
            self.assertEqual(find_banned(t), [], t[:200])
            self.assertEqual(len(re.findall(r'data-wealth-trap="', r["content"])), 3)
            sents = [x.strip() for line in t.split("\n") for x in re.split(r"(?<=[.!?])\s+", line)
                     if len(x.strip()) > 12 and "월 · " not in x]
            self.assertEqual(len(sents), len(set(sents)), [s for s in sents if sents.count(s) > 1])


if __name__ == "__main__":
    unittest.main()
