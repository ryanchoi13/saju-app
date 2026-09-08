import unittest
from app.engine.services.daily_menu import MENU_POOL
from app.engine.services.simple_menu import eligible_menus
from app.engine.services.menu_catalog_revision import RENAMES, MERGES, ADDITIONS
from app.engine.services.menu_categories import menu_category

class CatalogRevisionTests(unittest.TestCase):
    def test_all_edits_and_merges_have_unique_targets(self):
        lookup={m.name:m for m in MENU_POOL}
        self.assertEqual(len(MENU_POOL),294)
        self.assertEqual(len(lookup),294)
        self.assertEqual(set(lookup),{m.name for m in eligible_menus()})
        self.assertTrue(set(RENAMES).isdisjoint(lookup))
        self.assertTrue(set(MERGES).isdisjoint(lookup))
        for name,grade,_,ingredient,cuisine in ADDITIONS:
            self.assertEqual(lookup[name].popularity,grade,name)
            self.assertEqual(lookup[name].ingredient,ingredient,name)
            self.assertEqual(lookup[name].cuisine,cuisine,name)
        expected={'밤밥':1,'치킨카레':2,'된장국':3,'콩나물국':4,'만둣국':3,
                  '홍합탕':2,'김국':1,'콩비지찌개':3,'매운 소고기 쌀국수':2,
                  '해물볶음우동':2,'생선가스':2,'주꾸미볶음':3,'삼계탕':4,
                  '햄버거':4,'오븐구이 치킨':2,'아보카도 샌드위치':2}
        for n,v in expected.items():self.assertEqual(lookup[n].popularity,v,n)
        self.assertEqual(lookup['홍차와 에그타르트'].ingredient,'egg_dairy')

    def test_renames_and_new_foods_keep_correct_selection_categories(self):
        expected={'참치회':'raw_fish','생선회':'raw_fish','오야코동':'rice_bowl',
                  '치킨가스':'cutlet','오븐구이 치킨':'chicken','우육면':'chinese_noodles',
                  '아보카도 샌드위치':'sandwich','닭가슴살 포케':'poke',
                  '소고기 포케':'poke','블루베리 검은콩 스무디':'smoothie'}
        for n,c in expected.items():self.assertEqual(menu_category(n),c,n)
