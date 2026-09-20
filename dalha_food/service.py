"""Application-facing offline interface, no external API fallback."""
import json
from datetime import date,timedelta
from pathlib import Path
from .state import Birth,build_base,build_daily,food_target
from .selection import select_plan

def recommend(birth:Birth,start:str,days:int=1,mode:str='general',history=None,exclude_ids=None):
    if mode not in ('general','diet'):raise ValueError('mode must be general/diet')
    if isinstance(days,bool) or not isinstance(days,int) or not 1<=days<=366:raise ValueError('days must be1..366')
    first=date.fromisoformat(start);base=build_base(birth)
    periods=[build_daily(base,first+timedelta(days=i)) for i in range(days)]
    directions=[food_target(base,p) for p in periods]
    catalogue=json.loads(Path(__file__).with_name('catalogue.json').read_text(encoding='utf8'))
    menus=catalogue['menus']
    plans=select_plan(menus,directions,mode,birth=base['solar_birth'],sex=birth.sex,initial_history=history,exclude_ids=exclude_ids)
    return dict(source='dalha-local',api_calls=0,base=base,periods=periods,food_directions=directions,
                mode=mode,plans=plans,catalogue_version=catalogue['version'],weights=catalogue['weights'],
                deployment_status='local_integration_only')
