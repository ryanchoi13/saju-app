"""'지금의 나' v4 — 문구 은행·원국 프로필·렌더 검사."""
import random
import re
import unittest
from datetime import date, time, timedelta

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services import now_me_copy as copy
from app.engine.services.annual_copy import split_sentences
from app.engine.services.lifetime import build_lifetime_overall_report, LIFETIME_NARRATIVE_VERSION
from app.engine.services.now_me import build_now_me, natal_profile, hour_confidence, select_rows

TARGET = date(2026, 10, 23)


def _core(birth: date, clock: time | None, gender="male"):
    return calculate_myeongri_core(
        BirthInput(name="테스트", gender=gender, birth_date=birth, birth_time=clock, time_unknown=clock is None),
        target_date=TARGET,
    )


def _plain(html: str) -> str:
    return re.sub(r"<[^>]*>", "", html)


class CopyBankTests(unittest.TestCase):
    def test_every_row_passes_validator(self):
        for row in copy.ALL_ROWS.values():
            allow = bool(row.get("allow_absolute"))
            for field in ("label", "trait", "flip", "tip"):
                text = row[field]
                self.assertEqual(copy.validate_paragraph(text, allow_absolute=allow), [], f"{row['key']}.{field}: {text}")
                self.assertLessEqual(len(text), copy.SENTENCE_MAX, f"{row['key']}.{field}")
            if "people" in row:
                self.assertEqual(copy.validate_paragraph(row["people"]), [], row["key"])
        for row in copy.DAY_MASTER_ROWS.values():
            self.assertEqual(copy.validate_paragraph(row["label"] + " " + row["trait"]), [], row["key"])

    def test_scene_bank_is_short_single_clause_and_clean(self):
        for key, pool in copy.SCENES.items():
            self.assertGreaterEqual(len(pool), 2, key)
            for s in pool:
                self.assertLessEqual(len(s), 40, f"{key}: {s}")
                self.assertEqual(len(split_sentences(s)), 1, f"{key}: {s}")
                self.assertEqual(copy.validate_paragraph(s), [], f"{key}: {s}")
        for text in (copy.PEOPLE_NEUTRAL, *copy.PLACE_LINES.values()):
            self.assertEqual(copy.validate_paragraph(text), [])

    def test_table_shape_matches_dictionary(self):
        self.assertEqual(len(copy.ELEMENT_ROWS), 15)
        self.assertNotIn("B8", copy.ALL_ROWS)
        self.assertEqual({r["key"] for r in copy.TEN_GOD_ROWS},
                         {"B1", "B2", "B3", "B4", "B5", "B6", "B7", "B9", "B10", "B11", "B16", "B17", "B18"})
        self.assertEqual(set(copy.CONTRAST_LABELS), {"B12", "B13", "B14", "B15"})
        self.assertEqual(len(copy.SHENSHA_ROWS), 3)
        self.assertEqual(len(copy.DAY_MASTER_ROWS), 10)

    def test_validator_layers(self):
        self.assertTrue(copy.validate_paragraph("이 일은 파국으로 갑니다."))
        self.assertTrue(copy.validate_paragraph("절대로 가장 빠릅니다."))          # 강조어 2회
        self.assertEqual(copy.validate_paragraph("가장 빠릅니다."), [])           # 강조어 1회는 허용
        self.assertTrue(copy.validate_paragraph("멈출 힘이 아예 없습니다."))
        self.assertEqual(copy.validate_paragraph("멈출 힘이 아예 없습니다.", allow_absolute=True), [])
        self.assertTrue(copy.validate_paragraph("성과를 냅니다."))               # HR 금기어


