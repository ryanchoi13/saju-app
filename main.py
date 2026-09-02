import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
from datetime import date
from app.engine.pillars import calculate_saju
from app.engine.constants import GAN_WUXING
from lunar_python import Solar
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import datetime
import os
import random
 
app = FastAPI(title="DALHA - Style Destiny Backend Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- In-Memory DB Models ---
users_db: Dict[str, Dict[str, Any]] = {}
wardrobe_db: Dict[str, List[Dict[str, Any]]] = {}
reports_db: Dict[str, List[Dict[str, Any]]] = {}

# --- Request/Response Models ---
class KakaoAuthRequest(BaseModel):
    kakao_id: str
    name: Optional[str] = "달하 회원"
    gender: Optional[str] = "male"
    birthyear: Optional[str] = "1978"
    birthday: Optional[str] = "0813"
    birthday_type: Optional[str] = "SOLAR"

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
    category: str
    nickname: Optional[str] = ""
    colors: List[str]
    materials: List[str]

class UnlockReportRequest(BaseModel):
    user_id: str
    report_key: str
    cost: int
    sub_option: Optional[str] = "기본"
    partner_name: Optional[str] = "상대방"
    relation: Optional[str] = "인연/조화"

class ChargeCoinRequest(BaseModel):
    user_id: str
    amount: int

# --- Saju Calculation Constants & Engine ---
CHEONGAN = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
JIJI = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]

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

def calculate_biorhythm(birth_year: int, birth_month: int, birth_day: int):
    import math
    today = datetime.date.today()
    b_date = datetime.date(birth_year, birth_month, birth_day)
    days_lived = (today - b_date).days

    p_val = round(math.sin(2 * math.pi * days_lived / 23) * 100)
    e_val = round(math.sin(2 * math.pi * days_lived / 28) * 100)
    i_val = round(math.sin(2 * math.pi * days_lived / 33) * 100)

    def get_status(v):
        if v >= 50: return "고조기"
        if v > -50: return "안정기"
        return "저조기"

    return {
        "days_lived": days_lived,
        "physical": {"val": p_val, "status": get_status(p_val)},
        "emotional": {"val": e_val, "status": get_status(e_val)},
        "intellectual": {"val": i_val, "status": get_status(i_val)},
        "overall_summary": f"신체 에너지가 {get_status(p_val)}이며 지성적 판단력이 우수한 흐름입니다. 중요한 의사결정에 적합한 타이밍입니다."
    }

def get_saju_pillars_and_analysis(name: str, gender: str, y: int, m: int, d: int, cal_type: str, sijin: int):
    backend_calendar_type = "lunar" if cal_type in ["lunar", "leap"] else "solar"
    backend_is_leap = (cal_type == "leap")

    backend_saju = calculate_saju(
        birth_date=date(y, m, d),
        calendar_type=backend_calendar_type,
        is_leap_month=backend_is_leap,
        birth_time=None,
        time_unknown=True,
        gender=gender
    )

    cg_y = backend_saju.year.gan
    jj_y = backend_saju.year.zhi
    cg_m = backend_saju.month.gan
    jj_m = backend_saju.month.zhi
    cg_d = backend_saju.day.gan
    jj_d = backend_saju.day.zhi
    kst_now = datetime.datetime.now(
        datetime.timezone(datetime.timedelta(hours=9))
    )
    today_date = kst_now.date()

    today_solar = Solar.fromYmd(
        today_date.year,
        today_date.month,
        today_date.day
    )
    today_lunar = today_solar.getLunar()

    today_gan = today_lunar.getDayGan()
    today_zhi = today_lunar.getDayZhi()
    today_ganji = today_lunar.getDayInGanZhi()

    natal_gan_han = backend_saju.day_master_han
    natal_element = GAN_WUXING[natal_gan_han]
    today_element = GAN_WUXING[today_gan]
    
    generates = {
        "木": "火",
        "火": "土",
        "土": "金",
        "金": "水",
        "水": "木"
    }

    controls = {
        "木": "土",
        "土": "水",
        "水": "火",
        "火": "金",
        "金": "木"
    }

    if natal_element == today_element:
        element_relation = "same"
    elif generates[today_element] == natal_element:
        element_relation = "supported"
    elif generates[natal_element] == today_element:
        element_relation = "output"
    elif controls[natal_element] == today_element:
        element_relation = "wealth"
    else:
        element_relation = "pressure"
    
    if sijin >= 0:
        cg_h = CHEONGAN[(sijin * 2) % 10]
        jj_h = JIJI[sijin % 12]
    else:
        cg_h, jj_h = "무", "진"

    elements_weight = {"wood": 15, "fire": 25, "earth": 45, "metal": 0, "water": 15}
    if cg_d in ["경", "신"] or jj_d in ["신", "유"]:
        elements_weight["metal"] = 20
        elements_weight["earth"] = 25

    current_age = datetime.date.today().year - y + 1

    relation_fortunes = {
        "same": {
            "score": 78,
            "title": "내 기운을 단단히 다지는 날",
            "advice": "오늘은 나와 비슷한 기운이 강해집니다. 자신감은 살리되 고집이 앞서지 않도록 균형을 잡는 것이 좋습니다."
        },
        "supported": {
            "score": 90,
            "title": "도움과 기회가 따라오는 날",
            "advice": "오늘의 기운이 나를 북돋아 주는 흐름입니다. 새로운 제안이나 주변의 도움을 적극적으로 활용해 보세요."
        },
        "output": {
            "score": 82,
            "title": "능력을 펼치고 표현하기 좋은 날",
            "advice": "내 기운을 밖으로 발산하기 좋은 날입니다. 아이디어를 표현하거나 미뤄둔 일을 실행하면 성과를 만들기 좋습니다."
        },
        "wealth": {
            "score": 86,
            "title": "실속과 성과를 챙기기 좋은 날",
            "advice": "현실적인 결과와 재물의 흐름에 집중하기 좋은 날입니다. 계획을 구체적인 행동으로 옮겨 보세요."
        },
        "pressure": {
            "score": 68,
            "title": "서두르기보다 균형이 필요한 날",
            "advice": "외부의 요구나 부담을 크게 느낄 수 있습니다. 무리하게 밀어붙이기보다 우선순위를 정해 차분히 대응하는 것이 좋습니다."
        }
    }

    today_fortune = relation_fortunes[element_relation]

    return {
        "user_name": name,
        "birth_summary": f"{y}년 {m}월 {d}일생 · {'남성' if gender == 'male' else '여성'}",
        "current_age": current_age,
        "biorhythm": calculate_biorhythm(y, m, d),
        "saju_data": {
            "singang_label": "신약(身弱) 사주 · 보완형",
            "pillars_detail": {
                "year": {"cg": cg_y, "cg_elem": ELEM_MAP.get(cg_y, "earth"), "jj": jj_y, "jj_elem": ELEM_MAP.get(jj_y, "earth"), "jijanggan": JIJANGGAN_MAP.get(jj_y, [])},
                "month": {"cg": cg_m, "cg_elem": ELEM_MAP.get(cg_m, "fire"), "jj": jj_m, "jj_elem": ELEM_MAP.get(jj_m, "metal"), "jijanggan": JIJANGGAN_MAP.get(jj_m, [])},
                "day": {"cg": cg_d, "cg_elem": ELEM_MAP.get(cg_d, "earth"), "jj": jj_d, "jj_elem": ELEM_MAP.get(jj_d, "fire"), "jijanggan": JIJANGGAN_MAP.get(jj_d, [])},
                "hour": {"cg": cg_h, "cg_elem": ELEM_MAP.get(cg_h, "earth"), "jj": jj_h, "jj_elem": ELEM_MAP.get(jj_h, "earth"), "jijanggan": JIJANGGAN_MAP.get(jj_h, [])}
            },
            "elements": elements_weight
        },
        "daily_fortune": {
            "title": today_fortune["title"],
            "score": today_fortune["score"],
            "mode_badge": f"운세 {today_fortune['score']}점",
            "badge_style": "background:#FEF3C7; color:#78350F; border:1px solid #FDE68A;",
            "advice": today_fortune["advice"],
            "time_flow": {
                "morning": "준비와 기획에 최적화된 시간대입니다. 차분히 일정을 정돈하세요.",
                "afternoon": "대인관계 및 비즈니스 협상에서 유리한 주도권을 쥐게 됩니다.",
                "evening": "하루를 정리하며 나만의 시간을 가질 때 기운이 완벽히 충전됩니다."
            },
            "wada_palette": {
                "theme": "명경지수(明鏡止水) · 지적인 냉철함",
                "mood_desc": "깊은 미드나잇 인디고와 안개빛 스카이블루가 만나 사주의 금전운과 전문성을 견고히 세웁니다.",
                "mode": "harmony",
                "style_mood": "casual",
                "mood_tag": "🏃 캐주얼 & 액티브",
                "top": {"name": "미드나잇 인디고", "hex": "#1F3044", "standard_color": "네이비"},
                "bottom": {"name": "포그 스카이", "hex": "#8CA6B5", "standard_color": "스카이블루"},
                "point": None
            },
            "lucky_item": "실버 메탈 시계",
            "lucky_number": "4, 9",
            "lucky_direction": "정서쪽 (백호 방위)",
            "recommended_menu": "속이 편안한 영양 솥밥",
            "mindset": "원칙을 지키되 상황에 맞게 유연하게 대처하기",
            "action": "오늘 완료해야 할 우선순위 3가지 메모하기",
            "talisman": {
                "title": "재물만복부 (生財萬福)",
                "power": "금전운 상승 · 투자 결실 극대화",
                "desc": "사방에서 재물과 복록이 깃들게 하는 전통 비급 수제 부적입니다.",
                "talisman_type": "metal_wealth"
            }
        }
    }

