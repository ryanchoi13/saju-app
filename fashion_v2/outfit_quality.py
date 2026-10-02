"""Whole-outfit gates precede daily-color coverage.

This bounded editorial policy is explicit and versioned. It does not promote
the sparse evidence archive's draft scores into measured population facts.
"""
from copy import deepcopy
import json
from pathlib import Path

POLICY = json.loads(Path(__file__).with_name('practical_policy.json').read_text())
VERSION = POLICY['version']


def item_realism(item, look, describe, palette):
    c = describe({'hex': item['hex']})
    key = next((k for k, v in palette.items() if v['hex'].upper() == c['hex']), None)
    cat, label = item['category'], item['label']
    if cat == 'shoes' and label == '운동화':
        if look['gender'] == 'male' and (look.get('age') or 0) >= 40:
            return 4 if key in POLICY['mature_male_default_sneakers'] else 3
        return 4 if key in {'white', 'ivory', 'gray', 'light_gray', 'black'} else 3
    if cat in {'tie', 'bag', 'accessory'}:
        return 4
    if key in POLICY['supporting_colors']:
        return 4
    if c['family'] in {'white', 'gray', 'black'}:
        return 4
    if c['family'] == 'blue' and c['lightness'] < .34 and c['saturation'] < .72:
        return 4
    if c['family'] == 'brown' and c['saturation'] < .55:
        return 4
    if cat in {'top', 'mid'} and key in POLICY['soft_top_colors']:
        return 4
    if cat == 'shoes' and label != '운동화':
        return 4 if c['saturation'] < .45 else 3
    if label in {'패딩', '가디건'} and key in POLICY['soft_top_colors']:
        return 4
    if look['gender'] == 'female' and c['saturation'] < .50:
        return 4
    if (look['gender'] == 'male' and (look.get('age') or 0) >= 40
            and label == '블루종' and c['family'] in {'red', 'yellow', 'orange'}):
        return 2
    return 3


def whole_outfit_quality(items, look, describe, palette, coordination, color_count):
    ratings = [item_realism(i, look, describe, palette) for i in items]
    supporting = {palette[k]['hex'].upper() for k in POLICY['supporting_colors']}
    accents = []
    for item in items:
        if item['category'] not in {'top', 'bottom', 'dress', 'outer', 'coat', 'mid'} or item.get('wear_mode') == 'carry':
            continue
        c = describe({'hex': item['hex']})
        if c['hex'] not in supporting and c['family'] not in {'white', 'gray', 'black'}:
            accents.append(c['family'])
    conflicts = max(0, len(set(accents)) - 1)
    reasons = []
    if conflicts:
        reasons.append('서로 다른 포인트색의 큰 면적 사용을 줄여 비교')
    # B03 was conditional approval of the inner/bottom pair, not of a black
    # outer added on top. Preserve that exact scope in this starting policy.
    if (look['gender'] == 'male' and 40 <= (look.get('age') or 0) < 60
            and look.get('calendar_season', look['season']) == 'autumn' and look['tpo'] == 'casual'):
        by_slot = {i['category']: i['hex'].upper() for i in items}
        if (by_slot.get('outer') == palette['black']['hex'] and by_slot.get('bottom') == palette['beige']['hex']
                and by_slot.get('top') in {palette['pink']['hex'], palette['pale_pink']['hex']}):
            conflicts += 1
            reasons.append('핑크·베이지에 검정 겉옷을 더한 전체 조합은 추가 검토 대상')
    reviewed = bool(look.get('review_preference') or look.get('color_targets') or look.get('footwear_color_locked'))
    rank = (4 if reviewed else min(ratings), 0 if reviewed else -conflicts,
            coordination['score_adjustment'], -max(0, color_count-4))
    return dict(rank=rank, item_scores=ratings, reasons=reasons,
                basis=POLICY['basis'], policy_version=VERSION,
                aesthetic_approval=False, reviewed_exception=reviewed)


def base_outfit_options(look, palette, garment_options):
    """Prepare complete neutral outfit alternatives before considering A/B."""
    for option in garment_options(look, palette):
        yield option
        if look.get('review_preference') or look.get('color_targets') or look.get('footwear_color_locked'):
            continue
        if look['tpo'] != 'casual' or (look.get('age') or 0) < 40 or look['gender'] != 'male':
            continue
        if not any(i['label'] == '면바지' for i in option['items']):
            continue
        # Same garments/materials/weather modes; compare a light neutral outer
        # with the existing base. This is not a windbreaker substitution.
        outer = next((n for n, i in enumerate(option['items']) if i['category'] in {'outer', 'carry_outer'} and i['label'] == '블루종'), None)
        if outer is not None:
            alternate = deepcopy(option)
            c = palette['light_gray']
            alternate['items'][outer].update(base_color='light_gray', color_name=c['name'], hex=c['hex'])
            alternate.setdefault('selection_changes', []).append(dict(reason='검토 의견에 따라 밝은 회색 겉옷의 기본 배색도 비교'))
            yield alternate
