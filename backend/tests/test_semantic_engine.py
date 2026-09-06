from datetime import date
from unittest import TestCase

from app.engine.core.models import (
    ActivatedState,
    BirthInput,
    ConfidenceLevel,
    DiagnosticResult,
    MyeongriCoreResult,
    SemanticState,
    SynthesisResult,
    TimingResult,
)
from app.engine.semantic.engine import build_semantic_state
from app.engine.semantic.queries import build_service_query


def _synthesis():
    return SynthesisResult(
        overall_structure={"ordinary": "direct_wealth", "special": None},
        strength_state="balanced",
        climate_state={"state": "mild_balanced"},
        favorable_operations=[{
            "operation": "warm", "elements": ["火"], "evidence_ids": ["e:climate"]
        }],
        caution_operations=[{
            "operation": "drain", "elements": ["水"], "evidence_ids": ["e:strength"]
        }],
        summary="근거를 보존한 종합",
        evidence_ids=["e:synthesis"],
        confidence=ConfidenceLevel.MEDIUM,
    )


class SemanticEngineTests(TestCase):
    def test_semantic_state_uses_tokens_without_scores(self):
        state, evidence = build_semantic_state(
            _synthesis(),
            ActivatedState(activated_ten_gods=["direct_wealth", "eating_god"]),
        )
        self.assertEqual(state.favorable_elements, ["火"])
        self.assertIn("managed_resources_and_results", state.indicators["activated_topics"])
        self.assertEqual(state.indicators["score_used"], "false")
        self.assertFalse(evidence[0].source_values["shensha_can_override_core"])

    def test_lifetime_query_includes_all_luck_cycles_but_no_calendar_overlay(self):
        core = self._core()
        view = build_service_query(core, "lifetime_overall")
        self.assertEqual(view["scope"], "natal+all_luck_cycles")
        self.assertEqual(set(view["timing"]), {"luck_cycles"})
        self.assertNotIn("annual", view["timing"])
        self.assertIsNotNone(view["activated_state"])

    def test_annual_query_includes_only_daeyun_and_annual(self):
        core = self._core()
        view = build_service_query(core, "annual_overall")
        self.assertEqual(set(view["timing"]), {"luck_cycle", "annual"})
        self.assertNotIn("monthly", view["timing"])
        self.assertIsNotNone(view["activated_state"])

    def test_health_query_blocks_medical_claims(self):
        view = build_service_query(self._core(), "health")
        self.assertEqual(
            set(view["diagnostics"]), {"strength", "climate", "pathology", "mediation"}
        )
        self.assertFalse(view["constraints"]["medical_claim_allowed"])

    @staticmethod
    def _core():
        synthesis = _synthesis()
        semantic = SemanticState(evidence_ids=["e:semantic"])
        return MyeongriCoreResult(
            input=BirthInput(
                name="테스트", gender="male", birth_date=date(1990, 5, 15),
                time_unknown=True,
            ),
            synthesis=synthesis,
            diagnostics={
                name: DiagnosticResult(
                    module=name,
                    status="completed",
                    conclusion="fixture",
                )
                for name in ("strength", "climate", "pathology", "mediation")
            },
            semantic_state=semantic,
            timing=TimingResult(
                luck_cycle={"current": {"pillar": {"ganji": "壬午"}}},
                annual={"pillar": {"ganji": "丙午"}},
                monthly={"pillar": {"ganji": "丙申"}},
                daily={"pillar": {"ganji": "甲申"}},
            ),
            activated_state=ActivatedState(activated_ten_gods=["direct_wealth"]),
        )
