from datetime import date

from korean_lunar_calendar import KoreanLunarCalendar
from lunar_python import Solar


class CalendarError(ValueError):
    pass


def to_solar(
    birth_date: date,
    calendar_type: str,
    is_leap_month: bool = False,
) -> date:
    if calendar_type == "solar":
        return birth_date
    if calendar_type != "lunar":
        raise CalendarError("calendar_type은 solar 또는 lunar여야 합니다.")

    converter = KoreanLunarCalendar()
    ok = converter.setLunarDate(
        birth_date.year,
        birth_date.month,
        birth_date.day,
        bool(is_leap_month),
    )
    if not ok:
        raise CalendarError("유효하지 않은 음력 날짜입니다. 윤달 여부를 확인해 주세요.")
    return date(converter.solarYear, converter.solarMonth, converter.solarDay)


def solar_from_parts(year: int, month: int, day: int, hour: int, minute: int) -> Solar:
    return Solar.fromYmdHms(year, month, day, hour, minute, 0)
