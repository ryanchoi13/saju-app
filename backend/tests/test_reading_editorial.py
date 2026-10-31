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
from app.engine.services.reading_editorial import VERSION, THEME_VERSION
from app.engine.services.lifetime import LIFETIME_NARRATIVE_VERSION


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
                self.assertEqual(report['narrative_version'], LIFETIME_NARRATIVE_VERSION if report is reports[0] else THEME_VERSION)
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
            self.assertEqual(report['narrative_version'],THEME_VERSION)

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
                           created_at='2026.02.01',narrative_version=VERSION)
        wallet_store.buy_report(self.owner,key,220,self.original)

    def session_reports(self):
        main.users_db.clear(); main.reports_db.clear()
        response = self.client.get('/api/auth/session')
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()['unlocked_reports']

    def test_theme_reading_is_updated_for_free_and_only_once(self):
        self.seed_theme()
        report = self.session_reports()[0]
        self.assertEqual(report['narrative_version'], THEME_VERSION)
        self.assertEqual(report['created_at'], '2026.02.01')
        self.assertNotIn('previous_versions', report)
        state = wallet_store.load(self.owner)
        self.assertEqual(state['balance'], 780)
        self.assertEqual(state['reports'][0]['previous_versions'], [self.original])
        with patch('main.generate_detailed_report', side_effect=AssertionError('already updated')):
            self.assertEqual(self.session_reports()[0], report)

    def test_lifetime_reading_is_updated(self):
        original = dict(report_key='daewoon', report_title='기존 평생운세', report_content='<p>구매한 당시의 풀이</p>',
                        narrative_version=VERSION, created_at='2026.02.01')
        wallet_store.buy_report(self.owner, 'daewoon', 450, original)
        report = self.session_reports()[0]
        self.assertEqual(report['narrative_version'], LIFETIME_NARRATIVE_VERSION)
        self.assertIn('data-lifetime-v3="1"', report['report_content'])
        self.assertEqual(wallet_store.load(self.owner)['balance'], 550)

    def test_saved_situation_is_reused_and_never_guessed(self):
        self.seed_theme('business')                       # 상황 선택값이 없는 옛 풀이
        self.assertEqual(self.session_reports()[0]['report_content'], '<p>보존할 원문</p>')
        wallet_store.refresh_owned_report(self.owner, 'business', wallet_store.load(self.owner)['reports'][0],
                                          dict(narrative_version='older', reading_context=dict(sub_option='창업')))
        report = self.session_reports()[0]
        self.assertIn('창업 기준', report['report_content'])
        self.assertEqual(report['reading_context']['sub_option'], '창업')

    def test_compatibility_is_left_alone_without_partner_data(self):
        self.seed_theme('gunghap')
        before = wallet_store.load(self.owner)
        self.assertEqual(self.session_reports()[0]['report_content'], '<p>보존할 원문</p>')
        self.assertEqual(wallet_store.load(self.owner), before)

    def test_failure_and_concurrency_never_lose_originals_or_balance(self):
        self.seed_theme(); before=wallet_store.load(self.owner)
        with patch('main.generate_detailed_report',side_effect=ValueError('invalid')):
            self.session_reports()
        self.assertEqual(wallet_store.load(self.owner),before)
        replacement=dict(report_title='새 풀이',report_content='<p>새 원고</p>',narrative_version=THEME_VERSION)
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(lambda _:wallet_store.refresh_owned_report(
                self.owner,'wealth',self.original,replacement),range(8)))
        state=wallet_store.load(self.owner)
        self.assertEqual(state['balance'],780)
        self.assertEqual(state['reports'][0]['previous_versions'],[self.original])
