import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional
import os

app = FastAPI(title="운세의 신 PRO API", version="5.2.0")

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

# 4대 사주 맞춤 부적 마스터 (사주 오행 및 일간에 따라 실시간 매칭)
TALISMAN_TYPE_MAP = {
    "wealth": {"type": "wealth", "title": "재물만복부 (萬福符)", "power": "재물 증식 · 금전운 대통", "desc": "사방에서 금전과 복록이 샘솟듯 모여들고 헛돈 누수를 철통같이 차단하는 강력한 전통 경면주사 수제 부적입니다."},
    "love": {"type": "love", "title": "천생화합부 (和合符)", "power": "애정 결속 · 인연운 대길", "desc": "서로의 기운을 조화롭게 묶어주고 엇갈린 인연의 오해를 풀어 평생의 신뢰와 화목을 완성하는 비급 부적입니다."},
    "business": {"type": "business", "title": "사업대성부 (亨通符)", "power": "사업 번창 · 계약 성사", "desc": "막혔던 활로를 시원하게 뚫어주고 귀인의 조력과 승진·사업적 대성취를 견인하는 전통 수제 부적입니다."},
    "health": {"type": "health", "title": "무병장수부 (延壽符)", "power": "심신 정화 · 기력 회복", "desc": "오행의 탁한 기운을 정화하고 수승화강의 원리를 통해 평생의 원기와 활력을 지켜주는 수호 부적입니다."}
}

