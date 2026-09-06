from unittest import TestCase

from app.engine.constants import GAN_WUXING, ZHI_WUXING
from app.engine.core.models import PillarFact
from app.engine.diagnostics.climate import CLIMATE_BASELINE_VERSION, diagnose_climate
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


def _diagnose(pillars):
    hidden = calculate_hidden_stems(pillars)
    roots = calculate_roots(pillars, hidden)
    exposed = calculate_exposed_stems(pillars, hidden)
    relationships, _ = resolve_relationships(
        calculate_relationship_candidates(pillars), pillars, roots, exposed
    )
    return diagnose_climate(
        pillars, calculate_element_inventory(pillars, hidden), roots, relationships
    )


class ClimateDiagnosticTests(TestCase):
    def test_winter_checks_warming_and_stabilizing_supply(self):
        result, evidence = _diagnose({
            "year": _pillar("戊", "辰"),
            "month": _pillar("壬", "子"),
            "day": _pillar("丙", "午"),
        })
        self.assertEqual(result.conclusion, "very_cold_wet")
        operations = {item["operation"]: item for item in result.recommended_operations}
        self.assertEqual(operations["warming"]["availability"], "visible_and_rooted")
        self.assertIn("stabilizing", operations)
        self.assertFalse(evidence[0].source_values["single_yongshin_selected"])

    def test_summer_checks_water_availability_without_declaring_yongshin(self):
        result, _ = _diagnose({
            "year": _pillar("丙", "午"),
            "month": _pillar("丁", "午"),
            "day": _pillar("戊", "戌"),
        })
        cooling = next(item for item in result.recommended_operations if item["operation"] == "cooling")
        self.assertEqual(result.conclusion, "very_hot_dry")
        self.assertEqual(cooling["availability"], "absent")
        self.assertEqual(cooling["urgency"], "high")

    def test_baseline_convention_is_explicit(self):
        result, _ = _diagnose({"month": _pillar("戊", "辰"), "day": _pillar("甲", "寅")})
        self.assertEqual(result.signals[0]["baseline_version"], CLIMATE_BASELINE_VERSION)
        self.assertEqual(result.conclusion, "mild_wet")

    def test_month_competition_keeps_diagnosis_conditional(self):
        result, _ = _diagnose({
            "year": _pillar("壬", "子"),
            "month": _pillar("丁", "午"),
            "day": _pillar("甲", "辰"),
        })
        self.assertEqual(result.status, "conditional")
        self.assertEqual(result.confidence.value, "low")

    def test_missing_month_is_insufficient(self):
        pillars = {"day": _pillar("甲", "寅")}
        hidden = calculate_hidden_stems(pillars)
        result, evidence = diagnose_climate(
            pillars, calculate_element_inventory(pillars, hidden),
            calculate_roots(pillars, hidden), [],
        )
        self.assertEqual(result.status, "insufficient")
        self.assertEqual(evidence, [])
