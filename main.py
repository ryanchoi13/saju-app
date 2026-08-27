import datetime
import math
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional
import os
import random

app = FastAPI(title="운세의 신 API", version="26.0.0")

CHEONGAN_HANJA = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
JIJI_HANJA = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

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
    "甲": {"mbti": "대담한 통솔자 (ENTJ형)", "desc": "강한 추진력과 당당한 리더십으로 조직을 이끄는 개척자 사주"},
    "乙": {"mbti": "재기발랄한 활동가 (ENFP형)", "desc": "유연한 적응력과 풍부한 친화력으로 사람의 마음을 얻는 사주"},
    "丙": {"mbti": "자유로운 영혼의 연예인 (ESFP형)", "desc": "태양 같은 열정과 밝은 에너지로 주변을 환하게 밝히는 사주"},
    "丁": {"mbti": "용의주도한 전략가 (ENTJ형)", "desc": "치밀한 기획력과 은근한 카리스마로 목표를 완벽히 쟁취하는 사주"},
    "戊": {"mbti": "청렴결백한 논리주의자 (ISTJ형)", "desc": "묵직한 신뢰감과 흔들리지 않는 원칙으로 책임을 다하는 사주"},
    "己": {"mbti": "세심한 수호자 (ISFJ형)", "desc": "비옥한 땅처럼 주변을 묵묵히 품어주고 실속을 챙기는 사주"},
    "庚": {"mbti": "엄격한 관리자 (ESTJ형)", "desc": "의리와 결단력으로 무장하여 난관을 돌파하는 단호한 실행가 사주"},
    "辛": {"mbti": "용의주도한 완벽주의자 (INTJ형)", "desc": "보석처럼 예리한 감각과 높은 기준을 지닌 냉철한 분석가 사주"},
    "壬": {"mbti": "뜨거운 논쟁을 즐기는 변론가 (ENTP형)", "desc": "바다처럼 넓은 지혜와 임기응변으로 판을 주도하는 아이디어 뱅크 사주"},
    "癸": {"mbti": "선의의 옹호자 (INFJ형)", "desc": "맑은 이슬비처럼 깊은 직관과 통찰력으로 본질을 꿰뚫는 사색가 사주"}
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
    {"name": "0. THE FOOL (바보)", "keyword": "새로운 시작 · 순수한 열정", "fortune_reading": "오랫동안 머뭇거리던 일의 시작 단추를 꿰기에 최적의 날입니다."},
    {"name": "I. THE MAGICIAN (마법사)", "keyword": "창조적 역량 · 완벽한 주도권", "fortune_reading": "지식과 전문 기술이 빛을 발하며 당당한 태도로 판을 리드하게 됩니다."},
    {"name": "XIX. THE SUN (태양)", "keyword": "최고의 성공 · 밝은 활력", "fortune_reading": "모든 근심이 사라지고 목표하던 일이 시원하게 성취되는 최고의 운세입니다."}
]