class ProfileTests(unittest.TestCase):
    def test_sample_chart_profile_is_consistent_with_pillars(self):
        core = _core(date(1978, 3, 13), time(11, 0))
        profile = natal_profile(core)
        pillars = core.natal_facts.pillars
        self.assertEqual(profile["day_master"], pillars["day"].stem)
        if profile["day_master"] == "甲":
            self.assertEqual(profile["yangin"]["branch"], "卯")
            self.assertEqual(profile["yangin"]["month"], pillars["month"].branch == "卯")
        visible = [f for f in core.natal_facts.ten_gods.visible if f.ten_god.value != "day_master"]
        mains = [f for f in core.natal_facts.ten_gods.hidden if f.hidden_role.value == "main"]
        self.assertEqual(sum(g["main"] for g in profile["groups"].values()), len(visible) + len(mains))
        self.assertEqual(sum(e["main"] for e in profile["elements"].values()), 8)
        officer_main = sum(1 for f in visible + mains if f.ten_god.value in ("direct_officer", "seven_killings"))
        self.assertEqual(profile["groups"]["관성"]["main"], officer_main)
        self.assertIn(profile["hour_confidence"], ("low", "high"))
        self.assertEqual(profile["pillars"]["day"], pillars["day"].ganji)
        if pillars["day"].ganji == "甲戌" and pillars["month"].ganji == "乙卯":
            self.assertTrue(profile["yangin"]["month"])
            self.assertEqual(profile["groups"]["관성"]["main"], 0)
            self.assertTrue(profile["officer_hidden_only"])
            self.assertTrue(profile["crowd_rob_wealth"])
            keys = [r["key"] for r in select_rows(profile)]
            self.assertEqual(keys[:2], ["B11", "B16"])  # 성격은 겁재·양인 먼저, 군겁쟁재는 그 뒷면

    def test_unknown_hour_profile(self):
        core = _core(date(1990, 5, 15), None)
        profile = natal_profile(core)
        self.assertEqual(profile["hour_confidence"], "unknown")
        self.assertEqual(profile["glyphs"], 6)
        self.assertNotIn("hour", profile["pillars"])
        self.assertNotIn("B17", [r["key"] for r in select_rows(profile)])

    def test_hour_confidence_boundary(self):
        near = _core(date(1990, 5, 15), time(13, 5))     # 평균태양시 보정 후 13시 경계 근처
        far = _core(date(1990, 5, 15), time(14, 0))
        self.assertIn(hour_confidence(near), ("low", "high"))
        self.assertEqual(hour_confidence(far), "high")


class RenderTests(unittest.TestCase):
    def _check_html(self, html: str):
        self.assertIn('class="now-me-lead"', html)
        for sid in ("core", "people", "place"):
            self.assertIn(f'data-now-me-section="{sid}"', html)
        self.assertGreaterEqual(html.count("now-me-evidence"), 4)
        self.assertIn('data-now-me-link="gunghap"', html)
        self.assertIn('data-now-me-link="business"', html)
        self.assertNotIn("data-paywall-cta", html)      # 화면이 '준비 중' 문구로 바꿔 버리는 속성
        plain = _plain(html)
        for word in copy.BANNED_PERSONALITY:
            self.assertNotIn(word, plain)
        for body in re.findall(r"<p>(.*?)</p>", html):
            text = _plain(body)
            self.assertLessEqual(sum(text.count(w) for w in copy.EMPHASIS_WORDS), 1, text)
            for s in split_sentences(text):
                self.assertLessEqual(len(s), copy.SENTENCE_MAX, s)

    def test_sample_chart_render(self):
        result = build_now_me(_core(date(1978, 3, 13), time(11, 0)), "테스트")
        self._check_html(result["html"])
        self.assertEqual(result["copy_version"], copy.COPY_VERSION)
        self.assertEqual([s["id"] for s in result["sections"]][:2], ["lead", "core"])
        self.assertEqual(len(result["sections"]), 5)
        self.assertIn("테스트님의 원국은", result["html"])
        self.assertNotIn("甲</strong>", result["html"])  # 일간 글자는 노출하지 않는다

    def test_random_births_render_without_error(self):
        rng = random.Random(20261023)
        base = date(1950, 1, 1)
        for _ in range(30):
            birth = base + timedelta(days=rng.randrange(0, 365 * 60))
            clock = None if rng.random() < 0.2 else time(rng.randrange(24), rng.randrange(60))
            gender = rng.choice(("male", "female"))
            result = build_now_me(_core(birth, clock, gender), "테스트")
            self._check_html(result["html"])

    def test_lifetime_report_wraps_now_me_in_nature_section(self):
        report = build_lifetime_overall_report(_core(date(1978, 3, 13), time(11, 0)), "테스트")
        self.assertEqual(LIFETIME_NARRATIVE_VERSION, "lifetime-present-v4")
        self.assertEqual(report["now_me_version"], "now-me-v1")
        self.assertIn('<section data-lifetime-section="nature"><h2>지금의 나</h2>', report["content"])
        self.assertIn('data-now-me-section="core"', report["content"])
        self.assertNotIn("나의 타고난 성향", report["content"])
        self.assertIn("now_me", report["evidence_summary"])
        self.assertIn("ordered_rows", report["evidence_summary"]["now_me"])


if __name__ == "__main__":
    unittest.main()
