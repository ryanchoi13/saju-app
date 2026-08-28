import datetime
import math
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional
import os
import random

app = FastAPI(title="운세의 신 정통 명리학 엔진 - Mode 2 Ultimate", version="38.0.0")

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
    -1: "시간 모름",
    0: "자시(子時)",
    1: "축시(丑時)",
    2: "인시(寅時)",
    3: "묘시(卯時)",
    4: "진시(辰時)",
    5: "사시(巳時)",
    6: "오시(午時)",
    7: "미시(未時)",
    8: "신시(申時)",
    9: "유시(酉時)",
    10: "술시(戌時)",
    11: "해시(亥時)"
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
    "wood": {
        "type": "wood", "title": "사업대성부 (事業亨通符)", "power": "추진력 강화 · 사업 번창 · 승진운",
        "desc": "사주에 부족한 木(목)의 생명력과 추진력을 불어넣어 막힌 활로를 뚫고 사업과 직장에서 독보적인 주도권을 쥐게 하는 정통 비급 부적입니다."
    },
    "fire": {
        "type": "fire", "title": "소원성취부 (心想事成符)", "power": "열정 회복 · 명예 상승 · 소원 성취",
        "desc": "사주에 부족한 火(화)의 찬란한 빛을 밝혀 어둠을 몰아내고 염원하던 소망을 일사천리로 성취시키는 전통 경면주사 부적입니다."
    },
    "earth": {
        "type": "earth", "title": "금고수호부 (金庫安穩符)", "power": "자산 방어 · 누수 차단 · 재물 안착",
        "desc": "사주에 부족한 土(토)의 단단한 대지를 마련하여 헛돈 지출을 막고 평생 모은 자산을 철벽처럼 지켜주는 수호 부적입니다."
    },
    "metal": {
        "type": "metal", "title": "재물만복부 (萬福大吉符)", "power": "재물 증식 · 금전운 대통 · 투자 대박",
        "desc": "사주에 부족한 金(금)의 황금 기운을 채워 사방에서 금전과 복록이 쏟아지게 하는 전통 비급 부적입니다."
    },
    "water": {
        "type": "water", "title": "천생화합부 (萬事和合符)", "power": "인연 결속 · 애정 화합 · 귀인 유대",
        "desc": "사주에 부족한 水(수)의 지혜와 유대감을 채워 엇갈린 인연을 단단히 묶어주고 귀인의 조력을 이끄는 화합 부적입니다."
    }
}

TAROT_CARDS = [
    {
        "name": "0. THE FOOL (바보)",
        "keyword": "새로운 여정의 서막 · 순수한 직관 · 무한한 잠재력",
        "symbolism": "화려한 옷을 입고 벼랑 끝에서 발걸음을 내딛는 청년과 곁에서 위험을 경고하는 흰 개, 그리고 찬란하게 빛나는 태양은 과거의 관습과 두려움을 벗어던진 순수한 영혼의 새로운 도약을 상징합니다.",
        "reading_male": "오랫동안 가슴속에 품고 망설이던 프로젝트나 신규 투자의 첫 단추를 꿰기에 최상의 날입니다. 주변의 지나친 간섭보다 본인의 결단력과 도전 정신을 믿고 추진하세요.",
        "reading_female": "새로운 인연이나 오랫동안 염원하던 소망에 뜻밖의 기회가 찾아옵니다. 계산적인 생각보다 마음이 이끄는 첫 느낌을 따를 때 대길한 결과가 따릅니다.",
        "action_guide": "새로운 제안이 들어오면 편견 없이 경청하고, 떠오르는 창의적인 아이디어를 즉시 메모하세요."
    },
    {
        "name": "I. THE MAGICIAN (마법사)",
        "keyword": "탁월한 창조력 · 완벽한 주도권 · 만사형통",
        "symbolism": "머리 위의 무한대(∞) 기호와 제단 위에 놓인 4대 원소(지팡이·성배·검·펜타클)는 모든 상황을 내 뜻대로 통제하고 현실로 구현할 수 있는 완성된 지혜와 전문성을 뜻합니다.",
        "reading_male": "당신의 전문 역량과 논리적인 언변이 빛을 발합니다. 중요한 회의나 계약 협상에서 상대방을 내 페이스로 완벽히 리드할 수 있습니다.",
        "reading_female": "능숙한 대인관계 조율력과 따뜻한 카리스마로 주변 사람들을 내 든든한 아군으로 만듭니다. 본인의 의견을 당당하게 피력하세요.",
        "action_guide": "본인의 핵심 강점을 자신감 있게 표현하고, 주도적으로 대화의 흐름을 이끌어가세요."
    },
    {
        "name": "XIX. THE SUN (태양)",
        "keyword": "최고의 번영 · 찬란한 영광 · 축하받을 낭보",
        "symbolism": "붉은 깃발을 든 채 백마를 타고 천진난만하게 웃는 아이와 활짝 핀 해바라기는 어둠과 장애물을 완전히 걷어내고 승리와 축복을 맞이하는 절정의 운세를 의미합니다.",
        "reading_male": "그동안 막혀 있던 자금 흐름이나 프로젝트의 난관이 시원하게 뚫리며 성취의 결실을 맺습니다. 명예와 실속을 동시에 쟁취하는 날입니다.",
        "reading_female": "내면의 밝고 긍정적인 에너지가 주변을 환하게 밝힙니다. 칭찬과 축하받을 소식이 들려오며 가문과 인간관계에 화목이 넘칩니다.",
        "action_guide": "햇살을 받으며 가벼운 야외 산책을 즐기고, 기분 좋은 미소로 주변에 긍정적인 에너지를 전파하세요."
    }
]

