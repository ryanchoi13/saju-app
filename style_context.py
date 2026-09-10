"""Use existing Wada placement rules within the user's selected clothing context.

Color allowance scores are editorial clothing rules, not fortune scores.
The original daily A/B selection is preserved across all three contexts.
"""
from wada_color_rules import evaluate_duo
from wada_color_ko import get_wada_color_ko

TPO_LABELS = {'casual': '캐주얼', 'business_casual': '비즈니스 캐주얼', 'business_formal': '비즈니스 포멀'}
ITEM_LABELS = {'top':'상의', 'bottom':'바지', 'outer':'겉옷', 'shoes':'신발', 'bag':'가방',
               'shirt_knit_polo':'셔츠·니트·폴로', 'jacket':'재킷', 'belt':'벨트', 'watch':'시계',
               'suit':'상하의가 같은 색인 정장', 'shirt':'셔츠', 'tie':'넥타이',
               'bottom_skirt':'바지·스커트', 'dress':'원피스', 'blouse_knit':'블라우스·니트',
               'suit_jacket':'정장 재킷', 'blouse':'블라우스', 'scarf':'스카프', 'jewelry':'주얼리'}


def build_style_contexts(duo_no, gender, casual_palette):
    result = {}
    for tpo, label in TPO_LABELS.items():
        evaluation = evaluate_duo(duo_no, gender, tpo)
        colors, used, directions = [], set(), []
        for key in ('color_a', 'color_b'):
            entry = evaluation[key]
            # A conservative presentation gate on the existing allowance scale.
            # Try another clothing location before omitting this color from the outfit.
            slot = next((item for item, score in entry['ranked_items'] if score >= 60 and item not in used), None)
            color = {**get_wada_color_ko(entry['hex'], entry['name']), 'name':entry['name'], 'hex':entry['hex'],
                     'role':ITEM_LABELS[slot] if slot else '착장 적용 생략', 'item_type':slot}
            colors.append(color)
            if slot:
                used.add(slot)
                directions.append(f"{color['name_ko']} {ITEM_LABELS[slot]}")
        if tpo == 'casual':
            # Preserve the existing casual upper/lower assignment.
            palette = {**casual_palette, 'tpo':tpo, 'gender':gender, 'mood_tag':label}
        else:
            palette = {'top':colors[0], 'bottom':colors[1], 'point':None, 'mode':'harmony',
                       'tpo':tpo, 'gender':gender, 'style_mood':tpo, 'mood_tag':label,
                       'outfit_guidance':' · '.join(directions) or '두 색상을 억지로 착장에 적용하지 않아도 괜찮습니다.',
                       'mood_desc':'선택한 옷차림에 자연스럽게 사용할 수 있는 위치를 안내합니다.'}
        result[tpo] = palette
    return result
