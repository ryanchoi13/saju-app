import datetime
import math
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional
import os
import random

app = FastAPI(title="운세의 신 정통 명리학 엔진 - Mode 2 Production", version="28.0.0")

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

DAY_MBTI_MAP = {
    "甲": {"mbti": "대담한 통솔자 (ENTJ형)", "desc": "강한 추진력과 당당한 리더십으로 조직을 이끄는 개척자 사주", "essence": "거목의 기상"},
    "乙": {"mbti": "재기발랄한 활동가 (ENFP형)", "desc": "유연한 적응력과 풍부한 친화력으로 사람의 마음을 얻는 사주", "essence": "생명력 넘치는 화초"},
    "丙": {"mbti": "자유로운 영혼의 연예인 (ESFP형)", "desc": "태양 같은 열정과 밝은 에너지로 주변을 환하게 밝히는 사주", "essence": "하늘을 비추는 태양"},
    "丁": {"mbti": "용의주도한 전략가 (ENTJ형)", "desc": "치밀한 기획력과 은근한 카리스마로 목표를 완벽히 쟁취하는 사주", "essence": "어둠을 밝히는 촛불"},
    "戊": {"mbti": "청렴결백한 논리주의자 (ISTJ형)", "desc": "묵직한 신뢰감과 흔들리지 않는 원칙으로 책임을 다하는 사주", "essence": "단단하고 광활한 대지"},
    "己": {"mbti": "세심한 수호자 (ISFJ형)", "desc": "비옥한 땅처럼 주변을 묵묵히 품어주고 실속을 챙기는 사주", "essence": "만물을 키워내는 전답"},
    "庚": {"mbti": "엄격한 관리자 (ESTJ형)", "desc": "의리와 결단력으로 무장하여 난관을 돌파하는 단호한 실행가 사주", "essence": "강철과 원석의 결단력"},
    "辛": {"mbti": "용의주도한 완벽주의자 (INTJ형)", "desc": "보석처럼 예리한 감각과 높은 기준을 지닌 냉철한 분석가 사주", "essence": "빛나는 다이아몬드"},
    "壬": {"mbti": "뜨거운 논쟁을 즐기는 변론가 (ENTP형)", "desc": "바다처럼 넓은 지혜와 임기응변으로 판을 주도하는 아이디어 뱅크 사주", "essence": "도도하게 흐르는 큰 강"},
    "癸": {"mbti": "선의의 옹호자 (INFJ형)", "desc": "맑은 이슬비처럼 깊은 직관과 통찰력으로 본질을 꿰뚫는 사색가 사주", "essence": "만물을 적시는 봄비"}
}

ANIMAL_MAP = {"子": "쥐", "丑": "소", "寅": "호랑이", "卯": "토끼", "辰": "용", "巳": "뱀", "午": "말", "未": "양", "申": "원숭이", "酉": "닭", "戌": "개", "亥": "돼지"}
ANIMAL_ICONS = {"쥐": "🐭", "소": "🐮", "호랑이": "🐯", "토끼": "🐰", "용": "🐲", "뱀": "🐍", "말": "🐴", "양": "🐑", "원숭이": "🐵", "닭": "🐔", "개": "🐶", "돼지": "🐷"}

STAR_SIGNS = [
    {"name": "물병자리", "icon": "♒", "period": "01.20 ~ 02.18"},
    {"name": "물고기자리", "icon": "♓", "period": "02.19 ~ 03.20"},
    {"name": "양자리", "icon": "♈", "period": "03.21 ~ 04.19"},
    {"name": "황소자리", "icon": "♉", "period": "04.20 ~ 05.20"},
    {"name": "쌍둥이자리", "icon": "♊", "period": "05.21 ~ 06.21"},
    {"name": "게자리", "icon": "♋", "period": "06.22 ~ 07.22"},
    {"name": "사자자리", "icon": "♌", "period": "07.23 ~ 08.22"},
    {"name": "처녀자리", "icon": "♍", "period": "08.23 ~ 09.22"},
    {"name": "천칭자리", "icon": "♎", "period": "09.23 ~ 10.22"},
    {"name": "전갈자리", "icon": "♏", "period": "10.23 ~ 11.22"},
    {"name": "사수자리", "icon": "♐", "period": "11.23 ~ 12.21"},
    {"name": "염소자리", "icon": "♑", "period": "12.22 ~ 01.19"}
]

