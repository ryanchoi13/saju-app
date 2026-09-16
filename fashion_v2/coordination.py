"""DALHA outfit policy 1.0: optional colour relationships, not dress-code laws.

The numeric lightness/repetition checks are conservative SVG heuristics. They
are not measured garment colours, research-derived cutoffs or aesthetic proof.
This module evaluates existing outfits; it never adds an item or elemental C.
"""
from itertools import combinations

POLICY_VERSION = 'dalha-outfit-1.0'


def tie_separation(items, describe):
    suit = next((i for i in items if i.get('suit_group')), None)
    tie = next((i for i in items if i['category'] == 'tie'), None)
    shirt = next((i for i in items if i['category'] == 'top'), None)
    if not suit or not tie:
        return {'ok': True, 'basis': 'not_applicable'}
    sc, tc = describe({'hex':suit['hex']}), describe({'hex':tie['hex']})
    gap = abs(sc['lightness'] - tc['lightness'])
    base_distinct = sc['hex'] != tc['hex'] and (sc['family'] != tc['family'] or gap >= .12)
    stripe = tie.get('color_parts', {}).get('pattern')
    pattern_distinct = False
    if tie.get('pattern') == 'stripe' and stripe:
        pc = describe({'hex':stripe['hex']})
        pattern_distinct = (abs(pc['lightness'] - sc['lightness']) >= .12
                            and abs(pc['lightness'] - tc['lightness']) >= .12)
    shirt_distinct = not shirt or abs(describe({'hex':shirt['hex']})['lightness'] - tc['lightness']) >= .13
    return {'ok': bool((base_distinct or pattern_distinct) and shirt_distinct),
            'basis': 'base_color' if base_distinct else 'visible_pattern' if pattern_distinct else 'insufficient_separation',
            'shirt_distinct': shirt_distinct}


def evaluate_coordination(items, tpo, describe):
    """Recognise matching without rewarding matching for its own sake.

Only competing defaults (formal leather mismatch / >2 strong accent repeats)
receive a small penalty. Black, white and tonal clothing are not repetition
violations. Material compatibility is evaluated only when both are known.
    """
    colors = [describe({'hex':i['hex']}) for i in items]
    relations, cautions = [], []
    score = 0

    def relation(kind, indices, reason):
        relations.append(dict(kind=kind, items=[items[i].get('key', str(i)) for i in indices], reason=reason))

    suits = {}
    for n, item in enumerate(items):
        if item.get('suit_group'):
            suits.setdefault(item['suit_group'], []).append(n)
    for indices in suits.values():
        if len(indices) == 2 and colors[indices[0]]['hex'] == colors[indices[1]]['hex']:
            relation('set', indices, '수트 상·하의를 같은 색으로 연결')

    clothing = [n for n, i in enumerate(items) if i['category'] in {'top','bottom','dress','outer','coat','mid','carry_outer'}]
    for a, b in combinations(clothing, 2):
        ca, cb = colors[a], colors[b]
        if items[a].get('suit_group') and items[a].get('suit_group') == items[b].get('suit_group'):
            continue
        if ca['family'] == cb['family'] and ca['hex'] != cb['hex']:
            relation('tonal', [a,b], '같은 색 계열 안에서 톤을 달리한 배색')

    shoe = next((n for n,i in enumerate(items) if i['category'] == 'shoes'), None)
    if shoe is not None:
        for n, item in enumerate(items):
            same_family = colors[n]['family'] == colors[shoe]['family']
            close = same_family and abs(colors[n]['lightness'] - colors[shoe]['lightness']) <= .12
            if item['category'] == 'top' and close:
                relation('top_shoe_echo', [n,shoe], '상의와 신발의 색을 반복해 연결')
            if item['category'] == 'bag':
                relation('bag_shoe_match' if close else 'bag_shoe_independent', [n,shoe],
                         '가방·신발을 비슷한 색으로 정리' if close else '가방·신발은 서로 다른 톤도 허용')
            if item['label'] == '벨트' and tpo == 'business_formal':
                leather = lambda value: value.get('material') in {'leather','smooth_leather','patent_leather','suede'}
                if leather(item) and leather(items[shoe]):
                    relation('formal_leather_pair', [n,shoe], '포멀 가죽 구두·벨트는 같은 색 계열 우선')
                    if not same_family:
                        score -= 8
                        cautions.append('포멀 가죽 구두와 벨트의 색 계열이 다름')

    accents = {}
    for n, item in enumerate(items):
        if item['category'] not in {'bag','shoes','tie','accessory'}:
            continue
        c = colors[n]
        if c['family'] in {'red','orange','yellow','green','teal','blue','purple'} and c['saturation'] > .3 and .2 < c['lightness'] < .8:
            accents.setdefault(c['family'], []).append(n)
    for indices in accents.values():
        if len(indices) > 2:
            score -= 12 * (len(indices) - 2)
            cautions.append('같은 강한 포인트색의 소품 반복이 2개를 넘음')
    return dict(policy_version=POLICY_VERSION, relations=relations, cautions=cautions,
                score_adjustment=score, scope='existing_candidate_evaluation',
                aesthetic_approval=False)
