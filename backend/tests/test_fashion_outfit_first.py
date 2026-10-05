import builtins
import itertools

import pytest

from fashion_v2.daily_palette import select_daily_palette, private_color_hint, optional_wada_reference, PALETTE as DAILY_COLORS
from fashion_v2.svg_recommendation import build_svg_catalog_contexts, PALETTE
from fashion_v2.realwear_rules import visible_colors


def test_daily_colors_are_registered_deterministic_and_independent_of_wada(monkeypatch):
    import wada_color_rules
    original=select_daily_palette('土','火',20261002)
    monkeypatch.setattr(wada_color_rules,'WADA_DUOS',{})
    assert select_daily_palette('土','火',20261002)==original
    for primary,secondary in itertools.product('木火土金水',repeat=2):
        seen=set()
        for day in range(20261001,20261008):
            p=select_daily_palette(primary,secondary,day)
            assert p['top']['hex'] != p['bottom']['hex']
            assert p['top']['id'] in DAILY_COLORS and p['bottom']['id'] in DAILY_COLORS
            seen.add((p['top']['hex'],p['bottom']['hex']))
        assert len(seen)>1


def test_missing_wada_module_does_not_block_outfits(monkeypatch):
    original_import=builtins.__import__
    def no_wada(name,*args,**kwargs):
        if name.startswith('wada'):
            raise ImportError('reference intentionally unavailable')
        return original_import(name,*args,**kwargs)
    before=build_svg_catalog_contexts('male','autumn',PALETTE['red'],PALETTE['purple'],age=48)
    monkeypatch.setattr(builtins,'__import__',no_wada)
    after=build_svg_catalog_contexts('male','autumn',PALETTE['red'],PALETTE['purple'],age=48)
    for tpo in before:
        for old,new in zip(before[tpo]['looks'],after[tpo]['looks']):
            assert old['garment_spec']==new['garment_spec']
            assert new['color_strategy']['wada_reference']['available'] is False


@pytest.mark.parametrize('age',[45,48,55])
def test_reported_yellow_pink_is_not_forced_onto_outer_and_shoes(age):
    a={'hex':'#FBE6A0','name_ko':'옅은 노랑'}
    for look in build_svg_catalog_contexts('male','autumn',a,PALETTE['pink'],age=age)['casual']['looks']:
        s=look['garment_spec']
        assert s['outerColor'] not in {a['hex'],PALETTE['pink']['hex'],PALETTE['butter']['hex']}
        assert s['shoeColor'] in {PALETTE['white']['hex'],PALETTE['black']['hex']}
        assert s['bottomColor']==PALETTE['beige']['hex']
        assert look['coordination']['whole_outfit_quality']['rank'][:2] == (4,0)
        assert look['color_strategy']['original']['A']['hex']==a['hex']
        assert look['color_strategy']['selection_flow']==['base_outfit','optional_daily_colors','whole_outfit_recheck']


def test_private_hint_is_optional_and_never_counts_as_worn_color():
    looks=build_svg_catalog_contexts('male','autumn',PALETTE['red'],PALETTE['purple'],age=48)['casual']['looks']
    for look in looks:
        strategy=look['color_strategy'];hint=strategy['private_color_suggestion']
        assert hint['optional'] is True and hint['visible'] is False
        assert '속옷' in hint['text'] and '원하실 때' in hint['text']
        assert all(c['role'] not in strategy['placements'] for c in hint['colors'])
        assert all(i['category']!='underwear' for i in look['items'])
        assert strategy['color_count']==len(visible_colors(look['items']))
        assert strategy['original']['B']['hex']==PALETTE['purple']['hex']
    assert private_color_hint([]) is None


def test_two_unused_colors_are_alternatives_not_two_required_underwear_items():
    hint=private_color_hint([dict(role='A',name='빨강',hex='#FF0000'),dict(role='B',name='초록',hex='#00FF00')])
    assert '빨강 또는 초록' in hint['text']
    assert '반드시' not in hint['text']


def test_no_valid_color_placement_keeps_the_complete_base_outfit(monkeypatch):
    import fashion_v2.svg_recommendation as engine
    monkeypatch.setattr(engine,'candidates',lambda *args:[None])
    looks=engine.build_svg_catalog_contexts('male','autumn',PALETTE['yellow'],PALETTE['purple'],age=48)['casual']['looks']
    for look in looks:
        assert not look['color_strategy']['placements']
        assert len(look['color_strategy']['unresolved'])==2
        assert len(look['items'])==4 and look['garment_spec']['shoe']
        assert look['color_strategy']['private_color_suggestion']['kind']=='underwear'


def test_optional_reference_can_be_found_without_becoming_a_selection_gate():
    reference=optional_wada_reference([{'hex':'#fbe6a0'},{'hex':'#f27291'}])
    assert 14 in reference['matching_duos']
    assert reference['role']=='optional_reference'
    assert optional_wada_reference([PALETTE['beige'],PALETTE['pink']])['matching_duos']==[]


def test_held_black_outer_does_not_receive_a_negative_evidence_score():
    from fashion_v2.outfit_quality import whole_outfit_quality
    from fashion_v2.svg_recommendation import describe_color
    look = dict(gender='male', age=48, season='autumn', tpo='casual')
    def quality(outer):
        items = [dict(category=cat, label=label, hex=PALETTE[color]['hex'])
                 for cat, label, color in [('outer','블루종',outer),
                    ('top','맨투맨','pink'), ('bottom','면바지','beige'),
                    ('shoes','운동화','white')]]
        return whole_outfit_quality(items, look, describe_color, PALETTE,
                                    {'score_adjustment': 0}, 4)
    black, navy = quality('black'), quality('navy')
    assert black['rank'] == navy['rank']
    assert not black['aesthetic_approval'] and not navy['aesthetic_approval']
