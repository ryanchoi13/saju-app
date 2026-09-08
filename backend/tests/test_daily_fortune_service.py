from datetime import date, time, timedelta
from unittest import TestCase

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services.daily import (
    DAILY_FORTUNE_VERSION,
    _independent_relation_counts,
    build_daily_fortune,
)


class DailyFortuneServiceTests(TestCase):
    def _core(self, target: date):
        return calculate_myeongri_core(
            BirthInput(
                name="테스트",
                gender="male",
                birth_date=date(1978, 3, 13),
                birth_time=time(10, 30),
            ),
            target_date=target,
        )

    def test_daily_fortune_reads_all_timing_layers_and_daily_ten_god(self):
        target = date(2026, 9, 8)
        result = build_daily_fortune(self._core(target), "테스트", target)

        self.assertEqual(result["engine_version"], DAILY_FORTUNE_VERSION)
        self.assertEqual(result["day_ganji"], "을유(乙酉)")
        self.assertEqual(result["day_ganji_han"], "乙酉")
        self.assertEqual(result["day_ten_god"], "겁재")
        self.assertEqual(
            result["evidence_summary"]["scope"],
            "natal+luck_cycle+annual+monthly+daily",
        )
        self.assertIn("을유(乙酉) 일진", result["advice"])

    def test_lucky_item_comes_from_core_operation_and_element(self):
        target = date(2026, 9, 8)
        result = build_daily_fortune(
            self._core(target),
            "테스트",
            target,
            current_hour=12,
        )

        self.assertEqual(result["lucky_element"], "火")
        self.assertEqual(result["lucky_item"], "붉은색 포인트 파우치")
        self.assertIn("중요한 것을 지키고 정리", result["lucky_item_reason"])
        self.assertIn("보조 근거", result["lucky_item_reason"])
        self.assertEqual(result["lucky_number"], "2, 7")
        self.assertEqual(result["lucky_direction"], "남쪽 (화 기운)")
        self.assertGreaterEqual(result["menu_pool_size"], 200)
        self.assertEqual(len(result["recommended_menus"]), 1)
        self.assertEqual(result["recommended_menu"], result["recommended_menus"][0])
        self.assertEqual(result["diet_meal_plan"]["mode"], "diet")
        self.assertEqual(len(result["diet_meal_plan"]["meals"]), 3)
        self.assertIn(result["diet_meal_plan"]["diet_meal_count"], {1, 2})
        self.assertEqual(result["general_meal_plan"]["mode"], "general")
        self.assertEqual(len(result["general_meal_plan"]["meals"]), 3)

    def test_fortune_changes_with_the_actual_daily_pillar(self):
        first_date = date(2026, 9, 7)
        second_date = date(2026, 9, 8)
        first = build_daily_fortune(self._core(first_date), "테스트", first_date)
        second = build_daily_fortune(self._core(second_date), "테스트", second_date)

        self.assertNotEqual(first["day_ganji"], second["day_ganji"])
        self.assertNotEqual(first["day_ten_god"], second["day_ten_god"])
        self.assertNotEqual(first["title"], second["title"])

    def test_same_members_are_not_double_counted_as_independent_evidence(self):
        members = [
            {"pillar": "day", "position": "visible_stem", "symbol": "甲"},
            {"pillar": "timing:daily", "position": "visible_stem", "symbol": "己"},
        ]
        supportive, tension = _independent_relation_counts([
            {"type": "stem_combination", "members": members},
            {"type": "stem_control", "members": members},
        ])

        self.assertEqual((supportive, tension), (0, 1))

    def test_all_ten_daily_stems_have_copy_and_practical_item(self):
        start = date(2026, 9, 7)
        results = []
        for offset in range(10):
            target = start + timedelta(days=offset)
            results.append(build_daily_fortune(self._core(target), "테스트", target))

        self.assertEqual(len({item["day_ten_god"] for item in results}), 10)
        self.assertGreaterEqual(len({item["lucky_item"] for item in results}), 4)
        self.assertTrue(all(62 <= item["score"] <= 91 for item in results))
        self.assertTrue(all(item["lucky_item_reason"] for item in results))
