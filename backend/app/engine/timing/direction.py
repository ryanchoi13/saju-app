"""Compare explicit IF-effects with natal prescriptions, never realized fortune.

No inferred opposite element, favorable element count, or majority vote. All
hypotheses remain conditional until their force/function premises are resolved.
"""
from app.engine.core.models import Evidence, EvidenceLayer, ConfidenceLevel
from app.engine.timing.conditions import COMBINATIONS
from app.engine.relationships.functions import compare_balance_function
from app.engine.synthesis.operation_scope import operation_block_reason

VERSION = 'temporal-direction-comparison-v3-function-scope'
SUPPLY_OPERATIONS = {'warm', 'cool', 'moisten', 'dry', 'support'}


def _hypotheses(record):
    c=record.get('checks',{});kind=record.get('type');result=[]
    def add(name, effects, *premises, held_reason=None):
        result.append(dict(name=name,effects=effects,premises=list(premises),
            status='held_back' if held_reason else 'hypothetical',
            held_reason=held_reason))
    control=c.get('control')
    if kind=='stem_control' and control:
        add('control_reduces_target', {control['controlled']:'decrease'},
            'controller_effect_established','target_function_reduced')
        supply=control['mediator_supply']
        if supply['state']!='not_observed':
            add('mediation_functions', {control['mediator']:'mediate'},
                'mediator_usable','mediation_effect_established')
    elif kind=='branch_clash':
        # Either member may be affected. Do not decide the winner by month/count.
        for element in sorted(c.get('member_supply',{})):
            add('clash_reduces_' + element, {element:'decrease'},
                'clash_effect_established','affected_side_identified','target_function_reduced')
            add('clash_activates_' + element, {element:'increase'},
                'clash_effect_established','affected_side_identified','branch_function_activated')
    elif kind in COMBINATIONS:
        target=(c.get('season') or {}).get('target_element')
        if target:
            add('transformation_functions', {target:'increase'},
                'transformation_established','transformed_element_usable',
                held_reason='partial_group_cannot_stand_in_for_complete_transformation'
                    if kind=='branch_half_combination' else None)
        members=record.get('members',[])
        rooted=any(root.get('stem_pillar')==m.get('pillar')
            for m in members if m.get('position')=='visible_stem'
            for supply in c.get('member_supply',{}).values() for root in supply.get('root_links',[]))
        reason=('stem_binding_rule_not_transferable_to_branch_combinations' if kind!='stem_combination' else
                'member_positions_required' if not members else
                'day_master_combination_needs_separate_function_rule' if any(
                    m.get('pillar')=='day' and m.get('position')=='visible_stem' for m in members) else
                'rooted_member_may_retain_original_function' if rooted else
                'root_connection_check_missing' if not c.get('member_supply') or any(
                    'root_links' not in supply for supply in c['member_supply'].values()) else None)
        add('binding_reduces_original_availability',
            {e:'decrease' for e in c.get('member_supply',{})},
            'binding_without_transformation_established','original_functions_reduced',
            held_reason=reason)
    # No effective change is also possible; it prevents a falsely complete verdict.
    if result:
        add('no_effect_established', {}, 'effect_not_established')
    return result


