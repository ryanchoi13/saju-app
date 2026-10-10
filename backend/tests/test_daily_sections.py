"""오늘의 이야기 v2(총운 + 카테고리 문단) 은행 점검.

글의 좋고 나쁨은 사람이 읽고 정한다. 이 테스트는 사람이 놓치기 쉬운 것만 기계로 지킨다:
금칙어·의학 표현, 길이 범위, 문장 중복, 분량 순서(총운 > 카테고리), 보조 메시지 규칙, 결정론.
"""
import re
import unittest

from app.engine.services import daily_sections as ds
from app.engine.services.annual_copy import find_banned, split_sentences
from app.engine.services.health_copy import find_medical

G = ds.SECTION_GUARD


def _all_texts():
    for god, data in ds.SECTIONS.items():
        for key in ("overall", "money", "love", "work", "rhythm"):
            for i, text in enumerate(data[key]):
                yield god, key, i, text
    for rel, pool in ds.SECONDARY.items():
        for i, text in enumerate(pool):
            yield "secondary", rel, i, text


class SectionBankTests(unittest.TestCase):
    def test_every_cell_has_three_variants(self):
        for god, data in ds.SECTIONS.items():
            self.assertTrue(data["headline"] and len(data["headline"]) <= G["headline_max"], god)
            for key in ("overall", "money", "love", "work", "rhythm"):
                self.assertEqual(len(data[key]), 3, f"{god}.{key}")

    def test_no_banned_or_medical_words(self):
        for god, key, i, text in _all_texts():
            self.assertEqual(find_banned(text), [], f"{god}.{key}[{i}]")
            self.assertEqual(find_medical(text), [], f"{god}.{key}[{i}]")
        for god, data in ds.SECTIONS.items():
            self.assertEqual(find_banned(data["headline"]) + find_medical(data["headline"]), [], god)

    def test_length_and_sentence_guards(self):
        for god, key, i, text in _all_texts():
            guard = G["overall"] if key == "overall" else G["section"]
            if god == "secondary":
                guard = {"sentences": (2, 2), "chars": (30, 80)}
            sentences = split_sentences(text)
            where = f"{god}.{key}[{i}] {text}"
            self.assertGreaterEqual(len(sentences), guard["sentences"][0], where)
            self.assertLessEqual(len(sentences), guard["sentences"][1], where)
            self.assertGreaterEqual(len(text), guard["chars"][0], where)
            self.assertLessEqual(len(text), guard["chars"][1], where)
            for s in sentences:
                self.assertLessEqual(len(s), G["sentence_max"], f"긴 문장: {s}")

    def test_no_duplicate_sentences(self):
        seen = {}
        for god, key, i, text in _all_texts():
            for s in split_sentences(text):
                self.assertNotIn(s, seen, f"중복 문장: {s} ({seen.get(s)} / {god}.{key}[{i}])")
                seen[s] = f"{god}.{key}[{i}]"

    def test_no_slot_words_and_no_study_section(self):
        # 오전/오후 표현은 시간대 팁 카드와 겹치므로 본문에 쓰지 않는다. 학업은 이번 범위가 아니다.
        for god, key, i, text in _all_texts():
            self.assertIsNone(re.search(r"오전|오후|학업|시험|공부", text), f"{god}.{key}[{i}]")
        self.assertEqual([k for k, _ in ds.SECTION_ORDER], ["money", "love", "work", "rhythm"])

    def test_secondary_marker_only_in_secondary_pool(self):
        for god, key, i, text in _all_texts():
            has = text.startswith("한 가지 더")
            self.assertEqual(has, god == "secondary", f"{god}.{key}[{i}]")

    def test_overall_longer_than_each_section_on_average(self):
        for god, data in ds.SECTIONS.items():
            avg_overall = sum(map(len, data["overall"])) / 3
            for key in ("money", "love", "work", "rhythm"):
                avg = sum(map(len, data[key])) / 3
                self.assertGreater(avg_overall, avg, f"{god}.{key}")


class EnrichStoryTests(unittest.TestCase):
    BASE = dict(headline="기존", body="기존 본문입니다.", char_count=8, sentence_count=1,
                lead="career", tone="calm", god="x", rel="calm")

    def test_uncovered_god_is_untouched(self):
        for god in ("peer", "direct_wealth", None):
            self.assertEqual(ds.enrich_story(dict(self.BASE), god, "calm", 123), self.BASE)

    def test_covered_god_gets_four_sections_in_order(self):
        for god in ds.SECTION_GODS:
            story = ds.enrich_story(dict(self.BASE), god, "calm", 98765)
            self.assertEqual([s["key"] for s in story["sections"]], ["money", "love", "work", "rhythm"])
            self.assertEqual([s["title"] for s in story["sections"]], ["재물운", "연애·관계", "일", "생활 리듬"])
            self.assertTrue(all(s["body"] for s in story["sections"]))
            self.assertEqual(story["headline"], ds.SECTIONS[god]["headline"])
            self.assertEqual(story["char_count"], len(story["body"]))

    def test_calm_has_no_secondary_and_signals_do(self):
        for god in ds.SECTION_GODS:
            for seed in range(0, 3000, 37):
                calm = ds.enrich_story(dict(self.BASE), god, "calm", seed)["body"]
                self.assertNotIn("한 가지 더", calm)
                for rel in ("lift", "clash", "friction"):
                    body = ds.enrich_story(dict(self.BASE), god, rel, seed)["body"]
                    self.assertEqual(body.count("한 가지 더"), 1, body)
                    self.assertTrue(body.startswith(calm), "보조 메시지는 주 메시지 뒤에만 붙는다")

    def test_story_guard_ranges_for_combined_overall(self):
        for god in ds.SECTION_GODS:
            for seed in range(0, 5000, 53):
                for rel in ("calm", "lift", "clash", "friction"):
                    body = ds.enrich_story(dict(self.BASE), god, rel, seed)["body"]
                    n = len(split_sentences(body))
                    self.assertTrue(G["overall"]["sentences"][0] <= n <= G["overall"]["sentences"][1] + 2, body)

    def test_deterministic_and_rotating(self):
        a = ds.enrich_story(dict(self.BASE), "hurting_officer", "calm", 4242)
        b = ds.enrich_story(dict(self.BASE), "hurting_officer", "calm", 4242)
        self.assertEqual(a, b)
        bodies = {ds.enrich_story(dict(self.BASE), "hurting_officer", "calm", s)["body"] for s in range(0, 2000, 7)}
        self.assertEqual(len(bodies), 3)


if __name__ == "__main__":
    unittest.main()
