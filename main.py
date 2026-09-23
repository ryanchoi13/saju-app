import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
from datetime import date, time
from app.engine.korean import josa
from app.engine.pillars import calculate_saju
from app.engine.constants import GAN_KO, ZHI_KO
from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services import (
    build_annual_overall_report,
    build_compatibility_report,
    build_daily_fortune,
    build_lifetime_career_report,
    build_lifetime_health_report,
    build_lifetime_love_report,
    build_lifetime_overall_report,
    build_lifetime_study_report,
    build_lifetime_wealth_report,
)
import wardrobe_store
import meal_set_store as menu_store
import tarot_service
import account_store
import session_store
import wallet_store
import account_security
from style_context import build_style_contexts
from wada_context_placement import WADA_CONTEXT_PLACEMENT
from wada_color_rules import evaluate_duo
from wada_color_ko import get_wada_color_ko
from wada_wuxing_selector import select_wada_duo_for_targets
from fashion_v2.svg_recommendation import build_svg_catalog_contexts
from app.engine.services.fashion_colors import build_fashion_color_basis
from app.engine.services.annual_editorial import NARRATIVE_VERSION as ANNUAL_NARRATIVE_VERSION
from fashion_v2.weather_service import gyeongju_weather_cache, weather_api_payload
from lunar_python import Solar
from fastapi import FastAPI, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import datetime
import os
import random
 
app = FastAPI(title="DALHA - Style Destiny Backend Engine")
app.mount("/assets", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "assets")), name="assets")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://dalha.kr", "https://www.dalha.kr"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- In-Memory DB Models ---
users_db: Dict[str, Dict[str, Any]] = {}
reports_db: Dict[str, List[Dict[str, Any]]] = {}


def hydrate_account(user_id):
    """Caches are for rendering only; database state always wins."""
    saved = account_store.load(user_id)
    previous = users_db.get(user_id, {})
    assets = wallet_store.load(user_id, initial_balance=previous.get('coin', 1000),
                               initial_reports=reports_db.get(user_id, []))
    user = dict(previous, user_id=user_id, kakao_id=user_id[5:], coin=assets['balance'])
    if saved:
        user.update(saved['profile'], profile_complete=saved['confirmed'])
    users_db[user_id] = user
    reports_db[user_id] = assets['reports']
    return user


account_security.install(app, hydrate_account)

# --- Request/Response Models ---
class KakaoAuthRequest(BaseModel):
    kakao_id: str = Field(min_length=1, max_length=50, pattern=r"^[A-Za-z0-9_-]+$")
    name: Optional[str] = None
    gender: Optional[str] = None
    birthyear: Optional[str] = None
    birthday: Optional[str] = None
    birthday_type: Optional[str] = None
    sijin_index: Optional[int] = None
    profile_source: str = Field(default="saved", pattern=r"^(saved|kakao)$")
    is_leap_month: bool = False
    access_token: Optional[str] = Field(default=None, max_length=4096)

class RegisterSajuRequest(BaseModel):
    user_id: str
    name: str
    gender: str
    birth_year: int
    birth_month: int
    birth_day: int
    calendar_type: str
    sijin_index: int

class WardrobeItemRequest(BaseModel):
    user_id: str
    category: str = Field(min_length=1, max_length=50)
    nickname: Optional[str] = Field(default="", max_length=100)
    colors: List[str] = Field(min_length=1, max_length=8)
    materials: List[str] = Field(min_length=1, max_length=8)

class UnlockReportRequest(BaseModel):
    user_id: str
    report_key: str
    cost: int
    sub_option: Optional[str] = "기본"
    partner_name: Optional[str] = "상대방"
    relation: Optional[str] = "인연/조화"
    partner_gender: Optional[str] = None
    partner_birth_year: Optional[int] = None
    partner_birth_month: Optional[int] = None
    partner_birth_day: Optional[int] = None
    partner_calendar_type: Optional[str] = "solar"
    partner_sijin_index: Optional[int] = -1

class ChargeCoinRequest(BaseModel):
    user_id: str
    amount: int = Field(gt=0, le=100000, strict=True)

# --- Saju Calculation Constants & Engine ---
CHEONGAN = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
JIJI = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]

SIJIN_LABELS = [
    "자(子)시", "축(丑)시", "인(寅)시", "묘(卯)시", "진(辰)시", "사(巳)시",
    "오(午)시", "미(未)시", "신(申)시", "유(酉)시", "술(戌)시", "해(亥)시",
]
_ELEMENT_KEY = {"木": "wood", "火": "fire", "土": "earth", "金": "metal", "水": "water"}
_STRENGTH_LABEL = {
    "extremely_weak": "매우 신약(身弱)",
    "weak": "신약(身弱)",
    "balanced": "중화(中和)",
    "strong": "신강(身强)",
    "extremely_strong": "매우 신강(身强)",
}
# 화면용 오행 구성 비율. 천간 1칸, 지지 1칸을 동일 총량으로 두고
# 지지 1칸은 엔진의 지장간(본기·중기·여기)에 전통적 상대 비중으로 배분한다.
# 이는 길흉/강약 점수가 아니며 월령·통근·합충·조후는 진단 엔진에서 별도 평가한다.
_HIDDEN_STEM_COMPOSITION_WEIGHTS = {
    "子": {"main": 1.0},
    "丑": {"main": 0.6, "middle": 0.3, "residual": 0.1},
    "寅": {"main": 16 / 30, "middle": 7 / 30, "residual": 7 / 30},
    "卯": {"main": 1.0},
    "辰": {"main": 0.6, "middle": 0.3, "residual": 0.1},
    "巳": {"main": 16 / 30, "middle": 7 / 30, "residual": 7 / 30},
    "午": {"main": 0.7, "middle": 0.3},
    "未": {"main": 0.6, "middle": 0.3, "residual": 0.1},
    "申": {"main": 16 / 30, "middle": 7 / 30, "residual": 7 / 30},
    "酉": {"main": 1.0},
    "戌": {"main": 0.6, "middle": 0.1, "residual": 0.3},
    "亥": {"main": 0.7, "middle": 0.3},
}


def _sijin_midpoint(sijin: int) -> time | None:
    """Return a representative midpoint for the two-hour UI time range."""

    if not 0 <= sijin <= 11:
        return None
    return time((sijin * 2) % 24, 30)


