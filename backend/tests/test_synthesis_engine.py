from unittest import TestCase

from app.engine.core.models import ConfidenceLevel, DiagnosticResult
from app.engine.synthesis.engine import synthesize_diagnostics


def _diagnostic(
    module,
    conclusion,
    *,
    status="completed",
    operations=None,
    signals=None,
):
    return DiagnosticResult(
        module=module,
        status=status,
        conclusion=conclusion,
        recommended_operations=operations or [],
        signals=signals or [],
        confidence=ConfidenceLevel.MEDIUM,
        evidence_ids=[f"evidence:{module}"],
    )


def _complete_diagnostics():
    return {
        "structure": _diagnostic("structure", "direct_wealth"),
        "strength": _diagnostic("strength", "balanced", operations=[
            {"operation": "preserve_balance", "when": True},
        ]),
        "climate": _diagnostic("climate", "mild_balanced"),
        "pathology": _diagnostic("pathology", "no_critical_bottleneck"),
        "mediation": _diagnostic("mediation", "no_controlling_conflict"),
        "special_structure": _diagnostic(
            "special_structure", "ordinary_structure_preferred"
        ),
    }


class SynthesisEngineTests(TestCase):
    def test_completed_observation_does_not_approve_conditional_operation(self):
        diagnostics = _complete_diagnostics()
        diagnostics['mediation'] = _diagnostic('mediation', 'mediation_absent', operations=[{
            'operation': 'mediate_control_conflict', 'element': '水',
            'assessment_status': 'conditional', 'conflict_id': 'metal-controls-wood',
            'availability': 'absent', 'unresolved_requirements': ['verify_need'],
        }])
        result, _ = synthesize_diagnostics(diagnostics)
        self.assertFalse(any('水' in o['elements'] for o in result.favorable_operations))
        pending = result.pending_operations[0]
        self.assertEqual(pending['reason'], 'operation_judgment_unconfirmed')
        self.assertEqual(pending['conflict_id'], 'metal-controls-wood')
        self.assertEqual(pending['unresolved_requirements'], ['verify_need'])
        self.assertIn('preserve_balance', [o['operation'] for o in result.favorable_operations])

    def test_completed_operation_label_cannot_hide_unresolved_requirements(self):
        diagnostics = _complete_diagnostics()
        diagnostics['mediation'] = _diagnostic('mediation', 'mediation_available', operations=[{
            'operation': 'mediate_control_conflict', 'element': '木',
            'assessment_status': 'completed', 'unresolved_requirements': ['verify_endpoint_role'],
        }])
        result, _ = synthesize_diagnostics(diagnostics)
        self.assertFalse(any('木' in o['elements'] for o in result.favorable_operations))
        self.assertEqual(result.pending_operations[0]['reason'], 'operation_judgment_unconfirmed')

    def test_confirmed_operations_remain_available_beside_pending_ones(self):
        diagnostics = _complete_diagnostics()
        diagnostics['climate'] = _diagnostic('climate', 'cool', operations=[
            {'operation': 'warming', 'element': '火', 'assessment_status': 'completed'},
            {'operation': 'moistening', 'element': '水', 'assessment_status': 'conditional'},
        ])
        result, _ = synthesize_diagnostics(diagnostics)
        self.assertIn('火', [e for o in result.favorable_operations for e in o['elements']])
        self.assertNotIn('水', [e for o in result.favorable_operations for e in o['elements']])
        self.assertEqual(result.pending_operations[0]['element'], '水')

    def test_conditional_urgency_cannot_override_completed_direction(self):
        diagnostics = _complete_diagnostics()
        diagnostics['climate'] = _diagnostic('climate', 'cool', operations=[
            {'operation': 'warming', 'element': '火', 'urgency': 'low'}])
        diagnostics['mediation'] = _diagnostic('mediation', 'mediation_conditional',
            status='conditional', operations=[
                {'operation': 'cooling', 'element': '水', 'urgency': 'high'}])
        result, _ = synthesize_diagnostics(diagnostics)
        self.assertIn('warm', [o['operation'] for o in result.favorable_operations])
        self.assertNotIn('cool', [o['operation'] for o in result.favorable_operations])
        self.assertNotIn('cool', [o['operation'] for o in result.caution_operations])
        self.assertEqual(result.pending_operations[0]['operation'], 'cool')

    def test_pending_duplicate_does_not_inflate_evidence_or_urgency(self):
        diagnostics = _complete_diagnostics()
        diagnostics['strength'] = _diagnostic('strength', 'weak')
        diagnostics['climate'] = _diagnostic('climate', 'mixed', status='conditional', operations=[
            {'operation': 'stabilize_root_or_support', 'urgency': 'high'}])
        result, _ = synthesize_diagnostics(diagnostics)
        support = next(o for o in result.favorable_operations if o['operation'] == 'support')
        self.assertEqual(support['independent_evidence_sources'], ['strength'])
        self.assertEqual(support['urgency'], 'low')

    def test_completed_wrapper_does_not_certify_conditional_origin(self):
        diagnostics = _complete_diagnostics()
        diagnostics['strength'] = _diagnostic('strength', 'weak', status='conditional')
        diagnostics['pathology'] = _diagnostic('pathology', 'deficiency', operations=[
            {'operation': 'restore_supporting_capacity', 'bottleneck_id': 'bottleneck:deficiency'}])
        result, _ = synthesize_diagnostics(diagnostics)
        self.assertFalse(any(o['operation'] == 'support' for o in result.favorable_operations))
        self.assertEqual(len(result.pending_operations), 2)

    def test_pending_element_neither_becomes_lucky_nor_unlucky(self):
        from app.engine.semantic.engine import build_semantic_state
        from app.engine.core.models import ActivatedState
        diagnostics = _complete_diagnostics()
        diagnostics['mediation'] = _diagnostic('mediation', 'mediation_conditional',
            status='conditional', operations=[{'operation':'mediate_control_conflict', 'element':'水'}])
        result, _ = synthesize_diagnostics(diagnostics)
        state, _ = build_semantic_state(result, ActivatedState())
        self.assertNotIn('水', state.favorable_elements)
        self.assertNotIn('水', state.caution_elements)
        self.assertNotIn('mediate', state.action_tendencies)

    def test_pending_operation_is_not_used_as_temporal_prescription(self):
        from app.engine.timing.direction import compare_temporal_directions
        diagnostics = _complete_diagnostics()
        diagnostics['climate'] = _diagnostic('climate', 'dry', status='conditional',
            operations=[{'operation':'moistening', 'element':'水'}])
        result, _ = synthesize_diagnostics(diagnostics)
        conditions = {'records': [{'relationship_id':'test:clash', 'scope':'daily',
            'type':'branch_clash', 'eligibility':'conditional', 'evidence_ids':['test:condition'],
            'checks': {'member_supply': {'水': {}}}}]}
        comparison, _ = compare_temporal_directions(conditions, result)
        self.assertEqual(comparison['records'][0]['comparisons'], [])
        self.assertEqual(comparison['records'][0]['comparison_summary'], 'unresolved')

    def test_complete_ordinary_chart_produces_medium_confidence_summary(self):
        result, evidence = synthesize_diagnostics(_complete_diagnostics())

        self.assertEqual(result.confidence, ConfidenceLevel.MEDIUM)
        self.assertEqual(result.strength_state, "balanced")
        self.assertFalse(result.overall_structure["special_precedence"])
        self.assertIn("evidence:synthesis:diagnostic-priority", result.evidence_ids)
        self.assertFalse(evidence[0].source_values["fixed_weight_used"])
        self.assertFalse(evidence[0].source_values["majority_vote_used"])

    def test_high_urgency_climate_operation_is_prioritized(self):
        diagnostics = _complete_diagnostics()
        diagnostics["climate"] = _diagnostic("climate", "very_cold_wet", operations=[
            {"operation": "warming", "element": "火", "urgency": "high", "availability": "absent"},
        ])
        result, _ = synthesize_diagnostics(diagnostics)

        self.assertEqual(result.favorable_operations[0]["operation"], "warm")
        self.assertEqual(result.favorable_operations[0]["priority_reason"], "urgent")
        self.assertEqual(result.climate_state["urgent_operations"], ["warm"])

    def test_derived_pathology_does_not_double_count_climate_evidence(self):
        diagnostics = _complete_diagnostics()
        diagnostics["climate"] = _diagnostic("climate", "very_cold_wet", operations=[
            {"operation": "warming", "urgency": "high"},
        ])
        diagnostics["pathology"] = _diagnostic(
            "pathology",
            "climate_extreme",
            operations=[{
                "operation": "warming",
                "bottleneck_id": "bottleneck:climate_extreme",
                "side_effects": ["강약 방향과 교차 확인"],
            }],
            signals=[{"id": "bottleneck:climate_extreme", "urgency": "high"}],
        )
        result, _ = synthesize_diagnostics(diagnostics)
        warming = next(item for item in result.favorable_operations if item["operation"] == "warm")

        self.assertEqual(warming["source_modules"], ["climate", "pathology"])
        self.assertEqual(warming["independent_evidence_sources"], ["climate"])
        self.assertNotEqual(warming["priority_reason"], "cross_diagnostic")

    def test_independent_common_direction_is_marked_without_voting(self):
        diagnostics = _complete_diagnostics()
        diagnostics["strength"] = _diagnostic("strength", "weak")
        diagnostics["climate"] = _diagnostic("climate", "mild_balanced", operations=[
            {"operation": "stabilize_root_or_support", "urgency": "low"},
        ])
        result, _ = synthesize_diagnostics(diagnostics)
        support = next(item for item in result.favorable_operations if item["operation"] == "support")

        self.assertEqual(support["priority_reason"], "cross_diagnostic")
        self.assertEqual(support["independent_evidence_sources"], ["climate", "strength"])

    def test_follow_structure_moves_generic_support_to_caution(self):
        diagnostics = _complete_diagnostics()
        diagnostics["strength"] = _diagnostic("strength", "extremely_weak")
        diagnostics["special_structure"] = _diagnostic(
            "special_structure", "follow_wealth"
        )
        result, _ = synthesize_diagnostics(diagnostics)

        self.assertEqual(result.favorable_operations[0]["operation"], "preserve_special_structure")
        self.assertFalse(any(item["operation"] == "support" for item in result.favorable_operations))
        self.assertTrue(any(item["operation"] == "support" for item in result.caution_operations))
        self.assertTrue(any(
            item["type"] == "special_structure_precedence"
            for item in result.diagnostic_conflicts
        ))
        self.assertEqual(result.confidence, ConfidenceLevel.HIGH)

    def test_opposite_operations_are_preserved_as_conflict(self):
        diagnostics = _complete_diagnostics()
        diagnostics["climate"] = _diagnostic("climate", "cold_wet", operations=[
            {"operation": "warming", "urgency": "high"},
        ])
        diagnostics["mediation"] = _diagnostic("mediation", "mediation_available", operations=[
            {"operation": "cooling", "urgency": "low"},
        ])
        result, _ = synthesize_diagnostics(diagnostics)

        self.assertTrue(any(item["operation"] == "warm" for item in result.favorable_operations))
        self.assertTrue(any(item["operation"] == "cool" for item in result.caution_operations))
        conflict = next(
            item
            for item in result.diagnostic_conflicts
            if item["type"] == "directional_conflict"
        )
        self.assertEqual(conflict["preferred_operation"], "warm")
        self.assertEqual(result.confidence, ConfidenceLevel.LOW)

    def test_equal_urgency_conflict_keeps_both_out_of_favorable_operations(self):
        diagnostics = _complete_diagnostics()
        diagnostics["climate"] = _diagnostic("climate", "mixed", operations=[
            {"operation": "warming", "urgency": "medium"},
        ])
        diagnostics["mediation"] = _diagnostic("mediation", "mixed", operations=[
            {"operation": "cooling", "urgency": "medium"},
        ])
        result, _ = synthesize_diagnostics(diagnostics)

        self.assertFalse(any(item["operation"] in {"warm", "cool"} for item in result.favorable_operations))
        self.assertEqual(
            {
                item["operation"]
                for item in result.caution_operations
                if item.get("reason") == "directional_conflict_requires_context"
            },
            {"warm", "cool"},
        )

    def test_missing_diagnostic_returns_partial_undetermined_result(self):
        diagnostics = _complete_diagnostics()
        del diagnostics["mediation"]
        result, evidence = synthesize_diagnostics(diagnostics)

        self.assertEqual(result.confidence, ConfidenceLevel.UNDETERMINED)
        issue = next(item for item in result.diagnostic_conflicts if item["type"] == "incomplete_diagnostics")
        self.assertEqual(issue["missing_modules"], ["mediation"])
        self.assertEqual(evidence[0].reliability, ConfidenceLevel.UNDETERMINED)
