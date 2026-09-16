"""Approved SVG garments, selected before daily A/B placement.

Reuses the app's whole-outfit/weather catalog. The palette is the reviewed
24-color research pool, not an elemental classifier. Original daily colors
come from the existing caller; this module never chooses a third element.
Ranking constants below are implementation heuristics, not wearer statistics.
"""
from copy import deepcopy
from pathlib import Path
import colorsys
import itertools
import json
import re

from fashion_v2.template_catalog import templates_for
from fashion_v2.weather_catalog import weather_templates_for
from fashion_v2.review_preferences import apply_review_preferences
from fashion_v2.realwear_rules import styling_for, colour_parts, visible_colors, accessory_spec
from fashion_v2.coordination import POLICY_VERSION, tie_separation, evaluate_coordination
from wada_color_rules import WADA_COLORS

PALETTE = json.loads(Path(__file__).with_name('approved_palette.json').read_text())
PALETTE['light_gray'] = dict(id='light_gray', name='라이트 그레이', hex='#CDD0D3', family='neutral', element='금', kind='calm')
# A wearable tone requested in review, separate from the original research pool.
PALETTE['pale_pink'] = {**PALETTE['pink'], 'id':'pale_pink', 'name':'연한 분홍', 'hex':'#E8DADB'}
VERSION = 'approved-svg-4'
TPOS = ('casual', 'business_casual', 'business_formal')
ALIASES = {'cream':'ivory', 'dark_brown':'brown', 'dark_denim':'navy',
           'denim_blue':'denim', 'dusty_blue':'sky', 'light_blue':'sky',
           'soft_pink':'pink', 'ivory_navy':'ivory', 'burgundy_navy':'burgundy',
           'navy_burgundy':'navy'}


def tone(key):
    c = deepcopy(PALETTE[ALIASES.get(key, key)])
    c['name_ko'] = c['name']
    return c


def describe_color(value):
    c = deepcopy(value)
    if not re.fullmatch(r'#[a-fA-F0-9]{6}', c.get('hex', '')):
        raise ValueError('색상은 6자리 HEX여야 합니다')
    c['hex'] = c['hex'].upper()
    rgb = [int(c['hex'][i:i+2], 16)/255 for i in (1, 3, 5)]
    h, l, s = colorsys.rgb_to_hls(*rgb)
    known = next((p for p in PALETTE.values() if p['hex'].upper() == c['hex']), None)
    meta = WADA_COLORS.get(c['hex'].lower(), {})
    fam = (known or {}).get('family') or meta.get('hue_family')
    if fam == 'neutral':
        fam = 'black' if known['id'] == 'black' else 'white' if known['id'] in {'white','ivory'} else 'gray'
    fam = {'earth':'brown', 'navy':'blue', 'charcoal':'gray', 'pink':'red', 'violet':'purple', 'gold':'yellow'}.get(fam, fam)
    if not fam:
        fam = ('white' if l > .85 else 'black' if l < .16 else 'gray') if s < .10 else (
            'red' if h < .055 or h > .94 else 'orange' if h < .12 else 'yellow' if h < .19 else
            'green' if h < .44 else 'teal' if h < .53 else 'blue' if h < .72 else 'purple')
    c.update(family=fam, lightness=l, saturation=s, kind=(known or {}).get('kind') or ('vivid' if s>.65 and .25<l<.72 else 'calm'),
             name_ko=c.get('name_ko') or c.get('name') or (known or {}).get('name') or '추천색')
    return c


