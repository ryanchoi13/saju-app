"""Local calendar facts -> separated natal/daily state -> editorial food target.

Not a recreation of SAZU yongsin, strength, medical or narrative models.
Rules are versioned independently of comparison fixtures. No network/file reads.
"""
from collections import Counter
from dataclasses import asdict,dataclass
from datetime import date
from functools import lru_cache
from lunar_python import Solar
from korean_lunar_calendar import KoreanLunarCalendar

VERSION='dalha-local-food-state-v1'
STEMS='甲乙丙丁戊己庚辛壬癸';BRANCHES='子丑寅卯辰巳午未申酉戌亥'
SK='갑을병정무기경신임계';BK='자축인묘진사오미신유술해'
STEM_ELEMENTS=('wood','wood','fire','fire','earth','earth','metal','metal','water','water')
BRANCH_ELEMENTS=('water','earth','wood','wood','earth','fire','fire','earth','metal','metal','earth','water')
TRINES={'water':'申子辰','wood':'亥卯未','fire':'寅午戌','metal':'巳酉丑'}
SEASONS={'water':'亥子丑','wood':'寅卯辰','fire':'巳午未','metal':'申酉戌'}
OTHER={
    'six_combination':('子丑','寅亥','卯戌','辰酉','巳申','午未'),
    'clash':('子午','丑未','寅申','卯酉','辰戌','巳亥'),
    'harm':('子未','丑午','寅巳','卯辰','申亥','酉戌'),
    'break':('子酉','丑辰','寅亥','卯午','巳申','未戌'),
}
# Inherited month environment from the existing climate.py, not a yongsin table.
MONTH_CLIMATE={
    '寅':'cool','卯':'mild','辰':'mild','巳':'hot','午':'very_hot','未':'hot',
    '申':'warm','酉':'cool','戌':'cool','亥':'cold','子':'very_cold','丑':'cold'}

@dataclass(frozen=True)
class Birth:
    year:int
    month:int
    day:int
    hour:int|None
    minute:int=0
    sex:str='female'
    calendar:str='solar'
    leap:bool=False

    def solar_date(self):
        if self.sex not in ('female','male'):raise ValueError('sex must be male/female')
        if not 1900<=self.year<=2100:raise ValueError('Birth year outside reviewed calendar scope1900–2100')
        if self.hour is not None and not 0<=self.hour<=23:raise ValueError('Invalid hour')
        if not 0<=self.minute<=59:raise ValueError('Invalid minute')
        if self.hour is None and self.minute:raise ValueError('Unknown hour cannot have known minute')
        if self.calendar=='solar':
            if self.leap:raise ValueError('Solar input cannot specify lunar leap month')
            return date(self.year,self.month,self.day)
        if self.calendar!='lunar':raise ValueError('Unknown calendar')
        c=KoreanLunarCalendar()
        if not c.setLunarDate(self.year,self.month,self.day,self.leap):raise ValueError('Invalid or unsupported lunar date')
        if bool(c.isIntercalation)!=self.leap:raise ValueError('Requested lunar leap month does not exist')
        return date(c.solarYear,c.solarMonth,c.solarDay)

def pillar(text):
    return dict(stem=text[0],branch=text[1],full=SK[STEMS.index(text[0])]+BK[BRANCHES.index(text[1])],
                stem_element=STEM_ELEMENTS[STEMS.index(text[0])],branch_element=BRANCH_ELEMENTS[BRANCHES.index(text[1])])

def eight_on(d,hour=12,minute=0):
    eight=Solar.fromYmdHms(d.year,d.month,d.day,hour,minute,0).getLunar().getEightChar()
    eight.setSect(2) # Civil day changes at00:00, not early-zi23:00.
    return eight

