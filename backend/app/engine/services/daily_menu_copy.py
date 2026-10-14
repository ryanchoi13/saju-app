"""Tab 1 홈 '오늘 뭐 먹지?' 카드의 끼니 데이터와 화면 문구.

2026-10-14 정오님: 외식·집밥·다이어트 구분을 없애고 아침·점심·저녁을 보여 준다.
끼니마다 두 개("이거나 이거"), 하루에 한 번 정해져 언제 다시 봐도 같다.
- 메뉴 선택 계산은 daily.py(_menu_curation)와 daily_menu.py 가 한다. 이 파일은 화면에 나가는 말만 가진다.
- 집필 헌칙: 의학 경고·질병 예방·효능 표현 금지, HR 금기어 금지. 오행은 '그날의 결에 어울리는 취향 제안'이라는
  상징 언어로만 쓴다. (칼로리 숫자는 화면에 싣지 않는다 — 내부 추정치다.)
"""
from __future__ import annotations

from app.engine.services.daily_copy import ELEMENT_KO, find_flagged, _pick  # noqa: F401

COPY_VERSION = "dalha-daily-menu-2"

# (끼니 키, 화면 이름, 고를 때 쓰는 기준 시각)
MEALS = (
    ("breakfast", "아침", 8),
    ("lunch", "점심", 12),
    ("dinner", "저녁", 19),
)
MEAL_KEYS = tuple(k for k, _, _ in MEALS)

ELEMENT_LINE = {
    "木": ("오늘은 목(木) 기운을 채워 보는 날, 싱그러운 초록빛이 어우러진 한 끼를 골랐어요.",
          "오늘은 새순처럼 싱그러운 목(木) 기운이 어울리는 날이라 산뜻한 메뉴를 모았어요."),
    "火": ("오늘은 화(火) 기운을 채워 보는 날, 따끈하고 향긋하게 온기가 도는 한 끼예요.",
          "오늘은 온기가 반가운 화(火)의 날이라 따뜻하고 감칠맛 도는 메뉴를 골랐어요."),
    "土": ("오늘은 토(土) 기운을 채워 보는 날, 포근하고 든든하게 감싸 주는 한 끼예요.",
          "오늘은 땅처럼 듬직한 토(土) 기운이 어울리는 날이라 푸근한 메뉴를 모았어요."),
    "金": ("오늘은 금(金) 기운을 채워 보는 날, 맑고 깔끔한 맛으로 마음을 정돈하는 한 끼예요.",
          "오늘은 담백하고 선명한 금(金) 기운이 어울리는 날이라 깔끔한 메뉴를 골랐어요."),
    "水": ("오늘은 수(水) 기운을 채워 보는 날, 촉촉하고 깊은 맛이 스며드는 한 끼예요.",
          "오늘은 잔잔하게 스며드는 수(水) 기운이 어울리는 날이라 깊은 맛의 메뉴를 골랐어요."),
}
CAPTION = "둘 중 마음 가는 쪽으로 골라 보세요."
EMPTY_TEXT = "이 끼니에 어울리는 메뉴를 찾지 못했어요. 다른 끼니를 눌러 보세요."
FOOTNOTE = "메뉴는 오늘의 기운과 계절에 어울리는 취향 제안이에요. 하루 동안 그대로예요."


def compose_meal_card(meal: str, element: str, menus: list[str], seed: int) -> dict:
    meal = meal if meal in MEAL_KEYS else "lunch"
    key = element if element in ELEMENT_LINE else "土"
    label = next(name for k, name, _ in MEALS if k == meal)
    return dict(
        mode=meal, label=label, sub_label="", element=key, element_ko=ELEMENT_KO[key],
        headline=_pick(ELEMENT_LINE[key], seed, 6), caption=CAPTION,
        menus=list(menus), available=bool(menus), empty_text="" if menus else EMPTY_TEXT,
    )
