"""Tarot content and draw handling for the app's existing session coin wallet."""
from copy import deepcopy
from datetime import datetime, timezone, timedelta
from threading import RLock
import tarot_store

PRICE = 10
LOCK = RLock()
SESSIONS = {}

# Artwork descriptions paraphrase the original Rider–Waite–Smith symbolism.
# References: docs/tarot-talisman-polish.md.
DESCRIPTIONS = {
    "0. THE FOOL (바보)": "0번 '바보'는 작은 보따리를 메고 여행을 떠나는 인물의 카드입니다. 아직 정해지지 않은 가능성과 새로운 경험을 향한 마음을 담고 있습니다.",
    "I. THE MAGICIAN (마법사)": "1번 '마법사'는 네 가지 도구를 앞에 두고 한 손은 하늘, 다른 손은 땅을 가리킵니다. 생각과 재능을 실제 행동으로 옮기는 힘을 상징합니다.",
}


class DrawError(ValueError):
    def __init__(self, status, code, message, balance=None):
        self.status = status
        self.detail = {"code": code, "message": message, "cost": PRICE}
        if balance is not None:
            self.detail["new_balance"] = balance


def day_key():
    return datetime.now(timezone(timedelta(hours=9))).date().isoformat()


def get_state(user_id, day=None):
    today = day or day_key()
    try:
        receipts = tarot_store.read(user_id,today)
    except tarot_store.StorageUnavailable:
        return {'day':today,'available':False,'message':'오늘 뽑은 카드를 불러오지 못했습니다. 다시 시도해 주세요.'}
    cards = sorted((deepcopy(r['result']) for r in receipts.values()),key=lambda r:r['slot'])
    return {'day':today,'available':True,'cards':cards,'count':len(cards),'limit':3}


def draw(users, deck, choose, *, user_id, slot, request_id, is_paid, day=None, expected_day=None):
    """One free card and up to two existing-price paid cards, all distinct.

    Receipts are durable; the app's existing coin wallet contract is preserved.
    """
    today = day or day_key()
    if expected_day and expected_day != today:
        raise DrawError(409,'day_changed','날짜가 바뀌었습니다. 오늘의 카드를 다시 골라 주세요.')
    with LOCK:
        user = users.get(user_id)
        if user is None:
            raise DrawError(401, "login_required", "로그인 상태를 확인해 주세요.")
        with tarot_store.locked(user_id,today) as receipts:
            if request_id in receipts:
                saved = receipts[request_id]
                if saved['slot'] != slot or saved['is_paid'] != is_paid:
                    raise DrawError(409,'request_conflict','선택한 카드의 요청을 다시 확인해 주세요.')
                return {**deepcopy(saved['result']),'new_balance':user['coin']}
            same_slot = next((r for r in receipts.values() if r['slot']==slot),None)
            if same_slot:
                return {**deepcopy(same_slot['result']),'new_balance':user['coin'],'reused':True}
            if len(receipts) >= 3:
                raise DrawError(409,'daily_limit','오늘의 세 장을 모두 뽑았습니다.',user['coin'])
            if receipts and not is_paid:
                raise DrawError(409,'payment_required','오늘의 무료 카드는 이미 확인하셨어요. 한 장 더 뽑으려면 10 복채가 필요해요.',user['coin'])
            cost = PRICE if receipts else 0
            if user['coin'] < cost:
                raise DrawError(402,'insufficient_coins','한 장 더 뽑으려면 10 복채가 필요해요.',user['coin'])
            seen = {r['result']['card']['name'] for r in receipts.values()}
            candidates = [c for c in deck if c['name'] not in seen]
            if not candidates:
                raise DrawError(503,'deck_unavailable','새 카드를 준비하지 못했습니다. 잠시 후 다시 시도해 주세요.')
            card = deepcopy(choose(candidates))
            card['description'] = card.get('description') or DESCRIPTIONS.get(card['name'],'')
            result = {'card':card,'cost':cost,'new_balance':user['coin']-cost,
                      'request_id':request_id,'day':today,'slot':slot,'count':len(receipts)+1,'limit':3}
            receipts[request_id] = {'slot':slot,'is_paid':is_paid,'result':deepcopy(result)}
        # Commit the receipt before acknowledging success or mutating session coins.
        user["coin"] = result["new_balance"]
        return result
