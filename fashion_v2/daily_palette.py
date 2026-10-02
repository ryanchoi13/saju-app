"""Daily symbolic colors, independent of historical two-color pair catalogs.

The element labels reuse DALHA's registered wardrobe palette. These are
product correspondences, not a promise that wearing a color changes fortune.
"""
from copy import deepcopy
import json
from pathlib import Path

VERSION = 'daily-wardrobe-palette-1'
PALETTE = json.loads(Path(__file__).with_name('approved_palette.json').read_text())
ELEMENTS = {'木': '목', '火': '화', '土': '토', '金': '금', '水': '수'}
TPO_LABELS = {'casual': '캐주얼', 'business_casual': '비즈니스 캐주얼', 'business_formal': '비즈니스 포멀'}


def select_daily_palette(primary_element, secondary_element, date_key):
    """Rotate registered colors independently; no Wada pair is a prerequisite."""
    chosen = []
    for n, element in enumerate((primary_element, secondary_element)):
        if element not in ELEMENTS:
            raise ValueError('Supported color element required')
        pool = [c for c in PALETTE.values() if c['element'] == ELEMENTS[element]
                and (not chosen or c['hex'] != chosen[0]['hex'])]
        seed = int(date_key) + list(ELEMENTS).index(element) * 17 + n * 31
        color = deepcopy(pool[seed % len(pool)])
        color.update(name_ko=color['name'], standard_color=color['name'],
                     role='추천색 ' + ('A' if n == 0 else 'B'))
        chosen.append(color)
    return dict(version=VERSION, theme='오늘의 추천색', mode='harmony',
                source='registered_wardrobe_colors_by_core_elements',
                target_elements=[primary_element, secondary_element],
                top=chosen[0], bottom=chosen[1], point=None,
                mood_desc='전체 옷차림의 조화를 우선하고, 오늘 추천색은 자연스럽게 활용해 보세요.')


def optional_wada_reference(colors):
    """Attach source metadata after selection; never change eligibility or rank."""
    try:
        from wada_color_rules import WADA_DUOS
    except ImportError:
        return dict(role='optional_reference', matching_duos=[], available=False)
    pair = {c['hex'].upper() for c in colors}
    matches = [n for n, d in WADA_DUOS.items()
               if {d['a']['hex'].upper(), d['b']['hex'].upper()} == pair]
    return dict(role='optional_reference', matching_duos=matches, available=True)


def style_palette_contexts(palette, gender, age):
    if age is None:
        band = '30s'
    elif age < 20:
        band = '10s'
    elif age < 60:
        band = f'{int(age)//10*10}s'
    else:
        band = '60plus'
    return {tpo: dict(deepcopy(palette), tpo=tpo, gender=gender,
                      age_band=band, style_mood=tpo, mood_tag=label)
            for tpo, label in TPO_LABELS.items()}


def private_color_hint(unresolved):
    """Optional text only: never add an item, placement, or visible color."""
    unique = list({c['hex'].upper(): c for c in unresolved}.values())
    if not unique:
        return None
    names = ' 또는 '.join(c['name'] for c in unique)
    return dict(kind='underwear', optional=True, visible=False,
                colors=[dict(role=c['role'], name=c['name'], hex=c['hex']) for c in unique],
                text=f'오늘 추천색인 {names} 계열을 옷차림에 넣기 부담스럽다면, 원하실 때 속옷처럼 겉으로 드러나지 않는 곳에 활용해 보세요. 나만 아는 색으로 기분을 내는 방법도 있어요.')
