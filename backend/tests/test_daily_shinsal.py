"""오늘의 운세 12신살 결(daily_shinsal) — 문장 은행 규칙과 조립 동작.

글의 좋고 나쁨은 사람이 읽고 정한다. 여기서는 기계로 지킬 수 있는 것만 본다:
문체 규칙(daily_story_bank 와 같은 검사), 줄기 원칙(제목·총운·근거·처방이 한 신살에서), 카드와 총운이 다른 벌,
시작일 이전 날짜 불변, 분야 결과 어긋나는 날·튀는 분야가 있는 날 제외, 무작위 원국 무예외.
"""
import collections
import random
import re
import unittest
from datetime import date, time, timedelta

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services import daily_rx, daily_shinsal as SH, daily_story as S, daily_story_bank as B
from app.engine.services.annual_copy import find_banned, split_sentences
from app.engine.services.daily import build_daily_fortune
from app.engine.services.health_copy import find_medical
from app.engine.services.now_me_copy import validate_paragraph
from app.engine.shensha import TWELVE_SHENSHA

ROWS = list(SH.all_strings())
DAY = re.compile(B.DAY_END_RE)
BAN = re.compile(B.BANNED_RE)
FORBID = ("질병", "사망", "사고", "이혼")
RX_FORBIDDEN = re.compile(r"친다|꼰다|자리를|정면")
SENTENCE_MAX, RX_SENTENCE_MAX = 46, 52


def _core(birth: date, clock: time, gender="male"):
    return calculate_myeongri_core(
        BirthInput(name="테스트", gender=gender, birth_date=birth, birth_time=clock, time_unknown=False),
        target_date=SH.EPOCH,
    )


def _jungoh():
    return _core(date(1978, 3, 13), time(11, 0))   # test_daily_story 와 같은 테스트 원국(일지 戌 · 연지 午)


def _fresh():
    daily_rx._RENDER_CACHE.clear()
    daily_rx._HISTORY_CACHE.clear()


class BankTests(unittest.TestCase):
    def test_shape(self):
        self.assertEqual(set(SH.TITLE), {SH.PREFIX + n for n in TWELVE_SHENSHA})
        self.assertFalse(set(SH.TITLE) & set(B.TITLE), "은행 키와 겹치면 안 된다")
        for key in SH.TITLE:
            self.assertEqual([t["grade_ok"] for t in SH.TITLE[key]], [SH.GOOD, SH.GOOD, SH.MID, SH.MID, SH.BAD, SH.BAD])
            self.assertEqual([t["grade_ok"] for t in SH.TITLE[key]], [v["grade_ok"] for v in SH.LEAD[key]])
        for name in TWELVE_SHENSHA:
            self.assertEqual({t: len(v) for t, v in SH.EVIDENCE[name].items()}, {"길": 2, "평": 2, "흉": 2})
            self.assertEqual(set(SH.RX[name]), {"길", "흉"})
            for tone in ("길", "흉"):
                self.assertEqual({k: len(v) for k, v in SH.RX[name][tone].items()}, {"dont": 2, "do": 2})
        self.assertTrue(set(SH.DOMAIN_OF.values()) <= {"금전", "애정·관계", "일", "건강"})

    def test_no_duplicates_even_against_the_existing_banks(self):
        old = {s for _, _, s in B.all_strings()} | {t for _, t in daily_rx.all_sentences()}
        counts = collections.Counter(s for _, _, s in ROWS)
        self.assertEqual([s for s, c in counts.items() if c > 1 or s in old], [])

    def test_every_string_passes_the_style_rules(self):
        for name, path, s in ROWS:
            self.assertEqual(find_banned(s), [], (name, path, s))
            self.assertEqual(find_medical(s), [], (name, path, s))
            self.assertEqual([i for i in validate_paragraph(s) if "깁니다" not in str(i)], [], (name, path, s))
            self.assertFalse(any(w in s for w in FORBID), (name, path, s))
            self.assertIsNone(BAN.search(s), (name, path, s))
            self.assertIsNone(RX_FORBIDDEN.search(s), (name, path, s))
            self.assertNotIn("기운", s)
            self.assertNotIn("기 쉽", s, "정오님 11/10: '~하기 쉽습니다' 0개")
            self.assertNotIn("면 됩니다", s)
            self.assertIsNone(S.GYEOL.search(s), (name, path, s))
            limit = RX_SENTENCE_MAX if name == "RX" else SENTENCE_MAX
            for x in S.sents(s):
                self.assertLessEqual(len(x), limit, (name, path, x))

    def test_titles_and_scenes(self):
        for key, titles in SH.TITLE.items():
            for i, t in enumerate(titles):
                s, lead = t["text"], SH.LEAD[key][i]
                self.assertTrue(8 <= len(s) <= 20, s)
                self.assertTrue(s.endswith(("날", "하루")), s)
                self.assertIsNone(re.search(r"기운|편|쪽|흐름|흐르|살$", s), s)
                ss = S.sents(lead["scene"])
                self.assertEqual(len(ss), 2, lead["scene"])
                self.assertTrue(ss[0].startswith(s), "scene 첫 문장은 제목을 받는다: " + lead["scene"])
                self.assertTrue(DAY.search(ss[0]) and not DAY.search(ss[1]), lead["scene"])
                self.assertNotEqual(S.ending(ss[0]), S.ending(ss[1]), lead["scene"])
                self.assertEqual(len(S.sents(lead["advice"])), 1, lead["advice"])
                self.assertIsNone(DAY.search(lead["advice"]))
                if set(t["grade_ok"]) & set(B.GOOD):
                    text = s + lead["scene"] + lead["advice"]
                    self.assertFalse(any(w in text for w in B.LUKEWARM + B.LUKEWARM_MID_ONLY), text)

    def test_card_and_rx_sentence_counts(self):
        for name, path, s in ROWS:
            if name == "EVIDENCE":
                self.assertEqual(len(split_sentences(s)), 2, (path, s))
            elif name in ("RX", "REASON"):
                self.assertEqual(len(split_sentences(s)), 1, (path, s))
            if name != "TITLE" and not (name == "LEAD" and path[2] == "scene"):
                self.assertEqual([x for x in S.sents(s) if DAY.search(x)], [], (name, path, s))
        for name in TWELVE_SHENSHA:
            for tone in ("길", "흉"):
                for t in SH.RX[name][tone]["dont"]:
                    self.assertRegex(t, r"날(이니|이라),", t)       # 이유를 먼저 말하고 처방(11/12)

    def test_names_never_appear_in_the_body(self):
        names = set(TWELVE_SHENSHA) | set(SH.DISPLAY.values())
        for name, path, s in ROWS:
            if name == "GLOSS":
                continue
            self.assertFalse(any(n in s for n in names), (name, path, s))


