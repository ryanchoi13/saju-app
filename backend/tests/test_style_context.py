from unittest import TestCase
from style_context import build_style_contexts
from wada_color_rules import WADA_DUOS

class StyleContextTests(TestCase):
    def test_all_duos_respect_formal_placement_and_original_colors(self):
        for gender in ('male','female'):
            for duo_no, duo in WADA_DUOS.items():
                casual={'top':duo['a'],'bottom':duo['b']}
                contexts=build_style_contexts(duo_no,gender,casual)
                self.assertEqual(set(contexts),{'casual','business_casual','business_formal'})
                for tpo in ('business_casual','business_formal'):
                    p=contexts[tpo]
                    self.assertEqual({p['top']['hex'],p['bottom']['hex']},{duo['a']['hex'],duo['b']['hex']})
                    slots=[p[k]['item_type'] for k in ('top','bottom') if p[k]['item_type']]
                    self.assertEqual(len(slots),len(set(slots)))
                    self.assertNotIn('pocket_square',slots)
                    if tpo=='business_formal' and gender=='male':
                        self.assertNotIn('bottom',slots)
                        self.assertNotIn('jacket',slots)
    def test_profile_response_provides_all_contexts(self):
        from main import get_saju_pillars_and_analysis
        result=get_saju_pillars_and_analysis('검증','male',1978,3,13,'solar',5)
        contexts=result['daily_fortune']['style_palettes']
        self.assertEqual(contexts['casual']['top'],result['daily_fortune']['wada_palette']['top'])
        self.assertEqual(contexts['business_formal']['tpo'],'business_formal')
