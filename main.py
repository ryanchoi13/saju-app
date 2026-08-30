import datetime
import math
import os
import random
import sqlite3
from typing import Optional, List
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, Response
from pydantic import BaseModel

app = FastAPI(title="달하 (DALHA) - 정통 명리학 & 점성술 엔진", version="43.5.0")

DB_FILE = "dalha.db"

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
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
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS wardrobe_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        category VARCHAR(50),
        colors VARCHAR(150),
        materials VARCHAR(150),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    conn.commit()
    conn.close()

init_db()

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
    "wood": { "type": "wood", "title": "사업대성부 (事業亨通符)", "power": "추진력 강화 · 사업 번창 · 승진운", "desc": "사주에 부족한 木(목)의 생명력을 불어넣어 막힌 활로를 뚫고 주도권을 쥐게 하는 비급 부적입니다." },
    "fire": { "type": "fire", "title": "소원성취부 (心想事成符)", "power": "열정 회복 · 명예 상승 · 소원 성취", "desc": "사주에 부족한 火(화)의 찬란한 빛을 밝혀 염원하던 소망을 일사천리로 성취시키는 부적입니다." },
    "earth": { "type": "earth", "title": "금고수호부 (金庫安穩符)", "power": "자산 방어 · 누수 차단 · 재물 안착", "desc": "사주에 부족한 土(토)의 단단한 대지를 마련하여 헛돈 지출을 막고 자산을 지켜주는 부적입니다." },
    "metal": { "type": "metal", "title": "재물만복부 (萬福大吉符)", "power": "재물 증식 · 금전운 대통 · 투자 대박", "desc": "사주에 부족한 金(금)의 황금 기운을 채워 사방에서 금전과 복록이 쏟아지게 하는 전통 부적입니다." },
    "water": { "type": "water", "title": "천생화합부 (萬事和合符)", "power": "인연 결속 · 애정 화합 · 귀인 유대", "desc": "사주에 부족한 水(수)의 지혜를 채워 엇갈린 인연을 묶어주고 귀인의 조력을 이끄는 부적입니다." }
}

TAROT_CARDS = [
    {
        "name": "I. THE MAGICIAN (마법사)", "keyword": "탁월한 창조력 · 완벽한 주도권 · 만사형통",
        "symbolism": "머리 위의 무한대 기호와 제단 위의 4대 원소는 모든 상황을 내 뜻대로 통제하고 현실로 구현할 수 있는 완성된 지혜를 뜻합니다.",
        "reading_male": "전문 역량과 논리적인 언변이 빛을 발합니다. 중요한 회의나 계약 협상에서 상대방을 내 페이스로 리드할 수 있습니다.",
        "reading_female": "능숙한 대인관계 조율력과 따뜻한 카리스마로 주변 사람들을 내 아군으로 만듭니다. 의견을 당당하게 피력하세요.",
        "action_guide": "핵심 강점을 자신감 있게 표현하고 주도적으로 대화의 흐름을 이끌어가세요."
    },
    {
        "name": "0. THE FOOL (바보)", "keyword": "새로운 여정의 서막 · 순수한 직관 · 무한한 잠재력",
        "symbolism": "벼랑 끝에서 발걸음을 내딛는 청년과 흰 개는 과거의 관습과 두려움을 벗어던진 순수한 영혼의 새로운 도약을 상징합니다.",
        "reading_male": "오랫동안 망설이던 프로젝트나 신규 투자의 첫 단추를 꿰기에 최상의 날입니다. 본인의 결단력을 믿고 추진하세요.",
        "reading_female": "새로운 인연이나 소망에 뜻밖의 기회가 찾아옵니다. 첫 느낌을 따를 때 대길합니다.",
        "action_guide": "새로운 제안에 열린 마음을 갖고 떠오르는 아이디어를 즉시 메모하세요."
    },
    {
        "name": "XIX. THE SUN (태양)", "keyword": "최고의 번영 · 찬란한 영광 · 축하받을 낭보",
        "symbolism": "백마를 탄 아이와 해바라기는 어둠을 걷어내고 승리와 축복을 맞이하는 절정의 운세를 의미합니다.",
        "reading_male": "막혀 있던 자금 흐름이나 프로젝트의 난관이 시원하게 뚫리며 명예와 실속을 동시에 쟁취하는 날입니다.",
        "reading_female": "내면의 밝은 에너지가 주변을 환하게 밝히며 축하받을 소식과 함께 화목이 넘칩니다.",
        "action_guide": "햇살을 받으며 산책을 즐기고 긍정적인 미소로 주변과 소통하세요."
    }
]

DAILY_OUTFITS_POOL = {
    "male": {
        "young": ["흰색 카라 반팔티 & 베이지 슬랙스", "네이비 린넨 셔츠 & 메탈 시계", "스카이블루 반팔 셔츠 & 그레이 팬츠", "블랙 무지 반팔티 & 와이드 슬랙스"],
        "senior": ["흰색 린넨 셔츠 & 가죽 세미 워치", "네이비 쿨 셔츠 & 단정한 차콜 팬츠", "연베이지 셔츠 & 클래식 시계", "다크 올리브 린넨 셔츠 & 편안한 팬츠"]
    },
    "female": {
        "young": ["흰색 린넨 블라우스 & 라이트 데님", "연한 하늘색 셔츠 & 화이트 슬랙스", "베이지 톤 반팔 니트 & 롱 스커트", "네이비 린넨 원피스 & 미니멀 목걸이"],
        "senior": ["아이보리 린넨 블라우스 & 은은한 시계", "네이비 쉬폰 블라우스 & 베이지 슬랙스", "소프트 핑크 린넨 자켓 & 진주 귀걸이", "베이지 톤 오픈카라 셔츠 & 편안한 팬츠"]
    }
}

