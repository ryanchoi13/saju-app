from unittest import TestCase

from app.engine.constants import GAN_WUXING, ZHI_WUXING
from app.engine.core.models import PillarFact, TimingResult
from app.engine.shensha.engine import calculate_shensha


YANG_STEMS = set("甲丙戊庚壬")
YANG_BRANCHES = set("子寅辰午申戌")


def _pillar(stem, branch):
    return PillarFact(
        stem=stem,
        branch=branch,
        ganji=stem + branch,
        stem_element=GAN_WUXING[stem],
        stem_yin_yang="yang" if stem in YANG_STEMS else "yin",
        branch_element=ZHI_WUXING[branch],
        branch_yin_yang="yang" if branch in YANG_BRANCHES else "yin",
    )


def _axis(stem, branch):
    return {"pillar": _pillar(stem, branch).model_dump(mode="json")}


class ShenshaEngineTests(TestCase):
    def test_core_signals_can_be_detected(self):
        # 甲子: 역마=寅, 도화=酉, 화개=辰, 문창=巳, 천을=丑/未
        natal = {
            "year": _pillar("甲", "子"),
            "month": _pillar("乙", "酉"),
            "day": _pillar("甲", "辰"),
            "hour": _pillar("丁", "巳"),
        }
        timing = TimingResult(
            annual=_axis("丙", "寅"),
            monthly=_axis("丁", "丑"),
        )
        results, _ = calculate_shensha(natal, timing)
        self.assertEqual(
            {item.name for item in results},
            {"travel_horse", "peach_blossom", "flower_canopy", "solitary_star", "literary_star", "heavenly_noble"},
        )

    def test_solitary_and_widow_stars_use_year_seasonal_group(self):
        # 亥子丑 group: 고신=寅, 과숙=戌
        natal = {
            "year": _pillar("甲", "子"),
            "month": _pillar("丙", "寅"),
            "day": _pillar("戊", "戌"),
        }
        results, evidence = calculate_shensha(natal)
        names = {item.name for item in results}
        self.assertIn("solitary_star", names)
        self.assertIn("widow_star", names)
        solitary_evidence = next(item for item in evidence if item.supports == ["shensha:solitary_star"])
        self.assertEqual(solitary_evidence.source_values["basis_type"], "natal_year_branch_seasonal_group")

    def test_timing_only_signal_is_active(self):
        natal = {
            "year": _pillar("甲", "子"),
            "month": _pillar("乙", "卯"),
            "day": _pillar("甲", "辰"),
        }
        timing = TimingResult(annual=_axis("丙", "酉"))
        results, _ = calculate_shensha(natal, timing)
        peach = next(item for item in results if item.name == "peach_blossom")
        self.assertEqual(peach.source, "timing")
        self.assertEqual(peach.activation, "active")

    def test_natal_and_timing_match_is_strongly_active(self):
        natal = {
            "year": _pillar("甲", "子"),
            "month": _pillar("乙", "酉"),
            "day": _pillar("甲", "午"),
        }
        timing = TimingResult(annual=_axis("丙", "酉"))
        results, _ = calculate_shensha(natal, timing)
        peach = next(item for item in results if item.name == "peach_blossom")
        self.assertEqual(peach.activation, "strongly_active")

    def test_shensha_is_explicitly_supporting_only(self):
        natal = {
            "year": _pillar("甲", "子"),
            "month": _pillar("乙", "酉"),
            "day": _pillar("甲", "午"),
        }
        results, evidence = calculate_shensha(natal)
        self.assertTrue(results)
        self.assertTrue(all("supporting_signal_only" in item.core_cross_checks for item in results))
        self.assertTrue(all(not item.source_values["standalone_judgment_allowed"] for item in evidence))

    def test_missing_day_pillar_returns_no_signal(self):
        results, evidence = calculate_shensha({"year": _pillar("甲", "子")})
        self.assertEqual(results, [])
        self.assertEqual(evidence, [])