def natal_thermal(pillars):
    month=pillars['month']['branch'];dm=pillars['day']['stem_element']
    environment=MONTH_CLIMATE[month]
    if environment in ('cold','very_cold','cool'):
        direction='warming';needed='fire';target=75;rule='season-cool'
    elif environment in ('hot','very_hot','warm'):
        direction='cooling';needed='water';target=25;rule='season-warm'
    elif month=='卯' and dm=='wood':
        direction='warming';needed='fire';target=75;rule='spring-wood-fire'
    else:
        direction='balanced';needed=None;target=50;rule='mild-unresolved-neutral'
    inventory=Counter(e for p in pillars.values() if p for e in (p['stem_element'],p['branch_element']))
    return dict(direction=direction,needed_element=needed,target=target,rule=rule,
                month_environment=environment,day_master_element=dm,
                visible_element_counts={e:inventory[e] for e in ('wood','fire','earth','metal','water')},
                status='editorial_food_baseline',confidence='limited',
                provider_yongsin_equivalent=False,
                reasoning='월령 환경과 봄 목 일간 보완 규칙에 따른 달하 음식 기준. 장부·체질·신강약·최종 용신을 판정한 값이 아님.',
                limitations=['원국 내 조절 요소의 실효·종격 등 예외를 아직 해결하지 않음',
                             '50은 개인의 평성 확정이 아니라 온냉 방향 미정 시 중간 음식 목표',
                             '오행 개수는 관측 정보로만 보존하며 부족 개수 보충에 사용하지 않음'])

def build_base(birth):
    d=birth.solar_date();eight=eight_on(d,12 if birth.hour is None else birth.hour,birth.minute)
    pillars={n:pillar(v) for n,v in [('year',eight.getYear()),('month',eight.getMonth()),('day',eight.getDay())]}
    pillars['hour']=None if birth.hour is None else pillar(eight.getTime())
    return dict(version=VERSION,source='local',scope='natal',input=asdict(birth),
                solar_birth=d.isoformat(),pillars=pillars,thermal=natal_thermal(pillars),
                calendar_policy={'library':'lunar-python1.4.8','lunar_conversion':'korean-lunar-calendar0.3.1',
                    'time':'Korean civil clock as supplied; no city, longitude or true-solar correction',
                    'day_boundary':'00:00; EightChar sect2','year_month_boundary':'solar terms',
                    'unknown_hour':'hour pillar omitted; noon representative for year/month boundary, uncertainty retained'},
                incomplete_time=birth.hour is None)

def relationships(pillars,daily):
    """Observed group membership, not successful transformation or health effect."""
    results=[];b=daily['branch']
    for position,p in pillars.items():
        if p is None:continue
        a=p['branch'];pair={a,b}
        if a==b:continue
        for kind,groups in [('trine_pair',TRINES),('seasonal_pair',SEASONS)]:
            for element,group in groups.items():
                if pair<=set(group):
                    results.append(dict(kind=kind,element=element,source_position=position,
                                        source=a,target=b,full_group=group,
                                        transformation_established=False))
        for kind,groups in OTHER.items():
            if any(pair==set(group) for group in groups):
                results.append(dict(kind=kind,source_position=position,source=a,target=b,
                                    transformation_established=False))
    return results

def build_daily(base,on):
    d=date.fromisoformat(on) if isinstance(on,str) else on
    if d<date.fromisoformat(base['solar_birth']):raise ValueError('Reference before birth')
    eight=eight_on(d);day=pillar(eight.getDay())
    return dict(version=VERSION,source='local',scope='daily',date=d.isoformat(),day=day,
                calendar_context={'year':pillar(eight.getYear()),'month':pillar(eight.getMonth())},
                relations=relationships(base['pillars'],day),
                context_note='월주·세주는 계산 맥락으로 보존. 월운/세운의 음식 가중치를 별도로 적용하지 않음')

def food_target(base,period):
    if period['scope']!='daily':raise ValueError('Only daily food integration is implemented')
    thermal=base['thermal'];needed=thermal['needed_element'];start=thermal['target']
    evidence=[r for r in period['relations'] if r.get('element')==needed and needed is not None]
    kinds={r['kind'] for r in evidence}
    if 'seasonal_pair' in kinds:target=100-start;rule='seasonal-support-reverse'
    elif 'trine_pair' in kinds:target=50;rule='trine-support-neutral'
    else:target=start;rule='retain-natal-food-baseline'
    return dict(date=period['date'],target=target,preferred_elements=[],source='local',rule=rule,
                base_rule=thermal['rule'],evidence=evidence,policy_version=VERSION,
                status='dalha_product_rule',
                note='합 관계를 음식 방향 완화에 사용하는 초기 규칙. 실제 합화·과다·의학적 필요 판단 아님')
