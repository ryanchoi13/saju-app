"""Reproducible review inputs; no real user fortune/weather, no deployment."""
from pathlib import Path
from copy import deepcopy
from datetime import datetime
import json, sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from fashion_v2.svg_recommendation import build_svg_catalog_contexts, PALETTE, to_spec
from fashion_v2.realwear_rules import colour_parts, visible_colors
from fashion_v2.weather_outfit import classify_weather
from scripts.build_svg_review import CASES

OUT=ROOT/'review-output/realwear-v3'
OUT.mkdir(parents=True,exist_ok=True)
samples=[]
for title,g,season,tpo,n in [
    ('여성 가을 · 지정된 앵클부츠 유지','female','autumn','casual',1),
    ('여성 봄 · 지정된 플랫슈즈 유지','female','spring','casual',1),
    ('남성 봄 포멀 · 두 색 넥타이','male','spring','business_formal',0),
    ('남성 겨울 · 착장에 지정된 부츠','male','winter','casual',1),
]:
    l=build_svg_catalog_contexts(g,season,PALETTE['sky'],PALETTE['navy'],age=35)[tpo]['looks'][n]
    samples.append(dict(title=title,kind='actual_recommendation_code',look=l))
l=build_svg_catalog_contexts('female','autumn',PALETTE['forest'],PALETTE['purple'],age=55)['business_formal']['looks'][1]
samples.append(dict(title='여성 시계 · 승인한 노랑 줄·테두리와 녹색 문자판',kind='actual_recommendation_code',look=l))
demo=deepcopy(samples[1]['look']);demo.update(id='component-colour-demo',tpo='casual')
for i in demo['items']:
    colour='navy' if i['category'] in {'outer','bottom'} else 'ivory'
    i.update(hex=PALETTE[colour]['hex'],color_name=PALETTE[colour]['name'])
    for key in ['applied_daily_color','source_hex','source_color_name','color_relation','tone_reason']:i.pop(key,None)
def component(key,hex_value):return dict(hex=PALETTE[hex_value]['hex'],name=PALETTE[hex_value]['name'],source='review_demo_not_automatic_AB')
demo['items'] += [
 dict(key='demo-watch',category='accessory',label='시계',hex=PALETTE['forest']['hex'],color_name='포레스트',watch_variant='gender_basic_v1',parts_locked=True,color_parts={'dial':component('dial','forest'),'case':component('case','yellow'),'strap':component('strap','yellow')}),
 dict(key='demo-earrings',category='accessory',label='귀걸이',hex=PALETTE['navy']['hex'],color_name='네이비',parts_locked=True,color_parts={'metal':component('metal','yellow'),'stone':component('stone','navy')}),
 dict(key='demo-necklace',category='accessory',label='목걸이',hex=PALETTE['forest']['hex'],color_name='포레스트',parts_locked=True,color_parts={'chain':component('chain','yellow'),'pendant':component('pendant','forest')}),
]
colour_parts(demo['items'],PALETTE);demo['garment_spec']=to_spec(demo)
demo['color_strategy']={'color_count':len(visible_colors(demo['items'])),'review_required':True,'additional_element_C':None,'original':{},'placements':{},'unresolved':[]}
samples.append(dict(title='색 분리 기능 예시 · 시계·귀걸이·목걸이',kind='manual_mechanism_demo_not_auto_recommendation',look=demo))
(OUT/'samples.json').write_text(json.dumps(samples,ensure_ascii=False,indent=2))

# Recheck older approved fixtures without overwriting old user review files.
regression=[]
for id,season,age,gender,tpo,a,b,day,night,_ in CASES:
    p=classify_weather([{'time':datetime(2026,9,16,h),'apparent_temperature':v} for h,v in [(8,night),(13,day),(20,night)]])
    for n,look in enumerate(build_svg_catalog_contexts(gender,season,PALETTE[a],PALETTE[b],p,age)[tpo]['looks'],1):
        look['review_id']=f'{id}-{n}';regression.append(look)
(OUT/'regression.json').write_text(json.dumps(regression,ensure_ascii=False,indent=2))
print(f'{len(samples)} demonstration looks and {len(regression)} regression looks generated')
