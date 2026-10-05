"""Opt-in research collector. No public route, UI changes, or menu history writes.

Uses the existing server key; only foodBalance leaves the response envelope.
Monthly plans are observed coverage, never claimed to be the complete catalogue.
"""
import hashlib
import json
import logging
import os
import threading
import time
from datetime import date, datetime, timezone
from urllib.request import Request, urlopen

from wardrobe_store import _connection, _execute

API = 'https://api.sazu.app'
LOG = logging.getLogger(__name__)
BIRTH_FIELDS = ('birthYear', 'birthMonth', 'birthDay', 'birthHour', 'birthMinute',
                'isFemale', 'isLunar', 'isLeapMonth', 'birthCity')


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def request_key(body):
    return hashlib.sha256(('sazu-food-monthly-v1:' + _json(body)).encode()).hexdigest()


def initialize():
    with _connection() as (conn, pg):
        if pg:
            _execute(conn, pg, 'SELECT pg_advisory_xact_lock(74201933)')
        _execute(conn, pg, '''CREATE TABLE IF NOT EXISTS sazu_food_research (
            request_key VARCHAR(64) PRIMARY KEY, requested_on VARCHAR(10) NOT NULL,
            request_json TEXT NOT NULL, state VARCHAR(16) NOT NULL,
            food_balance TEXT, received_at VARCHAR(40), error_kind VARCHAR(80))''')
        _execute(conn, pg, '''CREATE TABLE IF NOT EXISTS sazu_food_observations (
            request_key VARCHAR(64) NOT NULL REFERENCES sazu_food_research(request_key),
            source_path TEXT NOT NULL, food_id TEXT NOT NULL, food_name TEXT NOT NULL,
            raw_item TEXT NOT NULL, PRIMARY KEY(request_key, source_path))''')


def claim(body):
    # Committed before contacting SAZU: restarts cannot silently spend quota twice.
    # A crash leaves "claimed" for manual review, never automatic retry.
    key = request_key(body)
    with _connection() as (conn, pg):
        count = _execute(conn, pg, '''INSERT INTO sazu_food_research
            (request_key,requested_on,request_json,state) VALUES(%s,%s,%s,%s)
            ON CONFLICT(request_key) DO NOTHING''',
            (key, body['date'], _json(body), 'claimed')).rowcount
    return key, count == 1


def food_items(balance):
    def walk(value, path):
        if isinstance(value, list):
            for i, item in enumerate(value):
                yield from walk(item, f'{path}[{i}]')
        elif isinstance(value, dict):
            if isinstance(value.get('id'), str) and isinstance(value.get('name'), str):
                yield path, value
            else:
                for name, item in value.items():
                    yield from walk(item, f'{path}.{name}' if path else name)
    # Preserve unknown fields in the full balance; index only food-bearing roots.
    for root in ('basket', 'avoid', 'plan', 'seasonal'):
        yield from walk(balance.get(root), root)


def save_response(key, balance):
    if not isinstance(balance, dict) or not isinstance(balance.get('basket'), dict):
        raise ValueError('Invalid food balance')
    observations = list(food_items(balance))
    with _connection() as (conn, pg):
        for path, item in observations:
            _execute(conn, pg, '''INSERT INTO sazu_food_observations
                (request_key,source_path,food_id,food_name,raw_item) VALUES(%s,%s,%s,%s,%s)
                ON CONFLICT(request_key,source_path) DO NOTHING''',
                (key, path, item['id'], item['name'], _json(item)))
        _execute(conn, pg, '''UPDATE sazu_food_research SET state=%s,
            food_balance=%s,received_at=%s WHERE request_key=%s''',
            ('complete', _json(balance), datetime.now(timezone.utc).isoformat(), key))
    return len({item['id'] for _, item in observations})


def fail_request(key, error):
    # Never save exception text, HTTP response bodies, keys or database URLs.
    kind = type(error).__name__
    with _connection() as (conn, pg):
        _execute(conn, pg, 'UPDATE sazu_food_research SET state=%s,error_kind=%s WHERE request_key=%s',
                 ('failed', kind, key))


