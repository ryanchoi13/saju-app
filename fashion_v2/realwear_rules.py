"""Owner-reviewed rules within the existing three TPOs (2026-09-16).

Sources inform choices, not universal dress codes. Pattern/part colours are
rendering data and never authorise an additional Five Elements colour C.
"""
from copy import deepcopy
import re

# Whole-outfit styling choices; no new user classification or half-tuck mode.
# A fine knit can be tucked. A skirt alone is not a reason to tuck every top.
TUCK_BY_TEMPLATE = {
    'female-spring-casual-trend': ('in', '얇은 파인 니트와 스커트의 허리를 정리한 착장'),
    'female-autumn-casual-trend': ('in', '티셔츠와 스커트의 허리를 정리한 착장'),
    'female-warm-transition-casual-trend': ('in', '가벼운 상의와 스커트의 허리를 정리한 착장'),
    'female-warm-transition-business_casual-daily': ('in', '검토 통과한 얇은 상의와 슬랙스의 허리 정리'),
}


def styling_for(look):
    top = next((i for i in look['items'] if i['category'] == 'top'), None)
    if not top:
        return {'tuck': 'out', 'reason': '원피스 착장', 'source': 'outfit_structure'}
    if top.get('tuck') in {'in', 'out'}:
        return {'tuck': top['tuck'], 'reason': '착장에 지정한 상의 처리', 'source': 'explicit_outfit'}
    if look.get('tuck') in {'in', 'out'}:
        return {'tuck': look['tuck'], 'reason': '착장에 지정한 상의 처리', 'source': 'explicit_outfit'}
    if any(i['label'] == '패딩' for i in look['items']) and top['label'] == '니트':
        return {'tuck': 'out', 'reason': '승인된 패딩 아래로 니트 밑단 연결', 'source': 'owner_approved'}
    if look.get('id') in TUCK_BY_TEMPLATE:
        tuck, reason = TUCK_BY_TEMPLATE[look['id']]
        return {'tuck': tuck, 'reason': reason, 'source': 'curated_from_styling_research'}
    shirt = '셔츠' in top['label'] and '티셔츠' not in top['label']
    tuck = 'in' if top['label'] == '긴팔 정장 셔츠' or shirt and look['tpo'] != 'casual' else 'out'
    return {'tuck': tuck, 'reason': '셔츠의 단정한 밑단 처리' if tuck == 'in' else '이 착장의 상의 밑단을 자연스럽게 꺼내기', 'source': 'outfit_default_not_universal_fashion_rule'}


PART_NAMES = {'body': '바탕', 'pattern': '무늬', 'strap': '줄', 'case': '테두리',
              'dial': '문자판', 'metal': '금속', 'stone': '장식', 'chain': '체인', 'pendant': '펜던트'}


def visible_colors(items):
    colors = set()
    for item in items:
        colors.add(item['hex'].upper())
        colors.update(p['hex'].upper() for p in item.get('color_parts', {}).values())
    return colors


def colour_parts(items, palette):
    """Build independent, traceable parts using the already selected palette.

    A tie stripe reuses an outfit colour if its original accent would push the
    outfit over four colours. Explicit owner watch colours remain an exception.
    Caller owns item copies; source templates are never mutated here.
    """
    base = {i['hex'].upper() for i in items}

    def part(item, key, hex_value=None, name=None, source='item_color'):
        p = dict(hex=(hex_value or item['hex']).upper(), name=name or item['color_name'], source=source)
        if hex_value is None and item.get('applied_daily_color'):
            p.update(role=item['applied_daily_color'], original_hex=item['source_hex'],
                     original_name=item['source_color_name'], relation=item['color_relation'])
        return key, p

    for item in items:
        # Explicit per-item parts also support imported/reviewed combinations.
        if item.get('parts_locked'):
            for value in item.get('color_parts', {}).values():
                if not re.fullmatch(r'#[0-9A-Fa-f]{6}', value.get('hex', '')):
                    raise ValueError('부위 색상은 6자리 HEX여야 합니다')
            base.update(p['hex'].upper() for p in item.get('color_parts', {}).values())
            continue
        name = item['label']
        if name == '넥타이':
            parts = dict([part(item, 'body')])
            if item.get('pattern') == 'stripe':
                choices = [palette[k] for k in item['pattern_palette']]
                choices += [{'hex': i['hex'], 'name': i['color_name']} for i in items
                            if i['category'] in {'top', 'outer', 'bottom'}]
                accent = next((c for c in choices if c['hex'].upper() != item['hex'].upper()
                               and len(base | {c['hex'].upper()}) <= 4), None)
                if accent:
                    parts.update([part(item, 'pattern', accent['hex'], accent['name'], 'outfit_pattern_base')])
                    base.add(accent['hex'].upper())
                else:
                    item['pattern_omitted_reason'] = '추가 색·같은 색 무늬를 피할 수 없어 단색 처리'
            item['color_parts'] = parts
        elif name == '시계':
            # Explicit approved designs win. Otherwise use a restrained material
            # baseline, not the trouser colour as an invented metal finish.
            case_hex = item.get('watch_case_hex')
            case_name = next((c['name'] for c in palette.values() if c['hex'].upper() == str(case_hex).upper()), None)
            if case_hex:
                strap_hex, strap_name = case_hex, case_name
                origin = 'owner_approved_component'
            else:
                case_hex, case_name = palette['light_gray']['hex'], '실버 표현색'
                strap_hex, strap_name = palette['black']['hex'], '블랙'
                origin = 'material_baseline_not_measured_product_hex'
            item['color_parts'] = dict([part(item,'dial'),part(item,'strap',strap_hex,strap_name,origin),part(item,'case',case_hex,case_name,origin)])
            item['watch_variant'] = 'gender_basic_v1'
            item['display_label'] = '시계'
            base.update([case_hex.upper(),strap_hex.upper()])
        elif name in {'귀걸이', '목걸이'}:
            target = 'stone' if name == '귀걸이' else 'pendant'
            structure = 'metal' if name == '귀걸이' else 'chain'
            metal_hex = palette['light_gray']['hex']
            item['color_parts'] = dict([part(item,target),part(item,structure,metal_hex,'실버 표현색','material_baseline_not_measured_product_hex')])
            base.add(metal_hex.upper())
        elif item['category'] == 'accessory':
            item['color_parts'] = dict([part(item,'body')])

    for item in items:
        parts = item.get('color_parts', {})
        if not parts:
            continue
        groups = {}
        for key, value in parts.items():
            groups.setdefault((value['hex'],value['name']),[]).append(PART_NAMES[key])
        if len(groups) > 1:
            item['color_description'] = ' · '.join(f'{name} {"·".join(names)}' for (_,name),names in groups.items())
        else:
            item['color_description'] = next(iter(groups))[1]


def accessory_spec(item):
    return dict(id=item.get('key', item['label']), name=item['label'], color=item['hex'],
                parts=deepcopy(item.get('color_parts', {})),
                pattern=item.get('pattern', 'solid'), variant=item.get('watch_variant'))
