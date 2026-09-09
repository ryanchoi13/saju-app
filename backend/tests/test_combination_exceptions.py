"""Boundary checks of the second natal-combination rule bundle."""
from unittest import TestCase

from app.engine.relationships.assessment import requires_role_review
from test_natal_function_assessment import facts


def pair(chart):
    p, h, roots, relations, evidence = facts(chart)
    relation = next(r for r in relations if r.type == 'stem_combination'
                    and {m['pillar'] for m in r.members} == {'year', 'month'})
    return relation, evidence


class CombinationExceptionTests(TestCase):
    def test_no_branch_assistance_excludes_conversion_but_not_binding(self):
        relation, evidence = pair(['丙午', '辛卯', '戊寅', '甲寅'])
        self.assertEqual(relation.transformation.status.value, 'not_established')
        self.assertEqual({t['function_state'] for t in relation.function_targets}, {'reduced'})
        basis = relation.effect_assessment['transformation_basis']
        self.assertEqual(basis['branch_carriers'], [])
        self.assertEqual(set(basis['support_elements']), {'金', '水'})
        self.assertTrue(set(relation.evidence_ids) <= {e.id for e in evidence})
        self.assertFalse(requires_role_review(relation))

    def test_hidden_support_blocks_the_absence_test(self):
        # Deliberate counterfactual, not an extra historical example.
        relation, _ = pair(['丙午', '辛卯', '戊申', '甲寅'])
        self.assertNotEqual(relation.transformation.status.value, 'not_established')
        self.assertTrue(relation.effect_assessment['transformation_basis']['branch_carriers'])

    def test_generating_element_is_assistance_even_without_target_element(self):
        relation, _ = pair(['乙未', '庚辰', '戊辰', '丙辰'])
        basis = relation.effect_assessment['transformation_basis']
        self.assertEqual({c['element'] for c in basis['branch_carriers']}, {'土'})
        self.assertEqual(basis['target'], '金')
        self.assertNotEqual(relation.transformation.status.value, 'not_established')

    def test_unknown_hour_cannot_establish_absence_in_entire_chart(self):
        relation, _ = pair(['丙午', '辛卯', '戊寅'])
        self.assertNotEqual(relation.transformation.status.value, 'not_established')
        self.assertEqual(relation.effect_assessment['transformation_basis']['status'], 'unreviewed')

    def test_role_judgment_does_not_certify_replacement_element(self):
        relation, _ = pair(['己卯', '甲戌', '乙亥', '己卯'])
        self.assertEqual(relation.effect_assessment['status'], 'established')
        self.assertEqual(relation.transformation.status.value, 'conditional')
        self.assertTrue(requires_role_review(relation))
        self.assertTrue(all(t['actual_valence'] == 'undetermined' for t in relation.function_targets))

    def test_month_alignment_alone_cannot_reproduce_opposed_context(self):
        for chart in (['己卯', '甲戌', '乙子', '己卯'],  # remove own wood root
                      ['己未', '甲戌', '乙亥', '己亥'],  # remove vigorous wood root
                      ['己卯', '甲戌', '乙亥', '辛卯']): # add controlling visible metal
            with self.subTest(chart=chart):
                relation, _ = pair(chart)
                self.assertEqual(relation.effect_assessment['status'], 'unresolved')

    def test_native_target_with_vigorous_season_is_not_removed_with_partner(self):
        relation, _ = pair(['庚申', '乙酉', '丁丑', '庚戌'])
        metal = next(t for t in relation.function_targets if t['stem'] == '庚')
        self.assertEqual(metal['function_state'], 'retained')
        self.assertEqual(relation.effect_assessment['status'], 'partial')
        self.assertNotEqual(relation.transformation.status.value, 'not_established')

    def test_known_conversion_examples_identify_pair_without_certifying_its_force(self):
        for chart in (['丁亥', '壬寅', '丙子', '丁酉'], ['癸巳', '戊午', '丙午', '庚寅']):
            relation, _ = pair(chart)
            self.assertNotEqual(relation.transformation.status.value, 'not_established')
            self.assertEqual(relation.transformation.status.value, 'established')
            self.assertEqual(relation.transformation.kind, 'pair')
            self.assertTrue(requires_role_review(relation))

    def test_root_in_fake_conversion_is_not_a_blanket_negative_verdict(self):
        relation, _ = pair(['己卯', '甲戌', '甲子', '己巳'])
        self.assertEqual(relation.transformation.status.value, 'conditional')
        self.assertNotEqual(relation.effect_assessment['status'], 'established')

    def test_shared_yin_officer_is_not_ordinary_removal_of_both_roles(self):
        for chart in (['壬申', '丁未', '丁未', '癸卯'], ['丙戌', '辛卯', '辛巳', '戊戌']):
            relation, _ = pair(chart)
            self.assertTrue(relation.effect_assessment['pair_context']['shared_yin_day_officer'])
            self.assertEqual(relation.effect_assessment['status'], 'partial')
            officer = next(t for t in relation.function_targets if t['role_to_day_master'] == 'direct_officer')
            self.assertEqual(officer['function_state'], 'retained')
            self.assertEqual(officer['role_direction'], 'shared_not_exclusive')
            self.assertFalse(any(t.get('function_state') == 'reduced' for t in relation.function_targets))

    def test_same_yang_stem_does_not_inherit_yin_officer_exception(self):
        relation, _ = pair(['己卯', '甲戌', '甲亥', '己卯'])
        self.assertFalse(relation.effect_assessment['pair_context']['shared_yin_day_officer'])
        self.assertEqual(relation.effect_assessment['status'], 'established')

    def test_clashed_roots_require_review_before_simple_role_binding(self):
        relation, _ = pair(['辛巳', '丙申', '壬寅', '庚戌'])
        self.assertTrue(relation.effect_assessment['pair_context']['clashed_member_roots'])
        self.assertEqual(relation.effect_assessment['status'], 'partial')
        self.assertFalse(any(t.get('function_state') == 'reduced' for t in relation.function_targets))
