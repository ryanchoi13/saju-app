"""오늘의 두 색(A·B)을 정하는 곳.

2026-10-13 정오님: "와다에 너무 얽매이지 말자" → 두 목표 오행에서 대표 착장색을 하나씩 고른다.
2026-10-28 정오님: 와다 배색 사전을 코드에서 완전히 뺀다. 색은 이 파일의 팔레트에서만 나온다.
"""
import colorsys

from fashion_v2.svg_recommendation import PALETTE

STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"

# 오행별 대표 착장색 (fashion_v2 팔레트 키). 튀는 색은 뒤 단계(연령·성별 규칙)가 소품·안 상의로 보낸다.
ELEMENT_WEAR_TONES = {
    "金": ("light_gray", "gray", "mid_gray", "ivory", "white", "charcoal"),
    "水": ("navy", "black", "sky", "denim"),
    "木": ("olive", "sage", "forest", "teal"),
    "火": ("burgundy", "plum", "coral", "rust", "red", "lavender", "pink"),   # 이웃한 날끼리 톤이 겹치지 않게 섞은 순서
    "土": ("beige", "camel", "brown", "butter", "mustard", "terracotta", "khaki"),
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


def _by_lightness(pool):
    """팔레트 키를 밝은 쪽 → 어두운 쪽 순으로(HLS 명도, 같으면 이름순)."""
    def light(key):
        h = PALETTE[key]["hex"].lstrip("#")
        r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
        return -colorsys.rgb_to_hls(r, g, b)[1], key
    return sorted(pool, key=light)


def ganji_index(ganji: str):
    """60갑자 번호(甲子=0). 천간·지지 조합 값. 몰라서 못 구하면 None."""
    if len(ganji) != 2 or ganji[0] not in STEMS or ganji[1] not in BRANCHES:
        return None
    s, b = STEMS.index(ganji[0]), BRANCHES.index(ganji[1])
    return next((n for n in range(60) if n % 10 == s and n % 12 == b), None)


def ganji_tone_pair(first: str, second: str, ganji: str, salt: int = 0):
    """일진(천간·지지) 값으로 두 톤을 정한다. 날짜 번호 순환 대신.

    60갑자는 하루마다 양·음이 번갈아 온다(甲子 양, 乙丑 음, ...). 이 성질을 이용한다.
    - 1칸(A): 양의 날은 그 오행 톤 중 밝은 절반, 음의 날은 어두운 절반에서 고른다.
    - 2칸(B): 항상 A의 반대쪽 절반에서 고른다.
    그래서 어느 칸이든 이틀 연속 같은 오행이 나와도 밝은 톤 ↔ 어두운 톤이 교차한다.
    절반 안에서는 지지 번호를 두 칸씩 밀며 돌려 같은 절반이 다시 올 때(이틀 뒤) 다른 톤이 된다.
    salt(사람마다 다른 수, 생년월일에서)만큼 절반 안의 시작 칸을 밀어, 같은 날 같은 오행이어도
    사람마다 톤이 갈린다(2026-11-24: salt 없이 같은 날 두 사람 두 색까지 같음 60% → 되돌림).
    밝음·어두움 절반을 고르는 규칙은 그대로라 연속 날 명도 교차는 유지된다.
    """
    n = ganji_index(ganji)
    if n is None:
        return None
    a_sorted = _by_lightness(ELEMENT_WEAR_TONES.get(first) or ELEMENT_WEAR_TONES["金"])
    b_sorted = _by_lightness(ELEMENT_WEAR_TONES.get(second) or ELEMENT_WEAR_TONES["水"])

    def halves(pool):
        k = (len(pool) + 1) // 2
        return pool[:k], pool[k:] or pool[:k]

    a_light, a_dark = halves(a_sorted)
    b_light, b_dark = halves(b_sorted)
    yang = n % 2 == 0
    a_half, b_half = (a_light, b_dark) if yang else (a_dark, b_light)
    a = a_half[((n % 12) // 2 + salt) % len(a_half)]
    b = b_half[((n % 10) // 2 + 1 + salt // 7) % len(b_half)]
    if b == a:
        b = b_half[(b_half.index(b) + 1) % len(b_half)]
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
    from app.engine.services.element_balance import (
        CONTROLLED_BY, GENERATES, TIER_AVOID, element_tiers, natal_balance, tier_first_element)

    from app.engine.services.fashion_colors import build_fashion_color_basis

    basis = build_fashion_color_basis(core)
    if basis["source"] == "confirmed_natal_direction":
        # 코어가 용신 방향을 확정한 드문 경우는 예전(10/30) 그대로: 확정 오행 + 오늘 일간 오행
        today_element = core.timing.daily["pillar"]["stem_element"]
        tone_a, tone_b = (ganji_tone_pair(basis["primary_element"], today_element, core.timing.daily["pillar"]["ganji"], salt)
                          or element_tone_pair(basis["primary_element"], today_element, day_ordinal, salt))
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
    usable = [e for e in ranking if tiers[e] != TIER_AVOID] or list(ranking)

    def ok(e, taken=()):
        return tiers[e] != TIER_AVOID and e not in taken

    branch = core.timing.daily["pillar"]["ganji"][1]
    first, first_rule = tier_first_element(core, tiers)   # 행운 카드·부적과 같은 함수(11/12)

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

    tone_a, tone_b = (ganji_tone_pair(first, second, core.timing.daily["pillar"]["ganji"], salt)
                      or element_tone_pair(first, second, day_ordinal, salt))
    element_a = first
    tongguan = today_fortune.get("tongguan")
    if tongguan and tiers.get(tongguan["element"]) == TIER_AVOID:
        tongguan = None
    if tongguan:
        tg = tongguan["element"]
        tone_a, element_a = tongguan_tone(tg), tg
        if second == tg:
            second, second_rule = first, "tongguan_shift"
            tone_b = (ganji_tone_pair(first, first, core.timing.daily["pillar"]["ganji"], salt)
                      or element_tone_pair(first, first, day_ordinal, salt))[1]
        if tone_b["id"] == tone_a["id"]:
            pool = ELEMENT_WEAR_TONES.get(second) or ELEMENT_WEAR_TONES["水"]
            tone_b = PALETTE[pool[(pool.index(tone_b["id"]) + 1) % len(pool)]] if tone_b["id"] in pool else tone_b
    basis = dict(source="element_tiers_daily", primary_element=element_a, secondary_element=second,
                 tiers=tiers, rules=[first_rule if not tongguan else "tongguan", second_rule])
    return dict(tone_a=tone_a, element_a=element_a, tone_b=tone_b, element_b=second,
                fashion_element=element_a, today_element=second,
                basis=basis, tongguan=tongguan)


_EL_LABEL = {"木": "목(木)", "火": "화(火)", "土": "토(土)", "金": "금(金)", "水": "수(水)"}


# 뜻은 같고 어조만 다른 연결 문구. 날짜 번호로 돌려서 이틀 연속 같은 문장이 나오지 않게 한다(2026-11-20).
CONTINUATION_TEMPLATES = (
    "어제에 이어 오늘도 {names}의 기운을 보충하는 날이에요.",
    "어제처럼 오늘도 {names}의 기운이 필요한 날이에요.",
    "{names}의 기운을 오늘도 한 번 더 채워 주세요.",
    "어제 채운 {names}의 기운을 오늘도 이어 가요.",
)


def continuation_caption(prev: dict | None, today: dict, day_ordinal: int = 0) -> str:
    """전날과 같은 칸(1칸끼리·2칸끼리)의 오행이 같으면 추천 사유 맨 앞에 붙일 연결 문구. 아니면 빈 문자열."""
    if not prev:
        return ""
    same = []
    for slot in ("element_a", "element_b"):
        e = today.get(slot)
        if e and e == prev.get(slot) and e not in same:
            same.append(e)
    if not same:
        return ""
    names = "·".join(_EL_LABEL.get(e, e) for e in same)
    # n + n//4: 이틀 연속 같은 문장이 나오지 않으면서(차이가 1 또는 2) 4가지가 고르게 돌아간다. n % 4만 쓰면 쏠린다.
    return CONTINUATION_TEMPLATES[(day_ordinal + day_ordinal // 4) % len(CONTINUATION_TEMPLATES)].format(names=names)
