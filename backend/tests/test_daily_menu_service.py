from collections import Counter
from datetime import date
from unittest import TestCase

from app.engine.services.daily_menu import MENU_POOL, recommend_daily_menus


class DailyMenuServiceTests(TestCase):
    def _recommend(self, *, hour: int = 12, element: str = "火") -> dict:
        return recommend_daily_menus(
            target_date=date(2026, 9, 8),
            current_hour=hour,
            day_master="甲",
            daily_ganji="乙酉",
            lucky_element=element,
            primary_operation="protect",
            count=2,
        )

    def test_pool_has_250_unique_real_menu_names(self):
        self.assertEqual(len(MENU_POOL), 250)
        self.assertEqual(len({item.name for item in MENU_POOL}), 250)

    def test_pool_prefers_recognizable_korean_choices(self):
        names = {item.name for item in MENU_POOL}
        self.assertTrue({
            "라면", "짜파게티", "비빔면", "후라이드치킨", "양념치킨",
            "간장치킨", "햄버거", "치킨버거", "감자탕", "돼지국밥",
            "오징어뭇국", "해물찜", "조개구이",
        }.issubset(names))
        self.assertTrue({
            "레몬 허브 치킨", "렌틸콩스튜", "배 리코타샐러드",
            "사워크라우트 소시지 플레이트",
        }.isdisjoint(names))

    def test_candidates_have_lifestyle_metadata(self):
        self.assertTrue(all(item.ingredient for item in MENU_POOL))
        self.assertTrue(all(item.cuisine for item in MENU_POOL))
        self.assertTrue(all(1 <= item.familiarity <= 4 for item in MENU_POOL))

    def test_pool_is_evenly_distributed_by_element_and_group(self):
        self.assertEqual(
            Counter(item.element for item in MENU_POOL),
            Counter({"木": 50, "火": 50, "土": 50, "金": 50, "水": 50}),
        )
        self.assertTrue(all(count == 10 for count in Counter(
            item.group for item in MENU_POOL
        ).values()))

    def test_recommendation_is_deterministic_and_diverse(self):
        first = self._recommend()
        second = self._recommend()

        self.assertEqual(first, second)
        selected = [item for item in MENU_POOL if item.name in first["menus"]]
        self.assertEqual(len(selected), 2)
        self.assertTrue(all(item.element == "火" for item in selected))
        self.assertTrue(all("lunch" in item.periods for item in selected))
        self.assertIn("ingredient_theme", first)
        self.assertIn("ingredient_theme_ko", first)
        self.assertTrue(any(
            item.ingredient == first["ingredient_theme"] for item in selected
        ))

    def test_time_context_changes_from_breakfast_to_dinner(self):
        breakfast = self._recommend(hour=7)
        dinner = self._recommend(hour=20)

        self.assertEqual(breakfast["meal_period"], "breakfast")
        self.assertEqual(dinner["meal_period"], "dinner")
        self.assertNotEqual(breakfast["menus"], dinner["menus"])
        breakfast_items = [item for item in MENU_POOL if item.name in breakfast["menus"]]
        dinner_items = [item for item in MENU_POOL if item.name in dinner["menus"]]
        self.assertTrue(all("breakfast" in item.periods for item in breakfast_items))
        self.assertTrue(all("dinner" in item.periods for item in dinner_items))

    def test_every_element_respects_each_meal_period(self):
        for element in "木火土金水":
            for hour, expected_period in ((7, "breakfast"), (12, "lunch"), (16, "snack"), (20, "dinner")):
                result = self._recommend(hour=hour, element=element)
                selected = [item for item in MENU_POOL if item.name in result["menus"]]
                self.assertTrue(
                    all(expected_period in item.periods for item in selected),
                    (element, hour, result),
                )