class RuleTests(unittest.TestCase):
    def test_name_follows_the_day_branch_triad(self):
        core = _jungoh()                                      # 일지 戌(寅午戌): 申 = 역마, 卯 = 년살, 辰 = 월살
        self.assertEqual(SH.name_of(core, date(2026, 11, 18)), "역마")   # 丙申
        self.assertEqual(SH.name_of(core, date(2026, 11, 13)), "년살")   # 辛卯
        self.assertEqual(SH.name_of(core, date(2026, 11, 14)), "월살")   # 壬辰
        self.assertEqual(SH.note(core, date(2026, 11, 13))["line"], "도화(桃花) · 시선이 모이는 날")
        self.assertEqual(SH.note(core, date(2026, 11, 14))["line"], "월살(月殺) · 아껴 쓰는 날")

    def test_spine_only_on_generic_days_after_the_epoch(self):
        core = _jungoh()
        good, mid, bad = {"grade": "좋음"}, {"grade": "보통"}, {"grade": "주의"}
        d = date(2026, 11, 18)
        self.assertEqual(SH.spine(core, mid, d, "억부 희신", {})["key"], "신살 역마")
        self.assertEqual(SH.spine(core, good, d, "결핍 채움", {})["tone"], "길")
        self.assertEqual(SH.spine(core, bad, d, "억부 기신", {})["tone"], "흉")
        self.assertIsNone(SH.spine(core, mid, d, "day지 충", {}))
        self.assertIsNone(SH.spine(core, mid, d, "삼합", {}))
        self.assertIsNone(SH.spine(core, mid, SH.EPOCH - timedelta(days=1), "억부 희신", {}))
        self.assertIsNone(SH.spine(core, {"grade": "좋음", "standout": ("금전", "좋음")}, d, "억부 희신", {}))

    def test_blocked_when_the_domain_tier_goes_the_other_way(self):
        core = _jungoh()
        d = date(2026, 11, 25)                                # 癸卯 = 년살(도화) → 애정·관계
        self.assertIsNone(SH.spine(core, {"grade": "좋음"}, d, "억부 희신", {"애정·관계": "주의"}))
        self.assertIsNone(SH.spine(core, {"grade": "주의"}, d, "억부 기신", {"애정·관계": "좋음"}))
        self.assertIsNotNone(SH.spine(core, {"grade": "좋음"}, d, "억부 희신", {"애정·관계": "보통", "일": "주의"}))

    def test_reason_second_only_for_demoted_generic_spines(self):
        d = date(2026, 11, 18)
        self.assertEqual(SH.reason_second(None, d), [])
        self.assertEqual(SH.reason_second(("day지 육합", 15), d), [])
        self.assertEqual(sorted(SH.reason_second(("억부 희신", 10), d)), sorted(SH.REASON["길"]))
        self.assertEqual(sorted(SH.reason_second(("12운성 down", -4), d)), sorted(SH.REASON["흉"]))


