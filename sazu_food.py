"""Opt-in SAZU food trial. Provider results are not rescored or made into meals.

Contract: https://www.sazu.app/manse-api/docs (2026-10-01, v2).
Live contract verification is required before enabling an account.
"""
import json
import hashlib
import logging
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def provider_for(user_id):
    # Reuse the existing server-approved testers once the paid key is installed.
    # An explicit empty override still disables the trial for rollback.
    configured = os.getenv('SAZU_FOOD_TRIAL_USERS')
    if configured is None:
        configured = os.getenv('DALHA_TEST_USER_IDS', '') if os.getenv('SAZU_API_KEY', '').strip() else ''
    allowed = {x.strip() for x in configured.split(',') if x.strip()}
    return 'sazu' if user_id and user_id in allowed else 'offline'


def build_request(profile, day):
    born = profile.birth_date
    clock = None if profile.time_unknown else profile.birth_time
    request = dict(birthYear=born.year, birthMonth=born.month, birthDay=born.day,
                   birthHour=clock.hour if clock else None,
                   birthMinute=clock.minute if clock else 0,
                   isFemale=profile.gender == 'female',
                   isLunar=profile.calendar_type == 'lunar',
                   isLeapMonth=bool(profile.is_leap_month), date=str(day),
                   foodRotation='daily', locale='ko', detail='full')
    # No guessed birth city or double solar-time correction. Missing city uses
    # the provider's documented Seoul default, displayed in the trial note.
    if profile.birth_place:
        request['birthCity'] = profile.birth_place
    return request


def profile_key(profile):
    # Date-independent cache scope, invalidated when saved birth inputs change.
    body = build_request(profile, '')
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


def _validate_balance(balance):
    if not isinstance(balance, dict) or not isinstance(balance.get('basket'), dict) or not balance['basket']:
        raise ValueError('foodBalance missing')
    if not isinstance(balance.get('disclaimer'), str) or not balance['disclaimer'].strip():
        raise ValueError('disclaimer missing')
    for field in ('cautions', 'why'):
        if not isinstance(balance.get(field), list) or not all(isinstance(x, str) for x in balance[field]):
            raise ValueError('unsupported text field')
    def items(value):
        values = value if isinstance(value, list) else [value] if value else []
        for item in values:
            if not isinstance(item, dict) or not isinstance(item.get('name'), str) or not isinstance(item.get('reason', ''), str):
                raise ValueError('unsupported basket item')
    basket = balance['basket']
    grains = basket.get('grains', {})
    if not isinstance(grains, dict):
        raise ValueError('unsupported grains')
    items(grains.get('staple'))
    items(grains.get('mix'))
    for field in ('soup', 'protein', 'sides', 'drinks', 'snack'):
        items(basket.get(field))
    items(balance.get('avoid'))


def build_set(profile, day):
    key = os.getenv('SAZU_API_KEY', '').strip()
    if not key:
        raise ValueError('SAZU 음식 추천 연결을 준비 중입니다.')
    body = build_request(profile, day)
    request = Request('https://api.sazu.app/v2/sazu/food',
                      data=json.dumps(body).encode('utf-8'), method='POST',
                      headers={'x-api-key': key, 'Content-Type': 'application/json'})
    try:
        # No automatic retry: each successful request consumes quota.
        with urlopen(request, timeout=6) as response:
            raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ValueError('response limit')
        data = json.loads(raw)
        if data.get('success') is False:
            raise ValueError('provider error')
        balance = data['data']['modules']['foodBalance']
        _validate_balance(balance)
        logging.getLogger(__name__).warning('SAZU food request succeeded; response validated')
        # Keep the food result intact. Do not return other private natal modules.
        return dict(provider='sazu', date=str(day), meals=[], food_balance=balance,
                    input_note='' if profile.birth_place else '출생지는 SAZU 기본값인 서울 기준입니다.')
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        logging.getLogger(__name__).warning('SAZU food request failed (%s, status=%s)',
            type(exc).__name__, exc.code if isinstance(exc, HTTPError) else 'n/a')
        # Do not echo provider payloads, birth details, keys or error bodies.
        raise ValueError('SAZU 음식 추천을 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.') from None
