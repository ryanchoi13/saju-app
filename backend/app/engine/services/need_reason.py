"""'필요한 기운' 바로 뒤에 붙는 한 줄 이유 (2026-11-16 정오님).

정오님 질문: 수·금이 없는데 왜 금·화가 필요하다고 나오나? → 필요한 기운은 '모자란 기운'이 아니라
일간의 균형(억부)으로 정한 값이다. 강하면 눌러 주고 풀어 주는 기운, 약하면 받쳐 주는 기운이 필요하고,
모자라도 일간을 더 키우는(강할 때) 또는 힘을 더 빼는(약할 때) 기운은 우선하지 않는다.
강약이 보류인 사람(궁통보감 조후로 정한 경우)은 이유를 붙이지 않는다.
"""
from __future__ import annotations

from app.engine.services.element_balance import (
    CONTROLLED_BY, CONTROLS, EOKBU_STRONG, EOKBU_WEAK, GENERATED_BY, GENERATES, composition,
)

NAME = {"木": "목(木)", "火": "화(火)", "土": "토(土)", "金": "금(金)", "水": "수(水)"}
EUN = {"木": "은", "火": "는", "土": "는", "金": "은", "水": "는"}
EUL = {"木": "을", "火": "를", "土": "를", "金": "을", "水": "를"}
DEFICIENT = 10     # health.DEFICIENT 와 같은 기준(%)


def need_reason(core, good: list[str]) -> str:
    if not good:
        return ""
    dm = core.natal_facts.pillars["day"].stem_element
    strength = str(core.synthesis.strength_state or "")
    if strength in EOKBU_STRONG:
        role = {GENERATES[dm]: "풀어 주고", CONTROLLED_BY[dm]: "눌러 주고", CONTROLS[dm]: "쓰게 해 주고"}
        state, skip_word = "단단한", "더 키우는"
        skipped = {GENERATED_BY[dm], dm}
    elif strength in EOKBU_WEAK:
        role = {GENERATED_BY[dm]: "받쳐 주고", dm: "곁에서 힘을 보태 주고"}
        state, skip_word = "약한", "힘을 더 빼는"
        skipped = {GENERATES[dm], CONTROLS[dm], CONTROLLED_BY[dm]}
    else:
        return ""
    parts = [f"{NAME[e]}{EUN[e]} {role[e]}" for e in good if e in role]
    if len(parts) != len(good):
        return ""
    text = f"{NAME[dm]} 기운이 {state} 편이라 " + " ".join(parts)
    text = text[:-1] + "서" if text.endswith("고") else text      # 마지막 '~주고' → '~줘서'
    text = (text[:-2] + "줘서") if text.endswith("주서") else text
    text += " 균형이 맞아요."
    comp = composition(core)
    lacking = [e for e in "木火土金水" if comp.get(e, 0) < DEFICIENT and e in skipped and e not in good]
    if lacking:
        e = lacking[0]
        tail = (f"{NAME[dm]}{EUL[dm]} 더 키우는 쪽" if strength in EOKBU_STRONG else "힘을 더 빼는 쪽")
        text += f" {NAME[e]}{EUN[e]} 모자라지만 {tail}이라 우선하지 않아요."
    return text
