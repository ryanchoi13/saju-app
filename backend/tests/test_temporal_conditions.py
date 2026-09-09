from copy import deepcopy
from unittest import TestCase
from app.engine.core.models import TimingResult, SynthesisResult
from app.engine.timing.engine import _pillar, _relationship_changes
from app.engine.timing.conditions import assess_temporal_conditions
from app.engine.services.daily_scenarios import select_daily_scenario
from app.engine.timing.observations import observe_temporal_structure


def timing_for(natal, overlays):
    values={k:dict(pillar=v.model_dump(mode='json')) for k,v in overlays.items()}
    return TimingResult(**values,relationship_changes=_relationship_changes(natal,overlays))


class TemporalConditionTests(TestCase):
    def setUp(self):
        self.natal=dict(year=_pillar('甲申'),month=_pillar('丙子'),day=_pillar('戊午'),hour=None)
        self.overlays=dict(monthly=_pillar('庚申'),daily=_pillar('甲辰'))
        self.timing=timing_for(self.natal,self.overlays)
        self.synthesis=SynthesisResult(confidence='high')

    def assess(self):
        return assess_temporal_conditions(self.natal,self.timing,self.synthesis)

    def test_complete_group_and_matching_month_do_not_establish_transformation(self):
        before=deepcopy((self.natal,self.timing,self.synthesis))
        result,evidence=self.assess()
        group=next(r for r in result['records'] if r.get('type')=='branch_three_combination')
        self.assertEqual(group['checks']['formation'],'complete_symbol_group')
        self.assertTrue(group['checks']['season']['natal_month_element_matches_target'])
        self.assertFalse(group['checks']['season']['current_month_element_matches_target'])
        self.assertEqual(group['transformation_status'],'unresolved')
        self.assertEqual(group['checks']['natal_adjacency'],'not_applicable_to_temporal_relation')
        self.assertIn('missing_birth_hour',group['unresolved_conditions'])
        self.assertEqual((self.natal,self.timing,self.synthesis),before)
        self.assertTrue(all(e.reliability.value != 'high' for e in evidence))

    def test_mediation_presence_is_not_success_or_favorable_valence(self):
        result,_=self.assess()
        r=next(r for r in result['records'] if r.get('checks',{}).get('control',{} ) and r['checks']['control']['controller']=='木')
        control=r['checks']['control']
        self.assertEqual(control['controlled'],'土')
        self.assertEqual(control['mediator'],'火')
        self.assertEqual(control['mediator_supply']['state'],'visible_with_root_connections')
        self.assertEqual(control['mediation_status'],'unresolved')
        self.assertEqual(r['valence'],'undetermined')
        self.assertTrue(r['requires_reassessment'])

    def test_current_month_changes_condition_without_overwriting_birth_month(self):
        first,_=self.assess()
        self.overlays['monthly']=_pillar('壬子')
        self.timing=timing_for(self.natal,self.overlays)
        second,_=self.assess()
        a=next(r for r in first['records'] if r.get('type')=='branch_three_combination')
        b=next(r for r in second['records'] if r.get('relationship_id')==a['relationship_id'])
        self.assertFalse(a['checks']['season']['current_month_element_matches_target'])
        self.assertTrue(b['checks']['season']['current_month_element_matches_target'])
        self.assertEqual(a['checks']['season']['natal_month_branch'],b['checks']['season']['natal_month_branch'])
        self.assertEqual(b['effect_status'],'unresolved')

    def test_stale_candidate_is_rejected(self):
        raw=self.timing.relationship_changes[0]
        rid=raw['relationship_id']
        raw['members'][0]['symbol']='癸'
        result,_=self.assess()
        r=next(r for r in result['records'] if r['relationship_id']==rid)
        self.assertEqual(r['eligibility'],'rejected')
        self.assertFalse(result['effect_assessment_complete'])

    def test_duplicate_candidates_do_not_add_independent_evidence(self):
        first,e1=self.assess()
        self.timing.relationship_changes+=deepcopy(self.timing.relationship_changes)
        second,e2=self.assess()
        self.assertEqual(first,second)
        self.assertEqual(e1,e2)
        ids=[e.id for e in e2]
        self.assertEqual(len(ids),len(set(ids)))

    def test_overlap_does_not_mean_competition_or_a_winner(self):
        result,_=self.assess()
        overlapping=[r for r in result['records'] if r.get('checks',{}).get('overlaps')]
        self.assertTrue(overlapping)
        for r in overlapping:
            self.assertTrue(all(o['competition_status']=='unresolved' for o in r['checks']['overlaps']))
            self.assertIn('shared_relation_effects',r['unresolved_conditions'])

    def test_empty_or_rejected_condition_records_cannot_nominate_scene(self):
        observations=observe_temporal_structure(self.natal,self.overlays)
        q=dict(synthesis=dict(confidence='medium'),timing=dict(daily=dict(ten_god='direct_wealth')),
            activated_state=dict(temporal_observations=observations))
        # No new layer preserves the prior conditional editor for older payloads.
        self.assertIsNotNone(select_daily_scenario(q))
        q['activated_state']['temporal_conditions']=dict(version='temporal-conditions-v1',records=[])
        self.assertIsNone(select_daily_scenario(q))

    def test_conflicting_duplicates_reject_id_regardless_of_order(self):
        raw=deepcopy(self.timing.relationship_changes[0])
        raw['members'][0]['symbol']='癸'
        self.timing.relationship_changes.append(raw)
        first,evidence=self.assess()
        self.timing.relationship_changes.reverse()
        second,_=self.assess()
        def selected(result):
            return next(r for r in result['records'] if r['relationship_id']==raw['relationship_id'])
        self.assertEqual(selected(first),selected(second))
        self.assertEqual(selected(first)['eligibility'],'rejected')
        self.assertEqual(len(evidence),len({e.id for e in evidence}))
