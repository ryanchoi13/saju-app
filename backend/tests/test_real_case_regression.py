"""Golden real-date cases that previously exposed root/backend discrepancies."""

from datetime import date, time
from unittest import TestCase

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.pillars import calculate_saju


CASES = (
    # date, gender, year, month, day, noon hour, day index (甲子=0)
    (date(1978, 3, 13), "male", "戊午", "乙卯", "甲戌", "庚午", 10),
    (date(1978, 8, 13), "male", "戊午", "庚申", "丁未", "丙午", 43),
    (date(1990, 5, 15), "male", "庚午", "辛巳", "庚辰", "壬午", 16),
    (date(1995, 5, 5), "female", "乙亥", "庚辰", "丙申", "甲午", 32),
)

STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"


def _jdn(value: date) -> int:
    """Independent Gregorian Julian-day-number calculation for day-pillar checks."""

    a = (14 - value.month) // 12
    year = value.year + 4800 - a
    month = value.month + 12 * a - 3
    return (
        value.day + (153 * month + 2) // 5 + 365 * year
        + year // 4 - year // 100 + year // 400 - 32045
    )


class RealCaseRegressionTests(TestCase):
    def test_four_real_dates_match_golden_pillars(self):
        for birth_date, gender, year, month, day, hour, _ in CASES:
            with self.subTest(birth_date=birth_date):
                result = calculate_saju(
                    birth_date=birth_date,
                    calendar_type="solar",
                    birth_time=time(12, 0),
                    time_unknown=False,
                    gender=gender,
                )
                self.assertEqual(result.year.han_label, year)
                self.assertEqual(result.month.han_label, month)
                self.assertEqual(result.day.han_label, day)
                self.assertEqual(result.time_pillar.han_label, hour)

    def test_day_pillars_match_independent_julian_day_formula(self):
        for birth_date, _, _, _, expected, _, expected_index in CASES:
            with self.subTest(birth_date=birth_date):
                index = (_jdn(birth_date) + 49) % 60
                ganji = STEMS[index % 10] + BRANCHES[index % 12]
                self.assertEqual(index, expected_index)
                self.assertEqual(ganji, expected)

    def test_legacy_and_new_core_share_the_same_objective_pillars(self):
        for birth_date, gender, year, month, day, hour, _ in CASES:
            with self.subTest(birth_date=birth_date):
                legacy = calculate_saju(
                    birth_date=birth_date,
                    calendar_type="solar",
                    birth_time=time(12, 0),
                    time_unknown=False,
                    gender=gender,
                )
                core = calculate_myeongri_core(
                    BirthInput(
                        name="검증",
                        gender=gender,
                        birth_date=birth_date,
                        birth_time=time(12, 0),
                    ),
                    target_date=date(2026, 9, 7),
                )
                self.assertEqual(
                    [core.natal_facts.pillars[key].ganji for key in ("year", "month", "day", "hour")],
                    [year, month, day, hour],
                )
                self.assertEqual(core.natal_facts.pillars["day"].stem, legacy.day_master_han)

    def test_lunar_equivalent_keeps_the_same_pillars(self):
        solar = calculate_saju(
            birth_date=date(1990, 5, 15), calendar_type="solar",
            birth_time=time(12), gender="male",
        )
        lunar = calculate_saju(
            birth_date=date(1990, 4, 21), calendar_type="lunar",
            birth_time=time(12), gender="male",
        )
        self.assertEqual(lunar.solar_date, solar.solar_date)
        self.assertEqual(
            [lunar.year.han_label, lunar.month.han_label, lunar.day.han_label, lunar.time_pillar.han_label],
            [solar.year.han_label, solar.month.han_label, solar.day.han_label, solar.time_pillar.han_label],
        )
