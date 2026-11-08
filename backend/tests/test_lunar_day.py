"""홈 머리의 음력·달 모양·다음 절기 (A안 '일력', 2026-11-08)."""
import unittest
from datetime import date

from app.engine.services.lunar_day import lunar_info, phase_name


class LunarDayTest(unittest.TestCase):
    def test_known_dates(self):
        self.assertEqual(lunar_info(date(2026, 11, 8)),
                         dict(month=9, day=30, leap=False, phase="그믐", next_term="소설", days_to_term=14, prev_term="입동"))
        self.assertEqual(lunar_info(date(2026, 11, 9))["phase"], "초하루")
        self.assertEqual(lunar_info(date(2026, 12, 22))["days_to_term"], 0)     # 동지 당일

    def test_phase_ranges(self):
        self.assertEqual([phase_name(d) for d in (1, 3, 8, 12, 15, 18, 22, 27, 30)],
                         ["초하루", "초승달", "상현달", "차오르는 달", "보름달", "기우는 달", "하현달", "그믐달", "그믐"])

    def test_every_day_of_a_year_has_a_korean_term_name(self):
        d = date(2026, 1, 1)
        for i in range(365):
            info = lunar_info(date.fromordinal(d.toordinal() + i))
            self.assertIn("next_term", info)
            self.assertTrue(1 <= info["day"] <= 30)


if __name__ == "__main__":
    unittest.main()
