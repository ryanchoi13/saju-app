"""Explicit whole-outfit templates for fashion v2 stage 1.

Each string below is one fixed outfit, not a pool for random item mixing.
All entries remain review-only until visual and owner approval.
"""

from collections import Counter

GENDERS = ('male', 'female')
SEASONS = ('spring', 'summer', 'autumn', 'winter')
TPOS = ('casual', 'business_casual', 'business_formal')
ROLES = ('daily', 'trend')
PRACTICAL_MALE_BOTTOM_COLORS = {
    'black', 'navy', 'beige', 'gray', 'charcoal', 'light_gray',
    'denim_blue', 'dark_denim',
}


def _item(value):
    fields = value.split('|')
    result = dict(zip(('category','label','color','material'), fields[:4]))
    if len(fields) > 4 and fields[4]:
        result['suit_group'] = fields[4]
    return result


def _look(value):
    form, formal_variant, items = value.split('::')
    return {'form': form, 'formal_variant': formal_variant or None,
            'items': [_item(v) for v in items.split(';')]}


# key: gender-season-TPO. value: Daily, Trend.
# item: category|Korean label|neutral color family|material|optional suit group.
RAW_LOOKS = {
    'male-spring-casual': (
        'pants::::outer|블루종|navy|cotton_nylon;top|맨투맨|cream|cotton;bottom|스트레이트 청바지|denim_blue|denim;shoes|레트로 운동화|gray|suede_mesh',
        'pants::::outer|데님 재킷|dark_denim|denim;top|스트라이프 니트|ivory_navy|cotton_knit;bottom|면바지|beige|cotton;shoes|스웨이드 운동화|brown|suede'),
    'male-spring-business_casual': (
        'pants::::outer|해링턴 재킷|beige|cotton;top|옥스퍼드 셔츠|light_blue|cotton;bottom|스트레이트 슬랙스|navy|wool_blend;shoes|로퍼|dark_brown|leather',
        'pants::::outer|블레이저|navy|wool_blend;top|파인 니트|gray|cotton_knit;bottom|면바지|beige|cotton;shoes|미니멀 운동화|black|leather'),
    'male-spring-business_formal': (
        'pants::strict::outer|수트 재킷|navy|spring_wool|navy_spring;top|드레스 셔츠|white|cotton;bottom|수트 바지|navy|spring_wool|navy_spring;tie|레지멘탈 타이|burgundy_navy|silk;shoes|옥스퍼드 구두|black|leather',
        'pants::strict::outer|수트 재킷|charcoal|spring_wool|charcoal_spring;top|드레스 셔츠|light_blue|cotton;bottom|수트 바지|charcoal|spring_wool|charcoal_spring;tie|솔리드 타이|navy|silk;shoes|더비 구두|dark_brown|leather'),
    'male-summer-casual': (
        'pants::::top|반팔 폴로|navy|cotton_pique;bottom|면바지|beige|light_cotton;shoes|캔버스 운동화|gray|canvas',
        'pants::::top|반팔 니트|burgundy|cotton_knit;bottom|버뮤다 반바지|navy|cotton;shoes|스트랩 샌들|black|leather'),
    'male-summer-business_casual': (
        'pants::::top|반팔 클래식 셔츠|light_blue|cotton;bottom|슬랙스|navy|summer_wool;shoes|로퍼|dark_brown|leather',
        'pants::::top|니트 폴로|ivory|cotton_knit;bottom|슬랙스|gray|summer_wool;shoes|미니멀 운동화|black|leather'),
    'male-summer-business_formal': (
        'pants::strict::outer|수트 재킷|navy|summer_wool|navy_summer;top|드레스 셔츠|white|cotton;bottom|수트 바지|navy|summer_wool|navy_summer;tie|솔리드 타이|navy|silk;shoes|옥스퍼드 구두|black|leather',
        'pants::strict::outer|수트 재킷|light_gray|summer_wool|gray_summer;top|드레스 셔츠|light_blue|cotton;bottom|수트 바지|light_gray|summer_wool|gray_summer;tie|레지멘탈 타이|navy_burgundy|silk;shoes|더비 구두|black|leather'),
    'male-autumn-casual': (
        'pants::::outer|필드 점퍼|navy|cotton;top|맨투맨|burgundy|cotton;bottom|스트레이트 청바지|dark_denim|denim;shoes|스웨이드 운동화|dark_brown|suede',
        'pants::::outer|워크 재킷|charcoal|wool_blend;top|후드 티셔츠|gray|cotton;bottom|블랙 청바지|black|denim;shoes|가죽 운동화|black|leather'),
    'male-autumn-business_casual': (
        'pants::::outer|블레이저|navy|wool_blend;top|크루넥 니트|cream|wool_knit;bottom|슬랙스|gray|wool_blend;shoes|로퍼|dark_brown|leather',
        'pants::::outer|필드 재킷|olive|cotton;top|옥스퍼드 셔츠|light_blue|cotton;bottom|단정한 면바지|navy|cotton;shoes|더비 구두|black|leather'),
    'male-autumn-business_formal': (
        'pants::strict::outer|수트 재킷|navy|autumn_wool|navy_autumn;top|드레스 셔츠|white|cotton;bottom|수트 바지|navy|autumn_wool|navy_autumn;tie|레지멘탈 타이|burgundy_navy|silk;shoes|옥스퍼드 구두|black|leather',
        'pants::strict::outer|수트 재킷|charcoal|autumn_wool|charcoal_autumn;top|드레스 셔츠|light_blue|cotton;bottom|수트 바지|charcoal|autumn_wool|charcoal_autumn;tie|솔리드 타이|burgundy|silk;shoes|더비 구두|dark_brown|leather'),
    'male-winter-casual': (
        'pants::::outer|숏 패딩|navy|down;top|후드 티셔츠|gray|fleece_cotton;bottom|기모 캐주얼 팬츠|black|fleece_cotton;shoes|가죽 운동화|black|leather',
        'pants::::coat|울 코트|charcoal|wool;top|하이넥 니트|burgundy|wool_knit;bottom|진청바지|dark_denim|denim;shoes|워크 부츠|dark_brown|leather'),
    'male-winter-business_casual': (
        'pants::::coat|울 코트|navy|wool;top|크루넥 니트|gray|wool_knit;bottom|슬랙스|charcoal|wool;shoes|더비 구두|black|leather',
        'pants::::outer|비즈니스 패딩|black|down;mid|가디건|burgundy|wool_knit;top|셔츠|white|cotton;bottom|슬랙스|navy|wool;shoes|로퍼|dark_brown|leather'),
    'male-winter-business_formal': (
        'pants::strict::coat|울 코트|charcoal|wool;outer|수트 재킷|navy|winter_wool|navy_winter;top|드레스 셔츠|white|cotton;bottom|수트 바지|navy|winter_wool|navy_winter;tie|솔리드 타이|burgundy|silk;shoes|옥스퍼드 구두|black|leather',
        'pants::strict::coat|비즈니스 롱 패딩|black|down;outer|수트 재킷|charcoal|winter_wool|charcoal_winter;top|드레스 셔츠|light_blue|cotton;bottom|수트 바지|charcoal|winter_wool|charcoal_winter;tie|레지멘탈 타이|navy_burgundy|silk;shoes|더비 구두|black|leather'),
    'female-spring-casual': (
        'pants::::outer|블루종|beige|cotton;top|긴팔 티셔츠|white|cotton;bottom|스트레이트 청바지|denim_blue|denim;shoes|레트로 운동화|gray|suede_mesh',
        'skirt::::outer|가디건|soft_pink|cotton_knit;top|파인 니트|ivory|cotton_knit;bottom|플리츠 스커트|navy|woven;shoes|플랫|beige|leather'),
    'female-spring-business_casual': (
        'pants::::outer|블레이저|navy|wool_blend;top|크루넥 니트|ivory|cotton_knit;bottom|슬랙스|gray|wool_blend;shoes|로퍼|dark_brown|leather',
        'skirt::::mid|가디건|dusty_blue|cotton_knit;top|셔츠|white|cotton;bottom|우븐 스커트|charcoal|woven;shoes|플랫|black|leather'),
    'female-spring-business_formal': (
        'pants::strict::outer|수트 재킷|navy|spring_wool|navy_spring;top|블라우스|white|silk_blend;bottom|수트 바지|navy|spring_wool|navy_spring;shoes|펌프스|black|leather',
        'skirt::strict::outer|수트 재킷|gray|spring_wool|gray_spring;top|블라우스|soft_pink|silk_blend;bottom|수트 스커트|gray|spring_wool|gray_spring;shoes|닫힌 로퍼|black|leather'),
    'female-summer-casual': (
        'pants::::top|반팔 티셔츠|white|cotton;bottom|버뮤다 반바지|navy|cotton;shoes|캔버스 운동화|gray|canvas',
        'dress::::dress|반팔 원피스|dusty_blue|linen_blend;shoes|스트랩 샌들|brown|leather'),
    'female-summer-business_casual': (
        'pants::::top|반팔 니트|ivory|cotton_knit;bottom|슬랙스|navy|summer_wool;shoes|로퍼|dark_brown|leather',
        'skirt::::top|반팔 블라우스|light_blue|cotton;bottom|우븐 스커트|gray|woven;shoes|플랫|black|leather'),
    'female-summer-business_formal': (
        'pants::strict::outer|수트 재킷|light_gray|summer_wool|gray_summer;top|블라우스|white|silk_blend;bottom|수트 바지|light_gray|summer_wool|gray_summer;shoes|펌프스|black|leather',
        'dress::dress_jacket::outer|경량 재킷|navy|summer_wool;dress|반팔 정장 원피스|navy|summer_wool;shoes|플랫|black|leather'),
    'female-autumn-casual': (
        'pants::::outer|블루종|olive|cotton;top|크루넥 니트|cream|wool_knit;bottom|스트레이트 청바지|dark_denim|denim;shoes|스웨이드 운동화|brown|suede',
        'skirt::::outer|가디건|burgundy|wool_knit;top|긴팔 티셔츠|ivory|cotton;bottom|플리츠 스커트|charcoal|woven;shoes|앵클부츠|black|leather'),
    'female-autumn-business_casual': (
        'pants::::outer|블레이저|navy|wool_blend;top|크루넥 니트|ivory|wool_knit;bottom|슬랙스|gray|wool_blend;shoes|로퍼|dark_brown|leather',
        'skirt::::mid|가디건|burgundy|wool_knit;top|셔츠|white|cotton;bottom|우븐 스커트|navy|woven;shoes|플랫|black|leather'),
    'female-autumn-business_formal': (
        'pants::strict::outer|수트 재킷|navy|autumn_wool|navy_autumn;top|블라우스|white|silk_blend;bottom|수트 바지|navy|autumn_wool|navy_autumn;shoes|펌프스|black|leather',
        'dress::dress_jacket::outer|정장 재킷|charcoal|autumn_wool;dress|정장 원피스|burgundy|autumn_wool;shoes|플랫|black|leather'),
    'female-winter-casual': (
        'pants::::outer|숏 패딩|navy|down;top|터틀넥 니트|cream|wool_knit;bottom|기모 캐주얼 팬츠|charcoal|fleece_cotton;shoes|가죽 운동화|black|leather',
        'dress::::coat|울 코트|camel|wool;dress|니트 원피스|burgundy|wool_knit;leg_layer|기모 타이츠|charcoal|fleece;shoes|앵클부츠|dark_brown|leather'),
    'female-winter-business_casual': (
        'pants::::coat|울 코트|navy|wool;top|크루넥 니트|gray|wool_knit;bottom|슬랙스|charcoal|wool;shoes|로퍼|black|leather',
        'skirt::::outer|비즈니스 패딩|black|down;mid|가디건|burgundy|wool_knit;top|파인 니트|ivory|wool_knit;bottom|우븐 스커트|navy|wool;leg_layer|기모 타이츠|charcoal|fleece;shoes|앵클부츠|black|leather'),
    'female-winter-business_formal': (
        'pants::strict::coat|울 코트|charcoal|wool;outer|수트 재킷|navy|winter_wool|navy_winter;top|블라우스|white|silk_blend;bottom|수트 바지|navy|winter_wool|navy_winter;shoes|펌프스|black|leather',
        'skirt::strict::coat|울 코트|navy|wool;outer|수트 재킷|charcoal|winter_wool|charcoal_winter;top|블라우스|light_blue|silk_blend;bottom|수트 스커트|charcoal|winter_wool|charcoal_winter;leg_layer|기모 타이츠|black|fleece;shoes|닫힌 로퍼|black|leather'),
}


