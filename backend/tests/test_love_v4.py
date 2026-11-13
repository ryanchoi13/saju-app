"""애정운 v4 (2026-11-13 정오님: 직업운 v3와 같은 틀 · 칸 10개 · 12달 등급)."""
import datetime
import html
import random
import re
import unittest

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services import love_copy, love_sections as sec
from app.engine.services.love import build_lifetime_love_report

PAID = ("express", "match", "fight", "now", "cycle", "months", "place", "actions")


def _core(birth=datetime.date(1978, 3, 13), gender="male", hour=11):
    return calculate_myeongri_core(
        BirthInput(name="t", gender=gender, birth_date=birth, birth_time=datetime.time(hour, 0)),
        target_date=datetime.date(2026, 11, 13))


def _text(content: str) -> str:
    content = re.sub(r'<details class="reading-evidence">.*?</details>', "", content, flags=re.S)
    return html.unescape(re.sub(r"<[^>]+>", "", content))


class LoveV4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.core = _core()
        cls.paid = build_lifetime_love_report(cls.core, "최정오", is_unlocked=True)
        cls.free = build_lifetime_love_report(cls.core, "최정오")

    def test_bank_has_no_flagged_words_or_hedges(self):
        for s in sec.all_sentences():
            self.assertEqual(love_copy.find_flagged(s), [], s)
            self.assertIsNone(re.search(r"수 있어요|수 있습니다|일지도", s), s)

    def test_paid_has_all_sections_and_double_the_old_length(self):
        c = self.paid["content"]
        for key in ("nature", "traps", *PAID):
            self.assertIn(f'data-love-section="{key}"', c)
        self.assertGreaterEqual(len(_text(c)), 2912)          # 옛 애정운 1,456자의 2배(직업운 v3와 비슷한 분량)
        self.assertEqual(len(re.findall(r'data-love-month="\d{4}-\d{2}"', c)), 12)
        self.assertEqual(len(re.findall(r'data-love-action="\d"', c)), 5)
        self.assertEqual(len(re.findall(r'data-love-trap="\d"', c)), 3)
        self.assertEqual(love_copy.find_sensitive(_text(c)), [])

    def test_locked_carries_no_paid_body(self):
        c = self.free["content"]
        for key in PAID:
            self.assertNotIn(f'data-love-section="{key}"', c)
        self.assertNotIn('data-paywall="unlocked"', c)
        self.assertNotIn("months", self.free["evidence_summary"])

    def test_good_key_month_agrees_with_now_section(self):
        # 일지 戌의 육합 卯 = 2027년 3월: '지금의 사랑'과 '눈여겨볼 달'·실천 원칙이 같은 달을 가리킨다
        c = self.paid["content"]
        self.assertIn('data-love-key-month="2027-03"', c)
        self.assertIn("2027년 3월처럼", _text(c))

    def test_gender_rule_is_not_used(self):
        for m in self.paid["evidence_summary"]["months"]:
            self.assertNotEqual(m["reason"], "이성 인연의 기운")

    def test_copula_follows_last_element(self):
        self.assertIn("금(金)이에요", sec.place_text("a", ["火", "金"]))
        self.assertIn("화(火)예요", sec.place_text("a", ["金", "火"]))

    def test_many_charts_render(self):
        rnd = random.Random(11)
        for _ in range(40):
            birth = datetime.date(1950, 1, 1) + datetime.timedelta(days=rnd.randrange(0, 20000))
            r = build_lifetime_love_report(_core(birth, rnd.choice(["male", "female"]), rnd.randrange(0, 24)),
                                           "t", is_unlocked=True)
            self.assertIn('data-love-section="actions"', r["content"])
            self.assertEqual(love_copy.find_flagged(_text(r["content"])), [])


if __name__ == "__main__":
    unittest.main()
