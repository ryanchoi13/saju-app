"""Approved deterministic menu selector, exported without research imports."""
import itertools
from collections import Counter
from .energy import energy_target
from .seasonality import preference

SNACKS=[dict(menu='추가 간식 없음',kcal=0,components=[]),
 dict(menu='플레인요거트 150g',kcal=118.5,components=[('요거트',150,79)]),
 dict(menu='우유 200g',kcal=126,components=[('우유',200,63)]),
 dict(menu='사과 150g·우유 200g',kcal=202.5,components=[('사과',150,51),('우유',200,63)]),
 dict(menu='바나나 100g·우유 200g·호두 15g',kcal=310.2,components=[('바나나',100,81),('우유',200,63),('호두',15,688)])]

def select_plan(pool,days,mode,birth,sex,initial_history=None,exclude_ids=None):
    tolerance=.20 if mode=='general' else .15
    history=list(initial_history or []);out=[]
    for i,day in enumerate(days):
        preferred=day.get('preferred_elements',['목','화'])
        budget=energy_target(birth,day['date'],sex,mode);target=budget['target_kcal'];lists=[]
        season_preferences={x['id']:preference(x,day['date']) for x in pool}
        recent=history[-9:];recent_ids={x['id'] for x in recent} | set(exclude_ids or []);counts=Counter(x['id'] for x in history)
        breakfasts=[x for x in history if x['period']=='breakfast']
        rolling_week=history[-18:] # Previous six complete days + current day = seven days.
        bread_count=sum(x['family']=='빵' and x['period']=='breakfast' for x in rolling_week)
        for period,fraction in [('breakfast',.20),('lunch',.37),('dinner',.35)]:
            eligible=[x for x in pool if period in x['periods'] and (mode=='general' or x['diet_eligible']) and x['id'] not in recent_ids]
            if period=='breakfast':eligible=[x for x in eligible if not(x['family']=='빵' and bread_count>=2)]
            else:
                limited={'pizza':2,'burger':1,'chinese_noodles':2}
                eligible=[x for x in eligible if x['category'] not in limited or sum(z['category']==x['category'] for z in rolling_week)<limited[x['category']]]
            # Keep normal single portions; calorie differences affect choice, not
            # arbitrary multiplication of a serving to make a total look exact.
            # Calories and variety can require expanding beyond the initial
            # ten-point band. Keep the expansion explicit on each selected dish.
            candidates=[x for x in eligible if x['score'] is not None and abs(x['score']-day['target'])<=30]
            if period=='breakfast' and breakfasts:
                varied=[x for x in candidates if x['family']!=breakfasts[-1]['family']]
                if varied:candidates=varied
            if not candidates:candidates=eligible
            def rank(x):
                return ((max(0,abs(x['kcal']-target*fraction)-100)/160 if target is not None else 0) + 3*counts[x['id']]
                    + (0 if not preferred or x['element'] in preferred else 1.2)
                    + (abs(x['score']-day['target'])/15 if x['score'] is not None else 5)
                    + sum(z['category']==x['category'] for z in recent)*1.8
                    + (sum(z['family']==x['family'] for z in breakfasts)*1.5 if period=='breakfast' else 0)
                    - season_preferences[x['id']]['bonus'])
            selected=sorted(candidates,key=lambda x:(rank(x),x['id']))[:24]
            # Cumulative novelty must not prune every feasible energy combination.
            # Preserve calorie coverage alongside the quality-ranked shortlist.
            if target is not None:
                extra=sorted(candidates,key=lambda x:(abs(x['kcal']-target*fraction),rank(x),x['id']))[:8]
                extra+=sorted(candidates,key=lambda x:(-x['kcal'],rank(x),x['id']))[:8]
                selected=list({x['id']:x for x in selected+extra}.values())
            if not selected:
                raise ValueError('조건에 맞는 다른 세트를 찾지 못했습니다. 현재 세트를 유지합니다.')
            lists.append([dict(x,period=period,window=next((w for w in (10,20,30,100) if x['score'] is None or abs(x['score']-day['target'])<=w),100),local_cost=rank(x),seasonal_preference=season_preferences[x['id']]) for x in selected])
        best=None
        for choices in itertools.product(*lists):
            if len({x['id'] for x in choices})<3:continue
            kcal=sum(x['kcal'] for x in choices)
            snack=min(SNACKS,key=lambda s:abs(kcal+s['kcal']-target)) if target is not None else SNACKS[0]
            total=kcal+snack['kcal']
            calorie_cost=(100*int(abs(total-target)>target*tolerance)+max(0,abs(total-target)-target*tolerance)/20+abs(total-target)/500) if target is not None else 0
            cost=calorie_cost+sum(x['local_cost'] for x in choices)
            cost+=2*int(choices[1]['family']==choices[2]['family'])
            if choices[1]['category']==choices[2]['category'] and choices[1]['category'] in ('pizza','burger','chinese_noodles'):continue
            if best is None or cost<best[0]:best=(cost,choices,snack,total)
        if best is None:
            raise ValueError('조건에 맞는 다른 세트를 찾지 못했습니다. 현재 세트를 유지합니다.')
        _,chosen,snack,total=best;history.extend(chosen)
        out.append(dict(date=day['date'],target=day['target'],energy=budget,meals=list(chosen),snack=snack,
                        total_kcal=round(total,2),difference_kcal=round(total-target,2) if target is not None else None,
                        tolerance=tolerance,
                        within_calorie_band=abs(total-target)<=target*tolerance if target is not None else None,
                        within_10_percent=abs(total-target)<=target*.1 if target is not None else None))
    return out
