"""연간 리포트 v2: 문구 은행, 중심 분야 배치, 월별 한 단어, 화면 조립.

엔진 계산이 필요 없는 부분은 문구 은행을 직접 검사하고, 조립(annual.py)은
계산 함수를 가짜로 바꿔 구조만 확인한다. 실제 엔진으로 만든 리포트는
test_annual_reader.py 가 확인한다.
"""
import re
from datetime import date
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from app.engine.services import annual, annual_v2 as v2
from app.engine.services.annual_copy import CopyLedger, find_banned, seed_from, split_sentences

ENGINE_DOMAINS = ("self", "enjoyment", "love", "relationships", "work", "money",
                  "wellbeing", "change", "learning")
MODES = ("base", "join", "change", "mixed", "recovery")


def selection(god, domains=(), mode="base"):
    picked = [dict(domain=d, mode=mode, source_ids=[f"src:{d}"]) for d in domains]
    return dict(focal_god=god, primary_domains=list(domains), selected=picked, candidates=picked)


class BankTests(TestCase):
    def test_all_ten_gods_have_complete_cells(self):
        self.assertEqual(len(v2.GODS), 10)
        for god, bank in v2.GODS.items():
            self.assertTrue(4 <= len(bank["overview"]) <= 6, god)
            self.assertEqual(set(bank["areas"]), set(v2.AREA_KEYS), god)
            for key in ("best", "caution", "advice"):
                self.assertEqual(len(split_sentences(bank[key])), 2, (god, key))
            for area, (short, deep) in bank["areas"].items():
                self.assertEqual(len(split_sentences(short)), 2, (god, area))
                self.assertEqual(len(split_sentences(deep)), 2, (god, area))

    def test_every_god_domain_and_mode_passes_the_writing_rules(self):
        for god in [*v2.GODS, None]:
            for domain in ENGINE_DOMAINS:
                for mode in MODES:
                    reading = v2.compose_year(selection(god, [domain], mode))
                    self.assertEqual(v2.validate_year(reading), [], (god, domain, mode))

    def test_mode_notes_cover_only_known_areas_and_pass_rules(self):
        for area, notes in v2.MODE_NOTE.items():
            self.assertIn(area, v2.AREA_KEYS)
            for mode, text in notes.items():
                self.assertIn(mode, MODES)
                self.assertEqual(len(split_sentences(text)), 2, (area, mode))
                self.assertEqual(find_banned(text), [])

    def test_no_calendar_words_or_event_predictions_in_year_text(self):
        pattern = re.compile(r"(지금|이번 달|이달|오늘|내년|올해 안에|될 것입니다|생길 것|찾아옵니다)")
        for god in v2.GODS:
            reading = v2.compose_year(selection(god, ["work"], "change"))
            for sentence in v2._year_sentences(reading):
                self.assertIsNone(pattern.search(sentence), sentence)


