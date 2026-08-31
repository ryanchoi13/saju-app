import os
import random
from typing import Optional, List
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from pydantic import BaseModel
import sqlite3

app = FastAPI()

DATABASE_URL = os.environ.get("DATABASE_URL")
USE_POSTGRES = bool(DATABASE_URL)

def get_db():
    if USE_POSTGRES:
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
        return conn
    else:
        conn = sqlite3.connect("dalha_local.db")
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    db = get_db()
    cursor = db.cursor()
    
    if USE_POSTGRES:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            kakao_id VARCHAR(100) UNIQUE,
            name VARCHAR(100),
            gender VARCHAR(20),
            birth_year INT,
            birth_month INT,
            birth_day INT,
            calendar_type VARCHAR(20),
            sijin_index INT,
            coin_balance INT DEFAULT 1000,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS unlocked_reports (
            id SERIAL PRIMARY KEY,
            user_id INT,
            report_key VARCHAR(50),
            report_title VARCHAR(150),
            report_content TEXT,
            created_at VARCHAR(50)
        );
        CREATE TABLE IF NOT EXISTS wardrobe_items (
            id SERIAL PRIMARY KEY,
            user_id INT,
            category VARCHAR(50),
            nickname VARCHAR(100),
            colors TEXT,
            materials TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
    else:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kakao_id TEXT UNIQUE,
            name TEXT,
            gender TEXT,
            birth_year INTEGER,
            birth_month INTEGER,
            birth_day INTEGER,
            calendar_type TEXT,
            sijin_index INTEGER,
            coin_balance INTEGER DEFAULT 1000,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS unlocked_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            report_key TEXT,
            report_title TEXT,
            report_content TEXT,
            created_at TEXT
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS wardrobe_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category TEXT,
            nickname TEXT,
            colors TEXT,
            materials TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)
    db.commit()
    db.close()

try:
    init_db()
except Exception as e:
    print(f"DB Init Error: {e}")

