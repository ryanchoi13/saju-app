import json
import os
import subprocess
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import date, time, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

import main
import menu_store
from fastapi import HTTPException
from app.engine.core.models import BirthInput
from app.engine.services.ranked_menu import build_rankings

DAY = date(2026, 9, 11)
BIRTH = BirthInput(name='테스트', gender='male', birth_date=date(1978, 3, 13), birth_time=time(10, 30))


class RankingTests(TestCase):
    def test_element_score_dominates_and_uncertainty_is_labelled(self):
        for favored in '木火土金水':
            result = build_rankings(BIRTH, DAY, {favored:4}, '土', 'medium')
            for mode, items in result['rankings'].items():
                self.assertEqual(len(items), 20 if mode == 'general' else 10)
                self.assertEqual(len({m['menu'] for m in items}), len(items))
                scores = [m['element_score'] for m in items]
                self.assertEqual(scores, sorted(scores, reverse=True))
                self.assertEqual(items[0]['element'], favored)
            self.assertEqual(result['basis'], 'core_direction')
        fallback = build_rankings(BIRTH, DAY, {}, '土', 'low')
        self.assertEqual(fallback['basis'], 'daily_symbol')
        self.assertEqual(fallback['confidence'], 'low')
        self.assertIn('일진', fallback['basis_text'])
        self.assertEqual(fallback['element_scores']['土'], 1)

    def test_breakfast_can_rank_first_and_caution_is_never_promoted(self):
        from app.engine.services.daily_menu import DIET_MENU_POOL
        breakfast = next(m for m in DIET_MENU_POOL if m.name == '계란후라이와 통밀토스트')
        others = [m for m in DIET_MENU_POOL if m.element != breakfast.element]
        with patch('app.engine.services.ranked_menu.DIET_MENU_POOL', (breakfast,*others)):
            result = build_rankings(BIRTH, DAY, {'火':6,'水':-4}, '水', 'medium')
        self.assertEqual(result['rankings']['diet'][0]['menu'], breakfast.name)
        self.assertNotIn('水', {m['element'] for m in result['rankings']['diet']})
        fallback = build_rankings(BIRTH, DAY, {'土':-4}, '土', 'low')
        self.assertEqual(fallback['element_scores']['土'], -4)
        self.assertNotIn('土', {m['element'] for m in fallback['rankings']['general']})

    def test_deterministic_names_do_not_affect_the_ranking(self):
        a=build_rankings(BIRTH, DAY, {}, '土', 'low')
        b=build_rankings(BIRTH.model_copy(update={'name':'다른 표시 이름'}), DAY, {}, '土', 'low')
        self.assertEqual(a,b)


