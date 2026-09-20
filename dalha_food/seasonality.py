"""Date-only preference. Never changes food nature/score, target, or eligibility."""
from datetime import date
import re

VERSION='seasonal-preference-v1'
SOURCES={
 'spring':'https://rda.go.kr/webzine/2026/03/3_3.html',
 'summer':'https://www.nongsaro.go.kr/portal/ps/psv/psvr/psvrc/rdaInterDtl.ps?cntntsNo=98757&menuId=PS00063',
 'sweet_potato':'https://www.mafra.go.kr/bbs/mafra/72/324840/artclView.do',
 'shrimp':'https://www.kamis.or.kr/customer/trend/product/product.do?action=detail&brdctsno=432381',
 'winter':'https://www.mof.go.kr/doc/ko/selectDoc.do?bbsSeq=10&docSeq=24336&menuSeq=971',
 'cod':'https://www.mof.go.kr/iframe/doc/ko/selectDoc.do?bbsSeq=10&docSeq=48051&menuSeq=971',
}
# Small source-backed registry. Named dish ingredients only: no guesses about
# a mixed vegetable/seafood label or unknown garnishes. Seasonal ranges are
# editorial calendar groupings, not claims about every cultivar/farm/region.
RULES=[
 ('봄나물',r'봄나물|냉이|달래', (3,4,5),'spring'),
 ('딸기',r'딸기',(3,),'spring'),
 ('오이·열무',r'오이|열무',(8,),'summer'),
 ('애호박',r'애호박',(7,),'summer'),
 ('수박',r'수박',(7,8),'summer'),
 ('갈치',r'갈치',(7,),'summer'),
 ('전복',r'전복',(8,),'summer'),
 ('해파리',r'해파리',(8,),'summer'),
 ('고구마',r'고구마',(10,),'sweet_potato'),
 ('새우',r'새우',(9,10,11),'shrimp'),
 ('굴',r'(?:^|[· /])굴(?=국|밥|전|찜|탕|무침|[· /]|$)',(12,1,2),'winter'),
 ('홍합',r'홍합',(12,1,2),'winter'),
 ('대구',r'대구',(12,),'cod'),
]
SEASON_LABEL={'spring':'봄','summer':'여름','autumn':'가을','winter':'겨울'}

def preference(menu,on):
    month=date.fromisoformat(on).month
    season=('winter' if month in (12,1,2) else 'spring' if month<=5 else 'summer' if month<=8 else 'autumn')
    matched=[{'ingredient':label,'source':SOURCES[source]} for label,pattern,months,source in RULES
             if month in months and re.search(pattern,menu['menu'])]
    food_bonus=.45 if matched else 0.0
    temp=menu.get('profile',{}).get('temperature')
    temp_match=(season=='winter' and temp in ('따뜻하게','뜨겁게')) or (season=='summer' and temp=='차게')
    temperature_bonus=.15 if temp_match else 0.0
    reasons=[]
    if matched:reasons.append('제철 재료 우대: '+', '.join(r['ingredient'] for r in matched))
    if temp_match:reasons.append(SEASON_LABEL[season]+' 제공 온도 선호')
    return {'version':VERSION,'month':month,'season':season,'bonus':round(food_bonus+temperature_bonus,2),
            'food_bonus':food_bonus,'temperature_bonus':temperature_bonus,'matched':matched,'reasons':reasons,
            'basis':'달하 추천 순서용 임시 보정. 음식 성질·목표점수에 합산하지 않음. 날씨·위치 미사용.'}
