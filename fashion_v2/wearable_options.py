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


def garment_options(look, palette):
    """Keep the whole outfit and its weather layers; also compare cotton pants.

No recoloured denim pretending to be beige/khaki cotton. Skirts, suits, shorts,
explicit owner-reviewed combinations and other TPOs are not converted here.
    """
    yield look
    if look['tpo'] != 'casual' or look.get('review_preference') or look.get('color_targets'):
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
