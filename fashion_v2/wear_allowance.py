"""색이 어느 옷 자리에 자연스럽게 들어가는지 0~100 허용 점수.

운세 점수가 아니라 착장 편집 규칙이다. 2026-10-28 와다 배색 사전을 걷어 내면서
색 정보(계열·명도·채도)를 사전 조회 대신 HEX에서 직접 계산하도록 옮겼다.
주머니 행커치프는 한국 사용자에게 맞지 않아 뺀다. 남성 포멀 수트는 상하 한 색으로만 본다.
"""
import colorsys

from fashion_v2.svg_recommendation import PALETTE

BASE_ITEM_SCORES = {'male': {'casual': {'top': 85, 'bottom': 78, 'outer': 75, 'shoes': 50, 'bag': 45}, 'business_casual': {'shirt_knit_polo': 82, 'bottom': 72, 'jacket': 68, 'shoes': 38, 'belt': 28, 'watch': 25}, 'business_formal': {'suit': 35, 'shirt': 38, 'tie': 78, 'shoes': 25, 'belt': 22, 'watch': 22}}, 'female': {'casual': {'top': 88, 'bottom_skirt': 82, 'dress': 82, 'outer': 76, 'shoes': 58, 'bag': 58}, 'business_casual': {'blouse_knit': 84, 'bottom_skirt': 76, 'jacket': 74, 'dress': 76, 'shoes': 52, 'bag': 56}, 'business_formal': {'suit_jacket': 62, 'bottom_skirt': 58, 'dress': 66, 'blouse': 72, 'scarf': 82, 'shoes': 42, 'bag': 48, 'jewelry': 30}}}

# 팔레트 색의 계열(점수 규칙에서 쓰는 이름). 무채색·네이비·브라운·올리브는 규칙상 '기본색'으로 본다.
_FAMILY_BY_ID = {
    'white': 'white', 'ivory': 'white', 'gray': 'gray', 'light_gray': 'gray',
    'mid_gray': 'charcoal', 'charcoal': 'charcoal', 'black': 'black', 'navy': 'navy',
    'olive': 'olive', 'pink': 'pink', 'pale_pink': 'pink', 'beige': 'brown', 'camel': 'brown',
    'brown': 'brown', 'rust': 'brown',
}
_FAMILY_BY_PALETTE_FAMILY = {'earth': 'brown'}


def color_meta(hex_value: str) -> dict:
    hx = hex_value.upper()
    r, g, b = (int(hx[i:i + 2], 16) / 255 for i in (1, 3, 5))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    known = next((p for p in PALETTE.values() if p['hex'].upper() == hx), None)
    if known:
        fam = _FAMILY_BY_ID.get(known['id']) or _FAMILY_BY_PALETTE_FAMILY.get(known['family'], known['family'])
    elif s < .10:
        fam = 'white' if l > .85 else 'black' if l < .16 else 'charcoal' if l < .35 else 'gray'
    else:
        fam = ('red' if h < .055 or h > .94 else 'orange' if h < .12 else 'yellow' if h < .19 else
               'green' if h < .44 else 'teal' if h < .53 else 'navy' if h < .72 and l < .25 else
               'blue' if h < .72 else 'purple')
    return {'hex': hx, 'hue_family': fam, 'lightness': l * 100, 'saturation': s * 100}


def _clamp(v):
    return max(0, min(100, int(round(v))))


def score_color_for_item(color, gender, tpo, item):
    """0..100 허용 점수. color 는 HEX 문자열이나 color_meta() 결과."""
    if isinstance(color, str):
        color = color_meta(color)

    fam = color["hue_family"]
    light = color["lightness"]
    sat = color["saturation"]
    score = BASE_ITEM_SCORES[gender][tpo][item]

    neutral = fam in {"white", "black", "gray", "charcoal", "navy", "brown", "olive"}
    pastel = light >= 72 and sat <= 55
    vivid = sat >= 65

    # CASUAL: broad freedom; vivid colors are welcome on tops, less automatic on bottoms.
    if tpo == "casual":
        if item in {"top", "dress"} and vivid:
            score += 8
        if item in {"bottom", "bottom_skirt"} and vivid:
            score -= 15
        if neutral:
            score += 6

    # BUSINESS CASUAL: wide, but calmer than casual.
    elif tpo == "business_casual":
        if neutral or pastel:
            score += 10
        if vivid:
            score -= 18
        if item in {"shoes", "belt"} and fam not in {"black", "brown", "navy", "charcoal", "gray"}:
            score -= 35

    # BUSINESS FORMAL: gender-specific rules.
    elif gender == "male":
        if item == "suit":
            # Matching suit colors: navy/charcoal/gray/black dominate.
            if fam in {"navy", "charcoal"}:
                score = 96
            elif fam == "gray":
                score = 88 if light < 72 else 66
            elif fam == "black":
                score = 82
            elif fam == "blue" and light < 45 and sat < 70:
                score = 68
            else:
                score = 8 if vivid else 18

        elif item == "shirt":
            if fam == "white":
                score = 100
            elif fam == "blue" and light >= 70:
                score = 96
            elif fam in {"pink", "purple", "green", "yellow"} and pastel:
                score = 62
            elif pastel:
                score = 52
            else:
                score = 12 if vivid else 28

        elif item == "tie":
            # Tie is the main color outlet in male formalwear.
            score = 88
            if fam in {"red", "navy", "blue", "purple", "pink", "green", "gold", "orange"}:
                score += 6
            if light >= 88:
                score -= 18
            if sat >= 90 and light >= 55:
                score -= 12

        elif item in {"shoes", "belt"}:
            if fam in {"black", "brown"}:
                score = 92
            elif fam in {"red", "purple"} and light < 38 and sat < 70:  # burgundy-like
                score = 68
            else:
                score = 8

        elif item == "watch":
            score = 65 if fam in {"black", "brown", "gray", "charcoal", "white"} else 20

    else:  # female business_formal
        # Women have a wider formal color range, but neutrals remain the safer default.
        if item in {"suit_jacket", "bottom_skirt", "dress"}:
            if neutral:
                score += 24
            elif pastel:
                score += 12
            elif vivid:
                score -= 8   # allowed, but not the default for unknown workplace/formality
            if item == "bottom_skirt" and vivid:
                score -= 8

        elif item == "blouse":
            if fam in {"white"}:
                score = 98
            elif pastel:
                score = 90
            elif vivid:
                score = 58
            else:
                score = 78

        elif item == "scarf":
            score = 94
            if light >= 92:
                score -= 10

        elif item in {"shoes", "bag"}:
            if neutral:
                score += 25
            elif vivid:
                score -= 12

        elif item == "jewelry":
            # Jewelry is primarily a material/metal axis, not a color outlet.
            score = 18 if not neutral else 35

    return _clamp(score)


def ranked_items_for_color(hex_value, gender, tpo):
    """한 색이 가장 자연스럽게 들어가는 자리부터."""
    meta = color_meta(hex_value)
    ranked = [(item, score_color_for_item(meta, gender, tpo, item)) for item in BASE_ITEM_SCORES[gender][tpo]]
    return sorted(ranked, key=lambda x: x[1], reverse=True)
