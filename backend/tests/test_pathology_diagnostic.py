from unittest import TestCase

from app.engine.core.models import (
    ConfidenceLevel,
    DiagnosticResult,
    RelationshipResult,
)
from app.engine.diagnostics.pathology import diagnose_pathology


def _diagnostic(module, conclusion, status="completed", counter=None, operations=None, signals=None):
    return DiagnosticResult(
        module=module, status=status, conclusion=conclusion,
        counter_evidence=counter or [], recommended_operations=operations or [],
        signals=signals or [], confidence=ConfidenceLevel.MEDIUM,
    )


def _relationship(kind, status, relation_id="rel-1", day=False):
    return RelationshipResult(
        id=relation_id, type=kind,
        members=[{"pillar": "day" if day else "month", "position": "branch", "symbol": "子"}],
        existence="confirmed", action_status=status,
        confidence=ConfidenceLevel.MEDIUM,
    )


class PathologyDiagnosticTests(TestCase):
    def test_structure_damage_and_climate_extreme_remain_separate(self):
        result, evidence = diagnose_pathology(
            _diagnostic("structure", "direct_officer", "conditional", ["월지 충"]),
            _diagnostic("strength", "balanced", signals=[{"step": "rooting", "root_count": 1}]),
            _diagnostic("climate", "very_hot_dry", operations=[{
                "operation": "cooling", "element": "水", "availability": "absent", "urgency": "high"
            }]),
            [],
        )
        self.assertEqual([item["type"] for item in result.signals[:2]], ["structural_damage", "climate_extreme"])
        self.assertEqual(result.status, "conditional")
        self.assertFalse(evidence[0].source_values["medical_inference_performed"])

    def test_competing_relationship_creates_conflict_bottleneck(self):
        result, _ = diagnose_pathology(
            _diagnostic("structure", "peer"),
            _diagnostic("strength", "balanced", signals=[{"step": "rooting", "root_count": 1}]),
            _diagnostic("climate", "mild_balanced"),
            [_relationship("branch_clash", "competing")],
        )
        self.assertEqual(result.conclusion, "conflict")
        self.assertEqual(result.status, "conditional")

    def test_extremely_weak_without_root_keeps_two_bottlenecks(self):
        result, _ = diagnose_pathology(
            _diagnostic("structure", "direct_wealth"),
            _diagnostic("strength", "extremely_weak", signals=[{"step": "rooting", "root_count": 0}]),
            _diagnostic("climate", "mild_balanced"),
            [],
        )
        kinds = [item["type"] for item in result.signals]
        self.assertIn("unstable_root", kinds)
        self.assertIn("deficiency", kinds)
        self.assertTrue(all(item["health_interpretation"] is False for item in result.signals))

    def test_day_stem_binding_is_preserved_separately(self):
        result, _ = diagnose_pathology(
            _diagnostic("structure", "direct_resource"),
            _diagnostic("strength", "balanced", signals=[{"step": "rooting", "root_count": 1}]),
            _diagnostic("climate", "mild_balanced"),
            [_relationship("stem_combination", "conditional", day=True)],
        )
        self.assertIn("bound_element", [item["type"] for item in result.signals])

    def test_insufficient_input_stops_diagnosis(self):
        result, evidence = diagnose_pathology(
            _diagnostic("structure", None, "insufficient"),
            _diagnostic("strength", "balanced"),
            _diagnostic("climate", "mild_balanced"),
            [],
        )
        self.assertEqual(result.status, "insufficient")
        self.assertEqual(evidence, [])
