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
        self.assertNotIn("일진", result["advice"])
        self.assertNotIn("겁재", result["advice"])
        self.assertIn("사람", result["advice"])

    def test_lucky_item_comes_from_confirmed_core_operation_and_element(self):
        target = date(2026, 9, 8)
        core = self._core(target)
        # Explicit renderer fixture: this is not a claim that this birth chart
        # has an established 火/protect judgment in the current research engine.
        core.synthesis = core.synthesis.model_copy(update={
            'favorable_operations': [{
                'operation': 'protect', 'elements': ['火'],
                'evidence_ids': ['fixture:confirmed-protection'],
            }],
        })
        core.semantic_state = core.semantic_state.model_copy(update={'favorable_elements': ['火']})
        result = build_daily_fortune(
            core,
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
        self.assertTrue(result['evidence_summary']['lucky_recommendation_basis']['recommendation_confirmed'])
        self.assertGreaterEqual(result["menu_pool_size"], 200)
        self.assertEqual(len(result["recommended_menus"]), 2)
        self.assertEqual([m['period'] for m in result['recommended_meals']], ['lunch','dinner'])
        self.assertEqual([m['menu'] for m in result['recommended_meals']], result['recommended_menus'])
        from app.engine.services.simple_menu import meal_comment
        self.assertEqual(result['recommended_menu_reason'], meal_comment(result['recommended_menus']))
        self.assertEqual(result["recommended_menu"], result["recommended_menus"][0])
        self.assertNotIn("diet_meal_plan", result)
        self.assertNotIn("general_meal_plan", result)
        self.assertEqual(result["menu_pool_version"], "simple-menu-v5-lunch-dinner")

    def test_unconfirmed_core_is_not_presented_as_balance_or_needed_element(self):
        target = date(2026, 9, 8)
        core = self._core(target)
        self.assertFalse(core.synthesis.favorable_operations)
        self.assertTrue(core.synthesis.pending_operations)
        result = build_daily_fortune(core, '테스트', target)
        self.assertEqual(result['evidence_summary']['primary_operation'], 'unconfirmed')
        basis = result['evidence_summary']['lucky_recommendation_basis']
        self.assertFalse(basis['recommendation_confirmed'])
        self.assertEqual(basis['element_source'], 'daily_symbolic_reference')
        self.assertNotIn('우선입니다', result['lucky_item_reason'])
        self.assertNotIn('보완 방향', result['talisman']['desc'])
        self.assertIn('참고 아이템', result['lucky_item_reason'])

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

    def test_short_guidance_is_connected_to_core_and_afternoon(self):
        from app.engine.semantic.queries import build_service_query
        from app.engine.services.daily_guidance import build_daily_guidance
        from app.engine.services.daily import _daily_relationships
        target = date(2026, 9, 9)
        core = self._core(target)
        query = build_service_query(core, 'daily_overall')
        expected = build_daily_guidance(query, query['timing']['daily']['ten_god'], _daily_relationships(query))
        result = build_daily_fortune(core, '테스트', target)
        # Legacy clients falling back to action must receive the same new
        # overall advice, not the previous work-focused operation template.
        self.assertEqual(result['mindset'], result['title'])
        self.assertEqual(result['action'], result['unified_advice'])
        self.assertNotEqual(result['time_flow']['afternoon'], result['unified_advice'])
        for key, value in expected['evidence'].items():
            self.assertEqual(result['evidence_summary']['guidance'][key], value)
        self.assertEqual(result['evidence_summary']['guidance']['rendered_by'],
                         result['evidence_summary']['overall']['version'])
