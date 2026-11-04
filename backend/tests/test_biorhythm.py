from datetime import date
from unittest import TestCase
from main import calculate_biorhythm, get_saju_pillars_and_analysis
from app.engine.calendar import to_solar

class BiorhythmTests(TestCase):
    def test_reported_regression_uses_actual_three_phases(self):
        r = calculate_biorhythm(1978,3,13,date(2026,9,10))
        self.assertEqual([r[k]['val'] for k in ('physical','emotional','intellectual')],[73,-62,-100])
        self.assertIn('신체는 고조기',r['overall_summary'])
        self.assertIn('감성·지성은 저조기',r['overall_summary'])
        self.assertIn('하나씩 정리',r['overall_summary'])
        self.assertNotIn('interpretation_note',r)
        self.assertNotIn('의사결정에 적합',r['overall_summary'])
        self.assertLessEqual(len(r['overall_summary']),110)
        self.assertEqual(r['overall_summary'].count('.'),2)

    def test_lunar_and_equivalent_solar_birth_agree(self):
        solar = to_solar(date(1978,3,13),'lunar',False)
        lunar_result = get_saju_pillars_and_analysis('검증','male',1978,3,13,'lunar',5)
        solar_result = get_saju_pillars_and_analysis('검증','male',solar.year,solar.month,solar.day,'solar',5)
        self.assertEqual(lunar_result['biorhythm'],solar_result['biorhythm'])

    def test_birth_day_is_zero_and_cycle_is_bounded(self):
        from datetime import timedelta
        start = date(2000,1,1)
        for days in range(70):
            r = calculate_biorhythm(2000,1,1,start+timedelta(days=days))
            self.assertLessEqual(len(r['overall_summary']),110)
            self.assertNotIn('\n',r['overall_summary'])
            for key in ('physical','emotional','intellectual'):
                self.assertLessEqual(abs(r[key]['val']),100)
                if days == 0: self.assertEqual(r[key]['val'],0)


class BiorhythmPhaseNamingTests(TestCase):
    """2026-11-04: + 고조기 / - 저조기 / 0을 지나는 날 요주의일 (일반 바이오리듬 앱 관례)."""

    def test_no_more_stable_label(self):
        from datetime import timedelta
        for i in range(60):
            r = calculate_biorhythm(1978,3,13,date(2026,11,1)+timedelta(days=i))
            self.assertNotIn('안정기', r['overall_summary'])

    def test_reported_day_names_crossing(self):
        r = calculate_biorhythm(1978,3,13,date(2026,11,4))
        self.assertEqual(r['physical']['status'], '요주의일')      # -14, 어제 +14 → 0을 지난 첫날
        self.assertEqual(r['emotional']['status'], '저조기')
        self.assertEqual(r['intellectual']['status'], '고조기')
        self.assertIn('신체는 요주의일', r['overall_summary'])

    def test_one_critical_day_per_half_cycle(self):
        from datetime import timedelta
        for key, period in (('physical',23),('emotional',28),('intellectual',33)):
            days = [i for i in range(period*4)
                    if calculate_biorhythm(2000,1,1,date(2000,1,1)+timedelta(days=i))[key]['status'] == '요주의일']
            self.assertEqual(len(days), 8, key)                    # 한 주기에 두 번, 네 주기면 여덟 번
            self.assertEqual(len(set(d // (period/2) for d in days)), 8, key)
