import datetime
import math
import os
import random
import sqlite3
from typing import Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, Response
from pydantic import BaseModel

app = FastAPI(title="달하 (DALHA) - 정통 명리학 & 점성술 엔진", version="43.0.0")

# --- SQLite 데이터베이스 초기화 ---
DB_FILE = "dalha.db"

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    # 사용자 테이블
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kakao_id VARCHAR(50) UNIQUE,
        name VARCHAR(50),
        gender VARCHAR(10),
        birth_year INTEGER,
        birth_month INTEGER,
        birth_day INTEGER,
        calendar_type VARCHAR(10),
        sijin_index INTEGER,
        coin_balance INTEGER DEFAULT 1000,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    # 유료 구매 감명서 보관함 테이블
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS unlocked_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        report_key VARCHAR(50),
        report_title VARCHAR(100),
        report_content TEXT,
        created_at DATE,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    conn.commit()
    conn.close()

init_db()

# --- 정통 명리학 상수 및 맵핑 데이터 ---
CHEONGAN_HANJA = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
JIJI_HANJA = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
YANG_STEMS = ["甲", "丙", "戊", "庚", "壬"]

CHEONGAN_ELEMENTS = {
    "甲": "wood", "乙": "wood", "丙": "fire", "丁": "fire", "戊": "earth",
    "己": "earth", "庚": "metal", "辛": "metal", "壬": "water", "癸": "water"
}
JIJI_ELEMENTS = {
    "子": "water", "丑": "earth", "寅": "wood", "卯": "wood", "辰": "earth",
    "巳": "fire", "午": "fire", "未": "earth", "申": "metal", "酉": "metal",
    "戌": "earth", "亥": "water"
}

SIJIN_KOREAN_MAP = {
    -1: "시간 모름", 0: "자시(子時)", 1: "축시(丑時)", 2: "인시(寅時)",
    3: "묘시(卯時)", 4: "진시(辰時)", 5: "사시(巳時)", 6: "오시(午時)",
    7: "미시(未時)", 8: "신시(申時)", 9: "유시(酉時)", 10: "술시(戌時)", 11: "해시(亥時)"
}

JIJANGGAN_FULL_MAP = {
    "子": [{"char": "壬", "elem": "water", "weight": 10}, {"char": "癸", "elem": "water", "weight": 20}],
    "丑": [{"char": "癸", "elem": "water", "weight": 9}, {"char": "辛", "elem": "metal", "weight": 3}, {"char": "己", "elem": "earth", "weight": 18}],
    "寅": [{"char": "戊", "elem": "earth", "weight": 7}, {"char": "丙", "elem": "fire", "weight": 7}, {"char": "甲", "elem": "wood", "weight": 16}],
    "卯": [{"char": "甲", "elem": "wood", "weight": 10}, {"char": "乙", "elem": "wood", "weight": 20}],
    "辰": [{"char": "乙", "elem": "wood", "weight": 9}, {"char": "癸", "elem": "water", "weight": 3}, {"char": "戊", "elem": "earth", "weight": 18}],
    "巳": [{"char": "戊", "elem": "earth", "weight": 7}, {"char": "庚", "elem": "metal", "weight": 7}, {"char": "丙", "elem": "fire", "weight": 16}],
    "午": [{"char": "丙", "elem": "fire", "weight": 10}, {"char": "己", "elem": "earth", "weight": 9}, {"char": "丁", "elem": "fire", "weight": 11}],
    "未": [{"char": "丁", "elem": "fire", "weight": 9}, {"char": "乙", "elem": "wood", "weight": 3}, {"char": "己", "elem": "earth", "weight": 18}],
    "申": [{"char": "戊", "elem": "earth", "weight": 7}, {"char": "壬", "elem": "water", "weight": 7}, {"char": "庚", "elem": "metal", "weight": 16}],
    "酉": [{"char": "庚", "elem": "metal", "weight": 10}, {"char": "辛", "elem": "metal", "weight": 20}],
    "戌": [{"char": "辛", "elem": "metal", "weight": 9}, {"char": "丁", "elem": "fire", "weight": 3}, {"char": "戊", "elem": "earth", "weight": 18}],
    "亥": [{"char": "戊", "elem": "earth", "weight": 7}, {"char": "甲", "elem": "wood", "weight": 7}, {"char": "壬", "elem": "water", "weight": 16}]
}

ANIMAL_MAP = {"子": "쥐", "丑": "소", "寅": "호랑이", "卯": "토끼", "辰": "용", "巳": "뱀", "午": "말", "未": "양", "申": "원숭이", "酉": "닭", "戌": "개", "亥": "돼지"}
ANIMAL_ICONS = {"쥐": "🐭", "소": "🐮", "호랑이": "🐯", "토끼": "🐰", "용": "🐲", "뱀": "🐍", "말": "🐴", "양": "🐑", "원숭이": "🐵", "닭": "🐔", "개": "🐶", "돼지": "🐷"}

STAR_SIGNS = [
    {"name": "물병자리", "icon": "♒", "period": "01.20 ~ 02.18"}, {"name": "물고기자리", "icon": "♓", "period": "02.19 ~ 03.20"},
    {"name": "양자리", "icon": "♈", "period": "03.21 ~ 04.19"}, {"name": "황소자리", "icon": "♉", "period": "04.20 ~ 05.20"},
    {"name": "쌍둥이자리", "icon": "♊", "period": "05.21 ~ 06.21"}, {"name": "게자리", "icon": "♋", "period": "06.22 ~ 07.22"},
    {"name": "사자자리", "icon": "♌", "period": "07.23 ~ 08.22"}, {"name": "처녀자리", "icon": "♍", "period": "08.23 ~ 09.22"},
    {"name": "천칭자리", "icon": "♎", "period": "09.23 ~ 10.22"}, {"name": "전갈자리", "icon": "♏", "period": "10.23 ~ 11.22"},
    {"name": "사수자리", "icon": "♐", "period": "11.23 ~ 12.21"}, {"name": "염소자리", "icon": "♑", "period": "12.22 ~ 01.19"}
]

TALISMAN_OHEANG_MAP = {
    "wood": { "type": "wood", "title": "사업대성부 (事業亨通符)", "power": "추진력 강화 · 사업 번창 · 승진운", "desc": "사주에 부족한 木(목)의 생명력과 추진력을 불어넣어 막힌 활로를 뚫고 주도권을 쥐게 하는 비급 부적입니다." },
    "fire": { "type": "fire", "title": "소원성취부 (心想事成符)", "power": "열정 회복 · 명예 상승 · 소원 성취", "desc": "사주에 부족한 火(화)의 찬란한 빛을 밝혀 어둠을 몰아내고 염원하던 소망을 일사천리로 성취시키는 부적입니다." },
    "earth": { "type": "earth", "title": "금고수호부 (金庫安穩符)", "power": "자산 방어 · 누수 차단 · 재물 안착", "desc": "사주에 부족한 土(토)의 단단한 대지를 마련하여 헛돈 지출을 막고 평생 모은 자산을 철벽처럼 지켜주는 부적입니다." },
    "metal": { "type": "metal", "title": "재물만복부 (萬福大吉符)", "power": "재물 증식 · 금전운 대통 · 투자 대박", "desc": "사주에 부족한 金(금)의 황금 기운을 채워 사방에서 금전과 복록이 쏟아지게 하는 전통 비급 부적입니다." },
    "water": { "type": "water", "title": "천생화합부 (萬事和合符)", "power": "인연 결속 · 애정 화합 · 귀인 유대", "desc": "사주에 부족한 水(수)의 지혜와 유대감을 채워 엇갈린 인연을 단단히 묶어주고 귀인의 조력을 이끄는 부적입니다." }
}