DAILY_OUTFITS_POOL = {
    "male": {
        "young": [
            "화이트 린넨 셔츠 & 실버 메탈 워치 쿨비즈 룩",
            "올리브 그린 쿨맥스 피케티 & 라이트 베이지 반바지",
            "코랄 핑크 린넨 셔츠 & 화이트 쿨 슬랙스",
            "웜 크림 톤 반팔 니트 & 차콜 밴딩 스판 팬츠",
            "딥 네이비 스트라이프 하프 셔츠 & 메탈 팔찌",
            "스카이블루 오픈카라 반팔 & 라이트 그레이 슬랙스"
        ],
        "senior": [
            "스노우 화이트 쿨비즈 셔츠 & 실버 가죽 세미 워치",
            "다크 올리브 린넨 헨리넥 셔츠 & 통풍 차콜 슬랙스",
            "딥 와인 톤 하프 카라티 & 로즈골드 메탈 워치",
            "샌드 베이지 린넨 재킷 & 오픈카라 쿨 셔츠",
            "미드나잇 블루 린넨 블레이저 & 크림 드레스 팬츠",
            "클래식 네이비 피케 셔츠 & 라이트 브라운 팬츠"
        ]
    },
    "female": {
        "young": [
            "순백색 린넨 스퀘어넥 원피스 & 은은한 실버 펜던트",
            "세이지 그린 린넨 원피스 & 실버 뱅글 팔찌",
            "로즈 핑크 뷔스티에 블라우스 & 라이트 데님",
            "크림 오프숄더 니트 & 샌드 베이지 와이드 팬츠",
            "스카이 블루 린넨 셔츠 & 화이트 하이웨스트 팬츠",
            "라벤더 톤 플리츠 원피스 & 미니멀 숄더백"
        ],
        "senior": [
            "스노우 화이트 린넨 셋업 & 고급스러운 실버 워치",
            "올리브 카키 린넨 블라우스 & 통풍 보타닉 슬랙스",
            "코랄 로즈 엘레강스 린넨 자켓 & 모던 이어링",
            "웜 베이지 실크 블렌드 셔츠 & 아이보리 쿨 와이드 팬츠",
            "딥 네이비 린넨 쉬폰 원피스 & 클래식 은 팔찌",
            "소프트 핑크 린넨 자켓 & 펄 네크리스"
        ]
    }
}

LUCKY_ITEMS_POOL = [
    "실버 메탈 워치", "가벼운 원목 명함집", "은은한 시트러스 아로마", "클래식 만년필",
    "가죽 미니 지갑", "블루라이트 차단 안경", "핸드메이드 가죽 키링", "산뜻한 린넨 손수건"
]

LUCKY_DIRECTIONS_POOL = [
    "정서쪽 (백호 방위)", "정동쪽 (청룡 방위)", "정남쪽 (주작 방위)",
    "정북쪽 (현무 방위)", "동남쪽 (풍수 생기방)", "서북쪽 (천문 금전방)"
]

LUCKY_MENUS_POOL = [
    "도라지차와 가벼운 고단백 식사", "신선한 아보카도 샐러드와 미온수", "따뜻한 전복죽과 비타민 과일",
    "속이 편안한 영양 솥밥", "검은콩 두유와 견과류", "시원한 메밀소바와 야채튀김"
]

MINDSETS_POOL = [
    "맺고 끊음을 명확히 대화하기", "새로운 제안에 열린 마음 갖기", "상대의 말을 경청하고 공감하기",
    "중요한 약속을 철저히 지키기", "원칙을 지키며 유연하게 대처하기", "서두르지 않고 한 번 더 검토하기"
]

ACTIONS_POOL = [
    "오늘 반드시 끝낼 우선순위 3가지 메모하기", "아침 시간 가벼운 스트레칭과 심호흡 5회", "점심 식사 후 햇볕 쬐며 10분간 산책하기",
    "지갑 속 영수증 정리하고 카드함 정돈하기", "오랫동안 고마웠던 지인에게 안부 문자 보내기", "책상 위 불필요한 서류 3개 정리하기"
]

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
    return HTMLResponse("<h2>운세의 신 서비스 준비 중</h2>")

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
            return {"val": val, "pct": pct, "status": "하강기", "color": "#2563EB", "tip": f"{cycle_name} 에너지가 소진되는 구간이니 페이스 조절이 필요합니다."}
        else:
            return {"val": val, "pct": pct, "status": "침체기", "color": "#475569", "tip": f"충분한 휴식과 재충전으로 내실을 다지세요."}

    is_critical_day = abs(p_val) <= 5 or abs(e_val) <= 5 or abs(i_val) <= 5
    
    if is_critical_day:
        overall_advice = "바이오리듬이 영점(0%) 전환선에 걸쳐 기운이 전환되는 민감한 날입니다. 감정적 언쟁이나 무리한 일정, 충동적인 계약 판단을 피하고 매사 한 번 더 확인하세요."
    elif p_val >= 30 and e_val >= 30 and i_val < 0:
        overall_advice = "지성 리듬이 다소 낮으나 신체와 감성 에너지가 충만합니다. 복잡한 수치 계산이나 서류 검토보다는 활발한 야외 활동, 스포츠, 대인관계 미팅에서 최고의 성과를 거둘 수 있습니다."
    elif i_val >= 30 and (p_val < 0 or e_val < 0):
        overall_advice = "체력이나 기분은 다소 차분하나 두뇌 회전과 직관이 번뜩이는 날입니다. 무리한 육체 활동을 줄이고 전략 기획, 서류 정리, 자기계발 공부에 집중할 때 능률이 극대화됩니다."
    elif p_val >= 40 and e_val >= 40 and i_val >= 40:
        overall_advice = "신체·감성·지성 3대 생체 에너지가 모두 절정에 달한 골든 데이입니다. 오랫동안 망설이던 중요 과제나 승부처를 주도적으로 추진하면 대길한 성취를 이룹니다."
    elif p_val < 0 and e_val < 0 and i_val < 0:
        overall_advice = "3대 에너지가 모두 재충전 구간에 머물러 있습니다. 중요한 결정은 내일로 미루고, 따뜻한 족욕과 균형 잡힌 식사로 내실을 다지며 푹 쉬는 것이 최고의 개운법입니다."
    else:
        overall_advice = "신체와 마음의 에너지가 안정된 균형을 유지하고 있습니다. 평소의 루틴을 차분히 지켜나가며 순조롭게 일과를 완수하기 좋은 하루입니다."

    return {
        "days_lived": days_lived,
        "physical": get_status(p_val, "신체"),
        "emotional": get_status(e_val, "감성"),
        "intellectual": get_status(i_val, "지성"),
        "overall_summary": overall_advice
    }

