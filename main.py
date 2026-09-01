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

# --- Saju Calculation Engine ---
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
    # 정통 명식 산출 기본 템플릿
    cg_y = CHEONGAN[(y - 4) % 10]
    jj_y = JIJI[(y - 4) % 12]
    cg_m = CHEONGAN[(y * 2 + m) % 10]
    jj_m = JIJI[(m + 1) % 12]
    cg_d = CHEONGAN[(y * 5 + d) % 10]
    jj_d = JIJI[(d + 3) % 12]

    if sijin >= 0:
        cg_h = CHEONGAN[(sijin * 2) % 10]
        jj_h = JIJI[sijin % 12]
    else:
        cg_h, jj_h = "무", "진"

    # 가중치 기반 오행 분포 (월지 35% 가중치)
    elements_weight = {"wood": 15, "fire": 25, "earth": 45, "metal": 0, "water": 15}
    if cg_d in ["경", "신"] or jj_d in ["신", "유"]:
        elements_weight["metal"] = 20
        elements_weight["earth"] = 25

    current_age = datetime.date.today().year - y + 1

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
            "title": "도약과 실속의 기운이 깃든 날",
            "score": 88,
            "mode_badge": "운세 88점 · 길운(吉運)",
            "badge_style": "background:#FEF3C7; color:#78350F; border:1px solid #FDE68A;",
            "advice": f"지혜롭게 내실을 다질 때입니다. 사주의 화(火) 기운과 토(土) 기운이 조화를 이루어, 오늘 내리는 결정이 향후 큰 결실로 이어집니다.",
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
        # 신규 사용자 기본 틀 생성
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

# --- Wardrobe API ---
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

