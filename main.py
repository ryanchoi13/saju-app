import datetime
import math
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional
import os
import random

app = FastAPI(title="운세의 신 정통 명리학 엔진", version="26.0.0")

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
    "甲": {"mbti": "대담한 통솔자 (ENTJ형)", "desc": "강한 추진력과 당당한 리더십으로 조직을 이끄는 개척자 사주", "essence": "거목(巨木)의 기상"},
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
    "fire": {"type": "fire", "title": "소원성취부 (心想事成符)", "power": "열정 회복 · 명예 상승 · 소원 성취", "desc": "사주에 부족한 火의 빛을 밝혀 오랫동안 염원하던 소망을 일사천리로 성취시키는 전통 부적입니다."},
    "earth": {"type": "earth", "title": "금고수호부 (金庫安穩符)", "power": "자산 방어 · 누수 차단 · 재물 안착", "desc": "사주에 부족한 土의 단단한 대지를 마련하여 헛돈 지출을 막고 평생의 자산을 지켜주는 수호 부적입니다."},
    "metal": {"type": "metal", "title": "재물만복부 (萬福大吉符)", "power": "재물 증식 · 금전운 대통 · 투자 대박", "desc": "사주에 부족한 金의 황금 기운을 채워 사방에서 금전과 복록이 쏟아지게 하는 전통 경면주사 부적입니다."},
    "water": {"type": "water", "title": "천생화합부 (萬事和合符)", "power": "인연 결속 · 애정 화합 · 인간관계 개선", "desc": "사주에 부족한 水의 지혜와 유대감을 채워 엇갈린 인연을 묶어주고 귀인을 이끄는 화합 부적입니다."}
}

