"""평생운세 v3(B안) — 구성 순서, 잠금, 근거 접힘, 여러 원국에서의 조립 안정성."""
import random
import re
import unittest
from datetime import date, time

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services import build_lifetime_overall_report
from app.engine.services import lifetime_copy
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
        subs = result["html"].count('class="lifetime-sub" data-now-me-row=')
        self.assertGreaterEqual(subs, 3)
        self.assertEqual(result["html"].count('<details class="lifetime-why">'), subs + 1)  # +1 원국 지도

    def test_past_cycles_each_get_a_line_and_next_cycle_body_stays_locked(self):
        result, past, now, future = _v3(_core(date(1978, 3, 13), time(11, 0)))
        self.assertEqual(result["html"].count("<li><strong>"), len(past))
        self.assertIn('data-locked="true"', result["html"])
        next_core = lifetime_copy.CYCLE_COPY[future[0]["ten_god"]][1]
        current_core = lifetime_copy.CYCLE_COPY[now["ten_god"]][1]
        if next_core != current_core:
            self.assertNotIn(next_core, result["html"])

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


if __name__ == "__main__":
    unittest.main()
