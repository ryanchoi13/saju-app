"""Separate natal/background context from daily evidence without promoting candidates.

The current resolver is natal-only. These gates deliberately do not pretend
that timing relationships have completed diagnostics or transformation checks.
"""


def daily_relationship_evidence(query):
    changes = (query.get('activated_state') or {}).get('relationship_changes', [])
    conditions = (query.get('activated_state') or {}).get('temporal_conditions') or {}
    records = {r.get('relationship_id'): r for r in conditions.get('records', [])}
    groups = {}
    background_ids = []
    for item in changes:
        members = item.get('members', [])
        if not any(m.get('pillar') == 'timing:daily' for m in members):
            if item.get('relationship_id'):
                background_ids.append(item['relationship_id'])
            continue
        key = tuple(sorted((m.get('pillar', ''), m.get('position', ''), m.get('symbol', '')) for m in members))
        group = groups.setdefault(key, {'members': members, 'candidates': [], 'assessed': []})
        record = records.get(item.get('relationship_id'), {})
        record_key = tuple(sorted((m.get('pillar', ''), m.get('position', ''), m.get('symbol', ''))
                                  for m in record.get('members', [])))
        # Activity is not valence. Only a matching, completed function/effect
        # assessment can justify a benefit or warning in the daily copy.
        assessed = (record_key == key and record.get('type') == item.get('type')
                    and record.get('checklist_evaluated') is True
                    and record.get('eligibility') not in {None, 'rejected', 'held_back'}
                    and record.get('effect_status') == 'established'
                    and record.get('valence') in {'beneficial', 'adverse', 'mixed', 'neutral'}
                    and record.get('requires_reassessment') is False
                    and bool(record.get('evidence_ids')))
        bucket = 'assessed' if assessed else 'candidates'
        signature = (item.get('relationship_id'), item.get('type'))
        if not any((r.get('relationship_id'), r.get('type')) == signature for r in group[bucket]):
            group[bucket].append({**item, 'valence': record['valence'],
                                  'effect_status': record['effect_status'],
                                  'evidence_ids': record['evidence_ids']} if assessed else item)
    return {'groups': list(groups.values()), 'background_ids': list(dict.fromkeys(background_ids)),
            'assessed': [r for g in groups.values() for r in g['assessed']],
            'cautions': [r for g in groups.values() for r in g['assessed'] if r['valence'] in {'adverse', 'mixed'}],
            'benefits': [r for g in groups.values() for r in g['assessed'] if r['valence'] == 'beneficial'],
            'candidates': [r for g in groups.values() for r in g['candidates']],
            'candidate_group_count': sum(bool(g['candidates']) for g in groups.values()),
            'assessment_complete': bool(groups) and all(not g['candidates'] for g in groups.values())}
