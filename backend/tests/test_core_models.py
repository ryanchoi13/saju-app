from datetime import date
from unittest import TestCase

from pydantic import ValidationError

from app.engine.core.models import (
    BirthInput,
    ConfidenceLevel,
    Evidence,
    EvidenceLayer,
    MyeongriCoreResult,
    UncertaintyResult,
)


class CoreModelTests(TestCase):
    def _input(self) -> BirthInput:
        return BirthInput(
            name="테스트",
            gender="male",
            birth_date=date(1990, 5, 15),
            calendar_type="solar",
            time_unknown=True,
        )

    def test_minimal_result_uses_v1_contract(self):
        result = MyeongriCoreResult(input=self._input())

        payload = result.model_dump(mode="json")

        self.assertEqual(payload["schema_version"], "myeongri-core-v1")
        self.assertEqual(payload["input"]["birth_date"], "1990-05-15")
        self.assertEqual(payload["uncertainty"]["scenario_count"], 0)
        self.assertEqual(payload["relationships"], [])

    def test_mutable_defaults_are_not_shared(self):
        first = MyeongriCoreResult(input=self._input())
        second = MyeongriCoreResult(input=self._input())

        first.warnings.append("first only")

        self.assertEqual(second.warnings, [])

    def test_evidence_keeps_layer_and_confidence_separate(self):
        evidence = Evidence(
            id="ev-001",
            layer=EvidenceLayer.FACT,
            source_module="pillars",
            description="일주 계산 결과",
            reliability=ConfidenceLevel.HIGH,
        )

        self.assertEqual(evidence.layer, EvidenceLayer.FACT)
        self.assertEqual(evidence.reliability, ConfidenceLevel.HIGH)

    def test_unknown_time_supports_twelve_scenarios(self):
        uncertainty = UncertaintyResult(time_unknown=True, scenario_count=12)

        self.assertEqual(uncertainty.scenario_count, 12)

    def test_scenario_count_cannot_exceed_twelve(self):
        with self.assertRaises(ValidationError):
            UncertaintyResult(time_unknown=True, scenario_count=13)

    def test_unknown_fields_are_rejected(self):
        with self.assertRaises(ValidationError):
            BirthInput(
                name="테스트",
                gender="male",
                birth_date=date(1990, 5, 15),
                unexpected=True,
            )
