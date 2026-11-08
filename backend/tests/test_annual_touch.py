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
        basis = T.compose_basis(year=2026, year_stem="丙", year_branch="午",
                                natal={"year": "卯", "month": "巳", "day": "巳", "hour": "卯"}, day_stem="庚",
                                balance=dict(ranking=["水", "金", "土", "木", "火"], overflow=[], eokbu_avoid=[],
                                             composition={"木": 30, "火": 40, "土": 10, "金": 20, "水": 0}),
                                strength="", cycle=None, year_god=None)
        self.assertEqual(basis["items"][0]["sentences"], list(T.NO_TOUCH))


class CopyRulesTest(unittest.TestCase):
    def test_every_area_and_attitude_sentence_fits_the_annual_rules(self):
        bank = [s for d in T.ATTITUDE.values() for s in d.values()] + list(T.TRIPLE_ATTITUDE.values())
        bank += [T.STEM_CLASH_ATTITUDE, T.STEM_COMBINE_ATTITUDE, T.TRIPLE_PUNISH_ATTITUDE, *T.NO_TOUCH]
        bank += list(T.REASON.values()) + [s for pair in T.LINK.values() for s in pair[1:]]
        bank += [s for d in T.STAR_STATE.values() for s in d.values()]
        bank += list(T.LOVE_SEAT.values()) + list(T.HEALTH_STRENGTH.values())
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
        self.assertEqual(T._j(T._lab("戌"), "과와"), "戌(술)과")


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

    def test_basis_box_sits_after_areas_and_is_not_a_numbered_section(self):
        c = self.report["content"]
        self.assertEqual(c.count('class="annual-basis"'), 1)
        self.assertNotIn("annual-touch", c)
        box = c[c.index('class="annual-basis"'):c.index("<h3>12개월 흐름</h3>")]
        self.assertNotIn("<h3", box)                     # 번호 매기는 본문 h3 와 위계가 다르다
        self.assertIn("계산 기준", box)
        self.assertIn('data-period-basis="annual"', box)  # 대표일 설명이 상자 안에
        self.assertLess(c.index('data-report-domain="study"'), c.index('class="annual-basis"'))
        self.assertEqual(annual_v2.validate_year(self.report["reading"]), [])

    def test_every_area_has_three_to_five_sentences(self):
        for area in self.report["reading"]["areas"]:
            cap = annual_v2.AREA_SENTENCE_MAX_CENTRAL if area["central"] else annual_v2.AREA_SENTENCE_MAX
            self.assertTrue(3 <= len(area["sentences"]) <= cap, area)

    def test_owner_sample(self):
        r = self.report["reading"]
        text = " ".join(T.basis_sentence_list(r["basis"]))
        self.assertIn("배우자 자리(일지)의 戌(술)과 올해 午(오)가 반쯤 합쳐져 화(火) 기운이 커집니다(반합).", text)
        self.assertIn("이 관계는 애정 풀이에 반영했습니다.", text)
        self.assertIn("식신제살(食神制殺)", text)
        love = next(a for a in r["areas"] if a["area"] == "love")["text"]
        self.assertIn("가까운 사람과 함께하는 시간에서 힘을 얻는 해입니다.", love)
        work = next(a for a in r["areas"] if a["area"] == "work")["text"]
        self.assertIn("대운 庚申의 관성 기운", work)


if __name__ == "__main__":
    unittest.main()
