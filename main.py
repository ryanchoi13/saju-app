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
        "wealth": {"title": "청목 생재부 (靑木 生財符)", "power": "사업 확장 · 신규 프로젝트 대박 · 활력 증진", "desc": "움트는 봄날의 거목처럼 사업과 재물의 터전을 크게 넓히고 활력을 불어넣는 비급 부적입니다.", "talisman_type": "wood_wealth", "seal_text": "生財"},
        "career": {"title": "문창 등과부 (文昌 登科符)", "power": "학업 성취 · 시험 합격 · 승진 영달", "desc": "문창성의 신령한 기운을 받아 학문과 시험, 승진의 관문을 단숨에 뚫어내는 부적입니다.", "talisman_type": "wood_career", "seal_text": "登科"},
        "love": {"title": "수목 화합부 (水木 和合符)", "power": "귀인 유입 · 좋은 인연 결속 · 대인 화합", "desc": "물과 나무가 만나 꽃을 피우듯, 마음에 품은 인연과 깊은 신뢰를 맺어주는 화합 부적입니다.", "talisman_type": "wood_love", "seal_text": "和合"},
        "ward": {"title": "벽사 청룡부 (辟邪 靑龍符)", "power": "구설수 차단 · 침체 극복 · 심신 안정", "desc": "청룡의 서기로 주변의 시기와 방해를 물리치고 올곧은 기운을 지켜내는 수호 부적입니다.", "talisman_type": "wood_ward", "seal_text": "辟邪"}
    },
    "fire": {
        "wealth": {"title": "적염 취재부 (赤焰 聚財符)", "power": "횡재수 포착 · 단기 매출 폭발 · 금전 회전", "desc": "타오르는 불꽃처럼 재물과 고객을 강력하게 끌어당겨 금전 회전을 극대화하는 부적입니다.", "talisman_type": "fire_wealth", "seal_text": "聚財"},
        "career": {"title": "천명 관운부 (天命 官運符)", "power": "명예 상승 · 리더십 발휘 · 직장 안착", "desc": "자신의 이름과 능력을 세상에 널리 알리고 조직 내에서 높은 명예를 얻게 돕는 부적입니다.", "talisman_type": "fire_career", "seal_text": "官運"},
        "love": {"title": "홍란 결연부 (紅鸞 結緣符)", "power": "도화 매력 발산 · 연애 성취 · 이성 호감", "desc": "홍란성의 빛나는 도화 기운을 발산하여 이성의 마음을 사로잡고 사랑을 성취하는 부적입니다.", "talisman_type": "fire_love", "seal_text": "結緣"},
        "ward": {"title": "주작 소재부 (朱雀 消災符)", "power": "불안 해소 · 충살 소멸 · 마음 평안", "desc": "불안정한 화기와 조급함을 정화하고 악살을 태워 마음의 평안을 되찾아주는 부적입니다.", "talisman_type": "fire_ward", "seal_text": "消災"}
    },
    "earth": {
        "wealth": {"title": "금고 보관부 (金庫 保管符)", "power": "자산 보존 · 부동산 취득 · 목돈 축적", "desc": "넓은 대지처럼 흩어지는 돈을 단단히 묶어 큰 자산으로 축적시키는 전통 보관 부적입니다.", "talisman_type": "earth_wealth", "seal_text": "保管"},
        "career": {"title": "태산 안착부 (泰山 安着符)", "power": "취업 성공 · 안정적 정착 · 계약 체결", "desc": "태산처럼 흔들림 없는 기반을 마련하여 원하는 직장이나 프로젝트에 안착하게 돕는 부적입니다.", "talisman_type": "earth_career", "seal_text": "安着"},
        "love": {"title": "화토 상생부 (火土 相生符)", "power": "가정 평안 · 신뢰 구축 · 백년해로", "desc": "따스한 온기로 서로에 대한 신뢰를 두텁게 다져 장기적인 사랑과 안정을 이끄는 부적입니다.", "talisman_type": "earth_love", "seal_text": "相生"},
        "ward": {"title": "황제 진택부 (黃帝 鎭宅符)", "power": "우환 예방 · 터 안전 · 재앙 소멸", "desc": "집안과 일터의 터를 안정시키고 예기치 못한 우환과 손실을 막아주는 비급 진택 부적입니다.", "talisman_type": "earth_ward", "seal_text": "鎭宅"}
    },
    "metal": {
        "wealth": {"title": "백호 금전부 (白虎 金錢符)", "power": "결단력 강화 · 투자 수익 실현 · 재물 쟁취", "desc": "백호의 날카로운 기운으로 투자 기회를 정확히 포착하고 실리를 쟁취하게 돕는 부적입니다.", "talisman_type": "metal_wealth", "seal_text": "金錢"},
        "career": {"title": "장원 급제부 (壯元 及第符)", "power": "전문 자격 취득 · 경쟁 돌파 · 독보적 성과", "desc": "치열한 경쟁 속에서 뛰어난 전문성을 발휘하여 당당히 정상에 오르게 하는 급제 부적입니다.", "talisman_type": "metal_career", "seal_text": "及第"},
        "love": {"title": "금옥 만당부 (金玉 滿堂符)", "power": "귀인 결속 · 품격 있는 만남 · 인복 확장", "desc": "보석처럼 품격 있고 나에게 큰 도움이 되는 든든한 귀인을 곁에 머물게 하는 부적입니다.", "talisman_type": "metal_love", "seal_text": "滿堂"},
        "ward": {"title": "참사 백호부 (斬邪 白虎符)", "power": "액운 절단 · 관재구설 차단 · 신변 보호", "desc": "날카로운 칼날처럼 나를 위협하는 사악한 기운과 관재구설을 일거에 베어내는 방어 부적입니다.", "talisman_type": "metal_ward", "seal_text": "斬邪"}
    },
    "water": {
        "wealth": {"title": "유수 통재부 (流水 通財符)", "power": "자금 유동성 확보 · 거래 성사 · 판로 개척", "desc": "끊이지 않고 흐르는 큰 강물처럼 자금의 물꼬를 트고 거래를 원활하게 성사시키는 부적입니다.", "talisman_type": "water_wealth", "seal_text": "通財"},
        "career": {"title": "지혜 총명부 (智慧 聰明符)", "power": "전략적 통찰 · 협상 우위 · 기획 성공", "desc": "깊은 바다와 같은 지혜와 직관력을 부여하여 중요한 협상과 기획을 승리로 이끄는 부적입니다.", "talisman_type": "water_career", "seal_text": "聰明"},
        "love": {"title": "애정 화합부 (愛情 和合符)", "power": "재회 성사 · 깊은 교감 · 짝사랑 성취", "desc": "멀어진 마음을 유연하게 이어주고 서먹했던 관계에 깊은 교감을 불어넣는 화합 부적입니다.", "talisman_type": "water_love", "seal_text": "愛合"},
        "ward": {"title": "현무 수호부 (玄武 守護符)", "power": "위기 극복 · 건강 회복 · 정신 안정", "desc": "현무의 두터운 방패로 갑작스러운 위기와 스트레스를 완벽히 막아내는 정통 수호 부적입니다.", "talisman_type": "water_ward", "seal_text": "守護"}
    }
}

