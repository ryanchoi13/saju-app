from unittest import TestCase
from app.engine.services.daily import _menu_timing_element_weights, _menu_climate_tags
from app.engine.services.daily_menu import MENU_POOL, DIET_MENU_POOL
from app.engine.services.menu_frequency import frequency_evidence, frequency_bonus
from app.engine.services.meal_nutrition import meal_estimate


class MenuCalculationTests(TestCase):
    def test_abundance_does_not_mean_dietary_need(self):
        timing = {axis:{"pillar":{"stem_element":"火", "branch_element":"火"}}
                  for axis in ("luck_cycle","annual","monthly","daily")}
        result = _menu_timing_element_weights(timing, {"favorable_elements":["水"],"caution_elements":["火"],"confidence":"low"})
        self.assertGreater(result["水"], 0)
        self.assertLess(result["火"], 0)
        self.assertLessEqual(abs(result["火"]), 4)
        self.assertEqual(_menu_timing_element_weights(timing, {}), {})

    def test_each_timing_layer_can_modify_assessed_direction(self):
        semantic = {"favorable_elements":["水"],"confidence":"high"}
        base = _menu_timing_element_weights({},semantic)["水"]
        for axis in ("luck_cycle","annual","monthly","daily"):
            timing = {axis:{"pillar":{"stem_element":"水","branch_element":"水"}}}
            # Weak slow layers accumulate before increasing the score.
            result = _menu_timing_element_weights(timing,semantic)["水"]
            self.assertGreaterEqual(result,base)
        self.assertGreater(_menu_timing_element_weights({"daily":{"pillar":{"stem_element":"水","branch_element":"水"}}},semantic)["水"],base)

    def test_conflicting_core_direction_is_not_invented_resolution(self):
        self.assertEqual(_menu_timing_element_weights({}, {"favorable_elements":["火"],"caution_elements":["火"]})["火"],0)
        self.assertEqual(_menu_climate_tags({"diagnostics":{"climate":{"recommended_operations":[{"operation":"warming"}]}}}),frozenset({"warm"}))

    def test_rice_is_counted_once_in_composed_meal(self):
        estimate = meal_estimate("된장찌개", 500, True, True, False)
        self.assertEqual([c["name"] for c in estimate["components"]].count("밥"),1)
        self.assertFalse(estimate["verified_recipe"])
        self.assertEqual(estimate["source_kind"],"editorial_estimate")
        self.assertAlmostEqual(estimate["estimated_kcal"],4*(estimate["carbohydrate_g"]+estimate["protein_g"])+9*estimate["fat_g"],places=1)

    def test_egg_accompaniment_changes_nutrients(self):
        menu = next(c for c in MENU_POOL if c.name == "딸기잼 토스트")
        self.assertIn("삶은 달걀",[c["name"] for c in menu.nutrition_estimate["components"]])
        self.assertGreaterEqual(menu.nutrition_estimate["protein_g"], 20)
        self.assertTrue(menu.has_protein)

    def test_survey_does_not_transfer_to_rare_variants(self):
        self.assertGreater(frequency_bonus("후라이드치킨"),0)
        self.assertEqual(frequency_bonus("탄두리치킨"),0)
        self.assertIsNone(frequency_evidence("꼬막비빔밥")["observed_percent"])

    def test_every_candidate_has_consistent_internal_nutrition(self):
        for menu in (*MENU_POOL,*DIET_MENU_POOL):
            with self.subTest(menu=menu.name):
                e = menu.nutrition_estimate
                self.assertIsNotNone(e)
                self.assertAlmostEqual(menu.estimated_kcal,e["estimated_kcal"],delta=.51)
                self.assertEqual(menu.has_protein,e["protein_g"]>=15)
                for key in ("carbohydrate_g","protein_g","fat_g"):
                    self.assertAlmostEqual(sum(c[key] for c in e["components"]),e[key],delta=.05)

    def test_familiar_meals_are_available_at_appropriate_times(self):
        menus = {c.name:c for c in MENU_POOL}
        for name in ("닭죽", "소고기죽", "야채죽", "양송이스프", "감자수프", "야채수프"):
            self.assertIn("breakfast", menus[name].periods)
        for name in ("콩나물국", "김치국", "된장국", "시래기국", "동태국", "김치볶음밥", "새우볶음밥", "계란볶음밥", "해물볶음밥", "햄볶음밥"):
            self.assertIn("lunch", menus[name].periods)
        self.assertNotIn("밥과 계란프라이", menus)
        self.assertIn("간장계란밥", menus)

    def test_diet_breakfast_and_exclusions(self):
        from app.engine.services.daily_menu import DIET_DEFAULT_EXCLUSIONS, _macro_penalty
        from app.engine.services.menu_categories import menu_category
        self.assertIn("채소 듬뿍 아귀찜", DIET_DEFAULT_EXCLUSIONS)
        menus = {c.name:c for c in DIET_MENU_POOL}
        for name in ("블루베리 두유 견과 스무디", "케일 바나나 사과 요거트 스무디", "땅콩버터 통밀토스트"):
            self.assertIn("breakfast",menus[name].periods)
            self.assertEqual(_macro_penalty(menus[name],(0,0,0)),0)
        self.assertEqual(menu_category("양송이스프"),"western_soup")
        self.assertEqual(menu_category("케일 바나나 두유 스무디"),"smoothie")
