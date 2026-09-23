"""Coverage for every paid surface and free, non-destructive editorial upgrades."""
import re
from datetime import date, time
from concurrent.futures import ThreadPoolExecutor
from unittest import TestCase
from unittest.mock import patch
import main
import wallet_store
from . import test_annual_reader as annual_tests
from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services import (
    build_lifetime_overall_report, build_lifetime_wealth_report,
    build_lifetime_career_report, build_lifetime_love_report,
    build_lifetime_health_report, build_lifetime_study_report, build_compatibility_report,
)
from app.engine.services.annual import build_annual_overall_report
from app.engine.services.reading_editorial import VERSION


def plain(content):
    return re.sub(r'<[^>]*>', '', content)


class EditorialCoverageTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.core = calculate_myeongri_core(BirthInput(name='검증', gender='female',
            birth_date=date(1992,5,16), birth_time=time(8)), target_date=date(2026,9,23))
        cls.other = calculate_myeongri_core(BirthInput(name='상대', gender='male',
            birth_date=date(1986,2,3), time_unknown=True), target_date=date(2026,9,23))

    def test_all_products_have_expanded_versioned_copy(self):
        reports = [
            build_lifetime_overall_report(self.core, '검증'),
            build_lifetime_wealth_report(self.core, '검증'),
            build_lifetime_health_report(self.core, '검증'),
            build_lifetime_study_report(self.core, '검증'),
        ] + [build_lifetime_career_report(self.core,'검증',s) for s in ['직장인','취업/이직','사업가','창업']
        ] + [build_lifetime_love_report(self.core,'검증',s) for s in ['솔로','썸/짝사랑','연애중','기혼']]
        for report in reports:
            with self.subTest(title=report['title']):
                self.assertEqual(report['narrative_version'], VERSION)
                self.assertGreater(len(plain(report['content'])), 2000)
                self.assertEqual(report['content'].count('data-report-cycle='),9)
                self.assertIn('이 풀이의 근거', report['content'])
                self.assertNotIn('생활에 남겨보세요', report['content'])
        annual = build_annual_overall_report(self.core,'검증',2026)
        self.assertNotIn('기본 사주에서 중심이 되는 주제와', annual['content'])
        self.assertNotIn('지금 가장 신경 쓰이는 분야부터 읽어보세요', annual['content'])

    def test_compatibility_uses_selected_relation_not_romance_for_everyone(self):
        for relation in ['연인 / 결혼','친구 / 지인','동업 / 비즈니스']:
            report=build_compatibility_report(self.core,self.other,'<script>','상대',relation)
            self.assertGreater(len(plain(report['content'])),2000)
            self.assertNotIn('<script>',report['content'])
            self.assertEqual('결혼하면 어떤가' in report['content'],relation=='연인 / 결혼')
            self.assertEqual(report['narrative_version'],VERSION)

    def test_all_theme_names_are_escaped_and_personalized(self):
        for builder in [build_lifetime_overall_report, build_lifetime_wealth_report,
                        build_lifetime_health_report,build_lifetime_study_report]:
            report=builder(self.core,'<img src=x>')
            self.assertNotIn('<img',report['content'])
            self.assertIn('&lt;img',report['content'])
            self.assertNotEqual(report['content'],builder(self.other,'<img src=x>')['content'])


class ReadingRefreshTests(TestCase):
    setUp = annual_tests.AnnualRefreshTests.setUp

    def seed_theme(self, key='wealth'):
        self.original=dict(report_key=key,report_title='이전 풀이',report_content='<p>보존할 원문</p>',
                           created_at='2026.02.01')
        wallet_store.buy_report(self.owner,key,220,self.original)

    def update(self, key='wealth', **extra):
        return self.client.post('/api/reports/refresh',json=dict(user_id=self.owner,report_key=key,**extra))

    def test_refresh_is_free_versioned_idempotent_and_keeps_history(self):
        self.seed_theme()
        response=self.update()
        self.assertEqual(response.status_code,200,response.text)
        data=response.json(); report=data['unlocked_reports'][0]
        self.assertEqual(data['new_balance'],780)
        self.assertEqual(report['previous_versions'],[self.original])
        self.assertEqual(report['created_at'],'2026.02.01')
        self.assertEqual(report['narrative_version'],VERSION)
        with patch('main.generate_detailed_report',side_effect=AssertionError('already updated')):
            self.assertEqual(self.update().json(),data)

    def test_status_must_be_selected_not_guessed(self):
        self.seed_theme('business')
        self.assertEqual(self.update('business').status_code,422)
        self.assertEqual(self.update('business',sub_option='창업').status_code,200)
        report=wallet_store.load(self.owner)['reports'][0]
        self.assertEqual(report['reading_context']['sub_option'],'창업')
        self.assertIn('창업 준비에서의 활용',report['report_content'])

    def test_missing_partner_does_not_recalculate_or_charge(self):
        self.seed_theme('gunghap')
        before=wallet_store.load(self.owner)
        self.assertEqual(self.update('gunghap').status_code,422)
        self.assertEqual(wallet_store.load(self.owner),before)
        response=self.update('gunghap',partner_name='상대',partner_gender='male',
            partner_birth_year=1986,partner_birth_month=2,partner_birth_day=3,
            partner_calendar_type='solar',partner_sijin_index=-1,relation='친구 / 지인')
        self.assertEqual(response.status_code,200,response.text)
        self.assertEqual(response.json()['new_balance'],780)
        self.assertNotIn('partner_birth_year',str(wallet_store.load(self.owner)['reports'][0].keys()))

    def test_http_boundary_and_ownership_are_enforced(self):
        self.assertEqual(self.update().status_code,403)
        self.seed_theme()
        for headers in [{'X-Dalha-Request':''},{'Origin':'https://evil.example'}]:
            self.assertEqual(self.client.post('/api/reports/refresh',
                json=dict(user_id=self.owner,report_key='wealth'),headers=headers).status_code,403)
        self.assertEqual(self.client.post('/api/reports/refresh',
            json=dict(user_id='user_other',report_key='wealth')).status_code,403)
        self.client.cookies.clear()
        self.assertEqual(self.update().status_code,401)

    def test_failure_and_concurrency_never_lose_originals_or_balance(self):
        self.seed_theme(); before=wallet_store.load(self.owner)
        with patch('main.generate_detailed_report',side_effect=ValueError('invalid')):
            self.assertEqual(self.update().status_code,422)
        self.assertEqual(wallet_store.load(self.owner),before)
        replacement=dict(report_title='새 풀이',report_content='<p>새 원고</p>',narrative_version=VERSION)
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(lambda _:wallet_store.refresh_owned_report(
                self.owner,'wealth',self.original,replacement),range(8)))
        state=wallet_store.load(self.owner)
        self.assertEqual(state['balance'],780)
        self.assertEqual(state['reports'][0]['previous_versions'],[self.original])
