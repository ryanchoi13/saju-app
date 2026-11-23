"""산 풀이는 지금 저장된 사주를 따라간다.

11/23 정오님 제보: 내 정보에서 이름·생년월일을 다른 사람으로 바꿨는데, 이미 산 직업운이
예전 이름과 예전 나이(48~57세 대운) 그대로 나왔다. 산 풀이가 구매 당시 본문으로 굳어 있었기 때문이다.
"""
import os
import re
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

import menu_store
from main import (
    KakaoAuthRequest,
    PreviewReportRequest,
    RegisterSajuRequest,
    UnlockReportRequest,
    auth_kakao,
    client_reports,
    preview_report,
    register_saju,
    reports_db,
    unlock_report,
    users_db,
)

USER = "user_test-follow"


def _text(html):
    return re.sub(r"<[^>]+>", " ", html)


class ReportFollowsProfileTests(TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        env = patch.dict(os.environ, {'DATABASE_URL': '', 'RENDER': '', 'RENDER_SERVICE_ID': '',
            'DALHA_WARDROBE_DB': self.tmp.name + '/profiles.sqlite',
            'DALHA_MENU_DB': self.tmp.name + '/menus.sqlite'})
        env.start(); self.addCleanup(env.stop)
        ready = patch.object(menu_store, '_READY', False); ready.start(); self.addCleanup(ready.stop)
        auth_kakao(KakaoAuthRequest(kakao_id="test-follow"))
        users_db[USER]['coin'] = 5000

    def tearDown(self):
        users_db.pop(USER, None)
        reports_db.pop(USER, None)

    def _me(self):
        return register_saju(RegisterSajuRequest(
            user_id=USER, name="가나다", gender="male", birth_year=1978, birth_month=3, birth_day=13,
            calendar_type="solar", birth_hour=10, birth_minute=30))

    def _other(self):
        return register_saju(RegisterSajuRequest(
            user_id=USER, name="라마바", gender="female", birth_year=2007, birth_month=5, birth_day=10,
            calendar_type="solar"))

    def _buy(self, key="business", cost=220):
        return unlock_report(UnlockReportRequest(user_id=USER, report_key=key, cost=cost, sub_option="기본"))

    def _owned(self, key="business"):
        return next(r for r in client_reports(USER) if r["report_key"] == key)

    def test_owned_reading_is_rewritten_when_profile_changes(self):
        self._me(); self._buy()
        self.assertIn("가나다", self._owned()["report_title"])
        self._other()
        owned = self._owned()
        self.assertIn("라마바", owned["report_title"])
        body = _text(owned["report_content"])
        self.assertNotIn("가나다", body)
        self.assertNotIn("48~57세", body)

    def test_preview_of_owned_reading_uses_current_profile(self):
        self._me(); self._buy()
        self._other()
        shown = preview_report(PreviewReportRequest(user_id=USER, report_key="business"))
        self.assertEqual(shown["status"], "owned")
        self.assertIn("라마바", shown["report"]["report_title"])

    def test_profile_save_returns_refreshed_readings(self):
        self._me(); self._buy()
        saved = self._other()
        titles = [r["report_title"] for r in saved["unlocked_reports"]]
        self.assertTrue(titles and all("라마바" in t for t in titles))

    def test_same_profile_is_not_rewritten_again(self):
        self._me(); self._buy()
        first = dict(self._owned())
        self._me()                      # 같은 내용으로 다시 저장
        self.assertEqual(self._owned(), first)
        self.assertFalse(reports_db[USER][0].get("previous_versions"))

    def test_basis_key_is_not_sent_to_the_screen(self):
        self._me(); self._buy()
        self.assertNotIn("profile_key", self._owned())
        self.assertNotIn("previous_versions", self._owned())

    def test_purchase_date_and_balance_survive_rewrite(self):
        self._me(); self._buy()
        bought, coin = self._owned()["created_at"], users_db[USER]["coin"]
        self._other()
        self.assertEqual(self._owned()["created_at"], bought)
        self.assertEqual(users_db[USER]["coin"], coin)

    def test_old_reading_without_basis_is_rewritten_once(self):
        # 이 수정 전에 산 풀이는 어느 사주로 쓰였는지 기록이 없다. 한 번만 지금 사주로 다시 쓴다.
        import wallet_store
        self._me(); self._buy()
        with wallet_store.locked(USER) as (_, _, state):
            state['reports'][0].pop('profile_key')
            state['reports'][0]['report_title'] = '옛 사람님 정통 명리 직업·사업운'
            reports_db[USER] = state['reports']
        self.assertIn("가나다", self._owned()["report_title"])
        again = self._owned()
        self.assertIn("가나다", again["report_title"])
        self.assertEqual(len(reports_db[USER][0]["previous_versions"]), 1)
