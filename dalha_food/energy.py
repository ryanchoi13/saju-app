"""Automatic reference targets, not individual energy prescriptions.

Input birth date must already be normalized to the solar calendar by the app.
No new weight/activity input. Normal targets are KDRI 2025 table values.
Diet presets are DALHA editorial meal-planning budgets, not KDRI recommendations.
"""
from datetime import date

SOURCE = 'https://health.seoulmc.or.kr/uploadFiles/2025_%ED%95%9C%EA%B5%AD%EC%9D%B8%EC%98%81%EC%96%91%EC%86%8C%EC%84%AD%EC%B7%A8%EA%B8%B0%EC%A4%80_%ED%99%9C%EC%9A%A9.pdf'
GENERAL = [(9,11,2000,1800),(12,14,2500,2000),(15,18,2700,2000),
           (19,29,2600,2000),(30,49,2500,1900),(50,64,2200,1700),
           (65,74,2000,1600),(75,120,1900,1500)]
DIET = {20:1900,30:1800,40:1800,50:1700,60:1700,70:1600,80:1600,90:1600,100:1600,110:1600,120:1600}

def age_on(birth, on):
    b=date.fromisoformat(birth); d=date.fromisoformat(on)
    if b>d: raise ValueError('Birth date is in the future')
    return d.year-b.year-((d.month,d.day)<(b.month,b.day))

def energy_target(birth, on, sex=None, mode='general'):
    age=age_on(birth,on); decade=age//10*10
    out=dict(age=age,age_band=f'{decade}대',mode=mode,automatic=True,
             additional_inputs=[],source_url=SOURCE)
    if mode not in ('general','diet'):raise ValueError('Unknown mode')
    if not 10<=age<=120: return dict(out,target_kcal=None,status='age_out_of_scope')
    if mode=='diet':
        # Never calculate a calorie-deficit budget for a child or teenager.
        if age<20:return dict(out,target_kcal=None,status='growth_balanced_menu',
                             basis='10대: 감량 열량 목표 없이 균형 메뉴 제안',sex_used=False)
        return dict(out,target_kcal=DIET[decade],status='editorial_budget',sex_used=False,
                    basis='달하 성인 식단 구성용 임시값 · 개인별 감량 보장/공식 권장량 아님')
    if sex not in ('male','female'):return dict(out,target_kcal=None,status='missing_existing_sex')
    row=next(x for x in GENERAL if x[0]<=age<=x[1])
    return dict(out,target_kcal=row[2 if sex=='male' else 3],status='reference',sex_used=True,
                source_age_range=[row[0],row[1]],basis='2025 한국인 영양소 섭취기준 · 에너지 필요추정량 표',sex=sex)
