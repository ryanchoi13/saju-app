from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from main import app
from zodiac_daily import ZODIACS, STAR_PROFILES, build_daily_zodiac, korean_today

SIGNS = [('zodiac', key) for key in ZODIACS] + [('star', key) for key in STAR_PROFILES]


@pytest.mark.parametrize('kind,key', SIGNS)
def test_thirty_days_have_distinct_content_and_same_day_is_stable(kind, key):
    first = date(2026, 9, 21)
    days = [build_daily_zodiac(kind, key, first + timedelta(days=i)) for i in range(30)]
    for field in ('title', 'overview', 'focus_content'):
        assert len({day[field] for day in days}) == 30, (kind, key, field)
    for i, result in enumerate(days):
        assert result == build_daily_zodiac(kind, key, first + timedelta(days=i))
        assert 70 <= result['score'] <= 96
        assert result['date'] == (first + timedelta(days=i)).isoformat()
        assert result['timezone'] == 'Asia/Seoul'
    if kind == 'zodiac':
        for row in range(4):
            assert len({day['year_tips'][row]['tip'] for day in days}) == 30
            assert len({day['year_tips'][row]['year_label'] for day in days}) == 1
    else:
        assert len({day['star_element'] for day in days}) == 1
        assert len({day['star_planet'] for day in days}) == 1


@pytest.mark.parametrize('first', [date(2026, 12, 31), date(2028, 2, 28), date(2028, 2, 29)])
def test_year_month_and_leap_day_boundaries(first):
    for kind, key in SIGNS:
        before = build_daily_zodiac(kind, key, first)
        after = build_daily_zodiac(kind, key, first + timedelta(days=1))
        assert before['overview'] != after['overview']
        assert before['title'] != after['title']


def test_korean_civil_midnight_not_server_utc_midnight():
    assert korean_today(datetime(2026, 9, 21, 14, 59, 59, tzinfo=timezone.utc)) == date(2026, 9, 21)
    assert korean_today(datetime(2026, 9, 21, 15, 0, 0, tzinfo=timezone.utc)) == date(2026, 9, 22)


@pytest.mark.parametrize('kind,key', [('star', '물고기자리'), ('zodiac', '말')])
def test_endpoint_uses_current_date_and_prevents_stale_cache(kind, key):
    client = TestClient(app)
    with patch('zodiac_daily.korean_today', return_value=date(2026, 9, 21)):
        today = client.get('/api/zodiac-fortune', params={'type':kind, 'key':key})
        again = client.get('/api/zodiac-fortune', params={'type':kind, 'key':key})
    with patch('zodiac_daily.korean_today', return_value=date(2026, 9, 22)):
        tomorrow = client.get('/api/zodiac-fortune', params={'type':kind, 'key':key})
    assert today.status_code == tomorrow.status_code == 200
    assert today.headers['cache-control'] == 'no-store'
    assert today.json() == again.json()
    assert today.json()['overview'] != tomorrow.json()['overview']
    assert tomorrow.json()['date'] == '2026-09-22'


@pytest.mark.parametrize('kind,key', [('other','말'), ('star','말'), ('zodiac','<script>')])
def test_invalid_signs_are_rejected_instead_of_fabricating_a_fallback(kind, key):
    result = TestClient(app).get('/api/zodiac-fortune', params={'type':kind, 'key':key})
    assert result.status_code == 422