TAROT_CARDS = [
    {
        "name": "0. THE FOOL (바보)", "keyword": "새로운 여정의 서막 · 순수한 직관 · 무한한 잠재력",
        "symbolism": "화려한 옷을 입고 벼랑 끝에서 발걸음을 내딛는 청년과 곁의 흰 개, 찬란한 태양은 과거의 관습과 두려움을 벗어던진 순수한 영혼의 새로운 도약을 상징합니다.",
        "reading_male": "오랫동안 망설이던 프로젝트나 신규 투자의 첫 단추를 꿰기에 최상의 날입니다. 주변의 간섭보다 본인의 결단력을 믿고 추진하세요.",
        "reading_female": "새로운 인연이나 오랫동안 염원하던 소망에 뜻밖의 기회가 찾아옵니다. 계산적인 생각보다 첫 느낌을 따를 때 대길합니다.",
        "action_guide": "새로운 제안이 들어오면 편견 없이 경청하고, 떠오르는 창의적인 아이디어를 즉시 메모하세요."
    },
    {
        "name": "I. THE MAGICIAN (마법사)", "keyword": "탁월한 창조력 · 완벽한 주도권 · 만사형통",
        "symbolism": "머리 위의 무한대 기호와 제단 위의 4대 원소는 모든 상황을 내 뜻대로 통제하고 현실로 구현할 수 있는 완성된 지혜와 전문성을 뜻합니다.",
        "reading_male": "전문 역량과 논리적인 언변이 빛을 발합니다. 중요한 회의나 계약 협상에서 상대방을 내 페이스로 완벽히 리드할 수 있습니다.",
        "reading_female": "능숙한 대인관계 조율력과 따뜻한 카리스마로 주변 사람들을 내 든든한 아군으로 만듭니다. 의견을 당당하게 피력하세요.",
        "action_guide": "핵심 강점을 자신감 있게 표현하고, 주도적으로 대화의 흐름을 이끌어가세요."
    },
    {
        "name": "XIX. THE SUN (태양)", "keyword": "최고의 번영 · 찬란한 영광 · 축하받을 낭보",
        "symbolism": "붉은 깃발을 들고 백마를 탄 아이와 해바라기는 어둠과 장애물을 완전히 걷어내고 승리와 축복을 맞이하는 절정의 운세를 의미합니다.",
        "reading_male": "막혀 있던 자금 흐름이나 프로젝트의 난관이 시원하게 뚫리며 결실을 맺습니다. 명예와 실속을 동시에 쟁취하는 날입니다.",
        "reading_female": "내면의 밝고 긍정적인 에너지가 주변을 환하게 밝힙니다. 축하받을 소식이 들려오며 인간관계에 화목이 넘칩니다.",
        "action_guide": "햇살을 받으며 가벼운 야외 산책을 즐기고, 기분 좋은 미소로 주변에 긍정 에너지를 전파하세요."
    }
]

DAILY_OUTFITS_POOL = {
    "male": {
        "young": ["화이트 린넨 셔츠 & 실버 메탈 워치 쿨비즈 룩", "올리브 그린 쿨맥스 피케티 & 라이트 베이지 반바지", "코랄 핑크 린넨 셔츠 & 화이트 쿨 슬랙스", "웜 크림 톤 반팔 니트 & 차콜 밴딩 스판 팬츠", "딥 네이비 스트라이프 하프 셔츠 & 메탈 팔찌", "스카이블루 오픈카라 반팔 & 라이트 그레이 슬랙스"],
        "senior": ["스노우 화이트 쿨비즈 셔츠 & 실버 가죽 세미 워치", "다크 올리브 린넨 헨리넥 셔츠 & 통풍 차콜 슬랙스", "딥 와인 톤 하프 카라티 & 로즈골드 메탈 워치", "샌드 베이지 린넨 재킷 & 오픈카라 쿨 셔츠", "미드나잇 블루 린넨 블레이저 & 크림 드레스 팬츠", "클래식 네이비 피케 셔츠 & 라이트 브라운 팬츠"]
    },
    "female": {
        "young": ["순백색 린넨 스퀘어넥 원피스 & 은은한 실버 펜던트", "세이지 그린 린넨 원피스 & 실버 뱅글 팔찌", "로즈 핑크 뷔스티에 블라우스 & 라이트 데님", "크림 오프숄더 니트 & 샌드 베이지 와이드 팬츠", "스카이 블루 린넨 셔츠 & 화이트 하이웨스트 팬츠", "라벤더 톤 플리츠 원피스 & 미니멀 숄더백"],
        "senior": ["스노우 화이트 린넨 셋업 & 고급스러운 실버 워치", "올리브 카키 린넨 블라우스 & 통풍 보타닉 슬랙스", "코랄 로즈 엘레강스 린넨 자켓 & 모던 이어링", "웜 베이지 실크 블렌드 셔츠 & 아이보리 쿨 와이드 팬츠", "딥 네이비 린넨 쉬폰 원피스 & 클래식 은 팔찌", "소프트 핑크 린넨 자켓 & 펄 네크리스"]
    }
}

LUCKY_ITEMS_POOL = ["실버 메탈 워치", "가벼운 원목 명함집", "은은한 시트러스 아로마", "클래식 만년필", "가죽 미니 지갑", "블루라이트 차단 안경", "핸드메이드 가죽 키링", "산뜻한 린넨 손수건"]
LUCKY_DIRECTIONS_POOL = ["정서쪽 (백호 방위)", "정동쪽 (청룡 방위)", "정남쪽 (주작 방위)", "정북쪽 (현무 방위)", "동남쪽 (풍수 생기방)", "서북쪽 (천문 금전방)"]
LUCKY_MENUS_POOL = ["도라지차와 가벼운 고단백 식사", "신선한 아보카도 샐러드와 미온수", "따뜻한 전복죽과 비타민 과일", "속이 편안한 영양 솥밥", "검은콩 두유와 견과류", "시원한 메밀소바와 야채튀김"]
MINDSETS_POOL = ["맺고 끊음을 명확히 대화하기", "새로운 제안에 열린 마음 갖기", "상대의 말을 경청하고 공감하기", "중요한 약속을 철저히 지키기", "원칙을 지키며 유연하게 대처하기", "서두르지 않고 한 번 더 검토하기"]
ACTIONS_POOL = ["오늘 반드시 끝낼 우선순위 3가지 메모하기", "아침 시간 가벼운 스트레칭과 심호흡 5회", "점심 식사 후 햇볕 쬐며 10분간 산책하기", "지갑 속 영수증 정리하고 카드함 정돈하기", "오랫동안 고마웠던 지인에게 안부 문자 보내기", "책상 위 불필요한 서류 3개 정리하기"]