def _birth_input_from_user(user: Dict[str, Any], name: str) -> BirthInput:
    sijin = int(user.get("sijin_index", -1))
    clock = _sijin_midpoint(sijin)
    calendar_type = "lunar" if user["calendar_type"] in {"lunar", "leap"} else "solar"
    return BirthInput(
        name=name or "회원",
        gender=user["gender"],
        birth_date=date(user["birth_year"], user["birth_month"], user["birth_day"]),
        calendar_type=calendar_type,
        is_leap_month=user["calendar_type"] == "leap",
        birth_time=clock,
        time_unknown=clock is None,
    )


def _element_composition_percent(core) -> Dict[str, float]:
    """Describe visible stems plus role-weighted hidden stems, not strength."""

    counts = {key: 0 for key in _ELEMENT_KEY.values()}
    for pillar_name, pillar in core.natal_facts.pillars.items():
        if pillar is None:
            continue
        # 드러난 천간 한 글자 = 1칸
        counts[_ELEMENT_KEY[pillar.stem_element]] += 1
        # 지지 한 글자 = 1칸. 그 안을 해당 지장간 비중으로 나눈다.
        hidden = core.natal_facts.hidden_stems.get(pillar_name)
        branch_weights = _HIDDEN_STEM_COMPOSITION_WEIGHTS[pillar.branch]
        for item in hidden.stems if hidden else []:
            counts[_ELEMENT_KEY[item.element]] += branch_weights[item.role.value]
    total = sum(counts.values())
    if not total:
        return {key: 0 for key in counts}
    values = {key: round(count / total * 100, 1) for key, count in counts.items()}
    drift = round(100 - sum(values.values()), 1)
    if drift:
        strongest = max(values, key=values.get)
        values[strongest] = round(values[strongest] + drift, 1)
    return values


def _pillar_detail(core, pillar_name: str) -> Dict[str, Any]:
    pillar = core.natal_facts.pillars.get(pillar_name)
    if pillar is None:
        return {"cg": "", "cg_elem": "", "jj": "", "jj_elem": "", "jijanggan": []}
    hidden = core.natal_facts.hidden_stems.get(pillar_name)
    return {
        "cg": GAN_KO[pillar.stem],
        "cg_elem": _ELEMENT_KEY[pillar.stem_element],
        "jj": ZHI_KO[pillar.branch],
        "jj_elem": _ELEMENT_KEY[pillar.branch_element],
        "jijanggan": [
            {"char": GAN_KO[item.stem], "elem": _ELEMENT_KEY[item.element]}
            for item in (hidden.stems if hidden else [])
        ],
    }


def _daeyun_phase(current_cycle: Dict[str, Any] | None) -> Dict[str, Any]:
    index = (current_cycle or {}).get("index")
    if index is None:
        phase = "대운 시작 전"
    elif index <= 2:
        phase = "초년기"
    elif index <= 4:
        phase = "청년기"
    elif index <= 7:
        phase = "중장년기"
    else:
        phase = "말년기"
    return {
        "name": phase,
        "cycle": (current_cycle or {}).get("pillar", {}).get("ganji"),
        "age_range": (
            f'{current_cycle["start_age"]}~{current_cycle["end_age"]}세'
            if current_cycle else None
        ),
    }

ELEM_MAP = {
    "갑": "wood", "을": "wood", "인": "wood", "묘": "wood",
    "병": "fire", "정": "fire", "사": "fire", "오": "fire",
    "무": "earth", "기": "earth", "진": "earth", "술": "earth", "축": "earth", "미": "earth",
    "경": "metal", "신": "metal", "유": "metal",
    "임": "water", "계": "water", "자": "water", "해": "water"
}

JIJANGGAN_MAP = {
    "자": [{"char": "임", "elem": "water"}, {"char": "계", "elem": "water"}],
    "축": [{"char": "계", "elem": "water"}, {"char": "신", "elem": "metal"}, {"char": "기", "elem": "earth"}],
    "인": [{"char": "무", "elem": "earth"}, {"char": "병", "elem": "fire"}, {"char": "갑", "elem": "wood"}],
    "묘": [{"char": "갑", "elem": "wood"}, {"char": "을", "elem": "wood"}],
    "진": [{"char": "을", "elem": "wood"}, {"char": "계", "elem": "water"}, {"char": "무", "elem": "earth"}],
    "사": [{"char": "무", "elem": "earth"}, {"char": "경", "elem": "metal"}, {"char": "병", "elem": "fire"}],
    "오": [{"char": "병", "elem": "fire"}, {"char": "기", "elem": "earth"}, {"char": "정", "elem": "fire"}],
    "미": [{"char": "정", "elem": "fire"}, {"char": "을", "elem": "wood"}, {"char": "기", "elem": "earth"}],
    "신": [{"char": "무", "elem": "earth"}, {"char": "임", "elem": "water"}, {"char": "경", "elem": "metal"}],
    "유": [{"char": "경", "elem": "metal"}, {"char": "신", "elem": "metal"}],
    "술": [{"char": "신", "elem": "metal"}, {"char": "정", "elem": "fire"}, {"char": "무", "elem": "earth"}],
    "해": [{"char": "무", "elem": "earth"}, {"char": "갑", "elem": "wood"}, {"char": "임", "elem": "water"}]
}

def calculate_biorhythm(birth_year: int, birth_month: int, birth_day: int, target_date=None):
    import math
    today = target_date or datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date()
    days_lived = (today - datetime.date(birth_year, birth_month, birth_day)).days
    def status(value):
        return "고조기" if value >= 50 else ("저조기" if value <= -50 else "안정기")
    result = {"days_lived": days_lived}
    for key, period in (("physical", 23), ("emotional", 28), ("intellectual", 33)):
        value = round(math.sin(2 * math.pi * days_lived / period) * 100)
        result[key] = {"val": value, "status": status(value)}
    # One short interpretation combines all three phases without repeating
    # the numeric legend or treating the curves as measured human abilities.
    labels = (("physical", "신체"), ("emotional", "감성"), ("intellectual", "지성"))
    groups = []
    for phase in ("고조기", "안정기", "저조기"):
        names = [label for key, label in labels if result[key]["status"] == phase]
        if names:
            groups.append(f"{josa('·'.join(names), '은/는')} {phase}")
    low = tuple(key for key, _ in labels if result[key]["status"] == "저조기")
    advice = {
        (): "하고 싶은 일 하나를 골라, 평소의 페이스로 가볍게 시작해 보세요.",
        ("physical",): "몸은 쉬엄쉬엄 움직이고, 대화나 생각을 정리하는 데 시간을 써 보세요.",
        ("emotional",): "활동은 평소대로 이어가되, 대화에서는 잠깐 여유를 두세요.",
        ("intellectual",): "활동과 대화를 즐기되, 중요한 내용은 짧게 메모해 보세요.",
        ("physical", "emotional"): "조용히 생각을 정리하면서, 몸과 마음에 쉴 틈을 주세요.",
        ("physical", "intellectual"): "편안한 대화로 하루를 채우고, 할 일은 하나씩 나눠 보세요.",
        ("emotional", "intellectual"): "가볍게 움직이며 기분을 환기하고, 중요한 일은 하나씩 정리해 보세요.",
        ("physical", "emotional", "intellectual"): "오늘은 속도를 조금 늦추고, 꼭 필요한 일부터 차분히 해보세요.",
    }
    result["overall_summary"] = ', '.join(groups) + "입니다. " + advice[low]
    return result

