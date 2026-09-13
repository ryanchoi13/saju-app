from datetime import datetime

from fashion_v2.weather_catalog import (
    WARM_TRANSITION_LOOKS,
    reviewed_weather_board_available,
    validate_weather_catalog,
    weather_templates_for,
)
from fashion_v2.weather_outfit import classify_weather


def point(hour, apparent, rain=0, precipitation=0):
    return {
        "time": datetime(2026, 9, 13, hour),
        "apparent_temperature": apparent,
        "precipitation_probability": rain,
        "precipitation": precipitation,
        "wind_speed_10m": 5,
        "wind_gusts_10m": 10,
        "relative_humidity_2m": 55,
    }


def hot_day_profile(rain=False):
    return classify_weather([
        point(8, 20, 60 if rain else 0, 1.2 if rain else 0),
        point(13, 29, 60 if rain else 0, 1.2 if rain else 0),
        point(20, 20),
    ])


def test_transition_catalog_is_complete_and_valid():
    assert validate_weather_catalog() is True
    assert len(WARM_TRANSITION_LOOKS) == 8


def test_hot_day_casual_is_short_sleeve_with_separate_carry_layer():
    looks = weather_templates_for("male", "casual", hot_day_profile())
    assert [x["look_role"] for x in looks] == ["daily", "trend"]
    for look in looks:
        carried = [x for x in look["items"] if x["wear_mode"] == "carry"]
        assert len(carried) == 1
        assert carried[0]["category"] == "carry_outer"
        assert any("반팔" in x["label"] for x in look["items"] if x["wear_mode"] == "worn")
        assert look["weather_fit"]["template_source"] == "warm_day_cool_evening"


def test_daily_and_trend_are_not_the_same_outfit_with_a_changed_jacket():
    daily, trend = weather_templates_for("male", "casual", hot_day_profile())
    daily_worn = {(x["category"], x["label"]) for x in daily["items"] if x["wear_mode"] == "worn"}
    trend_worn = {(x["category"], x["label"]) for x in trend["items"] if x["wear_mode"] == "worn"}
    assert daily_worn.isdisjoint(trend_worn)


def test_formal_keeps_a_complete_summer_suit_instead_of_fake_carry_styling():
    looks = weather_templates_for("male", "business_formal", hot_day_profile())
    assert len(looks) == 2
    assert all(x["weather_fit"]["template_source"] == "thermal_summer" for x in looks)
    assert all(not any(i["wear_mode"] == "carry" for i in x["items"]) for x in looks)


def test_rain_replaces_suede_without_changing_the_whole_outfit_selection():
    cool_rain = classify_weather([
        point(8, 14, 60, 1.2), point(13, 17, 60, 1.2), point(20, 13),
    ])
    looks = weather_templates_for("male", "casual", cool_rain)
    assert any(i.get("rain_adjusted") for look in looks for i in look["items"])
    assert not any("suede" in i["material"] for look in looks for i in look["items"])


def test_temperature_band_not_calendar_month_selects_clothing_weight():
    freezing = classify_weather([point(12, 3), point(20, 0)])
    looks = weather_templates_for("female", "casual", freezing)
    assert all(x["season"] == "winter" for x in looks)
    assert all(x["weather_fit"]["thermal_band"] == "freezing" for x in looks)


def test_weather_board_gate_is_exact_to_reviewed_gender_and_colors():
    a, b = {"hex": "#EBD3A2"}, {"hex": "#A2B0AD"}
    assert reviewed_weather_board_available("male", a, b) is True
    assert reviewed_weather_board_available("female", a, b) is True
    assert reviewed_weather_board_available("male", b, a) is False
    assert reviewed_weather_board_available("female", b, a) is False
