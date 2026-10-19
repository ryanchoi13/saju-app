"""정확한 출생 시각(시·분) 입력 저장·계산 테스트.

- 시·분이 있으면 시진 범위 대신 그 시각으로 계산한다.
- 시진 번호는 옛 표시·users 표 호환을 위해 함께 저장한다.
- 예전 시진만 저장된 사용자는 기존처럼 시진 가운데 시각으로 계산한다.
"""
import os
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from fastapi import HTTPException

import menu_store
from main import (
    KakaoAuthRequest,
    RegisterSajuRequest,
    _birth_clock,
    _sijin_from_clock,
    auth_kakao,
    register_saju,
    reports_db,
    users_db,
)

USER = "user_test-clock"


class BirthClockProfileTests(TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        env = patch.dict(os.environ, {'DATABASE_URL': '', 'RENDER': '', 'RENDER_SERVICE_ID': '',
            'DALHA_WARDROBE_DB': self.tmp.name + '/profiles.sqlite',
            'DALHA_MENU_DB': self.tmp.name + '/menus.sqlite'})
        env.start(); self.addCleanup(env.stop)
        ready = patch.object(menu_store, '_READY', False); ready.start(); self.addCleanup(ready.stop)
        auth_kakao(KakaoAuthRequest(kakao_id="test-clock"))

    def tearDown(self):
        users_db.pop(USER, None)
        reports_db.pop(USER, None)

    def _register(self, **clock):
        return register_saju(RegisterSajuRequest(
            user_id=USER, name="테스트", gender="male",
            birth_year=1990, birth_month=5, birth_day=15, calendar_type="solar", **clock))

    def test_late_evening_birth_uses_next_day_pillar(self):
        # 15일 23:45 → 태양시 23:12 → 23시 일 변경 → 신사일 무자시
        result = self._register(birth_hour=23, birth_minute=45)
        detail = result["saju_analysis"]["saju_data"]["pillars_detail"]
        self.assertEqual(detail["day"]["cg"] + detail["day"]["jj"], "신사")
        self.assertEqual(detail["hour"]["cg"] + detail["hour"]["jj"], "무자")
        self.assertIn("23시 45분생", result["saju_analysis"]["birth_summary"])

    def test_profile_keeps_clock_and_derived_sijin(self):
        result = self._register(birth_hour=23, birth_minute=45)
        profile = result["profile"]
        self.assertEqual((profile["birth_hour"], profile["birth_minute"]), (23, 45))
        self.assertEqual(profile["sijin_index"], 0)  # 자시 (23:30~01:29)

    def test_relogin_restores_exact_clock(self):
        self._register(birth_hour=7, birth_minute=5)
        users_db.pop(USER, None)  # 서버 재시작 흉내
        result = auth_kakao(KakaoAuthRequest(kakao_id="test-clock"))
        self.assertEqual(result["status"], "existing_user")
        self.assertEqual((result["profile"]["birth_hour"], result["profile"]["birth_minute"]), (7, 5))
        self.assertIn("7시 05분생", result["saju_analysis"]["birth_summary"])

    def test_unknown_time_still_works(self):
        result = self._register(sijin_index=-1)
        self.assertIn("생시 미상", result["saju_analysis"]["birth_summary"])
        self.assertIsNone(result["profile"]["birth_hour"])

    def test_invalid_clock_is_rejected(self):
        with self.assertRaises(HTTPException):
            self._register(birth_hour=24, birth_minute=0)
        with self.assertRaises(HTTPException):
            self._register(birth_hour=10, birth_minute=None)

    def test_legacy_sijin_profile_still_uses_midpoint(self):
        result = self._register(sijin_index=5)
        self.assertIn("사(巳)시생", result["saju_analysis"]["birth_summary"])
        self.assertIsNone(result["profile"]["birth_hour"])


class ClockHelpersTests(TestCase):
    def test_sijin_ranges_match_old_labels(self):
        self.assertEqual(_sijin_from_clock(23, 30), 0)
        self.assertEqual(_sijin_from_clock(1, 29), 0)
        self.assertEqual(_sijin_from_clock(1, 30), 1)
        self.assertEqual(_sijin_from_clock(11, 29), 5)
        self.assertEqual(_sijin_from_clock(23, 29), 11)

    def test_exact_clock_wins_over_sijin(self):
        self.assertEqual(str(_birth_clock(5, 23, 45)), "23:45:00")
        self.assertEqual(str(_birth_clock(5)), "10:30:00")
        self.assertIsNone(_birth_clock(-1))