TALISMAN_OHEANG_MAP = {
    "wood": {"type": "wood", "title": "사업대성부 (事業亨通符)", "power": "추진력 강화 · 사업 번창 · 승진운", "desc": "사주에 부족한 木의 활력을 불어넣어 막힌 활로를 뚫고 주도권을 쥐게 하는 비급 부적입니다."},
    "fire": {"type": "fire", "title": "소원성취부 (心想事成符)", "power": "열정 회복 · 명예 상승 · 소원 성취", "desc": "사주에 부족한 火의 빛을 밝혀 어둠을 몰아내고 소망을 성취시키는 전통 부적입니다."},
    "earth": {"type": "earth", "title": "금고수호부 (金庫安穩符)", "power": "자산 방어 · 누수 차단 · 재물 안착", "desc": "사주에 부족한 土의 단단한 대지를 마련하여 헛돈 지출을 막아주는 수호 부적입니다."},
    "metal": {"type": "metal", "title": "재물만복부 (萬福大吉符)", "power": "재물 증식 · 금전운 대통 · 투자 대박", "desc": "사주에 부족한 金의 황금 기운을 채워 금전과 복록이 쏟아지게 하는 부적입니다."},
    "water": {"type": "water", "title": "천생화합부 (萬事和合符)", "power": "인연 결속 · 애정 화합 · 인간관계 개선", "desc": "사주에 부족한 水의 지혜와 유대감을 채워 귀인을 이끄는 화합 부적입니다."}
}

TAROT_CARDS = [
    {"name": "0. THE FOOL (바보)", "keyword": "새로운 시작 · 순수한 열정 · 무한한 잠재력", "symbolism": "절벽 끝에 선 순수한 영혼으로 관습에 얽매이지 않는 새로운 여정의 출발을 상징합니다.", "fortune_reading_male": "오랫동안 머뭇거리던 사업이나 프로젝트의 시작 단추를 꿰기에 최적의 날입니다. 주도적인 열정으로 추진하세요.", "fortune_reading_female": "새로운 인연이나 마음속 염원하던 일의 반가운 첫걸음이 시작됩니다. 마음의 직관을 믿어보세요.", "advice": "새로운 제안에 열린 마음을 가지되 발걸음은 가볍고 시선은 신중히 유지하세요.", "action_tip": "떠오르는 아이디어를 즉시 메모하고 먼저 연락을 건네보세요."},
    {"name": "I. THE MAGICIAN (마법사)", "keyword": "창조적 역량 · 완벽한 주도권 · 실력 발휘", "symbolism": "머리 위의 무한대 기호와 제단 위의 4대 원소는 모든 도구를 통제하는 지혜를 뜻합니다.", "fortune_reading_male": "당신의 전문 실력과 언변이 빛을 발합니다. 미팅이나 협상에서 판을 완벽히 리드할 수 있습니다.", "fortune_reading_female": "능숙한 대인관계 능력으로 주변 사람들을 내 편으로 만듭니다. 당당한 카리스마를 발휘하세요.", "advice": "주저하지 말고 자신의 생각을 명확하게 피력하세요.", "action_tip": "중요한 대화에서 본인의 핵심 주장을 명확하게 어필하세요."},
    {"name": "XIX. THE SUN (태양)", "keyword": "최고의 성공 · 밝은 활력 · 승리와 영광", "symbolism": "찬란하게 빛나는 태양과 백마 탄 아이는 어둠을 몰아내는 승리와 기쁨을 상징합니다.", "fortune_reading_male": "모든 근심이 사라지고 목표하던 투자나 계약이 시원하게 성취되는 최고의 운세입니다.", "fortune_reading_female": "내면의 밝은 에너지가 주변에 확산되어 명예와 칭찬, 축하받을 낭보가 찾아옵니다.", "advice": "자신감을 갖고 주저 없이 전진하여 승리의 기쁨을 누리세요.", "action_tip": "야외로 나가 밝은 햇살을 맞으며 활력을 충전하세요."}
]