# --- 2026 신년운세 & 궁합 심층 리포트 생성기 ---
def generate_detailed_report(report_key: str, sub_option: str, partner_name: str, relation: str, user_name: str) -> Dict[str, str]:
    if report_key == "sinnian":
        title = f"2026 丙午년 {user_name}님 정밀 신년운세 & 토정비결"
        content = f"""
        <div style="text-align:left; line-height:1.8; color:#1E293B;">
            <div style="background:#ECFDF5; border-left:4px solid #10B981; padding:14px; border-radius:12px; margin-bottom:16px;">
                <h4 style="font-size:16px; font-weight:800; color:#065F46; margin-bottom:4px;">📜 2026년 丙午(병오)년 총운 (總論)</h4>
                <p style="font-size:13.5px; color:#047857; margin:0;">붉은 말의 해를 맞아 강렬한 양기(陽氣)가 사주의 잠재력을 자극합니다. 정체되었던 흐름이 풀리고 상반기보다 하반기로 갈수록 성과가 배가되는 비도진천(飛渡震天)의 형국입니다.</p>
            </div>

            <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:16px;">
                <div style="background:#F8FAFC; border:1px solid #E2E8F0; padding:12px; border-radius:12px;">
                    <span style="font-weight:800; color:#D97706; font-size:13px;">💰 2026 재물운</span>
                    <p style="font-size:12.5px; color:#475569; margin-top:4px;">문서운과 투자운이 길하여 부동산이나 중장기 자산 증식에 유리합니다. 무리한 단기 투기만 경계하면 큰 곳간을 채웁니다.</p>
                </div>
                <div style="background:#F8FAFC; border:1px solid #E2E8F0; padding:12px; border-radius:12px;">
                    <span style="font-weight:800; color:#2563EB; font-size:13px;">🏢 2026 직장·사업운</span>
                    <p style="font-size:12.5px; color:#475569; margin-top:4px;">조직 내에서 주도권을 잡거나 사업의 외연을 확장할 기회가 찾아옵니다. 5월과 10월에 귀인의 조력이 따릅니다.</p>
                </div>
                <div style="background:#F8FAFC; border:1px solid #E2E8F0; padding:12px; border-radius:12px;">
                    <span style="font-weight:800; color:#DC2626; font-size:13px;">🌿 2026 가정·건강운</span>
                    <p style="font-size:12.5px; color:#475569; margin-top:4px;">화기가 강해지는 여름철 심혈관계와 수면 패턴 관리가 필요합니다. 규칙적인 유산소 운동이 운을 틔웁니다.</p>
                </div>
                <div style="background:#F8FAFC; border:1px solid #E2E8F0; padding:12px; border-radius:12px;">
                    <span style="font-weight:800; color:#9333EA; font-size:13px;">💖 2026 이성·대인관계</span>
                    <p style="font-size:12.5px; color:#475569; margin-top:4px;">주변에 신뢰할 수 있는 파트너가 모여듭니다. 감정적인 언행을 줄이고 명확한 소통을 유지할 때 인덕이 극대화됩니다.</p>
                </div>
            </div>

            <h4 style="font-size:15px; font-weight:800; color:#0F172A; margin:16px 0 10px; border-bottom:1.5px solid #E2E8F0; padding-bottom:6px;">📅 2026년 1월 ~ 12월 월별 상세 토정비결</h4>
            <div style="display:flex; flex-direction:column; gap:8px; font-size:13px;">
                <div style="background:#F8FAFC; padding:10px 12px; border-radius:10px; border-left:3px solid #2D6A4F;"><strong>1월:</strong> 새로운 계획의 기틀을 닦는 달. 조급함을 버리고 기초를 견고히 다지세요.</div>
                <div style="background:#F8FAFC; padding:10px 12px; border-radius:10px; border-left:3px solid #2D6A4F;"><strong>2월:</strong> 대인관계에서 좋은 소식이 들려오며 정체되었던 일이 서서히 움직입니다.</div>
                <div style="background:#F8FAFC; padding:10px 12px; border-radius:10px; border-left:3px solid #2D6A4F;"><strong>3월:</strong> 문서 계약이나 중요한 결정에서 유리한 위치를 점하게 되는 길월입니다.</div>
                <div style="background:#F8FAFC; padding:10px 12px; border-radius:10px; border-left:3px solid #2D6A4F;"><strong>4월:</strong> 지출 관리가 필요한 시기입니다. 불필요한 충동구매나 투자를 삼가세요.</div>
                <div style="background:#F8FAFC; padding:10px 12px; border-radius:10px; border-left:3px solid #2D6A4F;"><strong>5월:</strong> 귀인의 도움이 따르며 직장이나 사업에서 괄목할 성과가 나타납니다.</div>
                <div style="background:#F8FAFC; padding:10px 12px; border-radius:10px; border-left:3px solid #2D6A4F;"><strong>6월:</strong> 건강 관리에 유의하세요. 충분한 휴식과 수분 섭취가 개운의 열쇠입니다.</div>
                <div style="background:#F8FAFC; padding:10px 12px; border-radius:10px; border-left:3px solid #2D6A4F;"><strong>7월:</strong> 재물운이 안정세를 찾으며 노력에 대한 정당한 보상이 주어집니다.</div>
                <div style="background:#F8FAFC; padding:10px 12px; border-radius:10px; border-left:3px solid #2D6A4F;"><strong>8월:</strong> 주변의 경쟁이나 구설을 지혜롭게 넘겨야 합니다. 원칙을 고수하세요.</div>
                <div style="background:#F8FAFC; padding:10px 12px; border-radius:10px; border-left:3px solid #2D6A4F;"><strong>9월:</strong> 가을의 결실이 맺히기 시작합니다. 그동안의 노력이 인정받는 달입니다.</div>
                <div style="background:#F8FAFC; padding:10px 12px; border-radius:10px; border-left:3px solid #2D6A4F;"><strong>10월:</strong> 뜻밖의 횡재수나 새로운 제안이 들어올 수 있으니 적극 검토하세요.</div>
                <div style="background:#F8FAFC; padding:10px 12px; border-radius:10px; border-left:3px solid #2D6A4F;"><strong>11월:</strong> 한 해를 정리하며 내실을 다질 때입니다. 인간관계를 돈독히 하세요.</div>
                <div style="background:#F8FAFC; padding:10px 12px; border-radius:10px; border-left:3px solid #2D6A4F;"><strong>12월:</strong> 안정과 번영 속에 한 해를 마무리하며 다음 해의 대운을 준비합니다.</div>
            </div>
        </div>
        """
    elif report_key == "gunghap":
        title = f"{user_name}님 & {partner_name}님 정통 사주 궁합 감명서"
        content = f"""
        <div style="text-align:left; line-height:1.8; color:#1E293B;">
            <div style="background:#FFF1F2; border-left:4px solid #E11D48; padding:14px; border-radius:12px; margin-bottom:16px;">
                <h4 style="font-size:16px; font-weight:800; color:#9F1239; margin-bottom:4px;">💞 인연 총평 ({relation})</h4>
                <p style="font-size:13.5px; color:#BE123C; margin:0;">서로의 부족한 기운을 상호 보완해 주는 '수화기제(水火旣濟)'의 길한 배합입니다. 서로의 가치관을 존중할 때 시너지가 200% 발휘됩니다.</p>
            </div>

            <div style="display:flex; flex-direction:column; gap:12px;">
                <div style="background:#F8FAFC; border:1px solid #E2E8F0; padding:14px; border-radius:14px;">
                    <h5 style="font-size:14px; font-weight:800; color:#0F172A; margin-bottom:6px;">1. 겉궁합 (성격 및 기질의 조화)</h5>
                    <p style="font-size:13px; color:#475569; margin:0;">{user_name}님의 차분하고 논리적인 리더십과 {partner_name}님의 포용력 있는 감성이 만나 편안한 안정감을 형성합니다. 일상적인 대화에서 공감대를 쉽게 형성합니다.</p>
                </div>

                <div style="background:#F8FAFC; border:1px solid #E2E8F0; padding:14px; border-radius:14px;">
                    <h5 style="font-size:14px; font-weight:800; color:#0F172A; margin-bottom:6px;">2. 속궁합 (오행 상생 밸런스 & 무의식적 끌림)</h5>
                    <p style="font-size:13px; color:#475569; margin:0;">사주 명식의 일간과 지지가 합(合)을 이루어 갈등이 발생하더라도 회복 탄력성이 뛰어납니다. 내면의 깊은 교감이 오래 지속되는 인연입니다.</p>
                </div>

                <div style="background:#F8FAFC; border:1px solid #E2E8F0; padding:14px; border-radius:14px;">
                    <h5 style="font-size:14px; font-weight:800; color:#0F172A; margin-bottom:6px;">3. 재물 및 협력 시너지</h5>
                    <p style="font-size:13px; color:#475569; margin:0;">함께 공동의 목표를 설정하거나 자산을 운용할 때 한 사람의 직관과 다른 사람의 치밀한 분석력이 결합되어 손실을 막고 자산을 불리는 형국입니다.</p>
                </div>

                <div style="background:#F8FAFC; border:1px solid #E2E8F0; padding:14px; border-radius:14px;">
                    <h5 style="font-size:14px; font-weight:800; color:#0F172A; margin-bottom:6px;">4. 갈등 예방 처세술 & 개운 가이드</h5>
                    <p style="font-size:13px; color:#475569; margin:0;">서로의 개인적인 영역과 취미를 존중해 주는 것이 핵심입니다. 의견 차이가 생길 때는 즉각적인 반박보다 반나절의 생각할 시간을 가지는 것이 대길합니다.</p>
                </div>
            </div>
        </div>
        """
    elif report_key == "daewoon":
        title = f"{user_name}님 자미두수 평생운세 & 10년 대운 심층 감명"
        content = f"""
        <div style="text-align:left; line-height:1.8; color:#1E293B;">
            <div style="background:#FFFBEB; border-left:4px solid #F59E0B; padding:14px; border-radius:12px; margin-bottom:14px;">
                <h4 style="font-size:15px; font-weight:800; color:#78350F; margin-bottom:4px;">👑 평생 본명궁 & 대운 분석</h4>
                <p style="font-size:13px; color:#92400E; margin:0;">생애 전반에 걸쳐 자수성가형 성공 기운이 뚜렷하며, 40대 중후반부터 60대까지 지속적인 번영의 황금기를 맞이합니다.</p>
            </div>
            <p style="font-size:13px; color:#475569;">관록궁과 재백궁의 길성이 회조하여 중년 이후 자산과 명예가 동반 상승하는 귀한 명식입니다.</p>
        </div>
        """
    else:
        title = f"{user_name}님 {sub_option} 맞춤 심층 감명서"
        content = f"""
        <div style="text-align:left; line-height:1.8; color:#1E293B;">
            <div style="background:#F8FAFC; border-left:4px solid #2D6A4F; padding:14px; border-radius:12px; margin-bottom:12px;">
                <h4 style="font-size:15px; font-weight:800; color:#065F46; margin-bottom:4px;">🎯 핵심 솔루션 ({sub_option})</h4>
                <p style="font-size:13px; color:#047857; margin:0;">현재 사주 대운의 흐름상 선택과 집중이 필요한 타이밍입니다. 흔들리지 않는 중심을 잡을 때 성공 확률이 극대화됩니다.</p>
            </div>
        </div>
        """
    return {"title": title, "content": content}

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

