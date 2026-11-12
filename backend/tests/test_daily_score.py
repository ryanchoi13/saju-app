"""오늘의 운세 길흉 등급 — 산식·매핑·문장 은행·선택기 검사 (2026-10-24 설계안·보정안)."""
import collections
import random
import re
import unittest
from datetime import date, time, timedelta

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services import daily_copy, daily_rx, daily_score as ds
from app.engine.services.annual_copy import find_banned, split_sentences
from app.engine.services.health_copy import find_medical
from app.engine.services.now_me_copy import validate_paragraph

SENTENCE_MAX = 46
FORBIDDEN = re.compile(r"친다|꼰다|자리를|정면")


def _core(birth: date, clock: time, gender="male", target=date(2026, 10, 24)):
    return calculate_myeongri_core(
        BirthInput(name="테스트", gender=gender, birth_date=birth, birth_time=clock, time_unknown=False),
        target_date=target,
    )


def _jungoh():
    return _core(date(1978, 3, 13), time(11, 0))   # test_now_me._core 와 같은 원국: 戊午 乙卯 甲戌 己巳, strong


class BankTests(unittest.TestCase):
    def test_banks_have_expected_shape(self):
        self.assertTrue(all(len(rows) == 4 for rows in daily_rx.EVIDENCE.values()), "근거는 요소마다 4변형")
        self.assertEqual(sum(len(r) for r in daily_rx.EVIDENCE.values()), 4 * len(daily_rx.EVIDENCE))
        self.assertEqual(sorted(daily_rx.DOMAIN), sorted(ds.DOMAINS))
        self.assertEqual(sum(len(rows) for k in daily_rx.DOMAIN.values() for rows in k.values()), 48)
        self.assertEqual(len(daily_rx.BANK), 10)
        self.assertEqual(sum(len(d["dont"]) + len(d["do"]) for d in daily_rx.BANK.values()), 361)   # 11/12 BANK_EXTRA 241 더함(union 몸 하지 말 것은 원래 0개라 4개)
        for name, data in daily_rx.BANK.items():
            for kind in ("dont", "do"):
                self.assertGreaterEqual(len(data[kind]), 6, f"{name}.{kind}")
                for scene in ("돈", "일", "사람", "몸"):    # 11/12: 분야 장면은 칸마다 4문장 이상(되풀이 방지)
                    self.assertGreaterEqual(sum(sc == scene for sc, _, _ in data[kind]), 4, f"{name}.{kind}.{scene}")
                variants = [v for _, v, _ in data[kind]]
                self.assertIn("season", variants, f"{name}.{kind}")
                self.assertTrue(set(variants) & {"weekday", "weekend"}, f"{name}.{kind}")

    def test_every_sentence_passes_validators(self):
        for src, text in daily_rx.all_sentences():
            self.assertEqual(validate_paragraph(text), [], f"{src}: {text}")
            self.assertEqual(find_banned(text), [], src)
            self.assertEqual(find_medical(text), [], src)
            self.assertIsNone(FORBIDDEN.search(text), f"{src}: {text}")
            for s in split_sentences(text):
                self.assertLessEqual(len(s), SENTENCE_MAX, f"{src}: {s}")

    def test_evidence_and_domain_are_two_sentences_and_bank_is_one(self):
        for key, rows in daily_rx.EVIDENCE.items():
            for t in rows:
                self.assertEqual(len(split_sentences(t)), 2, f"EVIDENCE[{key}]: {t}")
        for dom, kinds in daily_rx.DOMAIN.items():
            for kind, rows in kinds.items():
                for t in rows:
                    self.assertEqual(len(split_sentences(t)), 2, f"DOMAIN[{dom}][{kind}]: {t}")
        for name, data in daily_rx.BANK.items():
            for kind in ("dont", "do"):
                for _, _, t in data[kind]:
                    self.assertEqual(len(split_sentences(t)), 1, f"BANK[{name}][{kind}]: {t}")

    def test_label_avoids_the_medical_word(self):
        self.assertEqual(daily_rx.LABEL, "오늘은 이렇게")
        self.assertEqual(find_medical(daily_rx.LABEL), [])

    def test_every_score_item_label_has_evidence_and_rx_mapping(self):
        labels = {f"{pos}지 {kind}" for pos in ds.NATAL_PILLARS for kind in ("충", "형", "육합", "반합")}
        labels |= {"day지 해파", "month지 해파", "삼합", "방합", "일간 천간합", "일간 천간충", "일간 천간극",
                   "결핍 채움", "과다 강화", "억부 희신", "억부 기신", "천을귀인", "문창", "양인 일진", "백호 일진"}
        labels |= {f"12운성 {stage}" for stage in ds.STAGE_W}
        for label in labels:
            if label.endswith("해파"):          # 해·파만 있는 날은 '잔잔'으로 간다(확신 약)
                self.assertEqual(daily_rx.evidence_key([(label, -3)]), "잔잔")
                continue
            key = daily_rx.EVIDENCE_ALIAS.get(label, label)
            self.assertIn(key, daily_rx.EVIDENCE, label)
            self.assertTrue(key in daily_rx.CAUTION_MAP or key in daily_rx.LUCKY_MAP, label)
        for element in set(daily_rx.CAUTION_MAP.values()) | set(daily_rx.LUCKY_MAP.values()):
            self.assertIn(element, daily_rx.BANK)


