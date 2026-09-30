"""Exhaustive structural inventory, with equivalent weather inputs deduplicated.
Colour scoring is unnecessary here: only review preferences can alter geometry.
"""
import sys,json,itertools
from pathlib import Path
from copy import deepcopy
from datetime import datetime
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fashion_v2.svg_recommendation import select_template,to_spec,tone,TPOS
from fashion_v2.template_catalog import templates_for
from fashion_v2.weather_catalog import weather_templates_for
from fashion_v2.weather_outfit import classify_weather
from fashion_v2.review_preferences import apply_review_preferences

def inventory():
    found={};count=0
    pairs=[('navy','pink'),('yellow','purple'),('cobalt','pink'),('red','sky'),('forest','purple')]
    profiles=[None]
    for temp,carry,rain,wind in itertools.product([31,27,23,20,17,13,7,0],[False,True],[False,True],[False,True]):
        low=min(temp-8,19) if carry else temp
        profiles.append(classify_weather([dict(time=datetime(2026,9,30,h),apparent_temperature=t,precipitation_probability=80 if rain else 0,wind_speed_10m=25 if wind else 0) for h,t in [(8,low),(13,temp),(20,low)]]))
    for gender,season,age,profile in itertools.product(['male','female'],['spring','summer','autumn','winter'],[18,25,35,45,55],profiles):
        for tpo in TPOS:
            templates=weather_templates_for(gender,tpo,profile,calendar_season=season) if profile else templates_for(gender,season,tpo)
            for number,original in enumerate(templates,1):
                selected=select_template(original,age,number,profile)
                for a,b in pairs:
                    look=apply_review_preferences(deepcopy(selected),tone(a),tone(b))
                    for item in look['items']:
                        c=tone(item['base_color']);item.update(hex=c['hex'],color_name=c['name'])
                    spec=to_spec(look)
                    shape={k:v for k,v in spec.items() if not k.endswith('Color') and k not in ['accessoryItems','suitLinked','trouserExtraLength','formalHem']}
                    if shape.get('overOuter'):shape['overOuter']={k:v for k,v in shape['overOuter'].items() if k!='color'}
                    key=json.dumps(shape,sort_keys=True,ensure_ascii=False)
                    found[key]=shape;count+=1
    return {'cases':count,'shapes':list(found.values())}
if __name__=='__main__':print(json.dumps(inventory(),ensure_ascii=False))
