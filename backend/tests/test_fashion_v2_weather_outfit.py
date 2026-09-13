from datetime import datetime
from urllib.parse import parse_qs, urlparse

import pytest

from fashion_v2.weather_outfit import (
    GYEONGJU,
    classify_weather,
    open_meteo_url,
    parse_open_meteo,
    thermal_band,
)


def point(hour, apparent, rain=0, precipitation=0, wind=5, gust=10, humidity=55):
    return {
        "time": datetime(2026, 9, 13, hour),
        "apparent_temperature": apparent,
        "precipitation_probability": rain,
        "precipitation": precipitation,
        "wind_speed_10m": wind,
        "wind_gusts_10m": gust,
        "relative_humidity_2m": humidity,
    }


@pytest.mark.parametrize(
    ("temperature", "expected"),
    [(31, "very_hot"), (29, "very_hot"), (28.9, "hot"), (25, "hot"),
     (22, "warm"), (19, "mild"), (16, "cool"), (11, "chilly"),
     (5, "cold"), (4.9, "freezing")],
)
def test_thermal_band_boundaries(temperature, expected):
    assert thermal_band(temperature)["key"] == expected


def test_hot_day_and_cool_evening_recommends_only_a_carry_layer():
    result = classify_weather([
        point(8, 20), point(12, 26), point(15, 27), point(19, 21), point(22, 19),
    ])
    assert result["thermal_band"] == "hot"
    assert result["base_layer"] == "short_sleeve"
    assert result["outerwear"] == "carry_light"
    assert result["carry_light_outer"] is True
    assert result["catalog_season_hint"] == "summer"
    assert result["guidance"] == "낮에는 반팔이 알맞아요. 저녁에는 얇은 바람막이나 긴팔 셔츠를 챙기세요."


def test_rain_avoids_suede_and_wind_requires_a_shell():
    result = classify_weather([
        point(12, 27, rain=60, precipitation=1.2, wind=23, gust=38, humidity=78),
        point(20, 24, rain=30, wind=18, gust=30, humidity=75),
    ])
    assert result["rainy"] is True
    assert result["avoid_suede"] is True
    assert result["windy"] is True
    assert result["humid_hot"] is True
    assert result["outerwear"] == "wind_shell"
    assert "생활방수" in result["guidance"]


def test_fixed_korea_rollout_url_contains_no_user_location():
    parsed = urlparse(open_meteo_url())
    query = parse_qs(parsed.query)
    assert parsed.netloc == "api.open-meteo.com"
    assert query["latitude"] == [str(GYEONGJU["latitude"])]
    assert query["longitude"] == [str(GYEONGJU["longitude"])]
    assert query["timezone"] == ["Asia/Seoul"]


def test_open_meteo_parser_rejects_missing_temperature_series():
    with pytest.raises(ValueError):
        parse_open_meteo({"hourly": {"time": ["2026-09-13T12:00"]}})


def test_open_meteo_parser_normalizes_optional_missing_series():
    points = parse_open_meteo({"hourly": {
        "time": ["2026-09-13T12:00"],
        "apparent_temperature": [24.5],
    }})
    assert points[0]["time"] == datetime(2026, 9, 13, 12)
    assert points[0]["precipitation"] == 0