# 오행별 다채로운 배색 팔레트 풀
WADA_SANZO_PALETTES = {
    "wood": [
        {"palette_no": 48, "theme": "청록의 상생과 지혜", "mood_desc": "세이지 그린과 포그 블루가 만나 사주의 기운을 유연하고 맑게 정돈합니다.", "mode": "harmony", "style_mood": "casual", "mood_tag": "🏃 캐주얼 & 액티브", "top": {"name": "세이지 포레스트", "hex": "#4A6B5B", "standard_color": "그린"}, "bottom": {"name": "포그 블루", "hex": "#8CA6B5", "standard_color": "스카이블루"}, "point": None},
        {"palette_no": 114, "theme": "통관용신 · 벽갑인정", "mood_desc": "풍성한 목(木) 기운을 앤틱 버건디 소품으로 부드럽게 통관하여 추진력을 폭발시킵니다.", "mode": "reverse", "style_mood": "casual", "mood_tag": "✦ 시크릿 반전 데이", "top": {"name": "딥 틸 그린", "hex": "#2B4C47", "standard_color": "그린"}, "bottom": {"name": "페일 에크루", "hex": "#E3DAC9", "standard_color": "베이지"}, "point": {"name": "앤틱 보르도", "hex": "#7A2E3D", "standard_color": "와인/버건디"}},
        {"palette_no": 52, "theme": "초목 성장의 활력", "mood_desc": "올리브 카키와 웜 화이트가 어우러져 안정적인 성장과 신뢰를 이끕니다.", "mode": "harmony", "style_mood": "smart_casual", "mood_tag": "✨ 스마트 캐주얼", "top": {"name": "올리브 카키", "hex": "#556B2F", "standard_color": "올리브/카키"}, "bottom": {"name": "오이스터 화이트", "hex": "#F4F1EA", "standard_color": "화이트"}, "point": None}
    ],
    "fire": [
        {"palette_no": 72, "theme": "따스한 온기와 활력", "mood_desc": "은은한 코랄 브릭과 소프트 크림이 조화를 이루어 주변을 끌어당기는 카리스마를 만듭니다.", "mode": "harmony", "style_mood": "smart_casual", "mood_tag": "✨ 스마트 캐주얼", "top": {"name": "테라코타 앰버", "hex": "#C26D53", "standard_color": "코랄/오렌지"}, "bottom": {"name": "오이스터 화이트", "hex": "#F4F1EA", "standard_color": "화이트"}, "point": None},
        {"palette_no": 128, "theme": "수화기제(水火旣濟)", "mood_desc": "치솟는 화기를 차분한 미드나잇 인디고 소품으로 잡아주어 냉철한 판단력을 회복합니다.", "mode": "reverse", "style_mood": "formal", "mood_tag": "👔 클래식 & 포멀", "top": {"name": "소프트 웜 베이지", "hex": "#D8C7B5", "standard_color": "베이지"}, "bottom": {"name": "차콜 슬레이트", "hex": "#3A3D40", "standard_color": "차콜"}, "point": {"name": "미드나잇 네이비", "hex": "#1B2A47", "standard_color": "네이비"}},
        {"palette_no": 78, "theme": "홍란 도화의 매력", "mood_desc": "소프트 로즈 핑크와 라이트 그레이가 결합하여 대인관계의 매력을 극대화합니다.", "mode": "harmony", "style_mood": "casual", "mood_tag": "🏃 캐주얼 & 액티브", "top": {"name": "더스티 로즈", "hex": "#D9828A", "standard_color": "핑크"}, "bottom": {"name": "쿨 그레이", "hex": "#A0AEC0", "standard_color": "그레이"}, "point": None}
    ],
    "earth": [
        {"palette_no": 91, "theme": "대지의 신뢰와 품격", "mood_desc": "묵직한 카멜 브라운과 오트밀 베이지가 만나 흔들리지 않는 신뢰와 포용력을 드러냅니다.", "mode": "harmony", "style_mood": "formal", "mood_tag": "👔 클래식 & 포멀", "top": {"name": "로즈우드 카멜", "hex": "#9E6B55", "standard_color": "카멜/브라운"}, "bottom": {"name": "오트밀 크림", "hex": "#EAE4D9", "standard_color": "아이보리/크림"}, "point": None},
        {"palette_no": 95, "theme": "화토상생(火土相生)", "mood_desc": "머스터드 옐로우와 차콜 팬츠가 만나 안정적인 자산 관리 능력을 높여줍니다.", "mode": "harmony", "style_mood": "smart_casual", "mood_tag": "✨ 스마트 캐주얼", "top": {"name": "머스터드 앰버", "hex": "#D97706", "standard_color": "머스터드"}, "bottom": {"name": "차콜 그레이", "hex": "#374151", "standard_color": "차콜"}, "point": None}
    ],
    "metal": [
        {"palette_no": 84, "theme": "명경지수(明鏡止水) · 냉철함", "mood_desc": "깊은 미드나잇 인디고와 안개빛 스카이블루가 만나 사주의 금전운과 전문성을 견고히 세웁니다.", "mode": "harmony", "style_mood": "casual", "mood_tag": "🏃 캐주얼 & 액티브", "top": {"name": "미드나잇 인디고", "hex": "#1F3044", "standard_color": "네이비"}, "bottom": {"name": "포그 스카이", "hex": "#8CA6B5", "standard_color": "스카이블루"}, "point": None},
        {"palette_no": 105, "theme": "통관용신 · 조후 개운", "mood_desc": "사주 원국의 한기를 녹이기 위해 기본 의류 위에 앤틱 와인 소품을 얹어 재물의 숨통을 틔웁니다.", "mode": "reverse", "style_mood": "casual", "mood_tag": "✦ 시크릿 반전 데이", "top": {"name": "딥 프러시안", "hex": "#1A2A3A", "standard_color": "네이비"}, "bottom": {"name": "더스티 스카이", "hex": "#9CB2C0", "standard_color": "스카이블루"}, "point": {"name": "앤틱 보르도", "hex": "#7A2E3D", "standard_color": "와인/버건디"}},
        {"palette_no": 88, "theme": "정제된 모던 클래식", "mood_desc": "차콜 블랙과 퓨어 화이트의 대비로 결단력과 명확한 전문성을 부각합니다.", "mode": "harmony", "style_mood": "formal", "mood_tag": "👔 클래식 & 포멀", "top": {"name": "퓨어 화이트", "hex": "#FFFFFF", "standard_color": "화이트"}, "bottom": {"name": "인텐스 블랙", "hex": "#18181B", "standard_color": "블랙"}, "point": None}
    ],
    "water": [
        {"palette_no": 62, "theme": "유연한 교섭과 지혜", "mood_desc": "머스터드 옐로우와 차분한 베이지가 결합하여 차가운 기운을 녹이고 유연한 소통을 이끕니다.", "mode": "harmony", "style_mood": "smart_casual", "mood_tag": "✨ 스마트 캐주얼", "top": {"name": "앤틱 머스터드", "hex": "#C99700", "standard_color": "머스터드"}, "bottom": {"name": "소프트 샌드", "hex": "#D6C7B2", "standard_color": "베이지"}, "point": None},
        {"palette_no": 66, "theme": "심해의 평온과 통찰", "mood_desc": "네이비와 민트 라임의 산뜻한 포인트가 사주의 활력을 빠르게 끌어올립니다.", "mode": "harmony", "style_mood": "casual", "mood_tag": "🏃 캐주얼 & 액티브", "top": {"name": "로열 네이비", "hex": "#1E3A8A", "standard_color": "네이비"}, "bottom": {"name": "민트 세이지", "hex": "#6EE7B7", "standard_color": "민트/라임"}, "point": None}
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

def calculate_four_pillars(y: int, m: int, d: int, sijin_idx: int):
    gan_list = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    ji_list = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    elem_map = {
        "甲": "wood", "乙": "wood", "丙": "fire", "丁": "fire", "戊": "earth", "己": "earth", "庚": "metal", "辛": "metal", "壬": "water", "癸": "water",
        "子": "water", "丑": "earth", "寅": "wood", "卯": "wood", "辰": "earth", "巳": "fire", "午": "fire", "未": "earth", "申": "metal", "酉": "metal", "戌": "earth", "亥": "water"
    }
    jjg_map = {
        "子": [{"char": "壬", "elem": "water"}, {"char": "癸", "elem": "water"}],
        "丑": [{"char": "癸", "elem": "water"}, {"char": "辛", "elem": "metal"}, {"char": "己", "elem": "earth"}],
        "寅": [{"char": "戊", "elem": "earth"}, {"char": "丙", "elem": "fire"}, {"char": "甲", "elem": "wood"}],
        "卯": [{"char": "甲", "elem": "wood"}, {"char": "乙", "elem": "wood"}],
        "辰": [{"char": "乙", "elem": "wood"}, {"char": "癸", "elem": "water"}, {"char": "戊", "elem": "earth"}],
        "巳": [{"char": "戊", "elem": "earth"}, {"char": "庚", "elem": "metal"}, {"char": "丙", "elem": "fire"}],
        "午": [{"char": "丙", "elem": "fire"}, {"char": "己", "elem": "earth"}, {"char": "丁", "elem": "fire"}],
        "未": [{"char": "丁", "elem": "fire"}, {"char": "乙", "elem": "wood"}, {"char": "己", "elem": "earth"}],
        "申": [{"char": "戊", "elem": "earth"}, {"char": "壬", "elem": "water"}, {"char": "庚", "elem": "metal"}],
        "酉": [{"char": "庚", "elem": "metal"}, {"char": "辛", "elem": "metal"}],
        "戌": [{"char": "辛", "elem": "metal"}, {"char": "丁", "elem": "fire"}, {"char": "戊", "elem": "earth"}],
        "亥": [{"char": "戊", "elem": "earth"}, {"char": "甲", "elem": "wood"}, {"char": "壬", "elem": "water"}]
    }

    y_gan = gan_list[(y - 4) % 10]
    y_ji = ji_list[(y - 4) % 12]
    
    m_gan = gan_list[(y * 2 + m) % 10]
    m_ji = ji_list[(m + 1) % 12]
    
    base_date = datetime.date(1900, 1, 1)
    target_date = datetime.date(y, m, d)
    diff_days = (target_date - base_date).days
    d_gan = gan_list[(diff_days + 0) % 10]
    d_ji = ji_list[(diff_days + 10) % 12]
    
    if sijin_idx >= 0:
        h_ji = ji_list[sijin_idx % 12]
        h_gan = gan_list[(diff_days * 2 + sijin_idx) % 10]
    else:
        h_gan = "-"
        h_ji = "-"

    counts = {"wood": 0, "fire": 0, "earth": 0, "metal": 0, "water": 0}
    for char in [y_gan, y_ji, m_gan, m_ji, d_gan, d_ji, h_gan, h_ji]:
        if char in elem_map:
            counts[elem_map[char]] += 1
    total_c = max(1, sum(counts.values()))
    dist = {k: int((v / total_c) * 100) for k, v in counts.items()}
    remainder = 100 - sum(dist.values())
    dist["metal"] += remainder

    return {
        "pillars": {
            "year": {"cg": y_gan, "cg_elem": elem_map[y_gan], "jj": y_ji, "jj_elem": elem_map[y_ji], "jijanggan": jjg_map[y_ji]},
            "month": {"cg": m_gan, "cg_elem": elem_map[m_gan], "jj": m_ji, "jj_elem": elem_map[m_ji], "jijanggan": jjg_map[m_ji]},
            "day": {"cg": d_gan, "cg_elem": elem_map[d_gan], "jj": d_ji, "jj_elem": elem_map[d_ji], "jijanggan": jjg_map[d_ji]},
            "hour": {"cg": h_gan, "cg_elem": elem_map.get(h_gan, "none"), "jj": h_ji, "jj_elem": elem_map.get(h_ji, "none"), "jijanggan": jjg_map.get(h_ji, [])}
        },
        "elements": dist,
        "day_elem": elem_map[d_gan],
        "singang_label": "신강(身强) 사주" if dist[elem_map[d_gan]] >= 30 else "신약(身弱) 사주"
    }

# 매일 자정에 당일 날짜 기반으로 완전히 새롭게 바뀌는 오늘운세 생성기
def generate_saju_analysis_payload(name, gender, y, m, d, cal_type, sijin):
    saju_res = calculate_four_pillars(y, m, d, sijin)
    day_elem = saju_res["day_elem"]
    
    today = datetime.date.today()
    today_ord = today.toordinal()
    
    # 당일 날짜(연월일) + 사주 고유값을 결합한 시드 -> 날짜가 바뀌면 매일 달라짐
    daily_seed = today_ord * 1000 + (y % 100) * 100 + m * 10 + d + sijin
    rng = random.Random(daily_seed)
    
    palettes = WADA_SANZO_PALETTES.get(day_elem, WADA_SANZO_PALETTES["metal"])
    chosen_palette = palettes[rng.randint(0, len(palettes) - 1)]
    is_reverse = (chosen_palette["mode"] == "reverse")
    
    theme_keys = ["wealth", "career", "love", "ward"]
    today_theme_key = theme_keys[(today_ord + y + m + d) % 4]
    talisman_info = AUTHENTIC_TALISMAN_MATRIX.get(day_elem, AUTHENTIC_TALISMAN_MATRIX["metal"]).get(today_theme_key)

    sijin_names = ["자시(子時)", "축시(丑時)", "인시(寅時)", "묘시(卯時)", "진시(辰時)", "사시(巳時)", "오시(午時)", "미시(未時)", "신시(申時)", "유시(酉時)", "술시(戌時)", "해시(亥時)"]
    sijin_str = sijin_names[sijin] if 0 <= sijin < 12 else "시간모름"

    # 날짜별 역동적 텍스트 풀
    titles_pool = [
        "도약과 결실이 함께하는 대길의 하루",
        "귀인의 조력으로 막힌 물꼬가 시원하게 트이는 날",
        "지혜로운 판단이 뜻밖의 실리를 부르는 하루",
        "차분한 내실 경영이 큰 성과로 이어지는 길일",
        "새로운 기회와 좋은 인연이 찾아오는 상생의 날",
        "탁월한 집중력으로 오랜 난제를 해결하는 하루"
    ]
    
    advices_pool = [
        f"{today.strftime('%m월 %d일')} 오늘의 일진 기운이 사주 본원과 상생하여 막혀있던 흐름이 시원하게 풀립니다.\n미루어 두었던 중요한 계획이나 제안이 있다면 오늘 주도적으로 첫발을 내딛기에 길합니다.\n핵심 목표 1~2가지에 에너지를 집중할 때 성과를 온전히 거머쥐게 됩니다.",
        f"{today.strftime('%m월 %d일')} 대인관계에서 천을귀인의 서기가 비추는 날입니다.\n혼자 고민하기보다는 신뢰할 수 있는 동료나 지인과 상의할 때 명쾌한 해답을 얻습니다.\n유연하고 경청하는 자세가 뜻밖의 횡재와 기회를 부릅니다.",
        f"{today.strftime('%m월 %d일')} 차분하게 내실을 다지며 실리를 챙기기에 최적인 일진입니다.\n불필요한 과욕을 경계하고 현재 진행 중인 일의 디테일을 점검하세요.\n원칙을 지키는 정직한 태도가 주변의 큰 신뢰와 지지를 이끌어냅니다.",
        f"{today.strftime('%m월 %d일')} 활동 에너지와 지성 리듬이 조화를 이루는 역동적인 하루입니다.\n새로운 아이디어가 번뜩인다면 망설이지 말고 실행 계획으로 구체화하세요.\n발빠른 대처가 경쟁에서 우위를 점하는 결정적 무기가 됩니다."
    ]

    mindset_pool = [
        "원칙을 지키며 유연하게 대처하기",
        "상대방의 입장을 먼저 경청하고 배려하기",
        "조급함을 내려놓고 차분한 호흡 유지하기",
        "핵심 우선순위에 집중하고 잔가지는 쳐내기",
        "작은 성공에도 감사하며 긍정의 기운 돋우기",
        "자신의 직관과 노력을 굳게 신뢰하기"
    ]

    action_pool = [
        "오늘 완료해야 할 우선순위 3가지 메모하기",
        "가장 중요한 미팅이나 결정을 오전에 집중 처리하기",
        "감사한 지인 1명에게 따뜻한 안부 메시지 보내기",
        "점심 식사 후 10분간 가벼운 산책으로 기운 충전하기",
        "퇴근 전 책상과 주변 환경을 깔끔하게 정돈하기",
        "잠들기 전 오늘 하루의 감사한 일 3가지 되새기기"
    ]

    lucky_items_pool = ["실버 메탈 시계", "가죽 카드지갑", "심플한 만년필", "옥/원석 팔찌", "린넨 손수건", "미니멀 텀블러", "블루투스 이어폰"]
    lucky_menus_pool = ["속이 편안한 영양 솥밥", "맑은 조개탕", "신선한 비빔밥", "담백한 두부 요리", "따뜻한 메밀 국수", "정갈한 생선구이 정식"]
    lucky_dirs_pool = ["정동쪽 (청룡 방위)", "정남쪽 (주작 방위)", "정서쪽 (백호 방위)", "정북쪽 (현무 방위)", "남동쪽 (풍수 길방)"]

    return {
        "user_name": name,
        "current_age": 2026 - y + 1,
        "birth_summary": f"{y}년 {m}월 {d}일생 · {sijin_str}생",
        "daily_fortune": {
            "title": rng.choice(titles_pool),
            "score": rng.randint(84, 98),
            "advice": rng.choice(advices_pool),
            "time_flow": {
                "morning": "오전 (09시~12시): 판단력과 집중력이 정점입니다. 핵심 업무와 결정을 처리하세요.",
                "afternoon": "오후 (13시~18시): 소통과 협상운이 상승합니다. 미팅이나 협력에서 좋은 결과를 냅니다.",
                "evening": "저녁 (19시 이후): 심신을 정돈하는 힐링의 시간. 가벼운 휴식으로 활력을 채우세요."
            },
            "lucky_item": rng.choice(lucky_items_pool),
            "lucky_number": f"{rng.randint(1,9)}, {rng.randint(1,9)}",
            "lucky_direction": rng.choice(lucky_dirs_pool),
            "recommended_menu": rng.choice(lucky_menus_pool),
            "mindset": rng.choice(mindset_pool),
            "action": rng.choice(action_pool),
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
            "pillars_detail": saju_res["pillars"],
            "elements": saju_res["elements"],
            "singang_label": saju_res["singang_label"]
        },
        "biorhythm": {
            "days_lived": (today - datetime.date(y, m, d)).days,
            "physical": {"status": "고조기", "val": rng.randint(75, 95)},
            "emotional": {"status": "안정기", "val": rng.randint(60, 85)},
            "intellectual": {"status": "최고조", "val": rng.randint(85, 99)},
            "overall_summary": "지성 리듬과 활동 에너지가 상위 구간에 위치하여 전략적 결정이나 계약에 최적인 날입니다."
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

# 사용자 사주 기반 12개월 전체 및 테마별 1,500자+ 풀버전 정밀 감명서 생성 엔진
def build_detailed_report_content(report_key: str, user_dict: dict, sub_opt: str, p_name: str, relation: str):
    name = user_dict.get("name", "회원")
    y = user_dict.get("birth_year", 1978)
    m = user_dict.get("birth_month", 8)
    d = user_dict.get("birth_day", 13)
    sijin = user_dict.get("sijin_index", 5)
    age = 2026 - y + 1

    saju_calc = calculate_four_pillars(y, m, d, sijin)
    day_elem = saju_calc["day_elem"]

    if report_key == "daewoon":
        return f"""
        <div style="display:flex; flex-direction:column; gap:16px; font-size:13.5px; line-height:1.85; color:#334155;">
            <div>
                <h4 style="font-size:15.5px; font-weight:800; color:#0F172A; margin-bottom:8px;">Chapter 1. 선천 명반(命盤) 및 본원 격국 심층 감명</h4>
                <p>귀하의 본원은 <strong>{day_elem.upper()}(오행 본명)</strong>의 정기를 품고 태어났으며, 자미두수 명궁의 주성이 조좌하여 흔들리지 않는 중심축과 높은 기상을 지니고 있습니다.</p>
                <p>내면에 자리한 관록궁과 재백궁의 길합으로 인해 인생 전반에서 위기를 맞이하더라도 반드시 천을귀인의 조력을 받아 기사회생하고 실리를 쟁취하는 명조입니다.</p>
            </div>
            <hr style="border:none; border-top:1px solid #E2E8F0;">
            <div>
                <h4 style="font-size:15.5px; font-weight:800; color:#0F172A; margin-bottom:8px;">Chapter 2. 생애 10년 주기 대운(大運)의 4대 변곡점</h4>
                <p>• <strong>유년·청년기 (20~39세):</strong> 기반 형성기입니다. 다양한 도전과 수련을 통해 지혜를 축적하고 자신의 핵심 무기를 갈고닦은 시기였습니다.</p>
                <p style="color:#047857; font-weight:700; margin: 6px 0;">• <strong>중장년 대도약기 (40~59세) [현재 위치: {age}세]:</strong> 평생의 가장 큰 결실을 맺는 황금기입니다. 용신(用神)의 기운이 온전히 발현되어 본업의 권위가 서고 자산의 터전이 확고히 세워집니다.</p>
                <p>• <strong>노년 안락기 (60세 이후):</strong> 성취한 결실을 지키고 명예를 누리며 가문을 안정적으로 번영시키는 평온의 구간입니다.</p>
            </div>
            <hr style="border:none; border-top:1px solid #E2E8F0;">
            <div>
                <h4 style="font-size:15.5px; font-weight:800; color:#0F172A; margin-bottom:8px;">Chapter 3. 평생 부귀(富貴)와 개운 처세법</h4>
                <p>{name}님께서는 원칙을 견고히 지키시되, 인간관계에서 유연한 소통을 이어갈 때 재물과 인복이 배가됩니다. 특히 50대 초반으로 진입하는 길목에서 무리한 문어발식 확장보다는 본업의 전문성을 공고히 하는 것이 평생의 부를 지키는 비결입니다.</p>
            </div>
        </div>
        """
    elif report_key == "sinnian":
        return f"""
        <div style="display:flex; flex-direction:column; gap:16px; font-size:13.5px; line-height:1.85; color:#334155;">
            <div>
                <h4 style="font-size:15.5px; font-weight:800; color:#166534; margin-bottom:8px;">Chapter 1. 2026 丙午년 1년 총운 풀이 (재물·애정·건강 종합)</h4>
                <p><strong>[전체 총평]</strong> 2026년 붉은 말의 해(丙午年)는 타오르는 양기와 결실의 에너지가 공존하는 역동적인 해입니다. 귀하의 사주 원국과 병오년 세운이 상생(相生)의 순환을 이루어, 지난 2~3년간 정체되었던 일들이 시원하게 뚫리는 형국입니다.</p>
                <p><strong>[💰 재물 & 직업운]</strong> 추진 중인 프로젝트나 사업적 제안이 결실을 맺습니다. 특히 하반기(8월~10월)에 큰 자금 회전과 계약 성사가 따르며, 능력을 인정받아 명예가 상승합니다.</p>
                <p><strong>[💖 애정 & 대인관계]</strong> 귀인과 도화의 기운이 함께 들어옵니다. 소원했던 관계는 오해를 풀고 신뢰를 회복하며, 새로운 인연을 찾는 분은 품격 있는 동반자를 만날 기회가 열립니다.</p>
                <p><strong>[🌿 건강 & 조후 관리]</strong> 화(火) 기운이 왕성하므로 과로로 인한 피로와 심혈관계의 밸런스를 지켜야 합니다. 충분한 수분 섭취와 차분한 명상으로 수화기제(水火旣濟)를 이루세요.</p>
            </div>
            <hr style="border:none; border-top:1px solid #E2E8F0;">
            <div>
                <h4 style="font-size:15.5px; font-weight:800; color:#166534; margin-bottom:10px;">Chapter 2. 2026년 1월 ~ 12월 12개월 전체 정밀 토정비결</h4>
                <div style="display:flex; flex-direction:column; gap:8px;">
                    <p><strong>1월:</strong> 한 해의 기틀을 잡는 달. 무리한 확장보다 계획을 치밀하게 다듬으세요.</p>
                    <p><strong>2월:</strong> 새로운 제안이 들어오는 시기. 신중하게 검토 후 첫발을 떼세요.</p>
                    <p><strong>3월:</strong> 봄바람과 함께 인복이 확장됩니다. 대인관계에서 귀인을 만납니다.</p>
                    <p><strong>4월:</strong> 작은 지출 관리가 필요한 달. 충동적인 결정을 경계하세요.</p>
                    <p><strong>5월:</strong> 능력이 세상에 드러나는 시기. 적극적으로 아이디어를 개진하세요.</p>
                    <p><strong>6월:</strong> 상반기를 정리하고 재충전하는 시간. 건강과 컨디션을 챙기세요.</p>
                    <p><strong>7월:</strong> 주변의 의견이 분분할 수 있습니다. 중심을 지키고 내실을 다지세요.</p>
                    <p style="color:#047857; font-weight:700;"><strong>8월 [★ 황금의 달]:</strong> 계약, 승진, 자산 증식에서 가장 큰 성과가 터지는 절정기입니다.</p>
                    <p><strong>9월:</strong> 귀인의 조력으로 새로운 협력 기회가 생깁니다. 유연하게 교섭하세요.</p>
                    <p style="color:#047857; font-weight:700;"><strong>10월 [★ 결실의 달]:</strong> 투자와 시험, 자격증 취득 등 노력했던 일의 결실을 쟁취합니다.</p>
                    <p><strong>11월:</strong> 차분한 마무리가 필요한 달. 무리한 투자를 피하고 안정을 취하세요.</p>
                    <p><strong>12월:</strong> 한 해의 수확을 거두고 2027년의 새로운 도약을 준비하는 화합의 달입니다.</p>
                </div>
            </div>
        </div>
        """
    elif report_key == "gunghap":
        return f"""
        <div style="display:flex; flex-direction:column; gap:14px; font-size:13.5px; line-height:1.85; color:#334155;">
            <h4 style="font-size:15.5px; font-weight:800; color:#9F1239;">💞 {name}님과 {p_name}님의 정통 사주 인연 궁합 ({relation})</h4>
            <p><strong>1. 오행 상생 밸런스:</strong> {name}님의 본원과 {p_name}님의 기운은 서로의 부족한 점을 메워주는 음양의 상호보완적 조화를 이룹니다.</p>
            <p><strong>2. 성격 및 소통 궁합:</strong> {name}님의 과감한 결단력과 {p_name}님의 섬세한 배려가 어우러져, 크고 작은 갈등이 발생하더라도 대화를 통해 더 깊은 신뢰로 승화시키는 길연(吉緣)입니다.</p>
            <p><strong>3. 장기적 번영 가이드:</strong> 서로의 독립적인 영역을 존중하고 중요한 결정을 함께 상의할 때 가정과 사업 모두에서 큰 번영을 이룰 수 있습니다.</p>
        </div>
        """
    elif report_key == "wealth":
        return f"""
        <div style="display:flex; flex-direction:column; gap:14px; font-size:13.5px; line-height:1.85; color:#334155;">
            <h4 style="font-size:15.5px; font-weight:800; color:#0F172A;">💰 {name}님의 평생 재물운 및 부동산 자산 분석</h4>
            <p><strong>1. 평생 재물 그릇:</strong> 귀하의 사주 원국에는 재고(財庫)의 문이 안정적으로 자리하여, 젊은 시절 흩어졌던 자금이 나이가 들수록 큰 목돈으로 축적되는 대기만성형 재물운입니다.</p>
            <p><strong>2. 투자 및 부동산 적기:</strong> 단기적인 시세 차익보다는 실물 자산, 토지 및 부동산 등 장기적 가치를 지닌 자산에 투자할 때 가장 큰 결실을 맺습니다.</p>
            <p><strong>3. 손재수 방어법:</strong> 불확실한 보증이나 감정적인 금전 거래를 철저히 차단하는 것이 평생의 부를 지키는 핵심 열쇠입니다.</p>
        </div>
        """
    elif report_key == "love":
        return f"""
        <div style="display:flex; flex-direction:column; gap:14px; font-size:13.5px; line-height:1.85; color:#334155;">
            <h4 style="font-size:15.5px; font-weight:800; color:#0F172A;">💖 {name}님의 맞춤 평생 애정운 ({sub_opt})</h4>
            <p><strong>1. 인연의 특성과 성향:</strong> 귀하와 가장 이상적인 조화를 이루는 인연은 차분하면서도 내면이 단단하고, 귀하의 비전과 가치관을 온전히 지지해 줄 수 있는 사람입니다.</p>
            <p><strong>2. 애정운의 황금 타이밍:</strong> 세운과 일진에서 도화와 천을귀인이 합을 이루는 시기에 가장 순수하고 깊은 신뢰의 사랑이 찾아옵니다.</p>
            <p><strong>3. 화합을 위한 개운법:</strong> 솔직한 감정 표현과 상대방의 입장을 먼저 헤아리는 유연한 태도가 평생의 애정을 견고하게 지켜줍니다.</p>
        </div>
        """
    elif report_key == "business":
        return f"""
        <div style="display:flex; flex-direction:column; gap:14px; font-size:13.5px; line-height:1.85; color:#334155;">
            <h4 style="font-size:15.5px; font-weight:800; color:#0F172A;">🏢 {name}님의 평생 직업·사업 성공운 ({sub_opt})</h4>
            <p><strong>1. 독보적 직무 적성:</strong> 귀하는 기획력과 결단력을 동시에 갖추고 있어, 조직 내 핵심 리더나 독자적인 전문직, 사업가로서 정상에 오를 잠재력을 보유하고 있습니다.</p>
            <p><strong>2. 승진 및 창업 적기:</strong> 사주의 관성(官星)과 인성(印星)이 상생하는 시기에 과감하게 새로운 영역으로의 도전이나 승진 기회를 포착해야 합니다.</p>
            <p><strong>3. 리더십 개운 수칙:</strong> 부하 직원이나 협력 파트너와의 신뢰를 최우선으로 삼을 때 관재구설을 완벽히 차단하고 지속 가능한 성공을 거둡니다.</p>
        </div>
        """
    elif report_key == "health":
        return f"""
        <div style="display:flex; flex-direction:column; gap:14px; font-size:13.5px; line-height:1.85; color:#334155;">
            <h4 style="font-size:15.5px; font-weight:800; color:#0F172A;">🌿 {name}님의 평생 건강운 및 오행 치유 섭생법</h4>
            <p><strong>1. 취약 오행 장기 진단:</strong> 사주 원국의 오행 분포에 따라 스트레스가 누적될 때 간(木) 또는 심혈관(火) 계통에 무리가 올 수 있으니 평소 완급 조절이 필요합니다.</p>
            <p><strong>2. 맞춤 섭생 및 식이요법:</strong> 자극적인 음식보다는 담백한 자연 식단과 충분한 수분 섭취로 체내 열기와 조후를 균형 있게 다스리세요.</p>
            <p><strong>3. 심신 치유 운동법:</strong> 격렬한 운동보다는 숲길 걷기, 요가, 수영 등 유연성과 호흡을 가다듬는 유산소 운동이 건강 개운에 가장 탁월합니다.</p>
        </div>
        """
    else:
        return f"<p><strong>{name}님을 위한 정밀 감명 리포트</strong></p><p>귀하의 명조를 다각도로 분석한 결과입니다.</p>"

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
    cursor.execute("SELECT * FROM users WHERE id = %s" if USE_POSTGRES else "SELECT * FROM users WHERE id = ?", (req.user_id,))
    user = cursor.fetchone()
    if not user or user["coin_balance"] < req.cost:
        db.close()
        return JSONResponse(status_code=400, content={"error": "복채 부족"})

    new_bal = user["coin_balance"] - req.cost
    cursor.execute("UPDATE users SET coin_balance = %s WHERE id = %s" if USE_POSTGRES else "UPDATE users SET coin_balance = ? WHERE id = ?", (new_bal, req.user_id))

    title_map = {
        "daewoon": "👑 자미두수 평생 대운 정밀 감명서",
        "sinnian": "📅 2026 丙午년 신년 총운 & 12개월 토정비결",
        "gunghap": f"💞 {req.partner_name}님과의 정통 사주 인연 궁합",
        "wealth": "💰 평생 재물운 및 부동산 자산 분석",
        "love": f"💖 맞춤 평생 애정운 ({req.sub_option})",
        "business": f"🏢 평생 직업·사업 성공운 ({req.sub_option})",
        "health": "🌿 평생 건강운 및 오행 치유 섭생법"
    }
    report_title = title_map.get(req.report_key, "정밀 감명서")
    content = build_detailed_report_content(req.report_key, dict(user), req.sub_option, req.partner_name, req.relation)

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
    today_ord = datetime.date.today().toordinal()
    tarot_cards = [
        {"name": "I. THE MAGICIAN (마법사)", "keyword": "창조적 잠재력 · 탁월한 실행력", "symbolism": "4대 원소를 능숙히 다루는 마법사는 무한한 가능성과 시작을 의미합니다.", "reading_male": "주도적으로 프로젝트나 만남을 이끌어가기에 완벽한 시기입니다.", "reading_female": "빛나는 센스와 아이디어로 주변의 시선과 협력을 끌어당깁니다.", "action_guide": "망설이던 아이디어가 있다면 오늘 바로 구체적인 실행 계획을 작성하세요."},
        {"name": "0. THE FOOL (바보)", "keyword": "새로운 여정 · 순수한 모험심", "symbolism": "절벽 끝에서도 당당한 바보는 틀에 얽매이지 않는 자유로운 도약을 상징합니다.", "reading_male": "과거의 부담을 털어내고 새로운 방향을 모색할 때 뜻밖의 돌파구가 열립니다.", "reading_female": "선입견 없이 마음을 열고 다가갈 때 새로운 인연과 기쁨을 얻습니다.", "action_guide": "가보지 않았던 새로운 길이나 방식을 시도해 보세요."},
        {"name": "XIX. THE SUN (태양)", "keyword": "명확한 성공 · 긍정의 생명력", "symbolism": "빛나는 태양 아래 아이는 순수한 행복과 확실한 승리를 의미합니다.", "reading_male": "노력해 온 결과가 세상에 당당히 드러나 높은 평가를 받습니다.", "reading_female": "주변에 따뜻한 에너지를 전파하며 중심적인 위치에 서게 됩니다.", "action_guide": "자신감을 가지고 당신의 성과와 제안을 널리 알리세요."}
    ]
    card = tarot_cards[(today_ord + slot) % len(tarot_cards)]
    return card

# 띠별 5개 세대 연도 및 별자리 전용 데이터 분기 API (날짜별로 매일 업데이트)
@app.get("/api/zodiac-fortune")
def get_zodiac_fortune(type: str, key: str):
    today = datetime.date.today()
    today_ord = today.toordinal()
    rng = random.Random(today_ord + hash(key))

    if type == "star":
        star_meta = {
            "양자리": {"elem": "불 (Fire)", "planet": "화성 (Mars)", "color": "루비 레드", "time": "오전 07시 ~ 09시", "focus": "새로운 기획에 도전할 때 주변의 강력한 지지를 받습니다. 솔직한 표현이 매력을 높입니다."},
            "황소자리": {"elem": "흙 (Earth)", "planet": "금성 (Venus)", "color": "에메랄드 그린", "time": "오후 01시 ~ 03시", "focus": "재정적 안정을 도모하기에 좋습니다. 미식이나 예술적 힐링이 행운을 부릅니다."},
            "쌍둥이자리": {"elem": "공기 (Air)", "planet": "수성 (Mercury)", "color": "스카이 블루", "time": "오전 10시 ~ 12시", "focus": "활발한 정보 교류와 소통이 성과로 이어집니다. 가벼운 연락이 귀인으로 발전합니다."},
            "게자리": {"elem": "물 (Water)", "planet": "달 (Moon)", "color": "실버 화이트", "time": "저녁 08시 ~ 10시", "focus": "가족과 연인에게서 따스한 위로를 얻습니다. 감성을 살린 창작 활동이 빛을 발합니다."},
            "사자자리": {"elem": "불 (Fire)", "planet": "태양 (Sun)", "color": "로열 골드", "time": "오후 12시 ~ 02시", "focus": "당신의 리더십과 카리스마가 돋보이는 날입니다. 자신감 있는 제안이 성사됩니다."},
            "처녀자리": {"elem": "흙 (Earth)", "planet": "수성 (Mercury)", "color": "올리브 카키", "time": "오전 09시 ~ 11시", "focus": "디테일한 업무 처리와 분석에서 독보적 성과를 냅니다. 컨디션 조절에 유의하세요."},
            "천칭자리": {"elem": "공기 (Air)", "planet": "금성 (Venus)", "color": "로즈 핑크", "time": "오후 04시 ~ 06시", "focus": "협상과 파트너십에서 최적의 균형을 찾습니다. 세련된 스타일링이 인기를 부릅니다."},
            "전갈자리": {"elem": "물 (Water)", "planet": "명왕성 (Pluto)", "color": "딥 버건디", "time": "밤 09시 ~ 11시", "focus": "깊은 직관과 통찰력이 빛을 발합니다. 비밀스러운 계획을 구체화하기에 길합니다."},
            "사수자리": {"elem": "불 (Fire)", "planet": "목성 (Jupiter)", "color": "네이비 블루", "time": "오후 02시 ~ 04시", "focus": "먼 곳에서의 반가운 소식이나 여행, 확장의 기운이 강합니다. 시야를 넓히세요."},
            "염소자리": {"elem": "흙 (Earth)", "planet": "토성 (Saturn)", "color": "차콜 그레이", "time": "오전 08시 ~ 10시", "focus": "오랜 시간 공들여온 일의 결실을 맺습니다. 성실함이 최고의 무기가 되는 날입니다."},
            "물병자리": {"elem": "공기 (Air)", "planet": "천왕성 (Uranus)", "color": "터콰이즈 민트", "time": "오후 03시 ~ 05시", "focus": "독창적인 아이디어와 네트워킹이 활성화됩니다. 상식을 깨는 발상이 성공을 엽니다."},
            "물고기자리": {"elem": "물 (Water)", "planet": "해왕성 (Neptune)", "color": "라벤더 퍼플", "time": "저녁 07시 ~ 09시", "focus": "공감 능력과 예술적 감각이 최고조입니다. 마음을 열고 진솔한 대화를 나누세요."}
        }
        meta = star_meta.get(key, star_meta["양자리"])
        return {
            "name": key,
            "score": rng.randint(88, 98),
            "title": f"{today.strftime('%m월 %d일')} 천체의 영감과 기운이 가득한 하루",
            "overview": "행성의 순행 기운이 당신의 별자리를 비추어 창의적 아이디어와 인간관계의 확장이 일어납니다.",
            "star_element": meta["elem"],
            "star_planet": meta["planet"],
            "lucky_color": meta["color"],
            "lucky_time": meta["time"],
            "focus_content": meta["focus"]
        }
    else:
        zodiac_years_map = {
            "쥐": ["2008년생 (만 18세)", "1996년생 (만 30세)", "1984년생 (만 42세)", "1972년생 (만 54세)", "1960년생 (만 66세)"],
            "소": ["2009년생 (만 17세)", "1997년생 (만 29세)", "1985년생 (만 41세)", "1973년생 (만 53세)", "1961년생 (만 65세)"],
            "호랑이": ["2010년생 (만 16세)", "1998년생 (만 28세)", "1986년생 (만 40세)", "1974년생 (만 52세)", "1962년생 (만 64세)"],
            "토끼": ["2011년생 (만 15세)", "1999년생 (만 27세)", "1987년생 (만 39세)", "1975년생 (만 51세)", "1963년생 (만 63세)"],
            "용": ["2000년생 (만 26세)", "1988년생 (만 38세)", "1976년생 (만 50세)", "1964년생 (만 62세)", "1952년생 (만 74세)"],
            "뱀": ["2001년생 (만 25세)", "1989년생 (만 37세)", "1977년생 (만 49세)", "1965년생 (만 61세)", "1953년생 (만 73세)"],
            "말": ["2002년생 (만 24세)", "1990년생 (만 36세)", "1978년생 (만 48세)", "1966년생 (만 60세)", "1954년생 (만 72세)"],
            "양": ["2003년생 (만 23세)", "1991년생 (만 35세)", "1979년생 (만 47세)", "1967년생 (만 59세)", "1955년생 (만 71세)"],
            "원숭이": ["2004년생 (만 22세)", "1992년생 (만 34세)", "1980년생 (만 46세)", "1968년생 (만 58세)", "1956년생 (만 70세)"],
            "닭": ["2005년생 (만 21세)", "1993년생 (만 33세)", "1981년생 (만 45세)", "1969년생 (만 57세)", "1957년생 (만 69세)"],
            "개": ["2006년생 (만 20세)", "1994년생 (만 32세)", "1982년생 (만 44세)", "1970년생 (만 56세)", "1958년생 (만 68세)"],
            "돼지": ["2007년생 (만 19세)", "1995년생 (만 31세)", "1983년생 (만 43세)", "1971년생 (만 55세)", "1959년생 (만 67세)"]
        }
        years = zodiac_years_map.get(key, zodiac_years_map["말"])
        tips = [
            {"year_label": years[0], "tip": "새로운 도전과 배움에서 큰 성취를 얻는 활기찬 하루입니다."},
            {"year_label": years[1], "tip": "적극적인 제안과 기획이 좋은 기회와 협력으로 이어집니다."},
            {"year_label": years[2], "tip": "작은 양보와 신뢰가 훗날 큰 이득과 결실로 돌아옵니다."},
            {"year_label": years[3], "tip": "주변의 조언을 수용하면 복잡한 문제가 순조롭게 풀립니다."},
            {"year_label": years[4], "tip": "마음의 여유를 가질 때 건강과 재물 안정이 함께 찾아옵니다."}
        ]
        return {
            "name": key,
            "score": rng.randint(86, 99),
            "title": f"{today.strftime('%m월 %d일')} 막힘없이 활짝 열리는 대길의 일진",
            "overview": "노력해 온 일들이 귀인을 만나 결실을 맺게 되는 뜻깊고 보람찬 하루입니다.",
            "lucky_time": "오전 10시 ~ 12시",
            "lucky_match": "찰떡궁합: 소띠, 양띠",
            "year_tips": tips
        }
