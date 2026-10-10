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


GODS = list(v2.GODS)
# 2026년 甲 일간 기준 월간 십성(1~12월): 같은 십성이 두 번 오는 달이 있다.
SAMPLE_YEAR = ["direct_wealth", "seven_killings", "direct_officer", "indirect_resource", "direct_resource",
               "peer", "rob_wealth", "eating_god", "hurting_officer", "indirect_wealth",
               "direct_wealth", "seven_killings"]


def month(ledger, m, god, year_god="eating_god", area=None, flow="base", period=None):
    return v2.compose_month(ledger, m, month_god=god, year_god=year_god,
                            focus_area=area or v2.GOD_AREA[god], flow=flow, period=period)


class MonthTests(TestCase):
    def test_every_combination_passes_the_writing_rules(self):
        for year_god in GODS:
            for god in GODS:
                for area in v2.AREA_KEYS:
                    for flow in MODES:
                        r = month(CopyLedger(7), 10, god, year_god, area, flow)
                        self.assertEqual(v2.validate_month(r), [], (year_god, god, area, flow))
                        self.assertEqual(r["verdict"], v2.VERDICTS[flow])

    def test_month_has_all_blocks_and_focus_is_excluded_from_lines(self):
        r = month(CopyLedger(1), 10, "indirect_wealth", area="workmoney", flow="join")
        self.assertEqual(len(split_sentences(r["flow_text"])), 3)
        self.assertEqual(len(split_sentences(r["link"])), 2)
        self.assertEqual(r["focus"]["area"], "workmoney")
        self.assertEqual([l["area"] for l in r["lines"]], ["mind", "people", "body", "learn"])
        self.assertEqual([l["label"] for l in r["lines"]], ["마음", "관계", "건강", "배움"])
        self.assertTrue(r["do"] and r["avoid"])
        self.assertGreaterEqual(len(r["sentences"]), 10)

    def test_family_relations_cover_the_five_cycle(self):
        self.assertEqual(v2.family_relation("eating_god", "indirect_wealth"), "feeds")   # 식상생재
        self.assertEqual(v2.family_relation("eating_god", "direct_resource"), "controlled")  # 인성극식상
        self.assertEqual(v2.family_relation("eating_god", "seven_killings"), "controls")  # 식상극관
        self.assertEqual(v2.family_relation("eating_god", "peer"), "fed")  # 비겁생식상
        self.assertEqual(v2.family_relation("eating_god", "hurting_officer"), "same")
        rel = {v2.family_relation(y, m) for y in GODS for m in GODS}
        self.assertEqual(rel, set(v2.LINK))

    def test_link_templates_fill_cleanly_for_all_pairs(self):
        for y in GODS:
            for g in GODS:
                for template in v2.LINK[v2.family_relation(y, g)]:
                    text = template.format(m=10, Y=v2.YEAR_PHRASE[y], M=v2.MONTH_PHRASE[g])
                    self.assertNotIn("{", text)
                    self.assertEqual(len(split_sentences(text)), 2)

    def test_a_real_shaped_year_never_repeats_a_sentence(self):
        for seed in ("1984-03-02", "1990-01-01", "2001-12-31"):
            for flow in MODES:
                ledger = CopyLedger(seed_from(seed, 2026))
                sentences = []
                for m, god in enumerate(SAMPLE_YEAR, start=1):
                    sentences += month(ledger, m, god, flow=flow)["sentences"]
                dups = {s for s in sentences if sentences.count(s) > 1}
                self.assertEqual(dups, set(), (seed, flow))

    def test_worst_case_same_focus_every_month_still_no_repeats(self):
        for area in v2.AREA_KEYS:
            ledger = CopyLedger(3)
            sentences = []
            for m, god in enumerate(SAMPLE_YEAR, start=1):
                sentences += month(ledger, m, god, area=area, flow="join")["sentences"]
            focus_pool = set(v2.FOCUS[area])
            used_focus = [s for s in sentences if any(s in f for f in focus_pool)]
            self.assertGreaterEqual(len(v2.FOCUS[area]), 12, area)
            self.assertEqual(len(used_focus), len(set(used_focus)), area)

    def test_period_line(self):
        period = dict(name="한로", start=date(2026, 10, 8), end=date(2026, 11, 6))
        r = month(CopyLedger(1), 10, "indirect_wealth", period=period)
        self.assertEqual(r["period"], "10월 8일(한로)부터 11월 6일까지의 흐름입니다.")
        self.assertIsNone(month(CopyLedger(1), 10, "indirect_wealth")["period"])

    def test_unknown_month_god_still_gives_a_month(self):
        r = v2.compose_month(CopyLedger(1), 3, month_god=None, year_god="peer", focus_area="body")
        self.assertIsNone(r["link"])
        self.assertEqual(r["lines"], [])
        self.assertTrue(r["flow_text"] and r["do"])

    def test_every_month_pool_sentence_passes_rules(self):
        pools = [*v2.MONTH_FLOW.values(), v2.GENERAL_FLOW, *v2.FOCUS.values(), *v2.MODE_LINES.values(),
                 *[lines for fam in v2.AREA_LINES.values() for lines in fam.values()],
                 [x for pairs in [*v2.DO_AVOID.values(), v2.GENERAL_DO_AVOID] for pair in pairs for x in pair]]
        for pool in pools:
            for text in pool:
                for sentence in split_sentences(text):
                    self.assertLessEqual(len(sentence), v2.SENTENCE_MAX_MONTH, sentence)
                    self.assertFalse(any(h in sentence for h in v2.HEDGES), sentence)
        for fam in v2.AREA_LINES.values():
            self.assertEqual(set(fam), set(v2.AREA_KEYS))

    def test_month_text_is_attitude_not_event(self):
        pattern = re.compile(r"(생깁니다|일어납니다|찾아옵니다|사고가|사고를|질병|수술|반드시)")
        pools = [*v2.MONTH_FLOW.values(), v2.GENERAL_FLOW, *v2.FOCUS.values(), *v2.MODE_LINES.values(),
                 *[lines for fam in v2.AREA_LINES.values() for lines in fam.values()]]
        for pool in pools:
            for text in pool:
                self.assertIsNone(pattern.search(text), text)
                self.assertEqual(find_banned(text), [], text)