TAROT_CARDS = [
    {
        "name": "0. THE FOOL (바보)",
        "keyword": "새로운 시작 · 순수한 열정 · 무한한 잠재력",
        "symbolism": "화려한 옷을 입고 절벽 끝에 서 있는 청년은 세상의 관습에 얽매이지 않는 순수한 영혼과 새로운 여정의 출발을 상징합니다. 손에 쥔 하얀 장미는 순수성을, 곁의 하얀 개는 본능적인 위험 경고와 충성을 뜻합니다.",
        "fortune_reading": "오늘은 오랫동안 머뭇거리던 일의 시작 단추를 꿰기에 더없이 좋은 날입니다. 과거의 실패나 주변의 지나친 참견에 신경 쓰지 않고, 본인의 순수한 호기심과 직관을 따를 때 예상 밖의 통로가 시원하게 열립니다. 계산기를 두드리기보다는 일단 가벼운 마음으로 발을 내딛는 것이 핵심입니다.",
        "advice": "새로운 프로젝트 구상이나 이직/취미/약속 등 새로운 제안에 열린 마음을 가지세요. 다만 준비 없는 무모함은 피하고, 발걸음은 경쾌하되 시선은 주변을 살피는 지혜가 필요합니다.",
        "action_tip": "오늘 떠오르는 새로운 아이디어를 즉시 메모하고, 망설이던 연락을 먼저 건네보세요."
    },
    {
        "name": "I. THE MAGICIAN (마법사)",
        "keyword": "창조적 역량 · 완벽한 주도권 · 실력 발휘",
        "symbolism": "머리 위의 무한대(∞) 기호와 제단 위의 4대 원소(지팡이, 컵, 검, 동전)는 세상의 모든 도구와 자원을 능숙하게 통제할 수 있는 탁월한 지혜와 창조력을 상징합니다.",
        "fortune_reading": "귀하가 가진 지식, 언변, 전문 기술이 빛을 발하는 날입니다. 상대방을 설득하거나 협상을 주도하기에 최고의 컨디션이며, 막혀 있던 프로젝트도 귀하의 기지로 실마리를 풀 수 있습니다. 자신의 역량을 겸손 뒤에 숨기지 말고 자신 있게 세상에 드러내야 복이 들어옵니다.",
        "advice": "미팅이나 보고, 프레젠테이션에서 당당한 태도로 분위기를 리드하세요. 철저한 사전 준비가 뒷받침될 때 원하는 성과와 명예를 온전히 거머쥘 수 있습니다.",
        "action_tip": "중요한 대화나 업무에서 본인의 핵심 주장을 당당하고 명확하게 피력하세요."
    },
    {
        "name": "II. THE HIGH PRIESTESS (여사제)",
        "keyword": "깊은 통찰 · 직관과 혜안 · 침묵의 지혜",
        "symbolism": "흑과 백의 기둥 사이에 앉아 스크롤을 쥔 여사제는 이성과 감성의 조화, 표면 아래 숨겨진 본질적 진실을 상징합니다.",
        "fortune_reading": "겉으로 드러난 말보다 상대방의 숨은 의도나 상황의 이면을 꿰뚫어 보는 혜안이 극대화되는 날입니다. 성급하게 반응하기보다는 차분히 경청하고 심사숙고하세요.",
        "advice": "중요한 결정은 하루 이틀 여유를 두고 결정하세요.",
        "action_tip": "조용한 장소에서 생각을 차분히 정리하는 시간을 가지세요."
    }
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
    return HTMLResponse("<h2>운세의 신 PRO 준비 중</h2>")

@app.post("/api/analyze")
def analyze_saju(req: SajuRequest):
    base_date = datetime.date(1900, 1, 1)
    target_date = datetime.date(req.year, req.month, req.day)
    diff_days = (target_date - base_date).days
    
    d_cg_idx = (diff_days + 0) % 10
    d_jj_idx = (diff_days + 10) % 12
    d_cg = CHEONGAN_HANJA[d_cg_idx]
    d_jj = JIJI_HANJA[d_jj_idx]

    year_offset = (req.year - 4) % 60
    y_cg_idx = year_offset % 10
    y_jj_idx = year_offset % 12
    y_cg, y_jj = CHEONGAN_HANJA[y_cg_idx], JIJI_HANJA[y_jj_idx]

    m_jj_idx = (req.month) % 12
    m_cg_idx = (y_cg_idx % 5 * 2 + 2 + (req.month - 2)) % 10
    m_cg, m_jj = CHEONGAN_HANJA[m_cg_idx], JIJI_HANJA[m_jj_idx]

    if req.is_unknown_time or req.sijin_index is None or req.sijin_index < 0:
        h_pillar, h_cg, h_jj = "時未詳", "-", "-"
    else:
        h_jj_idx = req.sijin_index
        h_cg_idx = (d_cg_idx % 5 * 2 + h_jj_idx) % 10
        h_cg, h_jj = CHEONGAN_HANJA[h_cg_idx], JIJI_HANJA[h_jj_idx]
        h_pillar = f"{h_cg}{h_jj}"

    d_animal = ANIMAL_MAP.get(d_jj, "개")

    current_year = datetime.date.today().year
    current_age = current_year - req.year + 1

    pillars_detail = {
        "hour": {
            "cg": h_cg, "cg_elem": CHEONGAN_ELEMENTS.get(h_cg, "none"),
            "jj": h_jj, "jj_elem": JIJI_ELEMENTS.get(h_jj, "none"),
            "jijanggan": JIJANGGAN_FULL_MAP.get(h_jj, [])
        },
        "day": {
            "cg": d_cg, "cg_elem": CHEONGAN_ELEMENTS.get(d_cg, "none"),
            "jj": d_jj, "jj_elem": JIJI_ELEMENTS.get(d_jj, "none"),
            "jijanggan": JIJANGGAN_FULL_MAP.get(d_jj, [])
        },
        "month": {
            "cg": m_cg, "cg_elem": CHEONGAN_ELEMENTS.get(m_cg, "none"),
            "jj": m_jj, "jj_elem": JIJI_ELEMENTS.get(m_jj, "none"),
            "jijanggan": JIJANGGAN_FULL_MAP.get(m_jj, [])
        },
        "year": {
            "cg": y_cg, "cg_elem": CHEONGAN_ELEMENTS.get(y_cg, "none"),
            "jj": y_jj, "jj_elem": JIJI_ELEMENTS.get(y_jj, "none"),
            "jijanggan": JIJANGGAN_FULL_MAP.get(y_jj, [])
        }
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
    elem_percentages = {
        k: round((v / total_score) * 100, 1) for k, v in scores.items()
    }

    # 사용자 사주 일간(日干) 기반 맞춤 부적 자동 선택
    # 甲/乙(목): 사업대성부, 丙/丁(화): 재물만복부, 戊/己(토): 금고수호부, 庚/辛(금): 천생화합부, 壬/癸(수): 무병장수부
    talisman_key_map = {
        "甲": "business", "乙": "business",
        "丙": "wealth", "丁": "wealth",
        "戊": "wealth", "己": "wealth",
        "庚": "love", "辛": "love",
        "壬": "health", "癸": "health"
    }
    user_talisman_type = talisman_key_map.get(d_cg, "wealth")
    user_talisman = TALISMAN_TYPE_MAP.get(user_talisman_type, TALISMAN_TYPE_MAP["wealth"])

    user_mbti = DAY_MBTI_MAP.get(d_cg, {"mbti": "대담한 통솔자 (ENTJ형)", "desc": "강한 추진력과 당당한 리더십으로 조직을 이끄는 개척자 사주"})
    user_animal_icon = ANIMAL_ICONS.get(d_animal, "🐶")

    return {
        "user_name": req.name,
        "current_age": current_age,
        "saju_data": {
            "year_pillar": f"{y_cg}{y_jj}",
            "month_pillar": f"{m_cg}{m_jj}",
            "day_pillar": f"{d_cg}{d_jj}",
            "hour_pillar": h_pillar,
            "pillars_detail": pillars_detail,
            "mbti": user_mbti,
            "animal_symbol": d_animal,
            "animal_icon": user_animal_icon,
            "elements": elem_percentages
        },
        "daily_fortune": {
            "score": 97,
            "title": f"{d_cg} 기운이 서서히 솟아나는 도약의 하루",
            "advice": f"오전에는 귀인의 조력과 반가운 연락이 닿고, 오후에는 결단력과 추진력이 극대화되어 중요한 문서나 협상을 성사시키기에 최적의 날입니다.",
            "lucky_color": "스카이 블루 / 아이보리",
            "lucky_number": "1, 6",
            "lucky_direction": "정북쪽",
            "fashion_style": "단정하고 편안한 셔츠 또는 니트",
            "recommended_menu": "신선한 채소와 담백한 단백질 식단",
            "mindset": "상대의 말에 공감하고 핵심을 명확히 전달하기",
            "action": "오전 중 따뜻한 차 한 잔을 마시며 목표 3가지 메모하기",
            "talisman": user_talisman
        }
    }

@app.get("/api/daily-tarot")
def get_daily_tarot(slot: int = 1, rand_seed: Optional[str] = None):
    seed_val = int(rand_seed or str(datetime.date.today().toordinal()))
    idx = (seed_val + slot * 3) % len(TAROT_CARDS)
    return TAROT_CARDS[idx]

@app.post("/api/daewoon-report")
def get_daewoon_report(req: dict):
    user_name = req.get("name", "최정오")
    age = req.get("age", 49)
    age_decade = (age // 10) * 10
    start_age = age_decade + 3
    end_age = start_age + 9

    return {
        "title": f"👑 {user_name}님의 자미두수 & 10년 대운 심층 리포트",
        "content": f"""
        <div style="display: flex; flex-direction: column; gap: 14px; font-size: 12px; color: #334155; line-height: 1.65; text-align: left;">
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 16px; padding: 14px;">
                <h4 style="font-size: 13px; font-weight: 900; color: #0F172A; border-bottom: 1px solid #E2E8F0; padding-bottom: 8px; margin-bottom: 10px;">
                    🌐 1. {user_name}님의 평생 생애 주기별 대운맥(大運脈) 흐름
                </h4>
                <div style="display: flex; flex-direction: column; gap: 10px; font-size: 11px;">
                    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 10px;">
                        <p style="font-weight: 800; color: #0F172A; margin-bottom: 4px;">🌱 [유년기 (년주 기반 / 0세 ~ 19세) : 기틀 형성 및 학업기]</p>
                        <p style="color: #475569; line-height: 1.65;">타고난 영민함과 지적 호기심으로 내면의 가치관과 도덕적 기틀을 확립하던 시기입니다. 초년의 환경적 변화 속에서도 스스로 중심을 잡고 잠재력을 키워냈습니다.</p>
                    </div>
                    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 10px;">
                        <p style="font-weight: 800; color: #0F172A; margin-bottom: 4px;">🌿 [청년기 (월주 기반 / 20세 ~ 39세) : 도약 탐색 및 역량 구축기]</p>
                        <p style="color: #475569; line-height: 1.65;">사회에 진출하여 실전 경험과 전문성을 갈고닦으며 자신의 진가를 입증해 나간 시기입니다. 실패를 성공의 자산으로 바꾸는 혜안과 네트워크를 탄탄히 다졌습니다.</p>
                    </div>
                    <div style="background: #FEF3C7; border: 1.5px solid #FCD34D; border-radius: 12px; padding: 10px;">
                        <p style="font-weight: 900; color: #78350F; margin-bottom: 4px;">🔥 [중장년기 (*현재 일주 기반 / 40세 ~ 59세) : 황금 자산 결실기]</p>
                        <p style="color: #92400E; line-height: 1.65;"><strong>{user_name}님 인생 일대에서 가장 강력한 천운의 파도가 솟구치는 최고 하이라이트 구간입니다.</strong> 사회적 주도권을 잡고 자산과 명예의 결실이 폭발적으로 확장됩니다.</p>
                    </div>
                    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 10px;">
                        <p style="font-weight: 800; color: #0F172A; margin-bottom: 4px;">🍎 [말년기 (시주 기반 / 60세 이후) : 태평성대 및 명예 완성기]</p>
                        <p style="color: #475569; line-height: 1.65;">평생 축적한 부와 지혜를 토대로 안락하고 평온한 노후를 누리며 존경받는 원로로서 가문 번영을 완성합니다.</p>
                    </div>
                </div>
            </div>

            <div style="background: #FFFBEB; border: 1.5px solid #FDE68A; border-radius: 16px; padding: 14px;">
                <h4 style="font-size: 13px; font-weight: 900; color: #78350F; border-bottom: 1px solid #FCD34D; padding-bottom: 8px; margin-bottom: 10px;">
                    📈 2. {user_name}님의 현재 10년 대운 정밀 감명 ({start_age}세 ~ {end_age}세)
                </h4>
                <div style="margin-bottom: 12px; line-height: 1.65;">
                    <p style="font-weight: 800; color: #92400E; margin-bottom: 3px;">[대운의 본질과 주도권]</p>
                    <p style="color: #78350F;">본원에 귀인과 재성의 기운이 결합하는 시기로, 본인이 직접 판을 설계하고 이끌어가는 독보적인 리더십이 발현되는 10년의 절정기입니다.</p>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 11px; background: rgba(254,243,199,0.7); border-radius: 12px; padding: 12px;">
                    <p style="font-weight: 900; color: #78350F; font-size: 11.5px; margin-bottom: 2px;">[세운별 핵심 분기점 ({start_age}세 ~ {end_age}세)]</p>
                    <p style="color: #475569; line-height: 1.55;">• <strong>{start_age}세 ~ {start_age+2}세 (도입기):</strong> 고정 비용 정돈 및 안전 자산 중심 종잣돈 재배치.</p>
                    <p style="color: #B45309; font-weight: 900; line-height: 1.55; background: #FEF3C7; padding: 4px 6px; border-radius: 6px;">• <strong>{start_age+3}세 ~ {start_age+6}세 (정점기 / ★현재 {age}세 위치):</strong> 귀인의 결정적 조력과 함께 직위·자산이 수직 상승하는 황금 전환점.</p>
                    <p style="color: #475569; line-height: 1.55;">• <strong>{start_age+7}세 ~ {end_age}세 (결실기):</strong> 성과를 안정적 시스템 수익으로 확정 짓고 차기 대운으로의 연착륙.</p>
                </div>
            </div>
        </div>
        """
    }

# 4대 테마운 롱폼 심층 리포트 (재물운 수준의 3단 완벽 대등 구성)
@app.post("/api/theme-report")
def get_theme_report(req: dict):
    theme = req.get("theme", "wealth")
    sub_opt = req.get("sub_option", "기본")
    user_name = req.get("name", "최정오")
    
    titles = {
        "wealth": f"💰 {user_name}님의 평생 재물 그릇 & 금고운 심층 리포트",
        "love": f"💖 {user_name}님의 평생 애정운 & 인연법 ({sub_opt} 맞춤)",
        "business": f"🏢 {user_name}님의 사업 & 직업 성공 대길운 ({sub_opt} 맞춤)",
        "health": f"🌿 {user_name}님의 평생 오행 체질 & 건강 개운법"
    }

    contents = {
        "wealth": f"""
        <div style="display: flex; flex-direction: column; gap: 14px; font-size: 12px; color: #334155; line-height: 1.65; text-align: left;">
            <div style="background: #FFFBEB; border: 1.5px solid #FCD34D; border-radius: 16px; padding: 14px;">
                <span style="font-size: 10px; background: #D97706; color: white; padding: 2px 6px; border-radius: 6px; font-weight: 900;">원국 정밀 감명</span>
                <h4 style="font-size: 13px; font-weight: 900; color: #78350F; margin: 4px 0 6px;">[평생 재물 그릇] '암장(暗藏) 금고형' 자산 축적 원국</h4>
                <p style="color: #92400E; font-size: 11px; line-height: 1.6;">
                    {user_name}님의 사주는 겉으로 드러난 화려함보다 실속 있게 현금과 실물 자산을 차곡차곡 축적하는 전형적인 '황금 금고형' 구조입니다. 
                    지장간 속에 알짜배기 편재와 정재가 은밀하게 뿌리를 내리고 있어, 남들이 보지 못하는 틈새 기회를 포착하여 자산을 불리는 능력이 탁월합니다. 
                    단기적인 시세 차익이나 투기적 성격의 주식보다는, 시간이 지날수록 가치가 상승하는 실물 부동산과 우량 배당 자산 중심의 포트폴리오가 운명을 견인합니다.
                </p>
            </div>
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 14px; padding: 12px;">
                <p style="font-weight: 800; color: #0F172A; font-size: 12px; margin-bottom: 4px;">📊 1. {user_name}님의 생애 자산 증식 3단계 로드맵</p>
                <div style="display: flex; flex-direction: column; gap: 6px; font-size: 11px; color: #475569;">
                    <p>• <strong>초년~30대 (씨앗 축적기):</strong> 종잣돈을 모으고 금융/실물 경제의 원리를 체득하며 자산 운용의 안목을 기르는 시기였습니다.</p>
                    <p>• <strong>40대 중후반~50대 (*현재 황금기):</strong> 귀인의 도움과 부동산/사업적 결단으로 자산의 규모가 3배 이상 폭발적으로 퀀텀점프하는 최상의 전환점입니다.</p>
                    <p>• <strong>60대 이후 (임대/배당 태평기):</strong> 고정적인 현금 흐름을 바탕으로 자손에게 부를 안전하게 대물림하는 완벽한 자산 수성기입니다.</p>
                </div>
            </div>
            <div style="background: #ECFDF5; border: 1px solid #A7F3D0; border-radius: 14px; padding: 12px;">
                <p style="font-weight: 800; color: #065F46; font-size: 12px; margin-bottom: 4px;">💡 2. 재물운을 극대화하는 실전 개운(開運) 솔루션</p>
                <p style="font-size: 11px; color: #047857; line-height: 1.6;">
                    • <strong>행운의 방위:</strong> 주거지나 사무실 기준 '정북쪽'과 '동북쪽'이 재물이 샘솟는 황금 방위입니다.<br>
                    • <strong>금전 누수 방어법:</strong> 지갑 안에 현금을 항상 짝수 매수로 정돈하여 넣고, 노란색이나 짙은 갈색 소품을 휴대하면 헛돈 지출이 철통같이 차단됩니다.<br>
                    • <strong>문서 계약 대길 타이밍:</strong> 음력 4월, 8월, 12월에 체결하는 부동산이나 투자 계약이 평생의 거대한 복록을 부릅니다.
                </p>
            </div>
        </div>
        """,
        "love": f"""
        <div style="display: flex; flex-direction: column; gap: 14px; font-size: 12px; color: #334155; line-height: 1.65; text-align: left;">
            <div style="background: #FFF1F2; border: 1.5px solid #FECDD3; border-radius: 16px; padding: 14px;">
                <span style="font-size: 10px; background: #E11D48; color: white; padding: 2px 6px; border-radius: 6px; font-weight: 900;">상태 맞춤: {sub_opt}</span>
                <h4 style="font-size: 13px; font-weight: 900; color: #881337; margin: 4px 0 6px;">[평생 인연법] 깊은 신뢰와 상호 존중을 완성하는 천생연분</h4>
                <p style="color: #9F1239; font-size: 11px; line-height: 1.6;">
                    {user_name}님의 애정 원국은 가벼운 감정의 불꽃보다는 한 번 맺은 신뢰를 평생 지켜나가는 우직하고 따뜻한 포용력의 소유자입니다. 
                    현재 상태({sub_opt})를 고려할 때, 상대방에게 일방적으로 맞추기보다는 본인의 생각과 비전을 솔직하게 공유할 때 둘 사이의 유대감이 더욱 깊어집니다. 
                    겉으로 표현하지 않는 내면의 외로움이나 고민을 따뜻하게 안아주고 존중해 줄 수 있는 지혜로운 배필과 최고의 시너지를 발휘합니다.
                </p>
            </div>
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 14px; padding: 12px;">
                <p style="font-weight: 800; color: #0F172A; font-size: 12px; margin-bottom: 4px;">💞 1. {user_name}님과 운명적으로 통하는 상대방의 특징</p>
                <div style="display: flex; flex-direction: column; gap: 6px; font-size: 11px; color: #475569;">
                    <p>• <strong>성향과 인품:</strong> 감정 기복이 적고 원칙이 뚜렷하며, 대화 시 상대방의 이야기를 깊이 경청해 주는 차분한 스타일.</p>
                    <p>• <strong>외모 및 이미지:</strong> 부드럽고 온화한 인상에 단정하고 세련된 옷차림을 선호하며 지적인 분위기를 풍기는 사람.</p>
                    <p>• <strong>오행 궁합 조화:</strong> {user_name}님 사주에 꼭 필요한 水(물)과 金(쇠)의 차분한 기운을 채워줄 수 있는 띠(쥐띠, 닭띠, 원숭이띠)와 대길연(大吉緣)을 이룹니다.</p>
                </div>
            </div>
            <div style="background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 14px; padding: 12px;">
                <p style="font-weight: 800; color: #78350F; font-size: 12px; margin-bottom: 4px;">🌹 2. 관계를 화목하게 유지하는 관계 처세 비결</p>
                <p style="font-size: 11px; color: #92400E; line-height: 1.6;">
                    • <strong>소통의 법칙:</strong> 서운한 감정이 들 때는 즉각 반응하기보다 반나절 정도 생각을 정리한 후 부드러운 화법으로 전달하세요.<br>
                    • <strong>행운의 데이트/힐링 장소:</strong> 물이 잔잔하게 흐르는 호수 주변, 조용한 미술관이나 테라스가 있는 카페가 두 사람의 기운을 조화롭게 묶어줍니다.<br>
                    • <strong>인연운 상승 액션:</strong> 상대방에게 사소하지만 진심 어린 칭찬 한마디를 매일 건네면 가정과 연애 전선에 따뜻한 봄바람이 지속됩니다.
                </p>
            </div>
        </div>
        """,
        "business": f"""
        <div style="display: flex; flex-direction: column; gap: 14px; font-size: 12px; color: #334155; line-height: 1.65; text-align: left;">
            <div style="background: #EFF6FF; border: 1.5px solid #BFDBFE; border-radius: 16px; padding: 14px;">
                <span style="font-size: 10px; background: #2563EB; color: white; padding: 2px 6px; border-radius: 6px; font-weight: 900;">직업군 맞춤: {sub_opt}</span>
                <h4 style="font-size: 13px; font-weight: 900; color: #1E3A8A; margin: 4px 0 6px;">[사업 & 직업 성공] 치밀한 기획력과 결단력으로 조직을 이끄는 수장</h4>
                <p style="color: #1E40AF; font-size: 11px; line-height: 1.6;">
                    {user_name}님의 사주는 복잡하게 얽힌 문제의 핵심을 단번에 꿰뚫고 시스템을 정돈하는 탁월한 전략가이자 해결사의 기질을 타고났습니다. 
                    현재 직업군({sub_opt})에서 남들이 기피하거나 어려워하는 난제를 기지로 해결하며 대체 불가능한 핵심 리더로서 두각을 나타내게 됩니다. 
                    자신의 전문 역량을 데이터화하고 신뢰를 쌓아갈 때, 상급자나 대형 파트너사로부터 파격적인 협업 제안과 승진·사업 확장의 활로가 열립니다.
                </p>
            </div>
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 14px; padding: 12px;">
                <p style="font-weight: 800; color: #0F172A; font-size: 12px; margin-bottom: 4px;">🚀 1. {user_name}님의 대박 직무 분야 및 사업 아이템</p>
                <div style="display: flex; flex-direction: column; gap: 6px; font-size: 11px; color: #475569;">
                    <p>• <strong>추천 핵심 직무:</strong> 전략 기획, 경영 컨설팅, IT/기술 매니지먼트, 금융·투자 분석 등 구조와 프로세스를 설계하는 분야.</p>
                    <p>• <strong>창업 및 사업 방향:</strong> 지식 기반 플랫폼, 전문 라이선스 비즈니스, 유통/물류 시스템 혁신 등 무형의 노하우를 자산화하는 사업 모델에 최적입니다.</p>
                    <p>• <strong>조직 내 최적 포지션:</strong> 현장 실무자를 거쳐 최종 승인권과 기획권을 쥔 총괄 디렉터(C-Level) 자리에서 잠재력이 200% 발현됩니다.</p>
                </div>
            </div>
            <div style="background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 14px; padding: 12px;">
                <p style="font-weight: 800; color: #78350F; font-size: 12px; margin-bottom: 4px;">💼 2. 승진·이직·사업 대성을 위한 실전 처세 가이드</p>
                <p style="font-size: 11px; color: #92400E; line-height: 1.6;">
                    • <strong>인맥 관리 비결:</strong> '기브 앤 테이크'의 원칙을 지키되, 능력 있는 아랫사람을 너그럽게 품어줄 때 그들이 평생의 충성스러운 조력자가 됩니다.<br>
                    • <strong>이직/창업 대길 시기:</strong> 가을(양력 9~11월)과 초봄(양력 2~3월)에 들어오는 스카우트 제의나 신규 사업 론칭이 큰 명예를 안겨줍니다.<br>
                    • <strong>사무 공간 개운법:</strong> 책상을 출입문이 대각선으로 보이는 안정된 자리에 배치하고, 컴퓨터 옆에 작은 금속제 소품을 두면 집중력과 계약 성사율이 극대화됩니다.
                </p>
            </div>
        </div>
        """,
        "health": f"""
        <div style="display: flex; flex-direction: column; gap: 14px; font-size: 12px; color: #334155; line-height: 1.65; text-align: left;">
            <div style="background: #ECFDF5; border: 1.5px solid #A7F3D0; border-radius: 16px; padding: 14px;">
                <span style="font-size: 10px; background: #059669; color: white; padding: 2px 6px; border-radius: 6px; font-weight: 900;">오행 체질 정밀 분석</span>
                <h4 style="font-size: 13px; font-weight: 900; color: #065F46; margin: 4px 0 6px;">[평생 건강 & 체질] 왕성한 에너지와 수승화강(水昇火降) 관리 사주</h4>
                <p style="color: #047857; font-size: 11px; line-height: 1.6;">
                    {user_name}님의 오행 체질은 목(木)과 토(土)의 기운이 왕성하여 강인한 생명력과 추진력을 갖추고 있으나, 상대적으로 수(水)와 금(金) 기운의 보충이 필수적입니다. 
                    체내의 열기가 상체로 몰리기 쉬우므로 두한족열(頭寒足熱, 머리는 시원하게 발은 따뜻하게)의 기본 건강 수칙을 철저히 유지해야 합니다. 
                    스트레스가 누적될 경우 간 피로와 소화기계의 더부룩함으로 신호가 올 수 있으므로, 규칙적인 유산소 운동과 수분 섭취로 체내 순환을 원활히 돕는 것이 100세 건강의 비결입니다.
                </p>
            </div>
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 14px; padding: 12px;">
                <p style="font-weight: 800; color: #0F172A; font-size: 12px; margin-bottom: 4px;">🏥 1. {user_name}님이 각별히 챙겨야 할 3대 취약 장기</p>
                <div style="display: flex; flex-direction: column; gap: 6px; font-size: 11px; color: #475569;">
                    <p>• <strong>간장 & 담낭 (木 기운 조절):</strong> 만성 피로와 눈의 침침함을 방지하기 위해 과도한 음주를 피하고 밀크씨슬 등 간 보호 성분을 꾸준히 섭취하세요.</p>
                    <p>• <strong>신장 & 방광 (水 기운 보충):</strong> 체내 노폐물 배출과 진액 관리를 위해 하루 1.5L 이상의 미온수를 나누어 마시는 습관이 필수적입니다.</p>
                    <p>• <strong>위장 & 비장 (土 기운 순환):</strong> 불규칙한 식사나 야식을 지양하고, 자극적인 음식보다는 따뜻하고 담백한 식단을 유지해야 소화 흡수력이 강화됩니다.</p>
                </div>
            </div>
            <div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 14px; padding: 12px;">
                <p style="font-weight: 800; color: #1E3A8A; font-size: 12px; margin-bottom: 4px;">🌿 2. 평생 활력을 완성하는 일상 개운 섭생 루틴</p>
                <p style="font-size: 11px; color: #1E40AF; line-height: 1.6;">
                    • <strong>추천 보양 식재료:</strong> 검은콩, 흑임자, 미역 등 해조류와 신선한 녹색 잎채소가 부족한 수기(水氣)를 가득 채워줍니다.<br>
                    • <strong>취침 전 힐링 루틴:</strong> 매일 밤 15분간 따뜻한 족욕을 통해 하체의 순환을 돕고 숙면을 취하면 하루 동안 쌓인 탁한 기운이 깨끗이 정화됩니다.<br>
                    • <strong>추천 운동 요법:</strong> 격렬한 웨이트 트레이닝보다는 주 3회 30분 이상의 빠른 걷기나 수영 등 유산소 운동이 오행 밸런스를 가장 이상적으로 맞추어 줍니다.
                </p>
            </div>
        </div>
        """
    }
    
    return {
        "title": titles.get(theme, "심층 리포트"),
        "content": contents.get(theme, "<p>리포트 내용을 불러오는 중입니다.</p>")
    }
