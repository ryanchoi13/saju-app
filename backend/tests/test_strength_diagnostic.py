from unittest import TestCase

from app.engine.constants import GAN_WUXING, ZHI_WUXING
from app.engine.core.models import PillarFact
from app.engine.diagnostics.strength import diagnose_strength
from app.engine.facts.hidden_stems import calculate_hidden_stems
from app.engine.facts.relationship_candidates import calculate_relationship_candidates
from app.engine.facts.rooting import calculate_exposed_stems, calculate_roots
from app.engine.facts.ten_gods import calculate_ten_gods
from app.engine.relationships.resolver import resolve_relationships


def _pillar(stem: str, branch: str) -> PillarFact:
    return PillarFact(
        stem=stem, branch=branch, ganji=f"{stem}{branch}",
        stem_element=GAN_WUXING[stem], stem_yin_yang="yang",
        branch_element=ZHI_WUXING[branch], branch_yin_yang="yang",
    )


def _diagnose(pillars):
    day_master = pillars["day"].stem
    hidden = calculate_hidden_stems(pillars)
    roots = calculate_roots(pillars, hidden)
    exposed = calculate_exposed_stems(pillars, hidden)
    ten_gods = calculate_ten_gods(day_master, pillars, hidden)
    relationships, _ = resolve_relationships(
        calculate_relationship_candidates(pillars), pillars, roots, exposed
    )
    return diagnose_strength(day_master, pillars, roots, ten_gods, relationships)


class StrengthDiagnosticTests(TestCase):
    def test_same_season_exact_root_and_support_can_be_extremely_strong(self):
        result, evidence = _diagnose({
            "year": _pillar("壬", "子"),
            "month": _pillar("甲", "寅"),
            "day": _pillar("甲", "寅"),
        })
        self.assertEqual(result.conclusion, "extremely_strong")
        self.assertEqual(result.status, "completed")
        self.assertFalse(evidence[0].source_values["fixed_score_used"])

    def test_adverse_season_without_root_or_support_is_extremely_weak(self):
        result, _ = _diagnose({
            "year": _pillar("丙", "午"),
            "month": _pillar("庚", "申"),
            "day": _pillar("甲", "午"),
        })
        self.assertEqual(result.conclusion, "extremely_weak")

    def test_adverse_season_with_root_and_support_stays_balanced(self):
        result, _ = _diagnose({
            "year": _pillar("壬", "子"),
            "month": _pillar("庚", "申"),
            "day": _pillar("甲", "寅"),
        })
        self.assertEqual(result.conclusion, "balanced")
        self.assertTrue(result.counter_evidence)

    def test_competing_relationship_makes_result_conditional(self):
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
        result, evidence = diagnose_strength(
            "甲", pillars, calculate_roots(pillars, hidden),
            calculate_ten_gods("甲", pillars, hidden), [],
        )
        self.assertEqual(result.status, "insufficient")
        self.assertEqual(evidence, [])
