from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path
from unittest import TestCase

from fashion_v2.svg_recommendation import build_svg_catalog_contexts, PALETTE, describe_color, stable, permitted, tone
from fashion_v2.weather_outfit import classify_weather
from fashion_v2.wearable_options import wardrobe_tones
from fashion_v2.coordination import tie_separation, POLICY_VERSION
from wada_color_rules import WADA_DUOS

ROOT=Path(__file__).resolve().parents[2]


class SvgIntegrationTests(TestCase):
    def profile(self,day,night):
        return classify_weather([{'time':datetime(2026,9,16,h),'apparent_temperature':v} for h,v in [(8,night),(13,day),(20,night)]])

    def check_look(self,look):
        items=look['items'];s=look['garment_spec'];strategy=look['color_strategy']
        self.assertEqual(look['outfit_policy_version'],POLICY_VERSION)
        self.assertLessEqual(strategy['color_count'],5 if strategy.get('component_color_source')=='user_requested_not_element_C' else 4)
        self.assertEqual(strategy['additional_element_C'],None)
        self.assertEqual(sum(x['category']=='shoes' for x in items),1)
        for item in items:
            if item['category']=='bottom':
                self.assertTrue(permitted(describe_color({'hex':item['hex']}), {'category':'bottom','label':item['label']}, look),item)
            if item.get('applied_daily_color'):
                raw=strategy['original'][item['applied_daily_color']]
                self.assertEqual(item['source_hex'],raw['hex'])
                if item['color_relation']=='exact':self.assertEqual(item['hex'],raw['hex'])
                else:
                    self.assertTrue(item['tone_reason'])
                    self.assertIn(item['hex'], {tone(key)['hex'].upper() for key in wardrobe_tones(raw)}, 'Only explicit wardrobe-tone mappings are permitted')
        suit=[i for i in items if i.get('suit_group')]
        if suit:self.assertEqual(len({i['hex'] for i in suit}),1)
        if s['dress']:self.assertFalse(s['top'] or s['bottom'])
        if look['gender']=='male' and look['tpo']=='business_formal':
            self.assertIn(s['shoe'],['옥스퍼드','더비 구두'])
            tie=next(i for i in items if i['category']=='tie')
            self.assertTrue(tie_separation(items,describe_color)['ok'])
            self.assertEqual(s['accessories'].count('넥타이'),1)

    def test_all_actual_wada_pairs_both_genders_all_seasons(self):
        # Input pool used by the real app, not just the 24-color review subset.
        count=0
        for gender in ('male','female'):
            for season in ('spring','summer','autumn','winter'):
                for duo in WADA_DUOS.values():
                    contexts=build_svg_catalog_contexts(gender,season,duo['a'],duo['b'],age=50)
                    for ctx in contexts.values():
                        self.assertEqual(len(ctx['looks']),2)
                        for look in ctx['looks']:self.check_look(look);count+=1
        self.assertEqual(count,5760)

    def test_age_weather_constraints_and_carry(self):
        for age in (15,25,35,45,55):
            for gender in ('male','female'):
                for day,night in [(33,27),(25,16),(18,13),(8,2),(2,-4)]:
                    contexts=build_svg_catalog_contexts(gender,'autumn',PALETTE['red'],PALETTE['sky'],self.profile(day,night),age)
                    for ctx in contexts.values():
                        for look in ctx['looks']:
                            self.check_look(look)
                            if age==15 and gender=='female' and day<=8 and look['tpo']=='casual':
                                self.assertFalse(look['garment_spec']['dress'])
                                self.assertNotIn('스커트',look['garment_spec']['bottom'])
                            if day>=33 and look['tpo']=='casual':self.assertFalse(look['garment_spec']['outer'])
                            if day==25 and look['tpo']!='business_formal':self.assertEqual(look['garment_spec']['outerMode'],'carry')

    def test_no_palette_input_or_approved_art_mutation(self):
        a,b=deepcopy(PALETTE['pink']),deepcopy(PALETTE['charcoal']);before=deepcopy((a,b))
        build_svg_catalog_contexts('male','autumn',a,b,age=40)
        self.assertEqual((a,b),before)
        provenance=json.loads((ROOT/'docs/fashion-svg-art-provenance.json').read_text())
        for name,expected in provenance['files'].items():
            self.assertEqual(hashlib.sha256((ROOT/'assets/dalha-garments'/name).read_bytes()).hexdigest(),expected)

    def test_invalid_colors_rejected(self):
        with self.assertRaises(ValueError):build_svg_catalog_contexts('male','autumn',{'hex':'<script>'},PALETTE['white'])

    def test_approved_pink_charcoal_formal_order(self):
        looks=build_svg_catalog_contexts('male','autumn',PALETTE['pink'],PALETTE['charcoal'],age=40)['business_formal']['looks']
        first,second=[l['garment_spec'] for l in looks]
        self.assertEqual((first['outerColor'],first['topColor'],first['accessoryColor']),(PALETTE['charcoal']['hex'],PALETTE['white']['hex'],PALETTE['pink']['hex']))
        self.assertEqual((second['outerColor'],second['topColor'],second['accessoryColor']),(PALETTE['navy']['hex'],PALETTE['pale_pink']['hex'],PALETTE['charcoal']['hex']))

    def test_reviewed_five_looks_unchanged(self):
        from scripts.build_svg_review import CASES
        accepted={l['review_id']:l for l in json.loads((ROOT/'backend/tests/fixtures/svg_accepted_looks.json').read_text())}
        for id,season,age,gender,tpo,a,b,day,night,_ in CASES:
            looks=build_svg_catalog_contexts(gender,season,PALETTE[a],PALETTE[b],self.profile(day,night),age)[tpo]['looks']
            for n,look in enumerate(looks,1):
                if f'{id}-{n}' in accepted:
                    previous=accepted[f'{id}-{n}']
                    # New independent part metadata is an approved additive
                    # contract. Preserve the previously reviewed base choices.
                    spec={k:v for k,v in look['garment_spec'].items() if k!='accessoryItems'}
                    self.assertEqual(spec,previous['garment_spec'])
                    self.assertEqual([(i['label'],i['hex']) for i in look['items']],[(i['label'],i['hex']) for i in previous['items']])

    def test_review_requested_combinations_and_palette_explanations(self):
        def looks(gender,age,a,b,day,night):
            return build_svg_catalog_contexts(gender,'winter' if day<10 else 'summer',PALETTE[a],PALETTE[b],self.profile(day,night),age)['casual']['looks']
        summer=looks('male',25,'yellow','purple',33,27)
        for l in summer:
            self.assertEqual((l['garment_spec']['top'],l['garment_spec']['bottom'],l['garment_spec']['bottomColor']),('반팔 티셔츠','면바지',PALETTE['beige']['hex']))
        self.assertEqual(summer[0]['garment_spec']['topColor'],PALETTE['purple']['hex'])
        self.assertEqual(summer[1]['garment_spec']['topColor'],PALETTE['white']['hex'])
        self.assertEqual(len(summer[1]['color_strategy']['unresolved']),2)
        self.assertIn('실착',summer[1]['color_strategy']['unresolved'][0]['reason'])
        teen=looks('female',15,'cobalt','pink',2,-4)
        self.assertEqual(teen[0]['garment_spec']['bottom'],'데님 바지')
        s=teen[1]['garment_spec']
        self.assertEqual((s['outer'],s['outerColor'],s['topColor'],s['bottomColor']),('패딩',PALETTE['black']['hex'],PALETTE['pink']['hex'],PALETTE['denim']['hex']))
        s=looks('male',55,'red','sky',8,2)[1]['garment_spec']
        self.assertEqual((s['outerColor'],s['topColor'],s['bottomColor'],s['knitNeck']),(PALETTE['navy']['hex'],PALETTE['red']['hex'],PALETTE['beige']['hex'],'turtleneck'))
        self.assertNotEqual(s['bottom'],'반바지')

    def test_knee_variant_scope_and_green_watch(self):
        for age in (45,50,55,60):
            contexts=build_svg_catalog_contexts('female','autumn',PALETTE['forest'],PALETTE['purple'],self.profile(13,8),age)
            for tpo,ctx in contexts.items():
                for look in ctx['looks']:
                    s=look['garment_spec']
                    expected=50<=age<60 and tpo=='business_formal' and (s['dress'] or '스커트' in s['bottom'])
                    self.assertEqual(s.get('formalHem')=='knee',bool(expected))
                    if expected and s['dress']:
                        self.assertEqual(s['accessories'],['시계'])
                        self.assertEqual(s['accessoryColor'],PALETTE['forest']['hex'])
                        self.assertEqual(s['bagColor'],PALETTE['purple']['hex'])

    def test_actual_api_keeps_core_ab_and_applies_weather_to_svg(self):
        from main import get_saju_pillars_and_analysis
        daily=get_saju_pillars_and_analysis('연결검사','male',1990,5,15,'solar',5,weather_profile=self.profile(25,16))['daily_fortune']
        self.assertTrue(daily['weather_outfit']['template_applied'])
        for context in daily['fashion_v2'].values():
            self.assertEqual(context['status'],'svg_integration_review')
            for look in context['looks']:
                self.assertTrue(look['garment_spec'])
                for role,slot in [('A','top'),('B','bottom')]:
                    self.assertEqual(look['color_strategy']['original'][role]['hex'],daily['wada_palette'][slot]['hex'].upper())
