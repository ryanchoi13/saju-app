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

WADA_SANZO_PALETTES = {
    "wood": [
        {"palette_no": 48, "theme": "청록의 상생과 지혜", "mood_desc": "차분한 세이지 그린과 포그 블루가 만나 사주의 기운을 유연하고 맑게 정돈합니다.", "mode": "harmony", "style_mood": "casual", "mood_tag": "🏃 캐주얼 & 액티브", "top": {"name": "세이지 포레스트", "hex": "#4A6B5B", "standard_color": "그린"}, "bottom": {"name": "포그 블루", "hex": "#8CA6B5", "standard_color": "스카이블루"}, "point": None},
        {"palette_no": 114, "theme": "통관용신 · 벽갑인정", "mood_desc": "풍성한 목(木) 기운을 앤틱 버건디 소품으로 부드럽게 통관하여 추진력을 폭발시킵니다.", "mode": "reverse", "style_mood": "casual", "mood_tag": "✦ 시크릿 반전 데이", "top": {"name": "딥 틸 그린", "hex": "#2B4C47", "standard_color": "그린"}, "bottom": {"name": "페일 에크루", "hex": "#E3DAC9", "standard_color": "베이지"}, "point": {"name": "앤틱 보르도", "hex": "#7A2E3D", "standard_color": "와인/버건디"}}
    ],
    "fire": [
        {"palette_no": 72, "theme": "따스한 온기와 활력", "mood_desc": "은은한 코랄 브릭과 소프트 크림이 조화를 이루어 주변을 끌어당기는 카리스마를 만듭니다.", "mode": "harmony", "style_mood": "smart_casual", "mood_tag": "✨ 스마트 캐주얼", "top": {"name": "테라코타 앰버", "hex": "#C26D53", "standard_color": "코랄/오렌지"}, "bottom": {"name": "오이스터 화이트", "hex": "#F4F1EA", "standard_color": "화이트"}, "point": None},
        {"palette_no": 128, "theme": "수화기제(水火旣濟)", "mood_desc": "치솟는 화기를 차분한 미드나잇 인디고 소품으로 잡아주어 냉철한 판단력을 회복합니다.", "mode": "reverse", "style_mood": "formal", "mood_tag": "👔 클래식 & 포멀", "top": {"name": "소프트 웜 베이지", "hex": "#D8C7B5", "standard_color": "베이지"}, "bottom": {"name": "차콜 슬레이트", "hex": "#3A3D40", "standard_color": "차콜"}, "point": {"name": "미드나잇 네이비", "hex": "#1B2A47", "standard_color": "네이비"}}
    ],
    "earth": [
        {"palette_no": 91, "theme": "대지의 신뢰와 품격", "mood_desc": "묵직한 카멜 브라운과 오트밀 베이지가 만나 흔들리지 않는 신뢰와 포용력을 드러냅니다.", "mode": "harmony", "style_mood": "formal", "mood_tag": "👔 클래식 & 포멀", "top": {"name": "로즈우드 카멜", "hex": "#9E6B55", "standard_color": "카멜/브라운"}, "bottom": {"name": "오트밀 크림", "hex": "#EAE4D9", "standard_color": "아이보리/크림"}, "point": None}
    ],
    "metal": [
        {"palette_no": 84, "theme": "명경지수(明鏡止水) · 냉철함", "mood_desc": "깊은 미드나잇 인디고와 안개빛 스카이블루가 만나 사주의 금전운과 전문성을 견고히 세웁니다.", "mode": "harmony", "style_mood": "casual", "mood_tag": "🏃 캐주얼 & 액티브", "top": {"name": "미드나잇 인디고", "hex": "#1F3044", "standard_color": "네이비"}, "bottom": {"name": "포그 스카이", "hex": "#8CA6B5", "standard_color": "스카이블루"}, "point": None},
        {"palette_no": 105, "theme": "통관용신 · 조후 개운", "mood_desc": "사주 원국의 한기를 녹이기 위해 기본 의류 위에 앤틱 와인 소품을 얹어 재물의 숨통을 틔웁니다.", "mode": "reverse", "style_mood": "casual", "mood_tag": "✦ 시크릿 반전 데이", "top": {"name": "딥 프러시안", "hex": "#1A2A3A", "standard_color": "네이비"}, "bottom": {"name": "더스티 스카이", "hex": "#9CB2C0", "standard_color": "스카이블루"}, "point": {"name": "앤틱 보르도", "hex": "#7A2E3D", "standard_color": "와인/버건디"}}
    ],
    "water": [
        {"palette_no": 62, "theme": "유연한 교섭과 지혜", "mood_desc": "머스터드 옐로우와 차분한 베이지가 결합하여 차가운 기운을 녹이고 유연한 소통을 이끕니다.", "mode": "harmony", "style_mood": "smart_casual", "mood_tag": "✨ 스마트 캐주얼", "top": {"name": "앤틱 머스터드", "hex": "#C99700", "standard_color": "머스터드"}, "bottom": {"name": "소프트 샌드", "hex": "#D6C7B2", "standard_color": "베이지"}, "point": None}
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
        "day_gan": d_gan,
        "singang_label": "신강(身强) 사주" if dist[elem_map[d_gan]] >= 30 else "신약(身弱) 사주"
    }

def generate_saju_analysis_payload(name, gender, y, m, d, cal_type, sijin):
    saju_res = calculate_four_pillars(y, m, d, sijin)
    day_elem = saju_res["day_elem"]
    
    palettes = WADA_SANZO_PALETTES.get(day_elem, WADA_SANZO_PALETTES["metal"])
    chosen_palette = palettes[1] if len(palettes) > 1 and (d % 2 == 0) else palettes[0]
    is_reverse = (chosen_palette["mode"] == "reverse")
    
    today_ord = datetime.date.today().toordinal()
    theme_keys = ["wealth", "career", "love", "ward"]
    today_theme_key = theme_keys[(today_ord + y + m + d) % 4]
    talisman_info = AUTHENTIC_TALISMAN_MATRIX.get(day_elem, AUTHENTIC_TALISMAN_MATRIX["metal"]).get(today_theme_key)

    sijin_names = ["자시(子時)", "축시(丑時)", "인시(寅時)", "묘시(卯時)", "진시(辰時)", "사시(巳時)", "오시(午時)", "미시(未時)", "신시(申時)", "유시(酉時)", "술시(戌時)", "해시(亥時)"]
    sijin_str = sijin_names[sijin] if 0 <= sijin < 12 else "시간모름"

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
        "birth_summary": f"{y}년 {m}월 {d}일생 · {sijin_str}생",
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
            "pillars_detail": saju_res["pillars"],
            "elements": saju_res["elements"],
            "singang_label": saju_res["singang_label"]
        },
        "biorhythm": {
            "days_lived": (datetime.date.today() - datetime.date(y, m, d)).days,
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

# 사용자 사주 8글자 1:1 맞춤 풀버전 리포트 생성기
def build_detailed_report_content(report_key: str, user_dict: dict, sub_opt: str, p_name: str, relation: str):
    name = user_dict.get("name", "회원")
    y = user_dict.get("birth_year", 1978)
    m = user_dict.get("birth_month", 8)
    d = user_dict.get("birth_day", 13)
    sijin = user_dict.get("sijin_index", 5)
    age = 2026 - y + 1

    saju_data = calculate_four_pillars(y, m, d, sijin)
    p = saju_data["pillars"]
    day_gan = saju_data["day_gan"]
    day_elem = saju_data["day_elem"]
    singang = saju_data["singang_label"]
    elems = saju_data["elements"]

    elem_kr = {"wood": "목(木)", "fire": "화(火)", "earth": "토(土)", "metal": "금(金)", "water": "수(水)"}.get(day_elem, "금(金)")

    if report_key == "daewoon":
        return f"""
        <div style="display:flex; flex-direction:column; gap:16px; font-size:13.5px; line-height:1.85; color:#334155;">
            <div>
                <h4 style="font-size:15px; font-weight:800; color:#0F172A; margin-bottom:8px;">Chapter 1. {name}님의 사주 원국과 본원 분석</h4>
                <p>• 사주 본원: <strong>{p['year']['cg']}{p['year']['jj']}년 {p['month']['cg']}{p['month']['jj']}월 {p['day']['cg']}{p['day']['jj']}일 {p['hour']['cg']}{p['hour']['jj']}시</strong></p>
                <p>• {name}님은 천간의 <strong>{day_gan}({elem_kr})</strong> 일간으로 태어나 <strong>{singang}</strong>의 명조를 지녔습니다. 오행의 세력 중 금({elems['metal']}%)과 토({elems['earth']}%)의 조화가 뛰어나며, 강직한 원칙성과 섬세한 기획력을 평생의 큰 무기로 활용하는 명식입니다.</p>
            </div>
            <hr style="border:none; border-top:1px solid #E2E8F0;">
            <div>
                <h4 style="font-size:15px; font-weight:800; color:#0F172A; margin-bottom:8px;">Chapter 2. 생애 4대 대운의 주기적 흐름</h4>
                <p style="margin-bottom:6px;">• <strong>유년·청년기 (20~39세):</strong> 기반을 다지고 시련을 통해 실력을 쌓는 준비의 시기였습니다.</p>
                <p style="margin-bottom:6px; color:#047857; font-weight:800; background:#ECFDF5; padding:6px 10px; border-radius:6px;">• <strong>중장년 황금기 (40~59세) [현재 위치: {age}세]:</strong> 지금까지 축적한 지혜와 인맥이 결실을 맺는 인생 최대의 도약기입니다. 사주의 천을귀인이 작동하여 가장 큰 사회적 성취와 자산을 형성하는 핵심 황금기입니다.</p>
                <p style="margin-bottom:6px;">• <strong>노년 안락기 (60세 이후):</strong> 구축한 자산과 명예를 안정적으로 수성하며 평온을 누리는 결실의 시기입니다.</p>
            </div>
            <hr style="border:none; border-top:1px solid #E2E8F0;">
            <div>
                <h4 style="font-size:15px; font-weight:800; color:#0F172A; margin-bottom:8px;">Chapter 3. 평생 대운 성공 처세와 개운 비결</h4>
                <p>40대 후반에서 50대 초반으로 이어지는 대운의 변곡점에서는 무리한 확장보다 본업의 전문성을 극대화하고 신뢰 기반의 협력 체계를 공고히 할 때 평생의 부와 안정이 온전히 유지됩니다.</p>
            </div>
        </div>
        """
    elif report_key == "sinnian":
        return f"""
        <div style="display:flex; flex-direction:column; gap:16px; font-size:13.5px; line-height:1.85; color:#334155;">
            <div>
                <h4 style="font-size:15px; font-weight:800; color:#166534; margin-bottom:8px;">Chapter 1. 2026 丙午년 총운 심층 분석 (재물·애정·건강 종합)</h4>
                <p style="margin-bottom:10px;"><strong>[전체 총평]</strong> 2026년 붉은 말의 해(丙午年)는 솟구치는 양기와 결실의 에너지가 공존하는 역동적인 해입니다. 귀하의 일간 {day_gan}({elem_kr})과 병오년의 불꽃 같은 에너지가 상생 구도를 형성하여 정체되었던 자산과 사업의 흐름이 시원하게 뚫리게 됩니다.</p>
                <p style="margin-bottom:10px;"><strong>[💰 재물 & 직업운]</strong> 새로운 프로젝트나 자산 확장에 매우 유리한 기운이 작용합니다. 상반기에 뿌려둔 노력과 제안들이 하반기(음력 8월~10월)에 가시적인 수익과 실적으로 돌아오며, 특히 직장 내 승진이나 사업적 계약에서 우위를 점하게 됩니다.</p>
                <p style="margin-bottom:10px;"><strong>[💖 애정 & 대인관계운]</strong> 도화(桃花)와 귀인의 기운이 동시에 빛을 발합니다. 싱글의 경우 사회적 모임이나 업무적 교류 속에서 품격 있는 인연을 만날 기회가 열리며, 기혼/연인의 경우 오랜 오해를 풀고 깊은 신뢰와 유대감을 회복하는 전환점이 됩니다.</p>
                <p style="margin-bottom:10px;"><strong>[🌿 건강 & 심신 밸런스]</strong> 화(火) 기운이 왕성한 해인 만큼 심혈관계와 과로로 인한 피로 누적을 경계해야 합니다. 물(水)을 자주 섭취하고 차분한 명상과 가벼운 유산소 운동으로 조후의 균형을 맞추는 것이 건강 개운의 핵심입니다.</p>
            </div>
            <hr style="border:none; border-top:1px solid #E2E8F0;">
            <div>
                <h4 style="font-size:15px; font-weight:800; color:#166534; margin-bottom:10px;">Chapter 2. 2026 하반기 월별 정밀 가이드</h4>
                <p style="margin-bottom:8px;"><strong>7월:</strong> 주변의 의견이 분분해지는 시기입니다. 중심을 지키고 내실을 다지세요.</p>
                <hr style="border:none; border-top:1px dashed #E2E8F0; margin:6px 0;">
                <p style="margin-bottom:8px; color:#047857; font-weight:700;"><strong>8월 [★ 황금의 달]:</strong> 계약, 승진, 자산 증식에서 가장 큰 성과가 터지는 절정기입니다.</p>
                <hr style="border:none; border-top:1px dashed #E2E8F0; margin:6px 0;">
                <p style="margin-bottom:8px;"><strong>9월:</strong> 귀인의 조력으로 새로운 협력 기회가 생깁니다. 유연하게 교섭하세요.</p>
                <hr style="border:none; border-top:1px dashed #E2E8F0; margin:6px 0;">
                <p style="margin-bottom:8px; color:#047857; font-weight:700;"><strong>10월 [★ 결실의 달]:</strong> 투자와 시험, 자격증 취득 등 노력했던 일의 결실을 쟁취합니다.</p>
                <hr style="border:none; border-top:1px dashed #E2E8F0; margin:6px 0;">
                <p style="margin-bottom:8px;"><strong>11월:</strong> 건강 관리에 유의하며 무리한 지출이나 투자를 차분히 정리하는 달입니다.</p>
                <hr style="border:none; border-top:1px dashed #E2E8F0; margin:6px 0;">
                <p style="margin-bottom:8px;"><strong>12월:</strong> 한 해를 정리하고 2027년의 새로운 도약을 준비하는 안정과 화합의 달입니다.</p>
            </div>
        </div>
        """
    elif report_key == "wealth":
        return f"""
        <div style="display:flex; flex-direction:column; gap:16px; font-size:13.5px; line-height:1.85; color:#334155;">
            <div>
                <h4 style="font-size:15px; font-weight:800; color:#0F172A; margin-bottom:8px;">Chapter 1. {name}님의 타고난 재물 그릇과 금고(金庫) 분석</h4>
                <p>• {name}님의 사주는 <strong>{elem_kr}</strong> 본원으로 토(土) 인성과 금(金) 비견이 든든하게 받쳐주고 있어, 돈을 버는 능력뿐만 아니라 자산을 모으고 지키는 <strong>수성(守成)의 기운</strong>이 대단히 강한 부자 사주입니다.</p>
                <p>• 평생 자산 형성의 핵심 통로는 <strong>안정적 부동산 자산</strong>과 <strong>전문 기술/기획 기반의 사업적 실적</strong>입니다.</p>
            </div>
            <hr style="border:none; border-top:1px solid #E2E8F0;">
            <div>
                <h4 style="font-size:15px; font-weight:800; color:#0F172A; margin-bottom:8px;">Chapter 2. 투자 성공 전략 및 주의점</h4>
                <p>• 유망 투자처: 문서와 토지, 안정적인 배당형 자산 및 브랜드 가치가 있는 실물 자산</p>
                <p>• 재물 개운 팁: 지갑이나 업무 공간에 <strong>골드, 네이비, 차콜</strong> 계열의 소품을 배치하여 금전의 유출을 막고 신뢰를 높이세요.</p>
            </div>
        </div>
        """
    elif report_key == "love":
        return f"""
        <div style="display:flex; flex-direction:column; gap:16px; font-size:13.5px; line-height:1.85; color:#334155;">
            <div>
                <h4 style="font-size:15px; font-weight:800; color:#9F1239; margin-bottom:8px;">Chapter 1. {name}님의 평생 애정 성향 ({sub_opt})</h4>
                <p>• 사주 일간 {day_gan}({elem_kr})의 특성상 겉으로는 신중하고 과묵해 보이지만, 내면에는 한 사람에게 깊은 헌신과 온정을 쏟는 진중한 로맨티스트의 기질을 품고 있습니다.</p>
                <p>• 현재 <strong>[{sub_opt}]</strong> 상태에서 가장 필요한 것은 상대방에게 마음을 솔직하고 따뜻하게 표현하는 유연한 소통입니다.</p>
            </div>
            <hr style="border:none; border-top:1px solid #E2E8F0;">
            <div>
                <h4 style="font-size:15px; font-weight:800; color:#9F1239; margin-bottom:8px;">Chapter 2. 가장 잘 맞는 천생연분의 특징</h4>
                <p>• 나와 상생을 이루는 상대: 온화한 이해심을 지닌 <strong>수(水) 기운 또는 목(木) 기운</strong>의 상대</p>
                <p>• 애정운 극대화 개운법: 은은한 파스텔 핑크나 세련된 실버 주얼리로 따스하고 품격 있는 무드를 연출하세요.</p>
            </div>
        </div>
        """
    elif report_key == "business":
        return f"""
        <div style="display:flex; flex-direction:column; gap:16px; font-size:13.5px; line-height:1.85; color:#334155;">
            <div>
                <h4 style="font-size:15px; font-weight:800; color:#0F172A; margin-bottom:8px;">Chapter 1. {name}님의 타고난 직업적 천직과 리더십 ({sub_opt})</h4>
                <p>• 귀하의 사주는 조직을 안정적으로 이끌고 시스템을 구축하는 <strong>관리 및 전략 기획형 천직</strong>에 최적화되어 있습니다.</p>
                <p>• 현재 <strong>[{sub_opt}]</strong> 영역에서 경쟁자들을 압도할 수 있는 무기는 남들보다 한발 앞선 디테일한 분석력과 신뢰입니다.</p>
            </div>
            <hr style="border:none; border-top:1px solid #E2E8F0;">
            <div>
                <h4 style="font-size:15px; font-weight:800; color:#0F172A; margin-bottom:8px;">Chapter 2. 승진 및 사업 성공 로드맵</h4>
                <p>• 최적의 업무 파트너: 빠른 실행력을 지닌 동료와 협업할 때 시너지가 극대화됩니다.</p>
                <p>• 비즈니스 개운법: 단정한 포멀 룩과 네이비/블루 타이/시계를 매치하여 프로페셔널한 신뢰감을 구축하세요.</p>
            </div>
        </div>
        """
    elif report_key == "health":
        return f"""
        <div style="display:flex; flex-direction:column; gap:16px; font-size:13.5px; line-height:1.85; color:#334155;">
            <div>
                <h4 style="font-size:15px; font-weight:800; color:#047857; margin-bottom:8px;">Chapter 1. 사주 오행 기반 취약 장기 및 체질 분석</h4>
                <p>• 오행 분포 결과: <strong>금({elems['metal']}%), 토({elems['earth']}%), 화({elems['fire']}%)</strong>의 기운이 왕성하고 수(水)/목(木)의 보충이 필요한 사주입니다.</p>
                <p>• 주의해야 할 신체 부위: 기관지 및 호흡기계, 과도한 신경성 스트레스로 인한 소화기 부담에 유의해야 합니다.</p>
            </div>
            <hr style="border:none; border-top:1px solid #E2E8F0;">
            <div>
                <h4 style="font-size:15px; font-weight:800; color:#047857; margin-bottom:8px;">Chapter 2. 평생 맞춤 오행 치유 섭생법</h4>
                <p>• 추천 음식: 따뜻한 수분을 보충해주는 영양 솥밥, 맑은 차, 푸른 채소와 버섯류</p>
                <p>• 일상 운동법: 과격한 운동보다는 척추를 바로세우고 폐활량을 늘리는 유산소 걷기와 요가/스트레칭이 최고입니다.</p>
            </div>
        </div>
        """
    elif report_key == "gunghap":
        return f"""
        <div style="display:flex; flex-direction:column; gap:16px; font-size:13.5px; line-height:1.85; color:#334155;">
            <div>
                <h4 style="font-size:15px; font-weight:800; color:#9F1239; margin-bottom:8px;">Chapter 1. {name}님과 {p_name}님의 오행 상생 밸런스</h4>
                <p>• 두 사람의 관계 유형: <strong>[{relation}]</strong></p>
                <p>• {name}님의 {elem_kr} 기운과 {p_name}님의 본원 기운이 만나 서로의 결핍을 완벽히 보완해주는 <strong>음양화합(陰陽和合)의 대길 궁합</strong>입니다.</p>
            </div>
            <hr style="border:none; border-top:1px solid #E2E8F0;">
            <div>
                <h4 style="font-size:15px; font-weight:800; color:#9F1239; margin-bottom:8px;">Chapter 2. 두 사람의 장기적 관계 유지 비결</h4>
                <p>• {name}님의 확고한 추진력과 {p_name}님의 섬세한 배려가 결합할 때 금전과 화합이 배가됩니다. 서로의 자존심을 세워주는 대화법을 유지할 때 평생의 든든한 동반자가 됩니다.</p>
            </div>
        </div>
        """
    else:
        return f"<p>{name}님을 위한 정밀 사주 분석 감명서입니다.</p>"

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
        "sinnian": "📅 2026 丙午년 신년 총운 & 하반기 월별 토정비결",
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
    return {
        "name": "I. THE MAGICIAN (마법사)",
        "keyword": "창조적 잠재력 · 탁월한 실행력",
        "symbolism": "4대 원소를 능숙히 다루는 마법사는 무한한 가능성과 시작을 의미합니다.",
        "reading_male": "주도적으로 프로젝트나 만남을 이끌어가기에 완벽한 시기입니다.",
        "reading_female": "빛나는 센스와 아이디어로 주변의 시선과 협력을 끌어당깁니다.",
        "action_guide": "망설이던 아이디어가 있다면 오늘 바로 구체적인 실행 계획을 작성하세요."
    }

# 12간지 띠별 고유 데이터 DB
ZODIAC_CUSTOM_DB = {
    "쥐": {"score": 92, "title": "물 흐르듯 순조로운 지혜의 날", "overview": "막혔던 아이디어가 샘솟고 주변의 협력을 얻어 순풍을 타는 하루입니다.", "time": "오전 09시 ~ 11시", "match": "소띠, 용띠", "years": ["2008년생 (만 18세)", "1996년생 (만 30세)", "1984년생 (만 42세)", "1972년생 (만 54세)", "1960년생 (만 66세)"], "tips": ["학업과 새로운 취미에서 뛰어난 성취를 얻습니다.", "적극적인 의견 개진이 승진과 이직에 길합니다.", "작은 양보가 훗날 큰 재물로 돌아옵니다.", "문서 계약과 투자에서 실리를 챙기는 날입니다.", "가정에 경사가 생기고 마음이 평안합니다."]},
    "소": {"score": 95, "title": "묵묵한 노력이 큰 결실을 맺는 날", "overview": "성실하게 준비해 온 일들이 귀인을 만나 확실한 보상으로 이어집니다.", "time": "오후 01시 ~ 03시", "match": "쥐띠, 뱀띠", "years": ["2009년생 (만 17세)", "1997년생 (만 29세)", "1985년생 (만 41세)", "1973년생 (만 53세)", "1961년생 (만 65세)"], "tips": ["차분한 집중력이 시험 합격을 이끕니다.", "성실한 태도로 상사의 깊은 신뢰를 얻습니다.", "부동산 및 자산 축적에 청신호가 켜집니다.", "주변 사람들과의 협력이 큰 힘이 됩니다.", "건강이 회복되고 마음의 여유가 생깁니다."]},
    "호랑이": {"score": 89, "title": "당당한 용기와 리더십이 빛나는 날", "overview": "망설이지 않고 첫발을 내딛을 때 강력한 추진력으로 난관을 돌파합니다.", "time": "오전 07시 ~ 09시", "match": "말띠, 개띠", "years": ["2010년생 (만 16세)", "1998년생 (만 28세)", "1986년생 (만 40세)", "1974년생 (만 52세)", "1962년생 (만 64세)"], "tips": ["친구들과의 협업에서 주도적 역할을 합니다.", "도전적인 프로젝트에서 성과를 냅니다.", "과감한 투자 결단이 이득을 가져옵니다.", "사업적 영역을 확장하기에 최적의 시기입니다.", "가벼운 운동으로 활력을 유지하세요."]},
    "토끼": {"score": 94, "title": "섬세한 감각과 귀인의 조력이 따르는 날", "overview": "부드러운 소통과 유연한 처세로 주변 사람들의 마음을 사로잡습니다.", "time": "오전 10시 ~ 12시", "match": "양띠, 돼지띠", "years": ["2011년생 (만 15세)", "1999년생 (만 27세)", "1987년생 (만 39세)", "1975년생 (만 51세)", "1963년생 (만 63세)"], "tips": ["예술적 감각과 창의력이 최고조에 달합니다.", "소개팅이나 새로운 만남에서 인연을 만납니다.", "재정적 안정을 도모하기에 매우 길합니다.", "가족과의 대화에서 큰 위로와 해답을 찾습니다.", "산책과 휴식으로 내면의 평온을 누리세요."]},
    "용": {"score": 97, "title": "하늘로 비상하는 승천의 대길 일진", "overview": "오랫동안 염원하던 소망이 이루어지고 큰 명예를 얻는 최고의 하루입니다.", "time": "오후 02시 ~ 04시", "match": "원숭이띠, 닭띠", "years": ["2000년생 (만 26세)", "1988년생 (만 38세)", "1976년생 (만 50세)", "1964년생 (만 62세)", "1952년생 (만 74세)"], "tips": ["원하는 시험이나 자격증에서 쾌거를 거둡니다.", "자신의 분야에서 독보적 존재감을 드러냅니다.", "큰 규모의 계약이나 승진이 성사됩니다.", "자산 증식의 절호의 기회를 맞이합니다.", "주변 사람들의 존경과 축하를 받습니다."]},
    "뱀": {"score": 91, "title": "예리한 통찰과 직관이 승리를 이끄는 날", "overview": "복잡한 문제의 핵심을 꿰뚫어 보고 유리한 고지를 점하게 됩니다.", "time": "오전 09시 ~ 11시", "match": "소띠, 닭띠", "years": ["2001년생 (만 25세)", "1989년생 (만 37세)", "1977년생 (만 49세)", "1965년생 (만 61세)", "1953년생 (만 73세)"], "tips": ["깊이 있는 탐구와 학습이 빛을 봅니다.", "전략적인 기획안이 상사의 인정을 받습니다.", "숨은 알짜배기 투자처를 발견하게 됩니다.", "침착한 대처로 위기를 기회로 바꿉니다.", "건강 검진과 영양 관리에 신경 쓰세요."]},
    "말": {"score": 95, "title": "막힘없이 활짝 열리는 대도약의 하루", "overview": "역동적인 활동력으로 어디를 가나 환영받고 실리를 거머쥐게 됩니다.", "time": "오전 11시 ~ 오후 01시", "match": "호랑이띠, 양띠", "years": ["2002년생 (만 24세)", "1990년생 (만 36세)", "1978년생 (만 48세)", "1966년생 (만 60세)", "1954년생 (만 72세)"], "tips": ["새로운 도전과 배움에서 큰 성취를 얻습니다.", "적극적인 제안과 기획이 좋은 기회를 엽니다.", "작은 양보와 신뢰가 훗날 큰 이득으로 돌아옵니다.", "주변의 조언을 수용하면 순풍을 탑니다.", "마음의 여유를 가질 때 건강과 안정이 옵니다."]},
    "양": {"score": 93, "title": "평화로운 화합과 따스한 정이 넘치는 날", "overview": "서먹했던 관계가 풀리고 주변의 따뜻한 배려와 사랑을 느끼는 하루입니다.", "time": "오후 01시 ~ 03시", "match": "토끼띠, 돼지띠", "years": ["2003년생 (만 23세)", "1991년생 (만 35세)", "1979년생 (만 47세)", "1967년생 (만 59세)", "1955년생 (만 71세)"], "tips": ["진솔한 대화가 깊은 우정으로 이어집니다.", "팀워크를 발휘하여 공동의 목표를 이룹니다.", "안정적인 자산 관리로 실속을 챙깁니다.", "가족의 화목이 만사의 근원이 됩니다.", "편안한 수면과 휴식으로 기력을 회복하세요."]},
    "원숭이": {"score": 96, "title": "빛나는 재치와 센스로 기회를 낚는 날", "overview": "뛰어난 순발력으로 어려운 상황을 반전시키고 금전운을 쟁취합니다.", "time": "오후 03시 ~ 05시", "match": "쥐띠, 용띠", "years": ["2004년생 (만 22세)", "1992년생 (만 34세)", "1980년생 (만 46세)", "1968년생 (만 58세)", "1956년생 (만 70세)"], "tips": ["반짝이는 아이디어가 공모전이나 시험에 길합니다.", "영업과 미팅에서 최고의 성과를 도출합니다.", "단기 투자 및 재테크에서 수익이 발생합니다.", "유연한 대처로 경쟁 상대를 압도합니다.", "취미 생활을 통해 활력을 재충전하세요."]},
    "닭": {"score": 90, "title": "정확한 판단력과 명확한 결실의 하루", "overview": "흐트러진 일들을 깔끔하게 정리하고 확실한 성과를 인정받습니다.", "time": "오후 05시 ~ 07시", "match": "소띠, 뱀띠", "years": ["2005년생 (만 21세)", "1993년생 (만 33세)", "1981년생 (만 45세)", "1969년생 (만 57세)", "1957년생 (만 69세)"], "tips": ["꼼꼼한 준비가 완벽한 결과를 보장합니다.", "전문성을 인정받아 중요한 책임을 맡습니다.", "가계부와 자산을 정돈하여 지출을 줄입니다.", "명예와 신뢰가 한 단계 격상됩니다.", "충분한 수분 섭취로 컨디션을 조절하세요."]},
    "개": {"score": 93, "title": "신뢰와 의리로 귀인의 큰 도움을 받는 날", "overview": "한결같은 진심이 상대방을 감동시켜 든든한 조력자를 얻게 됩니다.", "time": "저녁 07시 ~ 09시", "match": "호랑이띠, 말띠", "years": ["2006년생 (만 20세)", "1994년생 (만 32세)", "1982년생 (만 44세)", "1970년생 (만 56세)", "1958년생 (만 68세)"], "tips": ["진심 어린 조언이 친구에게 큰 힘이 됩니다.", "직장 동료들과의 유대가 깊어집니다.", "장기적인 자산 투자에 유리한 정보를 얻습니다.", "신뢰를 바탕으로 한 계약이 체결됩니다.", "마음이 통하는 사람과 편안한 식사를 하세요."]},
    "돼지": {"score": 94, "title": "풍요로운 복록과 여유가 넘치는 날", "overview": "노력한 것 이상의 복과 보상이 따르며 마음이 풍요로운 하루입니다.", "time": "밤 09시 ~ 11시", "match": "토끼띠, 양띠", "years": ["2007년생 (만 19세)", "1995년생 (만 31세)", "1983년생 (만 43세)", "1971년생 (만 55세)", "1959년생 (만 67세)"], "tips": ["새로운 배움의 기회가 풍성하게 열립니다.", "노력에 대한 가시적 보상과 인센티브를 얻습니다.", "의외의 횡재수나 선물이 들어옵니다.", "사업의 결실을 풍요롭게 수확하는 날입니다.", "가족과 함께하는 시간이 큰 행복을 줍니다."]}
}

# 12성좌 별자리 고유 점성술 DB
STAR_CUSTOM_DB = {
    "양자리": {"elem": "불 (Fire)", "planet": "화성 (Mars)", "color": "루비 레드", "time": "오전 07시 ~ 09시", "focus": "새로운 기획에 도전할 때 주변의 강력한 지지를 받습니다. 솔직한 표현이 당신의 매력을 한층 돋보이게 합니다."},
    "황소자리": {"elem": "흙 (Earth)", "planet": "금성 (Venus)", "color": "에메랄드 그린", "time": "오후 01시 ~ 03시", "focus": "재정적 안정을 도모하기에 최적입니다. 미식이나 예술적 힐링을 즐길 때 예상치 못한 행운이 찾아옵니다."},
    "쌍둥이자리": {"elem": "공기 (Air)", "planet": "수성 (Mercury)", "color": "스카이 블루", "time": "오전 10시 ~ 12시", "focus": "활발한 정보 교류와 소통이 큰 성과로 이어집니다. 가벼운 안부 연락이 귀인과의 만남으로 발전합니다."},
    "게자리": {"elem": "물 (Water)", "planet": "달 (Moon)", "color": "실버 화이트", "time": "저녁 08시 ~ 10시", "focus": "가족과 연인에게서 따스한 위로와 신뢰를 얻습니다. 감성을 살린 창작 활동이 빛을 발하는 날입니다."},
    "사자자리": {"elem": "불 (Fire)", "planet": "태양 (Sun)", "color": "로열 골드", "time": "오후 12시 ~ 02시", "focus": "당신의 리더십과 카리스마가 돋보입니다. 중요한 프레젠테이션이나 제안에서 최상의 결과를 냅니다."},
    "처녀자리": {"elem": "흙 (Earth)", "planet": "수성 (Mercury)", "color": "올리브 카키", "time": "오전 09시 ~ 11시", "focus": "디테일한 업무 처리와 체계적 분석에서 독보적 성과를 냅니다. 충분한 휴식으로 컨디션을 조절하세요."},
    "천칭자리": {"elem": "공기 (Air)", "planet": "금성 (Venus)", "color": "로즈 핑크", "time": "오후 04시 ~ 06시", "focus": "협상과 파트너십에서 완벽한 균형을 찾습니다. 세련된 스타일링이 당신의 인기를 크게 높여줍니다."},
    "전갈자리": {"elem": "물 (Water)", "planet": "명왕성 (Pluto)", "color": "딥 버건디", "time": "밤 09시 ~ 11시", "focus": "깊은 직관과 통찰력이 빛을 발합니다. 중요한 비밀 계획을 구체화하거나 자금을 정돈하기에 길합니다."},
    "사수자리": {"elem": "불 (Fire)", "planet": "목성 (Jupiter)", "color": "네이비 블루", "time": "오후 02시 ~ 04시", "focus": "먼 곳에서의 반가운 소식이나 여행, 지적 확장의 기운이 강합니다. 시야를 넓히고 과감히 도전하세요."},
    "염소자리": {"elem": "흙 (Earth)", "planet": "토성 (Saturn)", "color": "차콜 그레이", "time": "오전 08시 ~ 10시", "focus": "오랜 시간 공들여온 일의 결실을 맺습니다. 당신의 묵직한 성실함이 최고의 무기가 되는 하루입니다."},
    "물병자리": {"elem": "공기 (Air)", "planet": "천왕성 (Uranus)", "color": "터콰이즈 민트", "time": "오후 03시 ~ 05시", "focus": "독창적인 아이디어와 네트워킹이 활성화됩니다. 기존 상식을 깨는 참신한 발상이 성공의 문을 엽니다."},
    "물고기자리": {"elem": "물 (Water)", "planet": "해왕성 (Neptune)", "color": "라벤더 퍼플", "time": "저녁 07시 ~ 09시", "focus": "공감 능력과 예술적 감각이 최고조에 달합니다. 마음을 열고 진솔한 대화를 나눌 때 인연이 깊어집니다."}
}

@app.get("/api/zodiac-fortune")
def get_zodiac_fortune(type: str, key: str):
    if type == "star":
        meta = STAR_CUSTOM_DB.get(key, STAR_CUSTOM_DB["양자리"])
        return {
            "name": key,
            "score": 93,
            "title": "천체의 조화와 영감이 가득한 하루",
            "overview": "행성의 순행 기운이 당신의 별자리를 비추어 창의적 아이디어와 인간관계의 확장이 활발히 일어납니다.",
            "star_element": meta["elem"],
            "star_planet": meta["planet"],
            "lucky_color": meta["color"],
            "lucky_time": meta["time"],
            "focus_content": meta["focus"]
        }
    else:
        meta = ZODIAC_CUSTOM_DB.get(key, ZODIAC_CUSTOM_DB["말"])
        tips = [{"year_label": meta["years"][i], "tip": meta["tips"][i]} for i in range(5)]
        return {
            "name": key,
            "score": meta["score"],
            "title": meta["title"],
            "overview": meta["overview"],
            "lucky_time": meta["time"],
            "lucky_match": f"찰떡궁합: {meta['match']}",
            "year_tips": tips
        }