def canonical_name(item, gender, tpo):
    """Explicit selection conversion; returned label is also the drawn label."""
    n, cat = item['label'], item['category']
    if cat == 'tie': return '넥타이'
    if cat == 'bag':
        return next((x for x in ('백팩','크로스백','숄더백','토트백','핸드백') if x in n), '핸드백')
    if cat == 'shoes':
        for pattern, name in [('옥스퍼드','옥스퍼드'),('더비','더비 구두'),('앵클','앵클부츠'),('부츠','부츠'),('샌들','샌들'),('펌프스','낮은 굽 펌프스'),('로퍼','로퍼'),('플랫|컴포트화','플랫슈즈'),('운동화|스니커즈','운동화')]:
            if re.search(pattern,n): return name
    if cat == 'bottom':
        for pattern, name in [('수트 스커트','수트 스커트'),('수트 바지','수트 바지'),('반바지','반바지'),('스커트','미디 스커트'),('청바지','데님 바지'),('슬랙스','슬랙스'),('팬츠|면바지','면바지')]:
            if re.search(pattern,n): return name
    if cat == 'dress': return '반팔 원피스' if '반팔' in n else '긴팔 원피스'
    if cat == 'top':
        if '후드' in n: return '후드티'
        if '맨투맨' in n: return '맨투맨'
        if '폴로' in n: return '반팔 폴로 티셔츠'
        if '니트' in n: return '반팔 폴로 티셔츠' if '반팔' in n and gender == 'male' else '반팔 티셔츠' if '반팔' in n else '니트'
        if '셔츠' in n or '블라우스' in n:
            if '티셔츠' in n: return '반팔 티셔츠' if '반팔' in n else '긴팔 티셔츠'
            if '반팔' in n: return '반팔 캐주얼 셔츠'
            return '긴팔 정장 셔츠' if tpo == 'business_formal' else '긴팔 캐주얼 셔츠'
    if cat in {'outer','coat','mid','carry_outer'}:
        for pattern, name in [('패딩','패딩'),('코트','코트'),('수트','수트 재킷'),('가디건','가디건'),('바람막이','바람막이'),('후드','집업 후드'),('블레이저|정장|언스트럭처드|칼라리스|경량 재킷','블레이저'),('재킷|점퍼|블루종|오버셔츠|크롭 셔츠','블루종')]:
            if re.search(pattern,n): return name
    raise ValueError(f'지원하지 않는 아이템: {cat} / {n}')


