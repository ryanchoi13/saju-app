"""Documented-contract fixtures, not evidence of a live SAZU integration."""
import io
import json
import os
import tempfile
import unittest
from datetime import date, time, timedelta
from types import SimpleNamespace
from unittest.mock import patch

import meal_set_store as store
import sazu_food


def profile(**changes):
    fields = dict(birth_date=date(1992, 5, 16), birth_time=time(8, 15),
                  time_unknown=False, gender='female', calendar_type='solar',
                  is_leap_month=False, birth_place=None)
    fields.update(changes)
    return SimpleNamespace(**fields)


def balance():
    return dict(basket={'grains': {'staple': {'name': '쌀', 'reason': '제공자 설명'}, 'mix': []},
                        'protein': [{'name': '두부', 'reason': '제공자 설명'}]},
                why=['제공자 근거'], cautions=['주의 문구'], disclaimer='의료 조언이 아닙니다.',
                rotation={'note': '매일 바뀝니다.'})


class SazuFoodTests(unittest.TestCase):
    def test_request_preserves_calendar_time_without_name(self):
        data = sazu_food.build_request(profile(calendar_type='lunar', is_leap_month=True), date(2026, 10, 5))
        self.assertEqual((data['birthHour'], data['birthMinute']), (8, 15))
        self.assertTrue(data['isLunar'] and data['isLeapMonth'] and data['isFemale'])
        self.assertNotIn('name', data)
        self.assertNotIn('birthCity', data)
        self.assertEqual(data['foodRotation'], 'daily')
        self.assertIsNone(sazu_food.build_request(profile(time_unknown=True), date(2026, 10, 5))['birthHour'])

    def test_result_not_rescored_and_private_modules_not_returned(self):
        food = balance()
        reply = {'success': True, 'data': {'modules': {'foodBalance': food, 'fourPillars': {'private': True}}}}
        with patch.dict(os.environ, {'SAZU_API_KEY': 'test-only-not-a-real-key'}), patch('sazu_food.urlopen', return_value=io.BytesIO(json.dumps(reply).encode())) as call:
            result = sazu_food.build_set(profile(), date(2026, 10, 5))
        self.assertEqual(result['food_balance'], food)
        self.assertEqual(result['meals'], [])
        self.assertNotIn('fourPillars', result)
        self.assertEqual(call.call_count, 1)
        self.assertEqual(json.loads(call.call_args.args[0].data)['date'], '2026-10-05')

    def test_errors_do_not_echo_secrets_or_silently_fallback(self):
        with patch.dict(os.environ, {'SAZU_API_KEY': 'test-only-secret'}), patch('sazu_food.urlopen', side_effect=TimeoutError('private birth details test-only-secret')):
            with self.assertRaises(ValueError) as error:
                sazu_food.build_set(profile(), date(2026, 10, 5))
        self.assertNotIn('secret', str(error.exception))
        self.assertNotIn('private', str(error.exception))
        reply = {'data': {'modules': {'foodBalance': {'basket': {'protein': []}}}}}
        with patch.dict(os.environ, {'SAZU_API_KEY': 'test'}), patch('sazu_food.urlopen', return_value=io.BytesIO(json.dumps(reply).encode())):
            with self.assertRaises(ValueError):
                sazu_food.build_set(profile(), date(2026, 10, 5))

    def test_rollout_requires_exact_account(self):
        with patch.dict(os.environ, {'SAZU_FOOD_TRIAL_USERS': 'user_123, user_456'}):
            self.assertEqual(sazu_food.provider_for('user_123'), 'sazu')
            self.assertEqual(sazu_food.provider_for('user_12'), 'offline')
            self.assertEqual(sazu_food.provider_for(None), 'offline')

    def test_profile_changes_invalidate_cache_scope(self):
        first = sazu_food.profile_key(profile())
        changed = sazu_food.profile_key(profile(birth_time=time(9, 15)))
        self.assertNotEqual(first, changed)
        self.assertNotEqual(store._provider_owner('user_123', 'sazu', first), store._provider_owner('user_123', 'sazu', changed))

    def test_cache_isolation_reload_rollover_and_token_ownership(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {'DALHA_WARDROBE_DB': tmp+'/test.sqlite', 'DATABASE_URL': '', 'RENDER': '', 'RENDER_SERVICE_ID': ''}):
            day = date(2026, 10, 5)
            calls = []
            def build(*args):
                calls.append(args)
                return {'provider': 'sazu', 'food_balance': balance(), 'meals': []}
            old = store.load('user_123', day, lambda *args: {'meals': [{'id': 'old', 'menu': '기존'}]})
            first = store.load('user_123', day, build, provider='sazu')
            self.assertNotEqual(first['token'], old['token'])
            self.assertEqual(first['version'], 'sazu-food-v1')
            self.assertEqual(first, store.load('user_123', day, build, provider='sazu'))
            self.assertEqual(len(calls), 1)
            params = dict(token=first['token'], mode='general', action='open', expected_day=str(day), expected_seen=1, provider='sazu')
            with self.assertRaises(KeyError):
                store.explore('user_456', day, build, **params)
            with self.assertRaises(ValueError):
                store.explore('user_123', day, build, **dict(params, action='next'))
            next_day = store.explore('user_123', day+timedelta(days=1), build, **params)
            self.assertEqual(next_day['date'], '2026-10-06')
            self.assertEqual(len(calls), 2)
            self.assertEqual(store.load('user_123', day, lambda *a: self.fail('offline cache lost'))['items'][0]['id'], 'old')


if __name__ == '__main__':
    unittest.main()
