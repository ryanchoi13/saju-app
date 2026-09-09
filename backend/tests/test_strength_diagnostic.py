from unittest import TestCase

from app.engine.constants import GAN_WUXING, ZHI_WUXING
from app.engine.core.models import PillarFact
from app.engine.diagnostics.strength import diagnose_strength
from app.engine.facts.hidden_stems import calculate_hidden_stems
from app.engine.facts.relationship_candidates import calculate_relationship_candidates
from app.engine.facts.rooting import calculate_exposed_stems, calculate_roots
from app.engine.facts.ten_gods import calculate_ten_gods
from app.engine.relationships.resolver import resolve_relationships
from app.engine.synthesis.engine import synthesize_diagnostics


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

    def test_hidden_resource_prevents_claiming_all_support_is_absent(self):
        result, _ = _diagnose({
            "year": _pillar("丙", "午"),
            "month": _pillar("庚", "申"),
            "day": _pillar("甲", "午"),
        })
        # 申 contains 壬: no visible helper is not the same as no support.
        self.assertEqual(result.conclusion, "weak")

    def test_opposing_observations_do_not_prove_balance(self):
        result, _ = _diagnose({
            "year": _pillar("壬", "子"),
            "month": _pillar("庚", "申"),
            "day": _pillar("甲", "寅"),
        })
        self.assertEqual(result.conclusion, "undetermined")
        self.assertEqual(result.status, "conditional")
        self.assertTrue(result.counter_evidence)

    def test_out_of_season_vigorous_root_without_visible_helper_is_not_automatically_weak(self):
        # Rule-based counterexamples across four elements, not named-chart
        # exceptions or alleged real birth charts.
        for month, day in [("庚酉", "甲寅"), ("壬子", "丙午"), ("丙午", "庚申"), ("甲卯", "壬子")]:
            with self.subTest(month=month, day=day):
                result, evidence = _diagnose({"month": _pillar(*month), "day": _pillar(*day)})
                self.assertEqual(result.conclusion, "undetermined")
                self.assertEqual(result.status, "conditional")
                self.assertTrue(evidence[0].source_values["season_only_weakness_blocked"])

    def test_growth_root_and_vigorous_root_both_require_review_out_of_season(self):
        for day in ("甲亥", "甲寅"):
            with self.subTest(day=day):
                result, _ = _diagnose({"month": _pillar("庚", "酉"), "day": _pillar(*day)})
                self.assertEqual(result.conclusion, "undetermined")

    def test_root_review_does_not_generate_confirmed_support_in_synthesis(self):
        result, _ = _diagnose({"month": _pillar("庚", "酉"), "day": _pillar("甲", "寅")})
        synthesis, _ = synthesize_diagnostics({"strength": result})
        self.assertFalse(any(o["operation"] == "support" for o in synthesis.favorable_operations))

    def test_helpers_sharing_one_storage_root_are_not_independent_root_locations(self):
        result, _ = _diagnose(dict(zip(
            ["year", "month", "day", "hour"],
            [_pillar(*p) for p in ["乙丑", "甲申", "甲申", "辛未"]],
        )))
        support = next(s for s in result.signals if s["step"] == "support")
        self.assertEqual(len(support["visible_support_profiles"]), 2)
        self.assertEqual(support["distinct_root_anchor_ids"], ["root:hour:乙"])
        profiles = support["visible_support_profiles"]
        self.assertEqual({r["category"] for p in profiles for r in p["root_contexts"]}, {"storage"})
        self.assertEqual(result.conclusion, "weak")
        self.assertTrue(all(r['effectiveness'] == 'reduced' for p in profiles for r in p['root_contexts']))

    def test_unrooted_visible_support_remains_visible_but_is_not_given_a_root(self):
        result, _ = _diagnose({"year": _pillar("壬", "午"), "month": _pillar("丙", "午"),
                               "day": _pillar("甲", "戌")})
        support = next(s for s in result.signals if s["step"] == "support")
        self.assertTrue(support["visible_ten_gods"])
        self.assertEqual(support["visible_support_profiles"][0]["root_contexts"], [])
        self.assertEqual(support["distinct_root_anchor_ids"], [])

    def test_classical_weak_case_is_not_certified_as_balanced(self):
        result, _ = _diagnose(dict(zip(
            ["year", "month", "day", "hour"],
            [_pillar(*p) for p in ["乙丑", "甲申", "甲申", "辛未"]],
        )))
        self.assertEqual(result.conclusion, "weak")
        self.assertEqual(result.status, "completed")
        root = next(s for s in result.signals if s['step'] == 'rooting')
        self.assertEqual(root['root_count'], 1)
        self.assertEqual(root['root_contexts'][0]['hidden_stem'], '乙')
        self.assertEqual(root['root_contexts'][0]['hidden_role'], 'residual')
        self.assertFalse(any(o.get('when') for o in result.recommended_operations
                             if o['operation'] == 'preserve_balance'))

    def test_hour_root_branch_relations_are_retained_without_declaring_damage(self):
        result, _ = _diagnose(dict(zip(
            ["year", "month", "day", "hour"],
            [_pillar(*p) for p in ["癸未", "辛酉", "甲申", "丙寅"]],
        )))
        rooting = next(s for s in result.signals if s['step'] == 'rooting')
        hour = next(r for r in rooting['root_contexts'] if r['branch_pillar'] == 'hour')
        self.assertTrue(any(i.startswith('branch_clash:') for i in hour['related_relationship_ids']))
        self.assertEqual(hour['effectiveness'], 'undetermined')

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
