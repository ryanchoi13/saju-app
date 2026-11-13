"""애정운 v3 (11/06): 잘 맞는 사람·지금의 사랑 추가, 연애 상태 선택 제거."""
import datetime
import random
import re
import unittest

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services.love import LOVE_NARRATIVE_VERSION, build_lifetime_love_report
from app.engine.services import love_copy


def _core(birth, target=datetime.date(2026, 11, 6), gender="male", hour=10):
    return calculate_myeongri_core(
        BirthInput(name="t", gender=gender, birth_date=birth, birth_time=datetime.time(hour, 30)),
        target_date=target)


def _text(html):
    return re.sub(r"<[^>]+>", " ", html)


class LoveV3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.core = _core(datetime.date(1978, 3, 13))
        cls.unlocked = build_lifetime_love_report(cls.core, "최정오", is_unlocked=True)
        cls.locked = build_lifetime_love_report(cls.core, "최정오")

    def test_version(self):
        self.assertEqual(self.unlocked["narrative_version"], LOVE_NARRATIVE_VERSION)
        self.assertEqual(LOVE_NARRATIVE_VERSION, "love-v4")

    def test_unlocked_has_new_sections_in_order(self):
        c = self.unlocked["content"]
        order = [c.index(f'data-love-tier="{t}"') for t in ("1", "2", "match", "now", "3", "4")]  # v4: 12개월 칸이 지금의 사랑 뒤로
        self.assertEqual(order, sorted(order))
        for title in (love_copy.MATCH_GOOD_TITLE, love_copy.MATCH_BAD_TITLE,
                      love_copy.NOW_SINGLE_TITLE, love_copy.NOW_COUPLE_TITLE):
            self.assertIn(title, c)

    def test_chart_values_for_reference_person(self):
        # 일지 戌: 육합 卯, 충 辰 / 대운 庚申(관성) / 2027 丁未(식상) / 도화 卯 = 2027년 3월
        t = _text(self.unlocked["content"])
        self.assertIn(love_copy.BRANCH_PERSON["卯"], t)
        self.assertIn(love_copy.BRANCH_PERSON["辰"], t)
        self.assertIn(love_copy.MEET_PATH["관성"], t)
        self.assertIn(love_copy.MEET_PATH["식상"], t)
        self.assertIn("2027년 3월은 도화가 들고", t)
        self.assertIn("2027년 4월은 사소한 일로", t)

    def test_locked_does_not_leak_new_sections(self):
        c = self.locked["content"]
        for marker in ('data-love-tier="match"', 'data-love-tier="now"', love_copy.MATCH_GOOD_TITLE,
                       love_copy.NOW_COUPLE_TITLE, "data-love-basis"):
            self.assertNotIn(marker, c)
        self.assertNotIn("match", self.locked["evidence_summary"])

    def test_status_no_longer_changes_the_reading(self):
        base = build_lifetime_love_report(self.core, "최정오", is_unlocked=True)["content"]
        for status in love_copy.STATUSES:
            with self.subTest(status=status):
                self.assertEqual(build_lifetime_love_report(self.core, "최정오", status, is_unlocked=True)["content"], base)

    def test_new_copy_bank_has_no_flagged_words(self):
        bank = [*love_copy.BRANCH_PERSON.values(), love_copy.MATCH_GOOD, love_copy.MATCH_BAD,
                *love_copy.MEET_PATH.values(), *love_copy.TALK.values(), love_copy.NOW_PATH_SAME,
                love_copy.NOW_PATH_TWO, love_copy.NOW_PEACH, love_copy.NOW_PEACH_COMBO,
                love_copy.NOW_COUPLE_MONTHS, love_copy.NOW_TALK, love_copy.COMMON_BULLET,
                *love_copy.MONTH_TEXT["opportunity"], *love_copy.MONTH_TEXT["caution"],
                love_copy.NOW_SINGLE_TITLE, love_copy.NOW_COUPLE_TITLE]
        for line in bank:
            with self.subTest(line=line):
                self.assertEqual(love_copy.find_flagged(line), [])

    def test_name_is_escaped(self):
        r = build_lifetime_love_report(self.core, "<img src=x>", is_unlocked=True)
        self.assertNotIn("<img", r["content"])

    def test_many_charts_render(self):
        rnd = random.Random(7)
        for _ in range(120):
            birth = datetime.date(1940, 1, 1) + datetime.timedelta(days=rnd.randrange(0, 31000))
            core = _core(birth, gender=rnd.choice(["male", "female"]), hour=rnd.randrange(0, 24))
            with self.subTest(birth=birth):
                r = build_lifetime_love_report(core, "t", is_unlocked=True)
                self.assertIn('data-love-tier="now"', r["content"])
                self.assertEqual(love_copy.find_sensitive(_text(r["content"])), [])
        # 첫 대운 전인 어린아이도 깨지지 않는다
        r = build_lifetime_love_report(_core(datetime.date(2024, 5, 1)), "t", is_unlocked=True)
        self.assertIn(love_copy.NOW_SINGLE_TITLE, r["content"])


    def test_bought_readings_refresh_whatever_status_was_saved(self):
        import main
        user = {"name": "최정오", "gender": "male", "birth_year": 1978, "birth_month": 3, "birth_day": 13,
                "calendar_type": "solar", "sijin_index": 5}
        for option in ("기본", "솔로", "기혼", None):
            with self.subTest(option=option):
                original = dict(report_key="love", report_content="옛 풀이", narrative_version="love-4tier-v2",
                                reading_context=dict(sub_option=option) if option else {})
                rebuilt = main._rebuilt_report(user, original, LOVE_NARRATIVE_VERSION)
                self.assertIsNotNone(rebuilt)
                self.assertEqual(rebuilt["narrative_version"], LOVE_NARRATIVE_VERSION)
                self.assertIn('data-love-tier="now"', rebuilt["report_content"])


if __name__ == "__main__":
    unittest.main()