def compare_temporal_directions(conditions, synthesis):
    operations=synthesis.favorable_operations
    synthesis_data=synthesis.model_dump(mode='json')
    blocked={o.get('operation') for o in synthesis.caution_operations}
    conflicts=any(c.get('resolution') in {'preserve_as_unresolved','preserve_partial_result'} and not c.get('operations')
        for c in synthesis.diagnostic_conflicts)
    special=bool(synthesis.overall_structure.get('special_precedence'))
    global_blocks=[]
    if synthesis.confidence.value=='undetermined': global_blocks.append('natal_direction_undetermined')
    if conflicts: global_blocks.append('unresolved_natal_conflict')
    if special: global_blocks.append('special_structure_requires_function_assessment')
    records=[];evidence=[]
    for r in conditions.get('records',[]):
        if r.get('eligibility')!='conditional':
            continue
        hypotheses=_hypotheses(r)
        for target in r.get('checks', {}).get('function_targets', []):
            for change in target.get('possible_changes', []):
                if change not in {'reduced', 'activated'}:
                    continue
                hypotheses.append(dict(name=f"function:{target['target_id']}:{change}", effects={},
                    target_id=target['target_id'], assumed_change=change, status='hypothetical', held_reason=None,
                    premises=['target_function_change_established', 'force_and_root_usability_assessed',
                              'other_relations_resolved', 'natal_balance_direction_still_applicable']))
        unmodeled=[];comparisons=[];seen=set()
        for op in operations:
            name=op.get('operation');elements=op.get('elements',[]);ids=op.get('evidence_ids',[])
            reason=operation_block_reason(op, synthesis_data)
            if reason:
                unmodeled.append(dict(operation=name,reason=reason,evidence_ids=ids));continue
            balance_direction = {'support':'strength_support_direction','drain':'strength_drain_direction'}.get(name) in op.get('source_operations', [])
            if balance_direction and ids and not op.get('side_effects'):
                for target in r.get('checks', {}).get('function_targets', []):
                    for change in target.get('possible_changes', []):
                        relation = compare_balance_function(target, change, name)
                        if not relation:
                            continue
                        hypothesis = f"function:{target['target_id']}:{change}"
                        key = (hypothesis, name, target['element'])
                        provenance = sorted(set(ids + r['evidence_ids']))
                        if key in seen:
                            existing = next(c for c in comparisons if
                                (c['hypothesis'], c['operation'], c['element']) == key)
                            existing['evidence_ids'] = sorted(set(existing['evidence_ids'] + provenance))
                            continue
                        seen.add(key)
                        comparisons.append(dict(hypothesis=hypothesis, operation=name, element=target['element'],
                            relation=relation, status='blocked' if global_blocks else 'conditional',
                            target_id=target['target_id'], role_to_day_master=target['role_to_day_master'],
                            assumed_change=change, comparison_scope='day_master_balance_direction',
                            specific_remedy_confirmed=False,
                            required_premises=['target_function_change_established', 'force_and_root_usability_assessed',
                                               'other_relations_resolved', 'natal_balance_direction_still_applicable'],
                            evidence_ids=provenance))
                # An element-free strength direction is now compared to named
                # functions; it is never converted into an invented element.
                if not elements:
                    if not r.get('checks', {}).get('function_targets'):
                        unmodeled.append(dict(operation=name, reason='function_targets_unavailable', evidence_ids=ids))
                    continue
            if name not in SUPPLY_OPERATIONS | {'mediate'}: reason='operation_needs_function_level_model'
            elif not elements: reason='operation_has_no_explicit_element'
            elif not ids: reason='operation_has_no_provenance'
            elif name in blocked: reason='operation_is_cautioned'
            elif op.get('side_effects'): reason='operation_has_unresolved_side_effects'
            if reason:
                unmodeled.append(dict(operation=name,reason=reason,evidence_ids=ids));continue
            for h in hypotheses:
                if h['status']!='hypothetical':
                    continue
                for element in sorted(set(elements) & set(h['effects'])):
                    effect=h['effects'][element]
                    if name=='mediate' and effect not in {'mediate','decrease'}:
                        continue
                    if name!='mediate' and effect=='mediate':
                        continue
                    key=(h['name'],name,element)
                    if key in seen:
                        existing=next(c for c in comparisons if (c['hypothesis'],c['operation'],c['element'])==key)
                        existing['evidence_ids']=sorted(set(existing['evidence_ids']+ids+r['evidence_ids']))
                        continue
                    seen.add(key)
                    comparisons.append(dict(hypothesis=h['name'],operation=name,element=element,
                        relation='opposes_requested_direction' if effect=='decrease' else 'matches_requested_direction',
                        status='blocked' if global_blocks else 'conditional',
                        required_premises=h['premises']+['usable_for_requested_natal_function']+
                            (['same_conflict_function_as_natal_prescription'] if name=='mediate' else []),
                        evidence_ids=sorted(set(ids+r['evidence_ids']))))
        directions={c['relation'] for c in comparisons if c['status']=='conditional'}
        conclusion=('unresolved' if not directions else 'mixed_by_hypothesis' if len(directions)>1 else
            'conditional_match' if 'matches_requested_direction' in directions else 'conditional_opposition')
        eid='evidence:temporal-direction:' + r['relationship_id']
        record=dict(relationship_id=r['relationship_id'],scope=r['scope'],
            function_targets=r.get('checks', {}).get('function_targets', []),
            hypotheses=hypotheses,comparisons=comparisons,unmodeled_operations=unmodeled,
            held_hypotheses=[dict(name=h['name'],reason=h['held_reason']) for h in hypotheses if h['status']=='held_back'],
            blocking_reasons=list(global_blocks),comparison_summary=conclusion,
            realized_valence='undetermined',effect_assessment_complete=False,
            no_effect_alternative_preserved=bool(hypotheses),
            evidence_ids=[eid],condition_evidence_ids=r['evidence_ids'])
        records.append(record)
        evidence.append(Evidence(id=eid,layer=EvidenceLayer.JUDGMENT,source_module=VERSION,
            rule_code='explicit-effect-vs-prescribed-function',description='가정한 작용과 원국 보완 방향의 조건부 비교',
            source_values=record,supports=[r['relationship_id']],reliability=ConfidenceLevel.LOW))
    return dict(version=VERSION,records=records,realized_valence='undetermined',
        comparison_is_not_event_prediction=True),evidence
