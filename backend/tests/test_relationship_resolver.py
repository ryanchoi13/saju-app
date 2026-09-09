from unittest import TestCase
import json
from pathlib import Path

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
    def test_sourced_flanking_and_separated_partners(self):
        fixture = json.loads((Path(__file__).parent / 'fixtures/classical_positional_cases.json').read_text())
        for case in fixture['cases']:
            expected = case['expected_competition']
            if expected is None:
                continue
            with self.subTest(case=case['id']):
                relationships, _ = _resolve(dict(zip(
                    ['year', 'month', 'day', 'hour'], [_pillar(*p) for p in case['pillars']])))
                pair = next(r for r in relationships if r.type == 'stem_combination'
                            and {m['pillar'] for m in r.members} == set(case['target']))
                self.assertEqual(pair.action_status == 'competing', expected)
                self.assertEqual(bool(pair.competing_relationship_ids), expected)
                self.assertTrue(all(a['function_state'] == 'undetermined'
                                    for a in pair.member_function_assessments))
                for competitor_id in pair.competing_relationship_ids:
                    competitor = next(r for r in relationships if r.id == competitor_id)
                    self.assertIn(pair.id, competitor.competing_relationship_ids)

    def test_stem_overlap_does_not_establish_competition_or_loss_of_role(self):
        relationships, evidence = _resolve(dict(zip(
            ['year', 'month', 'day', 'hour'],
            [_pillar(*p) for p in ['癸未', '辛酉', '甲申', '丙寅']],
        )))
        pair = next(r for r in relationships if r.type == 'stem_combination')
        self.assertEqual(pair.action_status, 'conditional')
        self.assertFalse(pair.competing_relationship_ids)
        self.assertTrue(pair.overlapping_relationship_ids)
        metal = next(a for a in pair.member_function_assessments if a['stem'] == '辛')
        self.assertEqual(metal['role_to_day_master'], 'direct_officer')
        self.assertTrue(metal['root_connections'])
        self.assertEqual(metal['function_state'], 'retained')
        self.assertEqual(metal['effect_rule'], 'seasonal-vigorous-month-role-retained-v1')
        self.assertTrue(set(metal['evidence_ids']) <= {e.id for e in evidence})

    def test_combination_with_day_master_has_separate_scope(self):
        relationships, _ = _resolve({'year': _pillar('己', '丑'), 'day': _pillar('甲', '寅')})
        pair = next(r for r in relationships if r.type == 'stem_combination')
        self.assertEqual(len(pair.member_function_assessments), 2)
        self.assertTrue(all(a['scope'] == 'day_master_combination'
                            and a['function_state'] == 'undetermined'
                            for a in pair.member_function_assessments))

    def test_adjacent_clash_is_active_when_uncontested(self):
        relationships, _ = _resolve({"year": _pillar("甲", "子"), "month": _pillar("丙", "午")})
        clash = next(item for item in relationships if item.type == "branch_clash")
        self.assertEqual(clash.action_status, "active")

    def test_non_adjacent_clash_remains_conditional(self):
        relationships, _ = _resolve({"year": _pillar("甲", "子"), "day": _pillar("丙", "午")})
        clash = next(item for item in relationships if item.type == "branch_clash")
        self.assertEqual(clash.action_status, "conditional")

    def test_shared_branch_member_is_context_not_proven_competition(self):
        pillars = {
            "year": _pillar("甲", "子"),
            "month": _pillar("己", "丑"),
            "day": _pillar("丙", "午"),
        }
        relationships, _ = _resolve(pillars)
        six = next(item for item in relationships if item.type == "branch_six_combination")
        self.assertEqual(six.action_status, "conditional")
        self.assertFalse(six.competing_relationship_ids)
        self.assertTrue(six.overlapping_relationship_ids)

    def test_incomplete_chart_cannot_establish_transformation(self):
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
