from datetime import date, time
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from app.engine.services import meal_history
from app.engine.services.meal_feedback import attach, update, preference_context, preference_bonus
from app.engine.services.menu_demographics import demographic_evidence, age_band
from app.engine.services.daily_menu import MENU_POOL

class MealPersonalizationTests(TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory();self.old=meal_history._DB;meal_history._DB=None
        self.env=patch.dict('os.environ',{'DALHA_MENU_HISTORY_DB':self.temp.name+'/history.sqlite'})
        self.env.start()
    def tearDown(self):
        if meal_history._DB:meal_history._DB.close()
        meal_history._DB=self.old;self.env.stop();self.temp.cleanup()
    def plan(self,day='2026-09-08',mode='general'):
        return {'date':day,'mode':mode,'meals':[{'menu':'제육볶음','ingredient':'pork','cuisine':'korean','category':'meat_stirfry'}]*3}
    def test_like_is_idempotent_persistent_and_cancellable(self):
        first=attach('a',self.plan());token=first['feedback']['token']
        update(token,liked=True);update(token,liked=True)
        meal_history._DB.close();meal_history._DB=None
        second=attach('a',self.plan())
        self.assertEqual(token,second['feedback']['token']);self.assertTrue(second['feedback']['liked'])
        self.assertEqual(preference_context('a','general',date(2026,9,9))['liked_plans'],1)
        update(token,liked=False)
        self.assertFalse(attach('a',self.plan())['feedback']['liked'])
    def test_accounts_modes_and_plan_revisions_are_isolated(self):
        a=attach('a',self.plan());b=attach('b',self.plan());diet=attach('a',self.plan(mode='diet'))
        self.assertNotEqual(a['feedback']['token'],b['feedback']['token'])
        update(a['feedback']['token'],liked=True)
        self.assertFalse(attach('b',self.plan())['feedback']['liked'])
        self.assertFalse(diet['feedback']['liked'])
        revised=self.plan();revised['meals'][0]={**revised['meals'][0],'menu':'다른 메뉴'}
        self.assertNotEqual(attach('a',revised)['feedback']['token'],a['feedback']['token'])
        with self.assertRaises(KeyError):update('invented token',liked=True)
    def test_unseen_and_unliked_are_not_negative_preferences(self):
        token=attach('a',self.plan())['feedback']['token']
        self.assertEqual(preference_context('a','general',date(2026,9,10))['weights'],{})
        update(token,seen=True);update(token,seen=True)
        self.assertEqual(preference_context('a','general',date(2026,9,10))['weights'],{})
    def test_whole_plan_signal_requires_multiple_days_and_no_future_leak(self):
        tokens=[]
        for day in (8,9,10):
            token=attach('a',self.plan(f'2026-09-{day:02}'))['feedback']['token'];tokens.append(token);update(token,liked=True)
        self.assertEqual(preference_context('a','general',date(2026,9,10))['weights'],{})
        context=preference_context('a','general',date(2026,9,11))
        self.assertEqual(context['liked_plans'],3)
        pork=next(c for c in MENU_POOL if c.name=='제육볶음')
        self.assertGreater(preference_bonus(pork,context),0)
        self.assertLessEqual(preference_bonus(pork,context),4)
        self.assertTrue(all(not key.startswith('menu:') for key in context['weights']))
        update(tokens[0],liked=False)
        self.assertEqual(preference_context('a','general',date(2026,9,11))['weights'],{})
    def test_demographics_use_actual_age_bounds_and_unknown_fallback(self):
        self.assertEqual(age_band(29),'19-29');self.assertEqual(age_band(30),'30-49')
        self.assertEqual(age_band(49),'30-49');self.assertEqual(age_band(50),'50-64')
        self.assertEqual(demographic_evidence('없는 음식',48,'male')['bonus'],0)
        evidence=demographic_evidence('김치찌개',48,'male')
        self.assertEqual(evidence['status'],'survey_age_sex')
        self.assertEqual(evidence['age_band'],'30-49')
        self.assertEqual(evidence['gender'],'male')
        self.assertLessEqual(abs(evidence['bonus']),2)
    def test_same_birth_accounts_do_not_share_recommendation_cache(self):
        from app.engine.core.models import BirthInput
        birth=BirthInput(name='test',gender='male',birth_date=date(1978,3,13),birth_time=time(11))
        def build(label):return lambda *args:{m:{'date':'2026-09-08','mode':m,'meals':[{'menu':label}]} for m in ('general','diet')}
        a=meal_history.stored_plans(birth,date(2026,9,8),build('a'),account_key='a')
        b=meal_history.stored_plans(birth,date(2026,9,8),build('b'),account_key='b')
        self.assertNotEqual(a['general']['meals'],b['general']['meals'])
