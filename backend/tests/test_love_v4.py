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

PAID = ("charm", "past", "palace", "weak", "match", "makeup", "remedy", "now", "partner", "cycle", "months", "place", "actions")


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
        self.assertIn(len(re.findall(r'data-love-action="\d"', c)), (4, 5))
        self.assertEqual(len(re.findall(r'data-love-trap="\d"', c)), 3)
        self.assertEqual(love_copy.find_sensitive(_text(c)), [])

    def test_locked_carries_no_paid_body(self):
        c = self.free["content"]
        for key in PAID:
            self.assertNotIn(f'data-love-section="{key}"', c)
        self.assertNotIn('data-paywall="unlocked"', c)
        self.assertNotIn("months", self.free["evidence_summary"])

    def test_key_months_skip_months_already_named_in_now_section(self):
        # '지금의 사랑'이 짚은 2027년 3월(도화·육합)·4월(충)은 눈여겨볼 달에서 되풀이하지 않고, 12달 목록에는 남는다
        c = self.paid["content"]
        for month in ("2027-03", "2027-04"):
            self.assertNotIn(f'data-love-key-month="{month}"', c)
            self.assertIn(f'data-love-month="{month}"', c)

    def test_no_sentence_repeats_within_a_report(self):
        sents = [x for x in re.split(r"(?<=[.!?])\s+|\n", _text(re.sub(r"<(p|li|strong|h2|h3)[^>]*>", "\n", self.paid["content"]))) if len(x.strip()) > 12]
        self.assertEqual(len(sents), len(set(sents)))

    def test_natal_peach_blossom_and_red_flower(self):
        # 정오님: 연지 午·일지 戌 → 도화 卯가 월지에(두 쪽이 같은 도화), 일간 甲의 홍염 午가 연지에
        t = _text(self.paid["content"])
        self.assertIn(sec.PEACH_PLACE["month"], t)
        self.assertIn(sec.PEACH_DOUBLE, t)
        self.assertIn(sec.REDFLOWER, t)
        ev = self.paid["evidence_summary"]["v4"]["charm"]
        self.assertEqual(ev["peach_positions"], ["month"])
        self.assertEqual(ev["redflower"], ["year"])
        self.assertIn(sec.CHARM_NONE.format(name="a")[:20], sec.charm_text("a", [], False, False))

    def test_remedy_section_for_reference_person(self):
        # 정오님: 필요한 오행 1순위 金 = 甲에게 관성 → 약속·기준 / 애정 십성에 재성 5 → 돈·생활 위기 / 일지 戌의 충 辰 = 2036 병진년
        # 도화 卯 = 동쪽
        c = self.paid["content"]
        ev = self.paid["evidence_summary"]["v4"]["remedy"]
        self.assertEqual((ev["key_group"], ev["risk"]), ("officer", "money"))
        t = _text(c)
        self.assertIn("2036년(병진년)", t)
        self.assertIn("동쪽", t)
        # 지금의 사랑 대화법(관성)이 열쇠와 같은 말이라 빠진다
        self.assertNotIn(love_copy.TALK["관성"], t)

    def test_chart_without_peach_gets_the_year_it_arrives(self):
        line = sec.charm_text("민지", [], False, False, sec.PEACH_YEAR_NONE.format(year=2029, ganji_ko="기유"))
        self.assertIn("도화가 드러나 있지 않아요", line)
        self.assertIn("2029년(기유년)은 도화가 드는 해", line)

    def test_depth_for_reference_person(self):
        # 11/13 정오님 결정: 남 = 재성이 인연의 별. 1998~99·2011·2023 인연의 해 → 2000·2012·2024 일지(戌) 충의 해
        dep = self.paid["evidence_summary"]["v4"]["depth"]
        self.assertEqual([(p["start"], p["end"], p["shake"]) for p in dep["periods"]],
                         [(1998, 1999, 2000), (2011, 2011, 2012), (2023, 2023, 2024)])
        self.assertEqual(dep["weak"], ["timing", "rival", "mixed"])     # 겁재 2(월간·월지), 정재·편재 섞임
        self.assertEqual(dep["palace"]["god"], "indirect_wealth")      # 일지 戌 본기 戊 = 편재
        t = _text(self.paid["content"])
        self.assertIn("28~47세", t)                                     # 戊午·己未 대운(재성)을 하나로
        self.assertIn("2028년(무신년), 2029년(기유년), 2035년(을묘년)", t)
        for banned in ("이별", "이혼", "결혼"):
            self.assertNotIn(banned, t)

    def test_female_uses_officer_as_star(self):
        core = _core(datetime.date(1990, 5, 5), "female", 9)
        r = build_lifetime_love_report(core, "a", is_unlocked=True)
        self.assertEqual(r["evidence_summary"]["v4"]["depth"]["gender_star"], "female")
        self.assertIn("정관·편관", _text(r["content"])) if r["evidence_summary"]["v4"]["depth"]["periods"] else None

    def test_tier1_does_not_preview_the_habits(self):
        # 11/13: 1단 B 문장(표현 방식)은 2단 습관과 겹쳐서 뺐다
        from app.engine.services import love_copy as lc
        self.assertNotIn(lc.TIER1["reality"]["B"], self.paid["content"])

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
