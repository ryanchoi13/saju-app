from unittest import TestCase

from fashion_v2.template_catalog import (
    PRACTICAL_MALE_BOTTOM_COLORS,
    TEMPLATES,
    templates_for,
    validate_catalog,
)


class FashionV2CatalogTests(TestCase):
    def test_catalog_has_24_scopes_and_48_complete_looks(self):
        self.assertTrue(validate_catalog())
        self.assertEqual(len(TEMPLATES), 48)
        self.assertEqual(len({(t['gender'],t['season'],t['tpo']) for t in TEMPLATES}), 24)

    def test_every_scope_has_distinct_daily_and_trend(self):
        for gender in ('male','female'):
            for season in ('spring','summer','autumn','winter'):
                for tpo in ('casual','business_casual','business_formal'):
                    pair = templates_for(gender,season,tpo)
                    self.assertEqual({t['look_role'] for t in pair}, {'daily','trend'})
                    self.assertNotEqual(pair[0]['items'], pair[1]['items'])
                    self.assertTrue(all(t['selection_mode']=='whole_template_only' for t in pair))

    def test_workwear_and_formal_rules(self):
        for template in TEMPLATES:
            labels = {i['label'] for i in template['items']}
            if template['tpo'] != 'casual':
                self.assertFalse(labels & {'버뮤다 반바지','스트랩 샌들'})
            if template['gender']=='male':
                bottom = next(i for i in template['items'] if i['category']=='bottom')
                self.assertIn(bottom['color'], PRACTICAL_MALE_BOTTOM_COLORS)
            if template['gender']=='male' and template['tpo']=='business_formal':
                shoes = next(i for i in template['items'] if i['category']=='shoes')
                self.assertIn(shoes['label'], {'옥스퍼드 구두','더비 구두'})
                suit = [i for i in template['items'] if i.get('suit_group')]
                self.assertEqual(len(suit), 2)
                self.assertEqual(
                    len({(i['suit_group'],i['color'],i['material']) for i in suit}),
                    1,
                )

    def test_womens_catalog_includes_pants_skirts_and_dresses(self):
        forms = {t['form'] for t in TEMPLATES if t['gender']=='female'}
        self.assertEqual(forms, {'pants', 'skirt', 'dress'})

    def test_winter_skirt_and_dress_looks_include_a_leg_layer(self):
        for template in TEMPLATES:
            if template['gender']=='female' and template['season']=='winter' and template['form'] in {'skirt','dress'}:
                self.assertIn('leg_layer', {i['category'] for i in template['items']})

    def test_age_is_metadata_not_an_exclusion(self):
        for template in TEMPLATES:
            self.assertEqual(template['age_policy'], 'soft_preference_no_exclusion')
            self.assertNotIn('min_age', template)
            self.assertNotIn('max_age', template)

    def test_catalog_stays_review_only(self):
        self.assertTrue(all(t['status']=='owner_review_pending' for t in TEMPLATES))

    def test_accessories_are_not_forced_into_complete_looks(self):
        self.assertTrue(all(
            item['category'] != 'accessory'
            for template in TEMPLATES
            for item in template['items']
        ))
