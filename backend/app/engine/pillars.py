from __future__ import annotations

from dataclasses import dataclass
from datetime import date, time
from typing import Literal

from lunar_python import EightChar, Solar

from app.engine.calendar import solar_from_parts, to_solar
from app.engine.characters import GapjaCharacter, get_character
from app.engine.constants import (
    GAN_KO,
    GAN_WUXING,
    SHISHEN_KO,
    WUXING_KO,
    ZHI_KO,
    ZHI_WUXING,
)


Gender = Literal["male", "female"]
CalendarType = Literal["solar", "lunar"]


@dataclass
class StemBranch:
    gan_han: str
    zhi_han: str
    gan: str
    zhi: str
    gan_wuxing: str
    zhi_wuxing: str
    shi_shen_gan: str | None = None
    shi_shen_zhi: str | None = None
    na_yin: str | None = None

    @property
    def label(self) -> str:
        return f"{self.gan}{self.zhi}"

    @property
    def han_label(self) -> str:
        return f"{self.gan_han}{self.zhi_han}"


@dataclass
class SajuResult:
    solar_date: date
    lunar_text: str
    time_unknown: bool
    gender: Gender
    year: StemBranch
    month: StemBranch
    day: StemBranch
    time_pillar: StemBranch | None
    day_master: str
    day_master_han: str
    day_master_wuxing: str
    wuxing_percent: dict[str, float]
    wuxing_counts: dict[str, float]
    character: GapjaCharacter
    pillars_table: list[dict]
    personality: str


def _ko_gan(han: str) -> str:
    return GAN_KO.get(han, han)


def _ko_zhi(han: str) -> str:
    return ZHI_KO.get(han, han)


def _ko_wx(han: str) -> str:
    return WUXING_KO.get(han, han)


def _ko_shishen(raw) -> str | None:
    if not raw:
        return None
    if isinstance(raw, list):
        raw = raw[0] if raw else None
    if not raw:
        return None
    return SHISHEN_KO.get(raw, raw)


def _stem_branch(
    gan_han: str,
    zhi_han: str,
    shi_shen_gan: str | None,
    shi_shen_zhi: str | None,
    na_yin: str | None,
) -> StemBranch:
    return StemBranch(
        gan_han=gan_han,
        zhi_han=zhi_han,
        gan=_ko_gan(gan_han),
        zhi=_ko_zhi(zhi_han),
        gan_wuxing=_ko_wx(GAN_WUXING[gan_han]),
        zhi_wuxing=_ko_wx(ZHI_WUXING[zhi_han]),
        shi_shen_gan=_ko_shishen(shi_shen_gan),
        shi_shen_zhi=_ko_shishen(shi_shen_zhi),
        na_yin=na_yin,
    )


def _wuxing_percent(pillars: list[StemBranch]) -> tuple[dict[str, float], dict[str, float]]:
    weights = {"목": 0.0, "화": 0.0, "토": 0.0, "금": 0.0, "수": 0.0}
    for pillar in pillars:
        weights[pillar.gan_wuxing] += 1.2
        weights[pillar.zhi_wuxing] += 1.0
    total = sum(weights.values()) or 1.0
    percents = {k: round(v / total * 100, 1) for k, v in weights.items()}
    # 반올림 오차 보정
    drift = round(100.0 - sum(percents.values()), 1)
    if drift:
        strongest = max(percents, key=percents.get)
        percents[strongest] = round(percents[strongest] + drift, 1)
    return percents, weights


def _clean_personality(
    result_day: StemBranch,
    month: StemBranch,
    percents: dict[str, float],
    gender: Gender,
    character: GapjaCharacter,
) -> str:
    top = max(percents, key=percents.get)
    bottom = min(percents, key=percents.get)
    tone = "직진과 승부" if gender == "male" else "관계와 분위기 읽기"
    return (
        f"{character.title} 타입입니다. {character.summary} "
        f"일간 {result_day.gan}({result_day.gan_wuxing})에 월주 {month.label}이 더해져 "
        f"기본 성격은 '{character.vibe}' 쪽으로 기울고, {tone}에서 결이 잘 보입니다. "
        f"오행은 {top}이 두드러지고 {bottom}이 비어 있으니, 부족한 기운을 색·장소·루틴으로 보완하면 균형이 좋아집니다."
    )


