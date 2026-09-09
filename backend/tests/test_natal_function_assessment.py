"""Sourced development examples and rule counterexamples, not prediction tests."""
from unittest import TestCase

from app.engine.core.models import DiagnosticResult, RelationshipResult
from app.engine.diagnostics.climate import diagnose_climate
from app.engine.diagnostics.pathology import diagnose_pathology
from app.engine.diagnostics.root_support import describe_root_support
from app.engine.diagnostics.strength import diagnose_strength
from app.engine.facts import (
    calculate_element_inventory, calculate_exposed_stems, calculate_hidden_stems,
    calculate_relationship_candidates, calculate_roots, calculate_ten_gods,
)
from app.engine.relationships.assessment import assess_natal_functions, REFERENCE_ONLY_TYPES
from app.engine.relationships.resolver import resolve_relationships
from app.engine.semantic.engine import build_semantic_state
from app.engine.synthesis.engine import synthesize_diagnostics
from app.engine.timing.engine import _pillar

ORDER = ('year', 'month', 'day', 'hour')


def facts(chart):
    pillars = dict(zip(ORDER, map(_pillar, chart)))
    hidden = calculate_hidden_stems(pillars)
    roots = calculate_roots(pillars, hidden)
    relations, evidence = resolve_relationships(calculate_relationship_candidates(pillars),
        pillars, roots, calculate_exposed_stems(pillars, hidden))
    return pillars, hidden, roots, relations, evidence


def strength(chart):
    p, h, roots, relations, _ = facts(chart)
    return diagnose_strength(p['day'].stem, p, roots,
        calculate_ten_gods(p['day'].stem, p, h), relations)[0]


def diagnostic(module, conclusion, **kwargs):
    return DiagnosticResult(module=module, status='completed', conclusion=conclusion, **kwargs)


