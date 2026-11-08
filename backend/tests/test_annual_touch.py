"""올해 운세 보강 단락(annual_touch, 2026-11-08)."""
import unittest
from datetime import date, time

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services import annual_touch as T
from app.engine.services import annual_v2
from app.engine.services.annual import build_annual_overall_report

# 정오님 원국(재현용): 戊午 · 乙卯 · 甲戌 · 己巳
NATAL = {"year": "午", "month": "卯", "day": "戌", "hour": "巳"}


class NatalTouchTest(unittest.TestCase):
    def test_bingwu_half_combine_on_day_and_self_punish_on_year(self):
        kinds = [(t["kind"], t["pos"]) for t in T.natal_touch("丙", "午", NATAL, "甲")]
        self.assertEqual(kinds, [("half", "day"), ("self", "year")])

    def test_break_and_harm_are_not_used(self):
        # 卯午 파(破)는 쓰지 않는다 — 월지 卯는 관계 목록에 없어야 한다
        self.assertNotIn("month", [t["pos"] for t in T.natal_touch("丙", "午", NATAL, "甲")])

    def test_one_relation_per_position_and_at_most_two(self):
        # 申 × 巳 는 육합이면서 형 — 한 자리에는 하나만(형이 먼저)
        found = T.natal_touch("壬", "申", {"year": "巳", "month": "寅", "day": "子", "hour": "辰"}, "甲")
        self.assertLessEqual(len(found), 2)
        positions = [t["pos"] for t in found if t["pos"]]
        self.assertEqual(len(positions), len(set(positions)))

    def test_completed_triple_absorbs_half_combines(self):
        found = T.natal_touch("甲", "辰", {"year": "申", "month": "子", "day": "卯", "hour": "未"}, "丙")
        self.assertEqual(found[0]["kind"], "triple")
        self.assertNotIn("half", [t["kind"] for t in found])

    def test_no_relation_says_so_without_inventing(self):
        touch = T.compose_touch(year=2026, year_stem="丙", year_branch="午",
                                natal={"year": "卯", "month": "巳", "day": "巳", "hour": "卯"}, day_stem="庚",
                                balance=dict(ranking=["水", "金", "土", "木", "火"], overflow=[], eokbu_avoid=[]),
                                strength="", cycle=None, year_god=None)
        self.assertEqual(touch["sections"][0]["paragraphs"], [list(T.NO_TOUCH)])


class CopyRulesTest(unittest.TestCase):
    def test_every_attitude_sentence_fits_the_annual_rules(self):
        bank = [s for d in T.ATTITUDE.values() for s in d.values()] + list(T.TRIPLE_ATTITUDE.values())
        bank += [T.STEM_CLASH_ATTITUDE, T.STEM_COMBINE_ATTITUDE, T.TRIPLE_PUNISH_ATTITUDE, *T.NO_TOUCH]
        bank += list(T.REASON.values()) + [s for pair in T.LINK.values() for s in pair[1:]]
        self.assertEqual(len(bank), len(set(bank)))
        for s in bank:
            self.assertLessEqual(len(s), annual_v2.SENTENCE_MAX, s)
            for w in annual_v2.HEDGES + annual_v2.TIME_WORDS:
                self.assertNotIn(w, s)

    def test_particles_follow_the_korean_reading(self):
        self.assertEqual(T._j("戌", "과와"), "戌과")     # 술
        self.assertEqual(T._j("午", "과와"), "午와")     # 오
        self.assertEqual(T._j("화(火)", "이가"), "화(火)가")
        self.assertEqual(T._j("금(金)", "이가"), "금(金)이")
        self.assertEqual(T._jp("관성", "을를"), "을")


class CycleLinkTest(unittest.TestCase):
    def test_generating_and_controlling_order(self):
        self.assertEqual(T._link("식상", "식상"), "same")
        self.assertEqual(T._link("식상", "재성"), "year_feeds")
        self.assertEqual(T._link("식상", "비겁"), "cycle_feeds")
        self.assertEqual(T._link("식상", "관성"), "year_controls")
        self.assertEqual(T._link("식상", "인성"), "cycle_controls")


class ReportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        core = calculate_myeongri_core(BirthInput(
            name="정오", gender="male", birth_date=date(1978, 3, 13), calendar_type="solar",
            is_leap_month=False, birth_time=time(11, 0), time_unknown=False), target_date=date(2026, 7, 1))
        cls.report = build_annual_overall_report(core, "정오", 2026)

    def test_three_sections_sit_between_overview_and_three_things(self):
        c = self.report["content"]
        for key in ("natal", "balance", "cycle"):
            self.assertEqual(c.count(f'data-annual-touch="{key}"'), 1)
        self.assertLess(c.index("annual-overview"), c.index('data-annual-touch="natal"'))
        self.assertLess(c.index('data-annual-touch="cycle"'), c.index("annual-three"))
        self.assertEqual(annual_v2.validate_year(self.report["reading"]), [])

    def test_owner_sample(self):
        text = " ".join(T.touch_sentence_list(self.report["reading"]["touch"]))
        self.assertIn("일지 戌과 올해 午가 반합해 화(火) 쪽으로 기웁니다.", text)
        self.assertIn("두 번째 보완 기운 화(火)가", text)
        self.assertIn("식신제살(食神制殺)", text)
        self.assertIn("올해는 그 두 번째 해입니다.", text)


if __name__ == "__main__":
    unittest.main()
