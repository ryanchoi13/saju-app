from unittest import TestCase

from app.engine.constants import GAN_WUXING, ZHI_WUXING
from app.engine.core.models import ConfidenceLevel, DiagnosticResult, PillarFact
from app.engine.diagnostics.mediation import diagnose_mediation
from app.engine.facts.element_inventory import calculate_element_inventory
from app.engine.facts.hidden_stems import calculate_hidden_stems
from app.engine.facts.relationship_candidates import calculate_relationship_candidates
from app.engine.facts.rooting import calculate_exposed_stems, calculate_roots
from app.engine.relationships.resolver import resolve_relationships


def _pillar(stem: str, branch: str) -> PillarFact:
    return PillarFact(
        stem=stem, branch=branch, ganji=f"{stem}{branch}",
        stem_element=GAN_WUXING[stem], stem_yin_yang="yang",
        branch_element=ZHI_WUXING[branch], branch_yin_yang="yang",
    )


def _diagnostic(module, conclusion, operations=None):
    return DiagnosticResult(
        module=module, status="completed", conclusion=conclusion,
        recommended_operations=operations or [], confidence=ConfidenceLevel.MEDIUM,
    )


def _diagnose(pillars, strength="balanced", climate_ops=None):
    hidden = calculate_hidden_stems(pillars)
    roots = calculate_roots(pillars, hidden)
    relationships, _ = resolve_relationships(
        calculate_relationship_candidates(pillars), pillars, roots,
        calculate_exposed_stems(pillars, hidden),
    )
    return diagnose_mediation(
        pillars["day"].stem, calculate_element_inventory(pillars, hidden), roots,
        relationships, _diagnostic("strength", strength),
        _diagnostic("climate", "mild_balanced", climate_ops),
    )


