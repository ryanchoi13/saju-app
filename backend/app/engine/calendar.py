from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from korean_lunar_calendar import KoreanLunarCalendar
from lunar_python import EightChar, Solar


class CalendarError(ValueError):
    pass


# ── 달하 시간 기준 (DALHA_TIME_STANDARD v1) ─────────────────────────────
# 1) 입력 시각은 출생 당시 한국의 '벽시계 시각'으로 받는다.
#    Asia/Seoul 시간대 데이터가 시대별 표준시(1954~1961 UTC+8:30 등)와
#    서머타임(1948~51, 1955~60, 1987~88)을 자동 반영해 실제 출생 순간(UTC)을 구한다.
# 2) 절기(년주·월주·대운)는 그 순간 기준으로 판정한다.
#    lunar-python은 절기를 중국 표준시(UTC+8) 벽시계로 계산하므로 UTC+8로 바꿔 넘긴다.
# 3) 일주·시주는 출생지 평균태양시(서울 경도 기준)로 판정하고,
#    자시는 23시(태양시)에 날이 바뀌는 방식(setSect(1))으로 통일한다.
TIME_STANDARD_VERSION = "dalha-time-v1"
SEOUL_TZ = ZoneInfo("Asia/Seoul")
LUNAR_PYTHON_TZ = timezone(timedelta(hours=8))
DEFAULT_LONGITUDE = 126.98  # 서울 (경주 129.22 등 지역별 입력은 추후)
DAY_CHANGE_SECT = 1  # 23시 일 변경


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


@dataclass(frozen=True)
class BirthMoment:
    utc: datetime
    seasonal_clock: datetime  # 절기 판정용 (UTC+8 벽시계)
    solar_clock: datetime  # 일주·시주 판정용 (평균태양시)


def resolve_birth_moment(
    solar_date: date,
    hour: int,
    minute: int,
    longitude: float = DEFAULT_LONGITUDE,
) -> BirthMoment:
    local = datetime(
        solar_date.year, solar_date.month, solar_date.day, hour, minute, tzinfo=SEOUL_TZ
    )
    utc = local.astimezone(timezone.utc)
    seasonal = utc.astimezone(LUNAR_PYTHON_TZ).replace(tzinfo=None)
    solar = (utc + timedelta(hours=longitude / 15.0)).replace(tzinfo=None)
    return BirthMoment(utc=utc, seasonal_clock=seasonal, solar_clock=solar)


def _solar(dt: datetime) -> Solar:
    return Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)


@dataclass(frozen=True)
class NatalEightChars:
    seasonal: EightChar  # 년주·월주·대운에만 사용
    daily: EightChar  # 일주·시주·일간에만 사용
    moment: BirthMoment


def natal_eight_chars(solar_date: date, hour: int, minute: int) -> NatalEightChars:
    """달하 시간 기준으로 원국 계산용 EightChar 두 개를 만든다."""
    moment = resolve_birth_moment(solar_date, hour, minute)
    seasonal = _solar(moment.seasonal_clock).getLunar().getEightChar()
    seasonal.setSect(DAY_CHANGE_SECT)
    daily = _solar(moment.solar_clock).getLunar().getEightChar()
    daily.setSect(DAY_CHANGE_SECT)
    return NatalEightChars(seasonal=seasonal, daily=daily, moment=moment)
