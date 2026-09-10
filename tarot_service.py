"""Tarot content and draw handling for the app's existing session coin wallet."""
from copy import deepcopy
from datetime import datetime, timezone, timedelta
from threading import RLock

PRICE = 10
LOCK = RLock()
SESSIONS = {}

# Artwork descriptions paraphrase the original Rider–Waite–Smith symbolism.
# References: docs/tarot-talisman-polish.md.
DESCRIPTIONS = {
    "0. THE FOOL (바보)": "0번 '바보'는 작은 보따리를 메고 여행을 떠나는 인물의 카드입니다. 아직 정해지지 않은 가능성과 새로운 경험을 향한 마음을 담고 있습니다.",
    "I. THE MAGICIAN (마법사)": "1번 '마법사'는 네 가지 도구를 앞에 두고 한 손은 하늘, 다른 손은 땅을 가리킵니다. 생각과 재능을 실제 행동으로 옮기는 힘을 상징합니다.",
}


class DrawError(Exception):
    def __init__(self, status, code, message, balance=None):
        self.status = status
        self.detail = {"code": code, "message": message, "cost": PRICE}
        if balance is not None:
            self.detail["new_balance"] = balance


def day_key():
    return datetime.now(timezone(timedelta(hours=9))).date().isoformat()


def draw(users, deck, choose, *, user_id, slot, request_id, is_paid, day=None):
    """Serialize a draw and return the server balance; retries reuse the receipt.

    Like the existing wallet, receipts are scoped to the running app process.
    This does not implement a payment gateway or persistent wallet migration.
    """
    today = day or day_key()
    with LOCK:
        user = users.get(user_id)
        if user is None:
            raise DrawError(401, "login_required", "로그인 상태를 확인해 주세요.")
        state = SESSIONS.get(user_id)
        if not state or state["day"] != today:
            state = SESSIONS[user_id] = {"day": today, "receipts": {}, "last_name": None}
        if request_id in state["receipts"]:
            saved = state["receipts"][request_id]
            if saved["slot"] != slot or saved["is_paid"] != is_paid:
                raise DrawError(409, "request_conflict", "선택한 카드의 요청을 다시 확인해 주세요.")
            return {**deepcopy(saved["result"]), "new_balance": user["coin"]}
        if state["receipts"] and not is_paid:
            raise DrawError(409, "payment_required", "오늘의 무료 카드는 이미 확인하셨어요. 한 장 더 뽑으려면 10 복채가 필요해요.", user["coin"])
        cost = PRICE if is_paid else 0
        if user["coin"] < cost:
            raise DrawError(402, "insufficient_coins", "한 장 더 뽑으려면 10 복채가 필요해요.", user["coin"])
        candidates = [c for c in deck if c["name"] != state["last_name"]] or deck
        card = deepcopy(choose(candidates))
        card["description"] = DESCRIPTIONS.get(card["name"], "")
        # Card creation must succeed before spending coins.
        result = {"card": card, "cost": cost, "new_balance": user["coin"] - cost,
                  "request_id": request_id, "day": today, "slot": slot}
        state["receipts"][request_id] = {"slot": slot, "is_paid": is_paid, "result": deepcopy(result)}
        state["last_name"] = card["name"]
        user["coin"] = result["new_balance"]
        return result
