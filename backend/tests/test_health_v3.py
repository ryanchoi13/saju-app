"""건강운 v3 (2026-11-13 정오님: 체질·강한 곳·음식·나이별 조심할 시기 등 건강운에서 사람들이 주로 보는 것)."""
import datetime
import html
import random
import re
import unittest

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services import health_sections as sec
from app.engine.services.health import build_lifetime_health_report
from app.engine.services.health_copy import find_medical_flagged

PAID = ("const", "body", "food", "move", "age", "season", "months", "kaiun", "actions")


def _core(birth=datetime.date(1978, 3, 13), gender="male", hour=11):
    return calculate_myeongri_core(BirthInput(name="t", gender=gender, birth_date=birth,
                                              birth_time=datetime.time(hour, 0)), target_date=datetime.date(2026, 11, 13))


def _text(content: str) -> str:
    content = re.sub(r'<details class="reading-evidence">.*?</details>', "", content, flags=re.S)
    return html.unescape(re.sub(r"<[^>]+>", "\n", content))


class HealthV3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.core = _core()
        cls.paid = build_lifetime_health_report(cls.core, "최정오", is_unlocked=True)
        cls.free = build_lifetime_health_report(cls.core, "최정오")

    def test_bank_has_no_medical_words_or_hedges(self):
        for s in sec.all_sentences():
            self.assertEqual(find_medical_flagged(s), [], s)
            self.assertIsNone(re.search(r"수 있어요|수 있습니다|일지도", s), s)

    def test_paid_sections_and_three_times_length(self):
        c = self.paid["content"]
        for key in PAID:
            self.assertIn(f'data-health-section="{key}"', c)
        self.assertGreaterEqual(len(_text(c).replace("\n", "")), 2658)    # 옛 건강운 886자의 3배
        self.assertEqual(len(re.findall(r'data-health-month="\d{4}-\d{2}"', c)), 12)
        self.assertEqual(find_medical_flagged(_text(c)), [])

    def test_locked_carries_no_paid_body(self):
        c = self.free["content"]
        for key in PAID:
            self.assertNotIn(f'data-health-section="{key}"', c)
        self.assertNotIn("months", self.free["evidence_summary"])

    def test_reference_person(self):
        # 정오님: 목 38 · 토 39 넘침, 금 4 · 수 0 모자람, 필요한 기운 금·화, 지금 庚申 대운 = 회복
        ev = self.paid["evidence_summary"]["v3"]
        self.assertEqual(set(ev["excess"]), {"木", "土"})
        self.assertEqual(ev["weak"], ["水", "金"])
        self.assertEqual(ev["good"], ["金", "火"])
        t = _text(self.paid["content"])
        self.assertIn("지금은 48~57세로, 회복이 붙는 10년 안에 있어요.", t)
        self.assertIn("붉은 먹거리가 몸에", t)

    def test_no_sentence_repeats(self):
        sents = [x.strip() for line in _text(self.paid["content"]).split("\n")
                 for x in re.split(r"(?<=[.!?])\s+", line) if len(x.strip()) > 12 and "월 · " not in x]
        self.assertEqual(len(sents), len(set(sents)))

    def test_many_charts(self):
        rnd = random.Random(3)
        for _ in range(30):
            birth = datetime.date(1950, 1, 1) + datetime.timedelta(days=rnd.randrange(0, 20000))
            r = build_lifetime_health_report(_core(birth, rnd.choice(["male", "female"]), rnd.randrange(24)),
                                             "t", is_unlocked=True)
            self.assertIn('data-health-section="kaiun"', r["content"])
            self.assertEqual(find_medical_flagged(_text(r["content"])), [])


if __name__ == "__main__":
    unittest.main()
