from copy import deepcopy
from unittest import TestCase
from app.engine.core.models import SynthesisResult
from app.engine.timing.direction import compare_temporal_directions


def condition(kind='stem_control'):
    return dict(records=[dict(relationship_id='r1',type=kind,scope='daily',eligibility='conditional',
        evidence_ids=['condition:r1'],members=[dict(pillar='year',position='visible_stem',symbol='壬'),dict(pillar='timing:daily',position='visible_stem',symbol='丁')],checks=dict(
            control=dict(controller='土',controlled='水',mediator='金',mediator_supply=dict(state='visible_only')),
            member_supply={'水':{'root_links':[]},'土':{'root_links':[]}},season=dict(target_element='水')))])


def natal(operation='moisten',element='水'):
    return SynthesisResult(confidence='medium',favorable_operations=[dict(operation=operation,
        elements=[element],evidence_ids=['natal:1'])])


class TemporalDirectionTests(TestCase):
    def test_reducing_requested_element_is_conditional_opposition_not_bad_fortune(self):
        c=condition();s=natal();before=deepcopy((c,s))
        result,_=compare_temporal_directions(c,s)
        r=result['records'][0]
        self.assertEqual(r['comparison_summary'],'conditional_opposition')
        self.assertEqual(r['realized_valence'],'undetermined')
        self.assertTrue(r['no_effect_alternative_preserved'])
        self.assertEqual((c,s),before)

    def test_combination_can_match_and_oppose_under_different_hypotheses(self):
        result,_=compare_temporal_directions(condition('stem_combination'),natal())
        r=result['records'][0]
        self.assertEqual(r['comparison_summary'],'mixed_by_hypothesis')
        self.assertEqual({c['hypothesis'] for c in r['comparisons']},
            {'transformation_functions','binding_reduces_original_availability'})
        self.assertEqual(r['realized_valence'],'undetermined')

    def test_mediation_requires_explicit_prescription_and_not_just_same_element(self):
        result,_=compare_temporal_directions(condition(),natal('mediate','金'))
        self.assertEqual(result['records'][0]['comparison_summary'],'conditional_match')
        result,_=compare_temporal_directions(condition(),natal('cool','金'))
        self.assertEqual(result['records'][0]['comparison_summary'],'unresolved')

    def test_missing_element_or_provenance_does_not_infer_a_direction(self):
        s=natal();s.favorable_operations[0]['elements']=[]
        result,_=compare_temporal_directions(condition(),s)
        self.assertEqual(result['records'][0]['comparisons'],[])
        s=natal();s.favorable_operations[0]['evidence_ids']=[]
        result,_=compare_temporal_directions(condition(),s)
        self.assertEqual(result['records'][0]['comparisons'],[])

    def test_conflict_special_structure_and_unknown_confidence_block_conclusion(self):
        for change in ('conflict','special','unknown'):
            s=natal()
            if change=='conflict': s.diagnostic_conflicts=[dict(resolution='preserve_as_unresolved')]
            if change=='special': s.overall_structure=dict(special_precedence=True)
            if change=='unknown': s=SynthesisResult(confidence='undetermined',favorable_operations=s.favorable_operations)
            result,_=compare_temporal_directions(condition(),s)
            self.assertEqual(result['records'][0]['comparison_summary'],'unresolved')
            self.assertTrue(result['records'][0]['blocking_reasons'])

    def test_cautioned_or_side_effect_operation_is_not_used(self):
        for side_effect in (False,True):
            s=natal()
            if side_effect:s.favorable_operations[0]['side_effects']=['requires_check']
            else:s.caution_operations=[dict(operation='moisten')]
            result,_=compare_temporal_directions(condition(),s)
            self.assertEqual(result['records'][0]['comparisons'],[])

    def test_duplicate_prescription_is_not_counted_twice(self):
        s=natal();a,_=compare_temporal_directions(condition(),s)
        s.favorable_operations+=deepcopy(s.favorable_operations)
        b,_=compare_temporal_directions(condition(),s)
        self.assertEqual(a,b)

    def test_rejected_candidates_have_no_comparison(self):
        c=condition();c['records'][0]['eligibility']='rejected'
        result,evidence=compare_temporal_directions(c,natal())
        self.assertEqual(result['records'],[])
        self.assertEqual(evidence,[])

    def test_shared_comparison_merges_provenance_without_adding_a_vote(self):
        s=natal()
        other=deepcopy(s.favorable_operations[0]);other['evidence_ids']=['natal:2']
        s.favorable_operations.append(other)
        result,_=compare_temporal_directions(condition(),s)
        comparisons=result['records'][0]['comparisons']
        self.assertEqual(len(comparisons),1)
        self.assertEqual(comparisons[0]['evidence_ids'],['condition:r1','natal:1','natal:2'])

    def test_clash_preserves_reduction_and_activation_alternatives(self):
        result,_=compare_temporal_directions(condition('branch_clash'),natal())
        r=result['records'][0]
        self.assertEqual(r['comparison_summary'],'mixed_by_hypothesis')
        self.assertEqual({x['hypothesis'] for x in r['comparisons']},{'clash_reduces_水','clash_activates_水'})
        self.assertEqual(r['realized_valence'],'undetermined')

    def test_day_master_combination_cannot_use_generic_binding_loss(self):
        c=condition('stem_combination');c['records'][0]['members'][0]['pillar']='day'
        result,_=compare_temporal_directions(c,natal())
        r=result['records'][0]
        self.assertNotIn('binding_reduces_original_availability',{x['hypothesis'] for x in r['comparisons']})
        self.assertEqual(r['held_hypotheses'][0]['reason'],'day_master_combination_needs_separate_function_rule')

    def test_root_connection_prevents_unqualified_binding_loss(self):
        c=condition('stem_combination')
        c['records'][0]['checks']['member_supply']['水']={'root_links':[{'stem_pillar':'year'}]}
        result,_=compare_temporal_directions(c,natal())
        self.assertEqual(result['records'][0]['held_hypotheses'][0]['reason'],'rooted_member_may_retain_original_function')
        self.assertNotIn('binding_reduces_original_availability',{x['hypothesis'] for x in result['records'][0]['comparisons']})

    def test_half_group_cannot_claim_complete_transformation_or_stem_binding(self):
        result,_=compare_temporal_directions(condition('branch_half_combination'),natal())
        r=result['records'][0]
        self.assertEqual(r['comparisons'],[])
        self.assertEqual(len(r['held_hypotheses']),2)
        self.assertTrue(r['no_effect_alternative_preserved'])

    def test_complete_branch_group_does_not_inherit_stem_binding(self):
        result,_=compare_temporal_directions(condition('branch_three_combination'),natal())
        r=result['records'][0]
        self.assertEqual({x['hypothesis'] for x in r['comparisons']},{'transformation_functions'})
        self.assertEqual(r['realized_valence'],'undetermined')

    def test_missing_root_check_is_not_treated_as_absence_of_roots(self):
        c=condition('stem_combination')
        del c['records'][0]['checks']['member_supply']['水']['root_links']
        result,_=compare_temporal_directions(c,natal())
        r=result['records'][0]
        self.assertNotIn('binding_reduces_original_availability',{x['hypothesis'] for x in r['comparisons']})
        self.assertEqual(r['held_hypotheses'][0]['reason'],'root_connection_check_missing')

    def test_function_direction_without_element_is_conditional_and_targeted(self):
        c=condition('branch_clash')
        c['records'][0]['checks']['function_targets']=[dict(target_id='root:day:甲',element='木',
            role_to_day_master='day_master',balance_role='supports_day',possible_changes=['retained','reduced','activated'])]
        s=natal('support');s.favorable_operations[0].update(elements=[],source_operations=['strength_support_direction'])
        result,_=compare_temporal_directions(c,s)
        record=result['records'][0]
        self.assertEqual(record['comparison_summary'],'mixed_by_hypothesis')
        self.assertEqual({x['assumed_change'] for x in record['comparisons']},{'reduced','activated'})
        self.assertTrue(all(x['comparison_scope']=='day_master_balance_direction' for x in record['comparisons']))
        self.assertTrue(all(not x['specific_remedy_confirmed'] for x in record['comparisons']))
        self.assertEqual(record['realized_valence'],'undetermined')

    def test_known_unrelated_conflict_keeps_comparison_but_related_one_blocks_it(self):
        s=natal()
        s.diagnostic_conflicts=[dict(operations=['support','drain'],resolution='preserve_as_unresolved')]
        result,_=compare_temporal_directions(condition(),s)
        self.assertEqual(result['records'][0]['comparison_summary'],'conditional_opposition')
        s.diagnostic_conflicts[0]['operations']=['moisten','dry']
        result,_=compare_temporal_directions(condition(),s)
        self.assertEqual(result['records'][0]['comparisons'],[])