def _api(path, body=None):
    key = os.environ['SAZU_API_KEY'].strip()
    request = Request(API + path, data=_json(body).encode() if body is not None else None,
        headers={'x-api-key': key, 'Content-Type': 'application/json'})
    with urlopen(request, timeout=30) as response:
        raw = response.read(8_000_001)
    if len(raw) > 8_000_000:
        raise ValueError('Response too large')
    result = json.loads(raw)
    if result.get('success') is not True or not isinstance(result.get('data'), dict):
        raise ValueError('Invalid API envelope')
    return result


def quota_remaining(envelope):
    data = envelope['data']
    if data.get('tier') == 'free' or data.get('plan', {}).get('kind') == 'free':
        raise ValueError('Live paid response required')
    included = data.get('included') or {}
    count = included.get('remaining', data.get('remaining'))
    if isinstance(count, bool) or not isinstance(count, int):
        raise ValueError('Cannot verify included quota')
    return count


def make_requests(profiles, dates, budget):
    result, seen = [], set()
    for day in dates:
        date.fromisoformat(day)
        for profile in profiles:
            body = {k: profile[k] for k in BIRTH_FIELDS if k in profile}
            body.update(date=day, foodRotation='daily', foodPlan='monthly',
                        foodPromptGuide=True, locale='ko', detail='full')
            key = request_key(body)
            if key not in seen:
                result.append(body)
                seen.add(key)
            if len(result) >= budget:
                return result
    return result


def run(profile_builder, api=_api, sleep=time.sleep):
    # Explicit date and budget, no rolling schedule. Default budget is six food calls.
    dates = [s.strip() for s in os.environ['SAZU_FOOD_COLLECT_DATES'].split(',') if s.strip()]
    if not dates or len(dates) > 12:
        raise ValueError('Use one to twelve explicit dates')
    for day in dates:
        date.fromisoformat(day)
    budget = int(os.getenv('SAZU_FOOD_COLLECT_LIMIT', '6'))
    if not 1 <= budget <= 30:
        raise ValueError('Food call budget must be 1..30')
    key_status = api('/v2/me')
    remaining = quota_remaining(key_status)
    if remaining < budget + 50:
        raise ValueError('Insufficient included quota; preserve normal service allowance')
    rate = key_status['data'].get('rateLimitPerMinute')
    if not isinstance(rate, int) or rate < 1:
        rate = (key_status['data'].get('rateLimit') or {}).get('perMinute', 10)
    if not isinstance(rate, int) or isinstance(rate, bool) or rate < 1:
        raise ValueError('Invalid rate limit')
    delay = max(2.1, 60 / rate + 0.1)
    sleep(delay)
    samples = api('/v2/sazu/samples')['data']['samples']
    profiles = profile_builder() + [s['input'] for s in samples[:5]]
    requests = make_requests(profiles, dates, budget)
    initialize()
    for body in requests:
        key, fresh = claim(body)
        if not fresh:
            continue
        try:
            sleep(delay)
            # Recheck remaining quota before every paid request; no overage spending.
            status = api('/v2/me')
            if quota_remaining(status) <= 50:
                raise ValueError('Included quota reserve reached')
            sleep(delay)
            response = api('/v2/sazu/food', body)
            balance = response['data']['modules']['foodBalance']
            observed = save_response(key, balance)
            if response.get('meta', {}).get('sample') or response['data'].get('meta', {}).get('sample'):
                raise ValueError('Sandbox response cannot establish live coverage')
            if not isinstance(balance.get('plan'), dict) or not balance['plan'].get('days'):
                raise ValueError('Monthly plan absent; raw response retained for diagnosis')
            LOG.warning('SAZU archive: one monthly response saved, %d distinct food IDs', observed)
        except Exception as error:
            fail_request(key, error)
            raise
    LOG.warning('SAZU archive: bounded pass finished; inspect stored request states')


def start(profile_builder):
    if os.getenv('SAZU_FOOD_COLLECT_ENABLED') != '1':
        return
    def work():
        try:
            run(profile_builder)
        except Exception as error:
            LOG.warning('SAZU archive stopped (%s); no automatic retry', type(error).__name__)
    threading.Thread(target=work, name='sazu-food-archive', daemon=True).start()
