"""Regression checks for the jointly reviewed grades and full food pool."""
import unittest
from datetime import date
from app.engine.services.daily_menu import MENU_POOL
from app.engine.services.menu_frequency_review import REVIEWED_POPULARITY
from app.engine.services.simple_menu import eligible_menus, select_menus, VERSION

class FrequencyReviewTests(unittest.TestCase):
    def test_final_feedback_overrides_initial_proposals(self):
        lookup = {m.name:m for m in MENU_POOL}
        expected = {'후라이드치킨':5,'감자탕':4,'된장국':3,
                    '오징어볶음':3,'주꾸미볶음':3,'소고기 샤브샤브':3,
                    '돼지고기수육':2,'고구마피자':2,'팥죽':1,'전복솥밥':1,
                    '꼬막비빔밥':1,'오리훈제샐러드':2,'떡볶이':5}
        for name,value in expected.items():self.assertEqual(lookup[name].popularity,value,name)
        self.assertNotIn('콜슬로 샌드위치',REVIEWED_POPULARITY)
        self.assertNotIn('우엉잡채',REVIEWED_POPULARITY)
        self.assertEqual('콜슬로 샌드위치' in lookup,False)
        self.assertEqual(lookup['우엉잡채'].popularity,2)
        self.assertEqual(len(MENU_POOL),294)

    def test_all_general_foods_are_candidates_and_daily_repetition_still_works(self):
        candidates=eligible_menus()
        names={m.name for m in candidates}
        self.assertEqual(names,{m.name for m in MENU_POOL})
        self.assertEqual(len(names),294)
        self.assertTrue({'떡볶이','햄치즈 토스트','흰콩두유','소금빵',
                         '양송이스프','간장계란밥','탄두리치킨','생선회'} <= names)
        lookup={m.name:m for m in candidates}
        seed='full-food-pool-check'
        first=select_menus(day=date(2026,9,9),seed=seed,weights={})
        self.assertEqual(first,select_menus(day=date(2026,9,9),seed=seed,weights={}))
        history=[tuple(lookup[name] for name in first)]
        second=select_menus(day=date(2026,9,10),seed=seed,weights={},history=history)
        self.assertEqual(len(set(first)),2)
        self.assertEqual(len(set(second)),2)
        self.assertTrue(set(first).isdisjoint(second))
        self.assertEqual(VERSION,'simple-menu-v5-lunch-dinner')

    def test_lunch_then_dinner_respect_periods_and_never_repeat_yesterday(self):
        from app.engine.services.simple_menu import DINNER_CHICKEN
        from app.engine.services.menu_categories import menu_category
        from datetime import timedelta
        lookup = {m.name:m for m in MENU_POOL}
        for person in range(12):
            history = []
            for offset in range(31):
                day = date(2026,9,1) + timedelta(days=offset)
                names = select_menus(day=day,seed=f'{person}|{day}',weights={},history=history[-7:])
                lunch,dinner = [lookup[n] for n in names]
                self.assertIn('lunch',lunch.periods)
                self.assertNotIn(lunch.name,DINNER_CHICKEN)
                self.assertIn('dinner',dinner.periods)
                self.assertNotEqual(menu_category(lunch.name),menu_category(dinner.name))
                if history: self.assertTrue(set(names).isdisjoint(m.name for m in history[-1]))
                history.append((lunch,dinner))

    def test_comment_follows_lunch_and_dinner_with_correct_particles(self):
        from app.engine.services.simple_menu import meal_comment
        self.assertEqual(meal_comment(['김치찌개','후라이드치킨']),
                         '오늘 점심에는 칼칼한 김치찌개를, 저녁에는 바삭한 후라이드치킨을 즐겨 보세요.')