TAROT_CARDS = [
    {"name": "0. THE FOOL (바보)", "keyword": "새로운 시작 · 순수한 열정 · 무한한 잠재력", "symbolism": "절벽 끝에 선 순수한 영혼으로 관습에 얽매이지 않는 새로운 여정의 출발을 상징합니다.", "fortune_reading": "오랫동안 머뭇거리던 일의 시작 단추를 꿰기에 최적의 날입니다. 직관을 따를 때 예상 밖의 통로가 열립니다.", "advice": "새로운 제안에 열린 마음을 가지되 발걸음은 가볍고 시선은 신중히 유지하세요.", "action_tip": "떠오르는 아이디어를 즉시 메모하고 먼저 연락을 건네보세요."},
    {"name": "I. THE MAGICIAN (마법사)", "keyword": "창조적 역량 · 완벽한 주도권 · 실력 발휘", "symbolism": "머리 위의 무한대 기호와 제단 위의 4대 원소는 모든 도구를 통제하는 지혜를 뜻합니다.", "fortune_reading": "지식과 언변, 전문 기술이 빛을 발하는 날입니다. 당당한 태도로 판을 리드하기에 최적입니다.", "advice": "미팅이나 보고에서 주도적으로 의견을 제시하고 실력을 드러내세요.", "action_tip": "중요한 대화에서 본인의 핵심 주장을 명확하게 피력하세요."},
    {"name": "II. THE HIGH PRIESTESS (여사제)", "keyword": "깊은 통찰 · 직관과 혜안 · 침묵의 지혜", "symbolism": "흑과 백의 기둥 사이에 앉아 본질적 진실과 영적인 직관을 상징합니다.", "fortune_reading": "겉으로 드러난 말보다 상대방의 숨은 의도나 상황의 이면을 꿰뚫어 보는 혜안이 극대화됩니다.", "advice": "성급하게 반응하기보다는 차분히 경청하고 심사숙고하세요.", "action_tip": "조용한 장소에서 생각을 차분히 정리하는 시간을 가지세요."},
    {"name": "III. THE EMPRESS (여황제)", "keyword": "풍요와 번영 · 따뜻한 포용 · 결실의 기쁨", "symbolism": "풍성한 곡식과 석류 장식은 모성적 사랑과 물질적·정신적 풍요로움을 상징합니다.", "fortune_reading": "그동안 공들여 준비한 일에서 만족스러운 성과와 금전적 보상이 주어지는 날입니다.", "advice": "주변 사람들에게 넉넉한 마음으로 베풀면 더 큰 행운이 돌아옵니다.", "action_tip": "맛있는 식사를 대접하거나 가까운 이에게 감사 인사를 전하세요."},
    {"name": "XIX. THE SUN (태양)", "keyword": "최고의 성공 · 밝은 활력 · 승리와 영광", "symbolism": "찬란하게 빛나는 태양과 백마 탄 아이는 어둠을 몰아내는 승리와 기쁨을 상징합니다.", "fortune_reading": "모든 근심이 사라지고 목표하던 일이 시원하게 성취되는 최고의 운세입니다.", "advice": "자신감을 갖고 주저 없이 전진하여 승리의 기쁨을 누리세요.", "action_tip": "야외로 나가 밝은 햇살을 맞으며 활력을 충전하세요."}
]

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
            return {"val": val, "pct": 50, "status": "전환점", "color": "#D97706", "tip": f"기운이 바뀌는 전환점이므로 무리수를 피하세요."}
        elif val > -50:
            return {"val": val, "pct": pct, "status": "하강기", "color": "#2563EB", "tip": f"에너지가 소진되는 구간이니 페이스 조절이 필요합니다."}
        else:
            return {"val": val, "pct": pct, "status": "침체기", "color": "#475569", "tip": f"충분한 휴식과 재충전으로 내실을 다지세요."}

    p_res = get_status(p_val, "신체")
    e_res = get_status(e_val, "감성")
    i_res = get_status(i_val, "지성")

    avg_val = (p_val + e_val + i_val) / 3
    if avg_val > 30:
        summary = "심신의 3대 생체 에너지가 모두 고조되어 적극적인 도전에 최적인 날입니다."
    elif avg_val > -20:
        summary = "신체와 정신의 균형이 안정적으로 유지되어 순조로운 하루입니다."
    else:
        summary = "무리한 일정보다 휴식과 마인드 컨트롤로 충전하기 좋은 날입니다."

    return {
        "days_lived": days_lived,
        "physical": p_res,
        "emotional": e_res,
        "intellectual": i_res,
        "overall_summary": summary
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

    stem_diff = (today_cg_idx - d_cg_idx) % 10
    shipshin_names = ["비견(比肩)", "겁재(劫財)", "식신(食神)", "상관(傷官)", "편재(偏財)", "정재(正財)", "편관(偏官)", "정관(正官)", "편인(偏印)", "정인(正印)"]
    today_shipshin = shipshin_names[stem_diff]

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

    if h_jj != "-":
        for item in JIJANGGAN_FULL_MAP.get(h_jj, []):
            scores[item["elem"]] += item["weight"] * 1.0

    total_score = sum(scores.values())
    elem_percentages = { k: round((v / total_score) * 100, 1) for k, v in scores.items() }

    day_elem = CHEONGAN_ELEMENTS[d_cg]
    support_score = scores.get(day_elem, 0)
    insoeng_map = {"wood": "water", "fire": "wood", "earth": "fire", "metal": "earth", "water": "metal"}
    support_score += scores.get(insoeng_map.get(day_elem, ""), 0)
    singang_status = "신약(身弱) 사주" if support_score < 45 else ("신강(身强) 사주" if support_score > 65 else "중화(中和) 사주")

    daily_seed = today.toordinal() + diff_days
    
    colors_pool = ["스노우 화이트 / 실버 그레이", "에메랄드 그린 / 포레스트 올리브", "크림슨 레드 / 로즈 골드", "웜 베이지 / 머스터드", "미드나잇 블루 / 네이비"]
    numbers_pool = ["4, 9", "3, 8", "2, 7", "5, 10", "1, 6"]
    directions_pool = ["정서쪽 (백호 방위)", "정동쪽 (청룡 방위)", "정남쪽 (주작 방위)", "중앙 및 동북쪽", "정북쪽 (현무 방위)"]
    styles_pool = ["각 잡힌 화이트 셔츠와 메탈 시계", "편안한 린넨 셔츠 / 그린 톤 캐주얼", "포인트 니트 / 클래식 타이", "포근한 브라운 톤 재킷", "세련된 네이비 셋업"]
    menus_pool = ["도라지차, 신선한 견과류와 고단백 요리", "신선한 샐러드와 미온수", "따뜻한 국물 요리와 비타민 과일", "속이 편안한 잡곡밥과 발효식품", "검은콩 두유와 해조류"]
    mindsets_pool = ["맺고 끊음을 명확히 대화하기", "새로운 시도에 열린 마음 갖기", "열정을 당당하게 피력하기", "약속을 철저히 지키며 중심 잡기", "상대의 말을 경청하고 공감하기"]
    actions_pool = ["오늘 완료해야 할 우선순위 3가지 메모하기", "아침 시간 가벼운 스트레칭하기", "점심 후 햇볕 10분간 쬐기", "주변 책상과 지갑 깨끗이 정리하기", "취침 전 따뜻한 족욕과 명상하기"]

    lucky_color = colors_pool[daily_seed % len(colors_pool)]
    lucky_number = numbers_pool[(daily_seed + 1) % len(numbers_pool)]
    lucky_direction = directions_pool[(daily_seed + 2) % len(directions_pool)]
    fashion_style = styles_pool[(daily_seed + 3) % len(styles_pool)]
    recommended_menu = menus_pool[(daily_seed + 4) % len(menus_pool)]
    mindset = mindsets_pool[(daily_seed + 5) % len(mindsets_pool)]
    action = actions_pool[(daily_seed + 6) % len(actions_pool)]

    daily_title = f"[{today_iljin_str}] 도약과 성취의 하루"
    three_stage_advice = (f"☀️ <strong>오전:</strong> 아이디어를 주변에 공유하고 활발하게 소통하며 기틀을 잡으세요.<br>"
                          f"🌤️ <strong>오후:</strong> 본원({d_cg})의 리더십으로 추진 중인 주요 과제를 당당하게 완성하세요.<br>"
                          f"🌙 <strong>저녁:</strong> 원만한 대화로 하루를 마무리하고 편안한 수면을 취하세요.")
    daily_score = 82 + (daily_seed * 7) % 17

    min_elem = min(elem_percentages, key=elem_percentages.get)
    user_talisman = TALISMAN_OHEANG_MAP.get(min_elem, TALISMAN_OHEANG_MAP["metal"])
    user_mbti = DAY_MBTI_MAP.get(d_cg, {"mbti": "대담한 통솔자 (ENTJ형)", "desc": "강한 추진력과 당당한 리더십으로 조직을 이끄는 개척자 사주", "essence": "거목의 기상"})
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
            "title": "창의적인 영감과 반가운 기회가 샘솟는 럭키 데이",
            "overview": f"{star_item['name']}에게 오늘은 내면의 직관이 강력하게 작용하는 날입니다.",
            "focus_badge": "💰 오늘 가장 중요한 재물운", "focus_content": "유리한 조건의 거래 계약이 성사될 가능성이 매우 높습니다.",
            "lucky_item": "은색 액세서리", "lucky_time": "오전 10시 ~ 12시"
        }

@app.get("/api/daily-tarot")
def get_daily_tarot(slot: int = 1, rand_seed: Optional[str] = None):
    random_idx = random.randint(0, len(TAROT_CARDS) - 1)
    return TAROT_CARDS[random_idx]

