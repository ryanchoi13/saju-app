"""Apply daily A/B colors after a complete outfit has been selected.

The algorithm prefers wearable area, not a fixed A=large/B=small split. A is
the tie-break priority; B may become the main garment color when A only fits a
smaller location. Unused colors remain available to the owned-wardrobe matcher
and finally to the palette UI.
"""

from copy import deepcopy

from wada_color_rules import WADA_COLORS, score_color_for_item


BASE_COLORS = {
    'beige': ('베이지', '#C4B294'), 'black': ('블랙', '#252629'),
    'brown': ('브라운', '#705443'), 'burgundy': ('버건디', '#7F2638'),
    'burgundy_navy': ('버건디·네이비', '#713247'),
    'camel': ('카멜', '#B28761'), 'charcoal': ('차콜', '#44474D'),
    'cream': ('크림', '#E8DFC8'), 'dark_brown': ('다크 브라운', '#4B352B'),
    'dark_denim': ('진청', '#294864'), 'denim_blue': ('데님 블루', '#466889'),
    'dusty_blue': ('더스티 블루', '#839BAE'), 'gray': ('그레이', '#85888D'),
    'ivory': ('아이보리', '#E8E0CF'), 'ivory_navy': ('아이보리·네이비', '#D6D1C4'),
    'light_blue': ('라이트 블루', '#A9C5D8'), 'light_gray': ('라이트 그레이', '#B6BAC1'),
    'navy': ('네이비', '#26354A'), 'navy_burgundy': ('네이비·버건디', '#343747'),
    'olive': ('올리브', '#787E62'), 'soft_pink': ('소프트 핑크', '#D8B4B8'),
    'white': ('화이트', '#F5F4EF'),
}

# A nearby wearable shade is allowed without pretending it is the exact Wada
# color. The original color remains visible in the palette.
RELATED_SHADES = {
    'red': ('버건디', '#7F2638'), 'orange': ('러스트 브라운', '#8A4F35'),
    'gold': ('머스터드', '#A78335'), 'yellow': ('모스 올리브', '#77764B'),
    'olive': ('올리브', '#787E62'), 'green': ('다크 그린', '#355F4B'),
    'teal': ('딥 틸', '#285D61'), 'blue': ('네이비', '#26354A'),
    'navy': ('네이비', '#26354A'), 'violet': ('딥 플럼', '#51435F'),
    'purple': ('딥 플럼', '#5B3D58'), 'pink': ('더스티 핑크', '#B67C87'),
    'brown': ('브라운', '#705443'), 'gray': ('그레이', '#85888D'),
    'charcoal': ('차콜', '#44474D'), 'black': ('블랙', '#252629'),
    'white': ('아이보리', '#E8E0CF'),
}

FORMAL_SUIT_SHADES = {
    'blue': ('네이비', '#26354A'), 'navy': ('네이비', '#26354A'),
    'teal': ('네이비', '#26354A'), 'gray': ('그레이', '#85888D'),
    'charcoal': ('차콜', '#44474D'), 'black': ('차콜', '#44474D'),
}

FORMAL_SHIRT_SHADES = {
    'white': ('화이트', '#F5F4EF'), 'blue': ('라이트 블루', '#A9C5D8'),
    'navy': ('라이트 블루', '#A9C5D8'), 'teal': ('라이트 블루', '#A9C5D8'),
    'red': ('페일 핑크', '#DEC1C4'), 'pink': ('페일 핑크', '#DEC1C4'),
    'purple': ('페일 핑크', '#D8C4D2'), 'violet': ('페일 라벤더', '#D1C8D9'),
    'gray': ('라이트 그레이', '#D2D3D5'), 'charcoal': ('라이트 그레이', '#D2D3D5'),
    'black': ('라이트 그레이', '#D2D3D5'),
}

AREA = {'large': 3, 'medium': 2, 'small': 1}