# [성별 x 연령대 x 8월 여름 계절 맞춤 추천 코디 matrix]
OUTFIT_MATRIX = {
    "male": {
        "young": { # 20~30대 남성
            "wood": "올리브 그린 쿨맥스 반팔 피케티 & 라이트 베이지 반바지",
            "fire": "코랄 핑크 린넨 셔츠 & 화이트 쿨 슬랙스",
            "earth": "웜 크림 톤 반팔 니트 & 차콜 밴딩 스판 팬츠",
            "metal": "화이트 린넨 셔츠 & 실버 메탈 워치 쿨비즈 룩",
            "water": "딥 네이비 스트라이프 반팔 셔츠 & 메탈 팔찌"
        },
        "senior": { # 40대 이상 남성
            "wood": "다크 올리브 린넨 헨리넥 셔츠 & 통풍 차콜 슬랙스",
            "fire": "딥 와인 톤 하프 카라티 & 로즈골드 메탈 워치",
            "earth": "샌드 베이지 린넨 재킷 & 오픈카라 쿨 셔츠",
            "metal": "스노우 화이트 쿨비즈 셔츠 & 실버 가죽 세미 워치",
            "water": "미드나잇 블루 린넨 블레이저 & 크림 드레스 팬츠"
        }
    },
    "female": {
        "young": { # 20~30대 여성
            "wood": "세이지 그린 린넨 원피스 & 실버 뱅글 팔찌",
            "fire": "로즈 핑크 뷔스티에 블라우스 & 라이트 데님",
            "earth": "크림 오프숄더 니트 & 샌드 베이지 와이드 팬츠",
            "metal": "순백색 린넨 스퀘어넥 원피스 & 은은한 실버 펜던트",
            "water": "스카이 블루 린넨 셔츠 & 화이트 하이웨스트 팬츠"
        },
        "senior": { # 40대 이상 여성
            "wood": "올리브 카키 린넨 블라우스 & 통풍 보타닉 슬랙스",
            "fire": "코랄 로즈 엘레강스 린넨 자켓 & 모던 이어링",
            "earth": "웜 베이지 실크 블렌드 셔츠 & 아이보리 쿨 와이드 팬츠",
            "metal": "스노우 화이트 린넨 셋업 & 고급스러운 실버 워치",
            "water": "딥 네이비 린넨 쉬폰 원피스 & 클래식 은 팔찌"
        }
    }
}

class SajuRequest(BaseModel):
    name: str
    gender: Optional[str] = "male"
    year: int
    month: int
    day: int
    calendar_type: Optional[str] = "solar"
    sijin_index: Optional[int] = 5
    is_unknown_time: Optional[bool] = False

@app.get("/")
def serve_home():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return HTMLResponse("<h2>운세의 신 준비 중</h2>")

def calculate_biorhythm(birth_date: datetime.date, target_date: datetime.date):
    days_lived = (target_date - birth_date).days
    p_val = round(math.sin(2 * math.pi * days_lived / 23) * 100)
    e_val = round(math.sin(2 * math.pi * days_lived / 28) * 100)
    i_val = round(math.sin(2 * math.pi * days_lived / 33) * 100)

    def get_status(val, cycle_name):
        pct = round((val + 100) / 2)
        if val >= 50:
            return {"val": val, "pct": pct, "status": "최고조", "color": "#DC2626", "tip": f"{cycle_name} 에너지가 최고조에 달해 최고의 활력을 발휘합니다."}
        elif val > 0:
            return {"val": val, "pct": pct, "status": "상승기", "color": "#EA580C", "tip": f"{cycle_name} 컨디션이 원활하게 유지되고 있습니다."}
        elif val == 0:
            return {"val": val, "pct": 50, "status": "전환점", "color": "#D97706", "tip": f"기운이 전환되는 구간이니 무리수를 피하세요."}
        elif val > -50:
            return {"val": val, "pct": pct, "status": "하강기", "color": "#2563EB", "tip": f"에너지가 소진되는 구간이니 페이스 조절이 필요합니다."}
        else:
            return {"val": val, "pct": pct, "status": "침체기", "color": "#475569", "tip": f"충분한 휴식과 재충전으로 내실을 다지세요."}

    return {
        "days_lived": days_lived,
        "physical": get_status(p_val, "신체"),
        "emotional": get_status(e_val, "감성"),
        "intellectual": get_status(i_val, "지성"),
        "overall_summary": "신체와 정신의 생체 에너지가 균형을 이루어 순조로운 하루입니다."
    }

