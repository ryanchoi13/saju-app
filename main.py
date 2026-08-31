import os
import random
import datetime
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

# 정통 20종 명리 개운 부적 매트릭스 DB
AUTHENTIC_TALISMAN_MATRIX = {
    "wood": {
        "wealth": {
            "title": "청목 생재부 (靑木 生財符)",
            "power": "사업 확장 · 신규 프로젝트 대박 · 활력 증진",
            "desc": "움트는 봄날의 거목처럼 사업과 재물의 터전을 크게 넓히고 활력을 불어넣는 비급 부적입니다.",
            "talisman_type": "wood_wealth",
            "seal_text": "生財"
        },
        "career": {
            "title": "문창 등과부 (文昌 登科符)",
            "power": "학업 성취 · 시험 합격 · 승진 영달",
            "desc": "문창성의 신령한 기운을 받아 학문과 시험, 승진의 관문을 단숨에 뚫어내는 부적입니다.",
            "talisman_type": "wood_career",
            "seal_text": "登科"
        },
        "love": {
            "title": "수목 화합부 (水木 和合符)",
            "power": "귀인 유입 · 좋은 인연 결속 · 대인 화합",
            "desc": "물과 나무가 만나 꽃을 피우듯, 마음에 품은 인연과 깊은 신뢰를 맺어주는 화합 부적입니다.",
            "talisman_type": "wood_love",
            "seal_text": "和合"
        },
        "ward": {
            "title": "벽사 청룡부 (辟邪 靑龍符)",
            "power": "구설수 차단 · 침체 극복 · 심신 안정",
            "desc": "청룡의 서기로 주변의 시기와 방해를 물리치고 올곧은 기운을 지켜내는 수호 부적입니다.",
            "talisman_type": "wood_ward",
            "seal_text": "辟邪"
        }
    },
    "fire": {
        "wealth": {
            "title": "적염 취재부 (赤焰 聚財符)",
            "power": "횡재수 포착 · 단기 매출 폭발 · 금전 회전",
            "desc": "타오르는 불꽃처럼 재물과 고객을 강력하게 끌어당겨 금전 회전을 극대화하는 부적입니다.",
            "talisman_type": "fire_wealth",
            "seal_text": "聚財"
        },
        "career": {
            "title": "천명 관운부 (天命 官運符)",
            "power": "명예 상승 · 리더십 발휘 · 직장 안착",
            "desc": "자신의 이름과 능력을 세상에 널리 알리고 조직 내에서 높은 명예를 얻게 돕는 부적입니다.",
            "talisman_type": "fire_career",
            "seal_text": "官運"
        },
        "love": {
            "title": "홍란 결연부 (紅鸞 結緣符)",
            "power": "도화 매력 발산 · 연애 성취 · 이성 호감",
            "desc": "홍란성의 빛나는 도화 기운을 발산하여 이성의 마음을 사로잡고 사랑을 성취하는 부적입니다.",
            "talisman_type": "fire_love",
            "seal_text": "結緣"
        },
        "ward": {
            "title": "주작 소재부 (朱雀 消災符)",
            "power": "불안 해소 · 충살 소멸 · 마음 평안",
            "desc": "불안정한 화기와 조급함을 정화하고 악살을 태워 마음의 평안을 되찾아주는 부적입니다.",
            "talisman_type": "fire_ward",
            "seal_text": "消災"
        }
    },
    "earth": {
        "wealth": {
            "title": "금고 보관부 (金庫 保管符)",
            "power": "자산 보존 · 부동산 취득 · 목돈 축적",
            "desc": "넓은 대지처럼 흩어지는 돈을 단단히 묶어 큰 자산으로 축적시키는 전통 보관 부적입니다.",
            "talisman_type": "earth_wealth",
            "seal_text": "保管"
        },
        "career": {
            "title": "태산 안착부 (泰山 安着符)",
            "power": "취업 성공 · 안정적 정착 · 계약 체결",
            "desc": "태산처럼 흔들림 없는 기반을 마련하여 원하는 직장이나 프로젝트에 안착하게 돕는 부적입니다.",
            "talisman_type": "earth_career",
            "seal_text": "安着"
        },
        "love": {
            "title": "화토 상생부 (火土 相生符)",
            "power": "가정 평안 · 신뢰 구축 · 백년해로",
            "desc": "따스한 온기로 서로에 대한 신뢰를 두텁게 다져 장기적인 사랑과 안정을 이끄는 부적입니다.",
            "talisman_type": "earth_love",
            "seal_text": "相生"
        },
        "ward": {
            "title": "황제 진택부 (黃帝 鎭宅符)",
            "power": "우환 예방 · 터 안전 · 재앙 소멸",
            "desc": "집안과 일터의 터를 안정시키고 예기치 못한 우환과 손실을 막아주는 비급 진택 부적입니다.",
            "talisman_type": "earth_ward",
            "seal_text": "鎭宅"
        }
    },
    "metal": {
        "wealth": {
            "title": "백호 금전부 (白虎 金錢符)",
            "power": "결단력 강화 · 투자 수익 실현 · 재물 쟁취",
            "desc": "백호의 날카로운 기운으로 투자 기회를 정확히 포착하고 실리를 쟁취하게 돕는 부적입니다.",
            "talisman_type": "metal_wealth",
            "seal_text": "金錢"
        },
        "career": {
            "title": "장원 급제부 (壯元 及第符)",
            "power": "전문 자격 취득 · 경쟁 돌파 · 독보적 성과",
            "desc": "치열한 경쟁 속에서 뛰어난 전문성을 발휘하여 당당히 정상에 오르게 하는 급제 부적입니다.",
            "talisman_type": "metal_career",
            "seal_text": "及第"
        },
        "love": {
            "title": "금옥 만당부 (金玉 滿堂符)",
            "power": "귀인 결속 · 품격 있는 만남 · 인복 확장",
            "desc": "보석처럼 품격 있고 나에게 큰 도움이 되는 든든한 귀인을 곁에 머물게 하는 부적입니다.",
            "talisman_type": "metal_love",
            "seal_text": "滿堂"
        },
        "ward": {
            "title": "참사 백호부 (斬邪 白虎符)",
            "power": "액운 절단 · 관재구설 차단 · 신변 보호",
            "desc": "날카로운 칼날처럼 나를 위협하는 사악한 기운과 관재구설을 일거에 베어내는 방어 부적입니다.",
            "talisman_type": "metal_ward",
            "seal_text": "斬邪"
        }
    },
    "water": {
        "wealth": {
            "title": "유수 통재부 (流水 通財符)",
            "power": "자금 유동성 확보 · 거래 성사 · 판로 개척",
            "desc": "끊이지 않고 흐르는 큰 강물처럼 자금의 물꼬를 트고 거래를 원활하게 성사시키는 부적입니다.",
            "talisman_type": "water_wealth",
            "seal_text": "通財"
        },
        "career": {
            "title": "지혜 총명부 (智慧 聰明符)",
            "power": "전략적 통찰 · 협상 우위 · 기획 성공",
            "desc": "깊은 바다와 같은 지혜와 직관력을 부여하여 중요한 협상과 기획을 승리로 이끄는 부적입니다.",
            "talisman_type": "water_career",
            "seal_text": "聰明"
        },
        "love": {
            "title": "애정 화합부 (愛情 和合符)",
            "power": "재회 성사 · 깊은 교감 · 짝사랑 성취",
            "desc": "멀어진 마음을 유연하게 이어주고 서먹했던 관계에 깊은 교감을 불어넣는 화합 부적입니다.",
            "talisman_type": "water_love",
            "seal_text": "愛合"
        },
        "ward": {
            "title": "현무 수호부 (玄武 守護符)",
            "power": "위기 극복 · 건강 회복 · 정신 안정",
            "desc": "현무의 두터운 방패로 갑작스러운 위기와 스트레스를 완벽히 막아내는 정통 수호 부적입니다.",
            "talisman_type": "water_ward",
            "seal_text": "守護"
        }
    }
}

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
            "theme": "통관용신 · 벽갑인정",
            "mood_desc": "풍성한 목(木) 기운을 앤틱 버건디 소품으로 부드럽게 통관하여 추진력을 폭발시킵니다.",
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
            "mood_desc": "은은한 코랄 브릭과 소프트 크림이 조화를 이루어 주변을 끌어당기는 카리스마를 만듭니다.",
            "mode": "harmony",
            "style_mood": "smart_casual",
            "mood_tag": "✨ 스마트 캐주얼",
            "top": {"name": "테라코타 앰버", "hex": "#C26D53", "standard_color": "코랄/오렌지"},
            "bottom": {"name": "오이스터 화이트", "hex": "#F4F1EA", "standard_color": "화이트"},
            "point": None
        },
        {
            "palette_no": 128,
            "theme": "수화기제(水火旣濟)",
            "mood_desc": "치솟는 화기를 차분한 미드나잇 인디고 소품으로 잡아주어 냉철한 판단력을 회복합니다.",
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
            "theme": "명경지수(明鏡止水) · 냉철함",
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
            "theme": "통관용신 · 조후 개운",
            "mood_desc": "사주 원국의 한기를 녹이기 위해 기본 의류 위에 앤틱 와인 소품을 얹어 재물의 숨통을 틔웁니다.",
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
            "theme": "유연한 교섭과 지혜",
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
    
    # 일진 테마 결정 (일진 날짜 합산 연산 기반: wealth, career, love, ward 순환)
    today_ord = datetime.date.today().toordinal()
    theme_keys = ["wealth", "career", "love", "ward"]
    today_theme_key = theme_keys[(today_ord + y + m + d) % 4]
    
    talisman_info = AUTHENTIC_TALISMAN_MATRIX.get(day_elem, AUTHENTIC_TALISMAN_MATRIX["metal"]).get(today_theme_key)
    
    overview_text = f"""오늘 일진의 기운이 사주 본원과 상생하여 막혀있던 흐름이 시원하게 풀리는 형국입니다.
미루어 두었던 중요한 계획이나 계약이 있다면 오늘 주도적으로 첫발을 내딛기에 매우 길합니다.
대인관계에서도 귀인의 조력이 따르니, 핵심 목표 1~2가지에 에너지를 집중해 보세요.
차분함과 유연성을 유지할 때 성과와 실리를 온전히 거머쥐는 알찬 하루가 될 것입니다."""

    time_flow_data = {
        "morning": "집중력과 판단력이 최고조에 이릅니다. 오늘 가장 중요한 핵심 업무나 결정을 오전에 처리하세요.",
        "afternoon": "대인관계와 소통운이 활짝 열립니다. 미팅, 조율, 외근 활동에서 뜻밖의 협력과 성과를 얻습니다.",
        "evening": "활동 에너지를 정리하는 시간입니다. 가벼운 산책과 편안한 휴식으로 내일의 기운을 충전하세요."
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
            "lucky_colors": [chosen_palette["top"]["standard_color"], chosen_palette["bottom"]["standard_color"]],
            "talisman": talisman_info
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
