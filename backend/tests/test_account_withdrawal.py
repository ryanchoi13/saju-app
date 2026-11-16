"""회원 탈퇴: 신청·취소·7일 유예 후 삭제·재가입 시 환영 복채 차단. 실제 카카오·운영 DB 없음."""
import json
import os
import time
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import main
import account_store
import account_withdrawal
import session_store
import wallet_store
from app.engine.services import meal_history

DAY = 24 * 60 * 60


class WithdrawalTests(TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        for context in [
            patch.dict(os.environ, {'DATABASE_URL': '', 'RENDER': '', 'RENDER_SERVICE_ID': '',
                'DALHA_WARDROBE_DB': self.tmp.name + '/withdraw.sqlite',
                'DALHA_MENU_HISTORY_DB': self.tmp.name + '/menu-history.sqlite'}),
            patch.dict(main.users_db, {}, clear=True), patch.dict(main.reports_db, {}, clear=True),
            patch.object(main.gyeongju_weather_cache, 'get', return_value=None),
            patch.object(main, 'get_saju_pillars_and_analysis', return_value={'daily_fortune': {}}),
            patch.object(main, 'generate_detailed_report',
                         return_value={'title': '테스트 해석', 'content': '<p>가상 해석</p>'}),
        ]:
            context.start(); self.addCleanup(context.stop)
        # 식단 기록 DB 연결은 전역이라 임시 폴더를 가리킨 채 남지 않게 되돌린다.
        saved_db, meal_history._DB = meal_history._DB, None
        self.addCleanup(self._restore_meal_db, saved_db)
        self.client = self.new_client()

    @staticmethod
    def _restore_meal_db(saved):
        if meal_history._DB is not None:
            meal_history._DB.close()
        meal_history._DB = saved

    def new_client(self):
        c = TestClient(main.app, base_url='https://dalha.test', raise_server_exceptions=False)
        c.headers['X-Dalha-Request'] = '1'
        self.addCleanup(c.close)
        return c

    def login(self, client=None, identity='qa-leaver'):
        c = client or self.client
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(
            {'id': identity, 'kakao_account': {}}).encode()
        with patch('urllib.request.urlopen', return_value=response):
            r = c.post('/api/auth/kakao', json={'kakao_id': identity, 'profile_source': 'kakao',
                                                'access_token': 'fake-test-token'})
        self.assertEqual(r.status_code, 200, r.text)
        return r

    def register(self, client=None, identity='qa-leaver'):
        c = client or self.client
        r = c.post('/api/user/register-saju', json=dict(
            user_id='user_' + identity, name='가상사용자', gender='female', birth_year=1992,
            birth_month=9, birth_day=21, calendar_type='solar', sijin_index=-1))
        self.assertEqual(r.status_code, 200, r.text)

    def withdraw(self, client=None, identity='qa-leaver', confirm=True):
        return (client or self.client).post('/api/user/withdraw',
                                            json={'user_id': 'user_' + identity, 'confirm': confirm})

    def test_withdraw_needs_confirmation_login_and_matching_account(self):
        self.login(); self.register()
        self.assertEqual(self.withdraw(confirm=False).status_code, 422)
        stranger = self.new_client()
        self.assertEqual(self.withdraw(stranger).status_code, 401)
        other = self.new_client(); self.login(other, 'qa-other'); self.register(other, 'qa-other')
        self.assertEqual(self.withdraw(other).status_code, 403)  # 남의 계정 탈퇴 불가
        self.assertIsNone(account_withdrawal.pending('user_qa-leaver'))

    def test_request_logs_out_and_login_shows_pending_then_cancel(self):
        self.login(); self.register()
        token = self.client.cookies.get(session_store.COOKIE)
        r = self.withdraw()
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()['delete_at'] - r.json()['requested_at'], 7 * DAY)
        self.assertIsNone(session_store.resolve(token))  # 신청과 함께 이 기기 로그아웃
        again = self.login()
        self.assertEqual(again.json()['status'], 'existing_user')
        pending = again.json()['withdrawal_pending']
        self.assertEqual(pending['delete_at'], r.json()['delete_at'])
        self.assertEqual(self.withdraw().json()['requested_at'], r.json()['requested_at'])  # 첫 신청일 유지
        self.login()
        cancel = self.client.post('/api/user/withdraw/cancel',
                                  json={'user_id': 'user_qa-leaver', 'confirm': True})
        self.assertEqual(cancel.status_code, 200)
        self.assertTrue(cancel.json()['cancelled'])
        self.assertIsNone(self.login().json()['withdrawal_pending'])

    def test_nothing_is_deleted_during_the_grace_period(self):
        self.login(); self.register(); self.withdraw()
        soon = time.time() + 6 * DAY
        self.assertEqual(account_withdrawal.purge_due(now=soon), [])
        self.assertEqual(account_store.load('user_qa-leaver')['profile']['name'], '가상사용자')

    def test_purge_deletes_everything_after_seven_days(self):
        self.login(); self.register()
        body = {'user_id': 'user_qa-leaver', 'report_key': 'daewoon', 'cost': 0}
        self.assertEqual(self.client.post('/api/reports/unlock', json=body).status_code, 200)
        self.assertEqual(wallet_store.load('user_qa-leaver')['balance'], 550)
        self.withdraw()
        done = account_withdrawal.purge_due(now=time.time() + 8 * DAY)
        self.assertEqual(done, ['user_qa-leaver'])
        self.assertIsNone(account_store.load('user_qa-leaver'))
        self.assertEqual(self.new_client().get('/api/auth/session').status_code, 401)
        self.assertIsNone(account_withdrawal.pending('user_qa-leaver'))
        # 같은 시각에 두 번 돌려도 안전하다.
        self.assertEqual(account_withdrawal.purge_due(now=time.time() + 8 * DAY), [])

    def test_cancelled_request_is_not_purged(self):
        self.login(); self.register(); self.withdraw()
        self.login()  # 신청하면 로그아웃되므로 다시 로그인해야 취소할 수 있다
        self.assertEqual(self.client.post('/api/user/withdraw/cancel',
                         json={'user_id': 'user_qa-leaver', 'confirm': True}).status_code, 200)
        self.assertEqual(account_withdrawal.purge_due(now=time.time() + 9 * DAY), [])
        self.assertIsNotNone(account_store.load('user_qa-leaver'))

    def test_rejoin_after_deletion_gets_no_welcome_coins_for_thirty_days(self):
        self.login(); self.register(); self.withdraw()
        account_withdrawal.purge_due(now=time.time() + 8 * DAY)
        main.users_db.clear(); main.reports_db.clear()
        fresh = self.new_client()
        r = self.login(fresh)
        self.assertEqual(r.json()['status'], 'new_user')
        self.assertEqual(r.json()['coin_balance'], 0)
        self.assertEqual(wallet_store.load('user_qa-leaver')['reports'], [])

    def test_rejoin_after_limit_gets_welcome_coins_again(self):
        self.login(); self.register(); self.withdraw()
        base = time.time()
        account_withdrawal.purge_due(now=base + 8 * DAY)
        after = base + 8 * DAY + account_withdrawal.REJOIN_LIMIT_SECONDS + 10
        account_withdrawal.purge_due(now=after)  # 오래된 표시 정리
        main.users_db.clear(); main.reports_db.clear()
        self.assertEqual(self.login(self.new_client()).json()['coin_balance'], 1000)

    def test_other_accounts_are_untouched(self):
        self.login(); self.register()
        other = self.new_client(); self.login(other, 'qa-keeper'); self.register(other, 'qa-keeper')
        self.withdraw()
        account_withdrawal.purge_due(now=time.time() + 8 * DAY)
        self.assertEqual(account_store.load('user_qa-keeper')['profile']['name'], '가상사용자')
        self.assertEqual(wallet_store.load('user_qa-keeper')['balance'], 1000)
