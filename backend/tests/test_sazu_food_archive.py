import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import sazu_food_archive as archive


class ArchiveTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = patch.dict(os.environ, {
            'DALHA_WARDROBE_DB': str(Path(self.tmp.name) / 'archive.sqlite'),
            'SAZU_API_KEY': 'test-only', 'SAZU_FOOD_COLLECT_DATES': '2026-10-05',
            'SAZU_FOOD_COLLECT_LIMIT': '1'}, clear=True)
        self.env.start()
        self.profile = dict(birthYear=1998,birthMonth=5,birthDay=19,birthHour=10,
                            isFemale=False,isLunar=False,birthCity='서울')
        self.balance = dict(basket={'protein':[{'id':'tofu','name':'두부','reason':'개인별 이유'}]},
            plan={'days':[{'date':'2026-10-05','sides':[{'id':'tofu','name':'두부'},
                {'id':'fish','name':'생선'}]}]}, boost=['fire','water'])
        archive.initialize()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def test_observations_preserve_context_without_inferred_elements(self):
        body = archive.make_requests([self.profile], ['2026-10-05'], 1)[0]
        key, fresh = archive.claim(body)
        self.assertTrue(fresh)
        self.assertEqual(archive.save_response(key, self.balance), 2)
        with archive._connection() as (conn, pg):
            rows = conn.execute('SELECT raw_item FROM sazu_food_observations').fetchall()
            raw = conn.execute('SELECT food_balance FROM sazu_food_research').fetchone()[0]
        self.assertEqual(len(rows), 3)
        self.assertEqual(json.loads(raw), self.balance)
        self.assertTrue(all('element' not in json.loads(r[0]) for r in rows))
        self.assertFalse(archive.claim(body)[1])

    def test_monthly_requests_are_bounded_and_strip_identity(self):
        profile = dict(self.profile, name='private name', user_id='private account')
        requests = archive.make_requests([profile, profile], ['2026-01-15','2026-04-15'], 2)
        self.assertEqual(len(requests), 2)
        for body in requests:
            self.assertEqual(body['foodPlan'], 'monthly')
            self.assertNotIn('name', body)
            self.assertNotIn('user_id', body)

    def test_restart_does_not_repeat_paid_calls(self):
        calls = []
        def api(path, body=None):
            if path == '/v2/me':
                return dict(success=True,data={'tier':'paid','remaining':100,'rateLimitPerMinute':30})
            if path == '/v2/sazu/samples':
                return dict(success=True,data={'samples':[{'input':self.profile}]})
            calls.append(body)
            return dict(success=True,data={'modules':{'foodBalance':self.balance}})
        archive.run(lambda: [], api=api, sleep=lambda _:None)
        archive.run(lambda: [], api=api, sleep=lambda _:None)
        self.assertEqual(len(calls), 1)

    def test_failed_request_not_retried_or_error_text_saved(self):
        def api(path, body=None):
            if path == '/v2/me':
                return dict(data={'tier':'paid','remaining':100,'rateLimitPerMinute':30})
            if path == '/v2/sazu/samples':
                return dict(data={'samples':[{'input':self.profile}]})
            raise RuntimeError('secret must not be retained')
        with self.assertRaises(RuntimeError):
            archive.run(lambda: [], api=api, sleep=lambda _:None)
        archive.run(lambda: [], api=api, sleep=lambda _:None)
        with archive._connection() as (conn, pg):
            state, kind = conn.execute('SELECT state,error_kind FROM sazu_food_research').fetchone()
        self.assertEqual((state,kind),('failed','RuntimeError'))

    def test_unknown_or_free_quota_refused(self):
        for data in [{'tier':'paid'}, {'tier':'free','remaining':1000}, {'remaining':True}]:
            with self.assertRaises(ValueError):
                archive.quota_remaining({'data':data})

    def test_disabled_start_has_no_thread_or_api_calls(self):
        with patch.object(archive.threading, 'Thread') as thread:
            archive.start(lambda: [])
            thread.assert_not_called()


if __name__ == '__main__':
    unittest.main()
