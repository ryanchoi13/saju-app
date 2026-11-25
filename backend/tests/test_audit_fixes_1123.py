"""11/23 자체 점검에서 나온 문제의 회귀 테스트."""
import os
import re
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from fastapi import HTTPException

import menu_store
import main
from main import (KakaoAuthRequest, RegisterSajuRequest, UnlockReportRequest, auth_kakao,
                  generate_detailed_report, register_saju, reports_db, users_db)

USER = "user_test-audit"
ME = dict(name="가나다", gender="male", birth_year=1978, birth_month=3, birth_day=13,
          calendar_type="solar", sijin_index=5, birth_hour=None, birth_minute=None)


def text_of(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))


class AccountCase(TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        env = patch.dict(os.environ, {'DATABASE_URL': '', 'RENDER': '', 'RENDER_SERVICE_ID': '',
            'DALHA_WARDROBE_DB': self.tmp.name + '/profiles.sqlite',
            'DALHA_MENU_DB': self.tmp.name + '/menus.sqlite'})
        env.start(); self.addCleanup(env.stop)
        ready = patch.object(menu_store, '_READY', False); ready.start(); self.addCleanup(ready.stop)
        auth_kakao(KakaoAuthRequest(kakao_id="test-audit"))

    def tearDown(self):
        users_db.pop(USER, None)
        reports_db.pop(USER, None)

    def save(self, **change):
        profile = {k: v for k, v in dict(ME, **change).items() if v is not None}
        return register_saju(RegisterSajuRequest(user_id=USER, **profile))


class LongNameTests(AccountCase):
    def test_long_name_still_gets_the_current_lifetime_reading(self):
        # 이름이 문장 길이 검사에 걸려 풀이 전체가 옛 버전으로 떨어지던 문제.
        for birth in ((1970, 1, 1), (1988, 6, 15), (1995, 11, 3), (2001, 4, 22)):
            for name in ("가나다라마바사아자차카타", "Christopher Alexander"):
                with self.subTest(birth=birth, name=name):
                    user = dict(ME, name=name, birth_year=birth[0], birth_month=birth[1], birth_day=birth[2])
                    report = generate_detailed_report('daewoon', '기본', '', '', name, user=user, is_unlocked=True)
                    self.assertIn('data-lifetime-v3="1"', report['content'])

    def test_name_longer_than_the_limit_is_refused(self):
        with self.assertRaises(HTTPException) as caught:
            self.save(name="가" * 21)
        self.assertEqual(caught.exception.status_code, 422)
        self.save(name="가" * 20)

    def test_name_input_limit_matches_the_server(self):
        html = open(os.path.join(os.path.dirname(main.__file__), 'index.html'), encoding='utf-8').read()
        for field in ('inputName', 'partnerNameInput'):
            self.assertRegex(html, rf'id="{field}"[^>]*maxlength="{main.NAME_MAX}"')

    def test_theme_intro_copy_has_no_broken_particle(self):
        html = open(os.path.join(os.path.dirname(main.__file__), 'index.html'), encoding='utf-8').read()
        self.assertNotIn('일까과', html)


class AnnualEditionTests(AccountCase):
    """올해운세는 해마다 따로 산다. 12월부터는 다음 해 풀이를 판다(11/23 정오님 결정)."""

    def on(self, year, month, day=5):
        import datetime
        clock = patch.object(main, '_kst_today', return_value=datetime.date(year, month, day))
        clock.start(); self.addCleanup(clock.stop)
        return clock

    def buy(self):
        return main.unlock_report(UnlockReportRequest(user_id=USER, report_key='sinnian', cost=300))

    def annuals(self):
        return [(r['report_year'], r['annual_role']) for r in main.client_reports(USER) if r['report_key'] == 'sinnian']

    def test_sale_year_switches_in_december(self):
        import datetime
        self.assertEqual(main._annual_sale_year(datetime.date(2026, 11, 30)), 2026)
        self.assertEqual(main._annual_sale_year(datetime.date(2026, 12, 1)), 2027)
        self.assertEqual(main._annual_sale_year(datetime.date(2027, 1, 1)), 2027)

    def test_december_purchase_is_next_years_reading(self):
        self.save(); clock = self.on(2026, 12)
        bought = self.buy()
        report = bought['unlocked_reports'][bought['focus_index']]
        self.assertEqual(report['report_year'], 2027)
        self.assertIn('2027년', report['report_title'])
        self.assertIn('丁未', text_of(report['report_content']))      # 2027년 = 정미(丁未)년
        self.assertEqual(report['annual_role'], 'sale')
        self.assertEqual(bought['annual_sale_year'], 2027)

    def test_this_years_owner_can_buy_next_year_from_december(self):
        self.save(); first = self.on(2026, 11)
        self.buy(); first.stop()
        self.assertEqual(self.annuals(), [(2026, 'sale')])
        self.on(2026, 12)
        self.assertEqual(self.annuals(), [(2026, 'current')])        # 12월에도 올해 풀이는 그대로 읽는다
        before = users_db[USER]['coin']
        bought = self.buy()
        self.assertEqual(users_db[USER]['coin'], before - 300)
        self.assertEqual(self.annuals(), [(2026, 'current'), (2027, 'sale')])
        self.assertEqual(bought['unlocked_reports'][bought['focus_index']]['report_year'], 2027)

    def test_same_year_is_never_charged_twice(self):
        self.save(); self.on(2026, 12)
        self.buy(); before = users_db[USER]['coin']
        again = self.buy()
        self.assertEqual(users_db[USER]['coin'], before)
        self.assertEqual(self.annuals(), [(2027, 'sale')])
        self.assertEqual(again['unlocked_reports'][again['focus_index']]['report_year'], 2027)

    def test_last_years_reading_does_not_block_the_new_year(self):
        self.save(); first = self.on(2026, 6)
        self.buy(); first.stop()
        self.on(2027, 1)
        self.assertEqual(self.annuals(), [(2026, 'past')])
        self.buy()
        self.assertEqual(self.annuals(), [(2026, 'past'), (2027, 'sale')])

    def test_old_years_reading_keeps_its_own_year_when_refreshed(self):
        import wallet_store
        self.save(); first = self.on(2026, 6)
        self.buy(); first.stop()
        self.on(2027, 3); self.buy()
        with wallet_store.locked(USER) as (_, _, state):
            state['reports'][0]['narrative_version'] = 'old'
            reports_db[USER] = state['reports']
        years = [(r['report_year'], r['report_title'][:5]) for r in main.client_reports(USER)]
        self.assertEqual(years, [(2026, '2026년'), (2027, '2027년')])


class SoonReportsTests(AccountCase):
    """11/25부터 '곧 열려요' 없이 모든 풀이를 판다. 화면과 서버 목록은 늘 같아야 한다."""

    def buy(self, key, cost):
        return main.unlock_report(UnlockReportRequest(user_id=USER, report_key=key, cost=cost))

    def test_all_theme_readings_sell_now(self):
        # 11/25: '곧 열려요'를 없앴다 — 테마운 6개 모두 복채로 바로 산다(테스트 계정이 아니어도).
        import report_access
        for key in ('business', 'venture', 'love', 'health', 'wealth', 'study'):
            self.assertTrue(report_access.on_sale(key), key)
        self.save()
        for key in ('venture', 'love', 'study'):
            self.buy(key, 220)
        self.assertEqual({r['report_key'] for r in main.client_reports(USER)}, {'venture', 'love', 'study'})

    def test_open_readings_still_sell(self):
        self.save()
        self.buy('daewoon', 450); self.buy('sinnian', 300)
        self.assertEqual({r['report_key'] for r in main.client_reports(USER)}, {'daewoon', 'sinnian'})

    def test_server_and_screen_share_the_same_soon_list(self):
        import report_access
        html = open(os.path.join(os.path.dirname(main.__file__), 'index.html'), encoding='utf-8').read()
        listed = re.search(r"DALHA_SOON_REPORTS = new Set\(\[([^\]]*)\]\)", html).group(1)
        self.assertEqual(set(re.findall(r"'(\w+)'", listed)), set(report_access.SOON_REPORTS))


class AgeTests(TestCase):
    """나이를 보지 않던 풀이: 어린 나이에는 읽는 법 한 줄을 먼저 붙이고, 아주 고령에는 '다음 10년'을 잇지 않는다."""

    def read(self, key, birth_year, name='시험'):
        user = dict(ME, name=name, birth_year=birth_year)
        return generate_detailed_report(key, '기본', '', '', name, user=user, is_unlocked=True)['content']

    def year(self, offset):
        return main._kst_today().year - offset

    def test_child_gets_a_reading_note_first(self):
        for key in ('daewoon', 'sinnian', 'business', 'love', 'wealth'):
            with self.subTest(key=key):
                content = self.read(key, self.year(6))
                self.assertRegex(content, r'^<div[^>]*><p class="reading-age-note">시험님은 아직 어린 나이예요\.')

    def test_teen_gets_the_teen_note(self):
        self.assertIn('아직 자라는 나이예요', self.read('love', self.year(16)))

    def test_adult_and_child_friendly_readings_have_no_note(self):
        self.assertNotIn('reading-age-note', self.read('love', self.year(19)))
        for key in ('study', 'health'):
            self.assertNotIn('reading-age-note', self.read(key, self.year(6)))

    def test_note_escapes_the_name(self):
        self.assertNotIn('<b>', self.read('wealth', self.year(6), name='<b>굵게</b>').split('</p>')[0].split('reading-age-note">')[1])

    def test_very_old_reader_is_not_told_about_a_decade_past_ninety(self):
        for key in ('business', 'love'):
            for age in (85, 92, 99):
                with self.subTest(key=key, age=age):
                    self.assertNotRegex(text_of(self.read(key, self.year(age))), r'다음 10년\((9[1-9]|1\d\d)세부터')
