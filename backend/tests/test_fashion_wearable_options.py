"""Regressions for the teal/camel screenshot, not a new hard colour ban."""
from copy import deepcopy
from datetime import datetime

import pytest

from fashion_v2.svg_recommendation import (
    PALETTE, build_svg_catalog_contexts, describe_color, permitted, select_template,
    tone, variants, candidates,
)
from fashion_v2.template_catalog import templates_for
from fashion_v2.weather_outfit import classify_weather
from fashion_v2.wearable_options import (
    garment_options, muted_green_bottom, outfit_balance, wardrobe_tones,
)

TEAL = {'hex': '#099197', 'name_ko': '딥 청록', 'element': '목'}
CAMEL = {'hex': '#C5A56E', 'name_ko': '카멜', 'element': '토'}


def autumn(number=1, tpo='casual'):
    return select_template(templates_for('male', 'autumn', tpo)[number-1], 48, number)


def profile(day, night):
    return classify_weather([
        {'time': datetime(2026, 9, 18, h), 'apparent_temperature': v}
        for h, v in [(8, night), (13, day), (20, night)]
    ])


def test_raw_camel_is_yellow_but_has_explicit_wardrobe_mapping():
    raw = describe_color(CAMEL)
    assert raw['family'] == 'yellow'  # Do not rewrite the fortune/pigment source.
    assert 'beige' in wardrobe_tones(raw)
    assert 'beige' not in wardrobe_tones(describe_color(PALETTE['yellow']))
    options = list(variants(raw))
    assert options[0][0]['hex'] == CAMEL['hex']
    assert any(c['id'] == 'beige' and reason for c, _, reason in options[1:])


def test_exact_allowed_slot_still_compares_adjacent_tones():
    options = candidates(autumn(), describe_color(TEAL), 'A')
    assert any(c and c['category'] == 'outer' and c['relation'] == 'exact' for c in options)
    assert any(c and c['category'] == 'outer' and c['relation'] == 'similar' for c in options)
    assert {'forest', 'sage', 'olive'} <= set(wardrobe_tones(describe_color(TEAL)))


@pytest.mark.parametrize('age', [35, 48, 55])
@pytest.mark.parametrize('reverse', [False, True])
def test_teal_camel_does_not_crowd_both_colours_above_fixed_jeans(age, reverse):
    a, b = (CAMEL, TEAL) if reverse else (TEAL, CAMEL)
    before = deepcopy((a, b))
    contexts = build_svg_catalog_contexts('male', 'autumn', a, b, age=age)
    for look in contexts['casual']['looks']:
        assert look['garment_spec']['bottom'] == '면바지'
        assert look['coordination']['wearability']['risk'] == 0
        places = look['color_strategy']['placements']
        assert {'A', 'B'} == set(places)
        assert 'bottom' in {p['slot'] for p in places.values()}
        assert look['color_strategy']['original']['A']['hex'] == a['hex']
        assert look['color_strategy']['original']['B']['hex'] == b['hex']
        assert look['color_strategy']['additional_element_C'] is None
        for item in look['items']:
            if item.get('applied_daily_color'):
                expected = a if item['applied_daily_color'] == 'A' else b
                assert item['source_hex'] == expected['hex']
    assert (a, b) == before


def test_reported_pair_has_neutral_inner_and_beige_or_olive_pants():
    looks = build_svg_catalog_contexts('male', 'autumn', TEAL, CAMEL, age=48)['casual']['looks']
    first, second = [l['garment_spec'] for l in looks]
    assert first['outerColor'] == TEAL['hex']
    assert first['topColor'] == PALETTE['white']['hex']
    assert first['bottomColor'] == PALETTE['beige']['hex']
    assert second['outerColor'] == CAMEL['hex']
    assert second['topColor'] == PALETTE['white']['hex']
    assert second['bottomColor'] == PALETTE['olive']['hex']
    assert first['top'] == '맨투맨' and second['top'] == '후드티'


@pytest.mark.parametrize('day,night', [(33,27), (25,16), (18,13), (8,2), (2,-4)])
def test_weather_layers_and_warmth_survive_cotton_option(day, night):
    contexts = build_svg_catalog_contexts('male', 'autumn', TEAL, CAMEL, profile(day, night), 48)
    for look in contexts['casual']['looks']:
        s = look['garment_spec']
        if day >= 33:
            assert not s['outer']
        if day == 25:
            assert s['outerMode'] == 'carry'
        if day <= 8:
            bottom = next(i for i in look['items'] if i['category'] == 'bottom')
            if bottom['label'] == '면바지':
                assert bottom['material'] in {'winter_cotton', 'fleece_cotton'}
            assert s['trouserExtraLength'] == 24


def test_cotton_does_not_mean_khaki_denim_or_vivid_pants():
    look = autumn()
    for key in ['olive', 'sage', 'forest']:
        c = describe_color(tone(key))
        assert muted_green_bottom(c)
        assert permitted(c, {'category':'bottom','label':'면바지'}, look)
        assert not permitted(c, {'category':'bottom','label':'데님 바지'}, look)
    for key in ['purple', 'cobalt', 'red']:
        assert not permitted(describe_color(tone(key)), {'category':'bottom','label':'면바지'}, look)
    formal = autumn(tpo='business_formal')
    assert not permitted(describe_color(tone('olive')), {'category':'suit','label':'수트'}, formal)


def test_original_denim_is_retained_for_compatible_outfits():
    looks = build_svg_catalog_contexts('male', 'autumn', PALETTE['navy'], PALETTE['white'], age=48)['casual']['looks']
    assert any(l['garment_spec']['bottom'] == '데님 바지' for l in looks)
    original = autumn()
    before = deepcopy(original)
    options = list(garment_options(original, PALETTE))
    assert len(options) == 2
    assert original == before
    assert options[0] is original
    for key in ['top', 'outer', 'shoes']:
        assert [i for i in options[0]['items'] if i['category']==key] == [i for i in options[1]['items'] if i['category']==key]
    original['review_preference'] = 'approved'
    assert len(list(garment_options(original, PALETTE))) == 1
    assert len(list(garment_options(autumn(tpo='business_formal'), PALETTE))) == 1


def test_two_coloured_upper_layers_are_not_a_blanket_violation():
    def risk(a,b):
        return outfit_balance([
            {'category':'outer', 'hex':a}, {'category':'top','hex':b}
        ], describe_color)['risk']
    assert risk(TEAL['hex'], CAMEL['hex']) == 2
    assert risk(PALETTE['teal']['hex'], PALETTE['beige']['hex']) == 0
    assert risk(PALETTE['navy']['hex'], PALETTE['sky']['hex']) == 0
    assert risk(PALETTE['black']['hex'], PALETTE['white']['hex']) == 0
