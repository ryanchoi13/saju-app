"""오늘의 부적 명세(서버)와 화면 부품(assets/talisman.js)이 어긋나지 않는지, 고르는 규칙이 지켜지는지 확인한다."""
import re
from datetime import date, time, timedelta
from pathlib import Path
from unittest import TestCase

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services import daily_talisman as dt
from app.engine.services.daily import build_daily_fortune

JS = Path(__file__).resolve().parents[2] / "assets" / "talisman.js"


def _js_part_names() -> set[str]:
    src = JS.read_text(encoding="utf-8")
    body = src[src.index("var PARTS = {"):src.index("var OVERLAY")]
    return set(re.findall(r"^\s{8}(\w+):", body, flags=re.M))


class DailyTalismanTests(TestCase):
    def _core(self, d, birth=date(1978, 3, 13)):
        return calculate_myeongri_core(
            BirthInput(name="테스트", gender="male", birth_date=birth, birth_time=time(10, 30)), target_date=d)

    def test_all_part_keys_exist_in_client(self):
        names = _js_part_names()
        self.assertGreaterEqual(len(names), 20)
        used = {k for v in dt.DOMAIN_PARTS.values() for k in v} | {k for v in dt.SHINSAL_PARTS.values() for k in v}
        self.assertEqual(used - names, set())

    def test_twelve_shinsal_and_six_domain_forms(self):
        self.assertEqual(len(dt.SHINSAL_PARTS), 12)
        self.assertEqual(len(dt.DOMAIN_PARTS), 6)   # 금전·사람·일 × 좋음·주의 (건강 제외)

    def test_domain_note_wins_and_sets_direction(self):
        a = dict(shinsal_name="장성", grade="보통", luck_element="金", account_key="a", d=date(2026, 11, 17))
        s = dt.pick(domain_note={"domain": "금전", "kind": "좋음"}, **a)
        self.assertEqual((s["kind"], s["domain"], s["dir"], s["layout"]), ("domain", "money", "good", "dense"))
        self.assertEqual(s["keys"], list(dt.DOMAIN_PARTS[("money", "good")]))
        s = dt.pick(domain_note={"domain": "사람", "kind": "주의"}, **a)
        self.assertEqual((s["domain"], s["dir"]), ("people", "caution"))
        self.assertEqual(s["element"], "metal")

    def test_health_standout_falls_back_to_shinsal(self):
        s = dt.pick(domain_note={"domain": "건강", "kind": "주의"}, shinsal_name="역마", grade="주의",
                    luck_element="水", account_key="a", d=date(2026, 11, 17))
        self.assertEqual((s["kind"], s["shinsal"], s["dir"]), ("shinsal", "역마", "caution"))

    def test_grade_tone_and_layout(self):
        base = dict(domain_note=None, shinsal_name="화개", luck_element="土", account_key="a", d=date(2026, 11, 17))
        for grade, tone, layout in [("아주 좋음", "good", "dense"), ("좋음", "good", "dense"), ("보통", "neutral", "simple"),
                                    ("주의", "caution", "dense"), ("나쁨", "caution", "dense")]:
            s = dt.pick(grade=grade, **base)
            self.assertEqual((s["dir"], s["layout"]), (tone, layout), grade)

    def test_unknown_shinsal_does_not_crash(self):
        s = dt.pick(domain_note=None, shinsal_name=None, grade="보통", luck_element="木", account_key="a", d=date(2026, 11, 17))
        self.assertEqual(s["shinsal"], "지살")

    def test_seed_is_stable_and_varies(self):
        d = date(2026, 11, 17)
        self.assertEqual(dt.seed_of("acc", d), dt.seed_of("acc", d))
        self.assertNotEqual(dt.seed_of("acc", d), dt.seed_of("acc", d + timedelta(days=1)))
        self.assertNotEqual(dt.seed_of("acc", d), dt.seed_of("other", d))

    def test_integration_with_daily_fortune(self):
        seen_kinds = set()
        for birth in (date(1978, 3, 13), date(1990, 7, 21), date(2001, 12, 2)):
            for i in range(60):
                d = date(2026, 11, 1) + timedelta(days=i)
                core = self._core(d, birth)
                r = build_daily_fortune(core, "테스트", d, account_key="acc", include_menu=False)
                spec = r["talisman"]["spec"]
                again = build_daily_fortune(core, "테스트", d, account_key="acc", include_menu=False)["talisman"]["spec"]
                self.assertEqual(spec, again)                       # 같은 날·같은 계정 = 같은 명세
                self.assertIn(spec["dir"], ("good", "neutral", "caution"))
                self.assertEqual(len(spec["keys"]), 3)
                self.assertTrue(set(spec["keys"]) <= _js_part_names())
                note = r.get("domain_note")
                if note and note["domain"] != "건강":
                    self.assertEqual(spec["kind"], "domain")
                    self.assertEqual(spec["dir"], "good" if note["kind"] == "좋음" else "caution")
                else:
                    self.assertEqual(spec["kind"], "shinsal")
                    self.assertEqual(spec["dir"], dt.tone_of(r["grade"]))
                seen_kinds.add(spec["kind"])
        self.assertEqual(seen_kinds, {"domain", "shinsal"})
