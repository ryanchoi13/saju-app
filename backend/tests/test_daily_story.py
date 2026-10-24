"""오늘의 이야기 v2 — 문구 은행(daily_story_bank)과 조립기(daily_story) 점검.

글의 좋고 나쁨은 사람이 읽고 정한다(정오님 검토본 GOLD). 여기서는 사람이 놓치기 쉬운 것만 기계로 지킨다:
금칙어·의학 표현·강조어 0, '기운' 1(샘플), "~날" 말끝 예산, 세트 겹침, 7일 조립본 스냅샷, 등급별 상이성, 결정론,
무작위 원국 200명 × 7일 무예외 + 조립 검사 전부 통과.
"""
import collections
import random
import re
import unittest
from datetime import date, time, timedelta

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services import daily_rx, daily_score, daily_sections, daily_story as S, daily_story_bank as B
from app.engine.services.annual_copy import find_banned
from app.engine.services.health_copy import find_medical
from app.engine.services.now_me_copy import validate_paragraph

ROWS = list(B.all_strings())
DAY = re.compile(B.DAY_END_RE)
BAN = re.compile(B.BANNED_RE)
FORBID = ("질병", "사망", "사고", "이혼")


def _core(birth: date, clock: time, gender="male"):
    return calculate_myeongri_core(
        BirthInput(name="테스트", gender=gender, birth_date=birth, birth_time=clock, time_unknown=False),
        target_date=date(2026, 10, 24),
    )


def _jungoh():
    return _core(date(1978, 3, 13), time(11, 0))   # test_now_me·test_daily_score 와 같은 테스트 원국


def _fresh():
    daily_rx._RENDER_CACHE.clear()
    daily_rx._HISTORY_CACHE.clear()


def _day_ends(s):
    return [x for x in S.sents(s) if DAY.search(x)]


# ---------------------------------------------------------------------------
# 은행
# ---------------------------------------------------------------------------
class BankTests(unittest.TestCase):
    def test_keys_match_card_bank_and_ten_gods(self):
        self.assertEqual(set(B.TITLE), set(daily_rx.EVIDENCE))
        self.assertEqual(set(B.LEAD), set(daily_rx.EVIDENCE))
        self.assertEqual(set(B.GOD_COLOR), set(daily_sections.SECTION_GODS))
        self.assertEqual(set(B.DOMAIN), {"금전", "애정·관계", "일", "건강"})
        self.assertEqual([t for _, t in S.SECTION_ORDER], ["금전", "애정·관계", "일", "건강"])

    def test_validators_zero(self):
        for name, path, s in ROWS:
            self.assertEqual(find_banned(s), [], (name, path, s))
            self.assertEqual(find_medical(s), [], (name, path, s))
            self.assertEqual([i for i in validate_paragraph(s) if "깁니다" not in str(i)], [], (name, path, s))
            self.assertFalse(any(w in s for w in FORBID), (name, path, s))
            self.assertFalse(BAN.search(s) and s not in B.GOLD, (name, path, s))

    def test_gi_un_only_in_the_gold_sample(self):
        hits = [(n, p) for n, p, s in ROWS if "기운" in s]
        self.assertEqual(hits, [("LEAD", ("day지 충", 0, "scene"))])
        self.assertTrue(all(any(x in g for g in B.GOLD) for n, p, s in ROWS for x in S.sents(s) if len(x) > 46),
                        "46자 초과 문장은 정오님 문장뿐이어야 한다")

    def test_no_duplicate_strings(self):
        dup = [k for k, c in collections.Counter(s for _, _, s in ROWS).items() if c > 1]
        self.assertEqual(dup, [])

    def test_day_ending_budget_per_bank(self):
        # "~날입니다" 말끝은 제목과 scene 첫 문장에만. 분야 문단은 첫 문장에 0~1회. 나머지 0회(정오님 문장 예외).
        for name, path, s in ROWS:
            if name == "TITLE" or s in B.GOLD:
                continue
            de = _day_ends(s)
            if name == "LEAD" and path[2] == "scene":
                self.assertLessEqual(len([x for x in de if x != S.sents(s)[0]]), 0, (path, s))
            elif name == "DOMAIN":
                self.assertLessEqual(len(de), 1, (path, s))
                if de:
                    self.assertEqual(de[0], S.sents(s)[0], (path, s))
            else:
                self.assertEqual(de, [], (name, path, s))

    def test_titles(self):
        for key, lst in B.TITLE.items():
            for i, t in enumerate(lst):
                s = t["text"]
                self.assertTrue(8 <= len(s) <= 20, s)
                self.assertTrue(s.endswith(("날", "하루")), s)
                self.assertFalse(re.search(r"기운|편|쪽|흐름|흐르", s), s)
                self.assertEqual(t["grade_ok"], B.LEAD[key][i]["grade_ok"], (key, i))
            for g in B.ALL:
                self.assertTrue(any(g in v["grade_ok"] for v in B.LEAD[key]), (key, g))

    def test_sentence_counts_and_adjacent_endings(self):
        for name, path, s in ROWS:
            n = len(S.sents(s))
            if name == "LEAD":
                self.assertEqual(n, 2 if path[2] == "scene" else 1, (path, s))
            elif name == "DOMAIN":
                self.assertEqual(n, 2 if path[1] == "보통" else 3, (path, s))
            elif name in ("LOVE", "GOD_COLOR", "CLOSE", "DOMAIN_EXTRA"):
                self.assertEqual(n, 1, (name, path, s))
            elif name in ("ATTITUDE", "SECOND"):
                self.assertIn(n, (1, 2), (name, path, s))
            ss = S.sents(s)
            for a, b in zip(ss, ss[1:]):
                self.assertTrue(S.ending(a) != S.ending(b) or s in B.GOLD, (name, path, s))

    def test_lukewarm_phrases_never_allowed_on_good_days(self):
        for name in ("TITLE", "LEAD", "SECOND", "DOMAIN", "DOMAIN_EXTRA", "LOVE", "GOD_COLOR"):
            for path, s in [(p, s) for n, p, s in ROWS if n == name]:
                if any(w in s for w in B.LUKEWARM + B.LUKEWARM_MID_ONLY):
                    node = B.BANKS[name]
                    for k in path[:-1] if isinstance(path[-1], str) else path:
                        node = node[k]
                    self.assertFalse(any(g in node["grade_ok"] for g in B.GOOD), (name, path, s))
        for g in B.GOOD:
            for s in B.ATTITUDE[g] + B.CLOSE[g]:
                self.assertFalse(any(w in s for w in B.LUKEWARM + B.LUKEWARM_MID_ONLY), s)

    def test_god_color_topics_meet_a_neutral_paragraph(self):
        dom_topics = {d: {t for p in B.DOMAIN[d]["보통"] for t in p["topics"]} for d in B.DOMAIN}
        for god, doms in B.GOD_COLOR.items():
            for d, lst in doms.items():
                for e in lst:
                    self.assertTrue(set(e["topic"]) & dom_topics[d], (god, d, e["text"]))

    def test_gold_sentences_are_all_in_the_bank(self):
        texts = [s for _, _, s in ROWS]
        for g in B.GOLD:
            self.assertTrue(any(g == s or g in s for s in texts), g)


