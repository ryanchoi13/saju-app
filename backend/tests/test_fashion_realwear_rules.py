from copy import deepcopy

from fashion_v2.svg_recommendation import (select_template, to_spec, build_svg_catalog_contexts,
    PALETTE, tone, describe_color, permitted, candidates)
from fashion_v2.template_catalog import templates_for
from fashion_v2.realwear_rules import styling_for, colour_parts, visible_colors
from fashion_v2.weather_catalog import _rain_safe


def selected(gender='female',season='autumn',tpo='casual',number=2):
    return select_template(templates_for(gender,season,tpo)[number-1],35,number)


def test_whole_outfit_shoes_survive_and_formal_stays_formal():
    assert to_spec(selected())['shoe']=='앵클부츠'
    assert to_spec(selected(season='spring'))['shoe']=='플랫슈즈'
    for season in ('spring','summer','autumn','winter'):
        for n in (1,2):
            assert to_spec(selected('male',season,'business_formal',n))['shoe'] in {'옥스퍼드','더비 구두'}


def test_skirt_alone_does_not_force_tuck_and_explicit_choice_wins():
    look=selected();look['id']='research-knit-with-skirt'
    top=next(i for i in look['items'] if i['category']=='top')
    top.update(label='니트',material='wool_knit')
    assert to_spec(look)['tuck']=='out'
    top['tuck']='in';assert to_spec(look)['tuck']=='in'
    assert styling_for(selected(season='spring'))['tuck']=='in'


def test_independent_accessory_payload_and_locked_parts_round_trip():
    look=selected();look['items'] += [
        dict(key='watch',category='accessory',label='시계',hex='#355B48',color_name='포레스트',color_parts={'dial':{'hex':'#355B48','name':'포레스트'},'strap':{'hex':'#EAC744','name':'옐로'},'case':{'hex':'#EAC744','name':'옐로'}},parts_locked=True),
        dict(key='earrings',category='accessory',label='귀걸이',hex='#70468A',color_name='퍼플')]
    colour_parts(look['items'],PALETTE)
    s=to_spec(look)
    assert s['accessoryItems'][0]['color']=='#355B48'
    assert s['accessoryItems'][1]['color']=='#70468A'
    assert s['accessoryItems'][1]['parts']['metal']['hex']==PALETTE['light_gray']['hex']
    assert s['accessoryItems'][0]['parts']['case']['hex']=='#EAC744'
    assert '#EAC744' in visible_colors(look['items'])


def test_tie_pattern_reuses_palette_and_is_counted():
    look=selected('male','spring','business_formal',1)
    tie=next(i for i in look['items'] if i['category']=='tie')
    assert tie['pattern']=='stripe'
    colour_parts(look['items'],PALETTE)
    assert tie['color_parts']['body']['hex']!=tie['color_parts']['pattern']['hex']
    assert len(visible_colors(look['items']))<=4
    assert to_spec(look)['accessoryItems'][0]['pattern']=='stripe'


def test_component_count_and_ab_provenance_in_full_pipeline():
    look=build_svg_catalog_contexts('female','autumn',PALETTE['forest'],PALETTE['purple'],age=55)['business_formal']['looks'][1]
    watch=next(i for i in look['items'] if i['label']=='시계')
    assert watch['color_parts']['dial']['role']=='A'
    assert watch['color_parts']['dial']['original_hex']==PALETTE['forest']['hex']
    assert watch['color_parts']['case']['hex']==PALETTE['yellow']['hex']
    assert look['color_strategy']['color_count']==len(visible_colors(look['items']))
    assert look['color_strategy']['additional_element_C'] is None
    assert look['color_strategy']['placements']['A']['parts'][0]['part']=='dial'


def test_rain_does_not_invent_waterproofing_or_mutate_original():
    original=templates_for('female','spring','casual')[0]
    changed=deepcopy(original);_rain_safe(changed)
    shoe=next(i for i in changed['items'] if i['category']=='shoes')
    assert '생활방수' not in shoe['label']
    assert shoe['rain_protection']=='unverified'
    assert 'rain_protection' not in next(i for i in original['items'] if i['category']=='shoes')


def test_researched_beige_coat_black_denim_and_adjacent_accessory_tone():
    look=selected()
    assert permitted(describe_color(tone('beige')),{'category':'coat','label':'코트'},look)
    assert not permitted(describe_color(tone('beige')),{'category':'coat','label':'코트'},{**look,'season':'winter'})
    assert permitted(describe_color(tone('black')),{'category':'bottom','label':'데님 바지'},look)
    male=selected('male','spring','business_formal',1)
    options=[x for x in candidates(male,describe_color(tone('red')),'A') if x and x['category']=='tie']
    assert {'exact','similar'}<={x['relation'] for x in options}
