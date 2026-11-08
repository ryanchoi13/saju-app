"""오늘운세 날짜 줄의 음력·달 모양·뜻 있는 날 한 줄 (2026-11-08)."""
import unittest
from datetime import date

from app.engine.services.lunar_day import TERM_KO, TERM_NOTE, lunar_info, phase_name


class LunarDayTest(unittest.TestCase):
    def test_known_dates(self):
        info = lunar_info(date(2026, 11, 8))
        self.assertEqual({k: info[k] for k in ("month", "day", "leap", "phase", "next_term", "days_to_term")},
                         dict(month=9, day=30, leap=False, phase="그믐", next_term="소설", days_to_term=14))
        self.assertNotIn("special", info)                                   # 보통 날은 한 줄 없음
        self.assertEqual(lunar_info(date(2026, 11, 9))["special"]["name"], "음력 초하루")
        self.assertEqual(lunar_info(date(2026, 12, 22))["special"], dict(name="동지", note=TERM_NOTE["동지"]))

    def test_phase_ranges(self):
        self.assertEqual([phase_name(d) for d in (1, 3, 8, 12, 15, 18, 22, 27, 30)],
                         ["초하루", "초승달", "상현달", "차오르는 달", "보름달", "기우는 달", "하현달", "그믐달", "그믐"])

    def test_every_term_has_a_note_and_a_year_has_24_term_days(self):
        self.assertEqual(set(TERM_NOTE), set(TERM_KO.values()))
        start, terms = date(2026, 1, 1), set()
        for i in range(365):
            info = lunar_info(date.fromordinal(start.toordinal() + i))
            self.assertTrue(1 <= info["day"] <= 30)
            if info.get("special") and info["special"]["name"] in TERM_NOTE:
                terms.add(info["special"]["name"])
        self.assertEqual(len(terms), 24)


if __name__ == "__main__":
    unittest.main()