LUCKY_ITEMS_POOL = ["실버 메탈 시계", "가죽 카드 지갑", "클래식 만년필", "은은한 시트러스 향수", "블루라이트 차단 안경", "산뜻한 손수건"]
LUCKY_DIRECTIONS_POOL = ["정서쪽 (백호 방위)", "정동쪽 (청룡 방위)", "정남쪽 (주작 방위)", "정북쪽 (현무 방위)", "동남쪽 (생기 방위)", "서북쪽 (금전 방위)"]
LUCKY_MENUS_POOL = ["속이 편안한 영양 솥밥", "신선한 샐러드와 차가운 물", "따뜻한 전복죽과 과일", "도라지차와 가벼운 정식", "시원한 메밀소바"]
MINDSETS_POOL = ["원칙을 지키며 유연하게 대처하기", "상대의 말을 경청하고 공감하기", "맺고 끊음을 명확히 하기", "새로운 제안에 열린 마음 갖기", "서두르지 않고 꼼꼼히 확인하기"]
ACTIONS_POOL = ["오늘 끝낼 우선순위 3가지 메모하기", "아침 5분간 가벼운 스트레칭하기", "점심 식사 후 10분간 햇볕 쬐며 산책하기", "책상 위 불필요한 서류 정리하기", "고마웠던 지인에게 안부 문자 보내기"]

STAR_FORTUNE_DETAILS = {
    "양자리": { "title": "과감한 결단력과 새로운 활로", "overview": "직관과 실행력이 최고조에 달하는 날입니다. 주저하던 일을 추진하기에 최적입니다.", "badge": "🔥 오늘 강력한 추진운", "focus": "압도적인 주도권으로 미뤄둔 제안을 성사시킵니다.", "item": "레드 포인트 소품", "time": "오전 09시 ~ 11시" },
    "황소자리": { "title": "안정적인 실속과 재물 결실", "overview": "침착한 안목이 빛을 발하며 재정 흐름이 단단하게 자리 잡는 날입니다.", "badge": "💰 오늘 중요한 재물운", "focus": "자산 관리나 지출 절감에서 실속 있는 이득을 봅니다.", "item": "가죽 카드 지갑", "time": "오후 01시 ~ 03시" },
    "쌍둥이자리": { "title": "반짝이는 영감과 유쾌한 소통", "overview": "두뇌 회전이 빠르고 언변이 좋아 사람들을 내 편으로 끌어들이는 날입니다.", "badge": "🗣️ 오늘 빛나는 소통운", "focus": "미팅이나 대화 자리에서 든든한 조력자를 만납니다.", "item": "스마트 워치", "time": "오전 11시 ~ 오후 01시" },
    "게자리": { "title": "내면의 평온과 소중한 화합", "overview": "따뜻한 공감 능력으로 오해를 풀고 신뢰를 회복하는 하루입니다.", "badge": "🏡 오늘 편안한 가족운", "focus": "가까운 지인과의 대화에서 뜻밖의 힐링을 얻습니다.", "item": "은은한 향수", "time": "저녁 07시 ~ 09시" },
    "사자자리": { "title": "당당한 리더십과 성과", "overview": "자신감 넘치는 태도가 주변을 이끌며 리더로서 진가를 입증합니다.", "badge": "👑 오늘 돋보이는 명예운", "focus": "프로젝트를 리드하며 탁월한 성과를 인정받습니다.", "item": "골드 메탈 소품", "time": "오후 02시 ~ 04시" },
    "처녀자리": { "title": "빈틈없는 분석과 업무 완수", "overview": "디테일을 짚어내는 감각으로 복잡한 문제를 명쾌하게 정리합니다.", "badge": "📊 오늘 확실한 성과운", "focus": "계획 수립과 서류 검토에서 실수를 완벽히 차단합니다.", "item": "깔끔한 메모장", "time": "오전 10시 ~ 12시" },
    "천칭자리": { "title": "균형 잡힌 조율과 파트너십", "overview": "상대방의 마음을 정확히 파악하여 윈-윈 관계를 이끌어냅니다.", "badge": "🤝 오늘 유리한 협력운", "focus": "의견 대립을 매끄럽게 중재하여 계약을 매듭짓습니다.", "item": "클래식 안경", "time": "오후 04시 ~ 06시" },
    "전갈자리": { "title": "예리한 통찰과 기회 포착", "overview": "이면의 흐름을 꿰뚫어 보며 결정적인 승부수를 던지기 좋습니다.", "badge": "🎯 오늘 강력한 승부운", "focus": "남들이 놓친 틈새시장을 발견해 실리를 챙깁니다.", "item": "블랙 가죽 키링", "time": "오후 05시 ~ 07시" },
    "사수자리": { "title": "넓은 시야와 새로운 도약", "overview": "미래를 향한 원대한 비전과 도전 의욕이 샘솟는 하루입니다.", "badge": "🚀 오늘 활발한 확장운", "focus": "새로운 분야의 공부나 비즈니스 구상에서 실마리를 잡습니다.", "item": "가벼운 텀블러", "time": "오후 01시 ~ 03시" },
    "염소자리": { "title": "성실한 노력과 지위 안착", "overview": "꾸준히 쌓아온 노력이 결과물로 전환되며 신뢰를 한몸에 받습니다.", "badge": "📈 오늘 단단한 승진운", "focus": "상급자로부터 능력을 인정받아 권한이 격상됩니다.", "item": "원목 명함집", "time": "오전 08시 ~ 10시" },
    "물병자리": { "title": "독창적인 발상과 혁신", "overview": "틀에 얽매이지 않는 신선한 아이디어가 주변에 영감을 줍니다.", "badge": "💡 오늘 빛나는 기획운", "focus": "정체된 일에 새로운 방식을 적용해 돌파구를 엽니다.", "item": "실버 링", "time": "오후 03시 ~ 05시" },
    "물고기자리": { "title": "풍부한 감성과 따뜻한 인연", "overview": "마음이 이끄는 대로 행동할 때 뜻밖의 행운과 만남이 이어집니다.", "badge": "💖 오늘 설레는 애정운", "focus": "마음이 잘 통하는 귀인을 만나 깊은 유대를 형성합니다.", "item": "실버 목걸이", "time": "오후 06시 ~ 08시" }
}