class ScoreMappingTests(unittest.TestCase):
    def test_tiebreak_keeps_integer_order_and_pushes_busy_days_outward(self):
        quiet = ds.raw_score([])
        busy = ds.raw_score([("day지 육합", 15), ("day지 충", -15)])
        self.assertEqual(quiet, 0.0)
        self.assertGreater(busy, quiet)
        self.assertLess(busy, 1.0)
        self.assertLess(ds.raw_score([("day지 충", -20), ("일간 천간충", -12), ("억부 희신", 10)]),
                        ds.raw_score([("day지 충", -20), ("과다 강화", -2)]))
        self.assertGreater(ds.raw_score([("결핍 채움", 3)]), ds.raw_score([("결핍 채움", 2), ("문창", 0)]))

    def test_display_is_monotonic_and_in_range_and_grade_bands_match(self):
        previous = 50
        for raw10 in range(-700, 701):
            score = ds.display_score(raw10 / 10)
            self.assertTrue(50 <= score <= 100)
            self.assertGreaterEqual(score, previous)
            previous = score
        self.assertEqual([ds.grade(s) for s in (50, 59, 60, 69, 70, 79, 80, 89, 90, 100)],
                         ["나쁨", "나쁨", "주의", "주의", "보통", "보통", "좋음", "좋음", "아주 좋음", "아주 좋음"])
        self.assertEqual(ds.grade(ds.display_score(ds.raw_score([]))), "보통")   # 요소 없는 날은 보통(11/11 재생성 후 70)

    def test_cdf_knots_are_sorted(self):
        fs = [f for f, _ in ds.RAW_CDF]
        ks = [k for _, k in ds.RAW_CDF]
        self.assertEqual(fs, sorted(fs))
        self.assertEqual(ks, sorted(ks))
        self.assertEqual((fs[0], fs[-1]), (0.0, 1.0))
        self.assertGreaterEqual(len(ds.RAW_CDF), 25)

    def test_standout_thresholds(self):
        self.assertIsNone(ds.standout({"금전": 7, "사람": -7, "일": 9, "건강": 0}))
        self.assertEqual(ds.standout({"금전": 0, "사람": -8, "일": 10, "건강": 0}), ("사람", "주의"))
        self.assertEqual(ds.standout({"금전": 0, "사람": 0, "일": 10, "건강": 0}), ("일", "좋음"))

    def test_good_day_lowers_only_the_good_threshold(self):
        """좋음·아주 좋음 날은 편차 +3부터 좋은 분야를 말한다(이야기 분야 결과 같은 저울). 주의 쪽은 그대로."""
        mid = {"금전": 1, "사람": 2, "일": 6, "건강": -4}
        self.assertIsNone(ds.standout(mid))                                   # 등급을 모르면 예전 규칙
        self.assertIsNone(ds.standout(mid, "보통"))
        self.assertIsNone(ds.standout(mid, "주의"))
        self.assertEqual(ds.standout(mid, "좋음"), ("일", "좋음"))
        self.assertEqual(ds.standout(mid, "아주 좋음"), ("일", "좋음"))
        self.assertIsNone(ds.standout({"금전": 1, "사람": 2, "일": 2, "건강": 0}, "좋음"))   # +2+3 < 6
        self.assertEqual(ds.standout({"금전": 3, "사람": 0, "일": 0, "건강": 0}, "좋음"), ("금전", "좋음"))
        # 좋은 날에도 −8 이하 분야가 있으면 주의가 먼저다(길흉을 포장하지 않는다)
        self.assertEqual(ds.standout({"금전": 6, "사람": 0, "일": 0, "건강": -8}, "좋음"), ("건강", "주의"))
        # 이야기의 분야 결과 같은 판정인지 — 같은 편차·같은 등급이면 둘이 어긋나지 않는다
        from app.engine.services import daily_story
        for grade_name in ("좋음", "아주 좋음"):
            for d in range(-6, 12):
                deltas = {"금전": d, "사람": 0, "일": 0, "건강": 0}
                shown = ds.standout(deltas, grade_name)
                tier = daily_story.domain_tiers(deltas, grade_name)["금전"]
                if d > ds.STANDOUT_CAUTION and d < ds.STANDOUT_GOOD:
                    self.assertEqual(shown == ("금전", "좋음"), tier == "좋음", (grade_name, d))

    def test_confidence_levels(self):
        self.assertEqual(ds.confidence([("day지 충", -20)]), "강")
        self.assertEqual(ds.confidence([("day지 형", -8), ("문창", 3)]), "중")
        self.assertEqual(ds.confidence([("day지 해파", -3)]), "약")
        self.assertEqual(ds.confidence([]), "약")
        self.assertEqual(daily_rx.evidence_key([("day지 해파", -3)]), "잔잔")
        self.assertEqual(daily_rx.evidence_key([("12운성 tomb", -4)]), "12운성 down")


