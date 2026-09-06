from datetime import date, time
from unittest import TestCase

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.semantic import build_service_query


class CoreOrchestratorTests(TestCase):
    def test_known_time_runs_every_core_stage(self):
        result = calculate_myeongri_core(
            BirthInput(
                name="테스트",
                gender="male",
                birth_date=date(1990, 5, 15),
                birth_time=time(9, 30),
            ),
            target_date=date(2026, 9, 7),
        )
        self.assertEqual(result.schema_version, "myeongri-core-v1")
        self.assertEqual(set(result.diagnostics), {
            "structure", "strength", "climate", "pathology", "mediation", "special_structure"
        })
        self.assertIsNotNone(result.natal_facts.pillars["hour"])
        self.assertTrue(result.timing.annual)
        self.assertTrue(result.semantic_state.evidence_ids)
        self.assertEqual(result.uncertainty.scenario_count, 1)

    def test_unknown_time_runs_twelve_scenarios(self):
        result = calculate_myeongri_core(
            BirthInput(
                name="테스트",
                gender="female",
                birth_date=date(1990, 5, 15),
                time_unknown=True,
            ),
            target_date=date(2026, 9, 7),
        )
        self.assertIsNone(result.natal_facts.pillars["hour"])
        self.assertEqual(result.uncertainty.scenario_count, 12)
        self.assertTrue(result.uncertainty.stable_conclusions)
        self.assertTrue(result.uncertainty.conditional_conclusions)
        self.assertTrue(result.warnings)
        timing_evidence = next(
            item for item in result.evidence if item.id == "evidence:timing:ordered-overlays"
        )
        self.assertEqual(
            timing_evidence.source_values["birth_time_assumption"],
            "noon_proxy_for_daeyun_start",
        )

    def test_service_query_accepts_full_core_result(self):
        result = calculate_myeongri_core(
            BirthInput(
                name="테스트",
                gender="male",
                birth_date=date(1990, 5, 15),
                birth_time=time(9, 30),
            ),
            target_date=date(2026, 9, 7),
        )
        annual = build_service_query(result, "annual_wealth")
        lifetime = build_service_query(result, "lifetime_wealth")
        self.assertEqual(set(annual["timing"]), {"luck_cycle", "annual"})
        self.assertEqual(set(lifetime["timing"]), {"luck_cycles"})

    def test_missing_time_requires_explicit_unknown_flag(self):
        with self.assertRaises(ValueError):
            calculate_myeongri_core(BirthInput(
                name="테스트",
                gender="male",
                birth_date=date(1990, 5, 15),
            ))
