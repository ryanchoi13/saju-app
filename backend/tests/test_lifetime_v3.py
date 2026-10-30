"""평생운세 v3(B안) — 구성 순서, 잠금, 근거 접힘, 여러 원국에서의 조립 안정성."""
import random
import re
import unittest
from datetime import date, time

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services import build_lifetime_overall_report
from app.engine.services import lifetime_v3_copy as v3copy
from app.engine.services import lifetime_flow as flow
from app.engine.services.lifetime_v3 import build_lifetime_v3
from app.engine.services.lifetime import _split_cycles
from app.engine.semantic import build_service_query

TARGET = date(2026, 10, 30)
ORDER = ["head", "map", "core", "first-seen", "domains", "flow", "closing"]


def _core(birth, clock, gender="male"):
    return calculate_myeongri_core(
        BirthInput(name="테스트", gender=gender, birth_date=birth, birth_time=clock, time_unknown=clock is None),
        target_date=TARGET)


def _v3(core):
    q = build_service_query(core, "lifetime_overall")
    past, now, future = _split_cycles(q["timing"]["luck_cycles"])
    return build_lifetime_v3(core, "테스트", past=past, now=now, future=future, current_selection=None,
                             climate=q["synthesis"]["climate_state"].get("state")), past, now, future


def _plain(html):
    return re.sub(r"<[^>]*>", " ", html)


class LifetimeV3Tests(unittest.TestCase):
    def test_sections_come_in_b_plan_order(self):
        report = build_lifetime_overall_report(_core(date(1978, 3, 13), time(11, 0)), "테스트")
        found = re.findall(r'data-lifetime-section="([a-z-]+)"', report["content"])
        top = [s for s in found if s in ORDER]
        self.assertEqual(top, ORDER)
        self.assertEqual(report["narrative_version"], "lifetime-v3")
        for n, title in enumerate(["원국 지도", "타고난 결", "사람들이 먼저 보는 것", "분야별로 보면", "인생의 흐름", "한마디"], 1):
            self.assertIn(f"<h3>{n}. {title}</h3>", report["content"])

    def test_every_reading_block_has_a_folded_why(self):
        result, *_ = _v3(_core(date(1978, 3, 13), time(11, 0)))
        html = result["html"]
        subs = html.count('class="lifetime-sub" data-now-me-row=')
        past = html.count('data-cycle-state="past"')
        self.assertGreaterEqual(subs, 3)
        # 성격 행 + 원국 지도 + 지나온 대운 하나하나 + 지금
        self.assertEqual(html.count('<details class="lifetime-why">'), subs + 1 + past + 1)

    def test_past_cycles_each_get_a_line_and_next_cycle_body_stays_locked(self):
        result, past, now, future = _v3(_core(date(1978, 3, 13), time(11, 0)))
        html = result["html"]
        self.assertEqual(html.count('data-cycle-state="past"'), len(past))
        self.assertIn('data-locked="true"', html)
        nxt = future[0]["ten_god"]
        if nxt != now["ten_god"]:                     # 다음 대운의 본문(지금용 문장)은 싣지 않는다
            for sentence in v3copy.THEME_NOW[nxt] + (v3copy.TIP_NOW[nxt],):
                self.assertNotIn(sentence, html)

    def test_unknown_birth_time_uses_six_glyphs(self):
        result, *_ = _v3(_core(date(1990, 5, 15), None))
        self.assertIn("모름", result["html"])
        self.assertIn("여섯 글자", _plain(result["html"]))

    def test_assembles_for_many_charts_without_falling_back(self):
        rng = random.Random(20261030)
        for _ in range(60):
            birth = date(rng.randint(1950, 2008), rng.randint(1, 12), rng.randint(1, 28))
            clock = None if rng.random() < 0.2 else time(rng.randint(0, 23), rng.choice((0, 30)))
            with self.subTest(birth=birth, clock=clock):
                result, *_ = _v3(_core(birth, clock, rng.choice(("male", "female"))))
                self.assertIn("한마디", result["html"])
                self.assertNotIn("{", _plain(result["html"]))


class FlowTests(unittest.TestCase):
    def setUp(self):
        self.core = _core(date(1978, 3, 13), time(11, 0))
        self.natal = {k: v.branch for k, v in self.core.natal_facts.pillars.items() if v is not None}
        from app.engine.services.now_me import natal_profile
        self.profile = natal_profile(self.core)
        self.cycles = self.core.timing.luck_cycle["cycles"]

    def test_year_pillar(self):
        self.assertEqual(flow.year_pillar(2026), ("丙", "午"))
        self.assertEqual(flow.year_pillar(1988), ("戊", "辰"))

    def test_current_cycle_fills_missing_metal(self):
        now = next(c for c in self.cycles if c["pillar"]["ganji"] == "庚申")
        info = flow.classify_cycle(now, self.profile, self.natal, "甲")
        self.assertEqual(info["kind"], "fill")
        self.assertEqual(info["fills"], ["金"])
        self.assertEqual(info["stem_rel"], "clash")           # 甲庚 천간충도 함께 잡는다

    def test_shaken_years_are_past_only_and_scored(self):
        first = next(c for c in self.cycles if c["pillar"]["ganji"] == "丙辰")
        years = flow.shaken_years(first, self.natal, "甲", 1978, 2026)
        self.assertIn(1988, [y["year"] for y in years])        # 戊辰: 일지 戌 충
        now = next(c for c in self.cycles if c["pillar"]["ganji"] == "庚申")
        self.assertTrue(all(y["year"] < 2026 for y in flow.shaken_years(now, self.natal, "甲", 1978, 2026)))

    def test_no_wood_metaphor_for_non_wood_day_master(self):
        result, *_ = _v3(_core(date(1976, 2, 5), time(12, 0), "female"))   # 丁 일간, 겁재 2
        block = re.search(r"data-now-me-row=\"B11\".*?</article>", result["html"], re.S)
        if block:
            self.assertNotIn("목(木) 기운", block.group(0))
            self.assertIn("화(火) 기운", block.group(0))

    def test_event_words_stay_out(self):
        rng = random.Random(7)
        for _ in range(40):
            birth = date(rng.randint(1945, 1995), rng.randint(1, 12), rng.randint(1, 28))
            result, *_ = _v3(_core(birth, time(rng.randint(0, 23), 0)))
            text = _plain(result["html"])
            for word in ("사고", "이혼", "사망", "질병"):
                self.assertNotIn(word, text)


if __name__ == "__main__":
    unittest.main()
