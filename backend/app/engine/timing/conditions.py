"""Temporal relationship condition audit, with no invented strength verdict.

A completed checklist is NOT a completed effect assessment. Reuses fact modules
only: natal adjacency and natal diagnostic thresholds are not reapplied to time.
"""
from app.engine.constants import GAN_WUXING, ZHI_WUXING
from app.engine.core.models import PillarFact, Evidence, EvidenceLayer, ConfidenceLevel
from app.engine.facts.hidden_stems import calculate_hidden_stems
from app.engine.facts.rooting import calculate_roots
from app.engine.facts.relationship_candidates import calculate_relationship_candidates
from app.engine.relationships.functions import describe_function_targets

VERSION = 'temporal-conditions-v2-function-targets'
GENERATES = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
CONTROLS = {'木': '土', '火': '金', '土': '水', '水': '火', '金': '木'}
COMBINATIONS = {'stem_combination', 'branch_six_combination', 'branch_three_combination',
                'branch_directional_combination', 'branch_half_combination'}
SUPPORTED = COMBINATIONS | {'stem_control', 'branch_clash'}


def _member_keys(members):
    return frozenset((m.pillar, m.position, m.symbol) for m in members)


def _supply(element, pillars, hidden, roots):
    visible = sorted(k for k, p in pillars.items() if p.stem_element == element)
    root_links = [r.model_dump(mode='json') for r in roots.items if r.element == element]
    hidden_positions = [dict(pillar=k, stem=h.stem, role=h.role.value)
        for k, branch in hidden.items() for h in branch.stems if h.element == element]
    return dict(element=element, visible_pillars=visible, hidden_positions=hidden_positions,
        root_links=root_links, state='visible_with_root_connections' if visible and root_links else
        'visible_only' if visible else 'hidden_only' if hidden_positions else 'not_observed',
        root_usability='unresolved', quantity_is_not_force=True)