def _build_catalog():
    result = []
    for key, pair in RAW_LOOKS.items():
        gender, season, tpo = key.split('-', 2)
        for role, raw in zip(ROLES, pair):
            result.append({'id': f'{key}-{role}', 'gender': gender, 'season': season,
                           'tpo': tpo, 'look_role': role, 'status': 'owner_review_pending',
                           'selection_mode': 'whole_template_only',
                           'age_policy': 'soft_preference_no_exclusion', **_look(raw)})
    return tuple(result)


TEMPLATES = _build_catalog()


def templates_for(gender, season, tpo):
    return tuple(t for t in TEMPLATES if (t['gender'],t['season'],t['tpo']) == (gender,season,tpo))


def validate_catalog():
    errors = []
    expected = {(g,s,t) for g in GENDERS for s in SEASONS for t in TPOS}
    if {(t['gender'],t['season'],t['tpo']) for t in TEMPLATES} != expected:
        errors.append('all 24 scopes are required')
    if len(TEMPLATES) != 48 or len({t['id'] for t in TEMPLATES}) != 48:
        errors.append('48 unique templates are required')
    counts = Counter((t['gender'],t['season'],t['tpo'],t['look_role']) for t in TEMPLATES)
    if any(counts[(g,s,t,r)] != 1 for g,s,t in expected for r in ROLES):
        errors.append('each scope needs one Daily and one Trend')
    for template in TEMPLATES:
        items, tid = template['items'], template['id']
        categories = [i['category'] for i in items]
        if categories.count('shoes') != 1:
            errors.append(f'{tid}: one shoe entry required')
        if 'dress' in categories and 'bottom' in categories:
            errors.append(f'{tid}: dress and bottom cannot coexist')
        if 'dress' not in categories and 'top' not in categories:
            errors.append(f'{tid}: top or dress required')
        if template['tpo'] != 'casual' and {'버뮤다 반바지','스트랩 샌들'} & {i['label'] for i in items}:
            errors.append(f'{tid}: casual-only item in workwear')
        if template['gender']=='male' and template['tpo']=='business_formal':
            if next(i for i in items if i['category']=='shoes')['label'] not in {'옥스퍼드 구두','더비 구두'}:
                errors.append(f'{tid}: invalid male formal shoes')
            suit = [i for i in items if i.get('suit_group')]
            if len(suit) != 2 or len({(i['suit_group'],i['color'],i['material']) for i in suit}) != 1:
                errors.append(f'{tid}: suit mismatch')
        if template['gender']=='male':
            bottom = next((i for i in items if i['category']=='bottom'), None)
            if bottom is None or bottom['color'] not in PRACTICAL_MALE_BOTTOM_COLORS:
                errors.append(f'{tid}: impractical male bottom color')
        if 'accessory' in categories:
            errors.append(f'{tid}: accessories must not be forced into a look')
        if template['season']=='winter' and not {'outer','coat'} & set(categories):
            errors.append(f'{tid}: winter outer required')
    if errors:
        raise ValueError('; '.join(errors))
    return True
