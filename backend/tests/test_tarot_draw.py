from concurrent.futures import ThreadPoolExecutor
from unittest import TestCase
from pydantic import ValidationError
from main import TAROT_DECK, TarotDrawRequest, get_daily_tarot
from fastapi import HTTPException
import tarot_service as tarot
import tarot_store
import os
from tempfile import TemporaryDirectory
from unittest.mock import patch

class TarotDrawTests(TestCase):
    def setUp(self):
        self.tmp=TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        env=patch.dict(os.environ,{'DATABASE_URL':'','RENDER':'','RENDER_SERVICE_ID':'','DALHA_WARDROBE_DB':self.tmp.name+'/tarot.sqlite'})
        env.start();self.addCleanup(env.stop)
        tarot.SESSIONS.clear()
        self.users = {'user_reader':{'coin':30},'user_other':{'coin':5}}

    def draw(self, key='free-request-00001', paid=False, slot=1, user='reader', day='2026-09-10', choose=None):
        return tarot.draw(self.users,TAROT_DECK,choose or (lambda deck:deck[0]),user_id='user_'+user,slot=slot,request_id=key,is_paid=paid,day=day)

    def test_free_paid_repeat_and_server_balance(self):
        first=self.draw()
        self.assertEqual((first['cost'],first['new_balance']),(0,30))
        self.assertTrue(first['card']['description'])
        with self.assertRaises(tarot.DrawError) as caught: self.draw('second-free-00001',slot=2)
        self.assertEqual(caught.exception.detail['code'],'payment_required')
        self.assertEqual(self.users['user_reader']['coin'],30)
        second=self.draw('paid-request-00001',True,2)
        self.assertNotEqual(first['card']['name'],second['card']['name'])
        self.assertEqual(second['new_balance'],20)
        retry=self.draw('paid-request-00001',True,2)
        self.assertEqual(retry,second)
        self.users['user_reader']['coin']=25
        self.assertEqual(self.draw('paid-request-00001',True,2)['new_balance'],25)

    def test_parallel_requests_spend_once(self):
        self.draw()
        with ThreadPoolExecutor(max_workers=8) as pool:
            results=list(pool.map(lambda _:self.draw('parallel-paid-001',True,2),range(12)))
        self.assertEqual(self.users['user_reader']['coin'],20)
        self.assertTrue(all(r==results[0] for r in results))

    def test_insufficient_unknown_user_and_failed_draw_do_not_spend(self):
        self.draw(user='other')
        with self.assertRaises(tarot.DrawError) as caught: self.draw('paid-other-request',paid=True,user='other',slot=2)
        self.assertEqual(caught.exception.status,402)
        self.assertEqual(self.users['user_other']['coin'],5)
        with self.assertRaises(tarot.DrawError) as caught: self.draw(user='missing')
        self.assertEqual(caught.exception.status,401)
        def fail(_): raise RuntimeError('card unavailable')
        with self.assertRaises(tarot_store.StorageUnavailable): self.draw(paid=True,choose=fail)
        self.assertEqual(self.users['user_reader']['coin'],30)

    def test_receipt_reuse_cannot_change_slot_or_payment(self):
        self.draw('same-request-00001',True)
        with self.assertRaises(tarot.DrawError): self.draw('same-request-00001',True,2)
        with self.assertRaises(tarot.DrawError): self.draw('same-request-00001',False)
        self.assertEqual(self.users['user_reader']['coin'],30)

    def test_new_day_and_accounts_have_separate_free_draws(self):
        self.draw()
        self.assertEqual(self.draw(user='other')['cost'],0)
        self.assertEqual(self.draw(day='2026-09-11')['cost'],0)
        self.assertEqual(self.users['user_reader']['coin'],30)

    def test_three_unique_cards_survive_restart_and_fourth_does_not_spend(self):
        results=[self.draw('unique-request-'+str(i),paid=i>1,slot=i) for i in (1,2,3)]
        self.assertEqual(len({r['card']['name'] for r in results}),3)
        tarot.SESSIONS.clear()
        state=tarot.get_state('user_reader','2026-09-10')
        self.assertEqual(state['count'],3)
        old=self.draw('fourth-request-0001',True,1)
        self.assertEqual(old['card'],results[0]['card'])
        self.assertEqual(self.users['user_reader']['coin'],10)
        self.assertEqual(tarot.get_state('user_reader','2026-09-11')['cards'],[])

    def test_midnight_request_rejected_without_spending(self):
        with self.assertRaises(tarot.DrawError) as caught:
            tarot.draw(self.users,TAROT_DECK,lambda d:d[0],user_id='user_reader',slot=1,
                request_id='midnight-request',is_paid=False,day='2026-09-11',expected_day='2026-09-10')
        self.assertEqual(caught.exception.detail['code'],'day_changed')
        self.assertEqual(self.users['user_reader']['coin'],30)

    def test_request_validation_and_legacy_get_cannot_spend(self):
        for slot in (0,4):
            with self.assertRaises(ValidationError): TarotDrawRequest(user_id='reader',slot=slot,request_id='valid-request-0001')
        with self.assertRaises(ValidationError): TarotDrawRequest(user_id='reader',slot=1,request_id='short')
        with self.assertRaises(HTTPException) as caught: get_daily_tarot(1,'reader',True)
        self.assertEqual(caught.exception.status_code,405)
        self.assertEqual(len(TAROT_DECK),22)
        for card in TAROT_DECK: self.assertTrue(card['description'])