# --- Detailed Report Generator Engine ---
def generate_detailed_report(report_key: str, sub_option: str, partner_name: str, relation: str, user_name: str) -> Dict[str, str]:
    if report_key == "sinnian":
        title = f"2026 丙午년 {user_name}님 정밀 신년운세 & 12개월 토정비결"
        content = f"""
        <div style="text-align:left; line-height:1.85; color:#1E293B;">
            <div style="background:#ECFDF5; border-left:4px solid #10B981; padding:16px; border-radius:14px; margin-bottom:18px;">
                <h4 style="font-size:16px; font-weight:800; color:#065F46; margin-bottom:6px;">📜 Chapter 1. 2026 丙午년 총운 (總論)</h4>
                <p style="font-size:13.5px; color:#047857; margin:0; line-height:1.75;">
                    2026년 丙午(병오)년은 타오르는 태양과 질주하는 적토마가 만난 형국으로, 사주 명식 내에 웅크리고 있던 잠재력이 본격적으로 발현되는 '도약과 대발(大發)의 해'입니다. 
                    그동안 준비해 온 역량이 외부로 드러나며 정체되었던 문제들이 일시에 해결의 실마리를 찾게 됩니다. 특히 상반기에는 내실과 기틀을 닦고, 하반기로 접어들수록 재물과 명예가 배가되는 비도진천(飛渡震天)의 강렬한 운의 흐름을 타게 됩니다.
                </p>
            </div>

            <div style="display:flex; flex-direction:column; gap:12px; margin-bottom:20px;">
                <div style="background:#F8FAFC; border:1px solid #E2E8F0; padding:14px 16px; border-radius:14px;">
                    <h5 style="font-size:14.5px; font-weight:800; color:#D97706; margin-bottom:4px;">💰 Chapter 2. 2026 재물운 & 투자 가이드</h5>
                    <p style="font-size:13px; color:#475569; margin:0; line-height:1.7;">
                        문서운(文書運)과 정재(正財)의 흐름이 견고하게 맞물려 실속 있는 자산 증식이 가능합니다. 단기적인 투기나 고위험 상품보다는 중장기 부동산, 안정적인 배당 자산, 실물 자산과의 궁합이 매우 우수합니다. 5월과 10월에 목돈이 들어올 운기가 강하며, 불필요한 충동 소비와 남을 위한 보증·무리한 대출만 피한다면 든든한 곳간을 채우는 한 해가 됩니다.
                    </p>
                </div>

                <div style="background:#F8FAFC; border:1px solid #E2E8F0; padding:14px 16px; border-radius:14px;">
                    <h5 style="font-size:14.5px; font-weight:800; color:#2563EB; margin-bottom:4px;">🏢 Chapter 3. 2026 직장·사업 & 커리어운</h5>
                    <p style="font-size:13px; color:#475569; margin:0; line-height:1.7;">
                        조직 내에서 자신의 발언권과 입지가 강화되며 승진, 영전, 프로젝트 총괄 등 주도적인 역할을 맡게 됩니다. 사업가라면 새로운 시장 개척이나 거래처 확대에 최적의 시기입니다. 다만 자신의 주장을 너무 강하게 밀어붙이면 주변의 시기나 견제를 부를 수 있으니, 성과는 팀원 및 파트너와 나누는 포용력을 발휘할 때 명예가 더욱 빛납니다.
                    </p>
                </div>

                <div style="background:#F8FAFC; border:1px solid #E2E8F0; padding:14px 16px; border-radius:14px;">
                    <h5 style="font-size:14.5px; font-weight:800; color:#DC2626; margin-bottom:4px;">🌿 Chapter 4. 2026 가정·건강 & 섭생 가이드</h5>
                    <p style="font-size:13px; color:#475569; margin:0; line-height:1.7;">
                        화기(火氣)가 강해지는 여름철(음력 4~6월)에는 혈압, 심혈관계, 수면 부족에 각별히 유의해야 합니다. 과도한 열정을 식혀주는 충분한 수분 섭취와 규칙적인 유산소 운동이 필수적입니다. 가정적으로는 화목이 깃드나 집안의 사소한 결정에서 독단적인 판단을 피하고 가족들의 의견을 경청할 때 가정궁이 더욱 평안해집니다.
                    </p>
                </div>

                <div style="background:#F8FAFC; border:1px solid #E2E8F0; padding:14px 16px; border-radius:14px;">
                    <h5 style="font-size:14.5px; font-weight:800; color:#9333EA; margin-bottom:4px;">💖 Chapter 5. 2026 이성 & 대인관계운</h5>
                    <p style="font-size:13px; color:#475569; margin:0; line-height:1.7;">
                        나에게 실질적인 도움을 주는 귀인(貴人)들이 사방에서 모여듭니다. 미혼자는 지적이고 당찬 성향의 인연과 깊은 결실을 맺을 수 있으며, 기혼자는 배우자와의 협업을 통해 가정을 번창시키는 시기입니다. 겉치레보다는 진정성 있는 태도로 대인관계를 맺을 때 평생을 함께할 든든한 조력자를 얻게 됩니다.
                    </p>
                </div>
            </div>

            <h4 style="font-size:15.5px; font-weight:800; color:#0F172A; margin:20px 0 12px; border-bottom:2px solid #E2E8F0; padding-bottom:8px;">📅 Chapter 6. 1월부터 12월까지 월별 정밀 토정비결</h4>
            <div style="display:flex; flex-direction:column; gap:10px;">
                <div style="background:#F8FAFC; border:1px solid #E2E8F0; padding:12px 14px; border-radius:12px; border-left:4px solid #2D6A4F;">
                    <strong style="color:#0F172A; font-size:13.5px;">1월 (正月):</strong> <span style="color:#475569; font-size:13px;">새로운 계획의 기틀을 다지는 달입니다. 조급하게 결론을 내리기보다 주변 동향을 살피고 기초 체력을 다지는 것이 유리합니다. (재물: 보통, 길방: 동쪽)</span>
                </div>
                <div style="background:#F8FAFC; border:1px solid #E2E8F0; padding:12px 14px; border-radius:12px; border-left:4px solid #2D6A4F;">
                    <strong style="color:#0F172A; font-size:13.5px;">2월 (二月):</strong> <span style="color:#475569; font-size:13px;">막혔던 흐름이 풀리고 귀인의 소식이 들려옵니다. 성실히 준비해 온 일에서 작은 결실이 나타나기 시작합니다. (재물: 길, 길방: 남쪽)</span>
                </div>
                <div style="background:#F8FAFC; border:1px solid #E2E8F0; padding:12px 14px; border-radius:12px; border-left:4px solid #2D6A4F;">
                    <strong style="color:#0F172A; font-size:13.5px;">3월 (三月):</strong> <span style="color:#475569; font-size:13px;">문서 계약이나 협상에서 매우 유리한 위치를 점합니다. 자산 매입이나 계약 체결에 길한 운이 따릅니다. (재물: 대길, 길방: 서북쪽)</span>
                </div>
                <div style="background:#F8FAFC; border:1px solid #E2E8F0; padding:12px 14px; border-radius:12px; border-left:4px solid #2D6A4F;">
                    <strong style="color:#0F172A; font-size:13.5px;">4월 (四月):</strong> <span style="color:#475569; font-size:13px;">지출 관리가 필요한 달입니다. 불필요한 충동구매나 무리한 확장을 자제하고 현금 유동성을 확보하세요. (재물: 주의, 건강: 휴식 필요)</span>
                </div>
                <div style="background:#F8FAFC; border:1px solid #E2E8F0; padding:12px 14px; border-radius:12px; border-left:4px solid #2D6A4F;">
                    <strong style="color:#0F172A; font-size:13.5px;">5월 (五月):</strong> <span style="color:#475569; font-size:13px;">상반기 최고의 황금기입니다. 직장 내 승진운과 사업상 대형 계약이 성사되며 명예가 크게 드높아집니다. (재물: 대길, 사업: 승승장구)</span>
                </div>
                <div style="background:#F8FAFC; border:1px solid #E2E8F0; padding:12px 14px; border-radius:12px; border-left:4px solid #2D6A4F;">
                    <strong style="color:#0F172A; font-size:13.5px;">6월 (六月):</strong> <span style="color:#475569; font-size:13px;">체력 안배가 중요한 시기입니다. 무더위 속 무리한 일정은 피하고 충분한 수면과 휴식을 통해 내실을 다지세요. (건강: 유의, 대인: 원만)</span>
                </div>
                <div style="background:#F8FAFC; border:1px solid #E2E8F0; padding:12px 14px; border-radius:12px; border-left:4px solid #2D6A4F;">
                    <strong style="color:#0F172A; font-size:13.5px;">7월 (七月):</strong> <span style="color:#475569; font-size:13px;">재물운이 안정세로 돌아서며 성과에 대한 합당한 보상이 주어집니다. 가족과 함께하는 시간이 큰 힘이 됩니다. (재물: 길, 가정: 평안)</span>
                </div>
                <div style="background:#F8FAFC; border:1px solid #E2E8F0; padding:12px 14px; border-radius:12px; border-left:4px solid #2D6A4F;">
                    <strong style="color:#0F172A; font-size:13.5px;">8월 (八月):</strong> <span style="color:#475569; font-size:13px;">주변의 시기나 구설을 주의해야 합니다. 원칙을 엄격히 지키고 감정적인 대응을 삼가면 화가 복으로 바뀝니다. (대인: 신중, 재물: 보통)</span>
                </div>
                <div style="background:#F8FAFC; border:1px solid #E2E8F0; padding:12px 14px; border-radius:12px; border-left:4px solid #2D6A4F;">
                    <strong style="color:#0F172A; font-size:13.5px;">9월 (九月):</strong> <span style="color:#475569; font-size:13px;">가을의 결실이 무르익습니다. 상반기에 뿌려둔 노력들이 풍성한 결과물로 수확되는 풍요로운 달입니다. (재물: 대길, 명예: 상승)</span>
                </div>
                <div style="background:#F8FAFC; border:1px solid #E2E8F0; padding:12px 14px; border-radius:12px; border-left:4px solid #2D6A4F;">
                    <strong style="color:#0F172A; font-size:13.5px;">10월 (十月):</strong> <span style="color:#475569; font-size:13px;">뜻밖의 횡재수나 새로운 사업적 제안이 찾아옵니다. 신뢰할 수 있는 파트너와의 협업이 큰 성과를 냅니다. (재물: 횡재수, 사업: 확장)</span>
                </div>
                <div style="background:#F8FAFC; border:1px solid #E2E8F0; padding:12px 14px; border-radius:12px; border-left:4px solid #2D6A4F;">
                    <strong style="color:#0F172A; font-size:13.5px;">11월 (十一月):</strong> <span style="color:#475569; font-size:13px;">한 해의 실적을 정돈하고 조직 내 인간관계를 다질 때입니다. 베푼 만큼 더 큰 신뢰로 되돌아옵니다. (대인: 길, 재물: 안정)</span>
                </div>
                <div style="background:#F8FAFC; border:1px solid #E2E8F0; padding:12px 14px; border-radius:12px; border-left:4px solid #2D6A4F;">
                    <strong style="color:#0F172A; font-size:13.5px;">12월 (十二月):</strong> <span style="color:#475569; font-size:13px;">안정과 번영 속에 보람찬 한 해를 마무리합니다. 다음 해의 더 큰 도약을 위한 튼튼한 토대가 완성됩니다. (총평: 대길 만복)</span>
                </div>
            </div>
        </div>
        """
    elif report_key == "gunghap":
        title = f"{user_name}님 & {partner_name}님 정통 사주 궁합 감명서"
        content = f"""
        <div style="text-align:left; line-height:1.85; color:#1E293B;">
            <div style="background:#FFF1F2; border-left:4px solid #E11D48; padding:16px; border-radius:14px; margin-bottom:18px;">
                <h4 style="font-size:16px; font-weight:800; color:#9F1239; margin-bottom:6px;">💞 인연 총평 ({relation}) : 수화기제(水火旣濟)의 조화</h4>
                <p style="font-size:13.5px; color:#BE123C; margin:0; line-height:1.75;">
                    두 사람의 사주는 서로의 부족한 오행 기운을 완벽하게 채워주는 상생(相生)의 명식입니다. 
                    한 사람의 뜨거운 열정과 결단력을 다른 한 사람의 차분한 지혜와 포용력이 균형 있게 감싸 안아, 함께할수록 서로의 인생 운기가 배가되는 최상의 인연 배합을 이루고 있습니다.
                </p>
            </div>

            <div style="display:flex; flex-direction:column; gap:14px;">
                <div style="background:#F8FAFC; border:1px solid #E2E8F0; padding:16px; border-radius:14px;">
                    <h5 style="font-size:14.5px; font-weight:800; color:#0F172A; margin-bottom:6px;">1. 겉궁합 (성격, 기질 및 소통 스타일의 조화)</h5>
                    <p style="font-size:13px; color:#475569; margin:0; line-height:1.7;">
                        {user_name}님의 논리정연하고 신중한 면모와 {partner_name}님의 따뜻하고 배려 깊은 성향이 만나 일상에서 깊은 정서적 유대감을 형성합니다. 
                        서로의 대화 방식이 달라 생길 수 있는 작은 오해도 진솔한 대화를 통해 쉽게 풀리며, 함께 있을 때 가장 나다운 편안함을 느끼게 됩니다.
                    </p>
                </div>

                <div style="background:#F8FAFC; border:1px solid #E2E8F0; padding:16px; border-radius:14px;">
                    <h5 style="font-size:14.5px; font-weight:800; color:#0F172A; margin-bottom:6px;">2. 속궁합 (오행 상생 밸런스 & 무의식적 애착도)</h5>
                    <p style="font-size:13px; color:#475569; margin:0; line-height:1.7;">
                        사주 명식의 일간(日干)과 지지(地支)가 은근한 합(合)을 이루고 있어 시간이 흐를수록 신뢰와 애정이 더욱 견고해집니다. 
                        갈등이 생기더라도 쉽게 인연의 끈이 끊어지지 않으며, 서로의 존재 자체가 심리적인 안식처 역할을 해주는 깊은 속궁합을 자랑합니다.
                    </p>
                </div>

                <div style="background:#F8FAFC; border:1px solid #E2E8F0; padding:16px; border-radius:14px;">
                    <h5 style="font-size:14.5px; font-weight:800; color:#0F172A; margin-bottom:6px;">3. 재물 및 공동 목표 달성 시너지</h5>
                    <p style="font-size:13px; color:#475569; margin:0; line-height:1.7;">
                        두 사람이 공동의 재정 목표를 세우거나 동업을 진행할 경우 한 사람의 직관적인 추진력과 다른 한 사람의 치밀한 자산 관리 능력이 결합됩니다. 
                        돈이 새어나가는 구멍을 철저히 막고 큰 자산을 모으는 강력한 재물 시너지를 발휘하게 됩니다.
                    </p>
                </div>

                <div style="background:#F8FAFC; border:1px solid #E2E8F0; padding:16px; border-radius:14px;">
                    <h5 style="font-size:14.5px; font-weight:800; color:#0F172A; margin-bottom:6px;">4. 장기적인 갈등 예방법 & 맞춤 개운 처세술</h5>
                    <p style="font-size:13px; color:#475569; margin:0; line-height:1.7;">
                        서로의 독립적인 시간과 취미 영역을 존중해 주는 것이 백년가약의 핵심 비결입니다. 의견 차이가 생겼을 때는 즉각적으로 반박하기보다 
                        반나절 정도 생각을 정리한 후 대화를 나누는 것이 화기애애한 관계를 평생 유지하는 최고의 개운법입니다.
                    </p>
                </div>
            </div>
        </div>
        """
    elif report_key == "daewoon":
        title = f"{user_name}님 자미두수 평생운세 & 10년 대운 심층 감명"
        content = f"""
        <div style="text-align:left; line-height:1.85; color:#1E293B;">
            <div style="background:#FFFBEB; border-left:4px solid #F59E0B; padding:16px; border-radius:14px; margin-bottom:16px;">
                <h4 style="font-size:16px; font-weight:800; color:#78350F; margin-bottom:6px;">👑 평생 본명궁(本命宮) 및 생애 총평</h4>
                <p style="font-size:13.5px; color:#92400E; margin:0; line-height:1.75;">
                    타고난 기개가 당당하고 스스로 일가를 이루는 자수성가형 귀격(貴格) 명식입니다. 
                    청년기의 치열한 담금질을 거쳐 40대 중반부터 60대까지 지속적인 번영과 성취를 이루는 '대기만성(大器晩成)'의 전형입니다.
                </p>
            </div>
            <div style="background:#F8FAFC; border:1px solid #E2E8F0; padding:14px 16px; border-radius:14px; margin-bottom:12px;">
                <h5 style="font-size:14px; font-weight:800; color:#0F172A; margin-bottom:4px;">📊 10년 대운(大運)의 황금기 분석</h5>
                <p style="font-size:13px; color:#475569; margin:0; line-height:1.7;">
                    현재 진입해 있는 대운은 사주의 용신(用神)과 희신이 힘을 얻는 구간으로, 자신의 사회적 역량을 인정받고 확고한 자산 기반을 확립하는 가장 중요한 인생 분기점입니다.
                </p>
            </div>
        </div>
        """
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
@app.post("/api/auth/kakao")
def auth_kakao(req: KakaoAuthRequest):
    user_id = f"user_{req.kakao_id}"
    
    if user_id in users_db:
        u = users_db[user_id]
        saju_res = get_saju_pillars_and_analysis(
            u["name"], u["gender"], u["birth_year"], u["birth_month"], u["birth_day"],
            u["calendar_type"], u["sijin_index"]
        )
        return {
            "status": "existing_user",
            "user_id": user_id,
            "coin_balance": u["coin"],
            "unlocked_reports": reports_db.get(user_id, []),
            "wardrobe_items": wardrobe_db.get(user_id, []),
            "saju_analysis": saju_res
        }
    else:
        users_db[user_id] = {
            "user_id": user_id,
            "kakao_id": req.kakao_id,
            "name": req.name if req.name != "달하 회원" else "",
            "gender": req.gender or "male",
            "birth_year": 1978,
            "birth_month": 8,
            "birth_day": 13,
            "calendar_type": "solar",
            "sijin_index": 5,
            "coin": 1000
        }
        reports_db[user_id] = []
        wardrobe_db[user_id] = []

        return {
            "status": "new_user",
            "user_id": user_id,
            "coin_balance": 1000,
            "kakao_prefill": {
                "name": users_db[user_id]["name"],
                "gender": users_db[user_id]["gender"],
                "calendar_type": "solar",
                "birth_year": 1978,
                "birth_month": 8,
                "birth_day": 13,
                "sijin_index": 5
            }
        }