# [신규] 계절 및 오행 기반 매칭 프리셋 데이터 (현재 월 자동 인식)
SEASONAL_COLOR_OUTFITS = {
    "summer": {  # 여름 (6, 7, 8월)
        "metal": {"color": "스노우 화이트 / 실버 그레이", "style": "화이트 린넨 반팔 셔츠와 실버 메탈 워치"},
        "wood": {"color": "에메랄드 그린 / 올리브 엠버", "style": "민트 톤 쿨맥스 카라티와 라이트 베이지 쇼츠"},
        "fire": {"color": "코랄 핑크 / 로즈 골드", "style": "피치 코랄 린넨 셔츠와 메탈 메쉬 시계"},
        "earth": {"color": "웜 베이지 / 샌드 크림", "style": "크림 톤 반팔 니트와 편안한 린넨 팬츠"},
        "water": {"color": "미드나잇 블루 / 딥 네이비", "style": "네이비 하프 피케티와 실버 뱅글 팔찌"}
    },
    "autumn": {  # 가을 (9, 10, 11월)
        "metal": {"color": "아이보리 / 실버 크롬", "style": "화이트 셔츠에 실버 핀 스프라이트 가디건"},
        "wood": {"color": "딥 그린 / 카키 차콜", "style": "올리브 카키 자켓과 어두운 톤 슬랙스"},
        "fire": {"color": "버건디 / 로즈 브라운", "style": "딥 버건디 니트와 클래식 브라운 수트"},
        "earth": {"color": "카멜 베이지 / 머스터드", "style": "포근한 카멜 트렌치 코트와 크림 슬랙스"},
        "water": {"color": "다크 네이비 / 차콜 블랙", "style": "네이비 블레이저와 깔끔한 인디고 데님"}
    },
    "winter": {  # 겨울 (12, 1, 2월)
        "metal": {"color": "퓨어 화이트 / 쿨 실버", "style": "화이트 울 니트와 실버 펜던트 목걸이"},
        "wood": {"color": "포레스트 그린 / 다크 카키", "style": "딥 그린 울 코트와 깔끔한 블랙 넥워머"},
        "fire": {"color": "딥 레드 / 로즈 골드", "style": "와인 레드 목폴라 니트와 골드 포인트 시계"},
        "earth": {"color": "토프 베이지 / 웜 브라운", "style": "브라운 패딩 자켓과 베이지 울 머플러"},
        "water": {"color": "젯 블랙 / 미드나잇 네이비", "style": "다크 네이비롱 코트와 차콜 톤 머플러"}
    },
    "spring": {  # 봄 (3, 4, 5월)
        "metal": {"color": "크림 화이트 / 라이트 실버", "style": "크림색 옥스포드 셔츠와 메탈 실버 워치"},
        "wood": {"color": "파스텔 민트 / 라이트 올리브", "style": "연민트 가디건과 깔끔한 아이보리 팬츠"},
        "fire": {"color": "라이트 핑크 / 피치 로즈", "style": "Soft 핑크 반집업 니트와 스니커즈"},
        "earth": {"color": "라이트 베이지 / 오트밀", "style": "오트밀 톤 자켓과 편안한 치노 팬츠"},
        "water": {"color": "스카이 블루 / 라이트 네이비", "style": "소라색 린넨 블렌드 셔츠와 차콜 슬랙스"}
    }
}

class SajuRequest(BaseModel):
    name: str
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

def get_current_season(month: int) -> str:
    if month in [6, 7, 8]:
        return "summer"
    elif month in [9, 10, 11]:
        return "autumn"
    elif month in [12, 1, 2]:
        return "winter"
    else:
        return "spring"

def calculate_biorhythm(birth_date: datetime.date, target_date: datetime.date):
    days_lived = (target_date - birth_date).days
    p_val = round(math.sin(2 * math.pi * days_lived / 23) * 100)
    e_val = round(math.sin(2 * math.pi * days_lived / 28) * 100)
    i_val = round(math.sin(2 * math.pi * days_lived / 33) * 100)

    def get_status(val, cycle_name):
        pct = round((val + 100) / 2)
        if val >= 50:
            return {"val": val, "pct": pct, "status": "최고조", "color": "#DC2626", "tip": f"{cycle_name} 에너지가 최고조에 달해 활력이 넘칩니다."}
        elif val > 0:
            return {"val": val, "pct": pct, "status": "상승기", "color": "#EA580C", "tip": f"{cycle_name} 컨디션이 순조롭게 유지됩니다."}
        elif val == 0:
            return {"val": val, "pct": 50, "status": "전환점", "color": "#D97706", "tip": f"기운이 전환되는 구간이니 무리수를 피하세요."}
        elif val > -50:
            return {"val": val, "pct": pct, "status": "하강기", "color": "#2563EB", "tip": f"에너지가 소진되는 구간이니 페이스를 조절하세요."}
        else:
            return {"val": val, "pct": pct, "status": "침체기", "color": "#475569", "tip": f"휴식과 재충전으로 내실을 다지기 좋은 날입니다."}

    return {
        "days_lived": days_lived,
        "physical": get_status(p_val, "신체"),
        "emotional": get_status(e_val, "감성"),
        "intellectual": get_status(i_val, "지성"),
        "overall_summary": "신체와 마음의 생체 에너지가 안정적으로 조화를 이루는 하루입니다."
    }

