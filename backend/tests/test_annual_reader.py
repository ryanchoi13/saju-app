"""Paid annual reader: evidence, copy isolation, 12 months and safe upgrades."""
import json
import os
from copy import deepcopy
from datetime import date, time
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import MagicMock, patch
from concurrent.futures import ThreadPoolExecutor

import main
import wallet_store
from fastapi.testclient import TestClient
from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services.annual import build_annual_overall_report, _domain_readings
from app.engine.services.annual_editorial import NARRATIVE_VERSION, GROUPS, ROLES


class AnnualReaderTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.core = calculate_myeongri_core(BirthInput(name='가상검증', gender='female',
            birth_date=date(1992,5,16), birth_time=time(8)), target_date=date(2026,9,23))
        cls.report = build_annual_overall_report(cls.core, '가상검증', 2026)

    def test_approved_structure_twelve_months_and_reading_volume(self):
        r = self.report
        self.assertEqual(r['narrative_version'], NARRATIVE_VERSION)
        self.assertEqual(len(r['reading']['domains']), 6)
        months = r['evidence_summary']['months']
        self.assertEqual([m['month'] for m in months], list(range(1,13)))
        readings = [r['reading']] + [m['reading'] for m in months]
        count = sum(len(p) for reading in readings for p in reading['paragraphs'])
        count += sum(len(p) for reading in readings for d in reading['domains'] for p in d['paragraphs'])
        self.assertGreaterEqual(count, 8000)
        self.assertLess(count, 14000)
        for month in months:
            self.assertGreaterEqual(len(month['reading']['paragraphs']), 3)
            self.assertEqual(len(month['reading']['domains']), 6)
            self.assertEqual(month['representative_date'], f"2026-{month['month']:02}-15")
        for m in range(1,13):
            self.assertEqual(r['content'].count(f'data-report-month="{m}"'), 1)
        for domain, _ in GROUPS:
            self.assertEqual(r['content'].count(f'data-report-domain="{domain}"'), 1)
            self.assertEqual(r['content'].count(f'data-month-domain="{domain}"'), 12)

    def test_scoped_evidence_is_preserved_and_general_guidance_is_not_forecast(self):
        self.assertTrue(self.report['evidence_summary']['annual']['policy']['ranking_is_editorial'])
        for reading, selection in [(self.report['reading'], self.report['evidence_summary']['annual'])] + [
                (m['reading'], m['interpretation']) for m in self.report['evidence_summary']['months']]:
            sources = {s for c in selection['candidates'] for s in c['source_ids']}
            for domain in reading['domains']:
                self.assertTrue(set(domain['source_ids']) <= sources)
                self.assertEqual(bool(domain['source_ids']), domain['kind'] == 'scoped_interpretation')
                if domain['kind'] == 'general_guidance':
                    self.assertNotIn('무난', ' '.join(domain['paragraphs']))
        blank = dict(candidates=[], focal_god='peer')
        self.assertTrue(all(d['kind'] == 'general_guidance' for d in _domain_readings(blank)))

    def test_daily_layers_cannot_change_the_annual_report(self):
        copy = self.core.model_copy(deep=True)
        copy.timing.daily = {}; copy.timing.monthly = {}
        self.assertEqual(build_annual_overall_report(copy, '가상검증', 2026), self.report)

    def test_monthly_domain_mode_overrides_broad_role_family(self):
        selection=dict(focal_god='direct_wealth', candidates=[dict(domain='love', mode='change', source_ids=['test'])])
        row=next(r for r in _domain_readings(selection, monthly=True) if r['domain']=='love')
        self.assertIn('직접 물어보세요',row['paragraphs'][0])
        self.assertNotIn('비용',row['paragraphs'][0])

    def test_different_births_use_different_calculated_readings_not_fictional_samples(self):
        other = calculate_myeongri_core(BirthInput(name='가상검증', gender='female',
            birth_date=date(1985,11,2), birth_time=time(19)), target_date=date(2026,9,23))
        self.assertNotEqual(self.report['content'], build_annual_overall_report(other, '가상검증', 2026)['content'])
        for token in ('지우님', '하린님', '도윤님', '당신의 가장 큰 강점', '반드시 성공', '질병이 생깁니다'):
            self.assertNotIn(token, self.report['content'])
        self.assertEqual(len(ROLES), 10)

    def test_name_is_escaped_and_unknown_hour_never_invented(self):
        core = calculate_myeongri_core(BirthInput(name='검증', gender='male',
            birth_date=date(2000,7,4), time_unknown=True), target_date=date(2026,9,23))
        r = build_annual_overall_report(core, '<img src=x onerror=alert(1)>', 2026)
        self.assertNotIn('<img', r['content']); self.assertNotIn('<img', r['title'])
        self.assertIn('&lt;img', r['content'])
        self.assertIsNone(core.natal_facts.pillars.get('hour'))

    def test_birth_year_skips_prebirth_months_and_prebirth_year_rejected(self):
        core = calculate_myeongri_core(BirthInput(name='검증', gender='female',
            birth_date=date(2026,9,23), time_unknown=True), target_date=date(2026,9,23))
        report = build_annual_overall_report(core, '검증', 2026)
        self.assertEqual(report['content'].count('출생 전 기간'), 8)
        self.assertEqual(report['evidence_summary']['months'][0]['representative_date'], '2026-09-23')
        with self.assertRaises(ValueError): build_annual_overall_report(core, '검증', 2025)