@app.post("/api/user/register-saju")
def register_saju(req: RegisterSajuRequest):
    if req.user_id not in users_db:
        users_db[req.user_id] = {"coin": 1000}

    users_db[req.user_id].update({
        "name": req.name,
        "gender": req.gender,
        "birth_year": req.birth_year,
        "birth_month": req.birth_month,
        "birth_day": req.birth_day,
        "calendar_type": req.calendar_type,
        "sijin_index": req.sijin_index
    })

    saju_res = get_saju_pillars_and_analysis(
        req.name, req.gender, req.birth_year, req.birth_month, req.birth_day,
        req.calendar_type, req.sijin_index
    )

    return {
        "status": "success",
        "coin_balance": users_db[req.user_id]["coin"],
        "saju_analysis": saju_res
    }

@app.post("/api/wardrobe/add")
def add_wardrobe(req: WardrobeItemRequest):
    if req.user_id not in wardrobe_db:
        wardrobe_db[req.user_id] = []
    
    new_item = {
        "id": int(datetime.datetime.now().timestamp() * 1000),
        "category": req.category,
        "nickname": req.nickname or f"{req.colors[0] if req.colors else ''} {req.category}",
        "colors": req.colors,
        "materials": req.materials
    }
    wardrobe_db[req.user_id].append(new_item)
    return {"status": "success", "wardrobe_items": wardrobe_db[req.user_id]}

