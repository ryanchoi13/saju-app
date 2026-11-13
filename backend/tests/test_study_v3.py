"""학업운 v3 (2026-11-13 정오님: 공부 머리·방해하는 습관·공부법·분야·시험운·잘 붙는 나이·좋은 해 등 학업운에서 주로 보는 것)."""
import datetime
import html
import random
import re
import unittest

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services import study_sections as sec
from app.engine.services.annual_copy import find_banned
from app.engine.services.study import build_lifetime_study_report

PAID = ("school", "pathway", "method", "field", "exam", "age", "year", "months", "kaiun", "actions")


def _core(birth=datetime.date(1978, 3, 13), gender="male", hour=10, minute=30):
    return calculate_myeongri_core(BirthInput(name="t", gender=gender, birth_date=birth,
                                              birth_time=datetime.time(hour, minute)), target_date=datetime.date(2026, 11, 13))


def _text(content: str) -> str:
    content = re.sub(r'<details class="reading-evidence">.*?</details>', "", content, flags=re.S)
    return html.unescape(re.sub(r"<[^>]+>", "\n", content))


class StudyV3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.core = _core()
        cls.paid = build_lifetime_study_report(cls.core, "최정오", is_unlocked=True)
        cls.free = build_lifetime_study_report(cls.core, "최정오")

    def test_bank_has_no_banned_words_or_hedges(self):
        for s in sec.all_sentences():
            self.assertEqual(find_banned(s), [], s)
            self.assertIsNone(re.search(r"수 있어요|수 있습니다|일지도|대박|수익 보장", s), s)

    def test_paid_sections_and_volume(self):
        c = self.paid["content"]
        self.assertEqual(self.paid["narrative_version"], "study-v3")
        for key in PAID:
            self.assertIn(f'data-study-section="{key}"', c)
        self.assertGreaterEqual(len(_text(c).replace("\n", "")), 2400)
        self.assertEqual(len(re.findall(r'data-study-month="\d{4}-\d{2}"', c)), 12)
        self.assertIn("합격이나 점수를 보장하지 않습니다", c)

    def test_free_part_and_locked_body(self):
        c = self.free["content"]
        self.assertIn('data-study-section="mind"', c)
        self.assertIn('data-study-section="leaks"', c)
        self.assertIn('data-paywall-cta="theme-study"', c)
        for key in PAID:
            self.assertNotIn(f'data-study-section="{key}"', c)
        self.assertNotIn("months", self.free["evidence_summary"])
        self.assertFalse(self.free["is_unlocked"])

    def test_truthy_non_bool_does_not_unlock(self):
        r = build_lifetime_study_report(self.core, "최정오", is_unlocked=1)
        self.assertNotIn('data-study-section="method"', r["content"])

    def test_reference_person(self):
        # 정오님 甲戌 일주: 인성 0 · 식상 2(午·巳) · 재성 3 → 해 보면서 익히는 응용형, 巳 문창귀인, 건축학과(토)·디자인(화)
        ev = self.paid["evidence_summary"]["v3"]
        self.assertEqual(ev["mind"], "make")
        self.assertTrue(ev["literary"])
        self.assertEqual(ev["fields"], ["火", "土"])
        self.assertEqual(ev["exam"], "practical")
        self.assertEqual(ev["leaks"][0], "busy")
        self.assertEqual(ev["now_state"], "exam")
        # 중학교 때 반에서 1·2등(정오님): 외우는 힘(인성)은 없어도 학교 공부 궁합은 좋음으로 나와야 한다
        self.assertEqual(ev["school"], "high")
        self.assertEqual(ev["school_cycle"], "good")
        self.assertEqual(ev["pathway"][:2], ["craft", "art"])
        t = _text(self.paid["content"])
        self.assertIn("건축·부동산·행정·사회과학", t)
        self.assertIn("남동쪽", t)

    def test_no_sentence_repeats(self):
        sents = [x.strip() for line in _text(self.paid["content"]).split("\n")
                 for x in re.split(r"(?<=[.!?])\s+", line) if len(x.strip()) > 12 and "월 · " not in x]
        self.assertEqual(len(sents), len(set(sents)), [s for s in sents if sents.count(s) > 1])

    def test_many_charts(self):
        rnd = random.Random(5)
        for _ in range(40):
            birth = datetime.date(1950, 1, 1) + datetime.timedelta(days=rnd.randrange(0, 20000))
            r = build_lifetime_study_report(_core(birth, rnd.choice(["male", "female"]), rnd.randrange(24), 0),
                                             "t", is_unlocked=True)
            t = _text(r["content"])
            self.assertIn('data-study-section="kaiun"', r["content"])
            self.assertEqual(find_banned(t), [], t[:200])
            self.assertEqual(len(re.findall(r'data-study-trap="', r["content"])), 3)
            sents = [x.strip() for line in t.split("\n") for x in re.split(r"(?<=[.!?])\s+", line)
                     if len(x.strip()) > 12 and "월 · " not in x]
            self.assertEqual(len(sents), len(set(sents)), [s for s in sents if sents.count(s) > 1])


if __name__ == "__main__":
    unittest.main()