def calculate_saju(
    *,
    birth_date: date,
    calendar_type: CalendarType,
    is_leap_month: bool = False,
    birth_time: time | None = None,
    time_unknown: bool = False,
    gender: Gender = "female",
) -> SajuResult:
    solar_date = to_solar(birth_date, calendar_type, is_leap_month)
    hour = 12 if time_unknown or birth_time is None else birth_time.hour
    minute = 0 if time_unknown or birth_time is None else birth_time.minute

    solar: Solar = solar_from_parts(solar_date.year, solar_date.month, solar_date.day, hour, minute)
    lunar = solar.getLunar()
    eight: EightChar = lunar.getEightChar()

    year = _stem_branch(
        eight.getYearGan(),
        eight.getYearZhi(),
        eight.getYearShiShenGan(),
        eight.getYearShiShenZhi(),
        eight.getYearNaYin(),
    )
    month = _stem_branch(
        eight.getMonthGan(),
        eight.getMonthZhi(),
        eight.getMonthShiShenGan(),
        eight.getMonthShiShenZhi(),
        eight.getMonthNaYin(),
    )
    day = _stem_branch(
        eight.getDayGan(),
        eight.getDayZhi(),
        "일간",
        eight.getDayShiShenZhi(),
        eight.getDayNaYin(),
    )

    time_pillar = None
    if not time_unknown and birth_time is not None:
        time_pillar = _stem_branch(
            eight.getTimeGan(),
            eight.getTimeZhi(),
            eight.getTimeShiShenGan(),
            eight.getTimeShiShenZhi(),
            eight.getTimeNaYin(),
        )

    pillars = [year, month, day] + ([time_pillar] if time_pillar else [])
    percents, counts = _wuxing_percent(pillars)
    character = get_character(day.gan, day.zhi)
    personality = _clean_personality(day, month, percents, gender, character)

    table = [
        {
            "key": "year",
            "name": "년주",
            "gan": year.gan,
            "zhi": year.zhi,
            "ganHan": year.gan_han,
            "zhiHan": year.zhi_han,
            "ganWuxing": year.gan_wuxing,
            "zhiWuxing": year.zhi_wuxing,
            "shiShenGan": year.shi_shen_gan,
            "shiShenZhi": year.shi_shen_zhi,
            "naYin": year.na_yin,
        },
        {
            "key": "month",
            "name": "월주",
            "gan": month.gan,
            "zhi": month.zhi,
            "ganHan": month.gan_han,
            "zhiHan": month.zhi_han,
            "ganWuxing": month.gan_wuxing,
            "zhiWuxing": month.zhi_wuxing,
            "shiShenGan": month.shi_shen_gan,
            "shiShenZhi": month.shi_shen_zhi,
            "naYin": month.na_yin,
        },
        {
            "key": "day",
            "name": "일주",
            "gan": day.gan,
            "zhi": day.zhi,
            "ganHan": day.gan_han,
            "zhiHan": day.zhi_han,
            "ganWuxing": day.gan_wuxing,
            "zhiWuxing": day.zhi_wuxing,
            "shiShenGan": "일간",
            "shiShenZhi": day.shi_shen_zhi,
            "naYin": day.na_yin,
        },
    ]
    if time_pillar:
        table.append(
            {
                "key": "time",
                "name": "시주",
                "gan": time_pillar.gan,
                "zhi": time_pillar.zhi,
                "ganHan": time_pillar.gan_han,
                "zhiHan": time_pillar.zhi_han,
                "ganWuxing": time_pillar.gan_wuxing,
                "zhiWuxing": time_pillar.zhi_wuxing,
                "shiShenGan": time_pillar.shi_shen_gan,
                "shiShenZhi": time_pillar.shi_shen_zhi,
                "naYin": time_pillar.na_yin,
            }
        )

    return SajuResult(
        solar_date=solar_date,
        lunar_text=lunar.toString(),
        time_unknown=time_unknown or birth_time is None,
        gender=gender,
        year=year,
        month=month,
        day=day,
        time_pillar=time_pillar,
        day_master=day.gan,
        day_master_han=day.gan_han,
        day_master_wuxing=day.gan_wuxing,
        wuxing_percent=percents,
        wuxing_counts=counts,
        character=character,
        pillars_table=table,
        personality=personality,
    )