@app.put("/api/wardrobe/edit/{item_id}")
def edit_wardrobe(item_id: int, req: WardrobeItemRequest):
    items = wardrobe_db.get(req.user_id, [])
    for item in items:
        if item["id"] == item_id:
            item["category"] = req.category
            item["nickname"] = req.nickname or f"{req.colors[0] if req.colors else ''} {req.category}"
            item["colors"] = req.colors
            item["materials"] = req.materials
            break
    return {"status": "success", "wardrobe_items": items}

@app.delete("/api/wardrobe/delete/{item_id}")
def delete_wardrobe(item_id: int, user_id: str):
    items = wardrobe_db.get(user_id, [])
    wardrobe_db[user_id] = [i for i in items if i["id"] != item_id]
    return {"status": "success", "wardrobe_items": wardrobe_db[user_id]}

@app.post("/api/reports/unlock")
def unlock_report(req: UnlockReportRequest):
    if req.user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = users_db[req.user_id]
    if user["coin"] < req.cost:
        raise HTTPException(status_code=400, detail="Insufficient coins")
    
    user["coin"] -= req.cost
    rep_data = generate_detailed_report(req.report_key, req.sub_option, req.partner_name, req.relation, user.get("name", "회원"))

    new_report = {
        "report_key": req.report_key,
        "report_title": rep_data["title"],
        "report_content": rep_data["content"],
        "created_at": datetime.date.today().strftime("%Y.%m.%d")
    }

    if req.user_id not in reports_db:
        reports_db[req.user_id] = []
    
    reports_db[req.user_id].append(new_report)

    return {
        "status": "success",
        "new_balance": user["coin"],
        "unlocked_reports": reports_db[req.user_id]
    }

