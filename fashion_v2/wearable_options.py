"""Bounded wardrobe alternatives, evaluated before A/B coverage.

These are conservative product heuristics, not universal colour laws. Original
fortune colours/element labels are never rewritten. A warm ochre pigment may be
shown as camel in Korean although its raw hue family is yellow; that is an
explicit wardrobe-tone mapping, not permission to turn every yellow brown.
"""
from copy import deepcopy
from itertools import combinations

WARM_EARTH_HEX = frozenset({
    '#C5A56E', '#D6B43E', '#E2B540', '#EBD3A2', '#EEB480', '#F3A257',
})
TONE_KEYS = {
    'blue': ('navy', 'denim', 'sky'),
    'red': ('pink', 'burgundy', 'pale_pink'),
    'green': ('sage', 'forest', 'olive'),
    'teal': ('teal', 'forest', 'sage', 'olive'),
    'purple': ('lavender', 'purple'),
    'brown': ('beige', 'brown'),
    'gray': ('light_gray', 'gray', 'charcoal'),
    'white': ('white', 'ivory'), 'black': ('black',), 'yellow': ('butter',),
}


SHOE_COLOR_ALIASES = {
    'dark_brown': 'brown', 'dark_denim': 'navy', 'denim_blue': 'denim',
    'cream': 'ivory', 'light_gray': 'gray', 'light_blue': 'sky',
}
SNEAKER_COLOR_RANGES = {
    'casual': {
        'spring': ('white', 'ivory', 'gray', 'beige', 'navy', 'brown'),
        'summer': ('white', 'ivory', 'gray', 'beige', 'navy'),
        'autumn': ('ivory', 'gray', 'beige', 'brown', 'navy', 'olive', 'burgundy', 'white'),
        'winter': ('gray', 'black', 'navy', 'brown', 'burgundy', 'ivory', 'white'),
    },
    'business_casual': {
        'spring': ('white', 'ivory', 'gray', 'navy', 'beige', 'brown'),
        'summer': ('white', 'ivory', 'gray', 'navy', 'beige'),
        'autumn': ('ivory', 'gray', 'navy', 'brown', 'beige', 'black'),
        'winter': ('gray', 'black', 'navy', 'brown', 'ivory'),
    },
}


def wardrobe_tones(color):
    if color['hex'].upper() in WARM_EARTH_HEX:
        return ('beige', 'camel', 'brown')
    return TONE_KEYS.get(color['family'], ())


def tone_explanation(color):
    if color['hex'].upper() in WARM_EARTH_HEX:
        return '카멜·오커 계열을 베이지·브라운의 착장용 톤으로 조정'
    if color['family'] == 'teal':
        return '청록·초록 범위에서 채도를 낮춘 그린·올리브 착장용 톤 적용'
    return '전체 착장의 배색을 비교해 같은 계열의 착장용 톤 적용'


def muted_green_bottom(color):
    return (color['family'] == 'green' and color['saturation'] <= .30
            and .20 <= color['lightness'] <= .75)


def _shoe_source_key(item):
    key = SHOE_COLOR_ALIASES.get(item.get('color'), item.get('color'))
    return key if key else item.get('base_color')


def sneaker_color_keys(look, item):
    """Return a bounded real-world sneaker range for this TPO and season.

    The source template colour stays a candidate. Casual has the broadest range;
    business casual stays restrained. Business formal never gets a sneaker
    colour override here. These are candidate ranges, not mandatory colours.
    """
    if item.get('label') != '운동화':
        return ()
    ranges = SNEAKER_COLOR_RANGES.get(look['tpo'])
    if not ranges:
        return ()
    keys = list(ranges[look['season']])
    source = _shoe_source_key(item)
    material = item.get('material', '')
    if source:
        keys.insert(0, source)
    # Suede is commonly used in earthy/grey/olive tones; leather can carry
    # cleaner black/navy/white. This only changes candidate order.
    if 'suede' in material:
        preferred = ['brown', 'gray', 'beige', 'olive', 'navy', 'ivory']
        keys = preferred + keys
    elif 'leather' in material:
        preferred = ['white', 'ivory', 'black', 'navy', 'gray', 'brown']
        keys = preferred + keys
    return tuple(dict.fromkeys(keys))


