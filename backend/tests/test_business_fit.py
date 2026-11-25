"""일의 성격 매핑 · 사업 선택지 비교 · 5년 흐름 · 사업 택일 (2026-11-25)."""
import datetime
import re
import unittest

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services import business_fit as bf
from app.engine.services import business_timing as bt
from app.engine.services.annual_copy import find_banned
from app.engine.services.career import build_lifetime_career_report
from app.engine.services.daily_score import calendar_ganji
from app.engine.services.theme_core import CLASH

HEDGE = re.compile(r"수 있어요|수 있습니다|일지도")


def _core(birth=datetime.date(1978, 3, 13), time=datetime.time(11, 0), gender="male"):
    return calculate_myeongri_core(
        BirthInput(name="시험", gender=gender, birth_date=birth, birth_time=time, time_unknown=time is None),
        target_date=datetime.date(2026, 11, 25))


class BusinessFitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.core = _core()

    def test_copy_has_no_banned_words_or_hedges(self):
        bank = (list(bf.FIT_TEXT.values()) + list(bt.RULE_TEXT.values()) + [bf.LIMIT_NOTE, bf.MULTI_NOTE]
                + list(bf.NATURE_NAME.values()))
        for s in bank:
            self.assertEqual(find_banned(s), [], s)
            self.assertIsNone(HEDGE.search(s), s)

    def test_natal_stars_are_counted(self):
        # 갑목 일간: 재성(戊·戌·己) 셋 → 재성 줄기는 '타고난 감각'이 걸려야 한다(십성 이름 키가 맞는지 확인)
        self.assertIn("natal_rich", bf.nature_fit(self.core, "wealth", 2026)["rules"])
        self.assertEqual(bt.natal_peer_count(self.core), 2)

    def test_lifetime_ranking_ignores_current_cycle(self):
        with_cycle = {r["nature"]: r["rules"] for r in bf.nature_ranking(self.core, 2026)}
        natal_only = {r["nature"]: r["rules"] for r in bf.nature_ranking(self.core, 2026, with_cycle=False)}
        self.assertFalse(any("cycle_same" in v for v in natal_only.values()))
        self.assertTrue(any("cycle_same" in v for v in with_cycle.values()))

    def test_career_report_splits_work_by_nature(self):
        r = build_lifetime_career_report(self.core, "최정오", "창업", is_unlocked=True)
        jobs = re.search(r'data-career-section="jobs".*?</section>', r["content"], re.S).group(0)
        self.assertIn("일의 성격으로 나눠 보면", jobs)
        self.assertEqual(find_banned(re.sub(r"<[^>]+>", "", jobs)), [])

    def test_compare_flags_partnership_and_big_money(self):
        res = bf.compare_options(self.core, [
            dict(name="가", category="content_app", capital="low"),
            dict(name="나", category="care_service", capital="high", partnership=True),
        ], 2027)
        by = {o["name"]: o for o in res["options"]}
        self.assertIn("partner_risk", by["나"]["rules"])
        self.assertIn("capital_keep_cycle", by["나"]["rules"])
        self.assertEqual(res["options"][0]["name"], "가")
        self.assertIn(bf.LIMIT_NOTE, res["notes"])
        self.assertIn(bf.MULTI_NOTE, res["notes"])

    def test_compare_rejects_unknown_category(self):
        with self.assertRaises(ValueError):
            bf.compare_options(self.core, [dict(name="?", category="nope")], 2027)

    def test_custom_option_without_catalog(self):
        res = bf.compare_options(self.core, [dict(name="직접", natures=["resource"], element="水")], 2027)
        self.assertEqual(res["options"][0]["nature_name"], bf.NATURE_NAME["resource"])

    def test_five_year_flow(self):
        rows = bt.five_year_flow(self.core, 2027)
        self.assertEqual([r["year"] for r in rows], [2027, 2028, 2029, 2030, 2031])
        self.assertEqual(rows[0]["ganji"], "丁未")
        for r in rows:
            self.assertEqual(set(r["events"]), set(bt.EVENTS))
            for e in r["events"].values():
                self.assertIn(e["grade"], ("good", "normal", "caution"))
                self.assertEqual(len(e["rules"]), len(e["reasons"]))
        # 원국 비겁 2 → 동업은 어느 해도 '좋음'이 아니다
        self.assertTrue(all(r["events"]["partner"]["grade"] != "good" for r in rows))
        # 己酉년: 酉가 월지 卯와 충 → 문 열기 규칙에 month_clash
        self.assertIn("month_clash", rows[2]["events"]["open"]["rules"])

    def test_pick_days_skip_clash_days(self):
        p = self.core.natal_facts.pillars
        bad = {CLASH[p["day"].branch], CLASH[p["month"].branch]}
        days = bt.pick_days(self.core, 2027, 6)
        self.assertTrue(0 < len(days) <= 5)
        self.assertEqual(days, sorted(days, key=lambda d: d["date"]))
        for d in days:
            gz = calendar_ganji(datetime.date.fromisoformat(d["date"]))[2]
            self.assertEqual(gz, d["ganji"])
            self.assertNotIn(gz[1], bad)
        self.assertTrue(bt.pick_days(self.core, 2027, 3, "contract"))

    def test_other_charts_render(self):
        for birth, t, g in ((datetime.date(1990, 8, 2), datetime.time(4, 0), "female"),
                            (datetime.date(2001, 12, 30), None, "male")):
            core = _core(birth, t, g)
            ranks = bf.nature_ranking(core, 2026)
            self.assertEqual(len(ranks), 5)
            bf.nature_text(core, "balanced", 2026)
            bf.compare_options(core, [dict(category=k) for k in list(bf.CATALOG)[:3]], 2027)


if __name__ == "__main__":
    unittest.main()
