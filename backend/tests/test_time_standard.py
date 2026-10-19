"""달하 시간 기준(dalha-time-v1) 경계 사례 회귀 테스트.

기준
- 절기(년주·월주·대운): 실제 출생 순간 기준. 입력은 출생 당시 한국 벽시계 시각.
- 일주·시주: 서울 평균태양시(경도 126.98°) 기준, 23시(태양시)에 날이 바뀜.
- 시대별 한국 표준시(1954~1961 UTC+8:30)와 서머타임은 Asia/Seoul 시간대 데이터로 반영.
"""
import unittest
from datetime import date, time

from app.engine.calendar import natal_eight_chars, resolve_birth_moment
from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core


def natal(y, m, d, hh, mm):
    n = natal_eight_chars(date(y, m, d), hh, mm)
    return (n.seasonal.getYear(), n.seasonal.getMonth(), n.daily.getDay(), n.daily.getTime())


class SolarTermBoundaryTests(unittest.TestCase):
    # 2024 입춘: 한국 시각 2024-02-04 17:27
    def test_before_ipchun_in_korea_is_previous_year(self):
        self.assertEqual(natal(2024, 2, 4, 17, 0)[:2], ("癸卯", "乙丑"))

    def test_after_ipchun_in_korea_is_new_year(self):
        self.assertEqual(natal(2024, 2, 4, 17, 40)[:2], ("甲辰", "丙寅"))


class SolarTimeTests(unittest.TestCase):
    def test_modern_birth_shifts_about_32_minutes(self):
        m = resolve_birth_moment(date(1990, 5, 15), 13, 20)
        self.assertEqual(m.solar_clock.strftime("%H:%M"), "12:47")

    def test_clock_0110_is_still_ja_hour(self):
        # 시계 01:10 → 태양시 00:38 → 자시
        self.assertEqual(natal(1990, 5, 15, 1, 10)[3][1], "子")

    def test_clock_0140_is_chuk_hour(self):
        self.assertEqual(natal(1990, 5, 15, 1, 40)[3][1], "丑")

    def test_1954_to_1961_standard_time_needs_almost_no_shift(self):
        # 당시 표준시 UTC+8:30 → 태양시와 약 2분 차이
        m = resolve_birth_moment(date(1958, 3, 1), 13, 20)
        self.assertEqual(m.solar_clock.strftime("%H:%M"), "13:17")

    def test_1987_daylight_saving_is_removed(self):
        # 1987-07-01 서머타임(UTC+10) 시계 10:20 → 태양시 08:47 → 진시
        m = resolve_birth_moment(date(1987, 7, 1), 10, 20)
        self.assertEqual(m.solar_clock.strftime("%H:%M"), "08:47")
        self.assertEqual(natal(1987, 7, 1, 10, 20)[3][1], "辰")


class DayChangeTests(unittest.TestCase):
    def test_2300_clock_is_still_same_day_before_solar_2300(self):
        # 시계 23:20 → 태양시 22:47 → 해시, 당일 일주
        self.assertEqual(natal(1990, 5, 15, 23, 20)[2:], ("庚辰", "丁亥"))

    def test_2345_clock_changes_day(self):
        # 시계 23:45 → 태양시 23:12 → 다음 날 일주 자시
        self.assertEqual(natal(1990, 5, 15, 23, 45)[2], "辛巳")

    def test_main_reading_and_food_agree_on_day_pillar(self):
        from dalha_food.state import Birth, build_base

        core = calculate_myeongri_core(
            BirthInput(name="테스트", birth_date=date(1990, 5, 15), birth_time=time(23, 45), gender="female")
        )
        food_day = build_base(Birth(sex="female", year=1990, month=5, day=15, hour=23, minute=45))["pillars"]["day"]
        self.assertEqual(core.natal_facts.pillars["day"].stem + core.natal_facts.pillars["day"].branch,
                         food_day["stem"] + food_day["branch"])


if __name__ == "__main__":
    unittest.main()