# 와다 산조 배색사전 기반 오행 연동 팔레트 DB
WADA_SANZO_PALETTES = {
    "wood": [
        {
            "palette_no": 48,
            "theme": "청록의 상생과 지혜",
            "mood_desc": "차분한 세이지 그린과 포그 블루가 만나 사주의 기운을 유연하고 맑게 정돈합니다.",
            "mode": "harmony",
            "style_mood": "casual",
            "mood_tag": "🏃 캐주얼 & 액티브",
            "top": {"name": "세이지 포레스트", "hex": "#4A6B5B", "standard_color": "그린"},
            "bottom": {"name": "포그 블루", "hex": "#8CA6B5", "standard_color": "스카이블루"},
            "point": None
        },
        {
            "palette_no": 114,
            "theme": "통관용신 · 벽갑인정(쪼개어 불을 켜다)",
            "mood_desc": "풍성한 목(木) 기운을 앤틱 버건디 소품으로 부드럽게 통관하여 묶여있던 추진력을 폭발시킵니다.",
            "mode": "reverse",
            "style_mood": "casual",
            "mood_tag": "✦ 시크릿 반전 데이",
            "top": {"name": "딥 틸 그린", "hex": "#2B4C47", "standard_color": "그린"},
            "bottom": {"name": "페일 에크루", "hex": "#E3DAC9", "standard_color": "베이지"},
            "point": {"name": "앤틱 보르도", "hex": "#7A2E3D", "standard_color": "와인/버건디"}
        }
    ],
    "fire": [
        {
            "palette_no": 72,
            "theme": "따스한 온기와 활력",
            "mood_desc": "은은한 코랄 브릭과 소프트 크림이 조화를 이루어 주변 사람을 끌어당기는 따뜻한 카리스마를 만듭니다.",
            "mode": "harmony",
            "style_mood": "smart_casual",
            "mood_tag": "✨ 스마트 캐주얼",
            "top": {"name": "테라코타 앰버", "hex": "#C26D53", "standard_color": "코랄/오렌지"},
            "bottom": {"name": "오이스터 화이트", "hex": "#F4F1EA", "standard_color": "화이트"},
            "point": None
        },
        {
            "palette_no": 128,
            "theme": "수화기제(水火旣濟) · 조후의 완성",
            "mood_desc": "치솟는 화기를 차분한 미드나잇 인디고 소품으로 잡아주어 냉철한 판단력과 금전운을 회복합니다.",
            "mode": "reverse",
            "style_mood": "formal",
            "mood_tag": "👔 클래식 & 포멀",
            "top": {"name": "소프트 웜 베이지", "hex": "#D8C7B5", "standard_color": "베이지"},
            "bottom": {"name": "차콜 슬레이트", "hex": "#3A3D40", "standard_color": "차콜"},
            "point": {"name": "미드나잇 네이비", "hex": "#1B2A47", "standard_color": "네이비"}
        }
    ],
    "earth": [
        {
            "palette_no": 91,
            "theme": "대지의 신뢰와 품격",
            "mood_desc": "묵직한 카멜 브라운과 오트밀 베이지가 만나 흔들리지 않는 신뢰와 포용력을 드러냅니다.",
            "mode": "harmony",
            "style_mood": "formal",
            "mood_tag": "👔 클래식 & 포멀",
            "top": {"name": "로즈우드 카멜", "hex": "#9E6B55", "standard_color": "카멜/브라운"},
            "bottom": {"name": "오트밀 크림", "hex": "#EAE4D9", "standard_color": "아이보리/크림"},
            "point": None
        }
    ],
    "metal": [
        {
            "palette_no": 84,
            "theme": "명경지수(明鏡止水) · 지적인 냉철함",
            "mood_desc": "깊은 미드나잇 인디고와 안개빛 스카이블루가 만나 사주의 금전운과 전문성을 견고히 세웁니다.",
            "mode": "harmony",
            "style_mood": "casual",
            "mood_tag": "🏃 캐주얼 & 액티브",
            "top": {"name": "미드나잇 인디고", "hex": "#1F3044", "standard_color": "네이비"},
            "bottom": {"name": "포그 스카이", "hex": "#8CA6B5", "standard_color": "스카이블루"},
            "point": None
        },
        {
            "palette_no": 105,
            "theme": "통관용신(通關用神) · 조후 개운",
            "mood_desc": "사주 원국의 한기를 녹여내기 위해, 기본 의류 위에 앤틱 와인/골드 소품을 얹어 재물의 숨통을 틔웁니다.",
            "mode": "reverse",
            "style_mood": "casual",
            "mood_tag": "✦ 시크릿 반전 데이",
            "top": {"name": "딥 프러시안", "hex": "#1A2A3A", "standard_color": "네이비"},
            "bottom": {"name": "더스티 스카이", "hex": "#9CB2C0", "standard_color": "스카이블루"},
            "point": {"name": "앤틱 보르도", "hex": "#7A2E3D", "standard_color": "와인/버건디"}
        }
    ],
    "water": [
        {
            "palette_no": 62,
            "theme": "깊은 통찰과 유연한 교섭",
            "mood_desc": "머스터드 옐로우와 차분한 베이지가 결합하여 차가운 기운을 녹이고 유연한 소통을 이끕니다.",
            "mode": "harmony",
            "style_mood": "smart_casual",
            "mood_tag": "✨ 스마트 캐주얼",
            "top": {"name": "앤틱 머스터드", "hex": "#C99700", "standard_color": "머스터드"},
            "bottom": {"name": "소프트 샌드", "hex": "#D6C7B2", "standard_color": "베이지"},
            "point": None
        }
    ]
}

def fetch_user_wardrobe(user_id: int):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM wardrobe_items WHERE user_id = %s ORDER BY id DESC" if USE_POSTGRES else "SELECT * FROM wardrobe_items WHERE user_id = ? ORDER BY id DESC", (user_id,))
    rows = cursor.fetchall()
    db.close()
    items = []
    for r in rows:
        items.append({
            "id": r["id"],
            "category": r["category"],
            "nickname": r["nickname"],
            "colors": [c.strip() for c in r["colors"].split(",") if c.strip()],
            "materials": [m.strip() for m in r["materials"].split(",") if m.strip()]
        })
    return items

