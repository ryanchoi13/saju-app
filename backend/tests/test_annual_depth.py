"""올해 운세 분량·깊이 보강 (2026-11-15 정오님 2.5~3배).

- 문장 규칙(46자·얼버무림·시점 표현·금기어·같은 문장 반복) 위반 0
- 새 칸 세 개(힘이 되는 사람·신살·개운법)가 모두 나온다
- 분야마다 '이렇게 해 보세요'·'조심할 점' 단락이 있다
- 상·하반기는 따로 칸이 아니라 문장에 녹는다(전용 제목 없음)
- 본문(근거 상자 제외) 1,800자 이상 — 보강 전 평균 약 770자
"""
import datetime
import random
import re
import unittest

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services import annual_depth, annual_v2
from app.engine.services.annual import build_annual_overall_report
from app.engine.services.annual_copy import split_sentences


class AnnualDepthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rnd = random.Random(15)
        cls.reports = []
        for _ in range(24):
            b = datetime.date(1950, 1, 1) + datetime.timedelta(days=rnd.randrange(26000))
            core = calculate_myeongri_core(
                BirthInput(name="t", gender=rnd.choice(["male", "female"]), birth_date=b,
                           birth_time=datetime.time(rnd.randrange(24), 0)),
                target_date=datetime.date(2026, 11, 15))
            cls.reports.append(build_annual_overall_report(core, "t", rnd.choice([2026, 2027])))

    def test_copy_rules_hold(self):
        for r in self.reports:
            self.assertEqual(annual_v2.validate_year(r["reading"]), [])

    def test_new_sections_and_area_tips(self):
        for r in self.reports:
            self.assertEqual([e["key"] for e in r["reading"]["extras"]], ["people", "shinsal", "gaewoon"])
            html = r["content"]
            self.assertEqual(html.count('data-annual-tip="do"'), 5)
            self.assertEqual(html.count('data-annual-tip="watch"'), 5)
            self.assertNotIn("<h3>상반기", html)
            self.assertNotIn("<h3>하반기", html)

    def test_body_is_at_least_two_and_a_half_times(self):
        for r in self.reports:
            year = r["content"].split("12개월 흐름")[0].split("이 풀이의 근거")[0]
            self.assertGreaterEqual(len(re.sub(r"\s", "", re.sub(r"<[^>]+>", "", year))), 1800)

    def test_bank_sentence_lengths(self):
        pools = [annual_depth.OVERVIEW_MORE_GENERAL, annual_depth.THREE_MORE_GENERAL, *annual_depth.OVERVIEW_MORE.values(),
                 *annual_depth.THREE_MORE.values(), *annual_depth.PEOPLE.values(), *annual_depth.SHINSAL_YEAR.values(),
                 *annual_depth.GAEWOON.values(), *annual_depth.HALF.values(), annual_depth.CENTRAL_LEAD.values()]
        for areas in [*annual_depth.AREA_MORE.values(), annual_depth.AREA_MORE_GENERAL]:
            for do, watch in areas.values():
                pools.append(split_sentences(do) + split_sentences(watch))
        for pool in pools:
            for s in pool:
                self.assertLessEqual(len(s), annual_v2.SENTENCE_MAX, s)


if __name__ == "__main__":
    unittest.main()