def with_wa_gwa(word: str):
    return josa(word, "과/와")

def get_saju_pillars_and_analysis(name: str, gender: str, y: int, m: int, d: int, cal_type: str, sijin: int, menu_account_id: str | None = None, weather_profile: dict | None = None):
    backend_calendar_type = "lunar" if cal_type in ["lunar", "leap"] else "solar"
    backend_is_leap = (cal_type == "leap")
    birth_clock = _sijin_midpoint(sijin)

    kst_now = datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=9))
    )
    today_date = kst_now.date()
    core = calculate_myeongri_core(
        BirthInput(
            name=name or "회원",
            gender=gender,
            birth_date=date(y, m, d),
            calendar_type=backend_calendar_type,
            is_leap_month=backend_is_leap,
            birth_time=birth_clock,
            time_unknown=birth_clock is None,
        ),
        target_date=today_date,
    )

    elements_weight = _element_composition_percent(core)
    singang_label = _STRENGTH_LABEL.get(
        core.synthesis.strength_state,
        "강약 판정 보류",
    )
    time_text = SIJIN_LABELS[sijin] + "생" if 0 <= sijin <= 11 else "생시 미상"
    gender_text = "남성" if gender == "male" else "여성"
    profile_detail = f"{y}년 {m}월 {d}일 · {time_text} · {gender_text}"

    current_age = datetime.date.today().year - y + 1

    today_fortune = build_daily_fortune(
        core,
        name,
        today_date,
        current_hour=kst_now.hour,
        account_key=menu_account_id,
        include_menu=False,
    )
    today_element = core.timing.daily["pillar"]["stem_element"]
    lucky_element = today_fortune["lucky_element"]
    fashion_color_basis = build_fashion_color_basis(core)
    fashion_element = fashion_color_basis["primary_element"]

    current_month = today_date.month

    if current_month in [3, 4, 5]:
        outfit_season = "spring"
    elif current_month in [6, 7, 8]:
        outfit_season = "summer"
    elif current_month in [9, 10, 11]:
        outfit_season = "autumn"
    else:
        outfit_season = "winter"

    age = today_date.year - y + 1
    solar_birth = datetime.date.fromisoformat(core.natal_facts.calendar["solar_date"])
    style_age = today_date.year - solar_birth.year - (
        (today_date.month, today_date.day) < (solar_birth.month, solar_birth.day)
    )

    if age < 40:
        outfit_age_group = "20s_30s"
    elif age < 60:
        outfit_age_group = "40s_50s"
    else:
        outfit_age_group = "60plus"

    wada_selection = select_wada_duo_for_targets(
        fashion_element,
        today_element,
        int(today_date.strftime("%Y%m%d"))
    )

    wada_duo_no = wada_selection["duo_no"]
    wada_duo = wada_selection["duo"]   

    outfit_tpo = "casual"

    wada_placement = WADA_CONTEXT_PLACEMENT[wada_duo_no][gender][outfit_tpo][outfit_season][outfit_age_group]

    wada_top_name = wada_placement["top"]
    wada_top_hex = wada_placement["top_hex"]
    wada_bottom_name = wada_placement["bottom"]
    wada_bottom_hex = wada_placement["bottom_hex"]
 
    wada_top_color = get_wada_color_ko(
        wada_top_hex,
        wada_top_name
    )

    wada_bottom_color = get_wada_color_ko(
        wada_bottom_hex,
        wada_bottom_name
    )
 
    result = {
        "user_name": name,
        "birth_summary": profile_detail,
        "saju_profile_detail": profile_detail,
        "current_age": current_age,
        "biorhythm": calculate_biorhythm(*map(int, core.natal_facts.calendar["solar_date"].split("-")), target_date=today_date),
        "saju_data": {
            "singang_label": singang_label,
            "pillars_detail": {
                "year": _pillar_detail(core, "year"),
                "month": _pillar_detail(core, "month"),
                "day": _pillar_detail(core, "day"),
                "hour": _pillar_detail(core, "hour"),
            },
            "elements": elements_weight,
            "elements_note": (
                "천간 4글자와 지지 속 지장간의 본기·중기·여기 비중을 합산한 원국 구성입니다. 월령·통근·합충·조후는 강약과 해석에 별도로 반영합니다."
                if birth_clock else
                "생시를 제외한 천간 3글자와 지지 속 지장간 비중을 합산한 원국 구성입니다. 생시 관련 비율은 확정하지 않으며 월령·통근·합충·조후는 별도로 판단합니다."
            ),
            "daeyun_phase": _daeyun_phase(core.timing.luck_cycle.get("current")),
        },
        "daily_fortune": {
            **today_fortune,
            "weather_outfit": weather_api_payload(weather_profile),
            "wada_palette": {
                "theme": f"Wada Duo #{wada_duo_no}",
                "mood_desc": f"{with_wa_gwa(wada_top_color['name_ko'])} {josa(wada_bottom_color['name_ko'], '으로/로')} 오늘의 의상 컬러를 조합해 보세요.",
                "mode": "harmony",
                "style_mood": outfit_tpo,
                "mood_tag": "캐주얼",
                "top": {
                    "name": wada_top_color["original_name"],
                    "name_ko": wada_top_color["name_ko"],
                    "hex": wada_top_hex,
                    "standard_color": wada_top_color["standard_color"]
                },
                "bottom": {
                    "name": wada_bottom_color["original_name"],
                    "name_ko": wada_bottom_color["name_ko"],
                    "hex": wada_bottom_hex,
                    "standard_color": wada_bottom_color["standard_color"]
                },
                "point": None
            },
            "lucky_colors": [
                wada_top_color["standard_color"],
                wada_bottom_color["standard_color"],
            ],
        }
    }

    result["daily_fortune"]["style_palettes"] = build_style_contexts(
        wada_duo_no, gender, result["daily_fortune"]["wada_palette"], fashion_element,
        user_name=name, age=style_age, season=outfit_season)
    color_a = {
        "name": wada_top_color["original_name"],
        "name_ko": wada_top_color["name_ko"],
        "hex": wada_top_hex,
    }
    color_b = {
        "name": wada_bottom_color["original_name"],
        "name_ko": wada_bottom_color["name_ko"],
        "hex": wada_bottom_hex,
    }
    complete_weather = weather_profile and all(key in weather_profile for key in (
        "thermal_band", "thermal_label", "daytime_apparent_high",
        "evening_apparent_low", "carry_light_outer", "rainy", "guidance",
        "base_layer", "catalog_season_hint", "avoid_suede",
    ))
    selected_weather = (
        weather_profile
        if complete_weather
        else None
    )
    result["daily_fortune"]["weather_outfit"]["template_applied"] = bool(selected_weather)
    result["daily_fortune"]["fashion_v2"] = build_svg_catalog_contexts(
        gender,
        outfit_season,
        color_a,
        color_b,
        weather_profile=selected_weather,
        age=style_age,
        board_weather_profile=weather_profile if complete_weather else None,
    )
    result["daily_fortune"]["fashion_color_basis"] = fashion_color_basis
    fortune = result["daily_fortune"]
    from meal_sets import build_set
    def build(mode, history, excluded):
        return build_set(core.input, today_date, mode, history, excluded)
    fortune.update(recommended_menus=[], recommended_menu='', recommended_meals=[])
    if menu_account_id:
        try:
            fortune['menu_recommendations'] = menu_store.load(menu_account_id, today_date, build)
        except (menu_store.StorageUnavailable, ValueError):
            fortune['menu_error'] = '식단을 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.'
    return result