# 20대 세분화 색상 및 소재 5대 오행 맵핑
DETAILED_COLOR_ELEM_MAP = {
    "화이트": "metal", "아이보리/크림": "metal", "베이지": "earth", "카멜/브라운": "earth",
    "블랙": "water", "차콜": "water", "그레이": "metal", "실버": "metal",
    "골드": "metal", "레드": "fire", "와인/버건디": "fire", "핑크": "fire",
    "코랄/오렌지": "fire", "옐로우": "earth", "머스터드": "earth", "올리브/카키": "wood",
    "민트/라임": "wood", "그린": "wood", "스카이블루": "wood", "네이비": "water"
}

DETAILED_MATERIAL_ELEM_MAP = {
    "면/린넨": "wood", "실크/쉬폰": "fire", "가죽/세무": "earth",
    "메탈/금속": "metal", "데님": "water", "니트/울": "earth"
}

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

    def get_status(val):
        pct = round((val + 100) / 2)
        if val >= 50: return {"val": val, "pct": pct, "status": "최고조"}
        elif val > 0: return {"val": val, "pct": pct, "status": "상승기"}
        elif val == 0: return {"val": val, "pct": 50, "status": "전환점"}
        elif val > -50: return {"val": val, "pct": pct, "status": "하강기"}
        else: return {"val": val, "pct": pct, "status": "침체기"}

    is_critical_day = abs(p_val) <= 5 or abs(e_val) <= 5 or abs(i_val) <= 5
    if is_critical_day:
        overall_advice = "바이오리듬이 영점(0%) 전환선에 걸쳐 기운이 바뀌는 민감한 날입니다. 중요한 결정이나 무리한 일정은 한 번 더 점검하세요."
    elif p_val >= 30 and e_val >= 30:
        overall_advice = "신체와 감성 에너지가 충만합니다. 적극적인 활동과 미팅에서 최고의 성과를 거둘 수 있습니다."
    elif i_val >= 30:
        overall_advice = "두뇌 회전과 직관이 번뜩이는 날입니다. 기획, 문서 검토, 학습에 집중할 때 효율이 극대화됩니다."
    elif p_val < 0 and e_val < 0 and i_val < 0:
        overall_advice = "3대 에너지가 재충전 구간에 있습니다. 무리한 약속보다는 편안한 휴식으로 내실을 다지세요."
    else:
        overall_advice = "몸과 마음의 에너지가 안정된 균형을 유지하고 있습니다. 평소 루틴을 차분히 지켜나가기 좋은 하루입니다."

    return {
        "days_lived": days_lived, "physical": get_status(p_val),
        "emotional": get_status(e_val), "intellectual": get_status(i_val),
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

    is_reverse_day = (daily_hash % 8 == 0)
    reverse_color_map = {
        "wood": "코랄/오렌지 & 화이트",
        "fire": "네이비/스카이블루 & 실버",
        "earth": "그린/올리브 & 아이보리",
        "metal": "핑크/와인 & 골드",
        "water": "옐로우/머스터드 & 베이지"
    }
    reverse_color = reverse_color_map.get(day_elem, "화사한 코랄/오렌지 & 베이지")
    
    if is_reverse_day:
        reverse_tip = f"✦ 오늘 일진이 평소 피하던 <strong>[{reverse_color}]</strong>을 완벽히 소화해 주는 황금의 날입니다! 아껴둔 밝은 아이템을 과감히 매치해보세요."
    else:
        reverse_tip = f"오늘의 일진은 사주 본원({d_cg})과 상생하는 <strong>차분한 뉴트럴 톤</strong>과 <strong>가죽/메탈 소품</strong>을 곁들일 때 기운이 가장 안정됩니다."

    daily_score = 68 + (daily_hash % 31)
    today_diff = (today - base_date).days
    today_cg, today_jj = CHEONGAN_HANJA[today_diff % 10], JIJI_HANJA[(today_diff + 10) % 12]
    
    score_status_word = "대길(大吉)과 도약의 하루" if daily_score >= 88 else ("순조로운 화합과 발전의 하루" if daily_score >= 75 else "내실을 다지고 신중을 기할 하루")
    daily_title = f"[{today_cg}{today_jj}일] {score_status_word}"

    AM_ADVICES = ["아이디어를 공유하며 주변과 활발히 소통하세요.", "하루의 핵심 우선순위를 정하고 차분히 시작하세요.", "새로운 제안이 오면 긍정적인 시각으로 검토하세요."]
    PM_ADVICES = [f"본원({d_cg})의 리더십으로 핵심 과제를 완수하세요.", "협력 파트너와의 조율에서 주도권을 쥐고 진행하세요.", "실속을 차리며 계약 및 약속을 확실히 매듭지으세요."]
    EVE_ADVICES = ["가볍게 하루 일과를 정리하고 편안히 충전하세요.", "지친 몸과 마음을 따뜻한 차 한잔으로 달래세요.", "내일의 계획을 메모하며 평온한 저녁을 보내세요."]

    am_text = AM_ADVICES[daily_hash % len(AM_ADVICES)]
    pm_text = PM_ADVICES[(daily_hash // 3) % len(PM_ADVICES)]
    eve_text = EVE_ADVICES[(daily_hash // 7) % len(EVE_ADVICES)]

    three_stage_advice = (f"☀️ <strong>오전:</strong> {am_text}<br>"
                          f"🌤️ <strong>오후:</strong> {pm_text}<br>"
                          f"🌙 <strong>저녁:</strong> {eve_text}")

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
            "talisman": user_talisman, "is_reverse_day": is_reverse_day, "reverse_tip": reverse_tip
        },
        "biorhythm": biorhythm_data
    }

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
    relation: Optional[str] = "선택안함"

class WardrobeAddRequest(BaseModel):
    user_id: int
    category: str
    colors: List[str]
    materials: List[str]

def fetch_user_wardrobe(user_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, category, colors, materials, created_at FROM wardrobe_items WHERE user_id = ? ORDER BY id DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    items = []
    for r in rows:
        items.append({
            "id": r["id"],
            "category": r["category"],
            "colors": r["colors"].split(",") if r["colors"] else [],
            "materials": r["materials"].split(",") if r["materials"] else [],
            "created_at": r["created_at"]
        })
    return items

# --- API 엔드포인트 ---

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

        wardrobe_list = fetch_user_wardrobe(user_id)

        return {
            "status": "existing_user",
            "user_id": user_id,
            "coin_balance": user["coin_balance"],
            "profile": {
                "name": user["name"], "gender": user["gender"], "birth_year": user["birth_year"],
                "birth_month": user["birth_month"], "birth_day": user["birth_day"],
                "calendar_type": user["calendar_type"], "sijin_index": user["sijin_index"]
            },
            "saju_analysis": saju_payload,
            "unlocked_reports": unlocked_list,
            "wardrobe_items": wardrobe_list
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
                "name": req.name, "gender": gender_val, "birth_year": b_year,
                "birth_month": b_month, "birth_day": b_day, "calendar_type": cal_type, "sijin_index": 5
            }
        }

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
            "name": user["name"], "gender": user["gender"], "birth_year": user["birth_year"],
            "birth_month": user["birth_month"], "birth_day": user["birth_day"],
            "calendar_type": user["calendar_type"], "sijin_index": user["sijin_index"]
        },
        "saju_analysis": saju_payload
    }

# 내 옷장 아이템 추가 API (20대 세분화 색상 및 복수 소재 맵핑)
@app.post("/api/wardrobe/add")
def add_wardrobe_item(req: WardrobeAddRequest):
    conn = get_db()
    cursor = conn.cursor()
    colors_str = ",".join(req.colors)
    mats_str = ",".join(req.materials)
    cursor.execute("""
    INSERT INTO wardrobe_items (user_id, category, colors, materials)
    VALUES (?, ?, ?, ?)
    """, (req.user_id, req.category, colors_str, mats_str))
    conn.commit()
    conn.close()
    return {"status": "success", "wardrobe_items": fetch_user_wardrobe(req.user_id)}

# 내 옷장 아이템 삭제 API
@app.delete("/api/wardrobe/delete/{item_id}")
def delete_wardrobe_item(item_id: int, user_id: int):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM wardrobe_items WHERE id = ? AND user_id = ?", (item_id, user_id))
    conn.commit()
    conn.close()
    return {"status": "success", "wardrobe_items": fetch_user_wardrobe(user_id)}

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

    current_age = datetime.date.today().year - user["birth_year"] + 1
    user_data = {
        "name": user["name"], "gender": user["gender"], "age": current_age,
        "sub_option": req.sub_option, "partner_name": req.partner_name, "relation": req.relation
    }

    report_title = ""
    report_content = ""

    if req.report_key == "daewoon":
        res = get_daewoon_report(user_data)
        report_title, report_content = res["title"], res["content"]
    elif req.report_key == "sinnian":
        res = get_sinnian_report(user_data)
        report_title, report_content = res["title"], res["content"]
    elif req.report_key == "gunghap":
        res = get_gunghap_report(user_data)
        report_title, report_content = res["title"], res["content"]
    elif req.report_key in ["wealth", "love", "business", "health"]:
        user_data["theme"] = req.report_key
        res = get_theme_report(user_data)
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
        "status": "success", "new_balance": new_balance,
        "title": report_title, "content": report_content, "unlocked_reports": unlocked_list
    }

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