# [핵심] 대운 순행/역행 정밀 연산 로직
def get_daewoon_info(y_cg: str, gender: str) -> tuple[str, bool]:
    is_yang = y_cg in YANG_STEMS
    is_male = (gender == "male")
    
    if (is_male and is_yang) or (not is_male and not is_yang):
        return ("순행(順行)", True)
    else:
        return ("역행(逆行)", False)

@app.post("/api/analyze")
def analyze_saju(req: SajuRequest):
    base_date = datetime.date(1900, 1, 1)
    today = datetime.date.today()
    gender = req.gender if req.gender in ["male", "female"] else "male"
    
    target_date = datetime.date(req.year, req.month, req.day)
    diff_days = (target_date - base_date).days
    d_cg_idx = diff_days % 10
    d_jj_idx = (diff_days + 10) % 12
    d_cg = CHEONGAN_HANJA[d_cg_idx]
    d_jj = JIJI_HANJA[d_jj_idx]

    year_offset = (req.year - 4) % 60
    y_cg_idx = year_offset % 10
    y_jj_idx = year_offset % 12
    y_cg, y_jj = CHEONGAN_HANJA[y_cg_idx], JIJI_HANJA[y_jj_idx]

    month_adj = req.month
    if req.calendar_type == "lunar":
        month_adj = (req.month + 1)
    elif req.calendar_type == "leap":
        month_adj = (req.month + 2)

    m_jj_idx = (month_adj) % 12
    m_cg_idx = (y_cg_idx % 5 * 2 + 2 + (month_adj - 2)) % 10
    m_cg, m_jj = CHEONGAN_HANJA[m_cg_idx], JIJI_HANJA[m_jj_idx]

    if req.is_unknown_time or req.sijin_index is None or req.sijin_index < 0:
        h_pillar, h_cg, h_jj = "時未詳", "-", "-"
    else:
        h_jj_idx = req.sijin_index
        h_cg_idx = (d_cg_idx % 5 * 2 + h_jj_idx) % 10
        h_cg, h_jj = CHEONGAN_HANJA[h_cg_idx], JIJI_HANJA[h_jj_idx]
        h_pillar = f"{h_cg}{h_jj}"

    d_animal = ANIMAL_MAP.get(d_jj, "개")

    today_diff = (today - base_date).days
    today_cg_idx = today_diff % 10
    today_jj_idx = (today_diff + 10) % 12
    today_cg = CHEONGAN_HANJA[today_cg_idx]
    today_jj = JIJI_HANJA[today_jj_idx]
    today_iljin_str = f"{today_cg}{today_jj}일"

    current_year = today.year
    current_age = current_year - req.year + 1

    pillars_detail = {
        "hour": { "cg": h_cg, "cg_elem": CHEONGAN_ELEMENTS.get(h_cg, "none"), "jj": h_jj, "jj_elem": JIJI_ELEMENTS.get(h_jj, "none"), "jijanggan": JIJANGGAN_FULL_MAP.get(h_jj, []) },
        "day": { "cg": d_cg, "cg_elem": CHEONGAN_ELEMENTS.get(d_cg, "none"), "jj": d_jj, "jj_elem": JIJI_ELEMENTS.get(d_jj, "none"), "jijanggan": JIJANGGAN_FULL_MAP.get(d_jj, []) },
        "month": { "cg": m_cg, "cg_elem": CHEONGAN_ELEMENTS.get(m_cg, "none"), "jj": m_jj, "jj_elem": JIJI_ELEMENTS.get(m_jj, "none"), "jijanggan": JIJANGGAN_FULL_MAP.get(m_jj, []) },
        "year": { "cg": y_cg, "cg_elem": CHEONGAN_ELEMENTS.get(y_cg, "none"), "jj": y_jj, "jj_elem": JIJI_ELEMENTS.get(y_jj, "none"), "jijanggan": JIJANGGAN_FULL_MAP.get(y_jj, []) }
    }

    scores = {"wood": 0.0, "fire": 0.0, "earth": 0.0, "metal": 0.0, "water": 0.0}
    for cg in [y_cg, m_cg, d_cg]:
        scores[CHEONGAN_ELEMENTS[cg]] += 25.0
    if h_cg != "-":
        scores[CHEONGAN_ELEMENTS[h_cg]] += 25.0

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

    # 성별 x 연령대 x 8월 여름 추천 코디 매칭
    age_group = "young" if current_age < 40 else "senior"
    fashion_style = OUTFIT_MATRIX[gender][age_group].get(day_elem, "화이트 린넨 셔츠 & 메탈 워치")

    daily_seed = today.toordinal() + diff_days
    lucky_number = ["4, 9", "3, 8", "2, 7", "5, 10", "1, 6"][daily_seed % 5]
    lucky_direction = ["정서쪽 (백호 방위)", "정동쪽 (청룡 방위)", "정남쪽 (주작 방위)", "중앙 및 동북쪽", "정북쪽 (현무 방위)"][daily_seed % 5]
    lucky_item = ["실버 메탈 액세서리", "가벼운 원목 명함집", "은은한 아로마 오일", "클래식 만년필", "가죽 미니 지갑"][daily_seed % 5]
    recommended_menu = ["도라지차와 고단백 가벼운 식사", "신선한 샐러드와 미온수", "따뜻한 국물 요리와 비타민 과일", "속이 편안한 잡곡밥", "검은콩 두유와 해조류"][daily_seed % 5]
    mindset = "맺고 끊음을 명확히 대화하기"
    action = "오늘 완료해야 할 우선순위 3가지 메모하기"

    daily_title = f"[{today_iljin_str}] 도약과 성취의 하루"
    three_stage_advice = (f"☀️ <strong>오전:</strong> 아이디어를 주변에 공유하고 활발하게 소통하세요.<br>"
                          f"🌤️ <strong>오후:</strong> 본원({d_cg})의 리더십으로 주요 과제를 당당하게 완수하세요.<br>"
                          f"🌙 <strong>저녁:</strong> 원만한 대화로 하루를 가볍게 정리하세요.")
    daily_score = 82 + (daily_seed * 7) % 17

    min_elem = min(elem_percentages, key=elem_percentages.get)
    user_talisman = TALISMAN_OHEANG_MAP.get(min_elem, TALISMAN_OHEANG_MAP["metal"])
    user_mbti = DAY_MBTI_MAP.get(d_cg, {"mbti": "대담한 통솔자 (ENTJ형)", "desc": "목표를 향해 나아가는 전략적 사주"})
    user_animal_icon = ANIMAL_ICONS.get(d_animal, "🐶")

    biorhythm_data = calculate_biorhythm(target_date, today)

    return {
        "user_name": req.name,
        "gender": gender,
        "current_age": current_age,
        "singang_status": singang_status,
        "daewoon_direction": daewoon_dir_name,
        "is_daewoon_forward": is_daewoon_forward,
        "saju_data": {
            "year_pillar": f"{y_cg}{y_jj}", "month_pillar": f"{m_cg}{m_jj}", "day_pillar": f"{d_cg}{d_jj}", "hour_pillar": h_pillar,
            "pillars_detail": pillars_detail, "mbti": user_mbti, "animal_symbol": d_animal, "animal_icon": user_animal_icon,
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

@app.get("/api/zodiac-fortune")
def get_zodiac_fortune(type: str = "zodiac", key: str = "쥐"):
    today = datetime.date.today()
    seed = today.toordinal() + hash(key)
    score = 65 + (seed % 36)
    
    if type == "zodiac":
        years = [2012, 2000, 1988, 1976, 1964]
        zodiac_names = list(ANIMAL_MAP.values())
        z_idx = zodiac_names.index(key) if key in zodiac_names else 0
        adj_years = [y - ((4 - z_idx) % 12) for y in years]
        
        year_advices = [
            {"year_label": f"{str(adj_years[0])[-2:]}년생 ({today.year - adj_years[0] + 1}세)", "tip": "학업과 진로에서 번뜩이는 영감을 발휘해 칭찬을 받는 날입니다."},
            {"year_label": f"{str(adj_years[1])[-2:]}년생 ({today.year - adj_years[1] + 1}세)", "tip": "취업·이직 및 프로젝트에서 중요한 주도권을 쥐게 됩니다."},
            {"year_label": f"{str(adj_years[2])[-2:]}년생 ({today.year - adj_years[2] + 1}세)", "tip": "실속을 차리고 금전적 결실과 성과를 확정 짓는 대길의 타이밍입니다."},
            {"year_label": f"{str(adj_years[3])[-2:]}년생 ({today.year - adj_years[3] + 1}세)", "tip": "귀인의 도움으로 복잡했던 계약이나 사업 협상이 순조롭게 성사됩니다."},
            {"year_label": f"{str(adj_years[4])[-2:]}년생 ({today.year - adj_years[4] + 1}세)", "tip": "무리한 확장보다 내실을 다지며 평온한 화목을 누리는 날입니다."}
        ]
        return {
            "name": f"{key}띠", "icon": ANIMAL_ICONS.get(key, "🐾"), "score": score, "title": "귀인의 조력과 재물운이 합을 이루는 대길의 날",
            "overview": f"오늘 {key}띠는 실력과 결단력이 빛을 발하는 날입니다. 큰 흐름을 보고 추진하면 큰 성취가 따릅니다.",
            "year_tips": year_advices, "lucky_time": "오후 2시 ~ 4시", "lucky_match": "소띠, 용띠"
        }
    else:
        star_item = next((s for s in STAR_SIGNS if s["name"] == key), STAR_SIGNS[0])
        return {
            "name": star_item["name"], "icon": star_item["icon"], "period": star_item["period"], "score": score,
            "title": "창의적인 영감이 샘솟는 럭키 데이",
            "overview": f"{star_item['name']}에게 오늘은 내면의 직관이 강력하게 작용하는 날입니다.",
            "focus_badge": "💰 오늘 가장 중요한 재물운", "focus_content": "유리한 조건의 거래 계약이 성사될 가능성이 매우 높습니다.",
            "lucky_item": "은색 액세서리", "lucky_time": "오전 10시 ~ 12시"
        }

@app.get("/api/daily-tarot")
def get_daily_tarot(slot: int = 1, rand_seed: Optional[str] = None):
    random_idx = random.randint(0, len(TAROT_CARDS) - 1)
    return TAROT_CARDS[random_idx]

# [Mode 2 풀버전] 자미두수 평생운세: 성별 x 대운 순행/역행 정밀 분기
@app.post("/api/daewoon-report")
def get_daewoon_report(req: dict):
    user_name = req.get("name", "최정오")
    gender = req.get("gender", "male")
    age = req.get("age", 49)
    age_decade = (age // 10) * 10
    start_age = age_decade + 3
    end_age = start_age + 9

    gender_str = "남성(男命)" if gender == "male" else "여성(女命)"
    spouse_star = "재성(財星 / 아내·재물)" if gender == "male" else "관성(官星 / 남편·명예)"

    return {
        "title": f"👑 자미두수 평생운세 ({gender_str})",
        "content": f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div>
                <div style="border-left: 4px solid #2D6A4F; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #2D6A4F; font-weight: 800;">Chapter 1. 성별 및 평생 대운맥</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #0F172A; margin-top: 2px;">
                        🌐 {user_name}님({gender_str})의 대운 흐름 및 생애 주도권
                    </h4>
                </div>
                <p style="color: #475569; margin-bottom: 10px;">
                    자미두수 명반과 성별 명식을 교차 감명한 결과, {user_name}님은 본원의 기운과 {spouse_star}의 흐름이 견고하게 조화를 이루어 중장년기에 폭발적인 부와 명예의 결실을 완성하는 <strong>'만성대기(晩成大器)형 정통 사주'</strong>입니다.
                </p>
                <div style="background: #FEF3C7; border: 1.5px solid #FCD34D; border-radius: 8px; padding: 10px 12px;">
                    <p style="font-weight: 800; color: #78350F; font-size: 14.5px; margin-bottom: 2px;">🔥 [현재 10년 대운 구간: {start_age}세 ~ {end_age}세]</p>
                    <p style="color: #92400E; font-size: 13.5px; font-weight: 600;">
                        일생일대에서 가장 강력한 천운의 파도가 솟구치는 최고 전성기입니다. 본인이 직접 주도권을 쥐고 설계한 판에서 자산과 사회적 지위가 폭발적으로 도약합니다.
                    </p>
                </div>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #D97706; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #D97706; font-weight: 800;">Chapter 2. 성공 및 개운 비책</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #78350F; margin-top: 2px;">
                        💡 {gender_str} 맞춤 자산 및 관계 수성법
                    </h4>
                </div>
                <p style="color: #78350F; line-height: 1.85;">
                    {spouse_star}의 기운을 보존하기 위해 문서와 계약은 반드시 직접 검증하고, 귀인과의 신뢰를 바탕으로 고정적 현금 흐름을 구축하세요.
                </p>
            </div>
        </div>
        """
    }

# [Mode 2 풀버전] 2026 신년운세 & 토정비결
@app.post("/api/sinnian-report")
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
                        🔥 2026 丙午년(붉은 말의 해) {user_name}님의 도약 총운
                    </h4>
                </div>
                <p style="color: #7F1D1D; line-height: 1.85;">
                    2026년은 강렬한 불(火)의 기운이 어둠을 걷어내고 대지를 환하게 비추는 丙午년입니다. {user_name}님의 명식과 조화를 이루어 그동안 수면 아래에서 준비해 온 역량이 화려하게 꽃을 피우며, 막혀 있던 활로가 시원하게 뚫리는 <strong>'비상(飛翔)의 한 해'</strong>가 됩니다.
                </p>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 8px;">
                    <div style="border-left: 4px solid #2D6A4F; padding-left: 10px;">
                        <span style="font-size: 12px; color: #2D6A4F; font-weight: 800;">Chapter 2. 12개월 정밀 토정비결</span>
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

# [Mode 2 풀버전] 정통 사주 궁합
@app.post("/api/gunghap-report")
def get_gunghap_report(req: dict):
    user_name = req.get("name", "최정오")
    partner_name = req.get("partner_name", "상대방")
    relation = req.get("relation", "연인/결혼")

    return {
        "title": f"💞 {user_name} & {partner_name} 정통 사주 궁합 ({relation})",
        "content": f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div style="background: linear-gradient(135deg, #FFF1F2 0%, #FFE4E6 100%); border: 1.5px solid #FECDD3; border-radius: 14px; padding: 14px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-size: 12px; color: #BE123C; font-weight: 800;">정통 오행 상생 궁합 지수</span>
                    <h3 style="font-size: 18px; font-weight: 900; color: #9F1239; margin-top: 2px;">94점 (천생연분 대길합)</h3>
                </div>
                <div style="font-size: 32px;">💖</div>
            </div>

            <div>
                <div style="border-left: 4px solid #E11D48; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #E11D48; font-weight: 800;">Chapter 1. 두 사람의 기운과 인연의 깊이</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #881337; margin-top: 2px;">
                        🔗 {user_name}님과 {partner_name}님의 천간·지지 상생 조화
                    </h4>
                </div>
                <p style="color: #9F1239; line-height: 1.85;">
                    {user_name}님의 사주에 부족하거나 필요한 기운을 {partner_name}님이 풍부하게 품어주고 있어, 함께할수록 서로의 운이 솟구치고 부족한 기운이 채워지는 <strong>'상호보완형 황금 궁합'</strong>입니다.
                </p>
            </div>
        </div>
        """
    }

# [Mode 2 풀버전] 4대 테마운세 (성별 분기 연동)
@app.post("/api/theme-report")
def get_theme_report(req: dict):
    theme = req.get("theme", "wealth")
    sub_opt = req.get("sub_option", "기본")
    user_name = req.get("name", "최정오")
    gender = req.get("gender", "male")
    
    titles = {
        "wealth": "💰 평생 재물운",
        "love": f"💖 평생 애정운 ({sub_opt})",
        "business": f"🏢 사업·직업운 ({sub_opt})",
        "health": "🌿 평생 건강운"
    }

    gender_term = "아내/재물(財星)" if gender == "male" else "남편/명예(官星)"

    content = f"""
    <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
        <div style="border-left: 4px solid #D97706; padding-left: 10px;">
            <span style="font-size: 12px; color: #D97706; font-weight: 800;">성별 심층 감명 기준: {gender_term}</span>
            <h4 style="font-size: 16.5px; font-weight: 800; color: #78350F; margin: 3px 0 6px;">{user_name}님의 평생 맞춤 솔루션</h4>
            <p style="color: #92400E; font-size: 14.5px; line-height: 1.85;">
                선택하신 상태({sub_opt})와 성별 명식을 결합 감명한 결과, 본인의 주도권과 전문성을 바탕으로 큰 부와 안정된 결실을 완성하는 명식입니다.
            </p>
        </div>
    </div>
    """
    
    return {
        "title": titles.get(theme, "심층 리포트"),
        "content": content
    }