# --- Detailed Report Generator Engine ---
def generate_detailed_report(
    report_key: str,
    sub_option: str,
    partner_name: str,
    relation: str,
    user_name: str,
    user: Optional[Dict[str, Any]] = None,
    partner: Optional[Dict[str, Any]] = None,
    report_year: Optional[int] = None,
) -> Dict[str, str]:
    if report_key == "sinnian":
        if not user:
            raise ValueError("올해 운세 생성에 사용자 사주 정보가 필요합니다.")
        kst_today = datetime.datetime.now(
            datetime.timezone(datetime.timedelta(hours=9))
        ).date()
        core = calculate_myeongri_core(
            _birth_input_from_user(user, user_name),
            target_date=kst_today,
        )
        return build_annual_overall_report(core, user_name, report_year or kst_today.year)
    elif report_key == "gunghap":
        if not user or not partner:
            raise ValueError("궁합 생성에 두 사람의 사주 정보가 필요합니다.")
        kst_today = datetime.datetime.now(
            datetime.timezone(datetime.timedelta(hours=9))
        ).date()
        user_core = calculate_myeongri_core(
            _birth_input_from_user(user, user_name), target_date=kst_today
        )
        partner_core = calculate_myeongri_core(
            _birth_input_from_user(partner, partner_name), target_date=kst_today
        )
        return build_compatibility_report(
            user_core, partner_core, user_name, partner_name, relation
        )
    elif report_key == "daewoon":
        if not user:
            raise ValueError("평생운세 생성에 사용자 사주 정보가 필요합니다.")
        kst_today = datetime.datetime.now(
            datetime.timezone(datetime.timedelta(hours=9))
        ).date()
        core = calculate_myeongri_core(
            _birth_input_from_user(user, user_name),
            target_date=kst_today,
        )
        return build_lifetime_overall_report(core, user_name)
    elif report_key == "wealth":
        if not user:
            raise ValueError("평생 재물운 생성에 사용자 사주 정보가 필요합니다.")
        kst_today = datetime.datetime.now(
            datetime.timezone(datetime.timedelta(hours=9))
        ).date()
        core = calculate_myeongri_core(
            _birth_input_from_user(user, user_name),
            target_date=kst_today,
        )
        return build_lifetime_wealth_report(core, user_name)
    elif report_key == "business":
        if not user:
            raise ValueError("평생 직업·사업운 생성에 사용자 사주 정보가 필요합니다.")
        kst_today = datetime.datetime.now(
            datetime.timezone(datetime.timedelta(hours=9))
        ).date()
        core = calculate_myeongri_core(
            _birth_input_from_user(user, user_name),
            target_date=kst_today,
        )
        return build_lifetime_career_report(core, user_name, sub_option)
    elif report_key == "love":
        if not user:
            raise ValueError("평생 애정·관계운 생성에 사용자 사주 정보가 필요합니다.")
        kst_today = datetime.datetime.now(
            datetime.timezone(datetime.timedelta(hours=9))
        ).date()
        core = calculate_myeongri_core(
            _birth_input_from_user(user, user_name),
            target_date=kst_today,
        )
        return build_lifetime_love_report(core, user_name, sub_option)
    elif report_key == "health":
        if not user:
            raise ValueError("평생 건강 생활흐름 생성에 사용자 사주 정보가 필요합니다.")
        kst_today = datetime.datetime.now(
            datetime.timezone(datetime.timedelta(hours=9))
        ).date()
        core = calculate_myeongri_core(
            _birth_input_from_user(user, user_name),
            target_date=kst_today,
        )
        return build_lifetime_health_report(core, user_name)
    elif report_key == "study":
        if not user:
            raise ValueError("평생 학업·시험운 생성에 사용자 사주 정보가 필요합니다.")
        kst_today = datetime.datetime.now(
            datetime.timezone(datetime.timedelta(hours=9))
        ).date()
        core = calculate_myeongri_core(
            _birth_input_from_user(user, user_name),
            target_date=kst_today,
        )
        return build_lifetime_study_report(core, user_name)
    else:
        title = f"{user_name}님 {sub_option} 맞춤 심층 감명서"
        content = f"""
        <div style="text-align:left; line-height:1.85; color:#1E293B;">
            <div style="background:#F8FAFC; border-left:4px solid #2D6A4F; padding:16px; border-radius:14px; margin-bottom:14px;">
                <h4 style="font-size:15.5px; font-weight:800; color:#065F46; margin-bottom:6px;">🎯 {sub_option} 핵심 분석 & 미래 전략</h4>
                <p style="font-size:13.5px; color:#047857; margin:0; line-height:1.75;">
                    현재 사주 운명의 흐름상 선택과 집중이 필요한 중요한 변곡점에 서 있습니다. 
                    단기적인 이익에 흔들리지 않고 장기적인 본질에 집중할 때 기대 이상의 성과와 번영을 달성할 수 있습니다.
                </p>
            </div>
        </div>
        """
    return {"title": title, "content": content}

