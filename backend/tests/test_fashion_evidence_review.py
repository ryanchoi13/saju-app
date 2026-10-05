from copy import deepcopy
import itertools

import pytest

from fashion_v2.evidence_review import (
    load_archive, validate_archive, score_item, evaluate_outfit, match_patterns,
)


@pytest.fixture
def archive():
    return load_archive()


def context(**changes):
    return dict(gender='male',age_band='forties',season='autumn',tpo='casual',**changes) if not changes else {**context(),**changes}


def gid(a,name):
    return next(g['id'] for g in a['garments'] if g['name']==name)


def test_identifiers_foreign_keys_and_frozen_palette(archive):
    assert validate_archive(archive)
    assert len(archive['colors'])==141
    assert len(archive['garments'])==49
    assert len({c['hex'] for c in archive['colors']})==141


def test_missing_color_evidence_is_not_zero_or_approved(archive):
    r=score_item(archive,gid(archive,'목걸이'),'wada-FBE6A0',context())
    assert r['score'] is None and r['status']=='unassessed'
    with pytest.raises(ValueError):score_item(archive,gid(archive,'목걸이'),'not-registered',context())
    with pytest.raises(ValueError):score_item(archive,gid(archive,'목걸이'),'wardrobe-white',{'gender':'male'})


def test_contextual_feedback_does_not_become_universal_color_ban(archive):
    garment=gid(archive,'블루종')
    male=score_item(archive,garment,'wardrobe-pink',context())
    female=score_item(archive,garment,'wardrobe-pink',context(gender='female'))
    summer=score_item(archive,garment,'wardrobe-pink',context(season='summer'))
    assert male['score']==2
    assert female['score'] is None and summer['score'] is None
    pants=gid(archive,'면바지')
    assert score_item(archive,pants,'wardrobe-pink',context(age_band='fifties'))['score']==2
    teen=score_item(archive,pants,'wardrobe-pink',context(gender='female',age_band='teen'))
    assert teen['score']==3 and teen['confidence']=='low'


def test_specific_rule_wins_and_equal_priority_conflict_is_visible(archive):
    g=gid(archive,'긴팔 캐주얼 셔츠')
    original=score_item(archive,g,'wardrobe-navy',context())
    high=next(r for r in archive['rules'] if r['id'] in original['rule_ids'])
    duplicate=deepcopy(high);duplicate.update(id='TEST',score=1)
    archive['rules'].append(duplicate)
    r=score_item(archive,g,'wardrobe-navy',context())
    assert r['status']=='conflict' and r['score'] is None


def test_reported_failures_stay_rejected_and_proposals_need_visual_review(archive):
    for b in archive['benchmarks']:
        r=evaluate_outfit(archive,b['items'],b['context'])
        assert r['production_eligible'] is False and r['aesthetic_score'] is None
        if b['id'] in ('B01','B02'):
            assert r['item_gate']=='revise'
            assert r['whole_outfit_status']=='revise'
        elif b['id'] in ('B03','B04','B05'):
            assert r['item_gate']=='candidate'
            assert r['whole_outfit_status']=='needs_visual_review'


def test_pair_support_never_certifies_whole_outfit_and_is_order_independent(archive):
    b=next(x for x in archive['benchmarks'] if x['id']=='B04')
    expected={'P01','P02'}
    for permutation in itertools.permutations(b['items']):
        r=evaluate_outfit(archive,list(permutation),b['context'])
        assert set(r['matched_pattern_ids'])==expected
        assert r['aesthetic_score'] is None
    bad=deepcopy(b['items'])
    bad[0]['color_id']='wardrobe-pink'
    assert evaluate_outfit(archive,bad,b['context'])['item_gate']=='revise'


def test_repeated_pattern_parts_require_distinct_garments(archive):
    g=gid(archive,'니트')
    archive['patterns']=[dict(id='TEST',scope={},parts=[
        {'garment_ids':[g],'color_ids':['wardrobe-gray']},
        {'garment_ids':[g],'color_ids':['wardrobe-gray']}])]
    assert not match_patterns(archive,[dict(garment_id=g,color_id='wardrobe-gray')],context())


def test_unverified_source_cannot_be_implicit_evidence(archive):
    excluded={s['id'] for s in archive['sources'] if s['status']=='excluded'}
    assert all(o['source_id'] not in excluded for o in archive['observations'])
    assert all(r['score']<5 for r in archive['rules'])
