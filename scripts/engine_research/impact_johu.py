"""보류자 1,000명 중 × 60갑자: 오늘 보완 오행 변화, 점수 카드 '과다 강화'와 겹침."""
import os as _os, sys as _sys
ROOT = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
DATA = _os.path.join(ROOT, 'docs', 'engine')
OUT = _os.environ.get('RESEARCH_OUT', '/tmp')
_sys.path[:0] = [ROOT, _os.path.join(ROOT, 'backend'), _os.path.dirname(_os.path.abspath(__file__))]

import sys, random, datetime as dt
from collections import Counter
from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services.element_balance import natal_balance, daily_blend, ELEMENTS
from app.engine.constants import GAN_WUXING
G="甲乙丙丁戊己庚辛壬癸"; Z="子丑寅卯辰巳午未申酉戌亥"
days=[(G[i%10],Z[i%12]) for i in range(60)]
rng=random.Random(20261024); c=Counter()
for _ in range(1000):
    y=rng.randint(1960,2004); m=rng.randint(1,12); d=rng.randint(1,28); h=rng.randint(0,23)
    core=calculate_myeongri_core(BirthInput(name='x',gender='male',birth_date=dt.date(y,m,d),calendar_type='solar',is_leap_month=False,birth_time=dt.time(h,0),time_unknown=False),target_date=dt.date(2026,11,5))
    nb=natal_balance(core)
    if nb['method']!='gungtong_johu': continue
    old={**nb,'blend_base':None,'overflow':None,'eokbu_avoid':[]}
    sc,sh=nb['scores'],nb['composition']
    oldrank=sorted(ELEMENTS,key=lambda e:(-sc[e],sh[e],ELEMENTS.index(e)))
    c['people']+=1; c['natal_primary_changed']+=oldrank[0]!=nb['primary']
    for s,b in days:
        n=daily_blend(nb,GAN_WUXING[s],b); o=daily_blend(old,GAN_WUXING[s],b)
        c['days']+=1; c['today_changed']+=n['element']!=o['element']
        for tag,res in (('new',n),('old',o)):
            c[f'{tag}_top_in_excess']+=sh[res['element']]>=35
            c[f'{tag}_top2_any_excess']+=any(sh[e]>=35 for e in res['order'][:2])
print({k:v for k,v in c.items()})
print('보완 1순위 바뀐 사람 %.0f%%, 오늘 오행 바뀐 날 %.0f%%, 1칸이 넘치는 오행: 전 %.1f%% → 후 %.1f%%, 두 칸 중 하나: 전 %.1f%% → 후 %.1f%%' % (
 100*c['natal_primary_changed']/c['people'],100*c['today_changed']/c['days'],100*c['old_top_in_excess']/c['days'],100*c['new_top_in_excess']/c['days'],100*c['old_top2_any_excess']/c['days'],100*c['new_top2_any_excess']/c['days']))