def fake_core(birth=date(1984, 3, 2)):
    return SimpleNamespace(
        input=SimpleNamespace(birth_date=birth, calendar_type="solar", is_leap_month=False),
        natal_facts=SimpleNamespace(pillars={}))


def run_builder(core, year=2026, god="eating_god", domains=("enjoyment",), mode="base", name="정오"):
    """계산 함수를 가짜로 바꿔 조립만 확인한다. 월별 십성은 실제 한 해처럼 달마다 바뀐다."""
    timing = SimpleNamespace(annual={"pillar": {"ganji": "丙午"}})
    year_sel = selection(god, domains, mode)
    months = iter(SAMPLE_YEAR * 2)

    def fake_select(core, scope, timing=None):
        if scope == "annual":
            return year_sel
        if scope == "monthly":
            return selection(next(months))
        return selection(None)

    with patch.object(annual, "to_solar", side_effect=lambda d, *_: d), \
         patch.object(annual, "calculate_timing", return_value=(timing, None, None)), \
         patch.object(annual, "select_overall_domains", side_effect=fake_select):
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

    def test_no_sentence_repeats_across_twelve_months(self):
        sentences = [s for m in self.report["evidence_summary"]["months"] for s in m["reading"]["sentences"]]
        self.assertEqual(len(sentences), len(set(sentences)))
        for m in self.report["evidence_summary"]["months"]:
            self.assertEqual(v2.validate_month(m["reading"]), [])

    def test_version_fields_and_basis_note(self):
        r = self.report
        self.assertEqual(r["narrative_version"], "annual-v2")
        self.assertEqual(r["month_schema"], "dalha.month.v3")
        self.assertIn('data-narrative-version="annual-v2"', r["content"])
        self.assertIn("2026-07-01을 대표일로 삼은 연간 해석", r["content"])
        self.assertIn("丙午", r["content"])
        self.assertIn("대운이 바뀌는 경우 전후 흐름을 각각 계산한 결과는 아닙니다", r["content"])
        self.assertEqual(v2.validate_year(r["reading"]), [])

    def test_month_card_shows_every_block(self):
        period = dict(name="한로", start=date(2026, 10, 8), end=date(2026, 11, 6))
        with patch.object(annual, "_term_period", return_value=period):
            r = run_builder(fake_core())
        card = r["content"][r["content"].index('data-report-month="10"'):]
        card = card[:card.index("</article>")]
        for token in ("(한로)부터", "annual-month-flow", "올해와 이어지는 점", "이달의 초점 · ",
                      "분야별 한 줄", "<strong>할 일</strong>", "<strong>피할 일</strong>"):
            self.assertIn(token, card)

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