class MenuStoreTests(TestCase):
    def setUp(self):
        self.temp=TemporaryDirectory()
        self.env=patch.dict(os.environ, {'DATABASE_URL':'','RENDER':'','RENDER_SERVICE_ID':'',
            'DALHA_WARDROBE_DB':str(Path(self.temp.name)/'test.sqlite')})
        self.env.start(); menu_store.initialize()
        self.payload=build_rankings(BIRTH, DAY, {}, '土', 'low')
        self.first=menu_store.load('user_test', DAY, lambda:self.payload)

    def tearDown(self):
        self.env.stop(); self.temp.cleanup()

    def request(self, state, mode=None, action='next', day=DAY):
        mode=mode or state['mode']
        return menu_store.explore('user_test', day, lambda:build_rankings(BIRTH,day,{},'土','low'),
            token=state['token'], mode=mode, action=action, expected_day=state['date'],
            expected_seen=state['mode_counts'][mode])

    def test_independent_limits_reopen_and_history(self):
        state=self.first
        self.assertEqual(state['seen_sets'],1)
        shown=[m['menu'] for m in state['items']]
        for i in range(2,11):
            state=self.request(state)
            self.assertEqual(state['seen_sets'],i)
            shown += [m['menu'] for m in state['items']]
        self.assertTrue(state['exhausted']); self.assertEqual(len(set(shown)),20)
        self.assertEqual(self.request(state)['seen_sets'],10)
        reopened=menu_store.load('user_test',DAY,lambda:None)
        self.assertEqual(reopened['items'],self.first['items'])
        self.assertEqual(len(reopened['history']),20)
        state=self.request(state,'diet','open')
        self.assertEqual(state['seen_sets'],1); self.assertEqual(state['mode_counts']['general'],10)
        for _ in range(4): state=self.request(state)
        self.assertEqual(len(state['history']),10); self.assertTrue(state['exhausted'])
        self.assertEqual(self.request(state)['seen_sets'],5)
        back=self.request(state,'general','open')
        self.assertEqual(back['items'],self.first['items']); self.assertTrue(back['exhausted'])

    def test_retry_and_concurrent_next_only_advance_once(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            results=list(pool.map(lambda _:self.request(self.first), range(4)))
        self.assertEqual({r['seen_sets'] for r in results},{2})
        self.assertEqual(self.request(self.first)['items'],results[0]['items'])

    def test_restart_uses_snapshot_not_new_profile_or_algorithm(self):
        state=self.request(self.first,'diet','open');state=self.request(state)
        code="import json, menu_store; from datetime import date; print(json.dumps(menu_store.load('user_test',date(2026,9,11),lambda:None)))"
        restored=json.loads(subprocess.check_output([sys.executable,'-c',code],text=True))
        self.assertEqual(restored['mode'],'diet');self.assertEqual(restored['seen_sets'],2)
        self.assertEqual(restored['display_set'],1);self.assertEqual(restored['token'],state['token'])

    def test_midnight_resets_without_spending_an_extra_set(self):
        state=self.request(self.first,'diet','open');state=self.request(state)
        tomorrow=self.request(state,day=DAY+timedelta(days=1))
        self.assertEqual(tomorrow['mode'],'diet');self.assertEqual(tomorrow['seen_sets'],1)
        self.assertEqual(tomorrow['mode_counts']['general'],0)
        self.assertEqual(tomorrow['display_set'],1)
        self.assertNotEqual(tomorrow['token'],state['token'])

    def test_account_isolation_invalid_token_and_unavailable_storage(self):
        other=menu_store.load('user_other',DAY,lambda:self.payload)
        self.assertNotEqual(other['token'],self.first['token'])
        with self.assertRaises(KeyError):
            menu_store.explore('user_other',DAY,lambda:self.payload,token=self.first['token'],
                mode='general',action='next',expected_day=str(DAY),expected_seen=1)
        with patch.dict(os.environ,{'RENDER':'true'}):
            with self.assertRaises(menu_store.StorageUnavailable):
                self.request(self.first)
        self.assertEqual(menu_store.load('user_test',DAY,lambda:None)['seen_sets'],1)

    def test_api_profile_binding_and_service_integration(self):
        main.users_db['user_test']=dict(name='테스트',gender='male',birth_year=1978,birth_month=3,
            birth_day=13,calendar_type='solar',sijin_index=5,profile_complete=True)
        try:
            req=main.MenuExploreRequest(user_id='user_test',token=self.first['token'],mode='general',
                action='next',expected_day=str(DAY),expected_seen=1)
            with patch.object(menu_store,'today',return_value=DAY):
                self.assertEqual(main.explore_menus(req)['seen_sets'],2)
                with self.assertRaises(HTTPException) as err:
                    main.explore_menus(req.model_copy(update={'user_id':'user_unknown'}))
                self.assertEqual(err.exception.status_code,401)
            result=main.get_saju_pillars_and_analysis('테스트','male',1978,3,13,'solar',5,menu_account_id='user_test')
            fortune=result['daily_fortune']
            self.assertIn('menu_recommendations',fortune)
            self.assertEqual(fortune['recommended_meals'],[])
            self.assertNotIn('점심',fortune['menu_recommendations']['basis_text'])
        finally: main.users_db.pop('user_test',None)
