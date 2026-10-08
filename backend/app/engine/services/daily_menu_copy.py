"""Tab 1 홈 '오늘 뭐 먹지?' 3모드 감성 큐레이션 카피와 모드 데이터.

모드: [외식·배달] / [10분 집밥] / [가벼운 한 끼(다이어트)]
- 메뉴 선택 계산은 daily_menu.py 가 한다. 이 파일은 (1) 모드별 후보 범위 데이터와 (2) 화면에 나가는 말만 가진다.
- 집필 헌칙: 의학 경고·질병 예방·효능 표현 금지, HR 금기어 금지. 오행은 '그날의 결에 어울리는 취향 제안'이라는
  상징 언어로만 쓴다. (칼로리 숫자는 화면에 싣지 않는다 — 내부 추정치다.)

QUICK_HOME_MENUS / HOME_ONLY_MENUS 는 '집에서 십 분 안에 차릴 수 있는가'에 대한 편집 판단이다.
daily_menu.MENU_POOL 에는 조리 시간 정보가 없어 사람이 골랐고, 이름이 풀에 실제로 있는지는 테스트가 확인한다.
"""
from __future__ import annotations

from app.engine.services.daily_copy import ELEMENT_KO, find_flagged, _pick  # noqa: F401

COPY_VERSION = "dalha-daily-menu-1"

MODES = (
    ("out", "외식·배달", ""),
    ("home", "10분 집밥", ""),
    ("light", "가벼운 한 끼", "다이어트"),
)
MODE_KEYS = tuple(k for k, _, _ in MODES)

# 10분 집밥 후보: 불 앞에 오래 서지 않고, 손질이 거의 없는 한 끼. (편집 판단 — 검토 필요)
QUICK_HOME_MENUS = frozenset({
    "간장계란밥", "계란볶음밥", "김치볶음밥", "햄볶음밥", "채소볶음밥",
    "비빔국수", "잔치국수", "들기름 막국수", "메밀 비빔국수",
    "라면", "짜파게티", "알리오 올리오", "두부김치", "두부채소볶음",
    "토마토 에그스크램블", "시금치오믈렛",
    "햄치즈 토스트", "햄에그 토스트", "계란프라이와 토스트", "삶은 계란과 토스트", "아보카도 토스트",
    "햄에그 샌드위치", "달걀샌드위치", "치즈샌드위치", "BLT 샌드위치",
    "연두부 채소샐러드", "닭가슴살 그린샐러드", "시저샐러드",
    "오트밀죽", "그래놀라 요거트", "과일 그래놀라 볼",
})
# 집에서만 어울리는 메뉴: 외식·배달 추천에서는 뺀다.
HOME_ONLY_MENUS = frozenset({
    "간장계란밥", "계란프라이와 토스트", "삶은 계란과 토스트", "라면", "짜파게티", "오트밀죽", "그래놀라 요거트",
})

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
MODE_CAPTION = {
    "out": "나가서 드셔도, 시켜 드셔도 좋아요. 마음 가는 쪽으로 골라 보세요.",
    "home": "냉장고 속 재료로 십 분이면 차려 낼 수 있어요. 집에서 편하게 즐겨 보세요.",
    "light": "든든함은 챙기고 부담은 덜어 낸 가벼운 한 끼예요. 천천히 즐겨 보세요.",
}
EMPTY_TEXT = "지금 시간에 어울리는 메뉴를 찾지 못했어요. 다른 모드를 눌러 보세요."
FOOTNOTE = "메뉴는 오늘의 기운과 계절, 시간대에 어울리는 취향 제안이에요."


def compose_mode_card(mode: str, element: str, menus: list[str], seed: int) -> dict:
    mode = mode if mode in MODE_KEYS else "out"
    key = element if element in ELEMENT_LINE else "土"
    label, sub = next((l, s) for k, l, s in MODES if k == mode)
    return dict(
        mode=mode, label=label, sub_label=sub, element=key, element_ko=ELEMENT_KO[key],
        headline=_pick(ELEMENT_LINE[key], seed, 6), caption=MODE_CAPTION[mode],
        menus=list(menus), available=bool(menus), empty_text="" if menus else EMPTY_TEXT,
    )
