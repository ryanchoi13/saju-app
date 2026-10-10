"""오늘의 이야기 문장 은행 계약.

- 문장 풀이 너무 작으면 매일 읽는 사람이 며칠 안에 같은 문장을 다시 만난다(2026-10-10: 2·3번째 문장 은행이 18개뿐이었음).
- 길이·문체 범위(STORY_GUARD)는 상수로만 있었고 검사하는 테스트가 없었다.
이 테스트가 풀 크기, 문장 길이, 문체, 금지어·의학 표현, 중복, 최악 조합의 전체 길이를 지킨다.
"""
import unittest

from app.engine.services import daily_copy as dc

GUARD = dc.STORY_GUARD
MIN_POOL = {"A": 6, "B": 6, "TIP": 6, "CAUTION": 5, "CLOSING": 5}


def _banks():
    for god, pool in dc.STORY_A_GOD.items():
        yield f"A_GOD[{god}]", "A", pool, "입니다."
    for rel, pool in dc.STORY_B_REL.items():
        yield f"B_REL[{rel}]", "B", pool, "요."
    for lead, pool in dc.STORY_TIP.items():
        yield f"TIP[{lead}]", "TIP", pool, "보세요."
    for rel, pool in dc.STORY_CAUTION.items():
        yield f"CAUTION[{rel}]", "CAUTION", pool, "보세요."
    for kind, pool in dc.STORY_CLOSING.items():
        yield f"CLOSING[{kind}]", "CLOSING", pool, "법이죠."


class DailyStoryBankTests(unittest.TestCase):
    def test_pools_are_large_enough_to_avoid_visible_repeats(self):
        for name, kind, pool, _ in _banks():
            self.assertGreaterEqual(len(pool), MIN_POOL[kind], f"{name} 풀이 작습니다({len(pool)})")

    def test_every_sentence_follows_voice_and_length_rules(self):
        for name, kind, pool, ending in _banks():
            for sentence in pool:
                self.assertTrue(sentence.endswith(ending), f"{name} 어미: {sentence}")
                self.assertLessEqual(len(sentence), GUARD["sentence_max"], f"{name} 너무 김({len(sentence)}): {sentence}")
                self.assertEqual(dc.find_banned(sentence), [], f"{name} 금지어: {sentence}")
                self.assertEqual(dc.find_medical(sentence), [], f"{name} 의학 표현: {sentence}")
            if kind == "B" and ("clash" in name or "friction" in name):
                for sentence in pool:
                    self.assertTrue(sentence.startswith("다만 "), f"{name}: {sentence}")

    def test_no_duplicate_sentences_across_banks(self):
        seen = {}
        for name, _, pool, _e in _banks():
            for sentence in pool:
                self.assertNotIn(sentence, seen, f"{name} 와 {seen.get(sentence)} 에 같은 문장")
                seen[sentence] = name

    def test_composed_story_stays_inside_guard_for_every_combination(self):
        lo_c, hi_c = GUARD["chars"]
        lo_s, hi_s = GUARD["sentences"]
        for god in dc.STORY_A_GOD:
            for rel in dc.STORY_B_REL:
                for lead in dc.LEADS:
                    for seed in range(0, 3000, 7):
                        story = dc.compose_story(lead, "calm", seed, god=god, rel=rel)
                        self.assertTrue(lo_s <= story["sentence_count"] <= hi_s, (god, rel, lead, seed))
                        self.assertTrue(lo_c <= story["char_count"] <= hi_c,
                                        f"{god}/{rel}/{lead}/{seed}: {story['char_count']}자")

    def test_worst_case_total_length_fits(self):
        # 시드와 무관하게, 각 은행에서 가장 긴 문장만 골라도 상한 안이어야 한다.
        hi_c = GUARD["chars"][1]
        longest = lambda pools: max(len(x) for p in pools for x in p)
        a = longest(dc.STORY_A_GOD.values())
        b = longest(dc.STORY_B_REL.values())
        tip = longest(dc.STORY_TIP.values())
        caution = longest(dc.STORY_CAUTION.values())
        closing = longest(dc.STORY_CLOSING.values())
        worst = a + b + tip + caution + closing + 4          # 문장 5개 + 공백 4개
        self.assertLessEqual(worst, hi_c, f"최악 조합 {worst}자")

    def test_same_day_same_story_and_different_days_vary(self):
        a = dc.compose_story("career", "calm", 12345, god="peer", rel="calm")
        b = dc.compose_story("career", "calm", 12345, god="peer", rel="calm")
        self.assertEqual(a, b)
        bodies = {dc.compose_story("career", "calm", seed, god="peer", rel="calm")["body"] for seed in range(0, 2000, 3)}
        self.assertGreaterEqual(len(bodies), 20, "같은 조건에서도 문장 조합이 충분히 달라야 합니다")


if __name__ == "__main__":
    unittest.main()