class CentralAreaTests(TestCase):
    def test_central_area_follows_engine_not_a_fixed_work_money_slot(self):
        for domain in ENGINE_DOMAINS:
            reading = v2.compose_year(selection("eating_god", [domain]))
            self.assertEqual(reading["areas"][0]["area"], v2.ENGINE_TO_AREA[domain])
            self.assertTrue(reading["areas"][0]["central"])
        areas = {v2.compose_year(selection("eating_god", [d]))["areas"][0]["area"] for d in ENGINE_DOMAINS}
        self.assertEqual(areas, set(v2.AREA_KEYS))

    def test_central_block_is_longer_than_the_others(self):
        reading = v2.compose_year(selection("peer", ["love"]))
        central, *others = reading["areas"]
        self.assertGreater(len(central["sentences"]), max(len(o["sentences"]) for o in others))
        self.assertEqual(sorted(a["area"] for a in reading["areas"]), sorted(v2.AREA_KEYS))

    def test_at_most_two_centers_and_ties_keep_engine_order(self):
        reading = v2.compose_year(selection("peer", ["work", "money", "love", "learning"]))
        self.assertEqual([c["area"] for c in reading["centers"]], ["workmoney", "people"])
        self.assertEqual([a["area"] for a in reading["areas"][:2]], ["workmoney", "people"])

    def test_without_engine_domains_fall_back_to_the_ten_god_area_and_say_so(self):
        reading = v2.compose_year(selection("direct_resource"))
        self.assertEqual(reading["centers"], [dict(area="learn", mode="base", basis="ten_god")])

    def test_unknown_god_uses_the_general_bank_without_a_center(self):
        reading = v2.compose_year(selection(None))
        self.assertIsNone(reading["god"])
        self.assertEqual(reading["centers"], [])
        self.assertFalse(any(a["central"] for a in reading["areas"]))

    def test_mode_note_only_on_the_central_block(self):
        reading = v2.compose_year(selection("peer", ["work"], "change"))
        self.assertIn(v2.MODE_NOTE["workmoney"]["change"], reading["areas"][0]["text"])
        self.assertTrue(all("달라지는 대목" not in a["text"] for a in reading["areas"][1:]))

    def test_deterministic(self):
        self.assertEqual(v2.compose_year(selection("peer", ["love"], "join")),
                         v2.compose_year(selection("peer", ["love"], "join")))


class MonthTests(TestCase):
    def test_every_flow_and_theme_gives_one_word_and_two_sentences(self):
        for flow in MODES:
            for theme in v2.THEME_LINES:
                ledger = CopyLedger(seed_from("2000-01-01", 2026))
                month = v2.compose_month(ledger, 3, theme, flow)
                self.assertEqual(month["verdict"], v2.VERDICTS[flow])
                self.assertEqual(len(month["sentences"]), 2)
                self.assertEqual(find_banned(month["text"]), [])
                self.assertLessEqual(len(month["verdict"]), 7)

    def test_twelve_months_do_not_repeat_a_sentence(self):
        for seed in ("1984-03-02", "1992-05-16", "2001-12-31"):
            ledger = CopyLedger(seed_from(seed, 2026))
            themes = list(v2.THEME_LINES)
            sentences = []
            for m in range(1, 13):
                sentences += v2.compose_month(ledger, m, themes[(m - 1) % 4], "base")["sentences"]
            theme_lines = [s for s in sentences if any(s in v2.THEME_LINES[t] for t in themes)]
            self.assertEqual(len(theme_lines), len(set(theme_lines)), seed)
            self.assertEqual(ledger.reused and [k for k, _ in ledger.reused if k.startswith("v2:theme")], [])

    def test_worst_case_distributions_never_reuse_a_sentence(self):
        themes = list(v2.THEME_LINES)
        cases = {
            "all career, all base": [("career", "base")] * 12,
            "all career, all change": [("career", "change")] * 12,
            "two themes alternating": [(themes[m % 2], "mixed") for m in range(12)],
            "rotation, recovery": [(themes[m % 4], "recovery") for m in range(12)],
        }
        for name, plan in cases.items():
            ledger = CopyLedger(seed_from("1984-03-02", 2026))
            sentences = []
            for month, (theme, flow) in enumerate(plan, start=1):
                sentences += v2.compose_month(ledger, month, theme, flow)["sentences"]
            self.assertEqual(len(sentences), len(set(sentences)), name)
            self.assertEqual(ledger.reused, [], name)

    def test_month_text_is_attitude_not_event(self):
        pattern = re.compile(r"(생깁니다|일어납니다|찾아옵니다|사고가|사고를|질병|수술)")
        for bank in (*v2.THEME_LINES.values(), *v2.FLOW_LINES.values()):
            for line in bank:
                self.assertIsNone(pattern.search(line), line)
                self.assertLessEqual(len(line), v2.SENTENCE_MAX)


def fake_core(birth=date(1984, 3, 2)):
    return SimpleNamespace(
        input=SimpleNamespace(birth_date=birth, calendar_type="solar", is_leap_month=False),
        natal_facts=SimpleNamespace(pillars={}))


