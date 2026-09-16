"""Weather-to-clothing classification for the Korea-only fashion v2 rollout.

Stage 1 deliberately uses one fixed forecast point (Gyeongju) and never asks
for browser geolocation.  Calendar season remains useful for colour mood, but
thermal weight is derived from apparent temperature and weather hazards.
"""

from __future__ import annotations

from datetime import datetime
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen


GYEONGJU = {
    "name": "경주",
    "latitude": 35.8562,
    "longitude": 129.2247,
    "timezone": "Asia/Seoul",
}

# Descending lower bounds keep every temperature in exactly one band.
THERMAL_BANDS = (
    (29, "very_hot", "한여름"),
    (25, "hot", "더운 날"),
    (22, "warm", "따뜻한 날"),
    (19, "mild", "선선한 날"),
    (16, "cool", "서늘한 날"),
    (11, "chilly", "쌀쌀한 날"),
    (5, "cold", "추운 날"),
    (float("-inf"), "freezing", "매우 추운 날"),
)

PROFILE_RULES = {
    "very_hot": ("short_sleeve", "none", "summer", "낮에는 반팔이 알맞아요."),
    "hot": ("short_sleeve", "none", "summer", "낮에는 반팔이 알맞아요."),
    "warm": ("short_or_thin_long", "none", "summer", "낮에는 반팔이나 얇은 긴팔이 알맞아요."),
    "mild": ("thin_long_sleeve", "light", "spring", "얇은 긴팔이나 가벼운 셔츠가 알맞아요."),
    "cool": ("long_sleeve", "light", "autumn", "긴팔에 얇은 재킷을 더하기 좋아요."),
    "chilly": ("knit", "medium", "autumn", "니트와 중간 두께 재킷이 알맞아요."),
    "cold": ("warm_knit", "warm", "winter", "도톰한 니트와 코트가 필요해요."),
    "freezing": ("winter_base", "heavy", "winter", "보온 내의와 두꺼운 겨울 아우터가 필요해요."),
}


def thermal_band(apparent_celsius: float) -> dict:
    value = float(apparent_celsius)
    for lower, key, label in THERMAL_BANDS:
        if value >= lower:
            base, outer, season_hint, sentence = PROFILE_RULES[key]
            return {
                "key": key,
                "label": label,
                "base_layer": base,
                "outerwear": outer,
                "catalog_season_hint": season_hint,
                "sentence": sentence,
            }
    raise AssertionError("unreachable thermal band")


def _period(points: list[dict], start_hour: int, end_hour: int) -> list[dict]:
    selected = [point for point in points if start_hour <= point["time"].hour <= end_hour]
    return selected or points