class MediationDiagnosticTests(TestCase):
    def test_rooted_water_is_a_potential_bridge_not_proven_mediation(self):
        result, evidence = _diagnose({
            "year": _pillar("庚", "酉"),
            "month": _pillar("甲", "寅"),
            "day": _pillar("壬", "子"),
        })
        signal = next(item for item in result.signals if item["controller_element"] == "金")
        self.assertEqual(signal["mediator_element"], "水")
        self.assertEqual(signal["mediation_status"], "conditional")
        self.assertEqual(result.conclusion, "mediation_conditional")
        self.assertEqual(signal['potential_paths'][0]['generation_legs'], [['庚', '壬'], ['壬', '甲']])
        self.assertFalse(evidence[0].source_values["fixed_score_used"])

    def test_classical_fire_bridge_keeps_its_combination_context(self):
        # Ziping section 4: 丙午 辛卯 戊寅 甲寅. Presence of 丙 alone
        # must not certify 甲→丙→戊 when the source discusses 丙辛 binding.
        result, _ = _diagnose(dict(zip(['year', 'month', 'day', 'hour'],
            [_pillar(*p) for p in ['丙午', '辛卯', '戊寅', '甲寅']])))
        signal = next(s for s in result.signals if s['controller_element'] == '木')
        path = signal['potential_paths'][0]
        self.assertEqual(path['generation_legs'], [['甲', '丙'], ['丙', '戊']])
        self.assertTrue(any(i.startswith('stem_combination:') for i in path['mediator_relationship_ids']))
        self.assertEqual(path['effectiveness'], 'undetermined')
        self.assertNotEqual(signal['mediation_status'], 'established')

    def test_generation_path_direction_is_not_input_order(self):
        result, _ = _diagnose({'year': _pillar('己','亥'),
            'month': _pillar('丁','卯'), 'day': _pillar('甲','子')})
        signal = next(s for s in result.signals if s['controller_element'] == '木')
        self.assertEqual(signal['potential_paths'][0]['generation_legs'], [['甲','丁'],['丁','己']])

    def test_absent_mediator_is_not_established(self):
        result, _ = _diagnose({
            "year": _pillar("庚", "酉"),
            "month": _pillar("甲", "卯"),
            "day": _pillar("丙", "午"),
        })
        signal = next(item for item in result.signals if item["controller_element"] == "金")
        self.assertEqual(signal["mediator_supply"]["availability"], "absent")
        self.assertEqual(signal["mediation_status"], "not_established")

    def test_hidden_only_mediator_stays_conditional(self):
        result, _ = _diagnose({
            "year": _pillar("庚", "申"),
            "month": _pillar("甲", "寅"),
            "day": _pillar("丙", "午"),
        })
        signal = next(item for item in result.signals if item["controller_element"] == "金")
        self.assertEqual(signal["mediator_supply"]["availability"], "present")
        self.assertEqual(signal["mediation_status"], "conditional")
        hidden_path = next(p for p in signal['potential_paths'] if p['mediator']['symbol'] == '壬')
        self.assertEqual(hidden_path['mediator']['position'], 'hidden_stem')
        self.assertEqual(hidden_path['generation_legs'], [['庚', '壬'], ['壬', '甲']])
        self.assertFalse(hidden_path['placement']['same_visible_channel'])
        self.assertTrue(any(r.startswith('branch_clash:')
                            for r in hidden_path['mediator_relationship_ids']))
        self.assertEqual(hidden_path['effectiveness'], 'undetermined')

    def test_absence_alone_cannot_supply_a_lucky_element_downstream(self):
        from app.engine.semantic.engine import build_semantic_state
        from app.engine.synthesis.engine import synthesize_diagnostics
        # A regression fixture, not a historical birth chart: every bridge is
        # absent. Completing the inventory must not approve a water prescription.
        result, _ = _diagnose(dict(zip(['year', 'month', 'day', 'hour'],
            [_pillar(*p) for p in ['庚酉', '辛酉', '甲卯', '乙卯']])))
        self.assertEqual(result.status, 'completed')
        self.assertEqual(result.conclusion, 'mediation_absent')
        diagnostics = {
            name: _diagnostic(name, conclusion) for name, conclusion in {
                'structure': 'direct_resource', 'strength': 'balanced',
                'climate': 'mild_balanced', 'pathology': 'no_critical_bottleneck',
                'special_structure': 'ordinary_structure_preferred',
            }.items()
        }
        diagnostics['mediation'] = result
        synthesis, _ = synthesize_diagnostics(diagnostics)
        semantic, _ = build_semantic_state(synthesis)
        self.assertNotIn('水', semantic.favorable_elements)
        self.assertNotIn('水', semantic.caution_elements)
        self.assertNotIn('mediate', semantic.action_tendencies)
        self.assertEqual(len(synthesis.pending_operations), len(result.signals))
        self.assertTrue(all(o['unresolved_requirements'] for o in synthesis.pending_operations))

    def test_classical_connected_and_separated_routes_are_distinguishable(self):
        # 滴天髓闡微 通關, cases 1 and 3. Check the textual premises;
        # neither a route record nor this test proves the historical outcome.
        connected, _ = _diagnose(dict(zip(['year', 'month', 'day', 'hour'],
            [_pillar(*p) for p in ['癸酉', '甲子', '丁卯', '丙午']])))
        separated, _ = _diagnose(dict(zip(['year', 'month', 'day', 'hour'],
            [_pillar(*p) for p in ['戊辰', '乙卯', '辛丑', '丁酉']])))
        c = next(s for s in connected.signals if s['controlled_element'] == '火')
        cp = next(p for p in c['potential_paths'] if p['mediator']['position'] == 'visible_stem')
        self.assertEqual(cp['generation_legs'], [['癸', '甲'], ['甲', '丁']])
        self.assertTrue(cp['placement']['mediator_between_endpoints'])
        self.assertTrue(all(not leg['intervening_visible_stems'] for leg in cp['placement']['legs']))
        s = next(s for s in separated.signals if s['controller_element'] == '火')
        sp = next(p for p in s['potential_paths'] if p['mediator']['position'] == 'visible_stem')
        self.assertEqual(sp['generation_legs'], [['丁', '戊'], ['戊', '辛']])
        self.assertFalse(sp['placement']['mediator_between_endpoints'])
        self.assertTrue(any('乙' in [n['symbol'] for n in leg['intervening_visible_stems']]
                            for leg in sp['placement']['legs']))
        self.assertTrue(any(r.startswith('stem_control:') for r in sp['mediator_relationship_ids']))
        self.assertTrue(any(p['mediator']['position'] == 'hidden_stem' for p in s['potential_paths']))

    def test_mediator_root_context_includes_relations_away_from_day_master(self):
        result, _ = _diagnose(dict(zip(['year', 'month', 'day', 'hour'],
            [_pillar(*p) for p in ['癸酉', '甲子', '丁卯', '丙午']])))
        signal = next(s for s in result.signals if s['controlled_element'] == '火')
        path = next(p for p in signal['potential_paths'] if p['mediator']['position'] == 'visible_stem')
        roots = path['node_contexts']['mediator']['root_contexts']
        root = next(r for r in roots if r['branch_pillar'] == 'day')
        self.assertEqual(root['hidden_stem'], '乙')
        self.assertFalse(root['exact_stem'])
        self.assertTrue(any(r.startswith('branch_clash:') for r in root['related_relationship_ids']))
        self.assertEqual(root['effectiveness'], 'undetermined')

    def test_strength_side_effect_is_preserved(self):
        result, _ = _diagnose({
            "year": _pillar("庚", "申"),
            "month": _pillar("甲", "寅"),
            "day": _pillar("丙", "午"),
        }, strength="extremely_weak")
        self.assertTrue(any("극약" in item for item in result.counter_evidence))

    def test_no_control_relation_needs_no_mediation(self):
        result, _ = _diagnose({
            "year": _pillar("乙", "卯"),
            "month": _pillar("甲", "寅"),
            "day": _pillar("甲", "寅"),
        })
        self.assertEqual(result.conclusion, "no_controlling_conflict")
