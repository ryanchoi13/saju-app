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