@app.get("/api/zodiac-fortune")
def get_zodiac_fortune(type: str = "zodiac", key: str = "쥐"):
    today = datetime.date.today()
    seed = today.toordinal() + hash(key)
    score = 70 + (seed % 29)
    
    if type == "zodiac":
        years = [2012, 2000, 1988, 1976, 1964]
        zodiac_names = list(ANIMAL_MAP.values())
        z_idx = zodiac_names.index(key) if key in zodiac_names else 0
        adj_years = [y - ((4 - z_idx) % 12) for y in years]
        
        year_advices = [
            {"year_label": f"{str(adj_years[0])[-2:]}년생 ({today.year - adj_years[0] + 1}세)", "tip": "학업과 진로에서 영감을 발휘해 인정을 받는 날입니다."},
            {"year_label": f"{str(adj_years[1])[-2:]}년생 ({today.year - adj_years[1] + 1}세)", "tip": "주요 프로젝트에서 결정적 주도권을 쥐게 됩니다."},
            {"year_label": f"{str(adj_years[2])[-2:]}년생 ({today.year - adj_years[2] + 1}세)", "tip": "실속을 차리고 금전적 결실을 확정 짓는 타이밍입니다."},
            {"year_label": f"{str(adj_years[3])[-2:]}년생 ({today.year - adj_years[3] + 1}세)", "tip": "귀인의 도움으로 복잡했던 협상이 성사됩니다."},
            {"year_label": f"{str(adj_years[4])[-2:]}년생 ({today.year - adj_years[4] + 1}세)", "tip": "무리한 확장보다 내실을 다지며 가문의 화목을 누립니다."}
        ]
        return {
            "name": f"{key}띠", "icon": ANIMAL_ICONS.get(key, "🐾"), "score": score, "title": "귀인의 조력과 재물운이 합을 이루는 대길의 날",
            "overview": f"오늘 {key}띠는 실력과 결단력이 빛을 발하는 날입니다. 큰 흐름을 보고 추진하면 성취가 따릅니다.",
            "year_tips": year_advices, "lucky_time": "오후 2시 ~ 4시", "lucky_match": "소띠, 용띠"
        }
    else:
        star_item = next((s for s in STAR_SIGNS if s["name"] == key), STAR_SIGNS[0])
        detail = STAR_FORTUNE_DETAILS.get(key, STAR_FORTUNE_DETAILS["양자리"])
        return {
            "name": star_item["name"], "icon": star_item["icon"], "period": star_item["period"],
            "score": score, "title": detail["title"], "overview": detail["overview"],
            "focus_badge": detail["badge"], "focus_content": detail["focus"],
            "lucky_item": detail["item"], "lucky_time": detail["time"]
        }