@app.get("/")
def serve_home():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return HTMLResponse("<h2>달하(DALHA) 서비스 준비 중</h2>")

def calculate_biorhythm(birth_date: datetime.date, target_date: datetime.date):
    days_lived = (target_date - birth_date).days
    p_val = round(math.sin(2 * math.pi * days_lived / 23) * 100)
    e_val = round(math.sin(2 * math.pi * days_lived / 28) * 100)
    i_val = round(math.sin(2 * math.pi * days_lived / 33) * 100)

    def get_status(val, cycle_name):
        pct = round((val + 100) / 2)
        if val >= 50: return {"val": val, "pct": pct, "status": "최고조", "color": "#DC2626"}
        elif val > 0: return {"val": val, "pct": pct, "status": "상승기", "color": "#EA580C"}
        elif val == 0: return {"val": val, "pct": 50, "status": "전환점", "color": "#D97706"}
        elif val > -50: return {"val": val, "pct": pct, "status": "하강기", "color": "#2563EB"}
        else: return {"val": val, "pct": pct, "status": "침체기", "color": "#475569"}

    is_critical_day = abs(p_val) <= 5 or abs(e_val) <= 5 or abs(i_val) <= 5
    if is_critical_day:
        overall_advice = "바이오리듬이 영점(0%) 전환선에 걸쳐 기운이 전환되는 민감한 날입니다. 감정적 언쟁이나 무리한 일정, 충동적인 계약 판단을 피하고 매사 한 번 더 확인하세요."
    elif p_val >= 30 and e_val >= 30 and i_val < 0:
        overall_advice = "지성 리듬이 다소 낮으나 신체와 감성 에너지가 충만합니다. 활발한 야외 활동, 스포츠, 대인관계 미팅에서 최고의 성과를 거둘 수 있습니다."
    elif i_val >= 30 and (p_val < 0 or e_val < 0):
        overall_advice = "두뇌 회전과 직관이 번뜩이는 날입니다. 무리한 육체 활동을 줄이고 전략 기획, 서류 정리, 자기계발 공부에 집중할 때 능률이 극대화됩니다."
    elif p_val >= 40 and e_val >= 40 and i_val >= 40:
        overall_advice = "신체·감성·지성 3대 생체 에너지가 모두 절정에 달한 골든 데이입니다. 오랫동안 망설이던 중요 과제를 주도적으로 추진하면 대길합니다."
    elif p_val < 0 and e_val < 0 and i_val < 0:
        overall_advice = "3대 에너지가 모두 재충전 구간에 머물러 있습니다. 중요한 결정은 잠시 미루고 따뜻한 휴식으로 내실을 다지세요."
    else:
        overall_advice = "신체와 마음의 에너지가 안정된 균형을 유지하고 있습니다. 평소 루틴을 차분히 지켜나가며 순조롭게 일과를 완수하기 좋은 하루입니다."

    return {
        "days_lived": days_lived, "physical": get_status(p_val, "신체"),
        "emotional": get_status(e_val, "감성"), "intellectual": get_status(i_val, "지성"),
        "overall_summary": overall_advice
    }

def get_daewoon_info(y_cg: str, gender: str) -> tuple[str, bool]:
    is_yang = y_cg in YANG_STEMS
    is_male = (gender == "male")
    return ("순행(順行)", True) if ((is_male and is_yang) or (not is_male and not is_yang)) else ("역행(逆行)", False)

