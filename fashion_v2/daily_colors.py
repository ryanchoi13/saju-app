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