def select_template(original, age, number, weather=None):
    result = deepcopy(original)
    result.update(look_role=f'recommendation_{number}', recommendation_number=number,
                  age=age, selection_mode='weather_template_then_approved_garments',
                  renderer=VERSION, selection_changes=[])
    items = []
    for source in original['items']:
        if source['category'] == 'leg_layer':
            # Winter skirt templates are replaced below when no tights drawing exists.
            continue
        item = deepcopy(source)
        item['source_label'] = source['label']
        item['label'] = canonical_name(item, result['gender'], result['tpo'])
        if item['label'] != item['source_label']:
            result['selection_changes'].append({'from':item['source_label'], 'to':item['label'], 'reason':'49종 확정 도안으로 구성 선택'})
        item['wear_mode'] = item.get('wear_mode', 'worn')
        item['base_color'] = ALIASES.get(item['color'], item['color'])
        if item['category'] == 'tie' and item['color'] in {'burgundy_navy','navy_burgundy'}:
            pattern_base, pattern_accent = item['color'].split('_')
            item.update(pattern='stripe', pattern_base=pattern_base, pattern_palette=[pattern_accent, pattern_base])
        items.append(item)
    cold = (weather or {}).get('thermal_band') in {'cold','freezing'} or (not weather and result['season'] == 'winter')
    hot = (weather or {}).get('thermal_band') in {'hot','very_hot','warm'} or (not weather and result['season'] == 'summer')
    # Avoid recommending a skirt without the required, currently unavailable leg layer.
    if cold and any(x['category'] == 'leg_layer' for x in original['items']):
        items = [x for x in items if x['category'] not in {'dress','bottom'}]
        if not any(x['category']=='top' for x in items):
            items.append(dict(category='top', label='니트', material='wool_knit', base_color='ivory', wear_mode='worn'))
        formal = result['tpo']=='business_formal'
        suit = next((x for x in items if x.get('suit_group')), {})
        items.append(dict(category='bottom',label='수트 바지' if formal else '면바지',base_color=suit.get('base_color','charcoal'),material=suit.get('material','fleece_cotton'),wear_mode='worn',**({'suit_group':suit['suit_group']} if suit.get('suit_group') else {})))
        result['selection_changes'].append({'reason':'겨울 보온 구성: 타이츠 도안이 없는 치마·원피스 대신 긴바지 착장 선택'})
    for item in items:
        cat, n = item['category'], item['label']
        # A whole outfit already chooses footwear by gender/season/TPO.
        # Do not erase a researched flat/boot merely because its TPO is casual.
        if cat=='shoes':
            item['selection_reason']='계절·성별·TPO에 맞춰 고른 착장의 지정 신발 유지'
        if cat=='bottom' and n=='데님 바지': item['base_color']='navy' if cold else 'denim'
        if cat=='top': item['base_color']='white'
        if cat=='shoes': item['base_color']='white' if item['label']=='운동화' else 'black'
        if cat=='tie': item['base_color']=item.get('pattern_base','burgundy')
        if cat=='coat': item['base_color']='black'
        if cat=='dress': item['base_color']='navy' if result['tpo']=='business_formal' else 'white'
        if cat in {'outer','mid','carry_outer'} and not item.get('suit_group'):
            item['base_color']='ivory' if result['tpo']=='casual' and number==1 else 'navy'
        if cat=='bottom' and item['label'] not in {'데님 바지','수트 바지','수트 스커트'}:
            item['base_color']='beige' if number==1 and not cold else 'charcoal'
        if hot and cat=='top' and item['label']=='니트':
            item['label']='반팔 폴로 티셔츠' if result['gender']=='male' else '반팔 티셔츠'
    # A functional bag belongs to this whole outfit before any color is considered.
    if result['gender']=='female' and (result['tpo']=='business_formal' or any(x['category']=='dress' for x in items)):
        items.append(dict(category='bag',label='핸드백' if result['tpo']=='business_formal' else '크로스백',base_color='black',material='leather',wear_mode='worn'))
    for i, item in enumerate(items):
        item['key']=f'item-{i}'
        c=tone(item['base_color'])
        item.update(color_name=c['name'],hex=c['hex'],color_relation='base')
    result['items']=items
    result['styling']=styling_for(result)
    result['form']='dress' if any(x['category']=='dress' for x in items) else 'skirt' if any('스커트' in x['label'] for x in items) else 'pants'
    return result


def stable(c, suit=False, denim=False):
    f,l,s=c['family'],c['lightness'],c['saturation']
    if denim: return f=='black' or f=='blue' and (s < .5 or l < .3 or l > .72)
    if f in {'gray','black'}: return True
    if f=='white': return not suit
    if f=='brown': return s < .55 and (not suit or l < .5)
    return f=='blue' and l < .34 and s < .72


def permitted(c, group, look):
    cat=group['category']; formal=look['tpo']=='business_formal'
    if cat=='suit': return stable(c, suit=True)
    if cat=='bottom': return stable(c, denim=group['label']=='데님 바지')
    if cat=='shoes':
        if look['gender']=='male' and formal: return c['family'] in {'black','brown'} and c['lightness'] < .46
        return stable(c) or (look['gender']=='female' and c['family']=='red' and c['lightness']<.45)
    if cat in {'tie','bag','accessory'}: return True
    # Bright coats were rejected in review; retain reviewed colored puffers.
    if group['label']=='코트':
        return stable(c, suit=True) or (look['season'] in {'spring','autumn'} and c['hex'].upper()==PALETTE['beige']['hex'].upper())
    if cat in {'outer','coat','carry_outer','mid','dress'} and formal: return stable(c,suit=cat!='mid')
    if formal and cat=='top':
        if c['family']=='red' and c['saturation']>.30: return False
        return c['family'] in {'white','gray','blue','red','purple'} and c['lightness']>=.72 and c['saturation']<.58
    if look['age'] is not None and look['age']>=50 and look['recommendation_number']==1:
        if c['kind']=='vivid' or c['saturation']>.5 and .25<c['lightness']<.72: return False
    if look['tpo']=='business_casual' and cat in {'outer','coat','carry_outer'} and group['label'] not in {'가디건','집업 후드'}:
        return stable(c)
    return not (look['tpo']=='business_casual' and c['saturation']>.7 and c['lightness']<.7)