def compute_saju_full_payload(name: str, gender: str, year: int, month: int, day: int, calendar_type: str, sijin_idx: int):
    base_date = datetime.date(1900, 1, 1)
    today = datetime.date.today()
    target_date = datetime.date(year, month, day)
    diff_days = (target_date - base_date).days

    d_cg_idx = diff_days % 10
    d_jj_idx = (diff_days + 10) % 12
    d_cg, d_jj = CHEONGAN_HANJA[d_cg_idx], JIJI_HANJA[d_jj_idx]

    year_offset = (year - 4) % 60
    y_cg_idx, y_jj_idx = year_offset % 10, year_offset % 12
    y_cg, y_jj = CHEONGAN_HANJA[y_cg_idx], JIJI_HANJA[y_jj_idx]

    month_adj = month
    if calendar_type == "lunar": month_adj = (month + 1)
    elif calendar_type == "leap": month_adj = (month + 2)

    m_jj_idx = (month_adj) % 12
    m_cg_idx = (y_cg_idx % 5 * 2 + 2 + (month_adj - 2)) % 10
    m_cg, m_jj = CHEONGAN_HANJA[m_cg_idx], JIJI_HANJA[m_jj_idx]

    if sijin_idx < 0:
        h_pillar, h_cg, h_jj = "時未詳", "-", "-"
        sijin_korean = "시간 모름"
    else:
        h_jj_idx = sijin_idx
        h_cg_idx = (d_cg_idx % 5 * 2 + h_jj_idx) % 10
        h_cg, h_jj = CHEONGAN_HANJA[h_cg_idx], JIJI_HANJA[h_jj_idx]
        h_pillar = f"{h_cg}{h_jj}"
        sijin_korean = SIJIN_KOREAN_MAP.get(sijin_idx, "사시(巳時)")

    d_animal = ANIMAL_MAP.get(d_jj, "개")
    current_age = today.year - year + 1

    pillars_detail = {
        "hour": { "cg": h_cg, "cg_elem": CHEONGAN_ELEMENTS.get(h_cg, "none"), "jj": h_jj, "jj_elem": JIJI_ELEMENTS.get(h_jj, "none"), "jijanggan": JIJANGGAN_FULL_MAP.get(h_jj, []) },
        "day": { "cg": d_cg, "cg_elem": CHEONGAN_ELEMENTS.get(d_cg, "none"), "jj": d_jj, "jj_elem": JIJI_ELEMENTS.get(d_jj, "none"), "jijanggan": JIJANGGAN_FULL_MAP.get(d_jj, []) },
        "month": { "cg": m_cg, "cg_elem": CHEONGAN_ELEMENTS.get(m_cg, "none"), "jj": m_jj, "jj_elem": JIJI_ELEMENTS.get(m_jj, "none"), "jijanggan": JIJANGGAN_FULL_MAP.get(m_jj, []) },
        "year": { "cg": y_cg, "cg_elem": CHEONGAN_ELEMENTS.get(y_cg, "none"), "jj": y_jj, "jj_elem": JIJI_ELEMENTS.get(y_jj, "none"), "jijanggan": JIJANGGAN_FULL_MAP.get(y_jj, []) }
    }

    scores = {"wood": 0.0, "fire": 0.0, "earth": 0.0, "metal": 0.0, "water": 0.0}
    for cg in [y_cg, m_cg, d_cg]: scores[CHEONGAN_ELEMENTS[cg]] += 25.0
    if h_cg != "-": scores[CHEONGAN_ELEMENTS[h_cg]] += 25.0

    for idx, jj in enumerate([y_jj, m_jj, d_jj]):
        mult = 1.5 if idx == 1 else 1.0
        for item in JIJANGGAN_FULL_MAP.get(jj, []):
            scores[item["elem"]] += item["weight"] * mult

    total_score = sum(scores.values())
    elem_percentages = { k: round((v / total_score) * 100, 1) for k, v in scores.items() }

    day_elem = CHEONGAN_ELEMENTS[d_cg]
    support_score = scores.get(day_elem, 0)
    singang_status = "신약(身弱) 사주" if support_score < 45 else ("신강(身强) 사주" if support_score > 65 else "중화(中和) 사주")

    daewoon_dir_name, is_daewoon_forward = get_daewoon_info(y_cg, gender)

    today_ordinal = today.toordinal()
    daily_hash = (today_ordinal * 31 + diff_days * 17 + (11 if gender == "male" else 23)) % 1000003

    age_group = "young" if current_age < 40 else "senior"
    outfit_list = DAILY_OUTFITS_POOL[gender][age_group]
    fashion_style = outfit_list[daily_hash % len(outfit_list)]

    num1 = ((daily_hash % 9) + 1)
    num2 = (((daily_hash // 10) % 9) + 1)
    if num1 == num2: num2 = (num1 % 9) + 1
    lucky_number = f"{min(num1, num2)}, {max(num1, num2)}"

    lucky_direction = LUCKY_DIRECTIONS_POOL[(daily_hash + 1) % len(LUCKY_DIRECTIONS_POOL)]
    lucky_item = LUCKY_ITEMS_POOL[(daily_hash + 2) % len(LUCKY_ITEMS_POOL)]
    recommended_menu = LUCKY_MENUS_POOL[(daily_hash + 3) % len(LUCKY_MENUS_POOL)]
    mindset = MINDSETS_POOL[(daily_hash + 4) % len(MINDSETS_POOL)]
    action = ACTIONS_POOL[(daily_hash + 5) % len(ACTIONS_POOL)]

    daily_score = 65 + (daily_hash % 36)
    today_diff = (today - base_date).days
    today_cg, today_jj = CHEONGAN_HANJA[today_diff % 10], JIJI_HANJA[(today_diff + 10) % 12]
    
    score_status_word = "대길(大吉)과 도약의 하루" if daily_score >= 88 else ("순조로운 화합과 발전의 하루" if daily_score >= 75 else "내실을 다지고 신중을 기할 하루")
    daily_title = f"[{today_cg}{today_jj}일] {score_status_word}"

    three_stage_advice = (f"☀️ <strong>오전:</strong> 아이디어를 공유하며 활발히 소통하세요.<br>"
                          f"🌤️ <strong>오후:</strong> 본원({d_cg})의 리더십으로 주요 과제를 완수하세요.<br>"
                          f"🌙 <strong>저녁:</strong> 가볍게 하루를 정리하고 충전하세요.")

    min_elem = min(elem_percentages, key=elem_percentages.get)
    user_talisman = TALISMAN_OHEANG_MAP.get(min_elem, TALISMAN_OHEANG_MAP["metal"])
    user_animal_icon = ANIMAL_ICONS.get(d_animal, "🐶")

    biorhythm_data = calculate_biorhythm(target_date, today)
    cal_name = "양력" if calendar_type == "solar" else ("음력(윤달)" if calendar_type == "leap" else "음력")
    birth_summary_str = f"{year}년 {month}월 {day}일생 ({cal_name}) · {sijin_korean}생"

    return {
        "user_name": name, "gender": gender, "birth_summary": birth_summary_str, "current_age": current_age,
        "singang_status": singang_status, "daewoon_direction": daewoon_dir_name, "is_daewoon_forward": is_daewoon_forward,
        "saju_data": {
            "year_pillar": f"{y_cg}{y_jj}", "month_pillar": f"{m_cg}{m_jj}", "day_pillar": f"{d_cg}{d_jj}", "hour_pillar": h_pillar,
            "pillars_detail": pillars_detail, "animal_symbol": d_animal, "animal_icon": user_animal_icon,
            "elements": elem_percentages
        },
        "daily_fortune": {
            "score": daily_score, "title": daily_title, "advice": three_stage_advice,
            "lucky_number": lucky_number, "lucky_direction": lucky_direction, "lucky_item": lucky_item,
            "fashion_style": fashion_style, "recommended_menu": recommended_menu, "mindset": mindset, "action": action,
            "talisman": user_talisman
        },
        "biorhythm": biorhythm_data
    }

# --- Pydantic 데이터 모델 ---
class KakaoLoginRequest(BaseModel):
    kakao_id: str
    name: Optional[str] = "최정오"
    gender: Optional[str] = "male"
    birthyear: Optional[str] = "1978"
    birthday: Optional[str] = "0813"
    birthday_type: Optional[str] = "SOLAR"

class RegisterSajuRequest(BaseModel):
    user_id: int
    name: str
    gender: str
    birth_year: int
    birth_month: int
    birth_day: int
    calendar_type: str
    sijin_index: int

class OrderReportRequest(BaseModel):
    user_id: int
    report_key: str
    cost: int
    sub_option: Optional[str] = "기본"
    partner_name: Optional[str] = "상대방"
    relation: Optional[str] = "연인/결혼"

# --- API 엔드포인트 ---

# 1. 카카오 로그인 및 회원 조회 API
@app.post("/api/auth/kakao")
def kakao_auth(req: KakaoLoginRequest):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE kakao_id = ?", (req.kakao_id,))
    user = cursor.fetchone()
    
    if user:
        user_id = user["id"]
        saju_payload = compute_saju_full_payload(
            user["name"], user["gender"], user["birth_year"],
            user["birth_month"], user["birth_day"], user["calendar_type"], user["sijin_index"]
        )
        
        cursor.execute("SELECT report_key, report_title, report_content, created_at FROM unlocked_reports WHERE user_id = ? ORDER BY id DESC", (user_id,))
        unlocked_list = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return {
            "status": "existing_user",
            "user_id": user_id,
            "coin_balance": user["coin_balance"],
            "profile": {
                "name": user["name"],
                "gender": user["gender"],
                "birth_year": user["birth_year"],
                "birth_month": user["birth_month"],
                "birth_day": user["birth_day"],
                "calendar_type": user["calendar_type"],
                "sijin_index": user["sijin_index"]
            },
            "saju_analysis": saju_payload,
            "unlocked_reports": unlocked_list
        }
    else:
        b_year = int(req.birthyear) if req.birthyear and req.birthyear.isdigit() else 1978
        b_month, b_day = 8, 13
        if req.birthday and len(req.birthday) == 4:
            b_month = int(req.birthday[:2])
            b_day = int(req.birthday[2:])

        cal_type = "lunar" if req.birthday_type == "LUNAR" else "solar"
        gender_val = "female" if req.gender in ["female", "F"] else "male"

        cursor.execute("""
        INSERT INTO users (kakao_id, name, gender, birth_year, birth_month, birth_day, calendar_type, sijin_index, coin_balance)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1000)
        """, (req.kakao_id, req.name, gender_val, b_year, b_month, b_day, cal_type, 5))
        conn.commit()
        new_user_id = cursor.lastrowid
        conn.close()

        return {
            "status": "new_user_needs_confirm",
            "user_id": new_user_id,
            "coin_balance": 1000,
            "kakao_prefill": {
                "name": req.name,
                "gender": gender_val,
                "birth_year": b_year,
                "birth_month": b_month,
                "birth_day": b_day,
                "calendar_type": cal_type,
                "sijin_index": 5
            }
        }

# 2. 신규 회원 사주 최종 확인 및 수정 등록 API
@app.post("/api/user/register-saju")
def register_saju(req: RegisterSajuRequest):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE users 
    SET name = ?, gender = ?, birth_year = ?, birth_month = ?, birth_day = ?, calendar_type = ?, sijin_index = ?
    WHERE id = ?
    """, (req.name, req.gender, req.birth_year, req.birth_month, req.birth_day, req.calendar_type, req.sijin_index, req.user_id))
    conn.commit()
    
    cursor.execute("SELECT * FROM users WHERE id = ?", (req.user_id,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    saju_payload = compute_saju_full_payload(
        user["name"], user["gender"], user["birth_year"],
        user["birth_month"], user["birth_day"], user["calendar_type"], user["sijin_index"]
    )

    return {
        "status": "success",
        "user_id": user["id"],
        "coin_balance": user["coin_balance"],
        "profile": {
            "name": user["name"],
            "gender": user["gender"],
            "birth_year": user["birth_year"],
            "birth_month": user["birth_month"],
            "birth_day": user["birth_day"],
            "calendar_type": user["calendar_type"],
            "sijin_index": user["sijin_index"]
        },
        "saju_analysis": saju_payload
    }

# 3. 유료 감명서 결제 및 서버 DB 저장 API
@app.post("/api/reports/unlock")
def unlock_report(req: OrderReportRequest):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (req.user_id,))
    user = cursor.fetchone()

    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="회원 정보가 없습니다.")

    if user["coin_balance"] < req.cost:
        conn.close()
        raise HTTPException(status_code=400, detail="보유 복채가 부족합니다.")

    new_balance = user["coin_balance"] - req.cost
    cursor.execute("UPDATE users SET coin_balance = ? WHERE id = ?", (new_balance, req.user_id))

    report_title = ""
    report_content = ""
    current_age = datetime.date.today().year - user["birth_year"] + 1

    if req.report_key == "daewoon":
        res = get_daewoon_report({"name": user["name"], "gender": user["gender"], "age": current_age})
        report_title, report_content = res["title"], res["content"]
    elif req.report_key == "sinnian":
        res = get_sinnian_report({"name": user["name"], "gender": user["gender"]})
        report_title, report_content = res["title"], res["content"]
    elif req.report_key == "gunghap":
        res = get_gunghap_report({"name": user["name"], "partner_name": req.partner_name, "relation": req.relation})
        report_title, report_content = res["title"], res["content"]
    elif req.report_key in ["wealth", "love", "business", "health"]:
        res = get_theme_report({"theme": req.report_key, "sub_option": req.sub_option, "name": user["name"], "gender": user["gender"]})
        report_title, report_content = res["title"], res["content"]

    today_str = datetime.date.today().strftime("%Y-%m-%d")
    cursor.execute("""
    INSERT INTO unlocked_reports (user_id, report_key, report_title, report_content, created_at)
    VALUES (?, ?, ?, ?, ?)
    """, (req.user_id, req.report_key, report_title, report_content, today_str))
    conn.commit()

    cursor.execute("SELECT report_key, report_title, report_content, created_at FROM unlocked_reports WHERE user_id = ? ORDER BY id DESC", (req.user_id,))
    unlocked_list = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return {
        "status": "success",
        "new_balance": new_balance,
        "title": report_title,
        "content": report_content,
        "unlocked_reports": unlocked_list
    }

# 4. 복채 충전 API (서버 DB 동기화)
@app.post("/api/user/charge-coin")
def charge_coin(req: dict):
    user_id = req.get("user_id")
    amount = req.get("amount", 0)
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET coin_balance = coin_balance + ? WHERE id = ?", (amount, user_id))
    conn.commit()
    cursor.execute("SELECT coin_balance FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return {"status": "success", "new_balance": user["coin_balance"]}

# 5. 별자리 및 타로 엔드포인트
@app.get("/api/zodiac-fortune")
def get_zodiac_fortune(type: str = "zodiac", key: str = "쥐"):
    today = datetime.date.today()
    seed = today.toordinal() + hash(key)
    score = 68 + (seed % 31)
    
    if type == "zodiac":
        years = [2012, 2000, 1988, 1976, 1964]
        zodiac_names = list(ANIMAL_MAP.values())
        z_idx = zodiac_names.index(key) if key in zodiac_names else 0
        adj_years = [y - ((4 - z_idx) % 12) for y in years]
        
        year_advices = [
            {"year_label": f"{str(adj_years[0])[-2:]}년생 ({today.year - adj_years[0] + 1}세)", "tip": "학업과 진로에서 번뜩이는 영감을 발휘해 칭찬을 받는 날입니다."},
            {"year_label": f"{str(adj_years[1])[-2:]}년생 ({today.year - adj_years[1] + 1}세)", "tip": "취업·이직 및 주요 프로젝트에서 결정적 주도권을 쥐게 됩니다."},
            {"year_label": f"{str(adj_years[2])[-2:]}년생 ({today.year - adj_years[2] + 1}세)", "tip": "실속을 차리고 금전적 결실과 성과를 확정 짓는 대길의 타이밍입니다."},
            {"year_label": f"{str(adj_years[3])[-2:]}년생 ({today.year - adj_years[3] + 1}세)", "tip": "귀인의 도움으로 복잡했던 계약이나 사업 협상이 순조롭게 성사됩니다."},
            {"year_label": f"{str(adj_years[4])[-2:]}년생 ({today.year - adj_years[4] + 1}세)", "tip": "무리한 확장보다 내실을 다지며 평온한 가문의 화목을 누립니다."}
        ]
        return {
            "name": f"{key}띠", "icon": ANIMAL_ICONS.get(key, "🐾"), "score": score, "title": "귀인의 조력과 재물운이 합을 이루는 대길의 날",
            "overview": f"오늘 {key}띠는 실력과 결단력이 빛을 발하는 날입니다. 큰 흐름을 보고 추진하면 성취가 따릅니다.",
            "year_tips": year_advices, "lucky_time": "오후 2시 ~ 4시", "lucky_match": "소띠, 용띠"
        }
    else:
        star_item = next((s for s in STAR_SIGNS if s["name"] == key), STAR_SIGNS[0])
        return {
            "name": star_item["name"], "icon": star_item["icon"], "period": star_item["period"], "score": score,
            "title": "창의적인 영감이 샘솟는 럭키 데이",
            "overview": f"{star_item['name']}에게 오늘은 내면의 직관이 강력하게 작용하여 뜻밖의 기회가 찾아오는 날입니다.",
            "focus_badge": "💰 오늘 가장 중요한 재물운", "focus_content": "유리한 조건의 거래 계약이나 금전적 이익이 성사될 가능성이 매우 높습니다.",
            "lucky_item": "은색 메탈 액세서리", "lucky_time": "오전 10시 ~ 12시"
        }

@app.get("/api/daily-tarot")
def get_daily_tarot(slot: int = 1):
    return TAROT_CARDS[random.randint(0, len(TAROT_CARDS) - 1)]

# 6. 리포트 생성 함수들
def get_daewoon_report(req: dict):
    user_name = req.get("name", "최정오")
    gender = req.get("gender", "male")
    age = req.get("age", 49)
    start_age = (age // 10) * 10 + 3
    end_age = start_age + 9
    gender_str = "남성(男命)" if gender == "male" else "여성(女命)"
    spouse_star = "재성(財星 / 아내·재물)" if gender == "male" else "관성(官星 / 남편·명예)"

    return {
        "title": f"👑 자미두수 평생운세 ({gender_str})",
        "content": f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div>
                <div style="border-left: 4px solid #2D6A4F; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #2D6A4F; font-weight: 800;">Chapter 1. 평생 대운맥 및 생애 주도권</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #0F172A; margin-top: 2px;">
                        🌐 {user_name}님({gender_str})의 생애 4대 주기별 거시적 운명 흐름
                    </h4>
                </div>
                <p style="color: #475569; margin-bottom: 10px;">
                    자미두수 명반과 성별 명식을 교차 감명한 결과, {user_name}님은 초년의 배움과 역량 축적을 거쳐 중장년기에 폭발적인 {spouse_star}의 결실을 완성하는 <strong>'만성대기(晩成大器)형 거목의 명식'</strong>입니다.
                </p>
                <div style="display: flex; flex-direction: column; gap: 10px;">
                    <div style="background: #F8FAFC; border-radius: 8px; padding: 10px 12px;">
                        <p style="font-weight: 800; color: #0F172A; font-size: 14.5px; margin-bottom: 2px;">🌱 [유년기 : 근본 기틀 형성기]</p>
                        <p style="color: #475569; font-size: 13.5px;">남다른 지적 호기심과 영민함으로 도덕적 기준과 가치관을 단단히 다지던 시기였습니다.</p>
                    </div>
                    <div style="background: #F8FAFC; border-radius: 8px; padding: 10px 12px;">
                        <p style="font-weight: 800; color: #0F172A; font-size: 14.5px; margin-bottom: 2px;">🌿 [청년기 : 역량 축적 및 실전기]</p>
                        <p style="color: #475569; font-size: 13.5px;">사회에 진출하여 실무 전문성을 연마하고, 인맥과 실물 감각의 뼈대를 견고히 구축했습니다.</p>
                    </div>
                    <div style="background: #FEF3C7; border: 1.5px solid #FCD34D; border-radius: 8px; padding: 10px 12px;">
                        <p style="font-weight: 800; color: #78350F; font-size: 14.5px; margin-bottom: 2px;">🔥 [중장년기 (*현재 위치 / {start_age}세 ~ {end_age}세) : 황금 결실기]</p>
                        <p style="color: #92400E; font-size: 13.5px; font-weight: 600;">
                            <strong>{user_name}님 인생 일대에서 가장 강력한 천운의 파도가 솟구치는 최고 전성기 구간입니다.</strong> 본인이 직접 주도권을 쥐고 설계한 판에서 자산과 사회적 지위가 수직 상승합니다.
                        </p>
                    </div>
                    <div style="background: #F8FAFC; border-radius: 8px; padding: 10px 12px;">
                        <p style="font-weight: 800; color: #0F172A; font-size: 14.5px; margin-bottom: 2px;">🍎 [말년기 : 태평성대 및 가문 번영기]</p>
                        <p style="color: #475569; font-size: 13.5px;">평생 축적한 자산과 인망을 토대로 안락한 노후를 누리며 후대에 안정적 번영을 대물림합니다.</p>
                    </div>
                </div>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #D97706; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #D97706; font-weight: 800;">Chapter 2. 현재 10년 대운 집중 감명</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #78350F; margin-top: 2px;">
                        📈 Q. {user_name}님의 현재 10년 대운({start_age}세 ~ {end_age}세) 핵심 결실은?
                    </h4>
                </div>
                <p style="color: #78350F; line-height: 1.85;">
                    현재 대운맥은 사주 본원에 귀인이 결합하는 절정기입니다. 끌려다니지 않고 본인의 통솔력으로 사업, 투자, 조직을 리드할 때 승률이 95% 이상으로 치솟습니다.
                </p>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #E11D48; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #E11D48; font-weight: 800;">Chapter 3. 자미두수 12궁 가문·가족운</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #881337; margin-top: 2px;">
                        🏡 부모덕 · 자녀 출세운 · 형제자매 우애 정밀 분석
                    </h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14px; color: #9F1239; line-height: 1.8;">
                    <p>• <strong>👴 부모궁 (父母宮 - 부모덕 & 유산운):</strong> 부모님의 든든한 가치관과 정서적 지지를 바탕으로 성장하는 명식입니다. 중장년 이후 부모님의 가업이나 부동산 상속·증여의 기운이 온화하게 연결되며, 효도를 다할수록 본인의 사업운이 배가됩니다.</p>
                    <p>• <strong>👶 자녀궁 (子女宮 - 자녀의 성품 & 미래 출세):</strong> 영민하고 도덕성이 높은 귀한 자손을 두는 명식입니다. 자녀가 전문직, 공직, 학계 등 사회적으로 인정받는 명예로운 분야로 진출하여 가문을 빛내는 효자·효녀가 됩니다.</p>
                    <p>• <strong>🤝 형제궁 (兄弟宮 - 형제자매 우애 & 상호 조력):</strong> 형제자매 간에 서로의 독립성을 존중해 줄 때 성인이 된 후 중요한 인생의 고비마다 든든한 지원군이자 비상시의 귀인이 되어줍니다.</p>
                </div>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #2563EB; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #2563EB; font-weight: 800;">Chapter 4. 평생 학업·시험·문서운</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #1E3A8A; margin-top: 2px;">
                        🎓 관록궁 & 문창성 기반 고시/자격/승진 시험 합격운
                    </h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14px; color: #1E40AF; line-height: 1.8;">
                    <p>• <strong>타고난 지적 역량:</strong> 한번 파고든 학문과 기술의 끝을 보는 '문창성(文昌星)'의 지혜를 타고났습니다. 벼락치기보다는 꾸준한 루틴을 세울 때 시험 합격률이 98%에 달합니다.</p>
                    <p>• <strong>국가공인/전문 자격증 합격운:</strong> 부동산, 금융, 법률, 기술 전문 자격 취득 및 공공기관/승진 시험에서 강력한 문서운이 발동하여 높은 점수로 합격증을 거머쥡니다.</p>
                </div>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #F59E0B; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #D97706; font-weight: 800;">Chapter 5. 실전 개운 솔루션</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #78350F; margin-top: 2px;">
                        🔥 {gender_str} 맞춤 3대 개운(開運) 비책
                    </h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14px; color: #451A03; line-height: 1.8;">
                    <p>• <strong>[자산 수성]:</strong> 단기 단타 투자보다 실물 부동산 및 우량 자산 중심 고정 현금 흐름을 창출하세요.</p>
                    <p>• <strong>[관계 처세]:</strong> 유능한 협력 파트너를 영입하여 위임의 기술을 발휘할 때 명예와 성취가 배가됩니다.</p>
                    <p>• <strong>[건강 관리]:</strong> 머리는 시원하게 하체는 따뜻하게 유지하는 두한족열 루틴으로 평정심을 유지하세요.</p>
                </div>
            </div>
        </div>
        """
    }

def get_sinnian_report(req: dict):
    user_name = req.get("name", "최정오")
    gender = req.get("gender", "male")
    gender_str = "남성" if gender == "male" else "여성"

    monthly_guides = [
        {"m": "1월", "gua": "지천태(地天泰) 괘", "opp": "새해 첫 출발이 대길하여 신규 사업 및 프로젝트 착수에 최적입니다.", "warn": "초반의 빠른 성취에 자만하지 말고 세부 규정을 차분히 정비하세요."},
        {"m": "2월", "gua": "수천수(水天需) 괘", "opp": "실력과 내실을 다지며 시장 상황의 흐름을 관망할 때 이익이 보존됩니다.", "warn": "서두른 결정이나 충동구매는 후회를 부르니 하루 이틀 시일을 두세요."},
        {"m": "3월", "gua": "천화동인(天火同人) 괘", "opp": "귀인의 조력이 닿아 인간관계와 직무에서 강력한 협력자가 나타납니다.", "warn": "주변과의 이견 조율 시 감정적 대응을 피하고 데이터로 설득하세요."},
        {"m": "4월", "gua": "풍천소축(風天小畜) 괘", "opp": "작은 성과가 차곡차곡 쌓여 종잣돈의 기틀이 한 단계 단단해집니다.", "warn": "무리한 대출이나 투자는 지양하고 현금 유동성을 확보하세요."},
        {"m": "5월", "gua": "화천대유(火天大有) 괘", "opp": "★올해 상반기 최고의 재물운! 부동산/투자/계약에서 큰 결실을 맺습니다.", "warn": "성과를 독식하려 하지 말고 함께한 동료들에게 따뜻하게 베푸세요."},
        {"m": "6월", "gua": "천풍구(天風姤) 괘", "opp": "새로운 제안과 이직/신규 프로젝트의 반가운 활로가 열립니다.", "warn": "계약서의 독소 조항과 구두 약속을 면밀히 검증하는 신중함이 필수입니다."},
        {"m": "7월", "gua": "천수송(天水訟) 괘", "opp": "기존의 복잡했던 업무 체계를 깔끔히 정리하고 체질을 개선하는 달.", "warn": "사소한 언쟁이나 시비수를 피하기 위해 공감 화법을 철저히 유지하세요."},
        {"m": "8월", "gua": "풍지관(風地觀) 괘", "opp": "상반기의 성과를 점검하고 하반기 대도약을 위한 전략을 세우기에 최적입니다.", "warn": "체력 저하와 간 피로를 방지하기 위해 충분한 수면과 족욕을 챙기세요."},
        {"m": "9월", "gua": "산지박(山地剝) 괘", "opp": "불필요한 고정비와 낭비 요소를 말끔히 청산하여 실속을 챙깁니다.", "warn": "무리한 확장보다 기존 고객 및 핵심 업무 관리에 집중하세요."},
        {"m": "10월", "gua": "지뢰복(地雷復) 괘", "opp": "★올해 하반기 최고의 승부처! 승진, 수주, 투자 회수에서 낭보가 울립니다.", "warn": "기회가 올 때 주저하지 말고 과감한 결단력으로 주도권을 쥐세요."},
        {"m": "11월", "gua": "수뢰준(水雷屯) 괘", "opp": "내년을 위한 새로운 아이템이나 자격/학업의 씨앗을 뿌리기에 좋습니다.", "warn": "경험자의 조언을 경청하여 불필요한 시행착오를 사전에 방지하세요."},
        {"m": "12월", "gua": "지화명이(地火明夷) 괘", "opp": "한 해 일군 풍성한 결실을 확정 짓고 가문과 가족의 화목을 누립니다.", "warn": "연말 과음과 과로를 피하고 따뜻한 온기로 몸과 마음을 달래세요."}
    ]

    months_html = "".join([f"""
        <div style="background: #F8FAFC; border-left: 3.5px solid #2D6A4F; border-radius: 8px; padding: 12px 14px; margin-bottom: 8px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                <span style="font-weight: 800; color: #0F172A; font-size: 15px;">📅 {item['m']} 세운 가이드</span>
                <span style="font-size: 12px; background: #EBF5EE; color: #2D6A4F; font-weight: 800; padding: 2px 8px; border-radius: 6px;">{item['gua']}</span>
            </div>
            <p style="color: #065F46; font-size: 13.5px; line-height: 1.6; margin-bottom: 2px;">
                <strong>✨ 기회의 순간:</strong> {item['opp']}
            </p>
            <p style="color: #991B1B; font-size: 13px; line-height: 1.55;">
                <strong>⚠️ 주의할 처세:</strong> {item['warn']}
            </p>
        </div>
    """ for item in monthly_guides])

    return {
        "title": f"📅 2026 丙午년 총운 & 하반기 정밀 월별 가이드 ({gender_str})",
        "content": f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div>
                <div style="border-left: 4px solid #DC2626; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #DC2626; font-weight: 800;">Chapter 1. 2026년 세운(歲運) 총론</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #991B1B; margin-top: 2px;">
                        🔥 2026 丙午년(붉은 말의 해) {user_name}님의 도약 총운 & 가족 화합
                    </h4>
                </div>
                <p style="color: #7F1D1D; line-height: 1.85; margin-bottom: 12px;">
                    2026년은 강렬한 불(火)의 기운이 어둠을 걷어내고 대지를 환하게 비추는 丙午년입니다. {user_name}님의 명식과 조화를 이루어 그동안 준비해 온 역량이 화려하게 꽃을 피우며 막혀 있던 활로가 시원하게 뚫리는 <strong>'비상(飛翔)의 한 해'</strong>가 됩니다. 집안에 경사가 깃들어 가족 간의 결속이 한층 두터워집니다.
                </p>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #F59E0B; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #D97706; font-weight: 800;">Chapter 2. 2026년 소망 성취 지수</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #78350F; margin-top: 2px;">
                        🎯 간절한 소원 성취 확률 92% & 달성 골든타임
                    </h4>
                </div>
                <p style="color: #78350F; line-height: 1.85;">
                    올해 품은 핵심 소망(이직, 계약 체결, 부동산 매매, 시험 합격 등)은 <strong>양력 5월과 10월</strong>에 천우신조의 기운을 만나 일사천리로 성취됩니다. 주저하지 말고 해당 시기에 적극적으로 실행에 옮기세요.
                </p>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 8px;">
                    <div style="border-left: 4px solid #2D6A4F; padding-left: 10px;">
                        <span style="font-size: 12px; color: #2D6A4F; font-weight: 800;">Chapter 3. 12개월 정밀 토정비결</span>
                        <h4 style="font-size: 16.5px; font-weight: 800; color: #0F172A; margin-top: 2px;">
                            📜 1월부터 12월까지 월별 기회와 주의점
                        </h4>
                    </div>
                    <span style="font-size: 11.5px; background: #FEF3C7; color: #78350F; font-weight: 700; padding: 3px 8px; border-radius: 6px; white-space: nowrap;">
                        ※ 본 월별 흐름은 양력(Solar) 기준입니다
                    </span>
                </div>
                <div style="display: flex; flex-direction: column; gap: 4px;">
                    {months_html}
                </div>
            </div>
        </div>
        """
    }

def get_gunghap_report(req: dict):
    user_name = req.get("name", "최정오")
    partner_name = req.get("partner_name", "상대방")
    relation = req.get("relation", "연인/결혼")

    return {
        "title": f"💞 {user_name} & {partner_name} 정통 사주 궁합 ({relation})",
        "content": f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div style="background: linear-gradient(135deg, #FFF1F2 0%, #FFE4E6 100%); border: 1.5px solid #FECDD3; border-radius: 14px; padding: 16px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 12px; color: #BE123C; font-weight: 800;">정통 오행 상생 궁합 지수</span>
                    <h3 style="font-size: 20px; font-weight: 900; color: #9F1239; margin-top: 2px;">94점 (천생연분 대길합)</h3>
                    <p style="font-size: 11.5px; color: #E11D48; margin-top: 2px;">애정합 96% · 신뢰합 92% · 재물시너지 95% · 성격조화 93%</p>
                </div>
                <div style="font-size: 36px;">💖</div>
            </div>
            <div>
                <div style="border-left: 4px solid #E11D48; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #E11D48; font-weight: 800;">Chapter 1. 두 사람의 천간·지지 기운과 인연의 깊이</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #881337; margin-top: 2px;">🔗 {user_name}님과 {partner_name}님의 오행 상생 조화</h4>
                </div>
                <p style="color: #9F1239; line-height: 1.85;">
                    {user_name}님의 사주에 부족한 기운을 {partner_name}님이 풍부하게 품어주고 있어, 만날수록 자존감이 회복되는 <strong>'상호보완형 황금 인연'</strong>입니다.
                </p>
            </div>
        </div>
        """
    }

def get_theme_report(req: dict):
    theme = req.get("theme", "wealth")
    sub_opt = req.get("sub_option", "기본")
    user_name = req.get("name", "최정오")
    titles = {"wealth": "💰 평생 재물운", "love": f"💖 평생 애정운 ({sub_opt})", "business": f"🏢 사업·직업운 ({sub_opt})", "health": "🌿 평생 건강운"}

    if theme == "wealth":
        content = f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div style="border-left: 4px solid #D97706; padding-left: 10px;">
                <span style="font-size: 12px; color: #D97706; font-weight: 800;">Chapter 1. 평생 재물 원국 정밀 감명</span>
                <h4 style="font-size: 16.5px; font-weight: 800; color: #78350F; margin: 3px 0 6px;">[타고난 금고] '암장(暗藏) 황금 금고형' 자산 축적 원국</h4>
                <p style="color: #92400E; font-size: 14.5px; line-height: 1.85;">
                    {user_name}님의 사주는 겉으로 드러난 화려함보다 실속 있게 현금과 실물 자산을 차곡차곡 축적하는 전형적인 '황금 금고형' 명식입니다.
                </p>
            </div>
        </div>
        """
    elif theme == "business":
        content = f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div style="border-left: 4px solid #2563EB; padding-left: 10px;">
                <span style="font-size: 12px; color: #2563EB; font-weight: 800;">Chapter 1. 직무/사업 맞춤 운세 ({sub_opt})</span>
                <h4 style="font-size: 16.5px; font-weight: 800; color: #1E3A8A; margin: 3px 0 6px;">🎯 전문 직무 승부처 & 성공 로드맵</h4>
                <p style="color: #1E40AF; font-size: 14.5px; line-height: 1.85;">
                    {user_name}님의 명식은 상황을 주도적으로 돌파하는 전략가형 기질을 품고 있어, 본인이 주도권을 쥔 환경에서 가장 큰 성과를 거둡니다.
                </p>
            </div>
        </div>
        """
    elif theme == "love":
        content = f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div style="border-left: 4px solid #E11D48; padding-left: 10px;">
                <span style="font-size: 12px; color: #E11D48; font-weight: 800;">Chapter 1. 상태 맞춤 애정 원국 ({sub_opt})</span>
                <h4 style="font-size: 16.5px; font-weight: 800; color: #881337; margin: 3px 0 6px;">💖 인연의 기운과 결실의 타이밍</h4>
                <p style="color: #9F1239; font-size: 14.5px; line-height: 1.85;">
                    {user_name}님의 사주는 신뢰와 따뜻한 배려가 결합할 때 애정의 기운이 평생 동안 번창합니다.
                </p>
            </div>
        </div>
        """
    else:
        content = f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div style="border-left: 4px solid #059669; padding-left: 10px;">
                <span style="font-size: 12px; color: #059669; font-weight: 800;">Chapter 1. 오행 체질 장부 정밀 분석</span>
                <h4 style="font-size: 16.5px; font-weight: 800; color: #065F46; margin: 3px 0 6px;">[평생 체질] 수승화강(水昇火降) 활력과 섭생법</h4>
                <p style="color: #047857; font-size: 14.5px; line-height: 1.85;">
                    두한족열(머리는 시원하게, 발은 따뜻하게)의 기본 수칙을 유지하면 평생 에너지가 고갈되지 않습니다.
                </p>
            </div>
        </div>
        """

    return {"title": titles.get(theme, "심층 리포트"), "content": content}
@app.get("/static/og_thumb.png")
def get_og_thumbnail():
    svg_data = """<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
        <rect width="1200" height="630" fill="#0D1527"/>
        <circle cx="600" cy="220" r="90" fill="none" stroke="#E2C068" stroke-width="3"/>
        <circle cx="600" cy="220" r="75" fill="#F6E2A1"/>
        <text x="600" y="248" font-size="75" font-family="'Noto Serif KR', serif" font-weight="900" fill="#0D1527" text-anchor="middle">月</text>
        <text x="600" y="380" font-size="58" font-family="'Noto Serif KR', sans-serif" font-weight="900" fill="#FAF9F6" text-anchor="middle" letter-spacing="-1px">달하 (DALHA)</text>
        <text x="600" y="435" font-size="24" font-family="'Pretendard', sans-serif" font-weight="700" fill="#E2C068" text-anchor="middle" letter-spacing="4px">AUTHENTIC EASTERN FORTUNE</text>
        <text x="600" y="500" font-size="26" font-family="'Pretendard', sans-serif" font-weight="500" fill="#94A3B8" text-anchor="middle">달빛이 비추는 당신의 운명 · 정통 사주 · 바이오리듬 · 타로</text>
    </svg>"""
    return Response(content=svg_data, media_type="image/svg+xml")
@app.get("/robots.txt")
def get_robots():
    data = "User-agent: *\nAllow: /\nSitemap: https://dalha.kr/sitemap.xml"
    return Response(content=data, media_type="text/plain")

@app.get("/sitemap.xml")
def get_sitemap():
    data = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://dalha.kr/</loc>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>"""
    return Response(content=data, media_type="application/xml")
    # 네이버 검색 등록용 소유확인 라우트
@app.get("/naverc5036aa02eca57807bf721e44ad78969.html")
def naver_verification():
    return HTMLResponse("naver-site-verification: naverc5036aa02eca57807bf721e44ad78969.html")
# 네이버 검색 등록용 소유확인 라우트
@app.get("/naverc5036aa02eca57807bf721e44ad78969.html")
def naver_verification():
    return HTMLResponse("naver-site-verification: naverc5036aa02eca57807bf721e44ad78969.html")