class AnnualRefreshTests(TestCase):
    def setUp(self):
        tmp = TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        for context in [patch.dict(os.environ, {'DATABASE_URL':'','RENDER':'','RENDER_SERVICE_ID':'',
                           'DALHA_WARDROBE_DB':tmp.name+'/refresh.sqlite'}),
                        patch.dict(main.users_db,{},clear=True), patch.dict(main.reports_db,{},clear=True),
                        patch.object(main.gyeongju_weather_cache,'get',return_value=None),
                        patch.object(main,'get_saju_pillars_and_analysis',return_value={'daily_fortune':{}})]:
            context.start(); self.addCleanup(context.stop)
        self.client = TestClient(main.app, base_url='https://dalha.test', raise_server_exceptions=False)
        self.client.headers['X-Dalha-Request']='1'; self.addCleanup(self.client.close)
        response=MagicMock(); response.__enter__.return_value.read.return_value=b'{"id":"annual-owner","kakao_account":{}}'
        with patch('urllib.request.urlopen',return_value=response):
            self.assertEqual(self.client.post('/api/auth/kakao',json=dict(kakao_id='annual-owner',profile_source='kakao',access_token='test')).status_code,200)
        self.owner='user_annual-owner'
        self.client.post('/api/user/register-saju',json=dict(user_id=self.owner,name='검증',gender='female',
            birth_year=1992,birth_month=5,birth_day=16,calendar_type='solar',sijin_index=-1)).raise_for_status()
        self.original=dict(report_key='sinnian',report_title='2025 기존 운세',
            report_content='<div data-report-year="2025"><p>보존할 원문</p></div>',created_at='2025.02.01')
        self.body=dict(user_id=self.owner)

    def seed(self):
        wallet_store.buy_report(self.owner,'sinnian',300,self.original)
        wallet_store.buy_report(self.owner,'love',220,dict(report_key='love',report_content='별도 풀이'))

    def refresh(self, **kwargs):
        return self.client.post('/api/reports/refresh-annual',json=self.body,**kwargs)

    def test_owned_refresh_preserves_year_original_balance_and_other_reports(self):
        self.seed()
        response=self.refresh(); self.assertEqual(response.status_code,200,response.text)
        data=response.json(); self.assertEqual(data['new_balance'],480)
        annual=data['unlocked_reports'][0]
        self.assertEqual(annual['report_year'],2025)
        self.assertEqual(annual['created_at'],'2025.02.01')
        self.assertEqual(annual['previous_versions'],[self.original])
        self.assertEqual(annual['narrative_version'],NARRATIVE_VERSION)
        self.assertIn('data-report-year="2025"',annual['report_content'])
        self.assertEqual(data['unlocked_reports'][1]['report_content'],'별도 풀이')
        with patch('main.generate_detailed_report',side_effect=AssertionError('must not regenerate')):
            self.assertEqual(self.refresh().json(),data)
        main.users_db.clear();main.reports_db.clear()
        self.assertEqual(self.client.get('/api/auth/session').json()['unlocked_reports'],data['unlocked_reports'])

    def test_no_unowned_cross_account_or_csrf_upgrade(self):
        self.assertEqual(self.refresh().status_code,403)
        self.seed()
        self.assertEqual(self.refresh(headers={'X-Dalha-Request':''}).status_code,403)
        self.assertEqual(self.refresh(headers={'Origin':'https://evil.example'}).status_code,403)
        self.body['user_id']='user_someone-else'
        self.assertEqual(self.refresh().status_code,403)
        self.client.cookies.clear()
        self.assertEqual(self.refresh().status_code,401)

    def test_unknown_year_never_guesses_or_changes_archive(self):
        self.original.update(report_content='<p>연도 없음</p>',report_title='이전 풀이')
        self.seed()
        self.assertEqual(self.refresh().status_code,422)
        self.assertEqual(wallet_store.load(self.owner)['reports'][0],self.original)

    def test_generation_failure_preserves_everything(self):
        self.seed(); before=wallet_store.load(self.owner)
        with patch('main.generate_detailed_report',side_effect=ValueError('bad profile')):
            self.assertEqual(self.refresh().status_code,422)
        self.assertEqual(wallet_store.load(self.owner),before)

    def test_storage_failure_rolls_back_archive_and_balance(self):
        self.seed(); before=wallet_store.load(self.owner)
        execute=wallet_store._execute
        def fail(conn,pg,sql,params=()):
            if sql.startswith('UPDATE account_assets') and NARRATIVE_VERSION in str(params):
                raise RuntimeError('simulated storage failure')
            return execute(conn,pg,sql,params)
        with patch('wallet_store._execute',side_effect=fail):
            self.assertEqual(self.refresh().status_code,503)
        self.assertEqual(wallet_store.load(self.owner),before)

    def test_concurrent_upgrades_append_history_once_and_do_not_debit(self):
        self.seed()
        replacement=dict(report_title='2025 새 풀이',report_content='<p>새 원고</p>',
            narrative_version=NARRATIVE_VERSION,report_year=2025,refreshed_at='2026-09-23',profile_basis='current_saved_profile')
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(lambda _:wallet_store.refresh_owned_annual(self.owner,self.original,replacement),range(8)))
        state=wallet_store.load(self.owner)
        self.assertEqual(state['balance'],480)
        self.assertEqual(state['reports'][0]['previous_versions'],[self.original])
        with self.assertRaises(ValueError):
            wallet_store.refresh_owned_annual(self.owner,dict(self.original,report_content='stale'),
                dict(replacement,narrative_version='future-version'))
