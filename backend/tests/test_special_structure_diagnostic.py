from unittest import TestCase

from app.engine.constants import GAN_WUXING, ZHI_WUXING
from app.engine.core.models import (
    ConfidenceLevel,
    DiagnosticResult,
    PillarFact,
    RelationshipResult,
    TransformationResult,
    TransformationStatus,
)
from app.engine.diagnostics.special_structure import diagnose_special_structure
from app.engine.facts.element_inventory import calculate_element_inventory
from app.engine.facts.hidden_stems import calculate_hidden_stems
from app.engine.facts.rooting import calculate_roots
from app.engine.facts.ten_gods import calculate_ten_gods


def _pillar(stem: str, branch: str) -> PillarFact:
    return PillarFact(
        stem=stem,
        branch=branch,
        ganji=f"{stem}{branch}",
        stem_element=GAN_WUXING[stem],
        stem_yin_yang="yang",
        branch_element=ZHI_WUXING[branch],
        branch_yin_yang="yang",
    )


def _strength(conclusion: str, status: str = "completed") -> DiagnosticResult:
    return DiagnosticResult(
        module="strength",
        status=status,
        conclusion=conclusion,
        confidence=ConfidenceLevel.HIGH,
    )


def _diagnose(pillars, strength, relationships=None):
    hidden = calculate_hidden_stems(pillars)
    roots = calculate_roots(pillars, hidden)
    return diagnose_special_structure(
        pillars["day"].stem,
        pillars,
        calculate_element_inventory(pillars, hidden),
        roots,
        calculate_ten_gods(pillars["day"].stem, pillars, hidden),
        relationships or [],
        _strength(strength),
    )


def _transformation_relation(action_status="active", competing=None, transformation_status=TransformationStatus.CONDITIONAL):
    return RelationshipResult(
        id="relationship:stem-combination:day-month",
        type="stem_combination",
        members=[
            {"pillar": "day", "position": "visible_stem", "symbol": "甲"},
            {"pillar": "month", "position": "visible_stem", "symbol": "己"},
        ],
        existence="confirmed",
        action_status=action_status,
        transformation=TransformationResult(
            target_element="土",
            status=transformation_status,
            reasons=["월령과 별도 교차 확인"],
        ),
        competing_relationship_ids=competing or [],
        confidence=ConfidenceLevel.MEDIUM,
    )


class SpecialStructureDiagnosticTests(TestCase):
    def test_extremely_weak_unrooted_single_family_establishes_follow_wealth(self):
        result, evidence = _diagnose({
            "year": _pillar("戊", "午"),
            "month": _pillar("己", "丑"),
            "day": _pillar("甲", "申"),
        }, "extremely_weak")
        self.assertEqual(result.conclusion, "follow_wealth")
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.confidence, ConfidenceLevel.HIGH)
        self.assertFalse(evidence[0].source_values["fixed_score_used"])

    def test_visible_resource_prevents_follow_structure_confirmation(self):
        result, _ = _diagnose({
            "year": _pillar("壬", "子"),
            "month": _pillar("戊", "戌"),
            "day": _pillar("甲", "申"),
        }, "extremely_weak")
        follow = next(item for item in result.signals if item["type"] == "follow_structure")
        self.assertNotEqual(follow["formation_status"], "established")
        self.assertIn("indirect_resource", follow["visible_supporting_ten_gods"])
        self.assertTrue(any(item["operation"] == "preserve_ordinary_diagnosis" for item in result.recommended_operations))

    def test_extremely_strong_rooted_single_force_establishes_dominant_wood(self):
        result, _ = _diagnose({
            "year": _pillar("乙", "卯"),
            "month": _pillar("甲", "寅"),
            "day": _pillar("甲", "卯"),
        }, "extremely_strong")
        self.assertEqual(result.conclusion, "dominant_wood")
        dominant = next(item for item in result.signals if item["type"] == "dominant_structure")
        self.assertTrue(dominant["main_month_root"])
        self.assertEqual(dominant["formation_status"], "established")

    def test_visible_output_keeps_dominant_structure_conditional(self):
        result, _ = _diagnose({
            "year": _pillar("丙", "午"),
            "month": _pillar("甲", "寅"),
            "day": _pillar("甲", "卯"),
        }, "extremely_strong")
        dominant = next(item for item in result.signals if item["type"] == "dominant_structure")
        self.assertEqual(dominant["formation_status"], "conditional")
        self.assertEqual(result.status, "conditional")

    def test_day_stem_transformation_requires_month_support_and_no_day_root(self):
        result, _ = _diagnose({
            "year": _pillar("戊", "戌"),
            "month": _pillar("己", "丑"),
            "day": _pillar("甲", "申"),
        }, "balanced", [_transformation_relation(transformation_status=TransformationStatus.ESTABLISHED)])
        self.assertEqual(result.conclusion, "transform_to_土")
        transformed = next(item for item in result.signals if item["type"] == "transformation_structure")
        self.assertEqual(transformed["formation_status"], "established")

    def test_conditional_conversion_is_not_certified_by_structure_wrapper(self):
        result, _ = _diagnose({
            "year": _pillar("戊", "戌"), "month": _pillar("己", "丑"), "day": _pillar("甲", "申"),
        }, "balanced", [_transformation_relation()])
        converted = next(s for s in result.signals if s['type'] == 'transformation_structure')
        self.assertEqual(converted['formation_status'], 'conditional')

    def test_negative_conversion_is_not_reopened_as_conditional(self):
        result, _ = _diagnose({
            "year": _pillar("戊", "戌"), "month": _pillar("己", "丑"), "day": _pillar("甲", "申"),
        }, "balanced", [_transformation_relation(transformation_status=TransformationStatus.NOT_ESTABLISHED)])
        converted = next(s for s in result.signals if s['type'] == 'transformation_structure')
        self.assertEqual(converted['formation_status'], 'not_established')

    def test_competing_transformation_stays_conditional(self):
        result, _ = _diagnose({
            "year": _pillar("戊", "戌"),
            "month": _pillar("己", "丑"),
            "day": _pillar("甲", "申"),
        }, "balanced", [_transformation_relation("competing", ["relationship:control"])])
        transformed = next(item for item in result.signals if item["type"] == "transformation_structure")
        self.assertEqual(transformed["formation_status"], "conditional")
        self.assertEqual(result.conclusion, "special_structure_possible")

    def test_balanced_chart_prefers_ordinary_structure(self):
        result, _ = _diagnose({
            "year": _pillar("壬", "子"),
            "month": _pillar("丙", "午"),
            "day": _pillar("甲", "寅"),
        }, "balanced")
        self.assertEqual(result.conclusion, "ordinary_structure_preferred")
        self.assertEqual(result.status, "completed")

    def test_missing_month_is_insufficient(self):
        pillars = {"day": _pillar("甲", "申")}
        hidden = calculate_hidden_stems(pillars)
        result, evidence = diagnose_special_structure(
            "甲",
            pillars,
            calculate_element_inventory(pillars, hidden),
            calculate_roots(pillars, hidden),
            calculate_ten_gods("甲", pillars, hidden),
            [],
            _strength("balanced"),
        )
        self.assertEqual(result.status, "insufficient")
        self.assertEqual(evidence, [])
