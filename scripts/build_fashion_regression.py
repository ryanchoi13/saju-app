"""Export deterministic regression payloads from the real recommendation code."""
from datetime import datetime
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from fashion_v2.svg_recommendation import build_svg_catalog_contexts, PALETTE
from fashion_v2.weather_outfit import classify_weather


def export():
    all_looks = []
    pairs = [({'hex':'#099197','name_ko':'딥 청록'}, {'hex':'#C5A56E','name_ko':'카멜'}),
             (PALETTE['pink'], PALETTE['charcoal']), (PALETTE['red'], PALETTE['sky'])]
    for gender in ('male', 'female'):
        for season, day, night in [('spring',18,12),('summer',33,27),('autumn',18,13),('winter',2,-4)]:
            weather = classify_weather([{'time':datetime(2026,9,18,h),'apparent_temperature':v}
                                        for h,v in [(8,night),(13,day),(20,night)]])
            for a,b in pairs:
                contexts = build_svg_catalog_contexts(gender,season,a,b,weather,48)
                all_looks.extend(l for ctx in contexts.values() for l in ctx['looks'])
    out = ROOT/'review-output/wearable-fix'
    out.mkdir(parents=True,exist_ok=True)
    (out/'regression.json').write_text(json.dumps(all_looks,ensure_ascii=False,indent=2))
    a,b=pairs[0]
    (out/'looks.json').write_text(json.dumps(build_svg_catalog_contexts('male','autumn',a,b,age=48),ensure_ascii=False,indent=2))
    print(f'{len(all_looks)} deterministic renderer payloads exported')


if __name__ == '__main__':
    export()
