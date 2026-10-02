"""Offline fashion evidence review. Never imported by the live recommender.

Ordinal editorial scores and source confidence are deliberately separate.
Unknown/conflicting evidence cannot silently pass the review gate. Pair-pattern
matches explain candidates; they never certify a complete outfit as beautiful.
"""
from __future__ import annotations

import json
from pathlib import Path

DATA = Path(__file__).with_name('evidence_data') / 'v1'
DIMENSIONS = {
    'gender': ('male', 'female'),
    'age_band': ('teen', 'twenties', 'thirties', 'forties', 'fifties'),
    'season': ('spring', 'summer', 'autumn', 'winter'),
    'tpo': ('casual', 'business_casual', 'business_formal'),
}


def load_archive(path=DATA):
    return {name: json.loads((Path(path) / f'{name}.json').read_text())
            for name in ('manifest', 'colors', 'garments', 'sources',
                         'observations', 'color_mappings', 'rules', 'patterns',
                         'benchmarks', 'review_events')}


def validate_context(context):
    for field, values in DIMENSIONS.items():
        if context.get(field) not in values:
            raise ValueError(f'Explicit supported {field} required')


def context_matches(scope, context):
    return all(context[k] in values for k, values in scope.items())


def score_item(archive, garment_id, color_id, context):
    validate_context(context)
    if garment_id not in {g['id'] for g in archive['garments']}:
        raise ValueError('Unknown garment id')
    if color_id not in {c['id'] for c in archive['colors']}:
        raise ValueError('Unknown color id')
    matching = [r for r in archive['rules']
                if garment_id in r['garment_ids'] and color_id in r['color_ids']
                and context_matches(r['scope'], context)]
    if not matching:
        return dict(score=None, status='unassessed', rule_ids=[], confidence='unknown',
                    reasons=['이 조건의 평가 근거가 아직 등록되지 않음'])
    priority = max(r['priority'] for r in matching)
    winners = [r for r in matching if r['priority'] == priority]
    if len({r['score'] for r in winners}) != 1:
        return dict(score=None, status='conflict', rule_ids=[r['id'] for r in winners],
                    confidence='unknown', reasons=['같은 우선순위의 평가가 충돌하여 재검토 필요'])
    return dict(score=winners[0]['score'], status='draft',
                rule_ids=[r['id'] for r in winners],
                confidence='low' if any(r['confidence'] == 'low' for r in winners) else 'medium',
                reasons=[r['reason'] for r in winners],
                evidence_ids=sorted({x for r in winners for x in r['evidence_ids']}),
                score_basis=sorted({r['basis'] for r in winners}))


def match_patterns(archive, items, context):
    """Require distinct garments for distinct pattern parts, independent of order."""
    def covered(requirements, remaining):
        if not requirements:
            return True
        part, rest = requirements[0], requirements[1:]
        for n, item in enumerate(remaining):
            if item['garment_id'] in part['garment_ids'] and item['color_id'] in part['color_ids']:
                if covered(rest, remaining[:n] + remaining[n+1:]):
                    return True
        return False
    return [p for p in archive['patterns'] if context_matches(p['scope'], context)
            and covered(p['parts'], list(items))]


def outfit_signature(items):
    return tuple(sorted((i['garment_id'], i['color_id']) for i in items))


def evaluate_outfit(archive, items, context):
    validate_context(context)
    if not items:
        raise ValueError('An outfit must have items')
    ratings = [dict(**i, assessment=score_item(archive, i['garment_id'], i['color_id'], context))
               for i in items]
    patterns = match_patterns(archive, items, context)
    issues = []
    if any(i['assessment']['score'] is not None and i['assessment']['score'] <= 2 for i in ratings):
        issues.append('low_item_realism')
    if any(i['assessment']['score'] is None for i in ratings):
        issues.append('unassessed_or_conflicting_item')
    visible_colors = len({i['color_id'] for i in items})
    if visible_colors >= 4:
        issues.append('four_or_more_colors_review')
    for b in archive['benchmarks']:
        if b['context'] == context and outfit_signature(b['items']) == outfit_signature(items):
            if b['verdict'] == 'owner_rejected':
                issues.append('owner_rejected_exact_outfit')
    # No score sums: daily color coverage cannot offset a low garment score.
    return dict(items=ratings, visible_color_count=visible_colors,
                matched_pattern_ids=[p['id'] for p in patterns],
                pattern_note='부분 배색의 참고 근거이며 전체 코디 승인 점수가 아님',
                issues=issues,
                item_gate='revise' if 'low_item_realism' in issues else 'unknown' if 'unassessed_or_conflicting_item' in issues else 'candidate',
                whole_outfit_status='revise' if 'owner_rejected_exact_outfit' in issues else 'needs_visual_review',
                aesthetic_score=None, production_eligible=False)


def validate_archive(archive):
    def unique(rows):
        ids=[x['id'] for x in rows]
        assert len(ids)==len(set(ids)), 'Duplicate identifiers'
        return set(ids)
    colors=unique(archive['colors']); garments=unique(archive['garments'])
    sources=unique(archive['sources']); obs=unique(archive['observations'])
    unique(archive['rules']); unique(archive['patterns']); unique(archive['benchmarks'])
    unique(archive['review_events'])
    assert len({c['hex'] for c in archive['colors']})==len(colors)
    assert archive['manifest']['production_enabled'] is False
    for o in archive['observations']:
        assert o['source_id'] in sources
        for item in o['items']:
            assert item['garment_id'] is None or item['garment_id'] in garments
            assert item['color_id'] is None or item['color_id'] in colors
    for rule in archive['rules']:
        assert isinstance(rule['score'],int) and 1<=rule['score']<=5
        assert rule['status']=='draft'
        assert set(rule['garment_ids'])<=garments and set(rule['color_ids'])<=colors
        assert set(rule['evidence_ids']) <= obs | {'F01','F02','F03','POLICY-20260916'}
        for key, values in rule['scope'].items():
            assert key in DIMENSIONS and set(values)<=set(DIMENSIONS[key])
    for pattern in archive['patterns']:
        assert set(pattern['evidence_ids'])<=obs
        assert pattern['whole_outfit_approved'] is False
        for part in pattern['parts']:
            assert set(part['garment_ids'])<=garments and set(part['color_ids'])<=colors
    for b in archive['benchmarks']:
        validate_context(b['context'])
        assert all(i['garment_id'] in garments and i['color_id'] in colors for i in b['items'])
    for m in archive['color_mappings']:
        assert m['source_color_id'] in colors and m['target_color_id'] in colors
    return True
