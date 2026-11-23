"""2026-11-22 문장 규칙 v2 — 테마운 다섯 개: 맨 위 해시태그 셋, '~기 쉬운' 되풀이 없음."""
import datetime
import inspect
import random
import re
import unittest

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services.career import build_lifetime_career_report
from app.engine.services.health import build_lifetime_health_report
from app.engine.services.love import build_lifetime_love_report
from app.engine.services.study import build_lifetime_study_report
from app.engine.services.wealth import build_lifetime_wealth_report

BUILDERS = {"love": build_lifetime_love_report, "career": build_lifetime_career_report, "health": build_lifetime_health_report,
            "wealth": build_lifetime_wealth_report, "study": build_lifetime_study_report}


def _build(key, core):
    fn = BUILDERS[key]
    kwargs = {"is_unlocked": True} if "is_unlocked" in inspect.signature(fn).parameters else {}
    return fn(core, "가", **kwargs)["content"]


class ThemeVoiceV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        random.seed(22)
        cls.cores = [calculate_myeongri_core(
            BirthInput(name="x", gender=random.choice(["male", "female"]),
                       birth_date=datetime.date(random.randint(1962, 2004), random.randint(1, 12), random.randint(1, 28)),
                       birth_time=datetime.time(random.randint(0, 23), 30)),
            target_date=datetime.date(2026, 11, 22)) for _ in range(12)]

    def test_every_theme_opens_with_three_hashtags(self):
        for key in BUILDERS:
            for core in self.cores:
                html = _build(key, core)
                m = re.match(r'<div class="theme-reading"[^>]*><p class="theme-tags">([^<]+)</p>', html)
                self.assertIsNotNone(m, key)
                tags = m.group(1).split()
                self.assertEqual(len(tags), 3, (key, tags))
                self.assertTrue(all(re.fullmatch(r"#[0-9A-Za-z가-힣]+", t) for t in tags), (key, tags))

    def test_easy_to_hedge_appears_at_most_twice(self):
        for key in BUILDERS:
            for core in self.cores:
                body = re.sub(r"<[^>]+>", " ", _build(key, core).split("<details")[0])
                self.assertLessEqual(len(re.findall("기 쉽|기 쉬", body)), 2, key)


if __name__ == "__main__":
    unittest.main()


class CommonSentenceConditionTests(unittest.TestCase):
    """2026-11-23: 너무 많은 사람에게 똑같이 나오던 문장의 조건을 좁혔다(바넘 효과 방지)."""

    def test_career_strength_sentence_needs_a_decided_strength(self):
        from app.engine.services import career_copy
        self.assertFalse(career_copy.strength_decided(None))
        self.assertTrue(career_copy.strength_decided("weak"))
        undecided = career_copy.compose_tier1("output", "career", None)
        decided = career_copy.compose_tier1("output", "career", "strong")
        self.assertNotIn("기운이 고른 편이라", undecided["body"])
        self.assertEqual(decided["sentence_count"], undecided["sentence_count"] + 1)

    def test_intent_word_is_not_flagged_as_medical(self):
        from app.engine.services.health_copy import find_medical
        self.assertEqual(find_medical("원치 않는 부탁에는 짧고 분명하게 의사를 전하세요."), [])
        self.assertEqual(find_medical("내 의사를 분명히 밝히세요."), [])
        self.assertTrue(find_medical("의사를 찾아가세요."))
        self.assertTrue(find_medical("의사에게 물어보세요."))
