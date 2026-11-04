"""지장간 화면 순서: 여기 → 중기 → 정기 (2026-11-04, 국내 만세력 방식)."""

import unittest
from datetime import date, time

from app.engine.core.models import BirthInput
from app.engine.facts.hidden_stems import get_hidden_stems
from app.engine.facts.hidden_stems_display import DISPLAY_HIDDEN_STEMS, display_hidden_stems
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services.lifetime_v3 import _chart_html, _hidden_counts
from app.engine.services.now_me import natal_profile


class HiddenStemDisplayTests(unittest.TestCase):
    def test_main_stem_matches_engine_and_comes_last(self):
        for branch in DISPLAY_HIDDEN_STEMS:
            rows = display_hidden_stems(branch)
            self.assertEqual(len(rows), 3)
            self.assertTrue(rows[-1]["main"])
            engine_main = get_hidden_stems(branch).stems[0].stem
            self.assertEqual(rows[-1]["stem"], engine_main, branch)

    def test_middle_gap_only_for_ja_myo_yu(self):
        gaps = {b for b in DISPLAY_HIDDEN_STEMS if display_hidden_stems(b)[1]["stem"] is None}
        self.assertEqual(gaps, {"子", "卯", "酉"})

    def test_korean_order_examples(self):
        stems = lambda b: [h["stem"] for h in display_hidden_stems(b)]
        self.assertEqual(stems("午"), ["丙", "己", "丁"])
        self.assertEqual(stems("卯"), ["甲", None, "乙"])
        self.assertEqual(stems("戌"), ["辛", "丁", "戊"])
        self.assertEqual(stems("巳"), ["戊", "庚", "丙"])

    def test_lifetime_chart_renders_display_order(self):
        core = calculate_myeongri_core(BirthInput(
            name="테스트", gender="male", birth_date=date(1978, 3, 13), birth_time=time(11, 0)))
        html = _chart_html(core, natal_profile(core), _hidden_counts(core))
        self.assertIn("pc-hidden-gap", html)           # 卯 중기 자리
        self.assertRegex(html, r"丙</span>[^|]*?己</span>[^|]*?is-main[^|]*?丁</span>")
        self.assertEqual(html.count("is-main"), 4)

    def test_api_pillar_detail_uses_display_order(self):
        import main
        core = calculate_myeongri_core(BirthInput(
            name="테스트", gender="male", birth_date=date(1978, 3, 13), birth_time=time(11, 0)))
        year = main._pillar_detail(core, "year")["jijanggan"]
        self.assertEqual([j["char"] for j in year], ["병", "기", "정"])
        self.assertEqual([j["main"] for j in year], [False, False, True])
        month = main._pillar_detail(core, "month")["jijanggan"]
        self.assertTrue(month[1].get("gap"))

if __name__ == "__main__":
    unittest.main()