def _meta(color):
    hx = color['hex'].lower()
    return WADA_COLORS[hx]


def _display(color):
    return (color.get('name_ko') or color.get('name') or '추천색', color['hex'])


def _rule_slot(template, item):
    category = item['category']
    gender, tpo = template['gender'], template['tpo']
    if tpo == 'casual':
        return {'top':'top', 'mid':'top', 'outer':'outer', 'coat':'outer',
                'bottom':'bottom_skirt' if gender == 'female' else 'bottom',
                'dress':'dress', 'shoes':'shoes'}.get(category)
    if tpo == 'business_casual':
        return {'top':'blouse_knit' if gender == 'female' else 'shirt_knit_polo',
                'mid':'blouse_knit' if gender == 'female' else 'shirt_knit_polo',
                'outer':'jacket', 'coat':'jacket',
                'bottom':'bottom_skirt' if gender == 'female' else 'bottom',
                'dress':'dress', 'shoes':'shoes'}.get(category)
    return {'top':'blouse' if gender == 'female' else 'shirt',
            'bottom':'bottom_skirt' if gender == 'female' else None,
            'dress':'dress' if gender == 'female' else None,
            'outer':'suit_jacket' if gender == 'female' else None,
            'tie':'scarf' if gender == 'female' else 'tie',
            'shoes':'shoes'}.get(category)


def _area_for(template, item):
    category = item['category']
    if category in {'shoes', 'tie', 'leg_layer'}:
        return 'small'
    if template['tpo'] == 'business_formal' and category == 'top':
        return 'medium'
    return 'large'


def _related_variant(color, template, slot, area):
    family = _meta(color)['hue_family']
    if template['tpo'] == 'business_formal' and slot in {'shirt', 'blouse'}:
        return FORMAL_SHIRT_SHADES.get(family)
    if area == 'large':
        return RELATED_SHADES.get(family)
    return None


def _candidate(template, color, indexes, slot, area, order):
    score = score_color_for_item(color['hex'], template['gender'], template['tpo'], slot)
    threshold = 70 if area == 'large' else (60 if area == 'medium' else 55)
    shade, relation = _display(color), 'exact'
    if score < threshold:
        shade = _related_variant(color, template, slot, area)
        relation = 'similar'
        if shade is None:
            return None
        score = threshold
    # Vivid/non-neutral color never recolors a man's trousers. A related shade
    # is also limited to the established practical bottom range.
    if template['gender'] == 'male' and slot == 'bottom':
        family = _meta(color)['hue_family']
        if family not in {'black', 'navy', 'blue', 'gray', 'charcoal', 'brown', 'white'}:
            return None
        if shade[0] not in {'블랙', '네이비', '그레이', '차콜', '브라운', '아이보리'}:
            return None
    return {'indexes': tuple(indexes), 'use_key': tuple(indexes), 'slot': slot,
            'area': area, 'area_rank': AREA[area], 'score': score,
            'name': shade[0], 'hex': shade[1], 'relation': relation,
            'order': order}


def _candidates(template, color):
    items = template['items']
    result, grouped = [], set()
    suit_groups = {}
    for index, item in enumerate(items):
        if item.get('suit_group'):
            suit_groups.setdefault(item['suit_group'], []).append(index)
    for indexes in suit_groups.values():
        if len(indexes) != 2:
            continue
        grouped.update(indexes)
        family = _meta(color)['hue_family']
        shade = FORMAL_SUIT_SHADES.get(family)
        if shade:
            result.append({'indexes': tuple(indexes), 'use_key': tuple(indexes), 'slot': 'suit',
                           'area': 'large', 'area_rank': 3, 'score': 96,
                           'name': shade[0], 'hex': shade[1], 'relation': 'similar', 'order': -1})
    for index, item in enumerate(items):
        if index in grouped:
            continue
        slot = _rule_slot(template, item)
        if not slot:
            continue
        candidate = _candidate(template, color, [index], slot, _area_for(template, item), index)
        if candidate:
            result.append(candidate)
    return sorted(result, key=lambda c: (-c['area_rank'], -c['score'], c['order']))