def generate_saju_analysis_payload(name, gender, y, m, d, cal_type, sijin):
    day_elem = "metal" if (y + m + d) % 2 == 0 else "wood"
    palettes = WADA_SANZO_PALETTES.get(day_elem, WADA_SANZO_PALETTES["metal"])
    chosen_palette = palettes[1] if len(palettes) > 1 and (d % 2 == 0) else palettes[0]
    is_reverse = (chosen_palette["mode"] == "reverse")
    
    # 5줄 분량의 명리 종합 풀이
    overview_text = f"""오늘 일진의 기운이 사주 본원과 자연스럽게 상생하여 막혀있던 흐름이 시원하게 뚫리는 형국입니다.
그동안 추진에 난항을 겪었거나 미루어 두었던 중요한 계획이 있다면 오늘 과감하게 첫발을 내딛기에 가장 이상적인 시기입니다.
주변 동료나 지인과의 소통에서도 귀인의 조력이 따르니, 자신의 생각과 비전을 명확하고 유연하게 전달해 보세요.
다만 지나친 확신으로 한 번에 많은 일을 벌이기보다는 핵심 우선순위 1~2가지에 온전히 에너지를 집중하는 것이 유리합니다.
마음의 여유를 잃지 않고 차분함을 유지할 때 금전과 사람이라는 두 가지 결실을 온전히 거머쥘 수 있는 대길의 하루입니다."""

    # 시간대별 흐름 가이드
    time_flow_data = {
        "morning": "머리가 맑고 집중력이 최고조에 이르는 시간입니다. 오늘 꼭 끝내야 할 가장 무겁고 중요한 업무나 의사결정을 오전에 집중 처리하세요.",
        "afternoon": "대인관계운과 협상운이 크게 열립니다. 미팅, 계약, 주변 사람들과의 의견 조율 및 외근 활동에서 뜻밖의 좋은 소식과 협력을 얻게 됩니다.",
        "evening": "활동 에너지를 차분하게 정돈하고 결실을 정리하는 때입니다. 무리한 약속보다는 편안한 식사와 가벼운 산책으로 내일을 위한 에너지를 충전하세요."
    }

    return {
        "user_name": name,
        "current_age": 2026 - y + 1,
        "birth_summary": f"{y}년 {m}월 {d}일생 · 사시(巳時)생",
        "daily_fortune": {
            "title": "도약과 결실의 하루",
            "score": 88,
            "advice": overview_text,
            "time_flow": time_flow_data,
            "lucky_item": "실버 메탈 시계",
            "lucky_number": "4, 9",
            "lucky_direction": "정서쪽 (백호 방위)",
            "recommended_menu": "속이 편안한 영양 솥밥",
            "mindset": "원칙을 지키며 유연하게 대처하기",
            "action": "오늘 완료해야 할 우선순위 3가지 메모하기",
            "is_reverse_day": is_reverse,
            "styling_mode": chosen_palette["mode"],
            "style_mood": chosen_palette["style_mood"],
            "mood_tag": chosen_palette["mood_tag"],
            "rule_title": chosen_palette["theme"],
            "rule_reason": chosen_palette["mood_desc"],
            "wada_palette": chosen_palette,
            "lucky_colors": [chosen_palette["top"]["standard_color"], chosen_palette["bottom"]["standard_color"]]
        },
        "saju_data": {
            "pillars_detail": {
                "year": {"cg": "戊", "cg_elem": "earth", "jj": "午", "jj_elem": "fire", "jijanggan": [{"char": "丙", "elem": "fire"}, {"char": "己", "elem": "earth"}, {"char": "丁", "elem": "fire"}]},
                "month": {"cg": "庚", "cg_elem": "metal", "jj": "申", "jj_elem": "metal", "jijanggan": [{"char": "戊", "elem": "earth"}, {"char": "壬", "elem": "water"}, {"char": "庚", "elem": "metal"}]},
                "day": {"cg": "辛", "cg_elem": "metal", "jj": "亥", "jj_elem": "water", "jijanggan": [{"char": "戊", "elem": "earth"}, {"char": "甲", "elem": "wood"}, {"char": "壬", "elem": "water"}]},
                "hour": {"cg": "癸", "cg_elem": "water", "jj": "巳", "jj_elem": "fire", "jijanggan": [{"char": "戊", "elem": "earth"}, {"char": "庚", "elem": "metal"}, {"char": "丙", "elem": "fire"}]}
            },
            "elements": {"wood": 15, "fire": 20, "earth": 25, "metal": 30, "water": 10}
        },
        "biorhythm": {
            "days_lived": 17540,
            "physical": {"status": "고조기", "val": 85},
            "emotional": {"status": "안정기", "val": 60},
            "intellectual": {"status": "최고조", "val": 95},
            "overall_summary": "지성 리듬이 최정점에 도달해 있어 전략적인 결정이나 계약에 최적의 타이밍입니다."
        }
    }

