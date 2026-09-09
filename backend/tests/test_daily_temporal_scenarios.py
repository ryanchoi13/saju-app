from copy import deepcopy
from datetime import date, time, timedelta
from unittest import TestCase
from unittest.mock import patch

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.semantic.queries import build_service_query
from app.engine.services.daily import build_daily_fortune
from app.engine.services.daily_evidence import daily_relationship_evidence
from app.engine.services.daily_scenarios import select_daily_scenario
from app.engine.services.daily_topics import select_daily_topics
from app.engine.timing.engine import _pillar
from app.engine.timing.observations import observe_temporal_structure


class TemporalStructureTests(TestCase):
    def test_daily_completes_group_without_claiming_transformation_or_mutating_natal(self):
        natal = dict(year=_pillar('甲申'), month=_pillar('丙子'), day=_pillar('戊午'), hour=None)
        before = deepcopy(natal)
        result = observe_temporal_structure(natal, dict(annual=_pillar('辛酉'), monthly=_pillar('壬寅'), daily=_pillar('甲辰')))
        self.assertEqual(natal, before)
        self.assertEqual(result['natal_month_branch'], '子')
        self.assertEqual(result['current_month_branch'], '寅')
        group = next(r for r in result['daily_observations'] if r['type'] == 'branch_three_combination' and {m['symbol'] for m in r['members']} == set('申子辰'))
        self.assertTrue(group['newly_introduced'])
        self.assertEqual(group['effect_status'], 'unresolved')
        self.assertEqual(group['valence'], 'undetermined')
        self.assertEqual(group['transformation_status'], 'unresolved')
        self.assertNotIn(group['relationship_id'], result['snapshots'][-2]['relationship_ids'])
        self.assertIn(group['relationship_id'], result['snapshots'][-1]['introduced_ids'])
        self.assertTrue(all(a['pillar'] != 'hour' for r in result['daily_observations'] for a in r['anchors']))

    def test_duplicate_and_reordered_observations_do_not_change_selection(self):
        q = scenario_query()
        before = select_daily_scenario(q)
        records = q['activated_state']['temporal_observations']['daily_observations']
        records[:] = list(reversed(records + deepcopy(records)))
        self.assertEqual(before, select_daily_scenario(q))

    def test_background_cannot_nominate_subject_and_candidates_stay_unresolved(self):
        q = scenario_query()
        for r in q['activated_state']['temporal_observations']['daily_observations']:
            for a in r['anchors']:
                a['natal'] = False
        self.assertIsNone(select_daily_scenario(q))
        q = scenario_query()
        self.assertEqual(daily_relationship_evidence(q)['assessed'], [])
        self.assertFalse(select_daily_scenario(q)['evidence']['strongest_fortune_domain_claim'])

    def test_date_string_does_not_rotate_copy_and_unknown_input_does_not_get_scene(self):
        q = scenario_query(); before = deepcopy(q)
        result = select_daily_scenario(q)
        self.assertEqual(q, before)
        q['timing']['daily']['date'] = '2099-12-31'
        self.assertEqual(result, select_daily_scenario(q))
        q['synthesis']['confidence'] = 'undetermined'
        self.assertIsNone(select_daily_scenario(q))

    def test_daily_subject_changes_action_not_only_wording(self):
        q = scenario_query()
        q['timing']['daily']['ten_god'] = 'direct_resource'
        learning = select_daily_scenario(q)
        q['timing']['daily']['ten_god'] = 'eating_god'
        enjoyment = select_daily_scenario(q)
        self.assertEqual(learning['evidence']['observation_ids'], enjoyment['evidence']['observation_ids'])
        self.assertIn('강의', learning['unified_advice'])
        self.assertIn('취미', enjoyment['unified_advice'])
        self.assertNotEqual(learning['time_flow'], enjoyment['time_flow'])

    def test_shared_join_and_clash_are_mixed_without_declaring_a_winner(self):
        q = scenario_query()
        records = q['activated_state']['temporal_observations']['daily_observations']
        clash = deepcopy(records[0]); clash.update(id='clash:example', type='branch_clash', rule_code='branch-clash')
        records.append(clash)
        result = select_daily_scenario(q)
        self.assertEqual(result['evidence']['mode'], 'mixed')
        self.assertEqual(result['evidence']['valence'], 'undetermined')

    def test_affected_natal_function_can_nominate_subject_without_inventing_valence(self):
        q=scenario_query()
        observation=q['activated_state']['temporal_observations']['daily_observations'][0]
        observation['relationship_id']='r1'
        before=select_daily_scenario(q)
        q['activated_state']['temporal_conditions']={'version':'temporal-conditions-v2-function-targets','records':[
            dict(relationship_id='r1',eligibility='conditional',evidence_ids=['condition:r1'],checks=dict(function_targets=[
                dict(target_id='root:year:甲:to:month',stem_pillar='month',role_to_day_master='direct_resource',function_kind='root_support')]))]}
        # The daily branch preference would otherwise keep the money subject.
        q['activated_state']['temporal_observations']['daily_branch_ten_god']='direct_resource'
        after=select_daily_scenario(q)
        self.assertEqual(before['evidence']['family'],'money')
        self.assertEqual(after['evidence']['family'],'learning')
        self.assertEqual(after['evidence']['function_target_ids'],['root:year:甲:to:month'])
        self.assertEqual(after['evidence']['valence'],'undetermined')