def variants(c):
    yield c, 'exact', ''
    family=c['family']
    choices={'blue':['navy','denim','sky'], 'red':['pink','burgundy','pale_pink'],
             'green':['sage','forest'], 'purple':['lavender','purple'],
             'brown':['beige','brown'], 'gray':['light_gray','gray','charcoal'],
             'white':['white','ivory'], 'black':['black'], 'yellow':['butter'],
             'teal':['teal']}.get(family,[])
    for key in choices:
        v=describe_color(tone(key))
        if v['hex']!=c['hex']:
            yield v,'similar','원색이 해당 부위의 착장 조건에 맞지 않아 같은 계열의 착장용 톤 적용'


def groups(look):
    grouped={}; result=[]
    for i,item in enumerate(look['items']):
        if item.get('suit_group'): grouped.setdefault(item['suit_group'],[]).append(i)
        else: result.append(dict(indexes=[i],category=item['category'],label=item['label']))
    for indices in grouped.values():
        if len(indices)!=2: raise ValueError('수트 한 세트가 필요합니다')
        result.append(dict(indexes=indices,category='suit',label='수트'))
    return result


def candidates(look, color, role):
    result=[None]
    targets=look.get('color_targets',{})
    if role in targets and targets[role] is None: return result
    target=targets.get(role,{})
    for group in groups(look):
        if target and group['category']!=target['category']: continue
        exact_allowed=permitted(color,group,look)
        for actual,relation,reason in variants(color):
            if target.get('tone') and actual['hex']!=tone(target['tone'])['hex']: continue
            if relation=='similar' and exact_allowed and not target.get('tone') and group['category'] not in {'tie','bag','accessory'}: continue
            if permitted(actual,group,look):
                area={'tie':1,'shoes':1,'bag':1,'accessory':1,'top':2 if look['tpo']=='business_formal' else 3,'suit':4}.get(group['category'],3)
                worn_outer=any(i['category'] in {'outer','coat'} and i['wear_mode']!='carry' for i in look['items'])
                if worn_outer and group['category'] in {'top','mid','dress'}: area=2
                if group['category']=='suit' and any(i['category']=='coat' for i in look['items']): area=2
                if relation=='similar' and target.get('tone'):
                    reason='검토 의견에 맞춰 같은 계열의 착장용 톤 적용'
                elif relation=='similar' and exact_allowed:
                    reason='소품에 원추천색과 같은 계열의 착장용 톤을 함께 비교해 적용'
                if relation=='similar' and group['category']=='top' and look['tpo']=='business_formal' and actual.get('id')=='pale_pink':
                    reason='포멀 셔츠의 분홍 채도를 낮춘 착장용 톤 적용'
                result.append(dict(**group,color=actual,relation=relation,reason=reason,area=area))
    return result