def _wardrobe_slots(template, color):
    ranked = []
    for slot in ('watch', 'bag', 'belt', 'shoes', 'scarf', 'jewelry'):
        try:
            score = score_color_for_item(color['hex'], template['gender'], template['tpo'], slot)
        except KeyError:
            continue
        if score >= 60:
            ranked.append({'slot': slot, 'minimum_score': 60})
    return ranked


def _decorate_base_items(template):
    for item in template['items']:
        name, hx = BASE_COLORS[item['color']]
        item['base_color'] = item['color']
        item['color_name'] = name
        item['hex'] = hx
    return template


def apply_daily_colors(template, color_a, color_b):
    """Return a colored copy of one fixed template plus placement metadata."""
    result = _decorate_base_items(deepcopy(template))
    colors = {'a': deepcopy(color_a), 'b': deepcopy(color_b)}
    candidates = {role: _candidates(result, color) for role, color in colors.items()}
    best_area = {role: (entries[0]['area_rank'] if entries else 0) for role, entries in candidates.items()}
    roles = ['b', 'a'] if best_area['b'] > best_area['a'] else ['a', 'b']
    used, placements = set(), {}
    for role in roles:
        choice = next((c for c in candidates[role] if not used.intersection(c['use_key'])), None)
        if choice is None:
            continue
        used.update(choice['use_key'])
        for index in choice['indexes']:
            result['items'][index].update(
                color_name=choice['name'], hex=choice['hex'],
                applied_daily_color=role.upper(), color_relation=choice['relation'],
                source_color_name=colors[role].get('name_ko') or colors[role].get('name'),
                source_hex=colors[role]['hex'],
            )
        placements[role] = {k: choice[k] for k in ('slot', 'area', 'relation', 'name', 'hex')}

    # If both colors only qualify for the same tie, retain A as the base and B
    # as a stripe. This is a real regimental/striped-tie use, not a fake item.
    if 'a' in placements and 'b' not in placements and placements['a']['slot'] == 'tie':
        other_tie = next((c for c in candidates['b'] if c['slot'] == 'tie'), None)
        tie_index = next((i for i, item in enumerate(result['items']) if item['category'] == 'tie'), None)
        if other_tie and tie_index is not None:
            result['items'][tie_index]['label'] = '레지멘탈 타이'
            result['items'][tie_index]['pattern_color'] = {
                'role': 'B', 'name': other_tie['name'], 'hex': other_tie['hex'],
                'relation': other_tie['relation'],
            }
            placements['b'] = {**{k: other_tie[k] for k in ('slot', 'area', 'relation', 'name', 'hex')},
                               'pattern': True}

    unresolved = []
    for role in ('a', 'b'):
        if role not in placements:
            unresolved.append({
                'role': role.upper(), 'name': colors[role].get('name_ko') or colors[role].get('name'),
                'hex': colors[role]['hex'], 'next_step': 'wardrobe_then_palette',
                'wardrobe_slots': _wardrobe_slots(result, colors[role]),
            })
    result['color_strategy'] = {
        'priority': 'A_first_unless_B_fits_larger_area',
        'placement_order': ['large', 'medium', 'small', 'owned_wardrobe', 'palette'],
        'placements': placements,
        'unresolved': unresolved,
    }
    return result


def build_colored_catalog_contexts(gender, season, color_a, color_b):
    from fashion_v2.template_catalog import templates_for

    result = {}
    for tpo in ('casual', 'business_casual', 'business_formal'):
        result[tpo] = {
            'status': 'ui_connected_stage3',
            'looks': [apply_daily_colors(t, color_a, color_b)
                      for t in templates_for(gender, season, tpo)],
        }
    return result