def assess_temporal_conditions(natal, timing, synthesis):
    pillars = {k: p for k, p in natal.items() if p is not None}
    axis_items = [('luck_cycle', timing.luck_cycle.get('current')),
                  ('annual', timing.annual), ('monthly', timing.monthly), ('daily', timing.daily)]
    for axis, value in axis_items:
        if value and value.get('pillar'):
            pillars['timing:' + axis] = PillarFact.model_validate(value['pillar'])
    hidden = calculate_hidden_stems(pillars)
    roots = calculate_roots(pillars, hidden)
    canonical = calculate_relationship_candidates(pillars).items
    by_id = {c.id: c for c in canonical}
    # Precompute supply once; observations are not accumulated as force scores.
    supplies = {e: _supply(e, pillars, hidden, roots) for e in GENERATES}
    records=[]; evidence=[]
    versions={}
    for raw in timing.relationship_changes:
        fingerprint=(raw.get("type"), raw.get("target_element"), tuple(sorted(
            (m.get("pillar", ""), m.get("position", ""), m.get("symbol", "")) for m in raw.get("members", []))))
        versions.setdefault(raw.get("relationship_id"), set()).add(fingerprint)
    conflicting_ids={rid for rid, fingerprints in versions.items() if len(fingerprints)>1}
    seen=set()
    for raw in timing.relationship_changes:
        relationship_id=raw.get('relationship_id')
        signature=(relationship_id, raw.get('type'), tuple(sorted(
            (m.get('pillar',''),m.get('position',''),m.get('symbol','')) for m in raw.get('members',[]))))
        if relationship_id in seen:
            continue
        seen.add(relationship_id)
        c=by_id.get(relationship_id)
        valid=bool(relationship_id not in conflicting_ids and c and c.type.value == raw.get('type') and
            sorted((m.pillar,m.position,m.symbol) for m in c.members) == list(signature[2]) and
            c.target_element == raw.get('target_element') and
            any(m.pillar.startswith('timing:') for m in c.members))
        eid='evidence:temporal-condition:' + str(relationship_id)
        if not valid:
            records.append(dict(relationship_id=relationship_id, eligibility='rejected',
                reason='candidate_does_not_match_current_pillars', evidence_ids=[eid],
                effect_status='unresolved', requires_reassessment=True))
            evidence.append(Evidence(id=eid,layer=EvidenceLayer.TIMING,source_module=VERSION,
                rule_code='validate-candidate-members',description='현재 기둥과 일치하지 않는 관계 후보 제외',
                source_values={'relationship_id':relationship_id},supports=[],reliability=ConfidenceLevel.HIGH))
            continue
        kind=c.type.value
        keys=_member_keys(c.members)
        overlaps=[o for o in canonical if o.id != c.id and keys & _member_keys(o.members)]
        overlap_records=[dict(relationship_id=o.id,type=o.type.value,
            shared_members=sorted(keys & _member_keys(o.members)),competition_status='unresolved') for o in overlaps]
        elements=sorted({GAN_WUXING[m.symbol] if m.position=='visible_stem' else ZHI_WUXING[m.symbol] for m in c.members})
        member_supply={e:supplies[e] for e in elements}
        target=c.target_element
        month= pillars.get('timing:monthly')
        natal_month=natal.get('month')
        season=dict(natal_month_branch=natal_month.branch if natal_month else None,
            current_month_branch=month.branch if month else None,
            target_element=target,
            natal_month_element_matches_target=(natal_month.branch_element == target) if target and natal_month else None,
            current_month_element_matches_target=(month.branch_element == target) if target and month else None,
            strength_conclusion='unresolved')
        control=None
        if kind=='stem_control':
            left,right=[GAN_WUXING[m.symbol] for m in c.members]
            controller,controlled=(left,right) if CONTROLS[left]==right else (right,left)
            mediator=GENERATES[controller]
            control=dict(controller=controller,controlled=controlled,
                mediator=mediator,mediator_supply=supplies[mediator],
                mediation_status='unresolved',winner='unresolved')
        unknown=['temporal_force_and_root_usability','shared_relation_effects',
                 'natal_function_change_and_valence']
        if not overlaps:
            unknown.remove('shared_relation_effects')
        if kind in COMBINATIONS:
            unknown.append('transformation_formation_conditions')
            if target is None:
                unknown.append('transformation_target_not_defined_by_fact_rule')
        if kind not in SUPPORTED:
            unknown.append('relationship_type_condition_policy_not_defined')
        if natal.get('hour') is None:
            unknown.append('missing_birth_hour')
        checks=dict(current_members='confirmed',
            function_targets=describe_function_targets(kind,
                [m.model_dump(mode='json') for m in c.members], pillars, roots),
            natal_adjacency='not_applicable_to_temporal_relation',
            member_supply=member_supply,season=season,overlaps=overlap_records,
            control=control,
            target_supply=supplies[target] if target else None,
            formation='partial_group' if kind=='branch_half_combination' else
                'complete_symbol_group' if kind in {'branch_three_combination','branch_directional_combination'} else 'direct_pair',
            natal_context=dict(confidence=synthesis.confidence.value,
                favorable_operation_ids=sorted({eid for o in synthesis.favorable_operations for eid in o.get('evidence_ids',[])}),
                caution_operations=synthesis.caution_operations,
                daily_valence_inferred=False))
        record=dict(relationship_id=c.id,type=kind,
            members=[m.model_dump(mode='json') for m in c.members],
            scope='daily' if any(m.pillar=='timing:daily' for m in c.members) else 'background',
            eligibility='conditional' if kind in SUPPORTED else 'held_back',
            checklist_evaluated=True, checks=checks, unresolved_conditions=unknown,
            effect_status='unresolved', transformation_status='unresolved' if kind in COMBINATIONS else 'not_applicable',
            valence='undetermined', requires_reassessment=True,evidence_ids=[eid])
        records.append(record)
        evidence.append(Evidence(id=eid,layer=EvidenceLayer.TIMING,source_module=VERSION,
            rule_code='separate-temporal-conditions-from-effects',
            description='시간축 관계의 구성·통근 연결·계절·겹침·미해결 조건 분리',
            source_values=record,supports=[c.id],reliability=ConfidenceLevel.LOW))
    return dict(version=VERSION,records=records,effect_assessment_complete=False,
        daily_completed_effects=0,
        checklist_evaluated_count=sum(r.get('checklist_evaluated',False) for r in records)), evidence