def shoe_color_options(look, palette):
    """Yield the existing shoe plus TPO/season/material-appropriate colours."""
    yield look
    shoe_index = next((n for n, i in enumerate(look['items'])
                       if i['category'] == 'shoes' and i['label'] == '운동화'), None)
    if shoe_index is None:
        return
    source_key = _shoe_source_key(look['items'][shoe_index])
    current_hex = look['items'][shoe_index].get('hex', '').upper()
    for key in sneaker_color_keys(look, look['items'][shoe_index]):
        if key not in palette:
            continue
        c = palette[key]
        if c['hex'].upper() == current_hex:
            continue
        alt = deepcopy(look)
        item = alt['items'][shoe_index]
        item.update(base_color=key, color_name=c['name'], hex=c['hex'],
                    color_relation='base', shoe_color_origin=(
                        'template_source' if key == source_key else 'tpo_season_range'),
                    selection_reason='TPO·계절·소재와 전체 배색을 함께 비교한 운동화 색상 후보')
        alt.setdefault('selection_changes', []).append({
            'from': look['items'][shoe_index].get('color_name', '기존 운동화 색상'),
            'to': c['name'],
            'reason': '화이트 고정 대신 TPO·계절·소재·전체 색수 안에서 운동화 색상 비교',
        })
        yield alt


def _bottom_options(look, palette):
    yield look
    if look['tpo'] != 'casual':
        return
    denim = next((n for n, i in enumerate(look['items'])
                  if i['category'] == 'bottom' and i['label'] == '데님 바지'), None)
    if denim is None:
        return
    alt = deepcopy(look)
    item = alt['items'][denim]
    old = item['label']
    band = look.get('weather_fit', {}).get('thermal_band')
    cold = band in {'cold', 'freezing'} or (not band and look['season'] == 'winter')
    hot = band in {'warm', 'hot', 'very_hot'} or (not band and look['season'] == 'summer')
    base = 'charcoal' if cold else 'beige'
    c = palette[base]
    item.update(label='면바지', base_color=base, color=base,
                color_name=c['name'], hex=c['hex'], color_relation='base',
                material='winter_cotton' if cold else 'light_cotton' if hot else 'cotton_twill',
                selection_reason='동일한 날씨·착장 안에서 데님과 면바지를 함께 비교')
    alt.setdefault('selection_changes', []).append({
        'from': old, 'to': '면바지',
        'reason': '추천색을 상의에 몰지 않고 하의까지 자연스럽게 활용할 후보 비교',
    })
    yield alt


def garment_options(look, palette):
    """Compare bounded garment and sneaker-colour alternatives before A/B use.

    Reviewed/explicitly targeted looks stay immutable. Otherwise casual denim
    may compete with cotton pants and sneakers may use a bounded TPO/season
    colour range. No option adds a new Five Elements colour.
    """
    if look.get('review_preference') or look.get('color_targets'):
        yield look
        return
    for base in _bottom_options(look, palette):
        yield from shoe_color_options(base, palette)


