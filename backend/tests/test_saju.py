from datetime import date, time

from app.engine.pillars import calculate_saju


def test_known_solar_noon_pillars():
    result = calculate_saju(
        birth_date=date(1990, 5, 15),
        calendar_type="solar",
        birth_time=time(12, 0),
        time_unknown=False,
        gender="male",
    )
    assert result.year.label == "경오"
    assert result.month.label == "신사"
    assert result.day.label == "경진"
    assert result.time_pillar is not None
    assert result.time_pillar.label == "임오"
    assert abs(sum(result.wuxing_percent.values()) - 100) < 0.2


def test_unknown_hour_is_three_pillars():
    result = calculate_saju(
        birth_date=date(1990, 5, 15),
        calendar_type="solar",
        time_unknown=True,
        gender="female",
    )
    assert result.time_pillar is None
    assert len(result.pillars_table) == 3


def test_korean_lunar_converts_to_same_day():
    result = calculate_saju(
        birth_date=date(1990, 4, 21),
        calendar_type="lunar",
        is_leap_month=False,
        birth_time=time(12, 0),
        gender="female",
    )
    assert result.solar_date == date(1990, 5, 15)
    assert result.day.label == "경진"
