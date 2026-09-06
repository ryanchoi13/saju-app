from unittest import TestCase

from app.engine.constants import GAN_WUXING, ZHI_WUXING
from app.engine.core.models import PillarFact, TransformationStatus
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


def _resolve(pillars):
    hidden = calculate_hidden_stems(pillars)
    return resolve_relationships(
        calculate_relationship_candidates(pillars), pillars,
        calculate_roots(pillars, hidden), calculate_exposed_stems(pillars, hidden),
    )


class RelationshipResolverTests(TestCase):
    def test_adjacent_clash_is_active_when_uncontested(self):
        relationships, _ = _resolve({"year": _pillar("甲", "子"), "month": _pillar("丙", "午")})
        clash = next(item for item in relationships if item.type == "branch_clash")
        self.assertEqual(clash.action_status, "active")

    def test_non_adjacent_clash_remains_conditional(self):
        relationships, _ = _resolve({"year": _pillar("甲", "子"), "day": _pillar("丙", "午")})
        clash = next(item for item in relationships if item.type == "branch_clash")
        self.assertEqual(clash.action_status, "conditional")

    def test_shared_member_marks_competing_relationships(self):
        pillars = {
            "year": _pillar("甲", "子"),
            "month": _pillar("己", "丑"),
            "day": _pillar("丙", "午"),
        }
        relationships, _ = _resolve(pillars)
        six = next(item for item in relationships if item.type == "branch_six_combination")
        self.assertEqual(six.action_status, "competing")
        self.assertTrue(six.competing_relationship_ids)

    def test_transformation_is_never_established_in_v1(self):
        relationships, _ = _resolve({"year": _pillar("甲", "子"), "month": _pillar("己", "丑")})
        combination = next(item for item in relationships if item.type == "stem_combination")
        self.assertIn(
            combination.transformation.status,
            {TransformationStatus.POSSIBLE, TransformationStatus.CONDITIONAL},
        )
        self.assertIsNot(combination.transformation.status, TransformationStatus.ESTABLISHED)

    def test_evidence_preserves_inputs_and_confidence(self):
        relationships, evidence = _resolve({"year": _pillar("甲", "子"), "month": _pillar("丙", "午")})
        self.assertEqual(len(relationships), len(evidence))
        self.assertEqual(relationships[0].evidence_ids, [evidence[0].id])
        self.assertIn("adjacent", evidence[0].source_values)

    def test_unknown_hour_is_not_fabricated(self):
        relationships, _ = _resolve({"day": _pillar("甲", "子"), "hour": None})
        self.assertNotIn("hour", {m["pillar"] for item in relationships for m in item.members})