def apply_colors(look, a, b, previous=None):
    raw={'A':describe_color(a),'B':describe_color(b)}
    # Candidate comparisons reuse the same small palette. Keep this cache
    # local to one outfit so profiles and policy changes cannot leak/stale.
    color_facts={}
    def describe_candidate_color(value):
        key=value['hex'].upper()
        if key not in color_facts:
            color_facts[key]=describe_color({'hex':key})
        return color_facts[key]
    best=None
    for ca,cb in itertools.product(candidates(look,raw['A'],'A'),candidates(look,raw['B'],'B')):
        if ca and cb and set(ca['indexes']) & set(cb['indexes']): continue
        items=deepcopy(look['items']); placements={}; score=0
        for role,choice in [('A',ca),('B',cb)]:
            if choice is None: continue
            c=choice['color']
            score+=(90 if role=='A' else 65)+choice['area']*9-(5 if choice['relation']=='similar' else 0)
            if choice['relation']=='similar':
                score-=abs(c['lightness']-raw[role]['lightness'])*6
            if previous and previous.get(role)==(choice['category'],c['hex']): score-=35
            if role=='A' and choice['category']=='tie' and look['recommendation_number']==1: score+=12
            if choice['category']=='suit' and c['family']=='brown': score-=9
            if choice['category'] in {'tie','bag','accessory'} and look['tpo']!='casual' and not look.get('color_targets'):
                # Soft preference, not a gender/age colour ban or new TPO.
                if c['saturation']>.65 and .25<c['lightness']<.72: score-=12
            for i in choice['indexes']:
                items[i].update(hex=c['hex'],color_name=c['name_ko'],applied_daily_color=role,color_relation=choice['relation'],source_hex=raw[role]['hex'],source_color_name=raw[role]['name_ko'],tone_reason=choice['reason'])
            placements[role]=dict(slot=choice['category'],indexes=choice['indexes'],name=c['name_ko'],hex=c['hex'],relation=choice['relation'],reason=choice['reason'],area='small' if choice['area']==1 else 'medium' if choice['area']==2 else 'large')
        suit=next((i for i in items if i.get('suit_group')),None)
        colour_parts(items,PALETTE)
        # Inspect the actual rendered pattern before rejecting a tonal tie.
        separation=tie_separation(items,describe_candidate_color)
        if not separation['ok'] and suit and not suit.get('applied_daily_color'):
            for key in ('navy','charcoal','gray'):
                alt=tone(key)
                for i in items:
                    if i.get('suit_group'):
                        i.update(hex=alt['hex'],color_name=alt['name_ko'],base_adjustment='도안에서 넥타이가 구분되도록 수트 기본색 조정')
                colour_parts(items,PALETTE)
                separation=tie_separation(items,describe_candidate_color)
                if separation['ok']: break
        if not separation['ok']: continue
        count=len(visible_colors(items))
        owner_component=any(i.get('watch_case_hex') for i in items)
        # 4-color output is retained for explicit review, never called approved.
        if count>(5 if owner_component else 4): continue
        score-=max(0,count-3)*18
        score+=evaluate_coordination(items,look['tpo'],describe_candidate_color)['score_adjustment']
        if best is None or score>best[0]: best=(score,items,placements,count)
    if best is None: raise ValueError('안전한 배색 후보가 없습니다')
    result=deepcopy(look)
    result['items'],placements=best[1],best[2]
    result['coordination']=evaluate_coordination(result['items'],look['tpo'],describe_candidate_color)
    result['coordination']['tie_separation']=tie_separation(result['items'],describe_candidate_color)
    result['outfit_policy_version']=POLICY_VERSION
    for role,placement in placements.items():
        placement['parts']=[dict(index=i,part=name,hex=part['hex'])
            for i in placement['indexes'] for name,part in result['items'][i].get('color_parts',{}).items()
            if part.get('role')==role]
    result['color_strategy']={'priority':'reviewed_outfit_preference' if look.get('review_preference') else 'A_first_unless_B_fits_larger_area','original':raw,'placements':placements,
        'unresolved':[dict(role=r,name=raw[r]['name_ko'],hex=raw[r]['hex'],next_step='palette',reason='검토에서 지정한 실착 조합을 우선하고 추천 팔레트로 안내' if r in look.get('color_targets',{}) and look['color_targets'][r] is None else '자연스럽게 적용할 부위가 없어 추천 팔레트로 안내') for r in raw if r not in placements],
        'color_count':best[3],'review_required':best[3]>3,'additional_element_C':None}
    result['garment_spec']=to_spec(result)
    component_colors={i['watch_case_hex'] for i in result['items'] if i.get('watch_case_hex')}
    if component_colors:
        result['color_strategy'].update(color_count=len(visible_colors(result['items'])),
            review_required=True, color_count_exception='사용자가 지정한 시계 부위별 배색',
            component_color_source='user_requested_not_element_C')
    return result