class AssemblyTests(unittest.TestCase):
    def test_before_the_epoch_nothing_changes(self):
        _fresh()
        core = _jungoh()
        for i in range(1, 15):
            out = daily_rx.render_day(core, "shinsal-test", SH.EPOCH - timedelta(days=i))
            self.assertIsNone(out["shinsal"])
            self.assertFalse(SH.is_key(out["evidence_key"]))
            self.assertFalse(any(SH.is_key(e) for e, _, _ in out["uses"]))
        fortune = build_daily_fortune(core, "정오", SH.EPOCH - timedelta(days=1), account_key="shinsal-test")
        self.assertIsNone(fortune["shinsal"])

    def test_generic_day_speaks_the_shinsal_in_every_slot(self):
        _fresh()
        core = _jungoh()
        out = daily_rx.render_day(core, "shinsal-test", date(2026, 11, 18))     # 丙申 · 보통 · 줄기 억부 희신 → 역마
        sh, story = out["shinsal"], out["story"]
        self.assertEqual((sh["name"], sh["tone"], sh["replaces"]), ("역마", "평", "억부 희신"))
        self.assertEqual(story["evidence_key"], "신살 역마")
        self.assertIn(story["title"], [t["text"] for t in SH.TITLE["신살 역마"][2:4]])
        self.assertTrue(story["overall"].startswith(story["title"]))
        self.assertIn(out["evidence_text"], SH.EVIDENCE["역마"]["평"])
        self.assertIsNone(out["rx_text"], "보통 날은 처방이 없다")
        # 카드 근거는 제목·총운과 다른 벌
        lead_variant = story["picks"]["general"]["lead"] - SH.lead_index("평", 0)
        self.assertEqual(SH.EVIDENCE["역마"]["평"].index(out["evidence_text"]), 1 - lead_variant)

    def test_caution_day_rx_comes_from_the_same_variant_as_the_title(self):
        _fresh()
        core = _jungoh()
        out = daily_rx.render_day(core, "shinsal-test", date(2026, 11, 16))     # 甲午 · 주의 · 줄기 억부 기신 → 장성
        sh, story = out["shinsal"], out["story"]
        self.assertEqual((sh["name"], sh["tone"]), ("장성", "흉"))
        v = story["picks"]["general"]["lead"] - SH.lead_index("흉", 0)
        self.assertEqual(v, sh["variant"])
        dont = SH.RX["장성"]["흉"]["dont"][v]
        self.assertTrue(out["rx_text"].startswith(dont))
        self.assertIn(out["rx_text"][len(dont) + 1:], SH.RX["장성"]["흉"]["do"])
        self.assertEqual(out["rx_element"], "신살 장성")
        self.assertIsNone(out["rx_scene"])

    def test_relation_spine_day_keeps_the_old_story_but_shows_the_note(self):
        _fresh()
        core = _jungoh()
        d = date(2026, 11, 14)                                                  # 壬辰 · 일지 충
        out = daily_rx.render_day(core, "shinsal-test", d)
        self.assertIsNone(out["shinsal"])
        self.assertIn(out["story"]["title"], [t["text"] for t in B.TITLE["day지 충"]])
        fortune = build_daily_fortune(core, "정오", d, account_key="shinsal-test")
        self.assertEqual(fortune["shinsal"]["line"], "월살(月殺) · 아껴 쓰는 날")
        self.assertNotIn("월살", fortune["story"]["body"])

    def test_random_charts_assemble_without_fallback(self):
        _fresh()
        rng = random.Random(20261113)
        seen = collections.Counter()
        for n in range(40):
            birth = date(rng.randint(1950, 2005), rng.randint(1, 12), rng.randint(1, 28))
            core = _core(birth, time(rng.randint(0, 23), rng.randint(0, 59)), rng.choice(["male", "female"]))
            for i in range(24):
                d = SH.EPOCH + timedelta(days=i)
                out = daily_rx.render_day(core, f"shinsal-{n}", d)
                story, sh = out["story"], out["shinsal"]
                self.assertIsNotNone(story, (birth, d))
                self.assertTrue(out["use_shinsal"], f"신살 없이 다시 고른 날이 있다: {birth} {d}")
                self.assertEqual(out, daily_rx.render_day(core, f"shinsal-{n}", d), "결정론")
                if not sh:
                    self.assertFalse(SH.is_key(story["evidence_key"]))
                    continue
                seen[sh["tone"]] += 1
                tone, name = sh["tone"], sh["name"]
                self.assertEqual(sh["tone"], SH.tone_of(out["evaluation"]["grade"]))
                self.assertIsNone(out["evaluation"]["standout"])
                self.assertEqual(story["evidence_key"], sh["key"])
                self.assertEqual(story["picks"]["general"]["lead"], SH.lead_index(tone, sh["variant"]))
                self.assertEqual(out["evidence_text"], SH.EVIDENCE[name][tone][1 - sh["variant"]])
                self.assertEqual(out["rx_text"] is None, tone == "평")
                body = " ".join([story["title"], story["overall"]] + [s["text"] for s in story["sections"]])
                self.assertFalse(any(x in body for x in TWELVE_SHENSHA), body)
        self.assertGreater(seen["길"], 0)
        self.assertGreater(seen["평"], 0)
        self.assertGreater(seen["흉"], 0)


if __name__ == "__main__":
    unittest.main()
