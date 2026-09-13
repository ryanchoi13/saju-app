from fashion_v2.weather_service import WeatherOutfitCache, weather_api_payload


def profile(guidance="낮에는 반팔이 알맞아요."):
    return {
        "location": "경주",
        "location_mode": "fixed_gyeongju",
        "guidance": guidance,
    }


def test_cache_fetches_once_during_ttl_and_returns_defensive_copies():
    cache = WeatherOutfitCache(ttl_seconds=30)
    calls = []

    def fetcher():
        calls.append(True)
        return profile()

    first = cache.get(fetcher, now=100)
    first["guidance"] = "changed"
    second = cache.get(fetcher, now=110)
    assert len(calls) == 1
    assert second["guidance"] == "낮에는 반팔이 알맞아요."


def test_failed_refresh_keeps_last_good_forecast():
    cache = WeatherOutfitCache(ttl_seconds=10, retry_seconds=5)
    cache.get(lambda: profile("정상 예보"), now=100)

    def fail():
        raise TimeoutError()

    assert cache.get(fail, now=111)["guidance"] == "정상 예보"
    assert cache.get(fail, now=113)["guidance"] == "정상 예보"


def test_first_failure_returns_safe_unavailable_payload():
    cache = WeatherOutfitCache()

    def fail():
        raise TimeoutError()

    assert cache.get(fail, now=100) is None
    assert weather_api_payload(None) == {
        "available": False,
        "location": "경주",
        "location_mode": "fixed_gyeongju",
        "guidance": "",
    }


def test_api_payload_never_contains_user_location_fields():
    payload = weather_api_payload(profile())
    assert payload["available"] is True
    assert "latitude" not in payload
    assert "longitude" not in payload
    assert "user_location" not in payload


def test_weather_endpoint_uses_the_shared_cache(monkeypatch):
    import main

    monkeypatch.setattr(main.gyeongju_weather_cache, "get", lambda: profile())
    payload = main.fashion_weather()
    assert payload["available"] is True
    assert payload["location"] == "경주"