# ---------------------------------------------------------------------------
# 조립
# ---------------------------------------------------------------------------
def _body_checks(tc, story):
    """조립 규칙 — build_story 안의 assert 와 별도로 결과물에서 다시 센다."""
    body = " ".join([story["overall"]] + [s["text"] for s in story["sections"]] + ([story["closing"]] if story["closing"] else []))
    tc.assertLessEqual(body.count("기운"), 1, body)
    tc.assertLessEqual(len(S.GYEOL.findall(story["title"] + " " + body)), 2, body)
    tc.assertLessEqual(len(_day_ends(body)), 6, body)
    tc.assertLessEqual(len(_day_ends(story["overall"])), 2, story["overall"])
    tc.assertLessEqual(len(re.findall(r"면 됩니다", body)), 3, body)
    tc.assertLessEqual(body.count("법이죠"), 1, body)
    tc.assertIsNone(BAN.search(body), BAN.findall(body))
    tc.assertEqual(find_banned(body) + find_medical(body), [], body)
    tc.assertLess(story["overall"].count("오늘"), 3, story["overall"])
    tc.assertTrue(3 <= len(S.sents(story["overall"])) <= 7, story["overall"])
    for sec in story["sections"]:
        tc.assertLessEqual(len(_day_ends(sec["text"])), 1, sec)
        tc.assertLess(sec["text"].count("오늘"), 3, sec)
        tc.assertTrue(2 <= len(S.sents(sec["text"])) <= 5, sec)
        ss = S.sents(sec["text"])
        for a, b in zip(ss, ss[1:]):
            tc.assertTrue(S.ending(a) != S.ending(b) or any((a + " " + b) in g for g in B.GOLD), sec)
    tc.assertEqual([s["key"] for s in story["sections"]], ["money", "love", "work", "health"])
    tc.assertEqual([s["title"] for s in story["sections"]], ["금전", "애정·관계", "일", "건강"])
    tc.assertEqual(story["closing"] is None, story["grade"] == "보통", story)
    if story["grade"] in B.GOOD:
        tc.assertFalse(any(w in body for w in B.LUKEWARM), body)


