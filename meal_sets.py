"""Single-day meal sets from the reviewed offline food engine."""
from dalha_food.app_adapter import recommend_for_profile


def build_set(profile, day, mode, history=(), exclude_ids=()):
    try:
        result = recommend_for_profile(profile, day, mode=mode, history=history, exclude_ids=exclude_ids)
    except AssertionError:
        raise ValueError('조건에 맞는 다른 세트를 찾지 못했습니다. 현재 세트를 유지합니다.') from None
    plan = result['plans'][0]
    if plan['within_calorie_band'] is False:
        raise ValueError('열량 범위에 맞는 새 세트를 찾지 못했습니다. 현재 세트를 유지합니다.')
    return plan
