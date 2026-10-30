"""오늘의 두 색(A·B)을 정하는 곳.

2026-10-13 정오님: "와다에 너무 얽매이지 말자" → 두 목표 오행에서 대표 착장색을 하나씩 고른다.
2026-10-28 정오님: 와다 배색 사전을 코드에서 완전히 뺀다. 색은 이 파일의 팔레트에서만 나온다.
"""
from fashion_v2.svg_recommendation import PALETTE

# 오행별 대표 착장색 (fashion_v2 팔레트 키). 튀는 색은 뒤 단계(연령·성별 규칙)가 소품·안 상의로 보낸다.
ELEMENT_WEAR_TONES = {
    "金": ("light_gray", "gray", "mid_gray", "ivory", "white"),
    "水": ("navy", "black", "sky", "denim"),
    "木": ("olive", "sage", "forest", "teal"),
    "火": ("burgundy", "plum", "coral", "rust", "red", "lavender", "pink"),   # 이웃한 날끼리 톤이 겹치지 않게 섞은 순서
    "土": ("beige", "camel", "brown", "butter"),
}

# 통관 오행 → 메인 옷에 쓸 가라앉은 톤 (fashion_v2 팔레트 키)
TONGGUAN_TONE = {"木": "olive", "水": "navy", "金": "mid_gray", "火": "burgundy", "土": "beige"}


def element_tone_pair(first: str, second: str, day: int, salt: int):
    """두 오행에서 하나씩. 날마다 두 색이 함께 바뀌도록 서로 다른 보폭으로 돈다(같은 오행이면 서로 다른 톤)."""
    a_pool = ELEMENT_WEAR_TONES.get(first) or ELEMENT_WEAR_TONES["金"]
    b_pool = ELEMENT_WEAR_TONES.get(second) or ELEMENT_WEAR_TONES["水"]
    a = a_pool[(day + salt) % len(a_pool)]
    b = b_pool[(day * 3 + salt // 7) % len(b_pool)]
    if b == a:
        b = b_pool[(b_pool.index(b) + 1) % len(b_pool)]
    return PALETTE[a], PALETTE[b]


def tongguan_tone(element: str):
    return PALETTE[TONGGUAN_TONE[element]]


def outfit_color(tone) -> dict:
    """코디 엔진(build_svg_catalog_contexts)에 넘기는 색."""
    return {"name": tone["id"], "name_ko": tone["name"], "hex": tone["hex"]}


def palette_color(tone) -> dict:
    """화면 색 칩·옷장 매칭에 쓰는 색."""
    return {**outfit_color(tone), "original_name": tone["name"], "standard_color": tone["name"]}


def all_daily_pairs():
    """앱이 실제로 낼 수 있는 모든 (A, B) 조합. 통관 날 A 교체까지 포함한다. 테스트·벤치마크용."""
    pairs = {}
    elements = list(ELEMENT_WEAR_TONES)
    for first in elements:
        for second in elements:
            for a in ELEMENT_WEAR_TONES[first]:
                for b in ELEMENT_WEAR_TONES[second]:
                    if a != b:
                        pairs[(a, b)] = None
    for a in TONGGUAN_TONE.values():
        for pool in ELEMENT_WEAR_TONES.values():
            for b in pool:
                pairs[(a, b)] = None
    return [(PALETTE[a], PALETTE[b]) for a, b in pairs]


def todays_lucky_tones(core, today_fortune, day_ordinal: int, salt: int) -> dict:
    """오늘의 행운 색 두 개를 정하는 단 하나의 입구(2026-10-30).

    화면(main.py)과 자동 검사(scripts/color_plan_report.py)가 같은 함수를 쓴다.
    1) 두 목표 오행: 원국 방향이 확정이면 그 오행 + 일간 오행, 보류면 오늘의 보완 오행 + 타고난 보완 오행
    2) 오행마다 대표 착장색 하나씩(element_tone_pair)
    3) 충 날이면 첫 색을 두 기운을 잇는 오행의 가라앉은 톤으로(통관)
    """
    from app.engine.services.fashion_colors import build_fashion_color_basis

    today_element = core.timing.daily["pillar"]["stem_element"]
    lucky_element = today_fortune["lucky_element"]
    basis = build_fashion_color_basis(core)
    fashion_element = basis["primary_element"]
    if basis["source"] != "confirmed_natal_direction":
        fashion_element = lucky_element
        natal_element = today_fortune["natal_balance_element"]
        today_element = natal_element if natal_element != lucky_element else today_element
        basis = {**basis, "primary_element": fashion_element, "secondary_element": today_element,
                 "source": "natal_balance_plus_daily"}
    tone_a, tone_b = element_tone_pair(fashion_element, today_element, day_ordinal, salt)
    tongguan = today_fortune.get("tongguan")
    element_a = fashion_element
    if tongguan:
        tone_a = tongguan_tone(tongguan["element"])
        element_a = tongguan["element"]
        if tone_b["id"] == tone_a["id"]:
            # 통관 톤이 두 번째 색과 같아지면 행운 색이 하나로 보인다(10/30 자동 검사에서 발견). 같은 오행의 다음 톤으로.
            pool = ELEMENT_WEAR_TONES.get(today_element) or ELEMENT_WEAR_TONES["水"]
            tone_b = PALETTE[pool[(pool.index(tone_b["id"]) + 1) % len(pool)]] if tone_b["id"] in pool else tone_b
    return dict(tone_a=tone_a, element_a=element_a, tone_b=tone_b, element_b=today_element,
                fashion_element=fashion_element, today_element=today_element,
                basis=basis, tongguan=tongguan)
