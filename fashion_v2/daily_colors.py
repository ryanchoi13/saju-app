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
    """오늘의 행운 색 두 개를 정하는 단 하나의 입구(2026-10-30). 화면(main.py)과 자동 검사가 같은 함수를 쓴다.

    2026-11-11 정오님 결정(3단계 원칙 B안). 결정 문서: 프로젝트 claude/decisions-2026-11-11-lucky-color-tiers.md
    - 오행을 좋음·무난·피함으로 나눈다(element_balance.element_tiers). 피함 오행은 색으로 내지 않는다.
    - 1칸 = 그날 천간의 오행. 좋음이나 무난이면 그대로, 피함이면 그것을 누르는 오행(제어) → 힘을 빼는 오행(설기)
      중 좋음인 것, 없으면 원국 순위의 첫 좋음.
    - 2칸 = 그날 지지의 지장간(정기 → 중기 → 여기)에서 피함이 아니고 1칸과 다른 첫 오행.
      없으면 정기 오행을 제어·설기하는 오행, 그래도 없으면 남은 좋음·무난 순위.
    - 통관 날: 통관 오행이 피함이 아니면 1칸을 통관 톤으로 바꾼다(피함이면 통관 처방을 쓰지 않는다).
    예전(11/5)에는 억부 기신을 모두 빼고 혼합 1·2순위를 썼다. 정오님 사주로 30일 중 28일이 금·화로 고정돼 바꿨다.
    """
    from app.engine.facts.hidden_stems import get_hidden_stems
    from app.engine.constants import GAN_WUXING
    from app.engine.services.element_balance import (
        CONTROLLED_BY, GENERATES, TIER_AVOID, TIER_GOOD, element_tiers, natal_balance)

    from app.engine.services.fashion_colors import build_fashion_color_basis

    basis = build_fashion_color_basis(core)
    if basis["source"] == "confirmed_natal_direction":
        # 코어가 용신 방향을 확정한 드문 경우는 예전(10/30) 그대로: 확정 오행 + 오늘 일간 오행
        today_element = core.timing.daily["pillar"]["stem_element"]
        tone_a, tone_b = element_tone_pair(basis["primary_element"], today_element, day_ordinal, salt)
        element_a, tongguan = basis["primary_element"], today_fortune.get("tongguan")
        if tongguan:
            tone_a, element_a = tongguan_tone(tongguan["element"]), tongguan["element"]
            if tone_b["id"] == tone_a["id"]:
                pool = ELEMENT_WEAR_TONES.get(today_element) or ELEMENT_WEAR_TONES["水"]
                tone_b = PALETTE[pool[(pool.index(tone_b["id"]) + 1) % len(pool)]] if tone_b["id"] in pool else tone_b
        return dict(tone_a=tone_a, element_a=element_a, tone_b=tone_b, element_b=today_element,
                    fashion_element=basis["primary_element"], today_element=today_element,
                    basis=basis, tongguan=tongguan)

    info = element_tiers(core)
    tiers = info["tiers"]
    ranking = natal_balance(core)["ranking"]
    good = [e for e in ranking if tiers[e] == TIER_GOOD]
    usable = [e for e in ranking if tiers[e] != TIER_AVOID]
    if not usable:   # 이론상 없지만 막아 둔다
        usable = list(ranking)

    def ok(e, taken=()):
        return tiers[e] != TIER_AVOID and e not in taken

    pillar = core.timing.daily["pillar"]
    stem, branch = pillar["ganji"][0], pillar["ganji"][1]

    first, first_rule = GAN_WUXING[stem], "stem"
    if not ok(first):
        for cand, rule in ((CONTROLLED_BY[first], "stem_control"), (GENERATES[first], "stem_drain")):
            if cand in good:
                first, first_rule = cand, rule
                break
        else:
            first, first_rule = (good or usable)[0], "natal_rank"

    second, second_rule = None, None
    hidden = get_hidden_stems(branch).stems
    for item in hidden:
        if ok(item.element, (first,)):
            second, second_rule = item.element, f"hidden_{getattr(item.role, 'value', item.role)}"
            break
    if second is None:
        main_el = hidden[0].element
        for cand, rule in ((CONTROLLED_BY[main_el], "branch_control"), (GENERATES[main_el], "branch_drain")):
            if ok(cand, (first,)):
                second, second_rule = cand, rule
                break
        else:
            rest = [e for e in usable if e != first] or [e for e in ranking if e != first]
            second, second_rule = rest[0], "natal_rank"

    tone_a, tone_b = element_tone_pair(first, second, day_ordinal, salt)
    element_a = first
    tongguan = today_fortune.get("tongguan")
    if tongguan and tiers.get(tongguan["element"]) == TIER_AVOID:
        tongguan = None
    if tongguan:
        tg = tongguan["element"]
        tone_a, element_a = tongguan_tone(tg), tg
        if second == tg:
            second, second_rule = first, "tongguan_shift"
            tone_b = element_tone_pair(first, first, day_ordinal, salt)[1]
        if tone_b["id"] == tone_a["id"]:
            pool = ELEMENT_WEAR_TONES.get(second) or ELEMENT_WEAR_TONES["水"]
            tone_b = PALETTE[pool[(pool.index(tone_b["id"]) + 1) % len(pool)]] if tone_b["id"] in pool else tone_b
    basis = dict(source="element_tiers_daily", primary_element=element_a, secondary_element=second,
                 tiers=tiers, rules=[first_rule if not tongguan else "tongguan", second_rule])
    return dict(tone_a=tone_a, element_a=element_a, tone_b=tone_b, element_b=second,
                fashion_element=element_a, today_element=second,
                basis=basis, tongguan=tongguan)
