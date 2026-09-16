from copy import deepcopy

from fashion_v2.coordination import evaluate_coordination, tie_separation
from fashion_v2.svg_recommendation import (PALETTE, apply_colors, describe_color,
                                          select_template)
from fashion_v2.template_catalog import templates_for


def item(category, label, color, **extra):
    c = PALETTE[color]
    return dict(category=category, label=label, hex=c['hex'], color_name=c['name'], **extra)


def evaluate(items, tpo='casual'):
    return evaluate_coordination(items, tpo, describe_color)


def test_same_navy_tie_requires_actual_visible_pattern_and_readable_shirt():
    items = [item('outer','수트 재킷','navy',suit_group='suit'),
             item('top','긴팔 정장 셔츠','white'), item('tie','넥타이','navy')]
    assert not tie_separation(items,describe_color)['ok']
    tie = items[-1]
    tie.update(pattern='stripe',color_parts={'pattern':{'hex':PALETTE['ivory']['hex']}})
    assert tie_separation(items,describe_color) == dict(ok=True,basis='visible_pattern',shirt_distinct=True)
    tie['color_parts']['pattern']['hex'] = tie['hex']
    assert not tie_separation(items,describe_color)['ok']
    tie['color_parts']['pattern']['hex'] = PALETTE['ivory']['hex']
    items[1]['hex'] = tie['hex']
    assert not tie_separation(items,describe_color)['ok']


def test_tonal_suit_tie_can_remain_in_real_recommendation_pipeline():
    look = select_template(templates_for('male','spring','business_formal')[0],35,1)
    look['color_targets'] = {'A':{'category':'suit'},'B':None}
    for i in look['items']:
        if i['category']=='tie':
            i.update(hex=PALETTE['navy']['hex'],color_name='네이비',pattern='stripe',pattern_palette=['ivory'])
    before = deepcopy(look)
    result = apply_colors(look,PALETTE['navy'],PALETTE['white'])
    suit = next(i for i in result['items'] if i.get('suit_group'))
    tie = next(i for i in result['items'] if i['category']=='tie')
    assert suit['hex'] == tie['hex'] == PALETTE['navy']['hex']
    assert result['coordination']['tie_separation']['basis'] == 'visible_pattern'
    assert result['color_strategy']['additional_element_C'] is None
    assert look == before


def test_matching_and_nonmatching_bags_are_equally_valid_and_add_no_items():
    items = [item('top','반팔 티셔츠','white'), item('bottom','데님 바지','denim'),
             item('shoes','운동화','white'), item('bag','토트백','brown')]
    before = deepcopy(items)
    report = evaluate(items)
    assert {'top_shoe_echo','bag_shoe_independent'} <= {r['kind'] for r in report['relations']}
    assert report['score_adjustment'] == 0 and items == before
    items[-1]['hex'] = PALETTE['white']['hex']
    assert evaluate(items)['score_adjustment'] == 0
    assert 'bag_shoe_match' in {r['kind'] for r in evaluate(items)['relations']}


def test_black_repetition_is_not_a_strong_accent_and_three_vivid_accessories_are_ranked_lower():
    items = [item('accessory','모자','black'),item('bag','크로스백','black'),item('shoes','운동화','black')]
    assert evaluate(items)['score_adjustment'] == 0
    for i in items:i['hex'] = PALETTE['red']['hex']
    assert evaluate(items)['score_adjustment'] < evaluate(items[:2])['score_adjustment']


def test_formal_leather_pair_prefers_family_only_when_material_is_known():
    items = [item('shoes','옥스퍼드','black',material='leather'),item('accessory','벨트','brown',material='leather')]
    assert evaluate(items,'business_formal')['score_adjustment'] < 0
    assert evaluate(items,'casual')['score_adjustment'] == 0
    items[-1]['hex'] = PALETTE['black']['hex']
    assert evaluate(items,'business_formal')['score_adjustment'] == 0
    del items[-1]['material']
    assert not evaluate(items,'business_formal')['relations']


def test_suit_set_and_tonal_layers_are_recorded_separately():
    items = [item('outer','수트 재킷','navy',suit_group='suit'),
             item('bottom','수트 바지','navy',suit_group='suit'), item('top','긴팔 정장 셔츠','sky')]
    report = evaluate(items,'business_formal')
    assert [r['kind'] for r in report['relations']].count('set') == 1
    assert 'tonal' in {r['kind'] for r in report['relations']}
    assert not report['cautions'] and report['aesthetic_approval'] is False