class TestChartTests(unittest.TestCase):
    """정오 원국(戊午 乙卯 甲戌 己巳, 신강) — 설계안 검증 조건."""

    def test_known_days(self):
        core = _jungoh()
        self.assertEqual({k: v.ganji for k, v in core.natal_facts.pillars.items()},
                         {"year": "戊午", "month": "乙卯", "day": "甲戌", "hour": "己巳"})
        self.assertEqual(ds.yong_direction(core), "strong")
        results = {}
        for d in (date(2026, 11, 1), date(2026, 11, 2), date(2026, 11, 5)):
            results[d] = ds.evaluate(core, ds.day_ganji(d), d)
        bad = results[date(2026, 11, 2)]          # 庚辰: 일지 충 −20 + 일간 충 −12
        self.assertEqual(bad["grade"], "나쁨", bad)
        self.assertIn(("day지 충", -20), bad["items"])
        self.assertIn(("일간 천간충", -12), bad["items"])
        self.assertEqual(bad["standout"], ("사람", "주의"))
        good = results[date(2026, 11, 1)]         # 己卯: 일지 육합 +15, 일간 합 +8 (양인 −6, 卯 木 피함 −6 상쇄)
        self.assertIn(("day지 육합", 15), good["items"])
        self.assertIn(("억부 기신", -6), good["items"])     # 己 土 무난 0 + 卯 木 피함 −6
        self.assertTrue(abs(good["score"] - 80) <= 2, good)   # 실측 2026-11-11: 79점

        # 癸未: 예전엔 결핍 채움 +10(水 0%). 11/11 3단계에서 水·土는 무난(틀끼리 의견이 갈림)이라 0
        neutral = results[date(2026, 11, 5)]
        names = [n for n, _ in neutral["items"]]
        for label in ("결핍 채움", "과다 강화", "억부 희신", "억부 기신"):
            self.assertNotIn(label, names)

    def test_good_day_shows_its_best_domain(self):
        """좋은 날엔 가장 좋은 분야가 뜬다. 11/12 庚寅(좋음 80, 일 +6) — 11/11 3단계 후 실측."""
        core = _jungoh()
        d = date(2026, 11, 12)
        ev = ds.evaluate(core, ds.day_ganji(d), d)
        self.assertEqual(ev["grade"], "좋음")
        self.assertEqual(ev["domain"]["일"], 6)
        self.assertEqual(ev["standout"], ("일", "좋음"))
        rx = daily_rx.render_day(core, "test-account", d, ev)
        self.assertEqual(rx["domain_note"]["domain"], "일")
        self.assertEqual(rx["domain_note"]["kind"], "좋음")
        self.assertTrue(rx["domain_note"]["text"])

    def test_tier_item_replaces_yong_and_balance(self):
        """11/11: 억부·결핍·과다 대신 오행 3단계 항목 하나. 행운 색과 같은 판정(정오님: 좋음 金火 / 무난 土水 / 피함 木)."""
        core = _jungoh()
        cases = {"辛未": ("억부 희신", 10),     # 辛 金 좋음 +10, 未 土 무난 0
                 "乙卯": ("억부 기신", -10),    # 木 피함 둘(천간 −10, 지지 −6 → −10으로 자름)
                 "甲午": ("억부 기신", -4),     # 甲 木 −10 + 午 火 +6
                 "癸亥": None, "己丑": None}    # 水·土 무난 → 항목 없음
        for gz, want in cases.items():
            self.assertEqual(ds.tier_item(core, gz), want, gz)
            names = [n for n, _ in ds.score_items(core, gz, date(2026, 11, 11))]
            self.assertEqual(sum(n in ("억부 희신", "억부 기신", "결핍 채움", "과다 강화") for n in names), 1 if want else 0, (gz, names))

    def test_scoring_from_a_base_core_matches_the_core_of_that_day(self):
        base = _jungoh()
        birth = base.input
        for offset in (0, 3, 9, 12):
            d = date(2026, 10, 24) + timedelta(days=offset)
            core = calculate_myeongri_core(birth, target_date=d)
            gj = core.timing.daily["pillar"]["ganji"]
            self.assertEqual(ds.day_ganji(d), gj)
            self.assertEqual(ds.score_items(base, gj, d), ds.score_items(core, gj, d))

    def test_undetermined_strength_keeps_yong_off(self):
        core = _jungoh()
        core.synthesis = core.synthesis.model_copy(update={"strength_state": "undetermined"})
        self.assertIsNone(ds.yong_item(core, "辛未"))
        self.assertFalse(any(n.startswith("억부") for n, _ in ds.score_items(core, "辛未", date(2026, 10, 24))))