@app.get("/api/daily-tarot")
def get_daily_tarot(slot: int = 1):
    return TAROT_CARDS[random.randint(0, len(TAROT_CARDS) - 1)]

def get_daewoon_report(req: dict):
    user_name = req.get("name", "회원")
    gender = req.get("gender", "male")
    age = req.get("age", 35)

    start_age = (age // 10) * 10 + 3
    if age < start_age:
        start_age -= 10
    end_age = start_age + 9

    p1_start, p1_end = start_age, start_age + 2
    p2_start, p2_end = start_age + 3, start_age + 5
    p3_start, p3_end = start_age + 6, end_age

    gender_str = "남성(男命)" if gender == "male" else "여성(女命)"
    spouse_star = "재성(財星 / 아내·실물자산)" if gender == "male" else "관성(官星 / 남편·명예관운)"

    if age < 30:
        stage_name = "청년 도약기 (기반 확립)"
        focus_goal = "전문 역량 축적 및 핵심 인맥 구축"
        p1_desc = f"{p1_start}세 ~ {p1_end}세는 진로의 방향성을 확립하고 내실 있는 실무 감각을 다지는 시기입니다."
        p2_desc = f"{p2_start}세 ~ {p2_end}세는 본인의 실력이 조직에서 인정받으며 기회가 열리는 성장기입니다."
        p3_desc = f"{p3_start}세 ~ {p3_end}세는 30대 황금기로 넘어가기 위한 확고한 발판을 마련하는 결실기입니다."
    elif age < 50:
        stage_name = "중장년 전성기 (황금 결실기)"
        focus_goal = "실질 자산 증식 및 사회적 주도권 장악"
        p1_desc = f"{p1_start}세 ~ {p1_end}세는 기존 판도를 재편하고 주체가 되는 사업/투자 포트폴리오를 구축한 전환기였습니다."
        p2_desc = f"{p2_start}세 ~ {p2_end}세는 귀인의 조력을 바탕으로 자산 볼륨이 팽창하는 가속 구간입니다."
        p3_desc = f"{p3_start}세 ~ {p3_end}세는 분산된 자금을 우량 자산으로 안착시키고 확고한 지위를 완성하는 대운의 절정기입니다."
    else:
        stage_name = "원숙 결실기 (자산 수성 및 가문 번영)"
        focus_goal = "안정적 현금 흐름 완성 및 명예로운 번영"
        p1_desc = f"{p1_start}세 ~ {p1_end}세는 불필요한 위험 자산을 정돈하고 안정적인 자산 방어 체계를 수립하는 시기입니다."
        p2_desc = f"{p2_start}세 ~ {p2_end}세는 쌓아온 인망을 토대로 후배/자녀의 조력자이자 멘토로 권위를 누립니다."
        p3_desc = f"{p3_start}세 ~ {p3_end}세는 평생 일군 결실을 평온히 누리며 가문의 유산을 안착시키는 구간입니다."

    return {
        "title": f"👑 자미두수 평생운세 ({gender_str})",
        "content": f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div>
                <div style="border-left: 4px solid #2D6A4F; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #2D6A4F; font-weight: 800;">Chapter 1. 평생 대운맥 및 생애 주도권</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #0F172A; margin-top: 2px;">
                        {user_name}님({gender_str} · 현재 {age}세)의 거시적 생애 운명 흐름
                    </h4>
                </div>
                <p style="color: #475569; margin-bottom: 12px;">
                    자미두수 명반을 정밀 감명한 결과, {user_name}님은 단계적 배움과 역량 축적을 거쳐 중장년기에 강력한 {spouse_star}의 결실을 맺는 <strong>'만성대기(晩成大器)형 명식'</strong>입니다.
                </p>

                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; overflow: hidden;">
                    <div style="padding: 12px 14px; border-bottom: 1px solid #E2E8F0;">
                        <p style="font-weight: 600; color: #475569; font-size: 13.5px; margin-bottom: 2px;">[유년기 : 근본 기틀 형성기]</p>
                        <p style="color: #64748B; font-size: 13px;">남다른 탐구심과 도덕적 가치관을 단단히 다지던 기초 형성기입니다.</p>
                    </div>
                    <div style="padding: 12px 14px; border-bottom: 1px solid #E2E8F0;">
                        <p style="font-weight: 600; color: #475569; font-size: 13.5px; margin-bottom: 2px;">[청년기 : 역량 축적 및 실전기]</p>
                        <p style="color: #64748B; font-size: 13px;">실무 전문성을 다지고 인맥과 실전 감각의 뼈대를 구축하는 시기입니다.</p>
                    </div>
                    <div style="background: #FEF3C7; padding: 12px 14px; border-bottom: 1px solid #FCD34D;">
                        <p style="font-weight: 800; color: #78350F; font-size: 14px; margin-bottom: 2px;">[{stage_name} (*현재 위치 / {start_age}세 ~ {end_age}세)]</p>
                        <p style="color: #92400E; font-size: 13px; font-weight: 600;">
                            <strong>{user_name}님의 핵심 승부처 구간입니다.</strong> {focus_goal}을(를) 목표로 본인이 직접 주도권을 쥘 때 성과가 극대화됩니다.
                        </p>
                    </div>
                    <div style="padding: 12px 14px;">
                        <p style="font-weight: 600; color: #475569; font-size: 13.5px; margin-bottom: 2px;">[말년기 : 태평성대 및 가문 번영기]</p>
                        <p style="color: #64748B; font-size: 13px;">축적한 자산과 인망을 토대로 안락한 노후와 가문의 번영을 누립니다.</p>
                    </div>
                </div>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #D97706; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #D97706; font-weight: 800;">Chapter 2. 현재 10년 대운 집중 감명</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #78350F; margin-top: 2px;">
                        {user_name}님의 {start_age}세 ~ {end_age}세 3단계 로드맵
                    </h4>
                </div>

                <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; overflow: hidden;">
                    <div style="padding: 12px 14px; border-bottom: 1px dashed #CBD5E1;">
                        <span style="font-weight: 700; color: #1E3A8A; font-size: 14px; display: block; margin-bottom: 3px;">[1단계] {p1_start}세 ~ {p1_end}세 : 기반 구축기</span>
                        <p style="color: #475569; font-size: 13px; line-height: 1.65;">{p1_desc}</p>
                    </div>
                    <div style="padding: 12px 14px; border-bottom: 1px dashed #CBD5E1;">
                        <span style="font-weight: 700; color: #065F46; font-size: 14px; display: block; margin-bottom: 3px;">[2단계] {p2_start}세 ~ {p2_end}세 : 확장 및 증식기</span>
                        <p style="color: #475569; font-size: 13px; line-height: 1.65;">{p2_desc}</p>
                    </div>
                    <div style="background: #FFFBEB; padding: 12px 14px;">
                        <span style="font-weight: 800; color: #78350F; font-size: 14px; display: block; margin-bottom: 3px;">[3단계] {p3_start}세 ~ {p3_end}세 : 대운의 총결실 (*현재)</span>
                        <p style="color: #92400E; font-size: 13px; line-height: 1.65; font-weight: 600;">{p3_desc}</p>
                    </div>
                </div>
            </div>
        </div>
        """
    }

def get_sinnian_report(req: dict):
    user_name = req.get("name", "최정오")
    gender = req.get("gender", "male")
    gender_str = "남성" if gender == "male" else "여성"

    seed = sum(ord(c) for c in user_name) + (17 if gender == "male" else 31)

    MONTH_NARRATIVES = [
        {"gua": "지천태(地天泰) 괘", "story": f"{user_name}님의 명식에 丙火의 온기가 스며들며 얼어붙었던 환경이 풀리는 상서로운 달입니다. 주변과의 소통이 원활해지고 정체되었던 일에서 새로운 해결의 실마리를 찾게 됩니다. 장기적인 플랜의 초석을 다지기에 가장 이상적인 시기입니다.", "opp": "새해 첫 출발이 대길하여 신규 사업 및 프로젝트 착수에 최적입니다.", "warn": "초반 성취에 자만하지 말고 세부 규정을 차분히 정비하세요."},
        {"gua": "수천수(水天需) 괘", "story": f"내실을 기하고 에너지를 비축해야 하는 관망의 달입니다. 겉보기에는 진행이 다소 더뎌 보일 수 있으나 더 큰 도약을 위한 도움닫기 구간입니다. 충동적인 투자나 급격한 변경은 피하고 전문성을 연마하며 때를 기다리세요.", "opp": "실력과 내실을 다지며 시장 흐름을 관망할 때 이익이 보존됩니다.", "warn": "서두른 결정이나 충동구매를 피하고 하루 이틀 시일을 두세요."},
        {"gua": "천화동인(天火同人) 괘", "story": f"귀인의 조력이 강하게 작용하여 뜻을 같이하는 동반자가 나타나는 달입니다. {user_name}님의 매력과 리더십이 빛을 발하여 대인관계에서 큰 신뢰를 얻고 협상에서 주도권을 잡을 수 있습니다.", "opp": "귀인의 조력이 닿아 인간관계와 직무에서 강력한 협력자가 나타납니다.", "warn": "이견 조율 시 감정적 대응을 피하고 데이터로 설득하세요."},
        {"gua": "풍천소축(風天小畜) 괘", "story": f"작은 결실들이 차곡차곡 쌓여 실속을 챙기는 실리 추구의 달입니다. 일상의 루틴을 철저히 지키며 불필요한 누수를 막아야 합니다. 금융 자산의 기틀을 다지고 지출을 효율적으로 통제할 때 재물운이 안정됩니다.", "opp": "작은 성과가 차곡차곡 쌓여 종잣돈의 기틀이 단단해집니다.", "warn": "무리한 대출이나 투자는 지양하고 현금 유동성을 확보하세요."},
        {"gua": "화천대유(火天大有) 괘", "story": f"★올해 상반기 최고의 황금기입니다! 그동안 땀 흘려 준비해 온 일들이 찬란한 결실로 이어지며 큰 보상과 명예를 얻게 됩니다. 부동산, 계약, 투자 회수 등에서 기대 이상의 이익이 발생합니다.", "opp": "대길의 재물운! 부동산/투자/계약에서 큰 결실을 맺습니다.", "warn": "성과를 독식하려 하지 말고 함께한 동료들에게 따뜻하게 베푸세요."},
        {"gua": "천풍구(天風姤) 괘", "story": f"뜻밖의 제안이나 새로운 분야로의 활로가 활짝 열리는 역동적인 달입니다. 생각지 못했던 인연을 통해 귀중한 정보를 얻거나 기회가 찾아옵니다. 실질적인 조건을 꼼꼼히 따져보는 안목이 중요합니다.", "opp": "새로운 제안과 신규 프로젝트의 반가운 활로가 열립니다.", "warn": "계약서의 독소 조항과 구두 약속을 면밀히 검증하세요."},
        {"gua": "천수송(天水訟) 괘", "story": f"복잡했던 업무 체계를 정리하고 불필요한 시비를 털어내는 체질 개선의 달입니다. 사소한 오해가 생길 수 있으나 유연한 태도로 대화하면 오히려 더 깊은 신뢰를 쌓는 계기가 됩니다.", "opp": "기존의 복잡했던 업무 체계를 깔끔히 정리하고 체질을 개선합니다.", "warn": "사소한 언쟁이나 시비수를 피하기 위해 공감 화법을 유지하세요."},
        {"gua": "풍지관(風地觀) 괘", "story": f"상반기 달려온 궤적을 돌아보고 하반기 도약을 위한 전략을 가다듬는 성찰의 달입니다. 심신의 여유를 찾고 건강 상태를 점검하기에 좋습니다. 차분히 계획을 재정비할 때 확실한 승기를 잡을 수 있습니다.", "opp": "성과를 점검하고 하반기 도약을 위한 전략을 세우기에 최적입니다.", "warn": "체력 저하와 피로를 방지하기 위해 충분한 수면과 휴식을 챙기세요."},
        {"gua": "산지박(山地剝) 괘", "story": f"군더더기를 깎아내고 본질에 집중해야 하는 실속 다지기의 달입니다. 무리한 확장보다 본인이 가장 잘하는 핵심 역량에 집중해야 합니다. 불필요한 고정비를 청산하기에 좋습니다.", "opp": "불필요한 고정비와 낭비 요소를 말끔히 청산하여 실속을 챙깁니다.", "warn": "무리한 확장보다 기존 고객 및 핵심 업무 관리에 집중하세요."},
        {"gua": "지뢰복(地雷復) 괘", "story": f"★올해 하반기 최고의 승부처입니다! 침체되었던 기운이 완전히 걷히고 강력한 상승 기류를 타게 됩니다. 승진, 대형 계약 수주, 투자 회수 등에서 눈부신 성취를 거두며 위상이 크게 격상됩니다.", "opp": "강력한 승부처! 승진, 수주, 투자 회수에서 결정적 주도권을 쥡니다.", "warn": "기회가 올 때 주저하지 말고 과감한 결단력으로 밀어붙이세요."},
        {"gua": "수뢰준(水雷屯) 괘", "story": f"내년을 위한 새로운 씨앗을 뿌리고 미래 먹거리를 준비하는 준비의 달입니다. 자격증 취득, 자기계발 등에 공을 들이면 훗날 큰 자산으로 되돌아옵니다. 기본기를 탄탄히 다지세요.", "opp": "새로운 아이템이나 자격/학업의 씨앗을 뿌려 미래를 준비하기 좋습니다.", "warn": "경험자의 조언을 경청하여 불필요한 시행착오를 사전에 방지하세요."},
        {"gua": "지화명이(地火明夷) 괘", "story": f"한 해 동안 일군 풍성한 결실을 확정 짓고 가문과 가족의 화목을 누리는 평온한 달입니다. 노고에 대한 정당한 보상을 받으며 주변과 따뜻한 온정을 나누게 됩니다. 건강을 잘 챙기세요.", "opp": "풍성한 결실을 확정 짓고 가문과 가족의 화목을 누립니다.", "warn": "연말 과음과 과로를 피하고 따뜻한 온기로 건강을 챙기세요."}
    ]

    monthly_guides = []
    for m_idx in range(1, 13):
        m_hash = (seed * 13 + m_idx * 37) % 100
        score = 68 + (m_hash % 31)
        item_idx = (seed + m_idx) % len(MONTH_NARRATIVES)
        pool_item = MONTH_NARRATIVES[item_idx]

        monthly_guides.append({
            "m": f"{m_idx}월", "score": score, "gua": pool_item["gua"],
            "story": pool_item["story"], "opp": pool_item["opp"], "warn": pool_item["warn"]
        })

    sorted_months = sorted(monthly_guides, key=lambda x: x["score"], reverse=True)
    top1_month, top1_score = sorted_months[0]["m"], sorted_months[0]["score"]
    top2_month, top2_score = sorted_months[1]["m"], sorted_months[1]["score"]

    months_html = "".join([f"""
        <div style="background: #F8FAFC; border-radius: 12px; padding: 14px 16px; margin-bottom: 12px; border: 1px solid #E2E8F0;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
                <span style="font-weight: 800; color: #0F172A; font-size: 15px;">{item['m']} 세운 가이드</span>
                <span style="font-size: 12px; background: #FEF3C7; color: #92400E; font-weight: 800; padding: 2px 8px; border-radius: 6px;">이달의 운세 점수: {item['score']}점</span>
            </div>
            <p style="font-size: 11.5px; color: #64748B; margin-bottom: 10px; font-weight: 400;">(주역 본괘 : {item['gua']})</p>
            <p style="color: #334155; font-size: 13.5px; line-height: 1.75; margin-bottom: 10px;">
                {item['story']}
            </p>
            <div style="border-top: 1px dashed #CBD5E1; padding-top: 8px; display: flex; flex-direction: column; gap: 4px;">
                <p style="color: #065F46; font-size: 13px; line-height: 1.55;">
                    <strong>✨ 기회의 순간:</strong> {item['opp']}
                </p>
                <p style="color: #991B1B; font-size: 13px; line-height: 1.55;">
                    <strong>⚠️ 주의할 처세:</strong> {item['warn']}
                </p>
            </div>
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
                        🔥 2026 丙午년 {user_name}님의 도약 총운
                    </h4>
                </div>
                <p style="color: #7F1D1D; line-height: 1.85;">
                    2026년은 강렬한 불(火)의 기운이 대지를 환하게 비추는 丙午년입니다. {user_name}님의 명식과 조화를 이루어 준비해 온 역량이 꽃을 피우며 활로가 뚫리는 비상의 한 해가 됩니다.
                </p>
            </div>
            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>
            <div>
                <div style="border-left: 4px solid #F59E0B; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #D97706; font-weight: 800;">Chapter 2. 소망 성취 골든타임</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #78350F; margin-top: 2px;">
                        🎯 성취 확률 92%의 황금 시기
                    </h4>
                </div>
                <p style="color: #78350F; line-height: 1.85;">
                    올해의 핵심 소망은 <strong>양력 {top1_month}({top1_score}점)과 {top2_month}({top2_score}점)</strong>에 천운을 만나 일사천리로 성취됩니다.
                </p>
            </div>
            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>
            <div>
                <div style="border-left: 4px solid #2D6A4F; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #2D6A4F; font-weight: 800;">Chapter 3. 월별 세운 흐름</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #0F172A; margin-top: 2px;">
                        📜 1월부터 12월까지 정밀 세운
                    </h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 4px;">{months_html}</div>
            </div>
        </div>
        """
    }

def get_gunghap_report(req: dict):
    user_name = req.get("name", "최정오")
    partner_name = req.get("partner_name", "상대방")
    relation = req.get("relation", "연인/결혼")
    if relation == "선택안함" or not relation:
        relation = "인연/조화"

    seed = sum(ord(c) for c in user_name) + sum(ord(c) for c in partner_name)
    total_score = 88 + (seed % 11)
    love_score = 90 + ((seed * 3) % 9)
    trust_score = 89 + ((seed * 7) % 10)
    synergy_score = 91 + ((seed * 11) % 8)

    return {
        "title": f"💞 {user_name} & {partner_name} 정통 사주 궁합 ({relation})",
        "content": f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div style="background: linear-gradient(135deg, #FFF1F2 0%, #FFE4E6 100%); border: 1.5px solid #FECDD3; border-radius: 14px; padding: 16px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 12px; color: #BE123C; font-weight: 800;">정통 오행 상생 궁합 지수 ({relation})</span>
                    <h3 style="font-size: 20px; font-weight: 900; color: #9F1239; margin-top: 2px;">{total_score}점 (천생연분 대길합)</h3>
                    <p style="font-size: 11.5px; color: #E11D48; margin-top: 2px;">애정합 {love_score}% · 신뢰합 {trust_score}% · 상생 시너지 {synergy_score}%</p>
                </div>
                <div style="font-size: 36px;">💖</div>
            </div>
            <div>
                <div style="border-left: 4px solid #E11D48; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #E11D48; font-weight: 800;">Chapter 1. 두 사람의 기운과 인연의 깊이</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #881337; margin-top: 2px;">🔗 {user_name}님과 {partner_name}님의 상생 조화</h4>
                </div>
                <p style="color: #9F1239; line-height: 1.85;">
                    {user_name}님의 사주에 부족한 기운을 {partner_name}님이 풍부하게 품어주고 있어 만날수록 자존감이 회복되는 상호보완형 인연입니다.
                </p>
            </div>
            <div style="background: #F8FAFC; border-radius: 10px; padding: 12px; border-left: 3.5px solid #BE123C;">
                <p style="font-weight: 800; color: #0F172A; font-size: 14px; margin-bottom: 4px;">💡 두 사람을 위한 맞춤 처세 팁:</p>
                <p style="color: #475569; font-size: 13.5px;">사소한 의견 차이가 생길 때는 즉각적인 반론보다 3초간 경청 후 상대방의 입장을 인정해 주는 화법을 구사할 때 갈등 없이 백년해로합니다.</p>
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
                    {user_name}님의 사주는 겉으로 드러난 화려함보다 실속 있게 현금과 실물 자산을 차곡차곡 축적하는 전형적인 황금 금고형 명식입니다.
                </p>
            </div>
        </div>
        """
    elif theme == "business":
        content = f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div style="border-left: 4px solid #2563EB; padding-left: 10px;">
                <span style="font-size: 12px; color: #2563EB; font-weight: 800;">Chapter 1. 직무/사업 맞춤 운세 ({sub_opt})</span>
                <h4 style="font-size: 16.5px; font-weight: 800; color: #1E3A8A; margin: 3px 0 6px;">🎯 전문 직무 승부처 & 로드맵</h4>
                <p style="color: #1E40AF; font-size: 14.5px; line-height: 1.85;">
                    {user_name}님의 명식은 상황을 주도적으로 돌파하는 전략가형 기질을 품고 있어 본인이 주도권을 쥔 환경에서 큰 성과를 거둡니다.
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
                    {user_name}님의 사주는 신뢰와 따뜻한 배려가 결합할 때 애정의 기운이 평생 동안 번창하는 온화한 명식입니다.
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
                    두한족열(머리는 시원하게, 발은 따뜻하게)의 기본 수칙을 유지하면 에너지가 고갈되지 않습니다.
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

@app.get("/naverc5036aa02eca57807bf721e44ad78969.html")
def naver_verification():
    return HTMLResponse("naver-site-verification: naverc5036aa02eca57807bf721e44ad78969.html")

@app.get("/google888b184f07770663.html")
def google_verification():
    return HTMLResponse("google-site-verification: google888b184f07770663.html")