@app.post("/api/daewoon-report")
def get_daewoon_report(req: dict):
    user_name = req.get("name", "최정오")
    age = req.get("age", 49)
    age_decade = (age // 10) * 10
    start_age = age_decade + 3
    end_age = start_age + 9

    return {
        "title": "👑 자미두수 평생운세",
        "content": f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div>
                <div style="border-left: 4px solid #2D6A4F; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #2D6A4F; font-weight: 800;">Chapter 1. 평생 대운맥</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #0F172A; margin-top: 2px;">
                        🌐 {user_name}님의 생애 4대 주기별 거시적 운명 흐름
                    </h4>
                </div>
                <p style="color: #475569; margin-bottom: 10px;">
                    자미두수 명반과 사주 원국을 교차 감명한 결과, {user_name}님의 인생은 초년의 치열한 배움을 거쳐 중장년기에 폭발적인 재물과 명예의 결실을 완성하는 <strong>'만성대기(晩成大器)형 거목의 명식'</strong>입니다.
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
                        <p style="font-weight: 800; color: #78350F; font-size: 14.5px; margin-bottom: 2px;">🔥 [중장년기 (*현재 위치 / 40세 ~ 59세) : 황금 결실기]</p>
                        <p style="color: #92400E; font-size: 13.5px; font-weight: 600;">
                            <strong>{user_name}님 인생 일대에서 가장 강력한 천운의 파도가 솟구치는 최고 전성기 구간입니다.</strong> 본인이 직접 주도권을 쥐고 설계한 판에서 자산 규모와 사회적 영향력이 수직 상승합니다.
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
                    <span style="font-size: 12px; color: #D97706; font-weight: 800;">Chapter 2. 현재 10년 대운</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #78350F; margin-top: 2px;">
                        📈 Q. {user_name}님의 현재 10년 대운({start_age}세 ~ {end_age}세) 핵심 결실은?
                    </h4>
                </div>
                <p style="color: #78350F; line-height: 1.85; margin-bottom: 10px;">
                    현재 지나고 계신 대운맥은 사주 본원에 '재성(財星)'과 '귀인(貴人)'이 강력하게 결합하는 절정기입니다. 남에게 끌려다니지 않고 본인의 통솔력으로 사업, 투자, 조직을 리드할 때 성공 확률이 95% 이상으로 치솟습니다.
                </p>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14px; color: #475569;">
                    <p>• <strong>{start_age}세 ~ {start_age+2}세 (기반 재편기):</strong> 흩어져 있던 지출을 정돈하고 실물 자산 중심 종잣돈 포트폴리오를 단단히 압축한 시기.</p>
                    <p style="color: #B45309; font-weight: 800;">• <strong>{start_age+3}세 ~ {start_age+6}세 (대운 정점기 / ★현재 {age}세 위치):</strong> 귀인의 결정적 조력과 함께 직위·자산 규모가 퀀텀 점프하는 일생일대의 승부처입니다.</p>
                    <p>• <strong>{start_age+7}세 ~ {end_age}세 (자산 수성기):</strong> 성과를 시스템 수익(부동산, 배당, 지식재산권)으로 고정시키며 차기 대운으로 연착륙합니다.</p>
                </div>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #DC2626; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #DC2626; font-weight: 800;">Chapter 3. 불운 방어</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #991B1B; margin-top: 2px;">
                        🛡️ Q. 대운 기간 중 반드시 경계해야 할 암초와 방어책은?
                    </h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14px; color: #451A03; line-height: 1.8;">
                    <p>• <strong>1. 구두 약속의 함정 (문서화 필수):</strong> 운세가 강할 때는 주변에서 달콤한 제안이 쏟아집니다. 친분 관계라 할지라도 지분, 계약, 금전 거래는 반드시 공증 및 문서화해야 관재수를 완벽히 차단합니다.</p>
                    <p>• <strong>2. 과도한 독단 경계:</strong> 본인의 직관이 뛰어나지만 중요한 의사결정 시 법률·세무·금융 전문가의 2차 검증을 거칠 때 자산 누수가 0%로 수렴합니다.</p>
                </div>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #F59E0B; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #D97706; font-weight: 800;">Chapter 4. 실전 개운 솔루션</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #78350F; margin-top: 2px;">
                        🔥 이번 10년 대운({start_age}세~{end_age}세) 맞춤 3대 개운(開運) 실천 비책
                    </h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 10px; font-size: 14px; line-height: 1.8; color: #451A03;">
                    <p>• <strong>[재물 및 자산 운용]:</strong> 단기 단타 투자보다 실물 부동산, 우량 배당 자산 등 고정적 현금 흐름을 창출하는 안전 자산에 집중할 때 부의 크기가 3배 이상 공고해집니다.</p>
                    <p>• <strong>[비즈니스 및 직업 처세]:</strong> 혼자 모든 짐을 짊어지려 하지 말고 유능한 협력 파트너를 적극적으로 영입하세요. 위임의 기술을 발휘할 때 명예와 성취가 배가됩니다.</p>
                    <p>• <strong>[건강 및 마인드셋]:</strong> 머리는 차갑게 식히고 하체 순환을 돕는 '두한족열' 루틴을 유지하세요. 감정에 휘둘리지 않는 평정심을 유지할 때 인생 최대의 복록을 온전히 담아낼 수 있습니다.</p>
                </div>
            </div>

        </div>
        """
    }

@app.post("/api/sinnian-report")
def get_sinnian_report(req: dict):
    user_name = req.get("name", "최정오")
    
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
        "title": "📅 2026 丙午년 총운 & 하반기 정밀 월별 가이드",
        "content": f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div>
                <div style="border-left: 4px solid #DC2626; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #DC2626; font-weight: 800;">Chapter 1. 2026년 세운(歲運) 총론</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #991B1B; margin-top: 2px;">
                        🔥 2026 丙午년(붉은 말의 해) {user_name}님의 도약 총운
                    </h4>
                </div>
                <p style="color: #7F1D1D; line-height: 1.85; margin-bottom: 12px;">
                    2026년은 강렬한 불(火)의 기운이 어둠을 걷어내고 대지를 환하게 비추는 丙午년입니다. {user_name}님의 사주 본원과 조화를 이루어 그동안 수면 아래에서 준비해 온 역량이 화려하게 꽃을 피우며, 막혀 있던 활로가 시원하게 뚫리는 <strong>'비상(飛翔)의 한 해'</strong>가 됩니다.
                </p>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14px; color: #475569;">
                    <p>• <strong>💰 재물 대박 타이밍:</strong> 양력 5월(상반기 결실)과 10월(하반기 결실)에 큰 금전적 성과와 유리한 계약 성사.</p>
                    <p>• <strong>💼 커리어 및 직무 운세:</strong> 상반기에 뿌린 기획이 하반기(9~11월)에 승진, 인정, 영전으로 직결됩니다.</p>
                    <p>• <strong>🤝 결정적 귀인수:</strong> 서북쪽 방위에서 다가오는 동료 및 전문 조력자가 핵심 난제를 해결해 줍니다.</p>
                </div>
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

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #D97706; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #D97706; font-weight: 800;">Chapter 3. 2026 개운 비책</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #78350F; margin-top: 2px;">
                        ✨ 2026년 운세를 200% 극대화하는 3대 실천 솔루션
                    </h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14px; color: #92400E; line-height: 1.8;">
                    <p>• <strong>행운의 방위:</strong> 주거지 및 집무실 기준 '정동쪽'과 '서북쪽'이 복록을 부르는 최고의 황금 방위입니다.</p>
                    <p>• <strong>금전 지출 방어:</strong> 양력 7월에는 충동적인 지출이나 무리한 확장을 자제하고 현금 유동성을 확보하세요.</p>
                    <p>• <strong>마인드셋 처세:</strong> 빠른 속도감 속에서도 중요한 계약서는 반드시 문구 하나까지 꼼꼼히 점검할 때 완벽한 승리를 거둡니다.</p>
                </div>
            </div>
        </div>
        """
    }

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

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #D97706; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #D97706; font-weight: 800;">Chapter 2. 실전 관계 조화 & 갈등 해결법</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #78350F; margin-top: 2px;">
                        💡 관계 유형 맞춤 처세: [{relation}]
                    </h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14px; color: #92400E;">
                    <p>• <strong>소통의 찰떡 포인트:</strong> {user_name}님의 통솔력과 {partner_name}님의 세심한 지혜가 결합하여 어떤 난관도 지혜롭게 돌파합니다.</p>
                    <p>• <strong>주의할 순간:</strong> 사소한 의견 차이가 생길 때는 감정적 직설보다 '맛있는 식사나 티타임'을 곁들이며 대화할 때 막힘없이 풀립니다.</p>
                </div>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #2D6A4F; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #2D6A4F; font-weight: 800;">Chapter 3. 인연을 백년해로로 이끄는 개운 비책</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #0F172A; margin-top: 2px;">
                        🌹 두 사람만의 행운의 방위 & 타이밍
                    </h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 6px; font-size: 14px; color: #475569;">
                    <p>• <strong>행운의 장소:</strong> 물이 잔잔히 흐르는 강변이나 클래식한 조명의 카페가 두 분의 애정운을 2배로 증폭시킵니다.</p>
                    <p>• <strong>결정적 결실의 시기:</strong> 봄(양력 3~5월)과 가을(양력 9~11월)에 두 사람 사이의 중요한 약속이나 결단이 이루어집니다.</p>
                </div>
            </div>

        </div>
        """
    }

# [4대 맞춤 복구] 애정운 분기 함수
def generate_love_report_content(user_name: str, sub_opt: str) -> str:
    if sub_opt == "기혼":
        return f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div style="border-left: 4px solid #E11D48; padding-left: 10px;">
                <span style="font-size: 12px; color: #E11D48; font-weight: 800;">Chapter 1. 부부 명식 감명</span>
                <h4 style="font-size: 16.5px; font-weight: 800; color: #881337; margin: 3px 0 6px;">[부부 해로 및 가정 화목운] 신뢰와 상호 존중의 평생 동반자</h4>
                <p style="color: #9F1239; font-size: 14.5px; line-height: 1.85;">
                    {user_name}님의 사주 원국은 부부 간의 신뢰와 가정의 안정을 최우선으로 삼는 묵직한 포용력을 지니고 있습니다. 일방적인 헌신이나 잔소리보다는 서로의 독립적인 영역을 인정하고 격려해 줄 때 부부 금실과 가정의 재물운이 함께 상승합니다.
                </p>
            </div>
            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>
            <div>
                <div style="border-left: 4px solid #BE123C; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #BE123C; font-weight: 800;">Chapter 2. 가정 에너지 분석</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #881337; margin-top: 2px;">🏡 Q. 배우자와의 성향 조화 및 가정 번영의 핵심은?</h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14.5px; color: #475569;">
                    <p>• <strong>배우자와의 성향 조화:</strong> 겉으로는 무던해 보여도 속정이 깊은 배우자궁을 타고났으며, 서로의 장단점을 보완해 주는 상생 구조입니다.</p>
                    <p>• <strong>가정 내 갈등 관리:</strong> 자녀 교육이나 재정 계획에 이견이 생길 때는 감정적 직설보다 차 한 잔을 나누며 대화할 때 막힘없이 풀립니다.</p>
                    <p>• <strong>가정 번영 오행 기운:</strong> 온화한 기운을 북돋워 주는 방위는 '남서쪽'이며, 거실에 따뜻한 조명을 두면 부부 화합이 배가됩니다.</p>
                </div>
            </div>
            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>
            <div>
                <div style="border-left: 4px solid #D97706; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #D97706; font-weight: 800;">Chapter 3. 백년해로 처세</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #78350F; margin-top: 2px;">🌹 평생 백년해로를 완성하는 실전 부부 개운법</h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14.5px; color: #92400E;">
                    <p>• <strong>감사 표현의 생활화:</strong> 일상적인 배려에 대해 "고마워요"라는 말을 하루 한 번 전하는 것이 최고의 부부 개운법입니다.</p>
                    <p>• <strong>행운의 힐링 추천:</strong> 주말 가벼운 근교 숲길 산책이나 조용한 힐링 여행이 부부의 권태감을 씻어내고 새로운 활력을 줍니다.</p>
                </div>
            </div>
        </div>
        """
    elif sub_opt == "연애중":
        return f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div style="border-left: 4px solid #E11D48; padding-left: 10px;">
                <span style="font-size: 12px; color: #E11D48; font-weight: 800;">Chapter 1. 연애 명식 감명</span>
                <h4 style="font-size: 16.5px; font-weight: 800; color: #881337; margin: 3px 0 6px;">[연애 발전 및 결실운] 깊은 교감과 미래를 약속하는 인연</h4>
                <p style="color: #9F1239; font-size: 14.5px; line-height: 1.85;">
                    {user_name}님은 연인과의 관계에서 진실된 소통과 배려를 중시하는 따뜻한 사랑의 소유자입니다. 현재 연애는 단순한 설렘을 넘어 미래의 진지한 동반자로 발전하기에 매우 좋은 기운이 흐르고 있습니다.
                </p>
            </div>
            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>
            <div>
                <div style="border-left: 4px solid #BE123C; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #BE123C; font-weight: 800;">Chapter 2. 결혼 결실 가이드</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #881337; margin-top: 2px;">💍 Q. 장기적 인연 발전 및 결혼의 최적 타이밍은?</h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14.5px; color: #475569;">
                    <p>• <strong>관계의 성숙 포인트:</strong> 바라는 점을 솔직하면서도 부드럽게 표현할 때 신뢰의 뿌리가 깊어집니다.</p>
                    <p>• <strong>결혼 및 결실의 타이밍:</strong> 가을(양력 9~11월)과 봄(양력 3~5월)에 중요한 약속이나 결혼 논의가 급물살을 타게 됩니다.</p>
                </div>
            </div>
            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>
            <div>
                <div style="border-left: 4px solid #D97706; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #D97706; font-weight: 800;">Chapter 3. 사랑 결속 처세</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #78350F; margin-top: 2px;">🌹 둘만의 사랑을 공고히 하는 실전 연애 처세법</h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14.5px; color: #92400E;">
                    <p>• <strong>밀당 없는 진정성:</strong> 계산적인 태도보다 솔직하고 일관된 태도를 보여줄 때 상대방의 마음을 완전히 사로잡습니다.</p>
                    <p>• <strong>추천 데이트 장소:</strong> 야경이 내려다보이는 레스토랑이나 클래식한 전시회가 로맨틱한 기운을 증폭시킵니다.</p>
                </div>
            </div>
        </div>
        """
    elif sub_opt == "썸/짝사랑":
        return f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div style="border-left: 4px solid #E11D48; padding-left: 10px;">
                <span style="font-size: 12px; color: #E11D48; font-weight: 800;">Chapter 1. 호감운 감명</span>
                <h4 style="font-size: 16.5px; font-weight: 800; color: #881337; margin: 3px 0 6px;">[호감 발전 및 연인 전환운] 매력 어필과 결정적 고백 타이밍</h4>
                <p style="color: #9F1239; font-size: 14.5px; line-height: 1.85;">
                    {user_name}님은 은근한 매력과 진중함으로 상대방에게 호감을 심어주는 기운을 지니고 있습니다. 망설이기보다는 적절한 순간에 확실한 시그널을 보낼 때 연인 관계로의 전환이 빠르게 이루어집니다.
                </p>
            </div>
            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>
            <div>
                <div style="border-left: 4px solid #BE123C; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #BE123C; font-weight: 800;">Chapter 2. 마음 공략법</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #881337; margin-top: 2px;">💘 Q. 상대방의 마음을 여는 핵심 전략과 결정적 순간은?</h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14.5px; color: #475569;">
                    <p>• <strong>공감대 형성:</strong> 상대방의 취향과 관심사를 미리 파악하여 자연스러운 대화 주제로 이끌어내세요.</p>
                    <p>• <strong>결정적 타이밍:</strong> 저녁 티타임이나 비 오는 날 은근한 칭찬과 함께 호감을 표현할 때 성공 확률이 2배로 높아집니다.</p>
                </div>
            </div>
            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>
            <div>
                <div style="border-left: 4px solid #D97706; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #D97706; font-weight: 800;">Chapter 3. 실전 고백 팁</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #78350F; margin-top: 2px;">🌹 썸을 연애로 만드는 실전 액션 팁</h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14.5px; color: #92400E;">
                    <p>• <strong>과도한 조급함 금물:</strong> 상대방의 반응 속도에 일희일비하지 말고 여유 있고 당당한 태도를 유지하세요.</p>
                    <p>• <strong>행운의 아이템:</strong> 은은한 우디/플로럴 계열 향수와 단정한 셔츠 차림이 매력도를 극대화합니다.</p>
                </div>
            </div>
        </div>
        """
    else: # 솔로 기본
        return f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div style="border-left: 4px solid #E11D48; padding-left: 10px;">
                <span style="font-size: 12px; color: #E11D48; font-weight: 800;">Chapter 1. 인연 명식 감명</span>
                <h4 style="font-size: 16.5px; font-weight: 800; color: #881337; margin: 3px 0 6px;">[평생 애정운] 깊은 신뢰와 상호 존중의 천생연분</h4>
                <p style="color: #9F1239; font-size: 14.5px; line-height: 1.85;">
                    {user_name}님의 애정 원국은 가벼운 감정의 불꽃보다는 한 번 맺은 신뢰를 평생 지켜나가는 따뜻한 포용력의 소유자입니다. 주변 사람들에게 굳이 맞추려 하지 않고 본인 본연의 당당함을 드러낼 때 뜻밖의 귀한 인연이 찾아옵니다.
                </p>
            </div>
            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>
            <div>
                <div style="border-left: 4px solid #BE123C; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #BE123C; font-weight: 800;">Chapter 2. 인연의 특징</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #881337; margin-top: 2px;">💞 Q. {user_name}님과 운명적으로 통하는 상대방의 특징은?</h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14.5px; color: #475569;">
                    <p>• <strong>성향과 인품:</strong> 감정 기복이 적고 원칙이 뚜렷하며, 대화 시 상대방의 이야기를 깊이 경청해 주는 차분한 스타일.</p>
                    <p>• <strong>외모 및 이미지:</strong> 부드럽고 온화한 인상에 단정하고 지적인 분위기를 풍기는 사람.</p>
                    <p>• <strong>오행 궁합 조화:</strong> 쥐띠, 닭띠, 원숭이띠와 사주 궁합에서 대길연을 이룹니다.</p>
                </div>
            </div>
            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>
            <div>
                <div style="border-left: 4px solid #D97706; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #D97706; font-weight: 800;">Chapter 3. 인연 성사 처세</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #78350F; margin-top: 2px;">🌹 평생 인연을 완성하는 실전 관계 처세법</h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14.5px; color: #92400E;">
                    <p>• <strong>만남의 장소:</strong> 물이 잔잔하게 흐르는 호수 주변, 조용한 미술관이나 테라스 카페가 인연의 기운을 조화롭게 묶어줍니다.</p>
                    <p>• <strong>인연 대길 시기:</strong> 가을(양력 9~11월)과 초봄(양력 2~3월)에 귀인의 소개로 다가오는 만남을 주목하세요.</p>
                </div>
            </div>
        </div>
        """

# [4대 맞춤 복구] 사업·직업운 분기 함수
def generate_business_report_content(user_name: str, sub_opt: str) -> str:
    if sub_opt == "취업/이직 준비중":
        return f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div style="border-left: 4px solid #2563EB; padding-left: 10px;">
                <span style="font-size: 12px; color: #2563EB; font-weight: 800;">상황 맞춤: 취업/이직 준비중</span>
                <h4 style="font-size: 16.5px; font-weight: 800; color: #1E3A8A; margin: 3px 0 6px;">[취업·이직 대길운] 숨겨진 잠재력 폭발과 합격의 낭보</h4>
                <p style="color: #1E40AF; font-size: 14.5px; line-height: 1.85;">
                    {user_name}님의 사주 원국은 치밀한 분석력과 묵직한 신뢰감을 겸비하고 있어 인사 결정권자에게 깊은 인상을 심어주는 관록의 명식입니다. 기준을 낮추기보다 전문 강점을 당당하게 어필할 때 더 좋은 조건으로 합격문이 열립니다.
                </p>
            </div>
            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>
            <div>
                <div style="border-left: 4px solid #1E40AF; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #1E40AF; font-weight: 800;">Chapter 2. 합격 최적 타이밍</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #0F172A; margin-top: 2px;">🎯 Q. 서류/면접 합격률이 가장 높은 황금 달(月)은?</h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14.5px; color: #475569;">
                    <p>• <strong>합격 대길 시기:</strong> 가을(양력 9~11월)과 초봄(양력 2~3월)에 문서운과 취업운이 결합하여 합격 통보를 받습니다.</p>
                    <p>• <strong>추천 직무 분야:</strong> 전략 기획, 경영 관리, IT/기술 매니지먼트, 금융 분석 등 원칙과 시스템을 다루는 분야에 최적입니다.</p>
                </div>
            </div>
            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>
            <div>
                <div style="border-left: 4px solid #D97706; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #D97706; font-weight: 800;">Chapter 3. 면접 합격 개운법</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #78350F; margin-top: 2px;">💼 합격을 부르는 면접 스타일 & 마인드셋</h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14.5px; color: #92400E;">
                    <p>• <strong>면접 복장 코디:</strong> 딥 네이비 정장에 단정한 화이트 셔츠와 메탈 시계를 착용하면 전문성과 신뢰감이 돋보입니다.</p>
                    <p>• <strong>실전 답변 전략:</strong> 화려한 미사여구보다 실제 경험을 두괄식으로 간결하게 전달할 때 압도적인 신뢰를 얻습니다.</p>
                </div>
            </div>
        </div>
        """
    elif sub_opt == "사업가/프리랜서":
        return f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div style="border-left: 4px solid #2563EB; padding-left: 10px;">
                <span style="font-size: 12px; color: #2563EB; font-weight: 800;">상황 맞춤: 사업가/프리랜서</span>
                <h4 style="font-size: 16.5px; font-weight: 800; color: #1E3A8A; margin: 3px 0 6px;">[사업 번창 & 수주 대길운] 매출 퀀텀점프와 독점적 시장 장악</h4>
                <p style="color: #1E40AF; font-size: 14.5px; line-height: 1.85;">
                    {user_name}님의 사주는 시장의 주도권을 쥐는 전형적인 '비즈니스 사령관'의 명식입니다. 단순 용역을 넘어 자신만의 시스템과 브랜드를 구축할 때 폭발적인 부의 확장이 일어납니다.
                </p>
            </div>
            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>
            <div>
                <div style="border-left: 4px solid #1E40AF; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #1E40AF; font-weight: 800;">Chapter 2. 매출 폭발 타이밍</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #0F172A; margin-top: 2px;">🚀 Q. 대형 수주 및 투자 유치 대박의 타이밍은?</h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14.5px; color: #475569;">
                    <p>• <strong>대박 수주·계약 시기:</strong> 양력 5월과 10월에 재물선과 계약선이 합을 이루어 연간 매출을 견인하는 대형 계약이 성사됩니다.</p>
                    <p>• <strong>파트너십 궁합:</strong> 실행력이 뛰어난 소띠, 용띠 파트너와 손을 잡으면 사업의 안정성과 속도가 3배로 빨라집니다.</p>
                </div>
            </div>
            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>
            <div>
                <div style="border-left: 4px solid #D97706; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #D97706; font-weight: 800;">Chapter 3. 사업 자산 방어</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #78350F; margin-top: 2px;">💼 금전 누수 차단 및 집무실 개운 비책</h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14.5px; color: #92400E;">
                    <p>• <strong>집무실 명당 배치:</strong> 출입문을 대각선으로 바라보는 자리에 앉고 등 뒤에 단단한 벽을 두면 구설과 배신수를 막아냅니다.</p>
                    <p>• <strong>미수금 방어법:</strong> 구두 계약을 절대 금하고 모든 계약은 단계별 선금과 서면 날인을 철저히 준수하세요.</p>
                </div>
            </div>
        </div>
        """
    elif sub_opt == "창업 준비중":
        return f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div style="border-left: 4px solid #2563EB; padding-left: 10px;">
                <span style="font-size: 12px; color: #2563EB; font-weight: 800;">상황 맞춤: 창업 준비중</span>
                <h4 style="font-size: 16.5px; font-weight: 800; color: #1E3A8A; margin: 3px 0 6px;">[창업 대길 & 개척운] 성공적인 론칭과 탄탄한 사업 기반 구축</h4>
                <p style="color: #1E40AF; font-size: 14.5px; line-height: 1.85;">
                    {user_name}님의 사주는 스스로 깃발을 꽂고 영토를 확장할 때 진정한 천운이 발현되는 창업가의 사주입니다. 철저한 시장 조사와 초기 자본 운용이 뒷받침된다면 3년 내에 탄탄한 기틀을 닦게 됩니다.
                </p>
            </div>
            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>
            <div>
                <div style="border-left: 4px solid #1E40AF; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #1E40AF; font-weight: 800;">Chapter 2. 창업 론칭 타이밍</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #0F172A; margin-top: 2px;">🏁 Q. 사업자 등록 및 공식 론칭 대길의 달은?</h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14.5px; color: #475569;">
                    <p>• <strong>사업자 등록 대길 시기:</strong> 봄(양력 3~4월)과 가을(양력 9~10월)에 오픈을 진행하면 초기 고객 유입 효과가 극대화됩니다.</p>
                    <p>• <strong>사업장 명당 방위:</strong> 주거지 기준 '정동쪽'과 '서북쪽'에 터를 잡으면 귀인의 발걸음이 끊이지 않습니다.</p>
                </div>
            </div>
            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>
            <div>
                <div style="border-left: 4px solid #D97706; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #D97706; font-weight: 800;">Chapter 3. 창업 생존 수칙</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #78350F; margin-top: 2px;">💡 망하지 않는 창업 3대 실천 원칙</h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14.5px; color: #92400E;">
                    <p>• <strong>초기 고정비 최소화:</strong> 화려한 인테리어보다 실제 마케팅과 제품 경쟁력에 80% 이상의 자금을 투입하세요.</p>
                    <p>• <strong>핵심 멤버 구성:</strong> 재무와 꼼꼼한 실무를 도맡아줄 파트너(소띠, 닭띠)를 초기에 확보하면 리스크가 줄어듭니다.</p>
                </div>
            </div>
        </div>
        """
    else: # 직장인 기본
        return f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div style="border-left: 4px solid #2563EB; padding-left: 10px;">
                <span style="font-size: 12px; color: #2563EB; font-weight: 800;">상황 맞춤: 직장인</span>
                <h4 style="font-size: 16.5px; font-weight: 800; color: #1E3A8A; margin: 3px 0 6px;">[직장·승진운] 핵심 인재로서의 두각과 고속 승진의 천운</h4>
                <p style="color: #1E40AF; font-size: 14.5px; line-height: 1.85;">
                    {user_name}님의 사주는 복잡한 난제를 단번에 해결하는 전략적 기획력과 결단력을 지니고 있어 조직 내에서 대체 불가능한 핵심 리더로서 인정받는 명식입니다. 본인만의 실적을 증명할 때 파격적인 승진과 연봉 인상의 기회가 찾아옵니다.
                </p>
            </div>
            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>
            <div>
                <div style="border-left: 4px solid #1E40AF; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #1E40AF; font-weight: 800;">Chapter 2. 승진·영전 타이밍</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #0F172A; margin-top: 2px;">🚀 Q. 사내 인사 고과 및 영전·승진의 최적기는?</h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14.5px; color: #475569;">
                    <p>• <strong>승진·영전 대길 시기:</strong> 하반기(양력 10~12월)와 초봄(양력 2~3월)에 상급자 및 인사위원회의 강력한 추천으로 직급 상승이 성사됩니다.</p>
                    <p>• <strong>사내 귀인 상사:</strong> 무게감 있고 원칙이 뚜렷한 상사(원숭이띠, 쥐띠)가 든든한 방패막이가 되어줍니다.</p>
                </div>
            </div>
            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>
            <div>
                <div style="border-left: 4px solid #D97706; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #D97706; font-weight: 800;">Chapter 3. 사내 처세 비책</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #78350F; margin-top: 2px;">💼 직장 스트레스 차단 & 사무 공간 개운법</h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14.5px; color: #92400E;">
                    <p>• <strong>사무실 책상 풍수:</strong> 모니터 옆에 메탈 소재의 소품이나 화분을 두면 잡음을 없애고 집중력을 극대화합니다.</p>
                    <p>• <strong>동료 관계 처세:</strong> 동료들의 불평불만에 휩쓸리지 말고 중립을 유지할 때 인사철에 가장 높은 평가를 받습니다.</p>
                </div>
            </div>
        </div>
        """

# 4대 테마운세 풀버전 라우터
@app.post("/api/theme-report")
def get_theme_report(req: dict):
    theme = req.get("theme", "wealth")
    sub_opt = req.get("sub_option", "기본")
    user_name = req.get("name", "최정오")
    
    titles = {
        "wealth": "💰 평생 재물운",
        "love": f"💖 평생 애정운 ({sub_opt})",
        "business": f"🏢 사업·직업운 ({sub_opt})",
        "health": "🌿 평생 건강운"
    }

    if theme == "love":
        content = generate_love_report_content(user_name, sub_opt)
    elif theme == "business":
        content = generate_business_report_content(user_name, sub_opt)
    elif theme == "wealth":
        content = f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div style="border-left: 4px solid #D97706; padding-left: 10px;">
                <span style="font-size: 12px; color: #D97706; font-weight: 800;">Chapter 1. 재물 원국 감명</span>
                <h4 style="font-size: 16.5px; font-weight: 800; color: #78350F; margin: 3px 0 6px;">[평생 재물운] '암장(暗藏) 금고형' 자산 축적 원국</h4>
                <p style="color: #92400E; font-size: 14.5px; line-height: 1.85;">
                    {user_name}님의 사주는 겉으로 드러난 화려함보다 실속 있게 현금과 실물 자산을 차곡차곡 축적하는 전형적인 '황금 금고형' 구조입니다. 지장간 속에 알짜배기 재성이 뿌리를 내리고 있어 틈새 기회를 포착하여 자산을 불리는 능력이 탁월합니다. 단기 시세 차익보다 실물 부동산과 우량 배당 자산 중심 포트폴리오가 운명을 견인합니다.
                </p>
            </div>
            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>
            <div>
                <div style="border-left: 4px solid #2D6A4F; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #2D6A4F; font-weight: 800;">Chapter 2. 생애 자산 로드맵</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #0F172A; margin-top: 2px;">📊 Q. {user_name}님의 생애 주기별 자산 퀀텀점프 시기는?</h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14.5px; color: #475569;">
                    <p>• <strong>초년~30대 (씨앗 축적기):</strong> 종잣돈을 모으고 금융/실물 경제의 안목을 기르는 시기였습니다.</p>
                    <p style="color: #B45309; font-weight: 800;">• <strong>40대 중후반~50대 (*현재 황금기):</strong> 귀인의 도움과 부동산/사업 결단으로 자산 규모가 3배 이상 폭발적으로 퀀텀점프하는 최상의 전환점입니다.</p>
                    <p>• <strong>60대 이후 (자산 수성기):</strong> 고정적 현금 흐름을 바탕으로 부를 안전하게 대물림하는 완벽한 자산 수성기입니다.</p>
                </div>
            </div>
            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>
            <div>
                <div style="border-left: 4px solid #059669; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #059669; font-weight: 800;">Chapter 3. 실전 부의 증식 비책</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #065F46; margin-top: 2px;">💡 재물운을 극대화하는 실전 개운(開運) 솔루션</h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14.5px; color: #047857;">
                    <p>• <strong>행운의 방위:</strong> 주거지나 사무실 기준 '정북쪽'과 '동북쪽'이 재물이 샘솟는 황금 방위입니다.</p>
                    <p>• <strong>금전 누수 방어법:</strong> 지갑 안에 현금을 항상 짝수 매수로 정돈하여 넣고, 노란색 소품을 휴대하면 헛돈 지출이 차단됩니다.</p>
                </div>
            </div>
        </div>
        """
    else: # 건강운 (선택옵션 없이 3대 챕터 풀버전 즉시 제공)
        content = f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div style="border-left: 4px solid #059669; padding-left: 10px;">
                <span style="font-size: 12px; color: #059669; font-weight: 800;">Chapter 1. 오행 체질 분석</span>
                <h4 style="font-size: 16.5px; font-weight: 800; color: #065F46; margin: 3px 0 6px;">[평생 건강운] 수승화강(水昇火降) 활력 관리</h4>
                <p style="color: #047857; font-size: 14.5px; line-height: 1.85;">
                    {user_name}님의 오행 체질은 강인한 생명력을 갖추고 있으나 두한족열(머리는 시원하게 발은 따뜻하게)의 수칙을 유지해야 합니다. 스트레스 누적 시 간 피로와 소화기계로 신호가 올 수 있으므로 규칙적인 유산소 운동이 건강의 비결입니다.
                </p>
            </div>
            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>
            <div>
                <div style="border-left: 4px solid #047857; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #047857; font-weight: 800;">Chapter 2. 취약 장기 관리</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #0F172A; margin-top: 2px;">🏥 Q. {user_name}님이 각별히 챙겨야 할 3대 취약 장기와 예방법은?</h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14.5px; color: #475569;">
                    <p>• <strong>간장 & 담낭:</strong> 만성 피로를 방지하기 위해 과도한 음주를 피하고 간 보호 성분을 섭취하세요.</p>
                    <p>• <strong>신장 & 방광:</strong> 노폐물 배출을 위해 하루 1.5L 이상의 미온수를 나누어 마시는 습관이 필수적입니다.</p>
                    <p>• <strong>위장 & 비장:</strong> 야식을 지양하고 담백한 식단을 유지해야 소화 흡수력이 강화됩니다.</p>
                </div>
            </div>
            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>
            <div>
                <div style="border-left: 4px solid #1E40AF; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #1E40AF; font-weight: 800;">Chapter 3. 일상 섭생 루틴</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #1E3A8A; margin-top: 2px;">🌿 평생 활력을 완성하는 일상 개운 섭생 루틴</h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14.5px; color: #1E40AF;">
                    <p>• <strong>취침 전 힐링 루틴:</strong> 매일 밤 15분간 따뜻한 족욕을 통해 하체 순환을 돕고 숙면을 취하세요.</p>
                    <p>• <strong>추천 운동 요법:</strong> 주 3회 30분 이상의 빠른 걷기나 수영 등 유산소 운동이 오행 밸런스를 맞춰줍니다.</p>
                </div>
            </div>
        </div>
        """
    
    return {
        "title": titles.get(theme, "심층 리포트"),
        "content": content
    }