class NatalFunctionAssessmentTests(TestCase):
    def test_sourced_month_role_retention_is_not_whole_pair_or_valence(self):
        for chart, symbol in [(['癸未', '辛酉', '甲申', '丙寅'], '辛'),
                              (['戊子', '癸亥', '庚寅', '戊寅'], '癸')]:
            with self.subTest(chart=chart):
                *_, relations, evidence = facts(chart)
                comb = next(r for r in relations if r.type == 'stem_combination')
                member = next(t for t in comb.function_targets if t['stem'] == symbol)
                self.assertEqual(member['function_state'], 'retained')
                self.assertEqual(comb.effect_assessment['status'], 'partial')
                self.assertTrue(set(member['effect_evidence_ids']) <= {e.id for e in evidence})
                self.assertTrue(all(t['actual_valence'] == 'undetermined' for t in comb.function_targets))

    def test_sourced_close_pair_can_restrict_a_rooted_supporter(self):
        p, h, roots, relations, _ = facts(['丙午', '辛卯', '戊寅', '甲寅'])
        comb = next(r for r in relations if r.type == 'stem_combination')
        self.assertTrue(any(root.stem_pillar == 'year' for root in roots.items))
        self.assertEqual({t['function_state'] for t in comb.function_targets}, {'reduced'})
        self.assertEqual(comb.effect_assessment['status'], 'established')
        result = diagnose_strength(p['day'].stem, p, roots,
            calculate_ten_gods(p['day'].stem, p, h), relations)[0]
        support = next(s for s in result.signals if s['step'] == 'support')
        self.assertIn('indirect_resource', support['visible_ten_gods'])
        self.assertNotIn('indirect_resource', support['operative_support_ten_gods'])
        self.assertEqual(set(support['restricted_visible_pillars']), {'year', 'month'})

    def test_month_aligned_role_exception_does_not_resolve_conversion(self):
        *_, relations, _ = facts(['己卯', '甲戌', '乙亥', '己卯'])
        comb = next(r for r in relations if r.type == 'stem_combination')
        self.assertEqual(comb.effect_assessment['status'], 'established')
        self.assertTrue(all(t['function_state'] == 'reduced' for t in comb.function_targets))
        self.assertEqual(comb.transformation.status.value, 'conditional')
        self.assertTrue(comb.effect_assessment['replacement_role_review_required'])

    def test_day_master_pair_and_flanking_competition_do_not_use_close_pair_rule(self):
        for chart in (['戊寅', '己未', '甲寅', '乙亥'], ['丙戌', '壬辰', '丁未', '壬寅']):
            *_, relations, _ = facts(chart)
            for comb in (r for r in relations if r.type == 'stem_combination'):
                self.assertEqual(comb.effect_assessment['status'], 'unresolved')
                self.assertTrue(all(t['effect_status'] == 'unresolved' for t in comb.function_targets))

    def test_distant_pair_is_not_treated_as_adjacent(self):
        *_, relations, _ = facts(['丁卯', '丙午', '丙子', '壬辰'])
        comb = next(r for r in relations if r.type == 'stem_combination')
        self.assertEqual(comb.effect_assessment['status'], 'unresolved')

    def test_storage_root_reduction_preserves_original_facts_and_hidden_roles(self):
        p, h, roots, relations, _ = facts(['乙丑', '甲申', '甲申', '辛未'])
        day_root = next(r for r in roots.items if r.stem_pillar == 'day')
        observed = next(r for r in describe_root_support(roots, p, relations) if r['stem_pillar'] == 'day')
        self.assertEqual(day_root.hidden_stem, '乙')
        self.assertEqual(observed['effectiveness'], 'reduced')
        self.assertTrue(observed['effect_evidence_ids'])
        clash = next(r for r in relations if r.type == 'branch_clash')
        self.assertEqual(clash.effect_assessment['status'], 'partial')
        self.assertTrue(all(t['effect_status'] == 'unresolved' for t in clash.function_targets
                            if t['function_kind'] == 'hidden_role'))

    def test_adding_vigorous_root_blocks_storage_only_rule(self):
        # Deliberate counterfactual, not an additional historical example.
        p, h, roots, relations, _ = facts(['乙丑', '甲申', '甲寅', '辛未'])
        day_roots = [r for r in describe_root_support(roots, p, relations) if r['stem_pillar'] == 'day']
        self.assertTrue(any(r['category'] == 'vigorous' for r in day_roots))
        self.assertFalse(any(r['effectiveness'] == 'reduced' for r in day_roots))
        self.assertEqual(strength(['乙丑', '甲申', '甲寅', '辛未']).status, 'conditional')

    def test_competing_root_combination_requires_separate_review(self):
        for month, expected in [('庚午', 'reduced'), ('庚酉', 'undetermined')]:
            p, h, roots, relations, _ = facts(['乙辰', month, '甲戌', '辛丑'])
            day = [r for r in describe_root_support(roots, p, relations) if r['stem_pillar'] == 'day']
            self.assertTrue(day)
            self.assertEqual({r['effectiveness'] for r in day}, {expected})

    def test_earth_roots_are_not_reduced_by_non_earth_rule(self):
        *_, relations, _ = facts(['辛未', '辛丑', '戊辰', '壬戌'])
        earth = [t for r in relations for t in r.function_targets
                 if t['function_kind'] == 'root_support' and t['element'] == '土']
        self.assertTrue(earth)
        self.assertTrue(all(t['effect_status'] == 'unresolved' for t in earth))

    def test_reference_labels_survive_as_facts_but_not_independent_damage(self):
        *_, relations, evidence = facts(['甲辰', '丁卯', '甲子', '戊辰'])
        labels = [r for r in relations if r.type in REFERENCE_ONLY_TYPES]
        self.assertTrue(labels)
        self.assertTrue(all(r.effect_assessment['status'] == 'observation_only' for r in labels))
        d, _ = diagnose_pathology(diagnostic('structure', 'peer'), diagnostic('strength', 'balanced'),
                                 diagnostic('climate', 'mild_balanced'), labels)
        self.assertEqual(d.status, 'completed')
        self.assertEqual(d.signals, [])
        synthesis, _ = synthesize_diagnostics({'pathology': d})
        semantic, _ = build_semantic_state(synthesis, relationships=labels)
        self.assertFalse(set(semantic.strongest_interactions) & {r.id for r in labels})

    def test_four_strength_examples_distinguish_degree_without_claiming_prescription(self):
        for chart, expected in [(['甲辰', '丁卯', '甲子', '戊辰'], 'strong'),
                                (['癸卯', '乙卯', '甲寅', '乙亥'], 'extremely_strong'),
                                (['乙丑', '甲申', '甲申', '辛未'], 'weak'),
                                (['己巳', '己巳', '乙酉', '丙戌'], 'extremely_weak')]:
            with self.subTest(chart=chart):
                result = strength(chart)
                self.assertEqual(result.conclusion, expected)
                self.assertFalse(any(o.get('stem') for o in result.recommended_operations))

    def test_hidden_rooted_resource_keeps_ordinary_weakness_provisional(self):
        result = strength(['庚申', '丙戌', '甲申', '壬申'])
        self.assertEqual(result.conclusion, 'weak')
        self.assertEqual(result.status, 'conditional')
        synthesis, _ = synthesize_diagnostics({'strength': result})
        self.assertFalse(synthesis.favorable_operations)

    def test_extreme_strength_does_not_certify_generic_remedy_via_wrapper(self):
        for state, remedy, bottleneck in [('extremely_strong', 'moderate_excess_force', 'excess'),
                                          ('extremely_weak', 'restore_supporting_capacity', 'deficiency')]:
            ds = {'strength': diagnostic('strength', state),
                  'pathology': diagnostic('pathology', bottleneck, recommended_operations=[{
                      'operation': remedy, 'bottleneck_id': 'bottleneck:' + bottleneck}])}
            result, _ = synthesize_diagnostics(ds)
            self.assertFalse(result.favorable_operations)
            self.assertEqual(len(result.pending_operations), 2)
            self.assertTrue(all(o['reason'] == 'extreme_strength_direction_unconfirmed'
                                for o in result.pending_operations))

    def test_climate_inventory_does_not_certify_personal_operation_via_wrapper(self):
        p, h, roots, relations, _ = facts(['丙午', '甲午', '丙午', '甲午'])
        climate, _ = diagnose_climate(p, calculate_element_inventory(p, h), roots, relations)
        self.assertTrue(climate.recommended_operations)
        climate.status = 'completed'  # Deliberately try to bypass an upstream gate.
        pathology, _ = diagnose_pathology(diagnostic('structure', 'peer'),
                                          diagnostic('strength', 'balanced'), climate, [])
        pathology.status = 'completed'
        result, _ = synthesize_diagnostics({'climate': climate, 'pathology': pathology})
        self.assertFalse(result.favorable_operations)
        self.assertTrue(all('personal_climate_need' in o['unresolved_requirements']
                            for o in result.pending_operations))

    def test_natal_rules_do_not_resolve_a_temporal_pair(self):
        p, h, roots, _, _ = facts(['丙午', '辛卯', '戊寅', '甲寅'])
        relation = RelationshipResult(id='mixed', type='stem_combination', members=[
            {'pillar': 'year', 'position': 'visible_stem', 'symbol': '丙'},
            {'pillar': 'timing:daily', 'position': 'visible_stem', 'symbol': '辛'}],
            existence='confirmed', action_status='active')
        evidence = assess_natal_functions([relation], p, roots)
        self.assertFalse(evidence)
        self.assertEqual(relation.effect_assessment['scope'], 'outside_natal_rule_scope')
        self.assertEqual(relation.effect_assessment['status'], 'unresolved')
