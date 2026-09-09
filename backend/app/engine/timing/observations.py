"""Reproducible temporal structure, separate from unresolved effects/valence.

Never promotes a relationship candidate to active. Snapshots and member roles
allow editorial advice to name a conditional situation without claiming events.
"""
from app.engine.facts.relationship_candidates import calculate_relationship_candidates
from app.engine.facts.hidden_stems import get_hidden_stems
from app.engine.facts.ten_gods import get_ten_god

VERSION = 'temporal-observations-v1'


def observe_temporal_structure(natal, overlays):
    combined = {k: v for k, v in natal.items() if v is not None}
    day_master = combined['day'].stem
    snapshots = []
    previous = set()
    daily_records = []
    for axis in ('luck_cycle', 'annual', 'monthly', 'daily'):
        if axis not in overlays:
            continue
        combined['timing:' + axis] = overlays[axis]
        candidates = calculate_relationship_candidates(combined).items
        records = []
        current = set()
        for c in candidates:
            if not any(m.pillar.startswith('timing:') for m in c.members):
                continue
            current.add(c.id)
            if axis != 'daily' or not any(m.pillar == 'timing:daily' for m in c.members):
                continue
            anchors = []
            for m in c.members:
                if m.pillar == 'timing:daily':
                    continue
                stem = m.symbol if m.position == 'visible_stem' else get_hidden_stems(m.symbol).stems[0].stem
                anchors.append(dict(pillar=m.pillar, position=m.position,
                    symbol=m.symbol, ten_god=get_ten_god(day_master, stem).value,
                    ten_god_basis='visible_stem' if m.position == 'visible_stem' else 'branch_main_hidden_stem',
                    natal=not m.pillar.startswith('timing:')))
            records.append(dict(id='observation:' + c.id, relationship_id=c.id,
                type=c.type.value, members=[m.model_dump(mode='json') for m in c.members],
                anchors=anchors, rule_code=c.rule_code,
                structure_status='observed', effect_status='unresolved',
                transformation_status='unresolved', valence='undetermined',
                event_domain='unresolved', newly_introduced=c.id not in previous))
        snapshots.append(dict(axis=axis, relationship_ids=sorted(current),
            introduced_ids=sorted(current - previous)))
        previous = current
        if axis == 'daily':
            daily_records = records
    # Shared members are recorded as overlap, never automatically competition.
    for r in daily_records:
        members = {(m['pillar'], m['position'], m['symbol']) for m in r['members']}
        r['overlapping_ids'] = [o['id'] for o in daily_records if o['id'] != r['id'] and
            members.intersection((m['pillar'], m['position'], m['symbol']) for m in o['members'])]
    return dict(version=VERSION, snapshots=snapshots, daily_observations=daily_records,
        natal_month_branch=natal['month'].branch,
        current_month_branch=overlays['monthly'].branch if 'monthly' in overlays else None,
        daily_branch_ten_god=get_ten_god(day_master, get_hidden_stems(overlays['daily'].branch).stems[0].stem).value if 'daily' in overlays else None,
        effect_assessment_complete=False)
