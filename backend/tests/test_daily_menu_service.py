from collections import Counter
from dataclasses import replace
from datetime import date
from unittest import TestCase

from app.engine.services.daily_menu import (
    DIET_DEFAULT_EXCLUSIONS,
    DIET_BREAKFAST_EXCLUSIONS,
    DIET_MENU_POOL,
    MENU_POOL,
    food_family,
    serving_suggestion,
    _grouped_selection,
    recommend_daily_diet_plan,
    recommend_daily_general_plan,
    recommend_daily_menus,
    recommend_diet_menus,
)


class DailyMenuServiceTests(TestCase):
    def test_adding_equal_variants_does_not_increase_category_weight(self):
        from app.engine.services.menu_categories import menu_category
        pool = {m.name: m for m in MENU_POOL}
        toast, stew = pool["햄치즈 토스트"], pool["된장찌개"]
        variants = [replace(toast, name=f"햄치즈 토스트 변형 {i}") for i in range(20)]
        for day in range(30):
            seed = str(day)
            first = _grouped_selection([toast, stew], lambda m: 10, seed, 1, (), {})
            expanded = _grouped_selection([toast, stew, *variants], lambda m: 10, seed, 1, (), {})
            self.assertEqual(menu_category(first[0].name), menu_category(expanded[0].name))

    def test_meal_suggestions_do_not_add_bread_to_pasta_salad(self):
        self.assertNotIn("통밀빵", serving_suggestion("닭가슴살 샐러드 파스타"))

    def test_common_dishes_outrank_special_variants_in_consumer_metadata(self):
        pool = {m.name: m for m in MENU_POOL}
        self.assertNotIn("시나몬토스트", pool)
        for basic, special in (("후라이드치킨", "탄두리치킨"),
                               ("콩나물국밥", "굴국밥"),
                               ("야채비빔밥", "꼬막비빔밥")):
            self.assertGreater(pool[basic].popularity, pool[special].popularity)
            self.assertGreater(pool[basic].accessibility, pool[special].accessibility)
        self.assertEqual(pool["육회비빔밥"].ingredient, "beef")
        self.assertIn("햄치즈양배추 토스트", pool)

    def test_culinary_families_and_meal_accompaniments(self):
        self.assertEqual(food_family("동태탕"), food_family("황태해장국"))
        self.assertEqual(food_family("북엇국"), food_family("코다리조림"))
        self.assertEqual(food_family("고등어구이와 채소 반찬"),
                         food_family("고등어구이·채소 반찬"))
        self.assertIn("달걀", serving_suggestion("시나몬토스트"))
        self.assertIn("두부", serving_suggestion("배추전"))
        self.assertEqual(next(m for m in MENU_POOL if m.name == "고추장삼겹살").periods,
                         frozenset({"dinner"}))

    def test_fish_families_do_not_repeat_within_day(self):
        for offset in range(30):
            target = date.fromordinal(date(2026, 9, 8).toordinal() + offset)
            for recommend in (recommend_daily_general_plan, recommend_daily_diet_plan):
                result = recommend(target_date=target, day_master="甲",
                                   daily_ganji="乙酉", lucky_element="水",
                                   primary_operation="protect")
                families = [m["food_family"] for m in result["meals"] if m["food_family"]]
                self.assertEqual(len(families), len(set(families)))

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

    def test_pool_has_a_broad_unique_real_menu_selection(self):
        self.assertGreaterEqual(len(MENU_POOL), 200)
        self.assertEqual(len({item.name for item in MENU_POOL}), len(MENU_POOL))

    def test_pool_prefers_recognizable_korean_choices(self):
        names = {item.name for item in MENU_POOL}
        self.assertTrue({
            "라면", "짜장라면", "비빔국수", "후라이드치킨", "양념치킨",
            "간장치킨", "햄버거", "치킨버거", "감자탕", "돼지국밥",
            "오징어뭇국", "해물찜", "조개구이", "소고기불고기",
            "콩밥", "분짜", "알리오 올리오", "어향가지", "모둠초밥",
            "생선회", "오코노미야키", "양송이스프",
        }.issubset(names))
        self.assertNotIn("비빔면", names)
        self.assertTrue({
            "레몬 허브 치킨", "렌틸콩스튜", "배 리코타샐러드",
            "사워크라우트 소시지 플레이트", "소금라멘", "계란찜 정식",
            "배숙", "고구마토스트", "아라비아타 파스타",
        }.isdisjoint(names))

    def test_candidates_have_lifestyle_metadata(self):
        self.assertTrue(all(item.ingredient for item in MENU_POOL))
        self.assertTrue(all(item.cuisine for item in MENU_POOL))
        self.assertTrue(all(1 <= item.familiarity <= 4 for item in MENU_POOL))
        self.assertTrue(all(item.estimated_kcal > 0 for item in MENU_POOL))
        self.assertTrue(all(item.macro_profile for item in MENU_POOL))
        self.assertTrue(all(item.estimated_kcal > 0 for item in DIET_MENU_POOL))
        self.assertTrue(all(item.macro_profile for item in DIET_MENU_POOL))
        self.assertTrue(all(1 <= item.popularity <= 5 for item in MENU_POOL))
        self.assertTrue(all(1 <= item.accessibility <= 5 for item in MENU_POOL))
        self.assertTrue(all(item.age_groups for item in MENU_POOL))

    def test_history_prevents_consecutive_and_caps_ten_day_frequency(self):
        results = []
        history = []
        start = date(2026, 9, 8)
        for offset in range(10):
            target = date.fromordinal(start.toordinal() + offset)
            result = recommend_daily_general_plan(
                target_date=target, day_master="甲", daily_ganji="乙酉",
                lucky_element="水", primary_operation="protect",
                age_group="middle_adult",
                history=tuple(history),
            )
            history.append(result)
            results.append([meal["menu"] for meal in result["meals"]])

        counts = Counter(menu for day in results for menu in day)
        self.assertLessEqual(max(counts.values()), 2)
        for previous, current in zip(results, results[1:]):
            self.assertTrue(set(previous).isdisjoint(current))

    def test_pool_has_broad_coverage_without_forcing_equal_counts(self):
        element_counts = Counter(item.element for item in MENU_POOL)
        self.assertEqual(set(element_counts), set("木火土金水"))
        self.assertTrue(all(count >= 40 for count in element_counts.values()))

    def test_breakfast_and_snack_are_classified_separately(self):
        by_name = {item.name: item for item in MENU_POOL}
        self.assertEqual(by_name["닭꼬치"].periods, frozenset({"snack"}))
        self.assertEqual(by_name["떡볶이"].periods, frozenset({"snack"}))
        self.assertNotIn("snack", by_name["토마토 에그스크램블"].periods)
        self.assertNotIn("breakfast", by_name["햄버거"].periods)
        self.assertNotIn("breakfast", by_name["김밥"].periods)
        self.assertNotIn("breakfast", by_name["매생이국"].periods)
        self.assertNotIn("breakfast", by_name["굴국밥"].periods)
        self.assertEqual(by_name["문어숙회"].periods, frozenset({"dinner"}))

    def test_recent_menu_is_only_a_weak_tie_breaker(self):
        first = self._recommend(hour=12)
        repeated = recommend_daily_menus(
            target_date=date(2026, 9, 8),
            current_hour=12,
            day_master="甲",
            daily_ganji="乙酉",
            lucky_element="火",
            primary_operation="protect",
            count=2,
            recent_menus=frozenset(first["menus"]),
        )
        self.assertEqual(len(repeated["menus"]), 2)
        self.assertTrue(all(menu in {item.name for item in MENU_POOL} for menu in repeated["menus"]))

    def test_an_already_selected_meal_is_not_repeated_on_the_same_day(self):
        first = self._recommend(hour=12)["menus"][0]
        dinner = recommend_daily_menus(
            target_date=date(2026, 9, 8), current_hour=20,
            day_master="甲", daily_ganji="乙酉", lucky_element="火",
            primary_operation="protect", count=1,
            used_menus=frozenset({first}),
        )
        self.assertNotEqual(dinner["menus"][0], first)

    def test_recommendation_is_deterministic_and_diverse(self):
        first = self._recommend()
        second = self._recommend()

        self.assertEqual(first, second)
        selected = [item for item in MENU_POOL if item.name in first["menus"]]
        self.assertEqual(len(selected), 2)
        self.assertTrue(any(item.element in {"火", "木"} for item in selected))
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

    def test_diet_pool_is_separate_and_has_about_sixty_real_meals(self):
        self.assertGreaterEqual(len(DIET_MENU_POOL), 55)
        self.assertEqual(
            len({item.name for item in DIET_MENU_POOL}),
            len(DIET_MENU_POOL),
        )
        names = {item.name for item in DIET_MENU_POOL}
        self.assertTrue({
            "계란후라이와 통밀토스트", "간장계란밥",
            "토마토 에그스크램블·무가당 차", "연어 오차즈케",
            "달걀 오차즈케", "닭가슴살 포케", "두부버섯전골",
        }.issubset(names))
        self.assertTrue(DIET_DEFAULT_EXCLUSIONS.isdisjoint(names))
        self.assertTrue({
            "고추장삼겹살", "감자탕", "뼈해장국", "돼지국밥",
            "순대국밥", "부대찌개", "짜장면", "오므라이스",
        }.issubset(DIET_DEFAULT_EXCLUSIONS))

    def test_diet_recommendation_keeps_calories_internal(self):
        result = recommend_diet_menus(
            target_date=date(2026, 9, 8), current_hour=8,
            day_master="甲", daily_ganji="乙酉", lucky_element="水",
            primary_operation="protect",
        )
        self.assertEqual(result["calorie_status"], "estimated_internal")
        self.assertEqual(len(result["menus"]), 1)
        selected = next(item for item in DIET_MENU_POOL if item.name == result["menus"][0])
        self.assertIn("breakfast", selected.periods)

    def test_diet_plan_uses_one_or_two_diet_meals_and_excludes_flagged_foods(self):
        for offset in range(30):
            target = date(2026, 9, 8).fromordinal(date(2026, 9, 8).toordinal() + offset)
            result = recommend_daily_diet_plan(
                target_date=target,
                day_master="甲",
                daily_ganji="乙酉",
                lucky_element="水",
                primary_operation="protect",
            )
            menus = [meal["menu"] for meal in result["meals"]]
            self.assertIn(result["diet_meal_count"], {1, 2})
            self.assertEqual(len(menus), 3)
            self.assertEqual(len(set(menus)), 3)
            self.assertTrue(DIET_DEFAULT_EXCLUSIONS.isdisjoint(menus))
            self.assertNotIn(menus[0], DIET_BREAKFAST_EXCLUSIONS)
            self.assertEqual(result["calorie_status"], "estimated_internal")
            self.assertGreater(result["estimated_daily_kcal"], 0)
            self.assertGreaterEqual(result["nutrition_check"]["protein_meals"], 2)
            self.assertGreaterEqual(result["nutrition_check"]["vegetable_meals"], 1)
            self.assertLessEqual(result["nutrition_check"]["carb_heavy_meals"], 1)
            self.assertLessEqual(result["nutrition_check"]["fat_heavy_meals"], 1)

            ingredients = []
            for meal in result["meals"]:
                pool = DIET_MENU_POOL if meal["diet_menu"] else MENU_POOL
                ingredients.append(next(
                    item.ingredient for item in pool if item.name == meal["menu"]
                ))
            self.assertGreater(len(set(ingredients)), 1)

    def test_general_plan_returns_three_distinct_meal_periods(self):
        result = recommend_daily_general_plan(
            target_date=date(2026, 9, 20),
            day_master="甲",
            daily_ganji="丁酉",
            lucky_element="水",
            primary_operation="protect",
        )
        self.assertEqual(result["mode"], "general")
        self.assertEqual(
            [meal["period"] for meal in result["meals"]],
            ["breakfast", "lunch", "dinner"],
        )
        self.assertEqual(len({meal["menu"] for meal in result["meals"]}), 3)
        self.assertGreater(result["estimated_daily_kcal"], 0)
        self.assertGreaterEqual(result["nutrition_check"]["protein_meals"], 2)
        self.assertGreaterEqual(result["nutrition_check"]["vegetable_meals"], 1)
        self.assertLessEqual(result["nutrition_check"]["carb_heavy_meals"], 1)
        self.assertLessEqual(result["nutrition_check"]["fat_heavy_meals"], 1)
