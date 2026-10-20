"""테마운 3단 타이밍: 앞으로 12개월 + 세운 맥락 (사전식 비교, 합산 없음)."""
import datetime
import re
import unittest

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services import theme_timing as tt
from app.engine.services.career import build_lifetime_career_report
from app.engine.services.health import build_lifetime_health_report
from app.engine.services.love import build_lifetime_love_report
from app.engine.services.love_copy import find_sensitive


def _core(today):
    return calculate_myeongri_core(
        BirthInput(name="최정오", gender="male", birth_date=datetime.date(1978, 3, 13),
                   birth_time=datetime.time(11, 0)),
        target_date=today)


def _row(i, score, annual_score):
    return dict(year=2027, month=i, score=score, annual_score=annual_score,
                annual=dict(ganji="丁未", luck_cycle="庚申", mode=None))


class WindowTests(unittest.TestCase):
    def test_start_skips_month_whose_15th_has_passed(self):
        core = _core(datetime.date(2026, 10, 21))
        self.assertEqual(tt.window_start(core, datetime.date(2026, 10, 15)), (2026, 10))
        self.assertEqual(tt.window_start(core, datetime.date(2026, 10, 16)), (2026, 11))
        self.assertEqual(tt.window_start(core, datetime.date(2026, 12, 20)), (2027, 1))
        self.assertEqual(tt.window_start(core), (2026, 11))

    def test_window_crosses_year(self):
        months = tt.window_months((2026, 11))
        self.assertEqual(len(months), 12)
        self.assertEqual(months[0], (2026, 11))
        self.assertEqual(months[-1], (2027, 10))


class ChooseTests(unittest.TestCase):
    def test_annual_alone_never_selects_a_month(self):
        rows = [_row(m, 0, 2) for m in range(1, 13)]
        self.assertEqual(tt.choose(rows), [])

    def test_monthly_score_outranks_annual_no_summation(self):
        rows = [_row(1, 1, 2)] + [_row(m, 2, -2) for m in (2, 3, 4)] + [_row(m, 0, 0) for m in range(5, 13)]
        months = [r["month"] for r, _ in tt.choose(rows)]
        self.assertEqual(months, [2, 3, 4])  # 합산(1+2=3 > 2-2=0)이었다면 1월이 뽑혔을 것

    def test_annual_breaks_ties(self):
        rows = [_row(1, 2, -1), _row(2, 2, 1), _row(3, 2, 0)] + [_row(m, 0, 0) for m in range(4, 13)]
        months = [r["month"] for r, _ in tt.choose(rows)]
        self.assertEqual(len(months), 3)
        first_opp = max(rows[:3], key=lambda r: r["annual_score"])
        self.assertIn(first_opp["month"], months)


class ServiceTests(unittest.TestCase):
    @staticmethod
    def _months(report):
        return re.findall(r'data-love-month="(\d{4}-\d{2})"', report["content"])

    def test_love_window_changes_by_viewing_year_and_skips_past(self):
        a = build_lifetime_love_report(_core(datetime.date(2026, 10, 21)), "최정오", "솔로", is_unlocked=True)
        b = build_lifetime_love_report(_core(datetime.date(2027, 10, 21)), "최정오", "솔로", is_unlocked=True)
        ma, mb = self._months(a), self._months(b)
        self.assertTrue(ma and mb)
        self.assertTrue(all("2026-11" <= m <= "2027-10" for m in ma))
        self.assertTrue(all("2027-11" <= m <= "2028-10" for m in mb))
        self.assertIn("앞으로 12개월 관계의 타이밍", a["content"])
        self.assertIn("years", a["evidence_summary"])
        self.assertEqual(find_sensitive(a["content"]), [])

    def test_locked_reports_compute_no_months(self):
        core = _core(datetime.date(2026, 10, 21))
        for r in (build_lifetime_love_report(core, "a", "솔로"),
                  build_lifetime_career_report(core, "a"),
                  build_lifetime_health_report(core, "a")):
            self.assertNotIn("months", r["evidence_summary"])
            self.assertNotIn("years", r["evidence_summary"])
            self.assertNotIn('data-paywall="unlocked"', r["content"])

    def test_explicit_year_keeps_calendar_year(self):
        r = build_lifetime_love_report(_core(datetime.date(2026, 10, 21)), "a", "솔로",
                                       is_unlocked=True, year=2026)
        self.assertTrue(all(m.startswith("2026-") for m in self._months(r)))


if __name__ == "__main__":
    unittest.main()
