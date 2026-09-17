"""Bounded whole-look comparisons, not a claim of objective aesthetic quality.

Keep both daily colours when the outfit supports them. Do not turn two large
upper-body accents into a rule violation: only competing, saturated hues get a
ranking penalty. Denim and weather-equivalent chinos are compared explicitly.
"""
from copy import deepcopy
from itertools import combinations

VERSION = 'wearable-balance-1'


def related_families(source, actual):
    """Only the reviewed blue-green -> muted green bridge crosses hue families."""
    return source == actual or (source == 'teal' and actual == 'green')


def balance_penalty(items, describe):
    upper = [i for i in items if i['category'] in {'outer', 'coat', 'mid', 'top', 'dress'}
             and i.get('wear_mode', 'worn') != 'carry']
    penalty = 0
    for left, right in combinations(upper, 2):
        a, b = describe({'hex': left['hex']}), describe({'hex': right['hex']})
        if a['family'] == b['family']:
            continue
        if {a['family'], b['family']} & {'black', 'white', 'gray'}:
            continue
        # Muted earth/green pairings remain available. A loud colour directly
        # beside another substantial chromatic layer must compete with calmer
        # tones and with moving one colour to the trousers.
        if (min(a['saturation'], b['saturation']) > .28
                and max(a['saturation'], b['saturation']) > .60
                and all(.18 < c['lightness'] < .82 for c in (a, b))):
            penalty += 1
    return penalty


def outfit_options(look):
    """Retain the source outfit; add at most one weather-equivalent alternative.

Never dye denim beige/khaki, break a suit, replace a skirt, remove an outer
layer, or reinterpret an explicit reviewed combination.
    """
    yield look
    if look['tpo'] == 'business_formal' or look.get('review_preference') or look.get('color_targets'):
        return
    index = next((n for n, i in enumerate(look['items'])
                  if i['category'] == 'bottom' and i['label'] == '데님 바지'
                  and not i.get('suit_group')), None)
    if index is None:
        return
    alternative = deepcopy(look)
    item = alternative['items'][index]
    band = look.get('weather_fit', {}).get('thermal_band')
    cold = band in {'cold', 'freezing'} or (not band and look['season'] == 'winter')
    hot = band in {'warm', 'hot', 'very_hot'} or (not band and look['season'] == 'summer')
    item.update(label='면바지', material='fleece_cotton' if cold else 'light_cotton' if hot else 'cotton_twill',
                base_color='beige' if look['recommendation_number'] == 1 and not cold else 'charcoal')
    alternative.setdefault('selection_changes', []).append({
        'from': '데님 바지', 'to': '면바지',
        'reason': '청바지를 고정하지 않고 같은 계절·TPO의 면바지 착장도 비교'})
    alternative['structural_alternative'] = 'weather_equivalent_chinos'
    yield alternative
