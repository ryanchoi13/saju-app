from datetime import date, timedelta
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

import meal_set_store as store


class MealSetLimitTests(TestCase):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        env = patch.dict('os.environ', {'DALHA_WARDROBE_DB': self.directory.name + '/test.sqlite',
                                      'DATABASE_URL': '', 'RENDER': '', 'RENDER_SERVICE_ID': ''})
        env.start()
        self.addCleanup(env.stop)
        self.day = date(2026, 9, 21)
        self.built = {'general': 0, 'diet': 0}

    def build(self, mode, history, excluded):
        self.built[mode] += 1
        number = self.built[mode]
        return {'meals': [dict(id=f'{mode}-{number}-{p}', menu=f'{mode} {number} {p}',
                               period=p, kcal=400) for p in ('breakfast', 'lunch', 'dinner')]}

    def explore(self, state, mode, action='next', expected=None, day=None):
        return store.explore('user_limit_test', day or self.day, self.build, token=state['token'],
                             mode=mode, action=action, expected_day=state['date'],
                             expected_seen=state['mode_counts'][mode] if expected is None else expected)

    def test_three_sets_each_order_reload_and_duplicate_requests(self):
        state = store.load('user_limit_test', self.day, self.build)
        for mode in ('general', 'diet'):
            state = self.explore(state, mode, 'open')
            first = state['plan']['meals']
            self.assertFalse(state['exhausted'])
            state = self.explore(state, mode)
            duplicate = self.explore(state, mode, expected=1)
            self.assertEqual(duplicate['plan'], state['plan'])
            state = self.explore(state, mode)
            for _ in range(3):
                state = self.explore(state, mode)
            self.assertTrue(state['exhausted'])
            self.assertEqual(state['set_limit'], 3)
            self.assertEqual(self.built[mode], 3)
            self.assertEqual(state['history'][0]['meals'], first)
            self.assertEqual([p['recommendation_number'] for p in state['history']], [1, 2, 3])
            self.assertEqual(len({m['id'] for p in state['history'] for m in p['meals']}), 9)
            self.assertEqual(store.load('user_limit_test', self.day, self.build), state)
        next_day = self.explore(state, 'general', day=self.day + timedelta(days=1))
        self.assertEqual(next_day['seen_sets'], 1)
        self.assertFalse(next_day['exhausted'])

    def test_existing_five_set_day_preserves_storage_but_displays_first_three(self):
        with patch.object(store, 'SET_LIMIT', 5):
            state = store.load('user_limit_test', self.day, self.build)
            for _ in range(4):
                state = self.explore(state, 'general')
        original = state['history']
        state = store.load('user_limit_test', self.day, self.build)
        state = self.explore(state, 'general')
        self.assertEqual(state['history'], original[:3])
        self.assertEqual(state['plan'], original[2])
        self.assertEqual(state['seen_sets'], 3)
        self.assertEqual(state['mode_counts']['general'], 5)
        self.assertEqual(self.built['general'], 5)
        self.assertTrue(state['exhausted'])