# --- 띠별 & 별자리 12개 전체 풀버전 데이터 (주의·경계 가이드 포함) ---
ZODIAC_FULL_DATA = {
    "쥐": {
        "score": 92, "title": "작은 노력으로 큰 결실을 맺는 날",
        "overview": "직관력과 기지가 빛을 발하여 복잡한 문제가 순조롭게 해결됩니다. 새로운 아이디어를 적극 제시하세요.",
        "year_tips": [
            {"year_label": "1960년생 (경자)", "tip": "재물운이 상승하나 문서 검토는 꼼꼼히 하세요. ⚠️ 무리한 투자는 금물"},
            {"year_label": "1972년생 (임자)", "tip": "직장에서 능력을 인정받습니다. ⚠️ 동료와의 언행에 배려가 필요합니다."},
            {"year_label": "1984년생 (갑자)", "tip": "새로운 기회가 찾아오는 날입니다. ⚠️ 조급함을 버리고 차분히 진행하세요."},
            {"year_label": "1996년생 (병자)", "tip": "대인관계가 원만하고 인기가 상승합니다. ⚠️ 지출 관리에 신경 쓰세요."}
        ],
        "lucky_time": "오후 1시 ~ 3시", "lucky_match": "소띠·용띠와 최고의 조화"
    },
    "소": {
        "score": 89, "title": "우직한 성실함이 빛을 발하는 하루",
        "overview": "원칙을 지키며 묵묵히 나아갈 때 주변의 신뢰와 지원을 얻습니다. 기초를 튼튼히 다지세요.",
        "year_tips": [
            {"year_label": "1961년생 (신축)", "tip": "가정에 평안이 깃듭니다. ⚠️ 건강을 위해 무리한 야외활동은 자제하세요."},
            {"year_label": "1973년생 (계축)", "tip": "사업상 실마리가 풀립니다. ⚠️ 계약 체결 시 세부 조항을 재확인하세요."},
            {"year_label": "1985년생 (을축)", "tip": "노력에 대한 정당한 보상이 따릅니다. ⚠️ 고집을 조금 내려놓으세요."},
            {"year_label": "1997년생 (정축)", "tip": "학업 및 자격증 준비에 길합니다. ⚠️ 체력 관리에 신경 쓰세요."}
        ],
        "lucky_time": "오전 9시 ~ 11시", "lucky_match": "쥐띠·뱀띠와 찰떡궁합"
    },
    "호랑이": {
        "score": 95, "title": "용맹한 리더십으로 판을 주도하는 날",
        "overview": "자신감이 충만하고 추진력이 배가되는 시기입니다. 망설였던 일에 과감하게 도전하세요.",
        "year_tips": [
            {"year_label": "1962년생 (임인)", "tip": "명예운이 상승합니다. ⚠️ 감정적인 언행은 피하고 품위를 유지하세요."},
            {"year_label": "1974년생 (갑인)", "tip": "새로운 프로젝트를 맡게 됩니다. ⚠️ 독단적인 결정보다 팀워크를 챙기세요."},
            {"year_label": "1986년생 (병인)", "tip": "재물운과 승진운이 따릅니다. ⚠️ 경쟁자와의 불필요한 마찰은 피하세요."},
            {"year_label": "1998년생 (무인)", "tip": "활동 반경이 넓어집니다. ⚠️ 안전운전에 각별히 유의하세요."}
        ],
        "lucky_time": "오후 3시 ~ 5시", "lucky_match": "말띠·개띠와 환상의 파트너"
    },
    "토끼": {
        "score": 90, "title": "지혜와 예술적 감각이 돋보이는 하루",
        "overview": "섬세한 배려와 유연한 대처가 주변 사람들의 마음을 움직입니다. 협상과 미팅에 유리합니다.",
        "year_tips": [
            {"year_label": "1963년생 (계묘)", "tip": "마음의 여유를 가지세요. ⚠️ 남의 일에 지나치게 참견하지 않는 것이 상책입니다."},
            {"year_label": "1975년생 (을묘)", "tip": "재테크 정보가 들어옵니다. ⚠️ 검증되지 않은 소문은 경계하세요."},
            {"year_label": "1987년생 (정묘)", "tip": "아이디어가 인정받습니다. ⚠️ 마무리를 꼼꼼하게 매듭지으세요."},
            {"year_label": "1999년생 (기묘)", "tip": "연애운과 대인관계가 길합니다. ⚠️ 충동구매를 주의하세요."}
        ],
        "lucky_time": "오전 7시 ~ 9시", "lucky_match": "양띠·돼지띠와 대길"
    },
    "용": {
        "score": 94, "title": "큰 뜻을 펼치고 기운이 상승하는 날",
        "overview": "스케일이 큰 계획을 추진하기에 최적의 날입니다. 시야를 넓히고 미래를 준비하세요.",
        "year_tips": [
            {"year_label": "1964년생 (갑진)", "tip": "자손에게 경사가 있습니다. ⚠️ 건강 검진을 미루지 마세요."},
            {"year_label": "1976년생 (병진)", "tip": "사업 확장의 기회가 옵니다. ⚠️ 자금 유동성을 먼저 확보하세요."},
            {"year_label": "1988년생 (무진)", "tip": "주변의 신망을 얻습니다. ⚠️ 겸손한 태도를 잃지 마세요."},
            {"year_label": "2000년생 (경진)", "tip": "취업 및 시험운이 길합니다. ⚠️ 집중력을 유지하세요."}
        ],
        "lucky_time": "오후 5시 ~ 7시", "lucky_match": "쥐띠·원숭이띠와 최고의 합"
    },
    "뱀": {
        "score": 91, "title": "냉철한 통찰력으로 실속을 챙기는 하루",
        "overview": "상황을 예리하게 분석하여 최선의 결과를 도출합니다. 계약 및 협상에서 큰 이득을 봅니다.",
        "year_tips": [
            {"year_label": "1965년생 (을사)", "tip": "부동산 및 문서운이 좋습니다. ⚠️ 지인과의 금전거래는 피하세요."},
            {"year_label": "1977년생 (정사)", "tip": "전문성을 인정받습니다. ⚠️ 지나친 완벽주의는 스트레스를 부릅니다."},
            {"year_label": "1989년생 (기사)", "tip": "재물운이 상승곡선을 탑니다. ⚠️ 비밀 유지가 필요한 하루입니다."},
            {"year_label": "2001년생 (신사)", "tip": "새로운 분야를 배우기에 길합니다. ⚠️ 휴식을 잊지 마세요."}
        ],
        "lucky_time": "오전 11시 ~ 오후 1시", "lucky_match": "소띠·닭띠와 찰떡궁합"
    },
    "말": {
        "score": 93, "title": "역동적인 에너지로 목표를 향해 질주하는 날",
        "overview": "막힘없이 일이 풀리고 활력이 넘칩니다. 장거리 이동이나 출장에 좋은 소식이 있습니다.",
        "year_tips": [
            {"year_label": "1966년생 (병오)", "tip": "명예와 지위가 확고해집니다. ⚠️ 혈압 관리에 유의하세요."},
            {"year_label": "1978년생 (무오)", "tip": "성과가 배가되는 날입니다. ⚠️ 서두르지 말고 한 템포 쉬어가세요."},
            {"year_label": "1990년생 (경오)", "tip": "이직이나 독립운이 따릅니다. ⚠️ 주변 조언을 경청하세요."},
            {"year_label": "2002년생 (임오)", "tip": "친구들과의 화합이 좋습니다. ⚠️ 과음을 경계하세요."}
        ],
        "lucky_time": "오전 11시 ~ 오후 1시", "lucky_match": "호랑이띠·양띠와 찰떡"
    },
    "양": {
        "score": 88, "title": "온화한 배려로 평안을 이루는 하루",
        "overview": "주변과의 불화를 치유하고 평화로운 분위기를 조성합니다. 예술 및 힐링에 좋은 날입니다.",
        "year_tips": [
            {"year_label": "1967년생 (정미)", "tip": "가정의 평안이 최우선입니다. ⚠️ 근심을 내려놓고 편안히 쉬세요."},
            {"year_label": "1979년생 (기미)", "tip": "협력 관계가 탄탄해집니다. ⚠️ 공과 사를 명확히 구분하세요."},
            {"year_label": "1991년생 (신미)", "tip": "재능이 발휘되는 날입니다. ⚠️ 우유부단한 태도는 피하세요."},
            {"year_label": "2003년생 (계미)", "tip": "좋은 친구를 만납니다. ⚠️ 계획적인 소비를 하세요."}
        ],
        "lucky_time": "오후 1시 ~ 3시", "lucky_match": "토끼띠·돼지띠와 대길"
    },
    "원숭이": {
        "score": 94, "title": "다재다능한 재치로 위기를 기회로 바꾸는 날",
        "overview": "순발력과 문제 해결력이 최고조에 달합니다. 난관에 부딪힌 일을 깔끔하게 해결합니다.",
        "year_tips": [
            {"year_label": "1968년생 (무신)", "tip": "투자 이익이 발생합니다. ⚠️ 자만하지 말고 내실을 다지세요."},
            {"year_label": "1980년생 (경신)", "tip": "승진 및 영전운이 따릅니다. ⚠️ 지나친 경쟁심은 경계하세요."},
            {"year_label": "1992년생 (임신)", "tip": "새로운 인연이 찾아옵니다. ⚠️ 언행을 신중히 하세요."},
            {"year_label": "2004년생 (갑신)", "tip": "도전하는 일마다 성과가 있습니다. ⚠️ 체력을 비축하세요."}
        ],
        "lucky_time": "오후 3시 ~ 5시", "lucky_match": "용띠·쥐띠와 최상의 궁합"
    },
    "닭": {
        "score": 90, "title": "정확한 판단력으로 결실을 맺는 하루",
        "overview": "정리정돈과 회계, 계약 검토에 최적의 날입니다. 사소한 틈새를 보완하여 완벽을 기하세요.",
        "year_tips": [
            {"year_label": "1969년생 (기유)", "tip": "문서운이 길합니다. ⚠️ 건강을 위해 가벼운 스트레칭을 하세요."},
            {"year_label": "1981년생 (신유)", "tip": "실력을 인정받습니다. ⚠️ 비판적인 말투는 부드럽게 바꾸세요."},
            {"year_label": "1993년생 (계유)", "tip": "재물 흐름이 순조롭습니다. ⚠️ 유행에 휩쓸리지 마세요."},
            {"year_label": "2005년생 (을유)", "tip": "학업 성취도가 높습니다. ⚠️ 주변과의 조화를 신경 쓰세요."}
        ],
        "lucky_time": "오후 5시 ~ 7시", "lucky_match": "소띠·뱀띠와 최고의 합"
    },
    "개": {
        "score": 92, "title": "변함없는 신의로 인정과 존경을 받는 날",
        "overview": "신뢰를 바탕으로 한 대인관계에서 큰 행운이 따릅니다. 오랜 친구나 은인과의 만남이 길합니다.",
        "year_tips": [
            {"year_label": "1970년생 (경술)", "tip": "명예가 드높아집니다. ⚠️ 건강 검진을 체크하세요."},
            {"year_label": "1982년생 (임술)", "tip": "믿을 수 있는 동반자를 얻습니다. ⚠️ 과욕은 금물입니다."},
            {"year_label": "1994년생 (갑술)", "tip": "직장에서 능력을 발휘합니다. ⚠️ 고집을 조금 꺾으세요."},
            {"year_label": "2006년생 (병술)", "tip": "새로운 시작에 길합니다. ⚠️ 긍정적인 마음을 가지세요."}
        ],
        "lucky_time": "저녁 7시 ~ 9시", "lucky_match": "호랑이띠·말띠와 대길"
    },
    "돼지": {
        "score": 93, "title": "넉넉한 복록과 행운이 가득한 하루",
        "overview": "재물운과 식복(食福)이 풍성하며 즐거운 소식이 들려옵니다. 여유를 가지고 하루를 즐기세요.",
        "year_tips": [
            {"year_label": "1971년생 (신해)", "tip": "재물이 모여듭니다. ⚠️ 과식과 과음은 피하세요."},
            {"year_label": "1983년생 (계해)", "tip": "사업상 번창이 따릅니다. ⚠️ 주변 사람들에게 베풀면 복이 됩니다."},
            {"year_label": "1995년생 (을해)", "tip": "애정운이 매우 길합니다. ⚠️ 중요한 결정을 내리기에 좋습니다."},
            {"year_label": "2007년생 (정해)", "tip": "학업운이 상승합니다. ⚠️ 기초를 탄탄히 하세요."}
        ],
        "lucky_time": "밤 9시 ~ 11시", "lucky_match": "토끼띠·양띠와 찰떡궁합"
    }
}