def classify_weather(points: list[dict]) -> dict:
    """Convert one local forecast day into deterministic clothing guidance."""
    if not points:
        raise ValueError("at least one hourly forecast point is required")

    daytime = _period(points, 11, 17)
    evening = _period(points, 18, 23)
    morning_evening = [p for p in points if 6 <= p["time"].hour <= 10 or 18 <= p["time"].hour <= 23] or points
    day_peak = max(float(p["apparent_temperature"]) for p in daytime)
    evening_low = min(float(p["apparent_temperature"]) for p in evening)
    comfort_low = min(float(p["apparent_temperature"]) for p in morning_evening)
    swing = round(day_peak - comfort_low, 1)
    band = thermal_band(day_peak)

    rain_probability = max(float(p.get("precipitation_probability", 0) or 0) for p in points)
    precipitation = round(sum(float(p.get("precipitation", 0) or 0) for p in points), 1)
    wind_speed = max(float(p.get("wind_speed_10m", 0) or 0) for p in points)
    wind_gust = max(float(p.get("wind_gusts_10m", 0) or 0) for p in points)
    daytime_humidity = sum(float(p.get("relative_humidity_2m", 0) or 0) for p in daytime) / len(daytime)

    rainy = rain_probability >= 40 or precipitation >= 1.0
    windy = wind_speed >= 20 or wind_gust >= 35
    humid_hot = day_peak >= 25 and daytime_humidity >= 70
    carry_light_outer = (
        band["key"] in {"very_hot", "hot", "warm"}
        and comfort_low < 22
    )

    outerwear = band["outerwear"]
    if carry_light_outer:
        outerwear = "carry_light"
    if windy and outerwear == "none":
        outerwear = "wind_shell"

    messages = [band["sentence"]]
    if carry_light_outer:
        messages.append("저녁에는 얇은 바람막이나 긴팔 셔츠를 챙기세요.")
    elif windy:
        messages.append("바람을 막을 수 있는 가벼운 겉옷이 좋아요.")
    if rainy:
        messages.append("비가 오는 날에는 스웨이드를 피하고, 신발·겉옷의 생활방수·발수 표기를 확인하세요.")
    elif humid_hot:
        messages.append("습도가 높아 통기성 좋은 소재가 편해요.")
    if band['key'] in {'cold','freezing'}:
        messages.append("코디 그림은 안쪽 옷을 보여주기 위한 구성이며, 추운 실외에서는 겉옷을 여며 입으세요.")

    return {
        "location": GYEONGJU["name"],
        "temperature_basis": "apparent_temperature",
        "daytime_apparent_high": round(day_peak, 1),
        "evening_apparent_low": round(evening_low, 1),
        "day_night_gap": swing,
        "thermal_band": band["key"],
        "thermal_label": band["label"],
        "base_layer": band["base_layer"],
        "outerwear": outerwear,
        "catalog_season_hint": band["catalog_season_hint"],
        "carry_light_outer": carry_light_outer,
        "rainy": rainy,
        "avoid_suede": rainy,
        "windy": windy,
        "humid_hot": humid_hot,
        "precipitation_probability_max": round(rain_probability),
        "precipitation_sum": precipitation,
        "wind_speed_max": round(wind_speed, 1),
        "wind_gust_max": round(wind_gust, 1),
        "guidance": " ".join(messages),
    }


def open_meteo_url() -> str:
    params = {
        "latitude": GYEONGJU["latitude"],
        "longitude": GYEONGJU["longitude"],
        "hourly": ",".join((
            "apparent_temperature", "relative_humidity_2m",
            "precipitation_probability", "precipitation",
            "wind_speed_10m", "wind_gusts_10m", "weather_code",
        )),
        "forecast_days": 1,
        "timezone": GYEONGJU["timezone"],
    }
    return "https://api.open-meteo.com/v1/forecast?" + urlencode(params)


def parse_open_meteo(payload: dict) -> list[dict]:
    hourly = payload.get("hourly") or {}
    times = hourly.get("time") or []
    required = ("apparent_temperature",)
    if not times or any(len(hourly.get(key) or []) != len(times) for key in required):
        raise ValueError("invalid Open-Meteo hourly forecast")
    optional = (
        "relative_humidity_2m", "precipitation_probability", "precipitation",
        "wind_speed_10m", "wind_gusts_10m", "weather_code",
    )
    points = []
    for index, value in enumerate(times):
        point = {
            "time": datetime.fromisoformat(value),
            "apparent_temperature": hourly["apparent_temperature"][index],
        }
        for key in optional:
            values = hourly.get(key) or []
            point[key] = values[index] if len(values) == len(times) else 0
        points.append(point)
    return points


def fetch_gyeongju_weather(timeout: float = 2.0) -> dict:
    """Fetch a forecast without receiving or storing any user coordinates."""
    request = Request(open_meteo_url(), headers={"User-Agent": "DALHA/1.0 weather-outfit"})
    with urlopen(request, timeout=timeout) as response:
        payload = json.load(response)
    result = classify_weather(parse_open_meteo(payload))
    result.update(source="Open-Meteo", location_mode="fixed_gyeongju", language="ko")
    return result