def to_spec(look):
    items=look['items']; s=dict(gender=look['gender'],top='',bottom='',dress='',outer='',shoe='',bag='',accessories=[],accessoryItems=[],suitLinked=True,outerOpen=True,outerMode='wear',tuck='out')
    layers=[]
    for item in items:
        c=item['category']; n=item['label']
        slot={'top':'top','bottom':'bottom','dress':'dress','shoes':'shoe','bag':'bag','tie':'accessory','accessory':'accessory'}.get(c)
        if c in {'outer','coat','mid','carry_outer'}: layers.append(item);continue
        if c in {'tie','accessory'}:
            s['accessories'].append(n)
            s['accessoryItems'].append(accessory_spec(item))
        elif slot: s[slot]=n
        if slot: s[('top' if slot=='dress' else slot)+'Color']=item['hex']
        if item.get('neck')=='turtleneck': s['knitNeck']='turtleneck'
        if item.get('hem_length')=='knee': s['formalHem']='knee'
        if item.get('watch_case_hex'): s['watchCaseColor']=item['watch_case_hex']
    # Innermost outer first; the extra layer is composited with the same approved paths.
    layers.sort(key=lambda i: {'mid':0,'outer':1,'coat':2,'carry_outer':3}[i['category']])
    if layers:
        first=layers[0];s.update(outer=first['label'],outerColor=first['hex'],outerMode='carry' if first['wear_mode']=='carry' else 'wear')
    if len(layers)>1:
        if len(layers)>2 or layers[1]['wear_mode']=='carry': raise ValueError('지원하지 않는 겉옷 레이어 조합')
        s['overOuter']={'name':layers[1]['label'],'color':layers[1]['hex'],'open':True}
    s['tuck']=styling_for(look)['tuck']
    if look['season']=='winter' or look.get('weather_fit',{}).get('thermal_band') in {'cold','freezing'}: s['trouserExtraLength']=24
    if s['dress']: s['top']='';s['bottom']=''
    return s


def build_svg_catalog_contexts(gender,season,color_a,color_b,weather_profile=None,age=None,board_weather_profile=None):
    if gender not in {'male','female'}: raise ValueError('성별 확인 필요')
    if season not in {'spring','summer','autumn','winter'}: raise ValueError('계절 확인 필요')
    result={}
    for tpo in TPOS:
        source=weather_templates_for(gender,tpo,weather_profile) if weather_profile else templates_for(gender,season,tpo)
        looks=[]; previous=None
        for number,original in enumerate(source,1):
            selected=apply_review_preferences(select_template(original,age,number,weather_profile),color_a,color_b)
            selected['styling']=styling_for(selected)
            for i,item in enumerate(selected['items']):
                c=tone(item['base_color'])
                item.update(key=f'item-{i}',color_name=c['name'],hex=c['hex'],color_relation='base')
            selected['form']='dress' if any(i['category']=='dress' for i in selected['items']) else 'skirt' if any('스커트' in i['label'] for i in selected['items']) else 'pants'
            look=apply_colors(selected,color_a,color_b,previous)
            previous={r:(p['slot'],p['hex']) for r,p in look['color_strategy']['placements'].items()}
            looks.append(look)
        result[tpo]={'status':'svg_integration_review','renderer':VERSION,'looks':looks,'weather_applied':bool(weather_profile)}
    return result
