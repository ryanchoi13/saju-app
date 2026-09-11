import json
from collections import Counter
from datetime import timedelta
from pathlib import Path
from unittest import TestCase

from app.engine.services.daily_menu import DIET_MENU_POOL, MENU_POOL
from app.engine.services.diet_catalog_revision import REVIEW, NEW_NAMES, diet_family
from app.engine.services.ranked_menu import build_rankings
from test_ranked_menu_explorer import BIRTH, DAY


class DietRevisionTests(TestCase):
    def test_reviewed_catalog_and_exact_images_cover_every_dish(self):
        self.assertEqual(len(DIET_MENU_POOL), 90)
        self.assertEqual(len(NEW_NAMES), 24)
        self.assertEqual(Counter(REVIEW[n]['family'] for n in NEW_NAMES),
                         {'salad': 6, 'poke': 2, 'grain_bowl': 2,
                          'sandwich': 6, 'wrap': 4, 'gimbap': 4})
        self.assertEqual({m.name for m in DIET_MENU_POOL}, set(REVIEW))
        self.assertGreater(len({m.element for m in DIET_MENU_POOL if '포케' in m.name}), 1)
        self.assertEqual(REVIEW['연어 오차즈케']['cuisine'], 'japanese')
        self.assertEqual(REVIEW['닭가슴살 샐러드 파스타']['cuisine'], 'western')
        self.assertTrue(all(m.cuisine == 'western' for m in DIET_MENU_POOL if '스무디' in m.name))
        root = Path(__file__).resolve().parents[2]
        manifest = json.loads((root/'assets/food-thumbnails-v1/manifest.json').read_text())
        names = [n for s in manifest['sheets'] for n in s['menus']]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(set(names), {m.name for m in (*MENU_POOL, *DIET_MENU_POOL)})
        from PIL import Image
        for s in manifest['sheets']:
            file = root/'assets/food-thumbnails-v1'/s['file']
            with Image.open(file) as image:
                self.assertEqual(image.size, (s['columns']*128, s['rows']*128))
            self.assertLessEqual(file.stat().st_size, 80*1024)
            self.assertEqual(len(s['menus']), len(s['crop_rects']))
            # Crops cannot overlap a neighboring menu's crop in either atlas size.
            for i, (x, y, w, h) in enumerate(s['crop_rects']):
                for xx, yy, ww, hh in s['crop_rects'][i+1:]:
                    self.assertFalse(x < xx+ww and xx < x+w and y < yy+hh and yy < y+h)

    def test_diet_diversity_never_reorders_element_scores(self):
        menus = {m.name: m for m in DIET_MENU_POOL}
        for offset in range(7):
            for element in '木火土金水':
                day = DAY + timedelta(days=offset)
                result = build_rankings(BIRTH, day, {element: 3}, element, 'medium')
                selected = result['rankings']['diet']
                self.assertEqual(len({m['menu'] for m in selected}), 10)
                self.assertTrue(all(m['element_score'] == 3 for m in selected))
                families = [diet_family(m['menu']) for m in selected]
                self.assertNotEqual(families[0], families[1])
                self.assertGreaterEqual(len(set(families)), 5)
                self.assertGreaterEqual(len({menus[m['menu']].cuisine for m in selected}), 2)
                self.assertEqual(result, build_rankings(BIRTH, day, {element: 3}, element, 'medium'))

    def test_general_ranking_stays_on_existing_order(self):
        # Recorded v1 general ranking: the diet change must not alter it.
        expected = ['된장찌개', '순대국밥', '뼈해장국', '감자탕', '햄버거',
                    '경양식 돈가스', '돼지국밥', '카레라이스', '간장계란밥', '일본식 돈카츠',
                    '콩비지찌개', '오므라이스', '프렌치토스트', '현미밥 정식',
                    '감자샐러드 샌드위치', '들깨수제비', '영양솥밥', '콩나물밥', '야채카레', '곤드레밥']
        result = build_rankings(BIRTH, DAY, {}, '土', 'low')
        self.assertEqual([m['menu'] for m in result['rankings']['general']], expected)
