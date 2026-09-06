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
    def test_rooted_water_mediates_active_metal_wood_control(self):
        result, evidence = _diagnose({
            "year": _pillar("庚", "酉"),
            "month": _pillar("甲", "寅"),
            "day": _pillar("壬", "子"),
        })
        signal = next(item for item in result.signals if item["controller_element"] == "金")
        self.assertEqual(signal["mediator_element"], "水")
        self.assertEqual(signal["mediation_status"], "established")
        self.assertEqual(result.conclusion, "mediation_available")
        self.assertFalse(evidence[0].source_values["fixed_score_used"])

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
