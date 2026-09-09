"""Source assertions and counterfactual boundaries of the third rule bundle."""
from unittest import TestCase

from app.engine.core.models import TransformationStatus
from app.engine.relationships.assessment import requires_role_review
from app.engine.relationships.combination_context import (
    shared_officer_context, metal_fire_release_context,
)
from test_combination_exceptions import pair
from test_natal_function_assessment import facts, strength


class CombinationRoleContextTests(TestCase):
    def test_shared_officer_retains_identity_without_exclusive_force(self):
        for chart in (['壬申', '丁未', '丁未', '癸卯'], ['丙戌', '辛卯', '辛巳', '戊戌']):
            relation, evidence = pair(chart)
            officer = next(t for t in relation.function_targets if t['role_to_day_master'] == 'direct_officer')
            self.assertEqual(officer['function_state'], 'retained')
            self.assertEqual(officer['retained_scope'], 'original_role_identity_only')
            self.assertEqual(officer['effective_force'], 'undetermined')
            self.assertEqual(officer['role_direction'], 'shared_not_exclusive')
            self.assertEqual(officer['actual_valence'], 'undetermined')
            self.assertTrue(set(officer['effect_evidence_ids']) <= {e.id for e in evidence})
            self.assertTrue(requires_role_review(relation))
            self.assertNotEqual(strength(chart).status, 'completed')

    def test_shared_officer_rule_does_not_spread_to_three_peers_or_two_officers(self):
        for chart in (['壬申', '丁未', '丁未', '丁卯'], ['壬申', '丁未', '丁未', '壬子']):
            relation, _ = pair(chart)
            self.assertIsNone(relation.effect_assessment['pair_context']['shared_officer_assessment'])
            self.assertFalse(any(t.get('effect_rule') == 'shared-yin-officer-identity-retained-v1'
                                 for t in relation.function_targets))

    def test_established_conversion_cannot_retain_the_old_officer_by_shared_rule(self):
        p, _, _, relations, _ = facts(['丙戌', '辛卯', '辛巳', '戊戌'])
        relation = next(r for r in relations if r.type == 'stem_combination' and len(r.members) == 2
                        and {m['pillar'] for m in r.members} == {'year', 'month'})
        relation.transformation.status = TransformationStatus.ESTABLISHED
        self.assertIsNone(shared_officer_context(relation, p))

    def test_rooted_water_examples_do_not_convert(self):
        for chart in (['壬申', '丁未', '丁未', '癸卯'], ['癸亥', '戊午', '壬午', '己酉']):
            relation, evidence = pair(chart)
            self.assertEqual(relation.transformation.status.value, 'not_established')
            context = relation.effect_assessment['pair_context']['rooted_water_assessment']
            self.assertTrue(context['own_roots'])
            self.assertTrue(set(relation.evidence_ids) <= {e.id for e in evidence})
            # Original water roots are not proof that both original roles stay usable.
            self.assertTrue(requires_role_review(relation))

    def test_own_water_root_and_remote_water_root_are_not_interchangeable(self):
        relation, _ = pair(['癸巳', '戊午', '壬午', '己亥'])
        self.assertIsNone(relation.effect_assessment['pair_context']['rooted_water_assessment'])
        self.assertNotEqual(relation.transformation.status.value, 'not_established')

    def test_root_in_a_branch_clash_or_combination_needs_its_own_review(self):
        for chart in (['癸亥', '戊午', '壬午', '己巳'],  # own root clashes
                      ['癸亥', '戊午', '壬午', '己寅'],  # own root combines
                      ['壬申', '丁卯', '丁未', '癸丑']): # stronger target season
            relation, _ = pair(chart)
            self.assertIsNone(relation.effect_assessment['pair_context']['rooted_water_assessment'])
            self.assertNotEqual(relation.transformation.status.value, 'not_established')

    def test_ren_wet_reserve_and_fire_branch_contrast(self):
        wet, _ = pair(['癸丑', '戊午', '丙午', '壬辰'])
        fire, _ = pair(['癸巳', '戊午', '丙午', '壬辰'])
        self.assertEqual(wet.transformation.status.value, 'not_established')
        self.assertTrue(wet.effect_assessment['pair_context']['rooted_water_assessment']['separate_rooted_water'])
        self.assertEqual(fire.transformation.status.value, 'established')
        self.assertEqual(fire.transformation.kind, 'pair')
        self.assertTrue(requires_role_review(fire))

    def test_wet_reserve_without_separate_rooted_water_is_not_the_full_context(self):
        for chart in (['癸丑', '戊午', '丙午', '庚辰'], ['癸丑', '戊午', '丙午', '壬午']):
            relation, _ = pair(chart)
            self.assertIsNone(relation.effect_assessment['pair_context']['rooted_water_assessment'])

    def test_release_path_keeps_metal_without_erasing_fire_roots(self):
        p, _, roots, relations, evidence = facts(['辛巳', '丙申', '壬寅', '庚戌'])
        relation = next(r for r in relations if r.type == 'stem_combination')
        metal = next(t for t in relation.function_targets if t['stem'] == '辛')
        fire = next(t for t in relation.function_targets if t['stem'] == '丙')
        context = relation.effect_assessment['pair_context']['metal_fire_release_assessment']
        self.assertEqual(relation.transformation.status.value, 'not_established')
        self.assertEqual(metal['function_state'], 'retained')
        self.assertEqual(fire['effect_status'], 'unresolved')
        self.assertEqual(context['branch_combination_verdict'], 'unresolved')
        self.assertFalse(context['root_erased'])
        self.assertTrue(set(context['path_relationship_ids']) <= {r.id for r in relations})
        self.assertTrue(set(metal['effect_evidence_ids']) <= {e.id for e in evidence})
        self.assertEqual({r.branch_pillar for r in roots.items if r.stem_pillar == 'month'}, {'year', 'day', 'hour'})
        self.assertTrue(requires_role_review(relation))

    def test_control_or_clash_alone_does_not_release_the_pair(self):
        p, _, roots, relations, _ = facts(['辛巳', '丙申', '壬寅', '庚戌'])
        relation = next(r for r in relations if r.type == 'stem_combination')
        for excluded in ('stem_control', 'branch_clash'):
            filtered = [r for r in relations if r.type != excluded]
            self.assertIsNone(metal_fire_release_context(relation, p, roots, filtered))

    def test_release_requires_its_source_season_and_an_unopposed_controller(self):
        for chart in (['辛巳', '丙午', '壬寅', '庚戌'],
                      ['辛巳', '丙申', '壬寅', '戊戌'],
                      ['辛巳', '丙申', '甲寅', '庚戌']):
            relation, _ = pair(chart)
            self.assertIsNone(relation.effect_assessment['pair_context']['metal_fire_release_assessment'])

    def test_unknown_hour_does_not_trigger_whole_context_rules(self):
        for chart in (['壬申', '丁未', '丁未'], ['癸亥', '戊午', '壬午'], ['辛巳', '丙申', '壬寅']):
            relation, _ = pair(chart)
            context = relation.effect_assessment['pair_context']
            self.assertTrue(all(context[k] is None for k in (
                'shared_officer_assessment', 'rooted_water_assessment', 'metal_fire_release_assessment')))