@app.get("/")
def get_index():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    elif os.path.exists("templates/index.html"):
        return FileResponse("templates/index.html")
    return HTMLResponse("<h1>index.html 파일을 찾을 수 없습니다.</h1>", status_code=404)

class KakaoAuthRequest(BaseModel):
    kakao_id: str
    name: Optional[str] = "달하 회원"
    gender: Optional[str] = "male"
    birthyear: Optional[str] = "1978"
    birthday: Optional[str] = "0813"
    birthday_type: Optional[str] = "SOLAR"

@app.post("/api/auth/kakao")
def kakao_auth_login(req: KakaoAuthRequest):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE kakao_id = %s" if USE_POSTGRES else "SELECT * FROM users WHERE kakao_id = ?", (req.kakao_id,))
    user = cursor.fetchone()

    if user:
        u_id = user["id"]
        u_coin = user["coin_balance"]
        cursor.execute("SELECT * FROM unlocked_reports WHERE user_id = %s ORDER BY id DESC" if USE_POSTGRES else "SELECT * FROM unlocked_reports WHERE user_id = ? ORDER BY id DESC", (u_id,))
        reports = [dict(r) for r in cursor.fetchall()]
        wardrobe = fetch_user_wardrobe(u_id)
        db.close()
        
        analysis = generate_saju_analysis_payload(
            user["name"], user["gender"], user["birth_year"], user["birth_month"], user["birth_day"], user["calendar_type"], user["sijin_index"]
        )
        return {
            "status": "existing_user",
            "user_id": u_id,
            "coin_balance": u_coin,
            "unlocked_reports": reports,
            "wardrobe_items": wardrobe,
            "saju_analysis": analysis
        }
    else:
        b_year = int(req.birthyear) if req.birthyear and req.birthyear.isdigit() else 1978
        b_month = 8
        b_day = 13
        if req.birthday and len(req.birthday) == 4:
            try:
                b_month = int(req.birthday[:2])
                b_day = int(req.birthday[2:])
            except:
                pass

        if USE_POSTGRES:
            cursor.execute("""
            INSERT INTO users (kakao_id, name, gender, birth_year, birth_month, birth_day, calendar_type, sijin_index, coin_balance)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1000) RETURNING id
            """, (req.kakao_id, req.name, req.gender or "male", b_year, b_month, b_day, "solar", 5))
            new_id = cursor.fetchone()["id"]
        else:
            cursor.execute("""
            INSERT INTO users (kakao_id, name, gender, birth_year, birth_month, birth_day, calendar_type, sijin_index, coin_balance)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1000)
            """, (req.kakao_id, req.name, req.gender or "male", b_year, b_month, b_day, "solar", 5))
            new_id = cursor.lastrowid

        db.commit()
        db.close()
        return {
            "status": "new_user_prefilled",
            "user_id": new_id,
            "coin_balance": 1000,
            "kakao_prefill": {
                "name": req.name, "gender": req.gender or "male",
                "birth_year": b_year, "birth_month": b_month, "birth_day": b_day,
                "calendar_type": "solar", "sijin_index": 5
            }
        }

class RegisterSajuRequest(BaseModel):
    user_id: int
    name: str
    gender: str
    birth_year: int
    birth_month: int
    birth_day: int
    calendar_type: str
    sijin_index: int