STAR_FULL_DATA = {
    "양자리": {"elem": "불 (Fire)", "planet": "화성 (Mars)", "score": 93, "title": "타오르는 열정으로 새로운 문을 여는 날", "overview": "추진력과 개척 정신이 최고조에 달합니다. 망설이지 말고 행동에 옮기세요.", "focus": "오늘 시작하는 프로젝트가 향후 1년간의 성장 발판이 됩니다. ⚠️ 주의: 성급한 판단보다 팩트를 재확인하세요.", "color": "루비 레드", "time": "오전 9시 ~ 11시"},
    "황소자리": {"elem": "흙 (Earth)", "planet": "금성 (Venus)", "score": 90, "title": "안정적인 기반 위에 실속을 쌓는 하루", "overview": "꾸준함과 끈기가 결실을 맺습니다. 금융 자산 관리 및 계약에 길합니다.", "focus": "장기적인 안목으로 자산을 배분하세요. ⚠️ 주의: 고집을 내려놓고 유연하게 수용하세요.", "color": "에메랄드 그린", "time": "오후 1시 ~ 3시"},
    "쌍둥이자리": {"elem": "공기 (Air)", "planet": "수성 (Mercury)", "score": 94, "title": "재치 있는 화술과 정보력이 빛나는 날", "overview": "새로운 소식과 유용한 정보를 선점합니다. 커뮤니케이션과 미팅에 최적입니다.", "focus": "사람들과의 교류 속에서 귀인을 만나게 됩니다. ⚠️ 주의: 뜬소문에 현혹되지 마세요.", "color": "브라이트 옐로우", "time": "오전 10시 ~ 12시"},
    "게자리": {"elem": "물 (Water)", "planet": "달 (Moon)", "score": 89, "title": "따뜻한 공감으로 사람들의 마음을 얻는 날", "overview": "가정과 가까운 이들과의 화합이 두터워집니다. 내면의 힐링에 집중하세요.", "focus": "주변에 온기를 나누어주면 더 큰 복으로 돌아옵니다. ⚠️ 주의: 감정 기복을 잘 다스리세요.", "color": "실버 화이트", "time": "저녁 6시 ~ 8시"},
    "사자자리": {"elem": "불 (Fire)", "planet": "태양 (Sun)", "score": 96, "title": "눈부신 카리스마로 무대의 주인공이 되는 하루", "overview": "자신의 재능과 리더십이 만천하에 드러납니다. 주도권을 쥐고 이끄세요.", "focus": "당당한 태도가 성공을 부릅니다. ⚠️ 주의: 오만함을 경계하고 파트너를 칭찬해 주세요.", "color": "임페리얼 골드", "time": "오후 2시 ~ 4시"},
    "처녀자리": {"elem": "흙 (Earth)", "planet": "수성 (Mercury)", "score": 91, "title": "정교한 분석과 완벽한 정리의 날", "overview": "복잡하게 얽힌 문제의 해답을 명쾌하게 찾아냅니다. 디테일의 승리입니다.", "focus": "작은 오점을 수정할 때 완벽한 결실이 맺어집니다. ⚠️ 주의: 지나친 비판은 삼가세요.", "color": "네이비 블루", "time": "오전 8시 ~ 10시"},
    "천칭자리": {"elem": "공기 (Air)", "planet": "금성 (Venus)", "score": 92, "title": "균형과 조화로 평화로운 결실을 맺는 날", "overview": "갈등을 중재하고 최선의 합의를 이끌어냅니다. 미적 감각이 돋보입니다.", "focus": "합리적인 선택이 이득을 가져옵니다. ⚠️ 주의: 결정을 너무 오래 미루지 마세요.", "color": "파스텔 핑크", "time": "오후 4시 ~ 6시"},
    "전갈자리": {"elem": "물 (Water)", "planet": "명왕성 (Pluto)", "score": 95, "title": "예리한 통찰력과 강력한 집중력의 하루", "overview": "사물의 본질을 꿰뚫어 보며 핵심을 장악합니다. 비밀 프로젝트에 길합니다.", "focus": "끝까지 밀어붙이는 집념이 기적을 만듭니다. ⚠️ 주의: 집착을 버리고 한 걸음 물러서세요.", "color": "딥 버건디", "time": "밤 8시 ~ 10시"},
    "사수자리": {"elem": "불 (Fire)", "planet": "목성 (Jupiter)", "score": 93, "title": "자유로운 탐험과 원대한 꿈을 펼치는 날", "overview": "활동 영역이 넓어지고 해외 및 장거리 이동에 길한 소식이 들려옵니다.", "focus": "넓은 시야로 미래를 기획하세요. ⚠️ 주의: 사소한 디테일을 놓치지 않도록 점검하세요.", "color": "로열 퍼플", "time": "오전 11시 ~ 오후 1시"},
    "염소자리": {"elem": "흙 (Earth)", "planet": "토성 (Saturn)", "score": 90, "title": "인내와 노력이 결실을 맺는 견고한 하루", "overview": "차근차근 쌓아온 신뢰가 명예와 보상으로 돌아옵니다. 책임감이 빛납니다.", "focus": "원칙을 고수할 때 흔들리지 않는 승리를 거둡니다. ⚠️ 주의: 스스로에게 너무 엄격하지 마세요.", "color": "차콜 그레이", "time": "오후 1시 ~ 3시"},
    "물병자리": {"elem": "공기 (Air)", "planet": "천왕성 (Uranus)", "score": 94, "title": "독창적인 영감과 혁신이 돋보이는 날", "overview": "남들이 생각지 못한 번뜩이는 아이디어로 판을 바꿉니다. 개성을 드러내세요.", "focus": "새로운 기술이나 지식을 적극 수용하세요. ⚠️ 주의: 현실적인 실현 가능성을 함께 고려하세요.", "color": "스카이 블루", "time": "오후 3시 ~ 5시"},
    "물고기자리": {"elem": "물 (Water)", "planet": "해왕성 (Neptune)", "score": 91, "title": "풍부한 감수성과 예술적 영감이 넘치는 하루", "overview": "마음이 편안해지고 직관이 적중합니다. 마음의 소리에 귀 기울이세요.", "focus": "영적인 안정과 예술적 활동에 대길합니다. ⚠️ 주의: 현실을 도피하지 말고 당당히 마주하세요.", "color": "아쿠아 마린", "time": "저녁 7시 ~ 9시"}
}

