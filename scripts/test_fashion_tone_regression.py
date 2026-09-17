"""Regression for the teal/camel incident. No live forecasts or user profiles."""
from copy import deepcopy
from pathlib import Path
import json
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from fashion_v2.svg_recommendation import (build_svg_catalog_contexts, describe_color,
    candidates, select_template, tone, variants, stable, PALETTE)
from fashion_v2.template_catalog import templates_for
from fashion_v2.outfit_balance import balance_penalty, outfit_options

TEAL={'hex':'#099197','name_ko':'딥 청록'}
CAMEL={'hex':'#C5A56E','name_ko':'카멜'}

class FashionToneRegression(unittest.TestCase):
    def test_actual_camel_has_beige_tones_without_changing_input(self):
        original=deepcopy(CAMEL)
        color=describe_color(CAMEL)
        self.assertEqual(color['family'],'brown')
        self.assertIn(PALETTE['beige']['hex'],[c['hex'] for c,_,_ in variants(color)])
        self.assertEqual(CAMEL,original)

    def test_similar_tone_competes_when_exact_top_is_allowed(self):
        look=select_template(templates_for('male','autumn','casual')[0],48,1)
        options=candidates(look,describe_color(TEAL),'A')
        tops=[c for c in options if c and c['category']=='top']
        self.assertTrue(any(c['relation']=='exact' for c in tops))
        self.assertTrue(any(c['color']['hex']==PALETTE['teal']['hex'] for c in tops))

    def test_adjacent_green_is_explicit_not_unrelated_neutral(self):
        options=list(variants(describe_color(TEAL)))
        olive=next((c,rel) for c,rel,_ in options if c['hex']==PALETTE['olive']['hex'])
        self.assertEqual(olive[1],'adjacent')
        self.assertTrue(stable(olive[0]))
        self.assertFalse(stable(olive[0],denim=True))
        self.assertFalse(stable(olive[0],suit=True))

    def test_only_weather_equivalent_denim_alternative(self):
        look=select_template(templates_for('male','winter','casual')[1],48,2)
        original=deepcopy(look)
        options=list(outfit_options(look))
        self.assertEqual(look,original)
        self.assertEqual(len(options),2)
        old=next(i for i in look['items'] if i['category']=='bottom')
        new=next(i for i in options[1]['items'] if i['category']=='bottom')
        self.assertEqual((old['label'],new['label'],new['material']),('데님 바지','면바지','fleece_cotton'))
        self.assertEqual([i for i in look['items'] if i['category']!='bottom'],[i for i in options[1]['items'] if i['category']!='bottom'])

    def test_formal_and_reviewed_outfits_are_not_restructured(self):
        for tpo in ('casual','business_formal'):
            look=select_template(templates_for('male','autumn',tpo)[0],48,1)
            if tpo=='casual': look['review_preference']='owner-reviewed'
            self.assertEqual(len(list(outfit_options(look))),1)

    def test_teal_camel_not_forced_into_two_upper_layers(self):
        for gender in ('male','female'):
            for a,b in ((TEAL,CAMEL),(CAMEL,TEAL)):
                looks=build_svg_catalog_contexts(gender,'autumn',a,b,age=48)['casual']['looks']
                for look in looks:
                    self.assertEqual(look['selection_evaluation']['balance_penalty'],0)
                    self.assertIn(look['garment_spec']['bottom'],['면바지','미디 스커트'])
                    if gender=='male': self.assertEqual(look['garment_spec']['bottom'],'면바지')
                    self.assertEqual(look['garment_spec']['topColor'],PALETTE['white']['hex'])
                    self.assertTrue(any(i['category']=='bottom' and i.get('applied_daily_color') for i in look['items']))
                    self.assertEqual(set(look['color_strategy']['placements']),{'A','B'})
                    self.assertIsNone(look['color_strategy']['additional_element_C'])
                    self.assertEqual(look['color_strategy']['original']['A']['hex'],a['hex'])
                    self.assertEqual(look['color_strategy']['original']['B']['hex'],b['hex'])

    def test_muted_upper_pair_is_not_blanket_banned(self):
        items=[dict(category='outer',hex=PALETTE['forest']['hex']),dict(category='top',hex=PALETTE['camel']['hex'])]
        self.assertEqual(balance_penalty(items,describe_color),0)
        items[0]['hex']=TEAL['hex']
        self.assertGreater(balance_penalty(items,describe_color),0)

    def test_source_and_daily_inputs_unchanged(self):
        before=deepcopy((TEAL,CAMEL,PALETTE))
        x=build_svg_catalog_contexts('male','autumn',TEAL,CAMEL,age=48)
        self.assertEqual(before,(TEAL,CAMEL,PALETTE))
        self.assertNotEqual(x['casual']['looks'][0]['garment_spec'],x['casual']['looks'][1]['garment_spec'])


def write_review_fixture():
    out=ROOT/'fashion-review-artifacts';out.mkdir(exist_ok=True)
    result=build_svg_catalog_contexts('male','autumn',TEAL,CAMEL,age=48)
    payload={'source':'synthetic autumn QA, not live user fortune or weather','contexts':result}
    (out/'teal-camel.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':
    write_review_fixture()
    unittest.main(verbosity=2)
