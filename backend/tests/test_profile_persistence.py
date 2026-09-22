from pathlib import Path
from unittest import TestCase
from unittest.mock import patch
from tempfile import TemporaryDirectory
import os
import account_store
import menu_store

from main import (
    KakaoAuthRequest,
    RegisterSajuRequest,
    auth_kakao,
    register_saju,
    reports_db,
    users_db,
)


class ProfilePersistenceTests(TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        env = patch.dict(os.environ, {'DATABASE_URL':'','RENDER':'','RENDER_SERVICE_ID':'',
            'DALHA_WARDROBE_DB':self.tmp.name+'/profiles.sqlite','DALHA_MENU_DB':self.tmp.name+'/menus.sqlite'})
        env.start(); self.addCleanup(env.stop)
        ready=patch.object(menu_store,'_READY',False);ready.start();self.addCleanup(ready.stop)

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

    def test_durable_profile_wins_stale_browser_after_restart(self):
        self.test_registration_returns_profile_for_form_prefill()
        users_db.pop('user_test-register')
        restored=auth_kakao(KakaoAuthRequest(kakao_id='test-register',name='stale',gender='male',
            birthyear='1978',birthday='0813',sijin_index=5))
        self.assertEqual(restored['profile']['birth_month'],3)
        self.assertEqual(restored['profile']['name'],'최정오')

    def test_partial_provider_fields_require_user_confirmation(self):
        from main import _profile_from_kakao_request
        profile=_profile_from_kakao_request(KakaoAuthRequest(kakao_id='partial',name='실명',
            profile_source='kakao',birthday='0313'))
        self.assertIsNone(profile['birth_year'])
        self.assertEqual(profile['birth_month'],3)
        self.assertFalse(profile['profile_complete'])

    def test_kakao_server_uses_verified_consent_not_client_fields(self):
        from main import _verified_kakao_request
        from unittest.mock import MagicMock
        import json
        response=MagicMock()
        response.__enter__.return_value.read.return_value=json.dumps({'id':321,'kakao_account':{
            'name':'실명','profile':{'nickname':'별명'},'birthyear':'1992','birthday':'0921',
            'gender':'female','birthday_needs_agreement':True}}).encode()
        with patch('urllib.request.urlopen',return_value=response):
            verified=_verified_kakao_request(KakaoAuthRequest(kakao_id='321',profile_source='kakao',
                access_token='test-token',name='가짜',birthyear='1978',birthday='0813',sijin_index=5))
        self.assertEqual(verified.name,'실명')
        self.assertEqual(verified.birthyear,'1992')
        self.assertIsNone(verified.birthday)
        self.assertIsNone(verified.sijin_index)

    def test_registration_returns_profile_for_form_prefill(self):
        auth_kakao(KakaoAuthRequest(kakao_id="test-register"))
        result = register_saju(RegisterSajuRequest(
            user_id="user_test-register", name="최정오", gender="male",
            birth_year=1978, birth_month=3, birth_day=13,
            calendar_type="solar", sijin_index=5,
        ))
        self.assertEqual(result["profile"]["name"], "최정오")
        self.assertEqual(result["profile"]["birth_month"], 3)

    def test_new_kakao_login_prefills_after_additional_consent(self):
        from unittest.mock import MagicMock
        import json
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({
            'id': 'test-empty', 'kakao_account': {
                'name': '테스트', 'gender': 'female', 'birthyear': '1992',
                'birthday': '0921', 'birthday_type': 'SOLAR',
                'name_needs_agreement': False, 'birthday_needs_agreement': False,
            },
        }).encode()
        auth_kakao(KakaoAuthRequest(kakao_id='test-empty'))
        with patch('urllib.request.urlopen', return_value=response):
            result = auth_kakao(KakaoAuthRequest(kakao_id='test-empty',
                profile_source='kakao', access_token='test-token'))
        self.assertEqual(result['status'], 'new_user')
        self.assertEqual(result['kakao_prefill']['name'], '테스트')
        self.assertEqual(result['kakao_prefill']['birth_year'], 1992)
        self.assertEqual(result['kakao_prefill']['birth_month'], 9)
        self.assertEqual(result['kakao_prefill']['birth_day'], 21)
        self.assertFalse(result['kakao_prefill']['profile_complete'])
        users_db.pop('user_test-empty')
        restored = auth_kakao(KakaoAuthRequest(kakao_id='test-empty'))
        self.assertEqual(restored['kakao_prefill']['birth_year'], 1992)

    def test_edit_form_prefills_saved_values_and_timeline_uses_new_ranges(self):
        html = (Path(__file__).parents[2] / "index.html").read_text(encoding="utf-8")
        self.assertIn("populateSajuForm(currentSajuProfile || getSavedUserSaju());", html)
        self.assertIn("fetch('/api/auth/session'", html)
        self.assertNotIn("buildKakaoAuthPayload(savedKakaoId)", html)
        self.assertIn("대운 5~6", html)
        self.assertIn("대운 7~9", html)
        self.assertNotIn("대운 8 이후", html)

    def test_simple_menu_hides_paused_controls(self):
        html = (Path(__file__).parents[2] / "index.html").read_text(encoding="utf-8")
        self.assertIn("fortune.recommended_menus", html)
        self.assertIn("document.getElementById('menuModeToggle').hidden = true", html)
        self.assertIn("document.getElementById('menuPlanLike').hidden = true", html)
