from datetime import date
from unittest import TestCase
from main import calculate_biorhythm, get_saju_pillars_and_analysis
from app.engine.calendar import to_solar

class BiorhythmTests(TestCase):
    def test_reported_regression_uses_actual_three_phases(self):
        r = calculate_biorhythm(1978,3,13,date(2026,9,10))
        self.assertEqual([r[k]['val'] for k in ('physical','emotional','intellectual')],[73,-62,-100])
        self.assertIn('지성은 저조기',r['overall_summary'])
        self.assertNotIn('우수',r['overall_summary'])
        self.assertNotIn('의사결정에 적합',r['overall_summary'])
        self.assertIn('최저점',r['overall_summary'])

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
            for key in ('physical','emotional','intellectual'):
                self.assertLessEqual(abs(r[key]['val']),100)
                if days == 0: self.assertEqual(r[key]['val'],0)
