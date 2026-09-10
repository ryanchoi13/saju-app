from copy import deepcopy
from datetime import date, time, timedelta
from unittest import TestCase

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.semantic.overall import select_overall_domains, OVERALL_VERSION
from app.engine.services.overall_narrative import render_overall
from app.engine.services.daily import build_daily_fortune
from app.engine.services.annual import build_annual_overall_report
from app.engine.services.lifetime import build_lifetime_overall_report


class OverallInterpretationTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.birth = BirthInput(name="검토", gender="male", birth_date=date(1978, 3, 13), birth_time=time(11))
        cls.core = calculate_myeongri_core(cls.birth, target_date=date(2026, 9, 15))

    def test_complete_core_recovery_can_lead_but_pending_cannot(self):
        core = self.core.model_copy(deep=True)
        before = select_overall_domains(core, "daily")
        self.assertIn("love", before["primary_domains"])
        operation = dict(operation="support", urgency="high", assessment_status="completed",
                         evidence_ids=["evidence:strength:ordered-diagnosis"])
        core.synthesis.favorable_operations.append(operation)
        selected = select_overall_domains(core, "daily")
        self.assertEqual(selected["primary_domains"], ["wellbeing"])
        # Important close-relationship evidence must remain in the body.
        self.assertIn("love", [c["domain"] for c in selected["selected"]])
        operation["assessment_status"] = "conditional"
        operation["unresolved_requirements"] = ["personal_need"]
        after = select_overall_domains(core, "daily")
        self.assertEqual(after["primary_domains"], before["primary_domains"])
        self.assertEqual(after["candidates"], before["candidates"])
        self.assertEqual(render_overall(after), render_overall(before))

    def test_unrelated_operation_conflict_does_not_block_recovery(self):
        core = self.core.model_copy(deep=True)
        core.synthesis.favorable_operations = [dict(operation="support", evidence_ids=["evidence:strength:ordered-diagnosis"])]
        core.synthesis.diagnostic_conflicts = [dict(operations=["warm", "cool"], resolution="preserve_as_unresolved")]
        self.assertEqual(select_overall_domains(core, "daily")["primary_domains"], ["wellbeing"])
        core.synthesis.diagnostic_conflicts[0]["operations"].append("support")
        self.assertNotIn("wellbeing", select_overall_domains(core, "daily")["primary_domains"])

    def test_duplicate_operations_do_not_increase_importance(self):
        core = self.core.model_copy(deep=True)
        op = dict(operation="support", evidence_ids=["evidence:strength:ordered-diagnosis"])
        core.synthesis.favorable_operations = [op]
        before = select_overall_domains(core, "daily")
        core.synthesis.favorable_operations.extend([deepcopy(op) for _ in range(10)])
        self.assertEqual(select_overall_domains(core, "daily"), before)

    def test_annual_and_lifetime_do_not_read_daily_or_monthly_overlays(self):
        core = self.core.model_copy(deep=True)
        annual = select_overall_domains(core, "annual")
        natal = select_overall_domains(core, "natal")
        cycle = select_overall_domains(core, "luck_cycle")
        different = calculate_myeongri_core(self.birth, target_date=date(2027, 2, 20))
        core.timing.daily = deepcopy(different.timing.daily)
        core.timing.monthly = deepcopy(different.timing.monthly)
        core.activated_state = different.activated_state
        self.assertEqual(select_overall_domains(core, "annual"), annual)
        self.assertEqual(select_overall_domains(core, "natal"), natal)
        self.assertEqual(select_overall_domains(core, "luck_cycle"), cycle)

    def test_each_cycle_is_independent_of_current_cycle_and_current_year(self):
        core = self.core.model_copy(deep=True)
        fixed = deepcopy(core.timing.luck_cycle["cycles"][0])
        before = select_overall_domains(core, "luck_cycle", cycle=fixed)
        core.timing.luck_cycle["current"] = core.timing.luck_cycle["cycles"][-1]
        core.timing.annual = {}; core.timing.monthly = {}; core.timing.daily = {}
        self.assertEqual(select_overall_domains(core, "luck_cycle", cycle=fixed), before)

    def test_monthly_scope_never_reads_the_daily_overlay(self):
        core = self.core.model_copy(deep=True)
        before = select_overall_domains(core, "monthly")
        core.timing.daily = {}; core.activated_state.temporal_observations = {}
        self.assertEqual(select_overall_domains(core, "monthly"), before)

    def test_source_provenance_and_no_input_mutation(self):
        before = self.core.model_dump(mode="json")
        for scope in ("natal", "annual", "monthly", "daily", "luck_cycle"):
            selected = select_overall_domains(self.core, scope)
            ids = {e["id"] for e in selected["evidence_records"]}
            self.assertTrue(all(set(c["source_ids"]) <= ids for c in selected["candidates"]))
            self.assertTrue(all(c["event_likelihood"] is None for c in selected["candidates"]))
        self.assertEqual(before, self.core.model_dump(mode="json"))

    def test_daily_uses_shared_topics_and_keeps_secondary_subjects(self):
        d = date(2026, 9, 15)
        selection = select_overall_domains(self.core, "daily")
        rendered = render_overall(selection)
        result = build_daily_fortune(self.core, "검토", d)
        self.assertEqual(result["title"], rendered["title"])
        self.assertEqual(result["unified_advice"], rendered["unified_advice"])
        self.assertEqual(result["evidence_summary"]["overall"], selection)
        self.assertIn(rendered["advice"], result["advice"])
        self.assertNotEqual(result["time_flow"]["afternoon"], rendered["subjects"][0]["time_flow"]["afternoon"])

    def test_thirty_days_do_not_require_every_domain_or_use_randomness(self):
        domains = set()
        titles = set()
        for i in range(30):
            d = date(2026, 9, 10) + timedelta(days=i)
            core = calculate_myeongri_core(self.birth, target_date=d)
            first = select_overall_domains(core, "daily")
            self.assertEqual(first, select_overall_domains(core, "daily"))
            domains.update(first["primary_domains"])
            narrative = render_overall(first); titles.add(narrative["title"])
            for forbidden in ("결혼하게", "이별하게", "당첨됩니다", "병에 걸", "확실한 수익", "반드시"):
                self.assertNotIn(forbidden, narrative["advice"])
        self.assertTrue({"love", "money", "wellbeing", "relationships"} <= domains)
        self.assertGreater(len(titles), 10)

    def test_all_overall_surfaces_share_version_and_record_domains(self):
        annual = build_annual_overall_report(self.core, "<script>검토</script>", 2026)
        lifetime = build_lifetime_overall_report(self.core, "<script>검토</script>")
        for report in (annual, lifetime):
            self.assertEqual(report["engine_version"], OVERALL_VERSION)
            self.assertNotIn("<script>", report["content"])
            self.assertIn(OVERALL_VERSION, report["content"])
        self.assertEqual(len(annual["evidence_summary"]["months"]), 12)
        self.assertEqual(len(lifetime["evidence_summary"]["cycles"]), 9)
        self.assertIn("love", lifetime["evidence_summary"]["natal"]["primary_domains"])
        self.assertIn("학업·배움", {d["label"] for d in annual["evidence_summary"]["annual"]["considered_domains"]})

    def test_annual_report_does_not_change_when_viewed_on_another_day(self):
        other = calculate_myeongri_core(self.birth, target_date=date(2026, 12, 25))
        self.assertEqual(build_annual_overall_report(self.core, "검토", 2026), build_annual_overall_report(other, "검토", 2026))

    def test_unknown_hour_and_newborn_do_not_create_missing_periods(self):
        birth = BirthInput(name="검토", gender="female", birth_date=date(2026, 9, 20), time_unknown=True)
        core = calculate_myeongri_core(birth, target_date=date(2026, 9, 20))
        report = build_annual_overall_report(core, "검토", 2026)
        self.assertEqual(report["content"].count("출생 전 기간"), 8)
        with self.assertRaises(ValueError):
            build_annual_overall_report(core, "검토", 2025)
        selection = select_overall_domains(core, "daily")
        for candidate in selection["candidates"]:
            for support in candidate["supports"]:
                self.assertFalse(any(m["pillar"] == "hour" for m in support["members"]))