class DailyScenarioIntegrationTests(TestCase):
    def test_one_selection_is_shared_by_title_body_and_guidance(self):
        birth=BirthInput(name='테스트',gender='male',birth_date=date(1978,3,13),birth_time=time(11))
        target=date(2026,9,9)
        core=calculate_myeongri_core(birth,target_date=target)
        with patch('app.engine.services.daily.select_daily_scenario', wraps=select_daily_scenario) as selector:
            output=build_daily_fortune(core,'테스트',target)
        self.assertEqual(selector.call_count,1)
        self.assertEqual(output['evidence_summary']['topics']['scenario'],output['evidence_summary']['guidance']['scenario'])
        ids={e.id for e in core.evidence}
        q=build_service_query(core,'daily_overall')
        self.assertTrue(any(r['checks'].get('function_targets') for r in q['activated_state']['temporal_conditions']['records']
                            if r.get('checklist_evaluated')))
        self.assertTrue(any(r['function_targets'] for r in q['natal']['relationships']))
        scenario=output['evidence_summary']['topics']['scenario']
        if scenario:
            self.assertTrue(set(scenario['condition_evidence_ids'])<=ids)
            self.assertTrue(scenario['function_targets_are_conditional'])

    def test_thirty_days_are_deterministic_and_not_a_ten_day_template_cycle(self):
        birth = BirthInput(name='테스트', gender='male', birth_date=date(1978, 3, 13), birth_time=time(11))
        results=[]; removed_changes=0
        for i in range(30):
            d=date(2026, 9, 9)+timedelta(days=i)
            core=calculate_myeongri_core(birth,target_date=d)
            before=core.model_dump(mode='json')
            r=build_daily_fortune(core,'테스트',d)
            self.assertEqual(r,build_daily_fortune(core,'테스트',d))
            self.assertEqual(before,core.model_dump(mode='json'))
            q=build_service_query(core,'daily_overall')
            actual=select_daily_topics(q,[],[])
            q['activated_state']['temporal_observations']={}
            removed_changes+=actual['title'] != select_daily_topics(q,[],[])['title']
            self.assertEqual(r['evidence_summary']['topics']['scenario'],r['evidence_summary']['guidance']['scenario'])
            results.append(r)
        self.assertGreater(removed_changes,0)
        self.assertTrue(any(results[i]['title'] != results[i+10]['title'] for i in range(20)))
        self.assertTrue(any(results[i]['unified_advice'] != results[i+10]['unified_advice'] for i in range(20)))


def scenario_query():
    # An observed combination connected to a natal wealth stem. Effect remains unknown.
    return dict(synthesis=dict(confidence='medium'), timing=dict(daily=dict(ten_god='direct_resource')),
        activated_state=dict(temporal_observations=dict(version='temporal-observations-v1', daily_branch_ten_god='direct_wealth',
            daily_observations=[dict(id='observed:wealth', type='stem_combination', rule_code='stem-combination',
                structure_status='observed', newly_introduced=True,
                members=[dict(pillar='timing:daily')], anchors=[dict(natal=True,ten_god='direct_wealth')])])) )
