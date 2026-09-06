from unittest import TestCase

from app.engine.constants import GAN_WUXING
from app.engine.core.models import PillarFact
from app.engine.facts.hidden_stems import calculate_hidden_stems
from app.engine.facts.rooting import (
    EXPOSED_STEM_RULE_VERSION,
    ROOTING_RULE_VERSION,
    calculate_exposed_stems,
    calculate_roots,
)


def _pillar(stem: str, branch: str) -> PillarFact:
    return PillarFact(
        stem=stem,
        branch=branch,
        ganji=f"{stem}{branch}",
        stem_element=GAN_WUXING[stem],
        stem_yin_yang="yang" if stem in "甲丙戊庚壬" else "yin",
        branch_element="木",
        branch_yin_yang="yang",
    )


class RootingTests(TestCase):
    def setUp(self):
        self.pillars = {
            "year": _pillar("乙", "卯"),
            "month": _pillar("丙", "寅"),
            "day": _pillar("甲", "辰"),
            "hour": None,
        }
        self.hidden = calculate_hidden_stems(self.pillars)

    def test_same_element_is_a_root_even_when_polarity_differs(self):
        roots = calculate_roots(self.pillars, self.hidden)
        year_in_day = next(
            item
            for item in roots.items
            if item.stem_pillar == "year" and item.branch_pillar == "day"
        )
        self.assertEqual(year_in_day.visible_stem, "乙")
        self.assertEqual(year_in_day.hidden_stem, "乙")
        self.assertTrue(year_in_day.exact_stem)

        day_in_year = next(
            item
            for item in roots.items
            if item.stem_pillar == "day" and item.branch_pillar == "year"
        )
        self.assertEqual(day_in_year.hidden_stem, "乙")
        self.assertFalse(day_in_year.exact_stem)
        self.assertEqual(roots.rule_version, ROOTING_RULE_VERSION)

    def test_exposure_requires_the_identical_stem(self):
        exposed = calculate_exposed_stems(self.pillars, self.hidden)
        links = {(item.hidden_pillar, item.visible_pillar, item.stem) for item in exposed.items}
        self.assertIn(("year", "year", "乙"), links)
        self.assertIn(("month", "month", "丙"), links)
        self.assertIn(("month", "day", "甲"), links)
        self.assertNotIn(("year", "day", "乙"), links)
        self.assertEqual(exposed.rule_version, EXPOSED_STEM_RULE_VERSION)

    def test_roles_are_preserved_without_strength_scores(self):
        exposed = calculate_exposed_stems(self.pillars, self.hidden)
        month_fire = next(
            item for item in exposed.items if item.hidden_pillar == "month" and item.stem == "丙"
        )
        self.assertEqual(month_fire.hidden_role.value, "middle")
        self.assertFalse(hasattr(month_fire, "strength"))

    def test_unknown_hour_is_not_fabricated(self):
        roots = calculate_roots(self.pillars, self.hidden)
        exposed = calculate_exposed_stems(self.pillars, self.hidden)
        self.assertNotIn("hour", {item.stem_pillar for item in roots.items})
        self.assertNotIn("hour", {item.branch_pillar for item in roots.items})
        self.assertNotIn("hour", {item.visible_pillar for item in exposed.items})
        self.assertNotIn("hour", {item.hidden_pillar for item in exposed.items})

    def test_invalid_visible_stem_is_rejected(self):
        invalid = {"day": self.pillars["day"].model_copy(update={"stem": "X"})}
        with self.assertRaisesRegex(ValueError, "지원하지 않는 천간"):
            calculate_roots(invalid, {})
