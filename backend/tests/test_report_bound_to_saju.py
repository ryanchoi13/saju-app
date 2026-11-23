"""산 풀이는 '산 사주'에 묶인다 (11/23 정오님 결정).

- 내 정보를 다른 사람으로 바꿔도 이미 산 풀이는 원래 사주 그대로 남고, 누구 풀이인지 표시한다.
- 바뀐 사주로 보려면 새로 사야 한다. 태어난 시간만 고쳐도 같다(예외 없음).
- 문구 버전이 올라 다시 쓸 때도 지금 프로필이 아니라 산 사주로 쓴다.
"""
import os
import re
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

import menu_store
import wallet_store
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

USER = "user_test-bound"
ME = dict(name="가나다", gender="male", birth_year=1978, birth_month=3, birth_day=13,
          calendar_type="solar", birth_hour=10, birth_minute=30)
OTHER = dict(name="라마바", gender="female", birth_year=2007, birth_month=5, birth_day=10, calendar_type="solar")


def _text(html):
    return re.sub(r"<[^>]+>", " ", html)


class ReportBoundToSajuTests(TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        env = patch.dict(os.environ, {'DATABASE_URL': '', 'RENDER': '', 'RENDER_SERVICE_ID': '',
            'DALHA_WARDROBE_DB': self.tmp.name + '/profiles.sqlite',
            'DALHA_MENU_DB': self.tmp.name + '/menus.sqlite'})
        env.start(); self.addCleanup(env.stop)
        ready = patch.object(menu_store, '_READY', False); ready.start(); self.addCleanup(ready.stop)
        auth_kakao(KakaoAuthRequest(kakao_id="test-bound"))
        self._coins(5000)

    def tearDown(self):
        users_db.pop(USER, None)
        reports_db.pop(USER, None)

    def _coins(self, amount):
        with wallet_store.locked(USER) as (_, _, state):
            state['balance'] = amount
        users_db[USER]['coin'] = amount

    def _save(self, profile, **change):
        return register_saju(RegisterSajuRequest(user_id=USER, **dict(profile, **change)))

    def _buy(self, key="business", cost=220):
        return unlock_report(UnlockReportRequest(user_id=USER, report_key=key, cost=cost, sub_option="기본"))

    def _owned(self, key="business"):
        return [r for r in client_reports(USER) if r["report_key"] == key]

    def _preview(self, key="business"):
        return preview_report(PreviewReportRequest(user_id=USER, report_key=key))

    def test_reading_stays_with_the_saju_it_was_bought_for(self):
        self._save(ME); self._buy()
        saved = self._save(OTHER)
        (mine,) = self._owned()
        self.assertIn("가나다", mine["report_title"])
        self.assertIn("48~57세", _text(mine["report_content"]))
        self.assertIs(mine["for_current_saju"], False)
        self.assertEqual(mine["basis_label"], "가나다 · 1978.3.13")
        self.assertEqual(saved["unlocked_reports"], [mine])

    def test_changed_saju_sees_a_preview_and_must_buy_again(self):
        self._save(ME); self._buy()
        self._save(OTHER)
        shown = self._preview()
        self.assertEqual(shown["status"], "preview")
        self.assertEqual(shown["price_coins"], 220)
        self.assertIn("라마바", shown["title"])
        before = users_db[USER]["coin"]
        self._buy()
        self.assertEqual(users_db[USER]["coin"], before - 220)
        flags = {r["basis_label"]: r["for_current_saju"] for r in self._owned()}
        self.assertEqual(flags, {"가나다 · 1978.3.13": False, "라마바 · 2007.5.10": True})
        owned = self._preview()
        self.assertEqual(owned["status"], "owned")
        self.assertIn("라마바", owned["report"]["report_title"])

    def test_coming_back_to_the_bought_saju_costs_nothing(self):
        self._save(ME); self._buy()
        self._save(OTHER); self._save(ME)
        (mine,) = self._owned()
        self.assertIs(mine["for_current_saju"], True)
        before = users_db[USER]["coin"]
        self._buy()
        self.assertEqual(users_db[USER]["coin"], before)
        self.assertEqual(len(self._owned()), 1)
        self.assertEqual(self._preview()["status"], "owned")

    def test_birth_time_change_is_a_different_saju(self):
        self._save(ME); self._buy()
        self._save(ME, birth_hour=14)
        (mine,) = self._owned()
        self.assertIs(mine["for_current_saju"], False)
        self.assertEqual(self._preview()["status"], "preview")

    def test_name_change_alone_keeps_the_reading(self):
        self._save(ME); self._buy()
        before = dict(self._owned()[0])
        self._save(ME, name="가나다라")
        self.assertEqual(self._owned(), [before])
        self.assertIs(before["for_current_saju"], True)

    def test_version_refresh_uses_the_bought_saju_not_the_current_profile(self):
        self._save(ME); self._buy()
        self._save(OTHER)
        with wallet_store.locked(USER) as (_, _, state):
            state['reports'][0]['narrative_version'] = 'old'
            state['reports'][0]['report_content'] = '<p>옛 본문</p>'
            reports_db[USER] = state['reports']
        (mine,) = self._owned()
        body = _text(mine["report_content"])
        self.assertNotIn("옛 본문", body)
        self.assertIn("48~57세", body)
        self.assertIn("가나다", mine["report_title"])
        self.assertNotIn("라마바", body)

    def test_server_only_fields_are_not_sent_to_the_screen(self):
        self._save(ME); self._buy()
        for hidden in ("basis", "saju_key", "previous_versions", "partner_key"):
            self.assertNotIn(hidden, self._owned()[0])

    def _make_legacy(self, title=None):
        with wallet_store.locked(USER) as (_, _, state):
            for field in ("basis", "saju_key"):
                state['reports'][0].pop(field)
            if title:
                state['reports'][0]['report_title'] = title
            reports_db[USER] = state['reports']

    def test_reading_bought_before_this_rule_is_bound_to_the_profile_saved_now(self):
        self._save(ME); self._buy(); self._make_legacy()
        (mine,) = self._owned()
        self.assertIs(mine["for_current_saju"], True)
        self._save(OTHER)
        (mine,) = self._owned()
        self.assertIs(mine["for_current_saju"], False)
        self.assertEqual(mine["basis_label"], "가나다 · 1978.3.13")

    def test_old_reading_titled_for_someone_else_is_left_alone(self):
        # 이 규칙 전에 이미 프로필을 바꿔 둔 계정: 제목의 이름이 지금 이름과 다르면 누구 사주인지 알 수 없다.
        self._save(ME); self._buy(); self._make_legacy()
        with wallet_store.locked(USER) as (_, _, state):
            state['reports'][0]['narrative_version'] = 'old'
            reports_db[USER] = state['reports']
        self._save(OTHER)
        (mine,) = self._owned()
        self.assertIs(mine["for_current_saju"], False)
        self.assertNotIn("basis_label", mine)
        self.assertIn("가나다", mine["report_title"])        # 다시 쓰지 않는다
        self.assertEqual(mine["narrative_version"], "old")
        self.assertEqual(self._preview()["status"], "preview")

    def test_compatibility_reading_is_not_bound_to_the_saju(self):
        self._save(ME)
        wallet_store.buy_report(USER, 'gunghap', 0, dict(report_key='gunghap', report_title='궁합',
                                                         report_content='<p>궁합</p>', partner_key='p1'))
        reports_db[USER] = wallet_store.load(USER)['reports']
        self._save(OTHER)
        (pair,) = self._owned('gunghap')
        self.assertIs(pair["for_current_saju"], True)
        self.assertNotIn("basis_label", pair)
