"""HTTP-boundary and database regression tests. No live Kakao or production DB."""
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
import main
import account_store
import session_store
import wallet_store
import tarot_store
import tarot_service


class AccountSecurityTests(TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        for context in [
            patch.dict(os.environ, {'DATABASE_URL':'','RENDER':'','RENDER_SERVICE_ID':'',
                'DALHA_WARDROBE_DB':self.tmp.name+'/secure.sqlite'}),
            patch.dict(main.users_db,{},clear=True), patch.dict(main.reports_db,{},clear=True),
            patch.object(main.gyeongju_weather_cache,'get',return_value=None),
            patch.object(main,'get_saju_pillars_and_analysis',return_value={'daily_fortune':{}}),
            patch.object(main,'generate_detailed_report',return_value={'title':'테스트 해석','content':'<p>가상 해석</p>'})
        ]:
            context.start();self.addCleanup(context.stop)
        self.client=self.new_client()

    def new_client(self):
        c=TestClient(main.app,base_url='https://dalha.test',raise_server_exceptions=False)
        c.headers['X-Dalha-Request']='1'
        self.addCleanup(c.close)
        return c

    def login(self, client=None, identity='qa-owner'):
        c=client or self.client
        response=MagicMock()
        response.__enter__.return_value.read.return_value=json.dumps({'id':identity,'kakao_account':{}}).encode()
        with patch('urllib.request.urlopen',return_value=response):
            r=c.post('/api/auth/kakao',json={'kakao_id':identity,'profile_source':'kakao','access_token':'fake-test-token'})
        self.assertEqual(r.status_code,200,r.text)
        return r

    def register(self, client=None, identity='qa-owner'):
        c=client or self.client
        p=dict(user_id='user_'+identity,name='가상사용자',gender='female',birth_year=1992,
               birth_month=9,birth_day=21,calendar_type='solar',sijin_index=-1)
        r=c.post('/api/user/register-saju',json=p)
        self.assertEqual(r.status_code,200,r.text)
        return p

    def test_no_id_only_login_or_private_access(self):
        self.login();profile=self.register()
        stranger=self.new_client()
        for body in [{'kakao_id':'qa-owner'}, {'kakao_id':'qa-owner','name':'가상사용자',
                     'gender':'female','birthyear':'1992','birthday':'0921','sijin_index':-1}]:
            self.assertEqual(stranger.post('/api/auth/kakao',json=body).status_code,401)
        for method,url,kwargs in [
            ('get','/api/auth/session',{}),('get','/api/wardrobe?user_id=user_qa-owner',{}),
            ('post','/api/user/register-saju',{'json':profile}),
            ('post','/api/reports/unlock',{'json':{'user_id':'user_qa-owner','report_key':'wealth','cost':0}}),
            ('post','/api/daily-tarot/draw',{'json':{'user_id':'user_qa-owner','slot':1,'request_id':'untrusted-request1'}}),
            ('get','/api/daily-tarot/state?user_id=user_qa-owner',{})]:
            self.assertEqual(getattr(stranger,method)(url,**kwargs).status_code,401,url)

    def test_cookie_flags_restart_resume_and_logout_revocation(self):
        r=self.login();self.register()
        header=r.headers['set-cookie'].lower()
        for flag in ['httponly','secure','samesite=lax','max-age=2592000']:
            self.assertIn(flag,header)
        token=self.client.cookies.get(session_store.COOKIE)
        main.users_db.clear();main.reports_db.clear()
        resumed=self.client.get('/api/auth/session')
        self.assertEqual(resumed.status_code,200,resumed.text)
        self.assertEqual(resumed.json()['profile']['name'],'가상사용자')
        self.assertEqual(resumed.headers['cache-control'],'no-store')
        self.assertEqual(self.client.post('/api/auth/logout').status_code,200)
        replay=self.new_client();replay.cookies.set(session_store.COOKIE,token)
        self.assertEqual(replay.get('/api/auth/session').status_code,401)

    def test_expiration_rotation_and_missing_or_forged_cookie(self):
        self.login();old=self.client.cookies.get(session_store.COOKIE)
        self.login();new=self.client.cookies.get(session_store.COOKIE)
        self.assertNotEqual(old,new);self.assertIsNone(session_store.resolve(old))
        with patch('session_store.time.time',return_value=time.time()+session_store.TTL+1):
            self.assertEqual(self.client.get('/api/auth/session').status_code,401)
        self.client.cookies.clear();self.client.cookies.set(session_store.COOKIE,'a'*43)
        self.assertEqual(self.client.get('/api/auth/session').status_code,401)

    def test_kakao_identity_mismatch_missing_token_and_cross_account(self):
        self.login();profile=self.register()
        other=self.new_client();self.login(other,'qa-other');self.register(other,'qa-other')
        self.assertEqual(other.post('/api/user/register-saju',json=profile).status_code,403)
        self.assertEqual(other.get('/api/wardrobe?user_id=user_qa-owner').status_code,403)
        self.assertEqual(other.post('/api/auth/kakao',json={'kakao_id':'qa-owner'}).status_code,403)
        response=MagicMock();response.__enter__.return_value.read.return_value=b'{"id":"not-owner","kakao_account":{}}'
        with patch('urllib.request.urlopen',return_value=response):
            r=other.post('/api/auth/kakao',json={'kakao_id':'qa-owner','profile_source':'kakao','access_token':'wrong'})
        self.assertEqual(r.status_code,401)
        self.assertEqual(other.post('/api/auth/kakao',json={'kakao_id':'qa-owner','profile_source':'kakao'}).status_code,401)

    def test_csrf_and_db_failure_fail_closed(self):
        self.login();p=self.register()
        self.assertEqual(self.client.post('/api/user/register-saju',json=p,headers={'Origin':'https://evil.example'}).status_code,403)
        self.assertEqual(self.client.post('/api/user/register-saju',json=p,headers={'X-Dalha-Request':''}).status_code,403)
        with patch('session_store.resolve',side_effect=account_store.StorageUnavailable):
            self.assertEqual(self.client.get('/api/auth/session').status_code,503)
        self.assertEqual(account_store.load('user_qa-owner')['profile']['name'],'가상사용자')

    def test_report_price_idempotency_and_restart(self):
        self.login();self.register()
        body={'user_id':'user_qa-owner','report_key':'daewoon','cost':-100000}
        for _ in range(2):
            r=self.client.post('/api/reports/unlock',json=body)
            self.assertEqual(r.status_code,200,r.text)
            self.assertEqual(r.json()['new_balance'],550)
            self.assertEqual(len(r.json()['unlocked_reports']),1)
        main.users_db.clear();main.reports_db.clear()
        self.login() # Verified login also must not re-grant the welcome balance.
        data=self.client.get('/api/auth/session').json()
        self.assertEqual(data['coin_balance'],550)
        self.assertEqual(len(data['unlocked_reports']),1)
        script="import json,wallet_store;print(json.dumps(wallet_store.load('user_qa-owner')))"
        restored=json.loads(subprocess.check_output([sys.executable,'-c',script],text=True))
        self.assertEqual(restored['balance'],550);self.assertEqual(len(restored['reports']),1)

    def test_unverified_charge_cannot_mint_coins(self):
        self.login()
        with patch.dict(os.environ, {'DALHA_TEST_USER_IDS':''}):
            r=self.client.post('/api/user/charge-coin',json={'user_id':'user_qa-owner','amount':1000})
        self.assertEqual(r.status_code,403)
        self.assertEqual(wallet_store.load('user_qa-owner')['balance'],1000)

    def test_tester_charge_is_persistent_and_validated(self):
        self.login()
        with patch.dict(os.environ, {'DALHA_TEST_USER_IDS':'user_qa-owner'}):
            for amount in [-1, 0, 100001, 1.5, True]:
                r=self.client.post('/api/user/charge-coin',json={'user_id':'user_qa-owner','amount':amount})
                self.assertEqual(r.status_code,422)
            r=self.client.post('/api/user/charge-coin',json={'user_id':'user_other','amount':1000})
            self.assertEqual(r.status_code,403)
            r=self.client.post('/api/user/charge-coin',json={'user_id':'user_qa-owner','amount':1000})
            self.assertEqual(r.status_code,200,r.text)
            self.assertTrue(r.json()['test_only'])
        main.users_db.clear()
        self.assertEqual(self.client.get('/api/auth/session').json()['coin_balance'],2000)

    def test_concurrent_report_spend_and_insufficient_funds(self):
        wallet_store.load('user_concurrent',initial_balance=450)
        report={'report_key':'daewoon','report_title':'테스트','report_content':'테스트'}
        with ThreadPoolExecutor(max_workers=6) as pool:
            results=list(pool.map(lambda _:wallet_store.buy_report('user_concurrent','daewoon',450,report),range(10)))
        self.assertTrue(all(r['balance']==0 and len(r['reports'])==1 for r in results))
        with self.assertRaises(ValueError):
            wallet_store.buy_report('user_concurrent','wealth',220,{'report_key':'wealth'})
        self.assertEqual(wallet_store.load('user_concurrent')['balance'],0)

    def test_tarot_receipt_and_debit_rollback_together(self):
        users={'user_tarot-qa':{'coin':30}}
        args=dict(user_id='user_tarot-qa',slot=1,request_id='free-request-qa1',is_paid=False,day='2026-09-22')
        tarot_service.draw(users,main.TAROT_DECK,lambda d:d[0],**args)
        execute=wallet_store._execute
        def fail_update(conn,pg,sql,params=()):
            if sql.startswith('UPDATE account_assets'):raise RuntimeError('simulated commit-path failure')
            return execute(conn,pg,sql,params)
        with patch('wallet_store._execute',side_effect=fail_update), self.assertRaises(wallet_store.StorageUnavailable):
            tarot_service.draw(users,main.TAROT_DECK,lambda d:d[0],**(args|dict(slot=2,request_id='paid-request-qa2',is_paid=True)))
        self.assertEqual(wallet_store.load('user_tarot-qa')['balance'],30)
        self.assertEqual(len(tarot_store.read('user_tarot-qa','2026-09-22')),1)
        users={'user_tarot-qa':{'coin':1000}} # Simulated stale process cache.
        result=tarot_service.draw(users,main.TAROT_DECK,lambda d:d[0],**(args|dict(slot=2,request_id='paid-request-qa2',is_paid=True)))
        self.assertEqual(result['new_balance'],20)
        self.assertEqual(wallet_store.load('user_tarot-qa')['balance'],20)

    def test_report_save_failure_never_debits(self):
        self.login();self.register()
        execute=wallet_store._execute
        def fail_saved_report(conn,pg,sql,params=()):
            if sql.startswith('UPDATE account_assets') and params[0]==780:
                raise RuntimeError('simulated write failure')
            return execute(conn,pg,sql,params)
        with patch('wallet_store._execute',side_effect=fail_saved_report):
            r=self.client.post('/api/reports/unlock',json={'user_id':'user_qa-owner','report_key':'wealth','cost':220})
        self.assertEqual(r.status_code,503)
        assets=wallet_store.load('user_qa-owner')
        self.assertEqual(assets['balance'],1000);self.assertEqual(assets['reports'],[])