class AssemblyTests(unittest.TestCase):
    # v5 조립본(/home/claude/reports/오늘의 이야기 은행 v5 보고.md §7)과 같은 계산: 계정 "x", 이력은 RX_EPOCH 60일 전부터 복원.
    SNAPSHOT = {
        date(2026, 10, 24): ("힘을 덜 들여도 일이 되는 날", (6, 2, 3, 4, 2), True),
        date(2026, 10, 25): ("평소 못 하던 일이 되는 날", (4, 2, 3, 3, 4), True),
        date(2026, 10, 26): ("하던 일 하나만 끝내는 날", (4, 3, 3, 3, 4), False),
        date(2026, 10, 27): ("일터에서 도움을 받을 수 있는 날", (4, 3, 2, 3, 2), False),
        date(2026, 10, 28): ("몸이 무겁고 마음이 급해지기 쉬운 날", (4, 2, 4, 2, 2), True),
        date(2026, 10, 29): ("집안에서 뜻밖의 소식이 오는 날", (5, 2, 2, 3, 2), True),
        date(2026, 10, 30): ("그럭저럭 무난히 흘러가는 하루", (6, 2, 3, 4, 2), False),
    }

    def test_seven_days_match_the_v5_assembly(self):
        core = _jungoh()
        _fresh()
        for d, (title, counts, has_close) in self.SNAPSHOT.items():
            out = daily_rx.render_day(core, "x", d)
            story = out["story"]
            self.assertIsNotNone(story, d)
            self.assertEqual(story["title"], title, d)
            got = (len(S.sents(story["overall"])),) + tuple(len(S.sents(s["text"])) for s in story["sections"])
            self.assertEqual(got, counts, (d, story))
            self.assertEqual(story["closing"] is not None, has_close, (d, story["closing"]))
            self.assertEqual(out["story_uses"], story["uses"])
            self.assertFalse(any(e == S.USE_ELEMENT for e, _, _ in out["uses"]), "카드 몫 uses 에 이야기 항목이 섞이면 안 된다")

    def test_grade_changes_the_overall_for_the_same_ten_god(self):
        core = _jungoh()
        d = date(2026, 10, 24)                                   # 辛未 · 정관 · 억부 희신 top
        ev = daily_score.evaluate(core, daily_score.day_ganji(d), d)
        rx = daily_rx.select_for_day(core, "x", d, [], ev)
        good = S.build_story(core, ev, rx, "x", d, "male", [])
        bad_ev = dict(ev, grade="나쁨", score=55)
        bad = S.build_story(core, bad_ev, rx, "x", d, "male", [])
        self.assertEqual(good["god"], bad["god"])
        self.assertNotEqual(good["overall"], bad["overall"])
        self.assertNotEqual(good["title"], bad["title"])
        self.assertNotEqual(good["closing"], bad["closing"])
        self.assertFalse(any(w in good["overall"] for w in B.LUKEWARM))
        self.assertIn(bad["closing"], B.CLOSE["나쁨"])
        self.assertIn(good["closing"], B.CLOSE["좋음"])

    def test_deterministic(self):
        core = _jungoh()
        d = date(2026, 11, 2)
        _fresh()
        first = daily_rx.render_day(core, "acc-정오", d)
        _fresh()
        second = daily_rx.render_day(core, "acc-정오", d)
        self.assertEqual(first["story"], second["story"])
        ev = first["evaluation"]
        a = S.build_story(core, ev, first, "acc-정오", d, "male", [])
        b = S.build_story(core, ev, first, "acc-정오", d, "male", [])
        self.assertEqual(a, b)

    def test_love_signal_follows_gender(self):
        items = [("억부 희신", 10)]
        self.assertEqual(S.love_signal(items, "direct_wealth", "male", (), "子"), "재성")
        self.assertIsNone(S.love_signal(items, "direct_wealth", "female", (), "子"))
        self.assertEqual(S.love_signal(items, "direct_officer", "female", (), "子"), "관성")
        self.assertIsNone(S.love_signal(items, "direct_officer", "male", (), "子"))
        self.assertEqual(S.love_signal(items, "peer", "male", ("午",), "卯"), "도화")
        self.assertEqual(S.love_signal([("day지 육합", 6)], "direct_wealth", "male", (), "子"), "일지 육합")
        self.assertEqual(S.love_signal([("day지 충", -8)], "direct_wealth", "male", (), "子"), "일지 충")

    def test_domain_tiers(self):
        self.assertEqual(S.domain_tiers({"금전": 1, "사람": 2, "일": 6, "건강": -4}, "좋음"),
                         {"금전": "보통", "애정·관계": "보통", "일": "좋음", "건강": "보통"})
        self.assertEqual(S.domain_tiers({"금전": -4, "사람": -4, "일": 0, "건강": -3}, "나쁨"),
                         {"금전": "주의", "애정·관계": "주의", "일": "보통", "건강": "주의"})

    def test_story_payload_keeps_the_screen_keys(self):
        core = _jungoh()
        _fresh()
        out = daily_rx.render_day(core, "x", date(2026, 10, 24))
        story = S.story_payload({"lead": "career", "tone": "calm"}, out["story"])
        self.assertEqual(story["headline"], story["title"])
        self.assertEqual(story["body"], story["overall"])
        self.assertEqual(story["lead"], "career")
        for sec in story["sections"]:
            self.assertEqual(sec["body"], sec["text"])
            self.assertIn(sec["key"], ("money", "love", "work", "health"))
        self.assertIn("closing", story)
        self.assertEqual(story["tiers"]["일"], "좋음")

    def test_thirty_day_rotation_for_story_variants(self):
        core = _jungoh()
        _fresh()
        timeline = []
        for i in range(60):
            d = date(2026, 10, 24) + timedelta(days=i)
            out = daily_rx.render_day(core, "acc-정오", d)
            self.assertIsNotNone(out["story"], d)
            _body_checks(self, out["story"])
            timeline.extend((d, k, idx) for _, k, idx in out["story_uses"])
        for n, (d, k, idx) in enumerate(timeline):
            prior = [p_idx for p_d, p_k, p_idx in timeline[:n] if p_k == k and p_d >= d - timedelta(days=daily_rx.RECENT_DAYS)]
            if idx in prior:
                # 30일 안에 같은 변형이 다시 나오는 건 다른 변형을 먼저 다 돌린 뒤뿐(후보가 조건으로 줄어든 날 포함)
                self.assertGreaterEqual(len(set(prior)), 2, (d, k, idx, prior))

    def test_two_hundred_random_births_seven_days(self):
        rng = random.Random(2026)
        seen_titles, seen_love = set(), set()
        for n in range(200):
            birth = date(rng.randint(1950, 2008), rng.randint(1, 12), rng.randint(1, 28))
            gender = rng.choice(["male", "female"])
            core = _core(birth, time(rng.randint(0, 23), 0), gender)
            recent = []
            for i in range(7):
                d = date(2026, 10, 24) + timedelta(days=i)
                ev = daily_score.evaluate(core, daily_score.day_ganji(d), d)
                rx = daily_rx.select_for_day(core, f"acc{n}", d, recent, ev)
                self.assertIsNotNone(rx["story"], (birth, gender, d))
                story = S.build_story(core, ev, rx, f"acc{n}", d, gender, recent)
                self.assertEqual(story, rx["story"])
                self.assertEqual(story["grade"], ev["grade"])
                _body_checks(self, story)
                recent.extend(story["uses"])
                seen_titles.add(story["title"])
                if story["love"]:
                    seen_love.add(story["love"])
        self.assertGreater(len(seen_titles), 25)
        self.assertTrue({"재성", "관성"} <= seen_love, seen_love)