# --- 띠별 & 별자리 운세 API (주의·경계 팁 추가) ---
@app.get("/api/zodiac-fortune")
def get_zodiac_fortune(type: str, key: str):
    if type == "star":
        star_elements = {
            "양자리": "불 (Fire)", "사자자리": "불 (Fire)", "사수자리": "불 (Fire)",
            "황소자리": "흙 (Earth)", "처녀자리": "흙 (Earth)", "염소자리": "흙 (Earth)",
            "쌍둥이자리": "공기 (Air)", "천칭자리": "공기 (Air)", "물병자리": "공기 (Air)",
            "게자리": "물 (Water)", "전갈자리": "물 (Water)", "물고기자리": "물 (Water)"
        }
        return {
            "name": key,
            "score": 91,
            "title": "내면의 열정이 구체적인 성과로 연결되는 날",
            "overview": "행성의 순행 배치로 인해 창의력과 직관이 고조됩니다. 다만 의욕이 앞서 성급한 결정을 내릴 수 있으니 한 템포 쉬어가는 여유가 필요합니다.",
            "star_element": star_elements.get(key, "불 (Fire)"),
            "star_planet": "태양 & 목성",
            "focus_content": "오늘 집중하는 일이 향후 1달간의 성패를 가릅니다. ⚠️ 주의: 타인의 말에 쉽게 휩쓸리지 말고 본인의 직관을 믿으세요.",
            "lucky_color": "골드 / 오렌지",
            "lucky_time": "오전 11시 ~ 오후 1시"
        }
    else:
        return {
            "name": f"{key}띠",
            "score": 93,
            "title": "신뢰를 바탕으로 실속을 챙기는 하루",
            "overview": "노력에 대한 정당한 대가가 따르는 길한 날입니다. 주변과의 협업이 순조롭게 진행됩니다.",
            "year_tips": [
                {"year_label": "1960/1972년생", "tip": "재물운이 상승하나 무리한 지출을 삼가세요. ⚠️ 문서 확인 필수"},
                {"year_label": "1984/1996년생", "tip": "직장에서 능력을 인정받습니다. ⚠️ 동료와의 언행에 유의하세요."}
            ],
            "lucky_time": "오후 2시 ~ 4시",
            "lucky_match": "소띠·용띠와 최상의 궁합"
        }

# --- 타로 카드 API (2회차 10 복채 유료 차감 연동) ---
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

# Static Web Hosting (Render / GitHub Pages 호환)
if os.path.exists("index.html"):
    @app.get("/")
    def serve_index():
        return FileResponse("index.html")