@app.post("/api/analyze")
def analyze_saju(req: SajuRequest):
    base_date = datetime.date(1900, 1, 1)
    today = datetime.date.today()
    
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
    singang_status = "신약(身弱) 사주" if support_score < 45 else "신강(身强) 사주"

    # [핵심 로직] 현재 계절(월) + 사주 용신/오행 결합 색상 및 코디 자동 매칭
    current_season = get_current_season(today.month)
    preset = SEASONAL_COLOR_OUTFITS.get(current_season, SEASONAL_COLOR_OUTFITS["summer"]).get(day_elem, SEASONAL_COLOR_OUTFITS["summer"]["metal"])

    lucky_color = preset["color"]
    fashion_style = preset["style"]

    daily_seed = today.toordinal() + diff_days
    lucky_number = ["4, 9", "3, 8", "2, 7", "5, 10", "1, 6"][daily_seed % 5]
    lucky_direction = ["정서쪽 (백호 방위)", "정동쪽 (청룡 방위)", "정남쪽 (주작 방위)", "중앙 및 동북쪽", "정북쪽 (현무 방위)"][daily_seed % 5]
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
        "current_age": current_age,
        "singang_status": singang_status,
        "saju_data": {
            "year_pillar": f"{y_cg}{y_jj}", "month_pillar": f"{m_cg}{m_jj}", "day_pillar": f"{d_cg}{d_jj}", "hour_pillar": h_pillar,
            "pillars_detail": pillars_detail, "mbti": user_mbti, "animal_symbol": d_animal, "animal_icon": user_animal_icon,
            "elements": elem_percentages
        },
        "daily_fortune": {
            "score": daily_score, "title": daily_title, "advice": three_stage_advice,
            "lucky_color": lucky_color, "lucky_number": lucky_number, "lucky_direction": lucky_direction,
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
        return {
            "name": f"{key}띠", "icon": ANIMAL_ICONS.get(key, "🐾"), "score": score, "title": "귀인의 조력과 재물운이 합을 이루는 대길의 날",
            "overview": f"오늘 {key}띠는 실력과 결단력이 빛을 발하는 날입니다.",
            "lucky_time": "오후 2시 ~ 4시", "lucky_match": "소띠, 용띠"
        }
    else:
        return {
            "name": key, "icon": "♈", "score": score, "title": "창의적인 영감이 샘솟는 럭키 데이",
            "overview": f"{key}에게 오늘은 내면의 직관이 강력하게 작용하는 날입니다.",
            "focus_content": "유리한 조건의 거래 계약이 성사될 가능성이 매우 높습니다.",
            "lucky_item": "은색 액세서리", "lucky_time": "오전 10시 ~ 12시"
        }

@app.get("/api/daily-tarot")
def get_daily_tarot(slot: int = 1, rand_seed: Optional[str] = None):
    random_idx = random.randint(0, len(TAROT_CARDS) - 1)
    return TAROT_CARDS[random_idx]

@app.post("/api/daewoon-report")
def get_daewoon_report(req: dict):
    user_name = req.get("name", "최정오")
    return {
        "title": "👑 자미두수 평생운세",
        "content": f"<p style='color:#334155; font-size:14.5px; line-height:1.85;'>{user_name}님의 인생은 중장년기에 폭발적인 재물과 명예의 결실을 완성하는 대길 명식입니다.</p>"
    }

@app.post("/api/sinnian-report")
def get_sinnian_report(req: dict):
    user_name = req.get("name", "최정오")
    return {
        "title": "📅 2026 丙午년 총운 & 하반기 월별 가이드",
        "content": f"<p style='color:#334155; font-size:14.5px; line-height:1.85;'>2026 丙午년은 {user_name}님의 역량이 꽃피는 비상의 해입니다. (양력 기준)</p>"
    }

@app.post("/api/gunghap-report")
def get_gunghap_report(req: dict):
    user_name = req.get("name", "최정오")
    partner_name = req.get("partner_name", "상대방")
    return {
        "title": f"💞 {user_name} & {partner_name} 정통 사주 궁합",
        "content": f"<p style='color:#9F1239; font-size:14.5px; line-height:1.85;'>두 분은 서로의 부족한 오행을 채워주는 상호보완형 황금 궁합(94점)입니다.</p>"
    }

@app.post("/api/theme-report")
def get_theme_report(req: dict):
    user_name = req.get("name", "최정오")
    return {
        "title": "💰 평생 테마 감명 리포트",
        "content": f"<p style='color:#78350F; font-size:14.5px; line-height:1.85;'>{user_name}님은 탁월한 기획력과 결단력으로 큰 자산을 다지는 명식입니다.</p>"
    }