# --- API Endpoints ---
def _profile_from_kakao_request(req: KakaoAuthRequest) -> Optional[Dict[str, Any]]:
    """Preserve partial consented fields; provider data still needs confirmation."""
    year = month = day = None
    try:
        if req.birthyear and len(req.birthyear) == 4 and req.birthyear.isdigit():
            candidate = int(req.birthyear)
            if 1900 <= candidate <= date.today().year:
                year = candidate
        if req.birthday and len(req.birthday) == 4 and req.birthday.isdigit():
            month, day = int(req.birthday[:2]), int(req.birthday[2:])
            if (req.birthday_type or 'SOLAR').upper() in {'LUNAR','LEAP'}:
                if not (1 <= month <= 12 and 1 <= day <= 30):
                    raise ValueError()
            else:
                date(year or 2000, month, day)
    except (TypeError, ValueError):
        month = day = None
    calendar_type = {
        "SOLAR": "solar", "LUNAR": "lunar", "LEAP": "leap",
    }.get((req.birthday_type or "SOLAR").upper(), "solar")
    if calendar_type == 'lunar' and req.is_leap_month:
        calendar_type = 'leap'
    sijin_index = req.sijin_index if req.sijin_index is not None else -1
    if not -1 <= sijin_index <= 11:
        sijin_index = -1
    return {
        "name": (req.name or "").strip(),
        "gender": req.gender if req.gender in {"male", "female"} else None,
        "birth_year": year,
        "birth_month": month,
        "birth_day": day,
        "calendar_type": calendar_type,
        "sijin_index": sijin_index,
        "profile_complete": bool(req.profile_source == 'saved' and year and month and day
                                 and req.name and req.gender in {'male','female'}
                                 and req.sijin_index is not None),
    }


def _verified_kakao_request(req):
    # Saved-profile resumes are internal or session-authorized by the HTTP boundary.
    if req.profile_source != 'kakao':
        return req
    if not req.access_token:
        raise HTTPException(status_code=401, detail='카카오 로그인을 다시 진행해 주세요.')
    import json
    from urllib.request import Request, urlopen
    try:
        request = Request('https://kapi.kakao.com/v2/user/me',
                          headers={'Authorization':'Bearer '+req.access_token})
        with urlopen(request, timeout=8) as response:
            data = json.load(response)
        if str(data.get('id')) != req.kakao_id:
            raise ValueError('identity mismatch')
        account = data.get('kakao_account') or {}
    except Exception:
        raise HTTPException(status_code=401, detail='카카오 정보를 확인하지 못했습니다. 다시 로그인해 주세요.') from None
    def shared(key):
        return None if account.get(key+'_needs_agreement') else account.get(key)
    return req.model_copy(update=dict(name=shared('name'), gender=shared('gender'),
        birthyear=shared('birthyear'), birthday=shared('birthday'),
        birthday_type=account.get('birthday_type'), is_leap_month=bool(account.get('is_leap_month')),
        sijin_index=None, access_token=None))



def _public_profile(user: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": user.get("name", ""),
        "gender": user.get("gender", "male"),
        "birth_year": user.get("birth_year"),
        "birth_month": user.get("birth_month"),
        "birth_day": user.get("birth_day"),
        "calendar_type": user.get("calendar_type", "solar"),
        "sijin_index": user.get("sijin_index", -1),
        "profile_complete": bool(user.get("profile_complete")),
    }


@app.on_event('startup')
def initialize_menu_storage():
    try:
        menu_store.initialize()
    except menu_store.StorageUnavailable:
        pass  # Other sections stay usable; menu writes explicitly return 503.


class MenuExploreRequest(BaseModel):
    user_id: str = Field(min_length=6, max_length=55)
    token: str = Field(min_length=64, max_length=64)
    mode: str
    action: str
    expected_day: str = Field(pattern=r'^\d{4}-\d{2}-\d{2}$')
    expected_seen: int = Field(ge=0, le=1000000)


@app.post('/api/menu/explore')
def explore_menus(req: MenuExploreRequest):
    user = users_db.get(req.user_id)
    if not user or not user.get('profile_complete'):
        raise HTTPException(status_code=401, detail='다시 접속해 추천 메뉴를 불러와 주세요.')
    day = menu_store.today()
    def build(mode, history, excluded):
        from meal_sets import build_set
        return build_set(_birth_input_from_user(user, user.get('name', '')), day, mode, history, excluded)
    try:
        return menu_store.explore(req.user_id, day, build, token=req.token,
                                  mode=req.mode, action=req.action,
                                  expected_day=req.expected_day, expected_seen=req.expected_seen)
    except KeyError:
        raise HTTPException(status_code=403, detail='다시 접속해 추천 기록을 불러와 주세요.')
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except menu_store.StorageUnavailable:
        raise HTTPException(status_code=503, detail='추천 기록을 저장하지 못했습니다. 잠시 후 다시 시도해 주세요.')


class MealFeedbackRequest(BaseModel):
    token: str = Field(min_length=32, max_length=128)
    liked: Optional[bool] = None


@app.post("/api/menu/feedback")
def menu_feedback(req: MealFeedbackRequest):
    from app.engine.services.meal_feedback import update
    try:
        return update(req.token, liked=req.liked, seen=req.liked is None)
    except KeyError:
        raise HTTPException(status_code=404, detail="식단을 다시 불러와 주세요.")