@app.get("/api/zodiac-fortune")
def get_zodiac_fortune(type: str, key: str):
    if type == "star":
        st = STAR_FULL_DATA.get(key, STAR_FULL_DATA["사자자리"])
        return {
            "name": key,
            "score": st["score"],
            "title": st["title"],
            "overview": st["overview"],
            "star_element": st["elem"],
            "star_planet": st["planet"],
            "focus_content": st["focus"],
            "lucky_color": st["color"],
            "lucky_time": st["time"]
        }
    else:
        zd = ZODIAC_FULL_DATA.get(key, ZODIAC_FULL_DATA["호랑이"])
        return {
            "name": f"{key}띠",
            "score": zd["score"],
            "title": zd["title"],
            "overview": zd["overview"],
            "year_tips": zd["year_tips"],
            "lucky_time": zd["lucky_time"],
            "lucky_match": zd["lucky_match"]
        }

TAROT_DECK = [
    {"name": "0. THE FOOL (바보)", "keyword": "새로운 시작 · 무한한 잠재력", "symbolism": "순수한 열정과 모험심", "reading_male": "새로운 프로젝트를 과감하게 시작하기에 최적입니다.", "reading_female": "마음이 이끄는 대로 새로운 도전을 시작해 보세요.", "action_guide": "과거의 걱정을 내려놓고 첫 발을 내딛으세요."},
    {"name": "I. THE MAGICIAN (마법사)", "keyword": "창조적 재능 · 탁월한 실행력", "symbolism": "모든 도구를 갖춘 완벽한 준비", "reading_male": "자신감을 가지고 주도권을 행사할 때 결과가 따릅니다.", "reading_female": "당신의 다재다능한 매력과 역량이 빛을 발합니다.", "action_guide": "준비된 실력을 주저 없이 세상에 드러내세요."}
]

@app.get("/api/daily-tarot")
def get_daily_tarot(slot: int, user_id: Optional[str] = None, is_paid: Optional[bool] = False):
    if is_paid and user_id:
        if user_id in users_db and users_db[user_id]["coin"] >= 10:
            users_db[user_id]["coin"] -= 10
        else:
            raise HTTPException(status_code=400, detail="Insufficient coins")
    
    card = random.choice(TAROT_DECK)
    return card

@app.post("/api/user/charge-coin")
def charge_coin(req: ChargeCoinRequest):
    if req.user_id not in users_db:
        users_db[req.user_id] = {"coin": 0}
    users_db[req.user_id]["coin"] += req.amount
    return {"status": "success", "new_balance": users_db[req.user_id]["coin"]}

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
        "input": {
            "year": y,
            "month": m,
            "day": d,
            "cal_type": cal_type,
            "gender": gender
        },
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