def run_builder(core, year=2026, god="eating_god", domains=("enjoyment",), mode="base", name="정오"):
    timing = SimpleNamespace(annual={"pillar": {"ganji": "丙午"}})
    sel = selection(god, domains, mode)
    with patch.object(annual, "to_solar", side_effect=lambda d, *_: d), \
         patch.object(annual, "calculate_timing", return_value=(timing, None, None)), \
         patch.object(annual, "select_overall_domains", return_value=sel):
        return annual.build_annual_overall_report(core, name, year)


class BuilderStructureTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = run_builder(fake_core())

    def test_everything_is_open_no_collapsible_elements(self):
        content = self.report["content"]
        for token in ("<details", "<summary", "annual-evidence"):
            self.assertNotIn(token, content)

    def test_sections_in_order(self):
        content = self.report["content"]
        order = [content.index(t) for t in ("올해 총운", "올해의 세 가지", 'data-report-domain=', "12개월 흐름")]
        self.assertEqual(order, sorted(order))
        for area in v2.AREA_KEYS:
            self.assertEqual(content.count(f'data-report-domain="{area}"'), 1)
        for key in ("best", "caution", "advice"):
            self.assertEqual(content.count(f'data-annual-three="{key}"'), 1)

    def test_central_marker_and_heading_match_the_reading(self):
        content = self.report["content"]
        self.assertEqual(content.count('data-central="true"'), 1)
        self.assertIn("올해의 중심 · 마음·표현", content)
        self.assertEqual(self.report["reading"]["areas"][0]["area"], "mind")

    def test_twelve_months_with_a_verdict_each(self):
        content = self.report["content"]
        for m in range(1, 13):
            self.assertEqual(content.count(f'data-report-month="{m}"'), 1)
        verdicts = tuple(v2.VERDICTS.values())
        heads = re.findall(r"<h4>(\d+)월 · ([^<]+)</h4>", content)
        self.assertEqual([int(m) for m, _ in heads], list(range(1, 13)))
        self.assertTrue(all(word in verdicts for _, word in heads))

    def test_version_fields_and_basis_note(self):
        r = self.report
        self.assertEqual(r["narrative_version"], "annual-v2")
        self.assertEqual(r["month_schema"], "dalha.month.v2")
        self.assertIn('data-narrative-version="annual-v2"', r["content"])
        self.assertIn("2026-07-01을 대표일로 삼은 연간 해석", r["content"])
        self.assertIn("丙午", r["content"])
        self.assertIn("대운이 바뀌는 경우 전후 흐름을 각각 계산한 결과는 아닙니다", r["content"])
        self.assertEqual(v2.validate_year(r["reading"]), [])

    def test_name_is_escaped(self):
        r = run_builder(fake_core(), name="<img src=x onerror=alert(1)>")
        self.assertNotIn("<img", r["content"])
        self.assertNotIn("<img", r["title"])
        self.assertIn("&lt;img", r["title"])

    def test_same_input_same_text_and_other_birth_other_month_text(self):
        again = run_builder(fake_core())
        self.assertEqual(again["content"], self.report["content"])
        other = run_builder(fake_core(date(1991, 11, 5)))
        self.assertNotEqual(other["content"], self.report["content"])

    def test_prebirth_months_skipped_and_prebirth_year_rejected(self):
        core = fake_core(date(2026, 9, 23))
        r = run_builder(core)
        self.assertEqual(r["content"].count("출생 전 기간"), 8)
        self.assertEqual(r["evidence_summary"]["months"][0]["representative_date"], "2026-09-23")
        self.assertIn("2026-09-23을 대표일로 삼은 연간 해석", r["content"])
        with self.assertRaises(ValueError):
            run_builder(core, year=2025)

    def test_changing_flow_changes_the_central_block_text(self):
        base = run_builder(fake_core(), domains=("work",), god="peer", mode="base")
        changed = run_builder(fake_core(), domains=("work",), god="peer", mode="change")
        self.assertNotEqual(base["reading"]["areas"][0]["text"], changed["reading"]["areas"][0]["text"])
        self.assertEqual(base["reading"]["areas"][0]["area"], "workmoney")