@app.post("/api/auth/kakao")
def auth_kakao(req: KakaoAuthRequest, response: Response = None, request: Request = None):
    req = _verified_kakao_request(req)
    user_id = f"user_{req.kakao_id}"
    incoming_profile = _profile_from_kakao_request(req)
    try:
        saved = account_store.load(user_id)
    except account_store.StorageUnavailable:
        raise HTTPException(status_code=503, detail='저장된 회원 정보를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.')

    if user_id not in users_db:
        users_db[user_id] = {
            "user_id": user_id,
            "kakao_id": req.kakao_id,
            "name": (req.name or "").strip(),
            "gender": req.gender if req.gender in {"male", "female"} else None,
            "birth_year": None,
            "birth_month": None,
            "birth_day": None,
            "calendar_type": "solar",
            "sijin_index": -1,
            "profile_complete": False,
            "coin": 1000,
        }
        reports_db[user_id] = []

    wardrobe = _wardrobe_response(user_id)
    user = users_db[user_id]
    if saved and saved['confirmed']:
        user.update(saved['profile'], profile_complete=True)
    elif incoming_profile and any(incoming_profile.get(k) for k in ('name','birth_year','birth_month')):
        if saved:
            user.update(saved['profile'])
        user.update({k:v for k,v in incoming_profile.items() if v is not None and v != ''})
        try:
            account_store.save(user_id, _public_profile(user), confirmed=user['profile_complete'])
        except account_store.StorageUnavailable:
            raise HTTPException(status_code=503, detail='회원 정보를 저장하지 못했습니다. 다시 시도해 주세요.')
    elif saved:
        user.update(saved['profile'], profile_complete=saved['confirmed'])

    try:
        if not saved:
            account_store.save(user_id, _public_profile(user), confirmed=user['profile_complete'])
        assets = wallet_store.load(user_id, initial_balance=user['coin'],
                                   initial_reports=reports_db.get(user_id, []))
        user['coin'] = assets['balance']
        reports_db[user_id] = assets['reports']
        if response is not None and req.profile_source == 'kakao':
            token = session_store.issue(user_id)
            if request is not None:
                session_store.revoke(request.cookies.get(session_store.COOKIE))
            secure = bool(os.getenv('RENDER') or os.getenv('RENDER_SERVICE_ID') or
                          (request is not None and request.url.scheme == 'https'))
            response.set_cookie(session_store.COOKIE, token, max_age=session_store.TTL,
                                httponly=True, secure=secure, samesite='lax', path='/')
    except account_store.StorageUnavailable:
        raise HTTPException(status_code=503, detail='회원 정보를 저장하지 못했습니다. 다시 시도해 주세요.')

    has_profile = bool(user.get("profile_complete"))
    if has_profile:
        saju_res = get_saju_pillars_and_analysis(
            user["name"], user["gender"], user["birth_year"],
            user["birth_month"], user["birth_day"], user["calendar_type"],
            user["sijin_index"], menu_account_id=user_id,
            weather_profile=gyeongju_weather_cache.get(),
        )
        return {
            "status": "existing_user",
            "user_id": user_id,
            "coin_balance": user["coin"],
            "unlocked_reports": reports_db.get(user_id, []),
            **wardrobe,
            "saju_analysis": saju_res,
            "profile": _public_profile(user),
            "tarot_state": tarot_service.get_state(user_id),
        }
    return {
        "status": "new_user",
        "user_id": user_id,
        "coin_balance": user["coin"],
        "kakao_prefill": _public_profile(user),
        **wardrobe,
    }

@app.get('/api/auth/session')
def resume_account(request: Request):
    return auth_kakao(KakaoAuthRequest(kakao_id=request.state.account_id[5:]))


@app.post('/api/auth/logout')
def logout_account(request: Request, response: Response):
    session_store.revoke(request.cookies.get(session_store.COOKIE))
    response.delete_cookie(session_store.COOKIE, path='/')
    return {'status':'success'}


@app.post("/api/user/register-saju")
def register_saju(req: RegisterSajuRequest):
    if req.user_id not in users_db:
        raise HTTPException(status_code=401, detail='로그인 상태를 확인해 주세요.')
    if not req.name.strip():
        raise HTTPException(status_code=422, detail='이름을 입력해 주세요.')
    if req.gender not in {'male','female'} or req.calendar_type not in {'solar','lunar','leap'} or not -1 <= req.sijin_index <= 11:
        raise HTTPException(status_code=422, detail='성별·달력·생시를 확인해 주세요.')
    try:
        if not 1900 <= req.birth_year <= date.today().year:
            raise ValueError()
        if req.calendar_type == 'solar':
            if date(req.birth_year, req.birth_month, req.birth_day) > date.today():
                raise ValueError()
        elif not (1 <= req.birth_month <= 12 and 1 <= req.birth_day <= 30):
            raise ValueError()
    except ValueError:
        raise HTTPException(status_code=422, detail='생년월일을 확인해 주세요.')
    # Validate the converted lunar/solar input before persisting the profile.
    try:
        saju_res = get_saju_pillars_and_analysis(
            req.name, req.gender, req.birth_year, req.birth_month, req.birth_day,
            req.calendar_type, req.sijin_index, menu_account_id=req.user_id,
            weather_profile=gyeongju_weather_cache.get())
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail='생년월일과 달력 구분을 확인해 주세요.')
    try:
        account_store.save(req.user_id, req.model_dump(exclude={'user_id'}), confirmed=True)
    except account_store.StorageUnavailable:
        raise HTTPException(status_code=503, detail='사주 정보를 저장하지 못했습니다. 다시 시도해 주세요.')
    if req.user_id not in users_db:
        users_db[req.user_id] = {"coin": 1000}

    users_db[req.user_id].update({
        "name": req.name,
        "gender": req.gender,
        "birth_year": req.birth_year,
        "birth_month": req.birth_month,
        "birth_day": req.birth_day,
        "calendar_type": req.calendar_type,
        "sijin_index": req.sijin_index,
        "profile_complete": True,
    })

    return {
        "status": "success",
        "coin_balance": users_db[req.user_id]["coin"],
        "saju_analysis": saju_res,
        "profile": _public_profile(users_db[req.user_id]),
    }

def _wardrobe_response(user_id):
    try:
        return {"wardrobe_items": wardrobe_store.list_items(user_id)}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except wardrobe_store.StorageUnavailable:
        # An unavailable database is not an empty wardrobe.
        return {"wardrobe_items": None, "wardrobe_error": "옷장을 불러오지 못했습니다. 잠시 후 다시 시도해 주세요."}


@app.get("/api/fashion/weather")
def fashion_weather():
    """Korea-only rollout: fixed Gyeongju forecast, never browser GPS."""
    return weather_api_payload(gyeongju_weather_cache.get())


@app.get("/api/health/storage")
def storage_health():
    try:
        return {"status": "ok", "wardrobe": wardrobe_store.health(), "menus": menu_store.health()}
    except wardrobe_store.StorageUnavailable:
        raise HTTPException(status_code=503, detail="Wardrobe storage unavailable")


@app.get("/api/wardrobe")
def get_wardrobe(user_id: str):
    result = _wardrobe_response(user_id)
    if result.get("wardrobe_error"):
        raise HTTPException(status_code=503, detail=result["wardrobe_error"])
    return result


def _change_wardrobe(user_id, operation, item_id=None, item=None):
    try:
        items = wardrobe_store.mutate(user_id, operation, item_id, item)
        return {"status": "success", "wardrobe_items": items}
    except wardrobe_store.StorageUnavailable:
        raise HTTPException(status_code=503, detail="옷장에 저장하지 못했습니다. 잠시 후 다시 시도해 주세요.")
    except KeyError:
        raise HTTPException(status_code=404, detail="아이템을 찾지 못했습니다. 옷장을 다시 불러와 주세요.")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@app.post("/api/wardrobe/add")
