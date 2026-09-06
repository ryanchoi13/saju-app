from unittest import TestCase

from app.engine.constants import GAN_WUXING, ZHI_WUXING
from app.engine.core.models import PillarFact
from app.engine.diagnostics.structure import diagnose_structure
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
    hidden = calculate_hidden_stems(pillars)
    ten_gods = calculate_ten_gods(pillars["day"].stem, pillars, hidden)
    roots = calculate_roots(pillars, hidden)
    exposed = calculate_exposed_stems(pillars, hidden)
    relationships, _ = resolve_relationships(
        calculate_relationship_candidates(pillars), pillars, roots, exposed
    )
    return diagnose_structure(pillars, hidden, ten_gods, exposed, roots, relationships)


class StructureDiagnosticTests(TestCase):
    def test_exposed_main_month_stem_becomes_clear_primary(self):
        result, evidence = _diagnose({
            "year": _pillar("甲", "子"),
            "month": _pillar("戊", "辰"),
            "day": _pillar("甲", "寅"),
        })
        primary = next(item for item in result.signals if item["role_in_diagnosis"] == "primary")
        self.assertEqual(primary["source_stem"], "戊")
        self.assertEqual(primary["source_role"], "main")
        self.assertEqual(primary["exposed_pillars"], ["month"])
        self.assertEqual(result.status, "completed")
        self.assertEqual(result.evidence_ids, [evidence[0].id])

    def test_unexposed_main_qi_remains_conditional(self):
        result, _ = _diagnose({
            "year": _pillar("甲", "子"),
            "month": _pillar("丙", "辰"),
            "day": _pillar("甲", "寅"),
        })
        self.assertEqual(result.status, "conditional")
        self.assertEqual(result.confidence.value, "low")

    def test_multiple_exposed_month_stems_preserve_alternatives(self):
        result, _ = _diagnose({
            "year": _pillar("乙", "子"),
            "month": _pillar("戊", "辰"),
            "day": _pillar("甲", "寅"),
            "hour": _pillar("癸", "亥"),
        })
        exposed = [item for item in result.signals if item["exposed_pillars"]]
        self.assertGreaterEqual(len(exposed), 2)
        self.assertEqual(result.status, "conditional")
        self.assertTrue(any("복수" in item for item in result.counter_evidence))

    def test_active_month_clash_is_counter_evidence(self):
        result, _ = _diagnose({
            "year": _pillar("甲", "子"),
            "month": _pillar("戊", "午"),
            "day": _pillar("甲", "寅"),
        })
        self.assertEqual(result.status, "conditional")
        self.assertTrue(any("형충파해" in item for item in result.counter_evidence))

    def test_missing_month_is_insufficient(self):
        pillars = {"day": _pillar("甲", "寅")}
        hidden = calculate_hidden_stems(pillars)
        result, evidence = diagnose_structure(
            pillars, hidden, calculate_ten_gods("甲", pillars, hidden),
            calculate_exposed_stems(pillars, hidden), calculate_roots(pillars, hidden), [],
        )
        self.assertEqual(result.status, "insufficient")
        self.assertEqual(evidence, [])