def footwear_color_score(items, look, describe, visible_color_count=None, previous_hex=None):
    """Soft ranking for sneaker colour inside the whole outfit.

    Shoes are larger than jewellery, so a new shoe colour is allowed only as a
    restrained fourth colour when the clothing itself is calm. Repeating the
    previous recommendation's sneaker gets a small penalty, never a hard ban.
    """
    shoe = next((i for i in items if i['category'] == 'shoes'), None)
    if not shoe or shoe.get('label') != '운동화':
        return {'score': 0, 'reasons': [], 'basis': 'not_sneakers'}

    sc = describe({'hex': shoe['hex']})
    sf = 'green' if sc['family'] == 'teal' else sc['family']
    if shoe['hex'].upper() in WARM_EARTH_HEX:
        sf = 'brown'
    neutral = sf in {'white', 'gray', 'black'}
    score, reasons = 0, []

    clothing = []
    for item in items:
        if item['category'] not in {'top', 'bottom', 'dress', 'outer', 'coat', 'mid'}:
            continue
        if item.get('wear_mode') == 'carry':
            continue
        cc = describe({'hex': item['hex']})
        fam = 'green' if cc['family'] == 'teal' else cc['family']
        if item['hex'].upper() in WARM_EARTH_HEX:
            fam = 'brown'
        chroma = 2 * min(cc['lightness'], 1-cc['lightness']) * cc['saturation']
        clothing.append((item, cc, fam, chroma))

    strong = [x for x in clothing if x[2] not in {'white', 'gray', 'black'} and x[3] > .30]
    if len(strong) >= 2:
        if neutral or sc['saturation'] < .24:
            score += 8
            reasons.append('의복의 강한 색이 이미 둘 이상이라 신발은 안정색 우선')
        else:
            score -= 10
            reasons.append('의복색이 많은 상태에서 신발까지 강한 색으로 늘어남')
    elif not neutral and sc['saturation'] <= .58:
        score += 2
        reasons.append('의복색이 정돈되어 차분한 컬러 운동화 허용')

    families = [x[2] for x in clothing]
    if sf in families:
        score += 5 if sf not in {'white', 'gray', 'black'} else 2
        reasons.append('상의·하의·아우터 중 한 색 계열과 신발을 연결')
    bottom = next((x for x in clothing if x[0]['category'] == 'bottom'), None)
    if bottom and shoe['hex'].upper() == bottom[0]['hex'].upper() and sf not in {'white', 'gray', 'black'}:
        score -= 5
        reasons.append('하의와 신발의 완전 동일색 반복은 약하게 감점')

    if look['tpo'] == 'casual':
        seasonal = {
            'spring': {'white', 'gray', 'brown', 'blue'},
            'summer': {'white', 'gray', 'brown', 'blue'},
            'autumn': {'gray', 'brown', 'blue', 'green'},
            'winter': {'black', 'gray', 'brown', 'blue'},
        }[look['season']]
        if sf in seasonal:
            score += 3
            reasons.append('계절에 자주 쓰는 운동화 색 계열')
        if look['season'] == 'winter' and sf == 'white':
            score -= 1
    elif look['tpo'] == 'business_casual':
        if sf in {'white', 'gray', 'black', 'brown', 'blue'} and sc['saturation'] <= .62:
            score += 4
            reasons.append('비즈니스 캐주얼에서 단정한 운동화 색 범위')

    # Preserve a researched template's original footwear colour as a useful
    # prior, without forcing it when the full outfit scores worse.
    if shoe.get('shoe_color_origin') == 'template_source':
        score += 3
        reasons.append('원래 착장 템플릿의 신발 색상')

    if visible_color_count == 4 and len(strong) <= 1 and sc['saturation'] <= .58:
        score += 8
        reasons.append('차분한 신발색을 네 번째 색으로 제한적으로 허용')

    if previous_hex and shoe['hex'].upper() == previous_hex.upper():
        score -= 6
        reasons.append('추천 1·2의 동일 운동화 색 반복을 약하게 감점')

    return {'score': score, 'reasons': reasons,
            'basis': 'tpo_season_material_whole_outfit_soft_ranking'}


def outfit_balance(items, describe, enabled=True):
    """Rank competing colour blocks before rewarding daily-colour coverage.

Two upper colours are NOT forbidden. Tonal, low-chroma and small-detail
combinations remain valid. This only flags multiple strong, unrelated fabric
blocks in the same outfit. Numeric thresholds are implementation heuristics.
    """
    if not enabled:
        return {'risk': 0, 'reasons': [], 'basis': 'existing_review_or_tpo'}
    clothing = []
    for item in items:
        if item['category'] not in {'top', 'bottom', 'dress', 'outer', 'coat', 'mid'}:
            continue
        if item.get('wear_mode') == 'carry':
            continue
        c = describe({'hex': item['hex']})
        if c['family'] in {'white', 'gray', 'black'}:
            continue
        chroma = 2 * min(c['lightness'], 1-c['lightness']) * c['saturation']
        family = 'green' if c['family'] == 'teal' else c['family']
        if c['hex'].upper() in WARM_EARTH_HEX:
            family = 'brown'
        clothing.append((item['category'], family, chroma, c['lightness']))
    strong = [c for c in clothing if c[2] > .30 and c[3] > .20]
    # A pale sky/denim can support one statement colour. Two strongly coloured
    # blocks from different families compete even after swapping their slots.
    conflicting = [(a, b) for a, b in combinations(strong, 2) if a[1] != b[1]]
    reasons = []
    if conflicting:
        reasons.append('서로 다른 강한 의복색이 동시에 큰 면적을 차지함')
    upper = {'top', 'outer', 'coat', 'mid'}
    if any(a[0] in upper and b[0] in upper for a, b in conflicting):
        reasons.append('강한 두 색이 상체 레이어에 집중됨')
    return {'risk': len(reasons), 'reasons': reasons,
            'basis': 'whole_outfit_colour_blocks_not_aesthetic_approval'}