class FortuneWiringTests(unittest.TestCase):
    def test_build_daily_fortune_carries_the_new_story(self):
        from app.engine.services.daily import build_daily_fortune, DAILY_FORTUNE_VERSION
        core = _jungoh()
        _fresh()
        out = build_daily_fortune(core, "테스트", date(2026, 10, 24), account_key="x", include_menu=False)
        story = out["story"]
        self.assertEqual(out["engine_version"], DAILY_FORTUNE_VERSION)
        self.assertEqual(story["story_version"], S.STORY_VERSION)
        self.assertEqual(story["headline"], "힘을 덜 들여도 일이 되는 날")
        self.assertEqual(story["title"], story["headline"])
        self.assertEqual([s["title"] for s in story["sections"]], ["금전", "애정·관계", "일", "건강"])
        self.assertTrue(all(s["body"] == s["text"] for s in story["sections"]))
        self.assertEqual(story["closing"], "순조로운 하루이니 무리 없이 보내도 좋겠네요.")
        self.assertNotIn("한 가지 더", story["body"])

    def test_falls_back_to_the_old_story_when_v2_fails(self):
        from app.engine.services import daily
        core = _jungoh()
        base = {"headline": "기존", "body": "기존 본문입니다.", "sections": []}
        rx = {"evidence_text": "x", "domain_note": None}          # story 키가 없으면 직접 조립을 시도한다
        ev = daily_score.evaluate(core, daily_score.day_ganji(date(2026, 10, 24)), date(2026, 10, 24))
        self.assertEqual(daily._story_v2(base, core, ev, rx, "x", date(2026, 10, 24))["title"], "업무와 약속이 제때 지켜지는 날")   # 이력 없이 직접 조립
        self.assertIs(daily._story_v2(base, core, ev, {"story": None}, "x", date(2026, 10, 24)), base)
        self.assertIs(daily._story_v2(base, core, {"items": None}, rx, "x", date(2026, 10, 24)), base)   # 조립 예외 → 폴백


if __name__ == "__main__":
    unittest.main()
