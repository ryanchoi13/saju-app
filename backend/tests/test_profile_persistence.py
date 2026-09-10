from pathlib import Path
from unittest import TestCase

from main import (
    KakaoAuthRequest,
    RegisterSajuRequest,
    auth_kakao,
    register_saju,
    reports_db,
    users_db,
)


class ProfilePersistenceTests(TestCase):
    def tearDown(self):
        for suffix in ("restore", "correct", "empty", "register"):
            user_id = f"user_test-{suffix}"
            users_db.pop(user_id, None)
            reports_db.pop(user_id, None)

    def test_complete_browser_profile_restores_after_server_restart(self):
        result = auth_kakao(KakaoAuthRequest(
            kakao_id="test-restore", name="최정오", gender="male",
            birthyear="1978", birthday="0313", birthday_type="SOLAR", sijin_index=5,
        ))
        self.assertEqual(result["status"], "existing_user")
        self.assertEqual(result["profile"]["birth_month"], 3)
        self.assertEqual(result["profile"]["birth_day"], 13)
        self.assertEqual(result["profile"]["name"], "최정오")
        self.assertEqual(result["profile"]["sijin_index"], 5)

    def test_incoming_saved_profile_corrects_old_default_birthday(self):
        user_id = "user_test-correct"
        users_db[user_id] = {
            "user_id": user_id, "kakao_id": "test-correct", "name": "최정오",
            "gender": "male", "birth_year": 1978, "birth_month": 8,
            "birth_day": 13, "calendar_type": "solar", "sijin_index": 5, "coin": 1000,
        }
        reports_db[user_id] = []
        result = auth_kakao(KakaoAuthRequest(
            kakao_id="test-correct", name="최정오", gender="male",
            birthyear="1978", birthday="0313", birthday_type="SOLAR", sijin_index=5,
        ))
        self.assertEqual(result["profile"]["birth_month"], 3)
        self.assertEqual(users_db[user_id]["birth_month"], 3)

    def test_missing_profile_does_not_fabricate_august_birthday(self):
        result = auth_kakao(KakaoAuthRequest(kakao_id="test-empty"))
        self.assertEqual(result["status"], "new_user")
        self.assertIsNone(result["kakao_prefill"]["birth_year"])
        self.assertIsNone(result["kakao_prefill"]["birth_month"])
        self.assertIsNone(result["kakao_prefill"]["birth_day"])
        self.assertEqual(result["kakao_prefill"]["sijin_index"], -1)

    def test_registration_returns_profile_for_form_prefill(self):
        auth_kakao(KakaoAuthRequest(kakao_id="test-register"))
        result = register_saju(RegisterSajuRequest(
            user_id="user_test-register", name="최정오", gender="male",
            birth_year=1978, birth_month=3, birth_day=13,
            calendar_type="solar", sijin_index=5,
        ))
        self.assertEqual(result["profile"]["name"], "최정오")
        self.assertEqual(result["profile"]["birth_month"], 3)

    def test_edit_form_prefills_saved_values_and_timeline_uses_new_ranges(self):
        html = (Path(__file__).parents[2] / "index.html").read_text(encoding="utf-8")
        self.assertIn("populateSajuForm(currentSajuProfile || getSavedUserSaju());", html)
        self.assertIn("buildKakaoAuthPayload(savedKakaoId)", html)
        self.assertIn("대운 5~6", html)
        self.assertIn("대운 7~9", html)
        self.assertNotIn("대운 8 이후", html)

    def test_simple_menu_hides_paused_controls(self):
        html = (Path(__file__).parents[2] / "index.html").read_text(encoding="utf-8")
        self.assertIn("fortune.recommended_menus", html)
        self.assertIn("document.getElementById('menuModeToggle').hidden = true", html)
        self.assertIn("document.getElementById('menuPlanLike').hidden = true", html)
