from unittest import TestCase

from app.engine.constants import GAN_WUXING, ZHI_WUXING
from app.engine.core.models import PillarFact, RelationshipCandidateType
from app.engine.facts.element_inventory import calculate_element_inventory
from app.engine.facts.hidden_stems import calculate_hidden_stems
from app.engine.facts.relationship_candidates import calculate_relationship_candidates


def _pillar(stem: str, branch: str) -> PillarFact:
    return PillarFact(
        stem=stem, branch=branch, ganji=f"{stem}{branch}",
        stem_element=GAN_WUXING[stem], stem_yin_yang="yang",
        branch_element=ZHI_WUXING[branch], branch_yin_yang="yang",
    )


class ElementInventoryTests(TestCase):
    def test_positions_are_preserved_without_scores(self):
        pillars = {"day": _pillar("甲", "辰"), "hour": None}
        result = calculate_element_inventory(pillars, calculate_hidden_stems(pillars))
        self.assertEqual(
            [(item.position, item.symbol, item.element) for item in result.occurrences],
            [("visible_stem", "甲", "木"), ("branch", "辰", "土"),
             ("hidden_stem", "戊", "土"), ("hidden_stem", "乙", "木"),
             ("hidden_stem", "癸", "水")],
        )
        self.assertTrue(all(not hasattr(item, "score") for item in result.occurrences))
        self.assertNotIn("hour", {item.pillar for item in result.occurrences})


class RelationshipCandidateTests(TestCase):
    def test_pair_candidates_are_detected_without_activation(self):
        pillars = {"year": _pillar("甲", "子"), "month": _pillar("己", "午")}
        result = calculate_relationship_candidates(pillars)
        kinds = {item.type for item in result.items}
        self.assertIn(RelationshipCandidateType.STEM_COMBINATION, kinds)
        self.assertIn(RelationshipCandidateType.BRANCH_CLASH, kinds)
        self.assertTrue(all(not hasattr(item, "action_status") for item in result.items))

    def test_three_and_directional_combinations(self):
        three = calculate_relationship_candidates({
            "year": _pillar("甲", "申"), "month": _pillar("丙", "子"), "day": _pillar("戊", "辰")
        })
        self.assertIn(RelationshipCandidateType.BRANCH_THREE_COMBINATION, {x.type for x in three.items})
        directional = calculate_relationship_candidates({
            "year": _pillar("甲", "寅"), "month": _pillar("丙", "卯"), "day": _pillar("戊", "辰")
        })
        self.assertIn(RelationshipCandidateType.BRANCH_DIRECTIONAL_COMBINATION, {x.type for x in directional.items})

    def test_half_combination_harm_break_and_punishment(self):
        cases = [
            (("申", "子"), RelationshipCandidateType.BRANCH_HALF_COMBINATION),
            (("子", "未"), RelationshipCandidateType.BRANCH_HARM),
            (("子", "酉"), RelationshipCandidateType.BRANCH_BREAK),
            (("子", "卯"), RelationshipCandidateType.BRANCH_PUNISHMENT),
            (("辰", "辰"), RelationshipCandidateType.BRANCH_PUNISHMENT),
        ]
        for branches, expected in cases:
            with self.subTest(branches=branches):
                result = calculate_relationship_candidates({
                    "year": _pillar("甲", branches[0]), "day": _pillar("丙", branches[1])
                })
                self.assertIn(expected, {item.type for item in result.items})

    def test_unknown_hour_is_not_fabricated(self):
        result = calculate_relationship_candidates({"day": _pillar("甲", "子"), "hour": None})
        self.assertNotIn("hour", {m.pillar for item in result.items for m in item.members})
