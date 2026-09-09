"""Function mapping tests; no assertion of historical event prediction."""
from copy import deepcopy
from unittest import TestCase

from app.engine.facts.hidden_stems import calculate_hidden_stems
from app.engine.facts.rooting import calculate_roots, calculate_exposed_stems
from app.engine.facts.relationship_candidates import calculate_relationship_candidates
from app.engine.relationships.resolver import resolve_relationships
from app.engine.relationships.functions import compare_balance_function
from app.engine.timing.engine import _pillar


def relationships(chart):
    pillars = dict(zip(('year','month','day','hour'),map(_pillar,chart)))
    hidden = calculate_hidden_stems(pillars)
    return resolve_relationships(calculate_relationship_candidates(pillars),pillars,
        calculate_roots(pillars,hidden),calculate_exposed_stems(pillars,hidden))[0]


class RelationshipFunctionTests(TestCase):
    def test_day_master_combination_does_not_erase_officer_or_wealth_identity(self):
        # 子平真詮評注 V: two explicit examples of the day master's own union.
        for chart, expected in [(['戊戌','甲子','己巳','戊辰'],'direct_officer'),
                                (['戊寅','己未','甲寅','乙亥'],'direct_wealth')]:
            result=next(r for r in relationships(chart) if r.type=='stem_combination'
                        and {m['pillar'] for m in r.members}=={'month','day'})
            partner=next(t for t in result.function_targets if t['stem_pillar']=='month')
            self.assertEqual(partner['role_to_day_master'],expected)
            self.assertEqual(partner['possible_changes'],['retained'])
            self.assertEqual(partner['original_role_policy'],'not_removed_by_day_master_combination_alone')
            self.assertEqual(partner['effect_status'],'unresolved')

    def test_rooted_other_stem_combination_preserves_both_role_alternatives(self):
        result=next(r for r in relationships(['癸未','辛酉','甲申','丙寅'])
                    if r.type=='stem_combination')
        self.assertTrue(all(t['possible_changes']==['retained','reduced'] for t in result.function_targets))
        self.assertTrue(all(t['actual_valence']=='undetermined' for t in result.function_targets))

    def test_clash_traces_hidden_roles_and_connected_natal_roots(self):
        # 子平真詮評注 VII explicitly discusses useful clashes in this chart.
        # We test the affected functions, not certify its entire interpretation.
        rs=relationships(['辛卯','丁酉','庚午','丙子'])
        clash=next(r for r in rs if r.type=='branch_clash' and {m['symbol'] for m in r.members}==set('子午'))
        kinds={t['function_kind'] for t in clash.function_targets}
        self.assertTrue({'hidden_role','root_support'}<=kinds)
        self.assertTrue(any(t['stem_pillar']=='month' and t['root_connection'] and
                            t['root_connection']['branch_pillar']=='day' for t in clash.function_targets))
        root=next(t for t in clash.function_targets if t['function_kind']=='root_support')
        self.assertEqual(root['possible_changes'],['retained','reduced','activated'])
        self.assertTrue(any(t['carrier_id']==root['carrier_id'] and t['function_kind']=='hidden_role'
                            for t in clash.function_targets))

    def test_same_role_change_has_different_direction_under_different_natal_needs(self):
        target={'balance_role':'supports_day'};before=deepcopy(target)
        self.assertEqual(compare_balance_function(target,'reduced','support'),'opposes_requested_direction')
        self.assertEqual(compare_balance_function(target,'reduced','drain'),'matches_requested_direction')
        target['balance_role']='drains_or_pressures_day'
        self.assertEqual(compare_balance_function(target,'reduced','support'),'matches_requested_direction')
        self.assertIsNone(compare_balance_function(before,'retained','support'))
        self.assertIsNone(compare_balance_function(before,'reduced','protect'))

    def test_unmodeled_branch_harm_does_not_inherit_clash_function_rules(self):
        rs=relationships(['甲子','己未','戊辰','丁酉'])
        harms=[r for r in rs if r.type=='branch_harm']
        self.assertTrue(harms)
        self.assertTrue(all(r.function_targets==[] for r in harms))