def get_daewoon_info(y_cg: str, gender: str) -> tuple[str, bool]:
    is_yang = y_cg in YANG_STEMS
    is_male = (gender == "male")
    return ("순행(順行)", True) if ((is_male and is_yang) or (not is_male and not is_yang)) else ("역행(逆行)", False)

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

    sijin_idx = req.sijin_index if req.sijin_index is not None else 5
    if req.is_unknown_time or sijin_idx < 0:
        h_pillar, h_cg, h_jj = "時未詳", "-", "-"
        sijin_korean = "시간 모름"
    else:
        h_jj_idx = sijin_idx
        h_cg_idx = (d_cg_idx % 5 * 2 + h_jj_idx) % 10
        h_cg, h_jj = CHEONGAN_HANJA[h_cg_idx], JIJI_HANJA[h_jj_idx]
        h_pillar = f"{h_cg}{h_jj}"
        sijin_korean = SIJIN_KOREAN_MAP.get(sijin_idx, "사시(巳時)")

    d_animal = ANIMAL_MAP.get(d_jj, "개")
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

    today_ordinal = today.toordinal()
    daily_hash = (today_ordinal * 31 + diff_days * 17 + (11 if gender == "male" else 23)) % 1000003

    age_group = "young" if current_age < 40 else "senior"
    outfit_list = DAILY_OUTFITS_POOL[gender][age_group]
    fashion_style = outfit_list[daily_hash % len(outfit_list)]

    num1 = ((daily_hash % 9) + 1)
    num2 = (((daily_hash // 10) % 9) + 1)
    if num1 == num2:
        num2 = (num1 % 9) + 1
    lucky_number = f"{min(num1, num2)}, {max(num1, num2)}"

    lucky_direction = LUCKY_DIRECTIONS_POOL[(daily_hash + 1) % len(LUCKY_DIRECTIONS_POOL)]
    lucky_item = LUCKY_ITEMS_POOL[(daily_hash + 2) % len(LUCKY_ITEMS_POOL)]
    recommended_menu = LUCKY_MENUS_POOL[(daily_hash + 3) % len(LUCKY_MENUS_POOL)]
    mindset = MINDSETS_POOL[(daily_hash + 4) % len(MINDSETS_POOL)]
    action = ACTIONS_POOL[(daily_hash + 5) % len(ACTIONS_POOL)]

    # [수정] 65점 ~ 100점 범위의 정밀 일진 운세 점수
    daily_score = 65 + (daily_hash % 36)

    today_diff = (today - base_date).days
    today_cg = CHEONGAN_HANJA[today_diff % 10]
    today_jj = JIJI_HANJA[(today_diff + 10) % 12]
    
    if daily_score >= 88:
        score_status_word = "대길(大吉)과 도약의 하루"
    elif daily_score >= 75:
        score_status_word = "순조로운 화합과 발전의 하루"
    else:
        score_status_word = "내실을 다지고 신중을 기할 하루"
        
    daily_title = f"[{today_cg}{today_jj}일] {score_status_word}"

    three_stage_advice = (f"☀️ <strong>오전:</strong> 아이디어를 공유하며 활발히 소통하세요.<br>"
                          f"🌤️ <strong>오후:</strong> 본원({d_cg})의 리더십으로 주요 과제를 완수하세요.<br>"
                          f"🌙 <strong>저녁:</strong> 가볍게 하루를 정리하고 충전하세요.")

    min_elem = min(elem_percentages, key=elem_percentages.get)
    user_talisman = TALISMAN_OHEANG_MAP.get(min_elem, TALISMAN_OHEANG_MAP["metal"])
    user_mbti = DAY_MBTI_MAP.get(d_cg, {"mbti": "대담한 통솔자 (ENTJ형)", "desc": "목표를 향해 나아가는 전략적 사주"})
    user_animal_icon = ANIMAL_ICONS.get(d_animal, "🐶")

    biorhythm_data = calculate_biorhythm(target_date, today)

    cal_name = "양력" if req.calendar_type == "solar" else ("음력(윤달)" if req.calendar_type == "leap" else "음력")
    birth_summary_str = f"{req.year}년 {req.month}월 {req.day}일생 ({cal_name}) · {sijin_korean}생"

    return {
        "user_name": req.name,
        "gender": gender,
        "birth_summary": birth_summary_str,
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
def get_daily_tarot(slot: int = 1, rand_seed: Optional[str] = None):
    random_idx = random.randint(0, len(TAROT_CARDS) - 1)
    return TAROT_CARDS[random_idx]

@app.post("/api/daewoon-report")
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
                <div style="border-left: 4px solid #F59E0B; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #D97706; font-weight: 800;">Chapter 3. 실전 개운 솔루션</span>
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
                <p style="color: #7F1D1D; line-height: 1.85; margin-bottom: 12px;">
                    2026년은 강렬한 불(火)의 기운이 어둠을 걷어내고 대지를 환하게 비추는 丙午년입니다. {user_name}님의 명식과 조화를 이루어 그동안 준비해 온 역량이 화려하게 꽃을 피우며 막혀 있던 활로가 시원하게 뚫리는 <strong>'비상(飛翔)의 한 해'</strong>가 됩니다.
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

@app.post("/api/gunghap-report")
def get_gunghap_report(req: dict):
    user_name = req.get("name", "최정오")
    partner_name = req.get("partner_name", "상대방")
    relation = req.get("relation", "연인/결혼")

    if relation == "동업/사업":
        chapter2_title = "💼 비즈니스 의사결정 케미 & 수익 배분 수칙"
        chapter2_desc = f"""
        <p>• <strong>기획 vs 실행의 황금 분담:</strong> {user_name}님의 거시적 사업 비전과 {partner_name}님의 꼼꼼한 실무·자금 관리 능력이 결합하여 동업 리스크를 90% 이상 줄여줍니다.</p>
        <p>• <strong>갈등 방지 원칙:</strong> 지분과 정산 구조는 초기에 문서화 및 공증을 완료할 때 동업 관계가 10년 이상 번창합니다.</p>
        <p>• <strong>위기 대응 전략:</strong> 자금 회수나 법적 분쟁 이슈 발생 시, {user_name}님이 대외 협상을 주도하고 {partner_name}님이 내부 문서를 검증하면 손실을 완벽히 방어합니다.</p>
        """
        chapter3_title = "📈 두 사람이 함께할 때 터지는 재물 시너지 & 대박 업종"
        chapter3_desc = f"""
        <p>두 분이 결합하면 금전 유입 운이 단독 사업 대비 2.8배 이상 증폭됩니다. 특히 <strong>신규 거래처 수주, 프랜차이즈/지점 확장, 투자 유치</strong>에서 막강한 시너지를 발휘합니다.</p>
        <p><strong>추천 협력 분야:</strong> 유통/이커머스, IT 솔루션, 지식 서비스, 프리미엄 식음료 및 부동산 자산 개발 분야에서 큰 부를 거머쥡니다.</p>
        """
    elif relation == "친구/지인":
        chapter2_title = "🍻 영혼의 소통 케미 & 평생 우정 유지법"
        chapter2_desc = f"""
        <p>• <strong>말하지 않아도 통하는 티키타카:</strong> 사주 오행의 균형 덕분에 첫 만남부터 10년 지기 같은 편안함과 신뢰를 느낍니다.</p>
        <p>• <strong>주의할 점:</strong> 서로에 대한 친밀감이 지나쳐 금전 차용이나 무리한 부탁을 하지 않는 선을 지킬 때 평생의 귀인 친구로 남습니다.</p>
        <p>• <strong>힐링 포인트:</strong> 가벼운 근교 드라이브나 취미 활동(골프, 테니스, 맛집 탐방)을 함께할 때 스트레스가 단숨에 해소됩니다.</p>
        """
        chapter3_title = "✨ 서로에게 주는 복록과 행운의 시너지"
        chapter3_desc = f"""
        <p>{partner_name}님은 {user_name}님이 인생의 고비나 번아웃에 직면했을 때 결정적인 멘탈 케어와 현실적 활로를 열어주는 귀인 역할을 담당합니다.</p>
        """
    else:
        chapter2_title = "💖 실전 생활/연애 케미 & 갈등 즉효성 해결 매뉴얼"
        chapter2_desc = f"""
        <p>• <strong>소통의 찰떡 포인트:</strong> {user_name}님의 당당한 통솔력과 {partner_name}님의 섬세한 배려가 결합하여 어떤 현실적 위기도 사랑으로 극복합니다.</p>
        <p>• <strong>다툼 발생 시 5분 즉효 솔루션:</strong> 메신저 텍스트 다툼을 멈추고 직접 만나 손을 잡고 대화하세요. '맛있는 식사나 따뜻한 티타임'을 곁들이며 대화할 때 막힌 응어리가 10분 만에 눈 녹듯 풀립니다.</p>
        <p>• <strong>결혼 적기 & 길일:</strong> 두 사람의 기운이 온화하게 합을 이루는 봄(양력 3~5월)과 가을(양력 9~11월)에 결실을 맺을 때 백년해로합니다.</p>
        <p>• <strong>가치관 조율:</strong> 경제권은 현실 감각이 뛰어난 쪽에게 위임하고, 주말 여가와 라이프스타일은 함께 결정할 때 갈등이 제로(0)가 됩니다.</p>
        """
        chapter3_title = "💰 두 사람이 결합할 때 폭발하는 가문 재물 & 부동산 대박운"
        chapter3_desc = f"""
        <p>결혼 후 가계 자산이 3배 이상 수직 상승하는 전형적인 <strong>'부귀쌍전(富貴雙全) 상생 궁합'</strong>입니다. 맞벌이든 외벌이든 서로의 운을 북돋워 부동산 청약 당첨 및 실물 자산 증식에서 놀라운 성과를 거둡니다.</p>
        <p>두 분이 함께 모은 종잣돈은 40대 중후반에 10억 이상의 탄탄한 자산 기틀을 완성하는 원동력이 됩니다.</p>
        """

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
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #881337; margin-top: 2px;">
                        🔗 {user_name}님과 {partner_name}님의 오행 상생 조화
                    </h4>
                </div>
                <p style="color: #9F1239; line-height: 1.85;">
                    {user_name}님의 사주에 부족하거나 필요한 기운을 {partner_name}님이 풍부하게 품어주고 있어, 만날수록 서로의 부족함이 채워지고 자존감이 회복되는 <strong>'상호보완형 황금 인연'</strong>입니다. 전생의 깊은 인연이 현생의 귀인으로 결실을 맺은 형국이며, 서로를 만난 후 사회적 성취와 심리적 안정이 비약적으로 상승합니다.
                </p>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #D97706; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #D97706; font-weight: 800;">Chapter 2. 실전 관계 조화 & 갈등 해결법</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #78350F; margin-top: 2px;">
                        {chapter2_title}
                    </h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14px; color: #92400E; line-height: 1.8;">
                    {chapter2_desc}
                </div>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #059669; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #059669; font-weight: 800;">Chapter 3. 시너지 및 복록</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #065F46; margin-top: 2px;">
                        {chapter3_title}
                    </h4>
                </div>
                <div style="color: #047857; font-size: 14px; line-height: 1.8;">
                    {chapter3_desc}
                </div>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #2D6A4F; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #2D6A4F; font-weight: 800;">Chapter 4. 인연을 백년해로로 이끄는 개운 비책</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #0F172A; margin-top: 2px;">
                        🌹 두 사람만의 행운의 방위 & 타이밍
                    </h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 6px; font-size: 14px; color: #475569;">
                    <p>• <strong>행운의 데이트 장소:</strong> 물이 잔잔히 흐르는 강변이나 클래식한 조명의 카페가 두 분의 유대감을 2배로 증폭시킵니다.</p>
                    <p>• <strong>추천 선물 아이템:</strong> 실버 톤의 메탈 시계나 은은한 천연 아로마 디퓨저가 두 분 사이의 애정 훈풍을 평생 지속시킵니다.</p>
                </div>
            </div>
        </div>
        """
    }

@app.post("/api/theme-report")
def get_theme_report(req: dict):
    theme = req.get("theme", "wealth")
    sub_opt = req.get("sub_option", "기본")
    user_name = req.get("name", "최정오")
    gender = req.get("gender", "male")
    
    titles = {"wealth": "💰 평생 재물운", "love": f"💖 평생 애정운 ({sub_opt})", "business": f"🏢 사업·직업운 ({sub_opt})", "health": "🌿 평생 건강운"}
    gender_term = "아내/재물(財星)" if gender == "male" else "남편/명예(官星)"

    if theme == "wealth":
        content = f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div style="border-left: 4px solid #D97706; padding-left: 10px;">
                <span style="font-size: 12px; color: #D97706; font-weight: 800;">Chapter 1. 평생 재물 원국 정밀 감명</span>
                <h4 style="font-size: 16.5px; font-weight: 800; color: #78350F; margin: 3px 0 6px;">[타고난 금고] '암장(暗藏) 황금 금고형' 자산 축적 원국</h4>
                <p style="color: #92400E; font-size: 14.5px; line-height: 1.85;">
                    {user_name}님의 사주는 겉으로 드러난 화려함보다 실속 있게 현금과 실물 자산을 차곡차곡 축적하는 전형적인 '황금 금고형' 명식입니다. 지장간 깊은 곳에 알짜배기 재성(財星)이 튼튼히 뿌리를 내리고 있어, 남들이 보지 못하는 틈새 기회를 포착하여 자산을 눈덩이처럼 불리는 능력이 탁월합니다.
                </p>
                <p style="color: #78350F; font-size: 13.5px; margin-top: 6px;">
                    초년에는 자금 흐름의 기복이 있을 수 있으나, 나이가 들수록 금고의 문이 굳건해져 헛돈 지출이 차단되고 평생 동안 안정적인 부를 누리게 되는 <strong>'부익부(富益富)의 대기만성형 사주'</strong>입니다.
                </p>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #2D6A4F; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #2D6A4F; font-weight: 800;">Chapter 2. 생애 주기별 4대 퀀텀점프 자산 로드맵</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #0F172A; margin-top: 2px;">📊 Q. {user_name}님의 생애 주기별 자산 대도약 시기는?</h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 14px; color: #475569;">
                    <p>• <strong>초년~30대 (종잣돈 형성기):</strong> 실물 경제 감각을 기르고 기초 종잣돈을 모으는 담금질의 시기였습니다. 다양한 경험을 통해 돈의 흐름을 읽는 안목이 완성되었습니다.</p>
                    <p style="color: #B45309; font-weight: 800;">• <strong>40대 중후반~50대 (*현재 황금기):</strong> 귀인의 결정적 조력과 과감한 투자 결단으로 자산 규모가 3배 이상 폭발적으로 도약하는 일생일대의 승부처입니다. 본인이 주도권을 쥔 사업이나 실물 투자에서 대성합니다.</p>
                    <p>• <strong>60대 이후 (자산 수성 및 완성기):</strong> 부동산 임대 수익, 우량 배당 등 고정 현금 흐름을 토대로 안락한 부를 누리며 자손에게 부를 안전하게 대물림합니다.</p>
                </div>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #2563EB; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #2563EB; font-weight: 800;">Chapter 3. 맞춤형 머니 파이프라인 & 대박 투자 종목</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #1E3A8A; margin-top: 2px;">📈 가장 유리한 재테크 vs 피해야 할 위험 자산</h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 6px; font-size: 14px; color: #1E40AF; line-height: 1.8;">
                    <p>• <strong>★대길 투자 종목:</strong> 입지가 탄탄한 수익형 부동산(상가·오피스), 독점적 기술을 가진 가치 우량 배당주, 안정적 국채 및 실물 금(Gold) 자산.</p>
                    <p>• <strong>⚠️ 기피 투자 종목:</strong> 변동성이 극단적인 초단타 선물/코인, 남의 말만 믿고 들어가는 비상장 지분 투자.</p>
                    <p>• <strong>자산 배분 황금 비율:</strong> 안전 실물 자산 55% : 우량 배당 자산 30% : 현금성 유동성 15%</p>
                </div>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #DC2626; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #DC2626; font-weight: 800;">Chapter 4. 손재수 완벽 차단 비책</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #991B1B; margin-top: 2px;">🛡️ 돈이 새어나가는 구멍 차단 솔루션</h4>
                </div>
                <p style="color: #451A03; font-size: 14px; line-height: 1.8;">
                    운이 상승할 때는 친인척이나 지인으로부터 솔깃한 동업/보증 제안이 들어옵니다. 사사로운 정에 얽매이지 않고 모든 금융 거래를 공증 및 문서화할 때 손재수를 0%로 완벽히 방어합니다. 지갑은 짙은 브라운이나 블랙 톤의 고급 가죽 지갑을 사용하고, 영수증을 즉시 비우는 습관이 금전운을 배가시킵니다.
                </p>
            </div>
        </div>
        """
    elif theme == "love":
        if sub_opt == "솔로":
            ch1_title = "💖 [솔로 탈출] 운명의 짝을 만나는 최고의 루트 & 장소"
            ch1_desc = f"""
            <p>• <strong>최고의 만남 방식:</strong> 자연스러운 길거리 헌팅보다는 <strong>'신뢰할 수 있는 멘토나 직장 동료의 주선 소개팅'</strong> 및 <strong>'전문 직무/취미 스터디 모임'</strong>에서 인연을 만날 때 성공률이 90%에 달합니다.</p>
            <p>• <strong>행운의 동선:</strong> 서북쪽과 정동쪽에 위치한 세련된 북카페, 미술관, 클래식한 와인바가 당신의 애정 기운을 강하게 깨워줍니다.</p>
            <p>• <strong>매력 어필 포인트:</strong> 과도한 꾸밈보다 단정하고 세련된 셔츠 룩과 지적인 경청 태도를 보여줄 때 상대방이 깊은 매력을 느낍니다.</p>
            """
            ch2_title = "👤 미래 배우자의 구체적 외모 & 성격 & 직업 프로필"
            ch2_desc = f"""
            <p>• <strong>외모 특징:</strong> 이목구비가 반듯하고 차분하고 맑은 눈빛을 지녔으며, 키가 훤칠하고 단정한 클래식 정장/셔츠 스타일이 잘 어울리는 세련된 외모입니다.</p>
            <p>• <strong>성격 및 기질:</strong> 겉은 쿨하고 냉철해 보이지만 내면은 당신을 묵묵히 챙겨주는 '외강내유형 든든한 조력자'입니다. 감정 기복이 적고 신뢰를 최우선으로 여깁니다.</p>
            <p>• <strong>추천 직업군:</strong> 공기업/공직자, 금융·회계 전문직, IT 기획자, 전문 자격사 등 안정성과 지적 역량을 겸비한 분야의 인물입니다.</p>
            <p>• <strong>나이 차이:</strong> 2~4살 연하 또는 동갑내기와 가장 이상적인 오행 화합을 이룹니다.</p>
            """
            ch3_title = "⏰ 인연이 닿는 골든타임 & 고백 성사 타이밍"
            ch3_desc = f"""
            <p>올해 상반기(양력 4~6월)와 가을(양력 9~11월)에 강력한 도화(桃花)의 훈풍이 불어옵니다. 첫 만남에서 너무 재기보다는 상대방의 가치관을 경청하며 솔직한 감정을 표현할 때 3번의 만남 안에 연인으로 발전합니다.</p>
            """
        elif sub_opt == "썸/짝사랑":
            ch1_title = "💘 상대방의 숨겨진 본심 & 현재 심리 상태 분석"
            ch1_desc = f"""
            <p>상대방 역시 {user_name}님에게 남다른 호감과 지적 매력을 느끼고 있으나, 먼저 다가가기 조심스러워 상황을 신중히 지켜보고 있습니다.</p>
            <p>당신의 호의가 단순한 친절인지 이성적 호감인지 확신을 원하고 있는 상태입니다.</p>
            """
            ch2_title = "🔥 썸에서 연인으로 직행하는 4단계 실전 화법 & 플러팅"
            ch2_desc = f"""
            <p>• <strong>1단계:</strong> 일상의 가벼운 공통 관심사(맛집, 영화, 취미) 공유로 친밀도 강화.</p>
            <p>• <strong>2단계:</strong> 상대방의 성취와 취향을 구체적으로 칭찬하여 '나를 알아주는 특별한 사람'이라는 인식 심기.</p>
            <p>• <strong>3단계:</strong> '이번 주말에 분위기 좋은 곳에서 맛있는 거 먹으러 가요'와 같이 자연스러운 1:1 약속 제안.</p>
            <p>• <strong>4단계:</strong> 저녁 식사 후 조용한 산책길에서 진심 어린 눈빛으로 확신을 주는 고백 건네기.</p>
            """
            ch3_title = "⚠️ 반드시 피해야 할 치명적인 밀당의 함정"
            ch3_desc = f"""
            <p>답장을 너무 늦게 하거나 떠보는 식의 질투 유발은 상대방의 자존심을 건드려 관계를 급랭시킵니다. 진정성 있는 다정함과 일관된 태도가 상대방의 마음을 완전히 여는 열쇠입니다.</p>
            """
        elif sub_opt == "연애중":
            ch1_title = "💍 결혼 결실을 맺는 골든타임 & 신뢰 증폭 비법"
            ch1_desc = f"""
            <p>두 사람의 기운이 온화하게 합을 이루는 시기입니다. 현실적인 재정 계획과 미래 가치관을 진솔하게 공유할 때 결혼 논의가 급물살을 탑니다.</p>
            <p>양가 부모님 인사와 프로포즈는 가을(양력 9~11월)에 진행할 때 만사형통으로 성사됩니다.</p>
            """
            ch2_title = "💡 연인 간 잦은 다툼 해결 & 권태기 극복 매뉴얼"
            ch2_desc = f"""
            <p>• 사소한 의견 차이가 생길 때는 메신저 다툼을 멈추고 직접 만나 손을 잡고 대화하세요.</p>
            <p>• 1박 2일 근교 힐링 여행이나 새로운 취미를 함께 시작할 때 권태기를 단숨에 날려줍니다.</p>
            <p>• 서로의 개인 시간과 영역을 존중해 줄 때 관계의 결속력이 2배로 단단해집니다.</p>
            """
            ch3_title = "🌹 두 사람의 사랑을 지켜주는 행운의 데이트"
            ch3_desc = f"""
            <p>야경이 아름다운 전망대나 조용한 강변 드라이브가 서로에 대한 애틋한 애정을 200% 증폭시킵니다.</p>
            """
        else:
            ch1_title = "🏡 부부 금슬 증폭 & 가문 재물운 합일 비책"
            ch1_desc = f"""
            <p>부부간의 신뢰가 곧 가문의 자산으로 직결되는 명식입니다. 서로의 노고를 인정하는 따뜻한 말 한마디가 집안에 황금 복록을 부릅니다.</p>
            <p>가정 내 재정 상태를 투명하게 공유하고 공동의 목표(부동산 청약, 노후 자산)를 설정할 때 부부 합일의 시너지가 극대화됩니다.</p>
            """
            ch2_title = "👶 자녀 번영 & 화목한 가정 환경 구축법"
            ch2_desc = f"""
            <p>자녀의 자율성을 존중하고 부모의 든든한 지지대를 보여줄 때 자녀의 학업운과 출세운이 대길하게 풀립니다.</p>
            <p>거실에 따뜻한 조명과 밝은 그림을 배치하여 집안의 양기를 북돋워 주세요.</p>
            """
            ch3_title = "✨ 부부 권태 방어 & 제2의 신혼 루틴"
            ch3_desc = f"""
            <p>매월 1회 부부만의 오붓한 외식 데이트를 정례화하고 일상 속 스킨십과 칭찬을 아끼지 마세요.</p>
            """

        content = f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div style="border-left: 4px solid #E11D48; padding-left: 10px;">
                <span style="font-size: 12px; color: #E11D48; font-weight: 800;">Chapter 1. 상태 맞춤 애정 원국 ({sub_opt})</span>
                <h4 style="font-size: 16.5px; font-weight: 800; color: #881337; margin: 3px 0 6px;">{ch1_title}</h4>
                <div style="color: #9F1239; font-size: 14.5px; line-height: 1.85;">
                    {ch1_desc}
                </div>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #D97706; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #D97706; font-weight: 800;">Chapter 2. 인연의 본질 & 디테일 프로필</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #78350F; margin-top: 2px;">{ch2_title}</h4>
                </div>
                <div style="color: #78350F; font-size: 14px; line-height: 1.8;">
                    {ch2_desc}
                </div>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #059669; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #059669; font-weight: 800;">Chapter 3. 실전 성공 로드맵</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #065F46; margin-top: 2px;">{ch3_title}</h4>
                </div>
                <div style="color: #047857; font-size: 14px; line-height: 1.8;">
                    {ch3_desc}
                </div>
            </div>
        </div>
        """
    elif theme == "business":
        if sub_opt == "취업/이직":
            b_ch1 = "🎯 [취업·이직 성공] 합격률 200% 승부처 & 면접 합격 비책"
            b_desc1 = f"""
            <p>• <strong>이직 골든타임:</strong> 상반기 3~5월과 하반기 9~11월에 당신의 이력서가 강력한 평가를 받습니다.</p>
            <p>• <strong>면접 필승 처세:</strong> 겸손한 태도 속에 본인의 실전 프로젝트 문제 해결 역량을 숫자로 당당하게 어필하세요.</p>
            <p>• <strong>연봉 협상:</strong> 본인의 성과 포트폴리오를 근거로 희망 연봉 상단을 제시할 때 15% 이상의 인상이 가능합니다.</p>
            """
            b_ch2 = "🏢 가장 운이 잘 풀리는 유망 직무 & 기업 형태"
            b_desc2 = f"""
            <p>대기업 기획실, 외국계 전문 직무, 공공기관 및 기술 기반 혁신 기업에서 당신의 직무 자율성이 극대화됩니다.</p>
            <p>단순 반복 업무보다는 전략 수립과 의사결정 권한이 주어지는 포지션에서 초고속 승진합니다.</p>
            """
        elif sub_opt == "사업가":
            b_ch1 = "🚀 [사업 확장 & 매출 폭발] 매출 3배 성장의 전환점"
            b_desc1 = f"""
            <p>• <strong>스케일업 타이밍:</strong> 기존 아이템의 내실을 다진 후 하반기에 신규 채널과 파트너십을 확장할 때 폭발적 매출이 일어납니다.</p>
            <p>• <strong>인사 관리:</strong> 실행력이 강한 실무 리더를 영입하고 권한을 위임할 때 사업 규모가 퀀텀점프합니다.</p>
            <p>• <strong>마케팅 전략:</strong> 충성 고객 중심의 바이럴과 프리미엄 포지셔닝이 객단가를 40% 끌어올립니다.</p>
            """
            b_ch2 = "💼 법률·세무 리스크 방어 & 관재구설수 차단"
            b_desc2 = f"""
            <p>세무 검증과 계약서 조항을 철저히 정비하여 관재수를 원천 차단하세요. 동업자나 주요 거래처와의 계약은 전문가 감수를 필수적으로 거치세요.</p>
            """
        elif sub_opt == "창업":
            b_ch1 = "💡 [성공 창업 가이드] 실패 없는 창업 아이템 & 상권 분석"
            b_desc1 = f"""
            <p>• <strong>대박 아이템:</strong> 전문 지식재산권 기반 서비스, 프리미엄 식음료/라이프스타일, B2B 솔루션 사업.</p>
            <p>• <strong>초기 전략:</strong> 고정비를 최소화하는 린(Lean) 스타트업 방식으로 시작하여 6개월 내 손익분기점을 달성하세요.</p>
            <p>• <strong>상권 입지:</strong> 유동인구가 꾸준하고 배후 세대가 탄탄한 역세권 인근이 최적의 명당입니다.</p>
            """
            b_ch2 = "🤝 투자 유치 & 동업 파트너십 수칙"
            b_desc2 = f"""
            <p>지분 구조를 7:3 이상으로 확고히 쥐고 대표의 경영권을 지킬 때 투자 유치와 정부 지원 사업이 순조롭습니다.</p>
            """
        else:
            b_ch1 = "🎖️ [직장인 초고속 승진] 사내 핵심 인재로 인정받는 처세술"
            b_desc1 = f"""
            <p>• <strong>승진 타이밍:</strong> 올해 인사 평가에서 당신의 기획안이 상급자의 두터운 신임을 얻습니다.</p>
            <p>• <strong>사내 정치 돌파:</strong> 잡음에 휩쓸리지 않고 독보적인 실적과 데이터로 증명할 때 파격 승진의 길이 열립니다.</p>
            <p>• <strong>핵심 성과 창출:</strong> 조직의 병목 현상을 해결하는 개선안을 선제적으로 보고하세요.</p>
            """
            b_ch2 = "👔 상사 및 팀원과의 황금 파트너십 구축"
            b_desc2 = f"""
            <p>상급자의 가려운 곳을 긁어주는 보고서 작성과 팀원들을 배려하는 리더십으로 사내에서 대체 불가능한 인망을 얻으세요.</p>
            """

        content = f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div style="border-left: 4px solid #2563EB; padding-left: 10px;">
                <span style="font-size: 12px; color: #2563EB; font-weight: 800;">Chapter 1. 직무/사업 맞춤 운세 ({sub_opt})</span>
                <h4 style="font-size: 16.5px; font-weight: 800; color: #1E3A8A; margin: 3px 0 6px;">{b_ch1}</h4>
                <div style="color: #1E40AF; font-size: 14.5px; line-height: 1.85;">
                    {b_desc1}
                </div>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #059669; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #059669; font-weight: 800;">Chapter 2. 유망 분야 & 실전 처세</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #065F46; margin-top: 2px;">{b_ch2}</h4>
                </div>
                <div style="color: #047857; font-size: 14px; line-height: 1.8;">
                    {b_desc2}
                </div>
            </div>
        </div>
        """
    else:
        content = f"""
        <div style="display: flex; flex-direction: column; gap: 16px; font-size: 14.5px; color: #334155; line-height: 1.85; text-align: left;">
            <div style="border-left: 4px solid #059669; padding-left: 10px;">
                <span style="font-size: 12px; color: #059669; font-weight: 800;">Chapter 1. 오행 체질 장부 정밀 분석</span>
                <h4 style="font-size: 16.5px; font-weight: 800; color: #065F46; margin: 3px 0 6px;">[평생 체질] 수승화강(水昇火降) 활력과 선천적 취약점</h4>
                <p style="color: #047857; font-size: 14.5px; line-height: 1.85;">
                    {user_name}님은 타고난 생명력과 지구력이 우수하나, 심장·혈관(火)의 열기가 머리로 치솟거나 간 피로(木)가 누적되기 쉬운 체질입니다. 두한족열(머리는 시원하게, 발은 따뜻하게)의 기본 수칙을 유지해야 평생 에너지가 고갈되지 않습니다.
                </p>
                <p style="color: #065F46; font-size: 13.5px; margin-top: 6px;">
                    스트레스가 극에 달할 때는 위장 장애나 수면 장애로 이어질 수 있으므로 감정 정화 루틴이 무엇보다 중요합니다.
                </p>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #D97706; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #D97706; font-weight: 800;">Chapter 2. 생애 주기별 필수 체크포인트</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #78350F; margin-top: 2px;">🏥 정기 검진 및 장기 케어 가이드</h4>
                </div>
                <div style="display: flex; flex-direction: column; gap: 6px; font-size: 14px; color: #78350F; line-height: 1.8;">
                    <p>• <strong>심혈관 & 혈압:</strong> 나트륨 섭취를 줄이고 유산소 운동으로 혈행을 원활히 유지하세요.</p>
                    <p>• <strong>척추 및 관절:</strong> 오랜 좌식 업무 시 허리 스트레칭과 바른 자세 유지가 필수입니다.</p>
                    <p>• <strong>간 피로 회복:</strong> 음주 후 충분한 수분 섭취와 밀크씨슬 섭취를 권장합니다.</p>
                </div>
            </div>

            <div style="border-top: 2px solid #FCD34D; margin: 4px 0;"></div>

            <div>
                <div style="border-left: 4px solid #2563EB; padding-left: 10px; margin-bottom: 8px;">
                    <span style="font-size: 12px; color: #2563EB; font-weight: 800;">Chapter 3. 맞춤 약선 식단 & 힐링 루틴</span>
                    <h4 style="font-size: 16.5px; font-weight: 800; color: #1E3A8A; margin-top: 2px;">🍵 기력 회복 약선차 & 운동법</h4>
                </div>
                <p style="color: #1E40AF; font-size: 14px; line-height: 1.8;">
                    도라지차, 구기자차, 신선한 녹황색 채소와 견과류를 곁들이세요. 주 3회 40분간의 빠른 걷기나 수영이 사주 오행의 막힌 혈을 시원하게 뚫어줍니다.
                </p>
            </div>
        </div>
        """

    return {
        "title": titles.get(theme, "심층 리포트"),
        "content": content
    }
