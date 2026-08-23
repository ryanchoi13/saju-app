from datetime import date

from fastapi import APIRouter, HTTPException

from app.content.generator import generate_period, generate_theme, generate_today
from app.db import save_profile
from app.engine.calendar import CalendarError
from app.engine.pillars import SajuResult, calculate_saju
from app.schemas import AnalyzeRequest, PeriodRequest, ProfileInput, ThemeRequest

router = APIRouter(prefix="/api")


def _saju_from(req: ProfileInput) -> SajuResult:
    try:
        return calculate_saju(
            birth_date=req.birth_date,
            calendar_type=req.calendar_type,
            is_leap_month=req.is_leap_month,
            birth_time=None if req.time_unknown else req.birth_time,
            time_unknown=req.time_unknown or req.birth_time is None,
            gender=req.gender,
        )
    except CalendarError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


def _saju_payload(saju: SajuResult, req: ProfileInput) -> dict:
    ch = saju.character
    return {
        "nickname": req.nickname,
        "gender": req.gender,
        "calendarType": req.calendar_type,
        "isLeapMonth": req.is_leap_month,
        "birthDate": req.birth_date.isoformat(),
        "solarDate": saju.solar_date.isoformat(),
        "lunarText": saju.lunar_text,
        "timeUnknown": saju.time_unknown,
        "loveStatus": req.love_status,
        "careerStatus": req.career_status,
        "dayMaster": saju.day_master,
        "dayMasterHan": saju.day_master_han,
        "dayMasterWuxing": saju.day_master_wuxing,
        "wuxingPercent": saju.wuxing_percent,
        "personality": saju.personality,
        "pillars": saju.pillars_table,
        "character": {
            "key": f"{ch.gan}{ch.zhi}",
            "title": ch.title,
            "animal": ch.animal,
            "element": ch.element,
            "summary": ch.summary,
            "vibe": ch.vibe,
            "gan": ch.gan,
            "zhi": ch.zhi,
        },
    }


@router.post("/profile")
def upsert_profile(req: ProfileInput) -> dict:
    saju = _saju_from(req)
    stored = save_profile(
        {
            "nickname": req.nickname,
            "gender": req.gender,
            "calendar_type": req.calendar_type,
            "is_leap_month": req.is_leap_month,
            "birth_date": req.birth_date.isoformat(),
            "birth_time": None if req.time_unknown else (req.birth_time.isoformat() if req.birth_time else None),
            "time_unknown": req.time_unknown or req.birth_time is None,
            "love_status": req.love_status,
            "career_status": req.career_status,
        }
    )
    return {"ok": True, "stored": stored is not None, "saju": _saju_payload(saju, req)}


@router.post("/saju/analyze")
def analyze(req: AnalyzeRequest) -> dict:
    saju = _saju_from(req)
    when = req.as_of or date.today()
    today = generate_today(saju, when, req.nickname)
    return {"saju": _saju_payload(saju, req), "today": today}


@router.post("/fortune/today")
def fortune_today(req: AnalyzeRequest) -> dict:
    saju = _saju_from(req)
    when = req.as_of or date.today()
    return generate_today(saju, when, req.nickname)


@router.post("/fortune/theme")
def fortune_theme(req: ThemeRequest) -> dict:
    saju = _saju_from(req)
    when = req.as_of or date.today()
    return generate_theme(saju, when, req.theme, req.nickname, req.love_status, req.career_status)


@router.post("/fortune/period")
def fortune_period(req: PeriodRequest) -> dict:
    saju = _saju_from(req)
    when = req.as_of or date.today()
    return generate_period(saju, when, req.period, req.nickname, req.love_status, req.career_status)