def add_wardrobe(req: WardrobeItemRequest):
    return _change_wardrobe(req.user_id, "add", item=req.model_dump())


@app.put("/api/wardrobe/edit/{item_id}")
def edit_wardrobe(item_id: int, req: WardrobeItemRequest):
    return _change_wardrobe(req.user_id, "edit", item_id, req.model_dump())


@app.delete("/api/wardrobe/delete/{item_id}")
def delete_wardrobe(item_id: int, user_id: str):
    return _change_wardrobe(user_id, "delete", item_id)

@app.post("/api/reports/unlock")
def unlock_report(req: UnlockReportRequest):
    if req.user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    prices = {'daewoon':450, 'sinnian':300, 'gunghap':350,
              'wealth':220, 'business':220, 'love':220, 'health':220, 'study':220}
    if req.report_key not in prices:
        raise HTTPException(status_code=422, detail='지원하지 않는 리포트입니다.')
    cost = prices[req.report_key]
    user = hydrate_account(req.user_id)
    if any(r['report_key'] == req.report_key for r in reports_db[req.user_id]):
        return {'status':'success', 'new_balance':user['coin'], 'unlocked_reports':reports_db[req.user_id]}
    if user["coin"] < cost:
        raise HTTPException(status_code=400, detail="Insufficient coins")
    if req.report_key == "gunghap":
        required = (
            req.partner_name, req.partner_gender, req.partner_birth_year,
            req.partner_birth_month, req.partner_birth_day,
        )
        if not all(required):
            raise HTTPException(status_code=400, detail="상대방 사주 정보를 모두 입력해 주세요.")
        if req.partner_gender not in {"male", "female"}:
            raise HTTPException(status_code=400, detail="상대방 성별 값이 올바르지 않습니다.")
        if req.partner_calendar_type not in {"solar", "lunar", "leap"}:
            raise HTTPException(status_code=400, detail="상대방 달력 구분이 올바르지 않습니다.")
        if req.partner_sijin_index is None or not -1 <= req.partner_sijin_index <= 11:
            raise HTTPException(status_code=400, detail="상대방 출생시간 값이 올바르지 않습니다.")
        try:
            date(req.partner_birth_year, req.partner_birth_month, req.partner_birth_day)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="상대방 생년월일이 올바르지 않습니다.") from exc
    
    rep_data = generate_detailed_report(
        req.report_key,
        req.sub_option,
        req.partner_name,
        req.relation,
        user.get("name", "회원"),
        user=user,
        partner={
            "name": req.partner_name,
            "gender": req.partner_gender,
            "birth_year": req.partner_birth_year,
            "birth_month": req.partner_birth_month,
            "birth_day": req.partner_birth_day,
            "calendar_type": req.partner_calendar_type,
            "sijin_index": req.partner_sijin_index,
        } if req.report_key == "gunghap" else None,
    )
    new_report = {
        "report_key": req.report_key,
        "report_title": rep_data["title"],
        "report_content": rep_data["content"],
        "created_at": datetime.date.today().strftime("%Y.%m.%d")
    }
    if req.report_key == 'sinnian':
        new_report.update(narrative_version=rep_data.get('narrative_version'),
                          report_year=rep_data.get('report_year'))

    try:
        assets = wallet_store.buy_report(req.user_id, req.report_key, cost, new_report)
    except ValueError:
        raise HTTPException(status_code=400, detail='Insufficient coins')
    except wallet_store.StorageUnavailable:
        raise HTTPException(status_code=503, detail='열람 정보를 저장하지 못했습니다. 다시 시도해 주세요.')
    user['coin'] = assets['balance']
    reports_db[req.user_id] = assets['reports']

    return {
        "status": "success",
        "new_balance": user["coin"],
        "unlocked_reports": reports_db[req.user_id]
    }


class RefreshAnnualRequest(BaseModel):
    user_id: str


@app.post('/api/reports/refresh-annual')
def refresh_annual_report(req: RefreshAnnualRequest):
    """Explicit free upgrade of an owned annual report, not a new purchase."""
    import re
    user = hydrate_account(req.user_id)
    original = next((r for r in reports_db[req.user_id] if r['report_key'] == 'sinnian'), None)
    if original is None:
        raise HTTPException(status_code=403, detail='먼저 올해운세를 열람해 주세요.')
    if original.get('narrative_version') == ANNUAL_NARRATIVE_VERSION:
        return dict(status='success', new_balance=user['coin'], unlocked_reports=reports_db[req.user_id])
    if not user.get('profile_complete'):
        raise HTTPException(status_code=422, detail='사주 정보를 먼저 확인해 주세요.')
    # Keep the purchased year. Never silently turn an older purchase into this year.
    year = original.get('report_year')
    if not isinstance(year, int) or isinstance(year, bool):
        matched = (re.search(r'data-report-year=[\"\x27](\d{4})[\"\x27]', original.get('report_content', ''))
                   or re.match(r'^(\d{4})\b', original.get('report_title', '')))
        year = int(matched.group(1)) if matched else None
    if year is None or not 1900 <= year <= 9999:
        raise HTTPException(status_code=422, detail='기존 풀이의 연도를 확인하지 못했습니다. 원문은 그대로 보관되어 있습니다.')
    try:
        generated = generate_detailed_report('sinnian', '기본', '', '', user.get('name', '회원'),
                                             user=user, report_year=year)
    except ValueError:
        raise HTTPException(status_code=422, detail='현재 저장한 사주 정보와 기존 풀이 연도를 확인해 주세요.')
    replacement = dict(report_title=generated['title'], report_content=generated['content'],
                       narrative_version=ANNUAL_NARRATIVE_VERSION, report_year=year,
                       refreshed_at=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).isoformat(),
                       profile_basis='current_saved_profile')
    try:
        assets = wallet_store.refresh_owned_annual(req.user_id, original, replacement)
    except ValueError:
        raise HTTPException(status_code=409, detail='보관함이 변경되었습니다. 새로고침한 뒤 다시 확인해 주세요.')
    except wallet_store.StorageUnavailable:
        raise HTTPException(status_code=503, detail='새 풀이를 저장하지 못했습니다. 기존 풀이와 복채는 유지됩니다.')
    user['coin'] = assets['balance']
    reports_db[req.user_id] = assets['reports']
    return dict(status='success', new_balance=user['coin'], unlocked_reports=assets['reports'])

# Date-specific Korean daily zodiac/star guides.
from zodiac_daily import build_daily_zodiac


@app.get("/api/zodiac-fortune")
def get_zodiac_fortune(type: str, key: str, response: Response):
    response.headers["Cache-Control"] = "no-store"
    try:
        return build_daily_zodiac(type, key)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


