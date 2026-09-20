"""Bridge the existing app ProfileInput fields without a framework dependency."""
from collections.abc import Mapping
from datetime import date,time,datetime,timedelta,timezone
from .state import Birth
from .service import recommend

def recommend_for_profile(profile,as_of=None,days=1,mode='general',history=None,exclude_ids=None):
    def get(key,default=None):
        return profile.get(key,default) if isinstance(profile,Mapping) else getattr(profile,key,default)
    bd=get('birth_date')
    if isinstance(bd,str):bd=date.fromisoformat(bd)
    if not isinstance(bd,date):raise ValueError('birth_date is required')
    bt=get('birth_time')
    if isinstance(bt,str):bt=time.fromisoformat(bt)
    if bt is not None and not isinstance(bt,time):raise ValueError('Invalid birth_time')
    unknown=get('time_unknown',False) or bt is None
    birth=Birth(bd.year,bd.month,bd.day,None if unknown else bt.hour,
                0 if unknown else bt.minute,sex=get('gender'),
                calendar=get('calendar_type','solar'),leap=get('is_leap_month',False))
    if as_of is None:as_of=get('as_of') or datetime.now(timezone(timedelta(hours=9))).date()
    if isinstance(as_of,date):as_of=as_of.isoformat()
    return recommend(birth,as_of,days,mode,history,exclude_ids)
