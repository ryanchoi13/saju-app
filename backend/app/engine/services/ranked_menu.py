"""Rank food ideas by the existing core direction; do not prescribe meals.

The element score is the first sorting key. Familiarity and daily tie breaking
cannot push a lower element score ahead of a higher one. Core uncertainty stays
intact: when no positive direction is confirmed, use the existing daily-symbol
fallback and label that basis explicitly.
"""
import hashlib
from .daily_menu import MENU_POOL, DIET_MENU_POOL, season_for

VERSION = 'ranked-menu-v1'
LIMITS = {'general': 10, 'diet': 5}


def build_rankings(birth, day, weights, daily_element, confidence):
    scores = {element: int(weights.get(element, 0)) for element in '木火土金水'}
    confirmed = any(score > 0 for score in scores.values())
    if not confirmed:
        # Never turn a caution/conflicting direction into a confirmed favorable one.
        if daily_element not in weights:
            scores[daily_element] = 1
    basis = ('core_direction' if confirmed else
             'daily_symbol' if scores.get(daily_element, 0) > 0 else 'core_caution')
    text = ('사주의 보완 방향과 오늘의 흐름을 참고해 추천 순서로 골랐습니다.' if confirmed
            else '오늘의 일진을 참고해 추천 순서로 골랐습니다.' if basis == 'daily_symbol'
            else '사주에서 주의할 방향을 참고해 골랐습니다.')
    identity = birth.model_dump_json(exclude={'name'})
    seed = f'{VERSION}|{identity}|{day}'
    season = season_for(day.month)
    rankings = {}
    for mode, pool in (('general', MENU_POOL), ('diet', DIET_MENU_POOL)):
        # A negative direction is not a reason to keep extending the recommendation.
        candidates = [item for item in pool if scores[item.element] >= 0]
        def key(item):
            everyday = (item.popularity, item.familiarity, item.accessibility,
                        int(season in item.seasons))
            tie = hashlib.sha256(f'{seed}|{mode}|{item.name}'.encode()).hexdigest()
            return (-scores[item.element], *(-value for value in everyday), tie, item.name)
        ordered = sorted(candidates, key=key)[:LIMITS[mode] * 2]
        ordered = ordered[:len(ordered)//2*2]
        rankings[mode] = [dict(menu=item.name, rank=i+1, element=item.element,
                               element_score=scores[item.element]) for i, item in enumerate(ordered)]
    return dict(version=VERSION, date=str(day), rankings=rankings,
                basis=basis, basis_text=text, confidence=confidence,
                element_scores=scores, pool_sizes={'general':len(MENU_POOL), 'diet':len(DIET_MENU_POOL)})