from tarot_catalog import DECK as TAROT_DECK


class TarotDrawRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=100)
    slot: int = Field(ge=1, le=3)
    request_id: str = Field(min_length=16, max_length=80, pattern=r"^[a-zA-Z0-9_-]+$")
    is_paid: bool = False
    expected_day: Optional[str] = Field(default=None, pattern=r'^\d{4}-\d{2}-\d{2}$')


@app.post("/api/daily-tarot/draw")
def draw_daily_tarot(req: TarotDrawRequest):
    try:
        return tarot_service.draw(users_db, TAROT_DECK, random.choice, **req.model_dump())
    except tarot_service.DrawError as exc:
        raise HTTPException(status_code=exc.status, detail=exc.detail)
    except wardrobe_store.StorageUnavailable:
        raise HTTPException(status_code=503, detail={'code':'storage_unavailable','message':'카드를 저장하지 못했습니다. 같은 요청으로 다시 확인해 주세요.'})


@app.get('/api/daily-tarot/state')
def daily_tarot_state(user_id: str):
    if user_id not in users_db:
        raise HTTPException(status_code=401, detail='로그인 상태를 확인해 주세요.')
    return tarot_service.get_state(user_id)



@app.get("/api/daily-tarot")
def get_daily_tarot(slot: int, user_id: Optional[str] = None, is_paid: Optional[bool] = False):
    # Legacy previews stay read-only: coin spending requires an explicit POST.
    if is_paid:
        raise HTTPException(status_code=405, detail="페이지를 새로고침한 뒤 카드를 선택해 주세요.")
    card = random.choice(TAROT_DECK)
    return {**card, "description": tarot_service.DESCRIPTIONS.get(card["name"], "")}

@app.post("/api/user/charge-coin")
def charge_coin(req: ChargeCoinRequest):
    # Explicit server-side allowlist only; never infer tester status from client data.
    testers = {v.strip() for v in os.getenv('DALHA_TEST_USER_IDS', '').split(',') if v.strip()}
    if req.user_id not in testers:
        raise HTTPException(status_code=403, detail='가상 충전은 등록된 테스트 계정에서만 가능합니다. 실제 결제는 진행되지 않습니다.')
    try:
        with wallet_store.locked(req.user_id) as (_, _, assets):
            if assets['balance'] + req.amount > 1000000:
                raise ValueError('test_balance_limit')
            assets['balance'] += req.amount
    except ValueError:
        raise HTTPException(status_code=400, detail='테스트 복채 보유 한도를 초과했습니다.')
    users_db[req.user_id]['coin'] = assets['balance']
    return {'status':'success', 'new_balance':assets['balance'], 'test_only':True}

@app.get("/api/today-ganji")
def get_today_ganji():
    kst_now = datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=9))
    )
    today_date = kst_now.date()

    solar = Solar.fromYmd(
        today_date.year,
        today_date.month,
        today_date.day
    )
    lunar = solar.getLunar()

    return {
        "date": today_date.strftime("%Y-%m-%d"),
        "cheongan": lunar.getDayGan(),
        "jiji": lunar.getDayZhi(),
        "ganji": lunar.getDayInGanZhi()
    }

@app.get("/api/test-saju-engine")
def test_saju_engine(
    y: int = 1978,
    m: int = 8,
    d: int = 13,
    cal_type: str = "solar",
    gender: str = "male"
):
    # A. 현재 root main.py 계산 결과
    root_result = get_saju_pillars_and_analysis(
        name="테스트",
        gender=gender,
        y=y,
        m=m,
        d=d,
        cal_type=cal_type,
        sijin=-1
    )
    root_pillars = root_result["saju_data"]["pillars_detail"]

    root_year = f"{root_pillars['year']['cg']}{root_pillars['year']['jj']}"
    root_month = f"{root_pillars['month']['cg']}{root_pillars['month']['jj']}"
    root_day = f"{root_pillars['day']['cg']}{root_pillars['day']['jj']}"
    root_day_master = root_pillars["day"]["cg"]

    # B. backend 엔진 계산 결과
    b_calendar_type = "lunar" if cal_type in ["lunar", "leap"] else "solar"
    b_is_leap = (cal_type == "leap")

    backend_result = calculate_saju(
        birth_date=date(y, m, d),
        calendar_type=b_calendar_type,
        is_leap_month=b_is_leap,
        birth_time=None,
        time_unknown=True,
        gender=gender
    )

    backend_year = backend_result.year.label
    backend_month = backend_result.month.label
    backend_day = backend_result.day.label
    backend_day_master = backend_result.day_master

    return {
        "engine_version": root_result["daily_fortune"].get("engine_version"),
        "overall_version": root_result["daily_fortune"].get("evidence_summary", {}).get("overall", {}).get("version"),
        "input": {
            "year": y,
            "month": m,
            "day": d,
            "cal_type": cal_type,
            "gender": gender
        },
        "fashion_color_basis": root_result["daily_fortune"]["fashion_color_basis"],
        "comparison": {
            "year_pillar": {
                "root_main": root_year,
                "backend_engine": backend_year,
                "is_match": root_year == backend_year
            },
            "month_pillar": {
                "root_main": root_month,
                "backend_engine": backend_month,
                "is_match": root_month == backend_month
            },
            "day_pillar": {
                "root_main": root_day,
                "backend_engine": backend_day,
                "is_match": root_day == backend_day
            },
            "day_master": {
                "root_main": root_day_master,
                "backend_engine": backend_day_master,
                "is_match": root_day_master == backend_day_master
            }
        }
    }
    
if os.path.exists("index.html"):
    @app.get("/")
    def serve_index():
        return FileResponse("index.html")

    @app.get("/design/{variant}", include_in_schema=False)
    def serve_design_comparison(variant: str):
        if variant == "fashion-review":
            return FileResponse("assets/fashion-review.html", headers={"X-Robots-Tag": "noindex, nofollow"})
        if variant == "fashion-review-fifty-female":
            return FileResponse("assets/fashion-review-fifty-female.html", headers={"X-Robots-Tag": "noindex, nofollow"})
        if variant == "fashion-age-research":
            return FileResponse("assets/fashion-age-research.html", headers={"X-Robots-Tag": "noindex, nofollow"})
        if variant == "compare":
            return FileResponse("assets/design-compare.html", headers={"X-Robots-Tag": "noindex, nofollow"})
        if variant not in {"clear", "moonlight"}:
            raise HTTPException(status_code=404, detail="Unknown design")
        return FileResponse("index.html", headers={"X-Robots-Tag": "noindex, nofollow"})