class PopulationTests(unittest.TestCase):
    def test_distribution_over_random_births_follows_the_target_bands(self):
        rng = random.Random(7)
        span = (date(2005, 12, 31) - date(1950, 1, 1)).days
        counts = collections.Counter()
        start = date(2026, 10, 24)
        for _ in range(200):
            birth = date(1950, 1, 1) + timedelta(days=rng.randint(0, span))
            core = _core(birth, time(rng.randint(0, 23), 0), rng.choice(["male", "female"]), target=start)
            for i in range(30):
                d = start + timedelta(days=i)
                ev = ds.evaluate(core, ds.day_ganji(d), d)
                self.assertTrue(50 <= ev["score"] <= 100)
                self.assertEqual(ev["grade"], ds.grade(ev["score"]))
                counts[ev["grade"]] += 1
        total = sum(counts.values())
        share = {g: 100 * counts[g] / total for g in ds.GRADES}
        target = {"나쁨": 15, "주의": 20, "보통": 30, "좋음": 20, "아주 좋음": 15}
        for g, want in target.items():
            self.assertLessEqual(abs(share[g] - want), 6, share)


class SelectorTests(unittest.TestCase):
    def test_pick_is_deterministic_and_respects_variants(self):
        weekday, weekend = date(2026, 11, 4), date(2026, 11, 7)
        for d in (weekday, weekend):
            a = daily_rx.pick("acc", d, "day_clash", "dont", [])
            b = daily_rx.pick("acc", d, "day_clash", "dont", [])
            self.assertEqual(a, b)
            i, _ = a
            variant = daily_rx.BANK["day_clash"]["dont"][i][1]
            self.assertNotEqual(variant, "weekend" if d.weekday() < 5 else "weekday")
        summer = date(2027, 7, 14)
        for _ in range(12):
            i, _ = daily_rx.pick("acc", summer, "blade", "do", [])
            self.assertNotEqual(daily_rx.BANK["blade"]["do"][i][1], "season")

    def test_do_follows_the_scene_of_dont(self):
        text, uses = daily_rx.compose_rx("acc", date(2026, 11, 2), "day_clash", [])
        (_, _, i), (_, _, j) = uses
        self.assertEqual(daily_rx.BANK["day_clash"]["dont"][i][0], daily_rx.BANK["day_clash"]["do"][j][0])
        self.assertEqual(len(split_sentences(text)), 2)

    def test_rx_element_rules(self):
        items = [("day지 충", -20), ("일간 천간충", -12), ("억부 희신", 10)]
        self.assertEqual(daily_rx.rx_element(items, "나쁨", ("사람", "주의")), "day_clash")
        self.assertEqual(daily_rx.rx_element(items, "나쁨", ("금전", "주의")), "wealth_hit")
        self.assertEqual(daily_rx.rx_element([("hour지 충", -8), ("12운성 birth", 4)], "주의", None), "day_punish")
        self.assertIsNone(daily_rx.rx_element([("day지 형", -8)], "보통", None))
        self.assertEqual(daily_rx.rx_element([("결핍 채움", 10), ("day지 형", -8)], "좋음", None), "fill")
        self.assertEqual(daily_rx.rx_element([("천을귀인", 6), ("일간 천간합", 8)], "좋음", None), "union")

    def test_no_repeat_within_thirty_days_for_one_account(self):
        core = _jungoh()
        daily_rx._RENDER_CACHE.clear()
        daily_rx._HISTORY_CACHE.clear()
        start = date(2026, 10, 24)
        timeline = []   # (day, element, kind, idx)
        for i in range(60):
            d = start + timedelta(days=i)
            out = daily_rx.render_day(core, "acc-정오", d)
            self.assertTrue(out["evidence_text"])
            if out["evaluation"]["grade"] in daily_rx.CAUTION_GRADES | daily_rx.LUCKY_GRADES:
                self.assertTrue(out["rx_text"], (d, out["evaluation"]))
            else:
                self.assertIsNone(out["rx_text"])
            timeline.extend((d, e, k, idx) for e, k, idx in out["uses"])
        for n, (d, e, k, idx) in enumerate(timeline):
            prior = [p_idx for p_d, p_e, p_k, p_idx in timeline[:n]
                     if (p_e, p_k) == (e, k) and p_d >= d - timedelta(days=daily_rx.RECENT_DAYS)]
            if idx in prior:
                # 30일 안에 같은 문장이 다시 나오는 건 후보(최소 4개)를 다 썼을 때, 또는 (11/12) 처방이 이야기의 분야 장면에
                # 묶여 그 장면 문장을 다시 쓸 때뿐. 어느 쪽이든 7일 안에는 되풀이하지 않는다.
                week = [p_idx for p_d, p_e, p_k, p_idx in timeline[:n]
                        if (p_e, p_k) == (e, k) and p_d >= d - timedelta(days=daily_rx.WEEK_DAYS)]
                self.assertNotIn(idx, week, (d, e, k, idx, week))
                if k not in ("dont", "do"):
                    self.assertGreaterEqual(len(set(prior)), 4, (d, e, k, idx, prior))
        used_elements = {e for _, e, k, _ in timeline if k == "evidence"}
        self.assertGreaterEqual(len(used_elements), 5)

    def test_render_is_deterministic_across_calls(self):
        core = _jungoh()
        d = date(2026, 11, 2)
        daily_rx._RENDER_CACHE.clear()
        daily_rx._HISTORY_CACHE.clear()
        first = daily_rx.render_day(core, "acc-정오", d)
        daily_rx._RENDER_CACHE.clear()
        daily_rx._HISTORY_CACHE.clear()
        second = daily_rx.render_day(core, "acc-정오", d)
        self.assertEqual(first, second)
        other = daily_rx.render_day(core, "acc-다른사람", d)
        self.assertEqual(other["evaluation"], first["evaluation"])   # 점수는 계정과 무관, 문장만 달라질 수 있다


class StoryTests(unittest.TestCase):
    def test_story_no_longer_carries_the_caution_lines(self):
        caution = {s for pool in daily_copy.STORY_CAUTION.values() for s in pool} | set(daily_copy.STORY_CLOSING["careful"])
        for rel in ("clash", "friction", "calm"):
            for seed in range(0, 2000, 97):
                story = daily_copy.compose_story("career", "careful", seed, god="direct_wealth", rel=rel)
                self.assertFalse(caution & set(split_sentences(story["body"])), story["body"])
                self.assertEqual(story["sentence_count"], 3)
        lift = daily_copy.compose_story("career", "lift", 5, god="direct_wealth", rel="lift")
        self.assertEqual(lift["sentence_count"], 4)


if __name__ == "__main__":
    unittest.main()
