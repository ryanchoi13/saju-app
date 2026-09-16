"""Run real selection/placement code with explicit, reproducible QA inputs."""
from datetime import datetime
from pathlib import Path
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from fashion_v2.svg_recommendation import build_svg_catalog_contexts, PALETTE, VERSION
from fashion_v2.weather_outfit import classify_weather

CASES=[
 ('13','summer',20,'male','casual','yellow','purple',33,27,'보라 티·베이지 바지 / 흰 티·베이지 바지'),
 ('14','spring',30,'female','business_casual','lavender','red',25,16,'여성 하의 제한 · 아침저녁 겉옷 챙기기'),
 ('15','autumn',40,'male','business_formal','pink','charcoal',18,13,'추천 1 유지 · 추천 2 셔츠의 분홍 채도 조정'),
 ('16','winter',10,'female','casual','cobalt','pink',2,-4,'데님 바지 · 검정 패딩과 분홍 니트'),
 ('17','winter',50,'male','casual','red','sky',8,2,'추천 1 유지 · 네이비 코트와 빨간 목폴라'),
 ('18','autumn',50,'female','business_formal','forest','purple',13,8,'추천 1 유지 · 포멀 무릎 기장 · 노란 줄과 녹색 문자판 시계'),
]


def build():
    sets=[]
    reviews={r['id']:r for r in json.loads((ROOT/'docs/fashion-svg-review-feedback.json').read_text())}
    accepted={l['review_id']:l for l in json.loads((ROOT/'backend/tests/fixtures/svg_accepted_looks.json').read_text())}
    for id,season,age,gender,tpo,a,b,day,night,focus in CASES:
        profile=classify_weather([{'time':datetime(2026,9,16,h),'apparent_temperature':v} for h,v in [(8,night),(13,day),(20,night)]])
        result=build_svg_catalog_contexts(gender,season,PALETTE[a],PALETTE[b],profile,age)[tpo]
        for i,look in enumerate(result['looks'],1):
            look['review_id']=f'{id}-{i}'
            r=reviews[look['review_id']]
            look['review']={'revision':3,'previous_verdict':r['verdict'],'previous_note':r['note'],
                'verdict':'통과' if r['verdict']=='통과' else '수정 후 재검토','change_note':r['change_note']}
            if look['review_id'] in accepted:
                base_spec={k:v for k,v in look['garment_spec'].items() if k!='accessoryItems'}
                assert base_spec==accepted[look['review_id']]['garment_spec'], '통과한 착장 변경 감지'
        sets.append(dict(id=id,season=season,age=age,gender=gender,tpo=tpo,focus=focus,
                         raw={'A':PALETTE[a],'B':PALETTE[b]},weather=profile,**result))
    out=ROOT/'review-output/svg-integration';out.mkdir(parents=True,exist_ok=True)
    (out/'automatic-sets.json').write_text(json.dumps({'source':'weather/catalog + explicit review preferences + A/B placement','dailyColors':'fixed QA palette, not actual personal fortune','weather':'synthetic hourly forecast, not live weather','engineVersion':VERSION,'reviewRevision':3,'sets':sets},ensure_ascii=False,indent=2)+'\n')
    print('Generated 6 conditions / 12 outfits from selection and placement code')
    for s in sets:
        print(s['id'],s['focus'])
        for l in s['looks']:
            print(' ',l['review_id'],' / '.join(i['color_name']+' '+i.get('display_label',i['label']) for i in l['items']),l['color_strategy']['color_count'],'colors',len(l['color_strategy']['unresolved']),'palette only')

if __name__=='__main__':build()