@app.post("/api/user/register-saju")
def register_saju_profile(req: RegisterSajuRequest):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
    UPDATE users SET name = %s, gender = %s, birth_year = %s, birth_month = %s, birth_day = %s, calendar_type = %s, sijin_index = %s
    WHERE id = %s
    """ if USE_POSTGRES else """
    UPDATE users SET name = ?, gender = ?, birth_year = ?, birth_month = ?, birth_day = ?, calendar_type = ?, sijin_index = ?
    WHERE id = ?
    """, (req.name, req.gender, req.birth_year, req.birth_month, req.birth_day, req.calendar_type, req.sijin_index, req.user_id))
    db.commit()
    db.close()

    analysis = generate_saju_analysis_payload(
        req.name, req.gender, req.birth_year, req.birth_month, req.birth_day, req.calendar_type, req.sijin_index
    )
    return {"status": "success", "coin_balance": 1000, "saju_analysis": analysis}

class WardrobeAddRequest(BaseModel):
    user_id: int
    category: str
    nickname: Optional[str] = ""
    colors: List[str]
    materials: List[str]

@app.post("/api/wardrobe/add")
def add_wardrobe_item(req: WardrobeAddRequest):
    db = get_db()
    cursor = db.cursor()
    colors_str = ",".join(req.colors)
    mats_str = ",".join(req.materials)
    final_name = req.nickname.strip() if (req.nickname and req.nickname.strip()) else f"{' '.join(req.colors)} {' '.join(req.materials)} {req.category}".strip()

    if USE_POSTGRES:
        cursor.execute("INSERT INTO wardrobe_items (user_id, category, nickname, colors, materials) VALUES (%s, %s, %s, %s, %s)",
                       (req.user_id, req.category, final_name, colors_str, mats_str))
    else:
        cursor.execute("INSERT INTO wardrobe_items (user_id, category, nickname, colors, materials) VALUES (?, ?, ?, ?, ?)",
                       (req.user_id, req.category, final_name, colors_str, mats_str))
    db.commit()
    db.close()
    return {"status": "success", "wardrobe_items": fetch_user_wardrobe(req.user_id)}

class WardrobeEditRequest(BaseModel):
    user_id: int
    category: str
    nickname: Optional[str] = ""
    colors: List[str]
    materials: List[str]

@app.put("/api/wardrobe/edit/{item_id}")
def edit_wardrobe_item(item_id: int, req: WardrobeEditRequest):
    db = get_db()
    cursor = db.cursor()
    colors_str = ",".join(req.colors)
    mats_str = ",".join(req.materials)
    final_name = req.nickname.strip() if (req.nickname and req.nickname.strip()) else f"{' '.join(req.colors)} {' '.join(req.materials)} {req.category}".strip()

    cursor.execute("""
    UPDATE wardrobe_items 
    SET category = %s, nickname = %s, colors = %s, materials = %s
    WHERE id = %s AND user_id = %s
    """ if USE_POSTGRES else """
    UPDATE wardrobe_items 
    SET category = ?, nickname = ?, colors = ?, materials = ?
    WHERE id = ? AND user_id = ?
    """, (req.category, final_name, colors_str, mats_str, item_id, req.user_id))
    db.commit()
    db.close()
    return {"status": "success", "wardrobe_items": fetch_user_wardrobe(req.user_id)}

@app.delete("/api/wardrobe/delete/{item_id}")
def delete_wardrobe_item(item_id: int, user_id: int):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM wardrobe_items WHERE id = %s AND user_id = %s" if USE_POSTGRES else "DELETE FROM wardrobe_items WHERE id = ? AND user_id = ?", (item_id, user_id))
    db.commit()
    db.close()
    return {"status": "success", "wardrobe_items": fetch_user_wardrobe(user_id)}

class UnlockReportRequest(BaseModel):
    user_id: int
    report_key: str
    cost: int
    sub_option: Optional[str] = "기본"
    partner_name: Optional[str] = "상대방"
    relation: Optional[str] = "인연"

@app.post("/api/reports/unlock")
def unlock_report_endpoint(req: UnlockReportRequest):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT coin_balance, name FROM users WHERE id = %s" if USE_POSTGRES else "SELECT coin_balance, name FROM users WHERE id = ?", (req.user_id,))
    user = cursor.fetchone()
    if not user or user["coin_balance"] < req.cost:
        db.close()
        return JSONResponse(status_code=400, content={"error": "복채 부족"})

    new_bal = user["coin_balance"] - req.cost
    cursor.execute("UPDATE users SET coin_balance = %s WHERE id = %s" if USE_POSTGRES else "UPDATE users SET coin_balance = ? WHERE id = ?", (new_bal, req.user_id))

    title_map = {
        "daewoon": "👑 자미두수 평생 대운 정밀 감명서",
        "sinnian": "📅 2026 丙午년 신년 총운 & 하반기 월별 토정비결",
        "gunghap": f"💞 {req.partner_name}님과의 정통 사주 인연 궁합",
        "wealth": "💰 평생 재물운 및 부동산 자산 분석",
        "love": f"💖 맞춤 평생 애정운 ({req.sub_option})",
        "business": f"🏢 평생 직업·사업 성공운 ({req.sub_option})",
        "health": "🌿 평생 건강운 및 오행 치유 섭생법"
    }
    report_title = title_map.get(req.report_key, "정밀 감명서")
    content = f"<p><strong>{user['name']}님을 위한 {report_title}</strong></p><p>사주 원국과 대운의 흐름을 대입한 결과, 귀하의 본원은 천을귀인의 조력을 받아 원하는 바를 성취하는 대길의 명조입니다.</p>"

    import datetime
    created_at = datetime.datetime.now().strftime("%Y.%m.%d")

    if USE_POSTGRES:
        cursor.execute("INSERT INTO unlocked_reports (user_id, report_key, report_title, report_content, created_at) VALUES (%s, %s, %s, %s, %s)",
                       (req.user_id, req.report_key, report_title, content, created_at))
    else:
        cursor.execute("INSERT INTO unlocked_reports (user_id, report_key, report_title, report_content, created_at) VALUES (?, ?, ?, ?, ?)",
                       (req.user_id, req.report_key, report_title, content, created_at))
    db.commit()

    cursor.execute("SELECT * FROM unlocked_reports WHERE user_id = %s ORDER BY id DESC" if USE_POSTGRES else "SELECT * FROM unlocked_reports WHERE user_id = ? ORDER BY id DESC", (req.user_id,))
    reports = [dict(r) for r in cursor.fetchall()]
    db.close()
    return {"status": "success", "new_balance": new_bal, "unlocked_reports": reports}

class ChargeCoinRequest(BaseModel):
    user_id: int
    amount: int

@app.post("/api/user/charge-coin")
def charge_coin_endpoint(req: ChargeCoinRequest):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT coin_balance FROM users WHERE id = %s" if USE_POSTGRES else "SELECT coin_balance FROM users WHERE id = ?", (req.user_id,))
    user = cursor.fetchone()
    new_bal = (user["coin_balance"] if user else 1000) + req.amount
    cursor.execute("UPDATE users SET coin_balance = %s WHERE id = %s" if USE_POSTGRES else "UPDATE users SET coin_balance = ? WHERE id = ?", (new_bal, req.user_id))
    db.commit()
    db.close()
    return {"status": "success", "new_balance": new_bal}

@app.get("/api/daily-tarot")
def get_daily_tarot(slot: int):
    return {
        "name": "I. THE MAGICIAN (마법사)",
        "keyword": "창조적 잠재력 · 탁월한 실행력",
        "symbolism": "4대 원소를 능숙히 다루는 마법사는 무한한 가능성과 시작을 의미합니다.",
        "reading_male": "주도적으로 프로젝트나 만남을 이끌어가기에 완벽한 시기입니다.",
        "reading_female": "빛나는 센스와 아이디어로 주변의 시선과 협력을 끌어당깁니다.",
        "action_guide": "망설이던 아이디어가 있다면 오늘 바로 구체적인 실행 계획을 작성하세요."
    }

@app.get("/api/zodiac-fortune")
def get_zodiac_fortune(type: str, key: str):
    return {
        "name": key,
        "score": 95,
        "title": "막힘없이 활짝 열리는 운세",
        "overview": "노력해 온 일들이 귀인을 만나 결실을 맺게 되는 뜻깊은 하루입니다.",
        "lucky_time": "오전 10시 ~ 12시",
        "lucky_match": "찰떡궁합: 소띠, 용띠",
        "lucky_item": "블루 계열 액세서리",
        "year_tips": [
            {"year_label": "1972년생", "tip": "작은 양보가 큰 이득으로 돌아오는 날입니다."},
            {"year_label": "1984년생", "tip": "적극적인 의견 개진이 좋은 성과를 냅니다."},
            {"year_label": "1996년생", "tip": "새로운 사람과의 교류에서 기회를 잡습니다."}
        ]
    }
