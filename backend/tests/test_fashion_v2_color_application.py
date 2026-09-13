from unittest import TestCase

from fashion_v2.color_application import apply_daily_colors, build_colored_catalog_contexts
from fashion_v2.template_catalog import TEMPLATES, templates_for
from wada_color_ko import get_wada_color_ko
from wada_color_rules import WADA_DUOS


def color(hex_value, name='Test Color'):
    return {**{'name': name, 'hex': hex_value}, **get_wada_color_ko(hex_value, name)}


class FashionV2ColorApplicationTests(TestCase):
    def test_b_can_take_the_large_formal_area_when_a_only_fits_small(self):
        look = templates_for('male', 'autumn', 'business_formal')[0]
        colored = apply_daily_colors(look, color('#f8ed43'), color('#051230'))
        strategy = colored['color_strategy']['placements']
        self.assertEqual(strategy['b']['slot'], 'suit')
        self.assertEqual(strategy['b']['area'], 'large')
        self.assertEqual(strategy['a']['slot'], 'tie')
        suit = [i for i in colored['items'] if i.get('suit_group')]
        self.assertEqual({i['applied_daily_color'] for i in suit}, {'B'})
        self.assertEqual(len({(i['hex'], i['material']) for i in suit}), 1)

    def test_a_and_b_can_both_use_large_areas_in_casual(self):
        look = templates_for('male', 'autumn', 'casual')[0]
        colored = apply_daily_colors(look, color('#f48067'), color('#051230'))
        placements = colored['color_strategy']['placements']
        self.assertEqual(placements['a']['area'], 'large')
        self.assertEqual(placements['b']['area'], 'large')

    def test_two_tie_only_colors_become_a_real_patterned_tie(self):
        look = templates_for('male', 'spring', 'business_formal')[0]
        colored = apply_daily_colors(look, color('#f8ed43'), color('#f15a30'))
        placements = colored['color_strategy']['placements']
        self.assertEqual(placements['a']['slot'], 'tie')
        self.assertTrue(placements['b']['pattern'])
        tie = next(i for i in colored['items'] if i['category'] == 'tie')
        self.assertEqual(tie['label'], '레지멘탈 타이')
        self.assertEqual(tie['pattern_color']['role'], 'B')

    def test_mens_bottoms_never_receive_red_or_purple(self):
        for tpo in ('casual', 'business_casual'):
            for look in templates_for('male', 'autumn', tpo):
                for accent in (color('#f48067'), color('#a36aa5')):
                    colored = apply_daily_colors(look, accent, color('#f8ed43'))
                    bottom = next(i for i in colored['items'] if i['category'] == 'bottom')
                    self.assertNotIn(bottom.get('applied_daily_color'), {'A', 'B'})

    def test_unplaced_color_waits_for_owned_wardrobe_then_palette(self):
        # Remove all garment candidates to exercise the abstention contract.
        template = {
            **templates_for('male', 'summer', 'casual')[0],
            'items': [{'category':'leg_layer', 'label':'이너', 'color':'black', 'material':'cotton'}],
        }
        colored = apply_daily_colors(template, color('#f8ed43'), color('#f15a30'))
        self.assertEqual(len(colored['color_strategy']['unresolved']), 2)
        self.assertTrue(all(x['next_step'] == 'wardrobe_then_palette'
                            for x in colored['color_strategy']['unresolved']))

    def test_all_duos_build_all_contexts_without_breaking_complete_looks(self):
        for gender in ('male', 'female'):
            for season in ('spring', 'summer', 'autumn', 'winter'):
                for duo in WADA_DUOS.values():
                    a = color(duo['a']['hex'], duo['a']['name'])
                    b = color(duo['b']['hex'], duo['b']['name'])
                    contexts = build_colored_catalog_contexts(gender, season, a, b)
                    self.assertEqual(set(contexts), {'casual', 'business_casual', 'business_formal'})
                    for tpo, context in contexts.items():
                        self.assertEqual(len(context['looks']), 2)
                        for look in context['looks']:
                            self.assertEqual(look['tpo'], tpo)
                            self.assertEqual(len([i for i in look['items'] if i['category']=='shoes']), 1)
                            if gender == 'male' and tpo == 'business_formal':
                                suit = [i for i in look['items'] if i.get('suit_group')]
                                self.assertEqual(len({(i['hex'], i['material']) for i in suit}), 1)

    def test_profile_response_exposes_v2_without_replacing_current_ui_payload(self):
        from main import get_saju_pillars_and_analysis

        result = get_saju_pillars_and_analysis('검증', 'male', 1978, 3, 13, 'solar', 5)
        daily = result['daily_fortune']
        self.assertIn('style_palettes', daily)
        self.assertEqual(set(daily['fashion_v2']), {'casual', 'business_casual', 'business_formal'})
        self.assertTrue(all(context['status'] == 'engine_ready_ui_pending'
                            for context in daily['fashion_v2'].values()))
