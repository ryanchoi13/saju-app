import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional
import os

app = FastAPI(title="운세의 신 PRO API", version="4.5.0")

CHEONGAN_HANJA = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
JIJI_HANJA = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 천간 / 지지 오행 마스터 매핑
CHEONGAN_ELEMENTS = {
    "甲": "wood", "乙": "wood",
    "丙": "fire", "丁": "fire",
    "戊": "earth", "己": "earth",
    "庚": "metal", "辛": "metal",
    "壬": "water", "癸": "water"
}
JIJI_ELEMENTS = {
    "子": "water", "丑": "earth", "寅": "wood", "卯": "wood",
    "辰": "earth", "巳": "fire", "午": "fire", "未": "earth",
    "申": "metal", "酉": "metal", "戌": "earth", "亥": "water"
}

# 12지지별 정밀 지장간 (여기, 중기, 정기)
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

TALISMAN_LIST = [
    {"title": "재물만복부 (萬福符)", "chinese": "勅令 · 萬福大吉", "power": "재물 증식 · 금전운 대통", "desc": "사방에서 금전과 복록이 샘솟듯 모여드는 강력한 재물 비급 부적입니다."},
    {"title": "금고수호부 (金庫守護符)", "chinese": "勅令 · 金庫安穩", "power": "자산 방어 · 누수 차단", "desc": "새어나가는 헛돈을 철통같이 막아주고 보유 자산을 굳건히 지켜줍니다."},
    {"title": "사업대성부 (事業大成符)", "chinese": "勅令 · 萬事亨通", "power": "사업 번창 · 계약 성사", "desc": "막혔던 활로를 시원하게 뚫어주고 거래와 사업 번창을 돕는 부적입니다."}
]

TAROT_CARDS = [
    {
        "name": "0. THE FOOL (바보)",
        "keyword": "새로운 시작 · 순수한 열정 · 무한한 잠재력",
        "symbolism": "화려한 옷을 입고 절벽 끝에 서 있는 청년은 세상의 관습에 얽매이지 않는 순수한 영혼과 새로운 여정의 출발을 상징합니다.",
        "fortune_reading": "오늘은 오랫동안 머뭇거리던 일의 시작 단추를 꿰기에 더없이 좋은 날입니다. 직관을 따를 때 예상 밖의 통로가 열립니다.",
        "advice": "새로운 제안에 열린 마음을 가지되, 발걸음은 가볍되 시선은 주변을 살피는 지혜가 필요합니다.",
        "action_tip": "오늘 떠오르는 새로운 아이디어를 메모하고 먼저 안부 연락을 건네보세요."
    },
    {
        "name": "I. THE MAGICIAN (마법사)",
        "keyword": "창조적 역량 · 완벽한 주도권 · 실력 발휘",
        "symbolism": "머리 위의 무한대(∞) 기호와 제단 위의 4대 원소는 세상의 모든 도구를 능숙하게 통제하는 지혜와 창조력을 상징합니다.",
        "fortune_reading": "귀하가 가진 지식과 언변, 전문 기술이 빛을 발하는 날입니다. 당당한 태도로 판을 리드하기에 최적입니다.",
        "advice": "미팅이나 보고에서 주도적으로 의견을 제시하고 실력을 마음껏 드러내세요.",
        "action_tip": "중요한 대화나 업무에서 본인의 핵심 주장을 명확하게 피력하세요."
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

    # 1. 지장간 리스트 상세 추출
    jj_list = [h_jj, d_jj, m_jj, y_jj]
    cg_list = [h_cg, d_cg, m_cg, y_cg]

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

    # 2. 지장간 가중치 합산 정밀 오행 계산
    # 천간 4글자: 각 25점 (총 100점)
    # 지장간: 각 지지당 30점 만점 할당 (월지는 계절성 반영 1.5배 가중)
    scores = {"wood": 0.0, "fire": 0.0, "earth": 0.0, "metal": 0.0, "water": 0.0}
    
    # 천간 배점
    for cg in [y_cg, m_cg, d_cg]:
        scores[CHEONGAN_ELEMENTS[cg]] += 25.0
    if h_cg != "-":
        scores[CHEONGAN_ELEMENTS[h_cg]] += 25.0

    # 지장간 배점
    for idx, jj in enumerate([y_jj, m_jj, d_jj]):
        mult = 1.5 if idx == 1 else 1.0 # 월지 가중치
        for item in JIJANGGAN_FULL_MAP.get(jj, []):
            scores[item["elem"]] += item["weight"] * mult

    if h_jj != "-":
        for item in JIJANGGAN_FULL_MAP.get(h_jj, []):
            scores[item["elem"]] += item["weight"] * 1.0

    total_score = sum(scores.values())
    elem_percentages = {
        k: round((v / total_score) * 100, 1) for k, v in scores.items()
    }

    user_mbti = DAY_MBTI_MAP.get(d_cg, {"mbti": "대담한 통솔자 (ENTJ형)", "desc": "강한 추진력과 당당한 리더십으로 조직을 이끄는 개척자 사주"})
    user_animal_icon = ANIMAL_ICONS.get(d_animal, "🐶")

    daily_advice_rich = (
        f"금빛 기운이 서서히 솟구치며 정체되었던 일들의 막힌 혈을 시원하게 뚫어주는 대길(大吉)의 하루입니다.\n\n"
        f"오전(09:00~12:00)에는 뜻밖의 반가운 소식이나 귀인의 연락이 닿아 오랫동안 추진해 오던 프로젝트에 강력한 가속도가 붙게 됩니다.\n\n"
        f"오후(13:00~17:00)로 넘어가며 결단력과 판단력이 최고조에 달하므로, 중요한 협상이나 문서를 처리하기에 최적입니다."
    )

    return {
        "user_name": req.name,
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
            "title": "금빛 기운이 서서히 솟아나는 도약의 하루",
            "advice": daily_advice_rich,
            "lucky_color": "스카이 블루 / 아이보리",
            "lucky_number": "1, 6",
            "lucky_direction": "정북쪽",
            "fashion_style": "부드러운 니트 또는 셔츠",
            "recommended_menu": "신선한 샐러드와 담백한 단백질 식단",
            "mindset": "상대의 말에 공감하고 명확하게 전달하기",
            "action": "오전 중 따뜻한 차 한 잔을 마시며 목표 3가지 메모하기",
            "talisman": TALISMAN_LIST[0]
        }
    }

@app.get("/api/daily-tarot")
def get_daily_tarot(slot: int = 1, rand_seed: Optional[str] = None):
    seed_val = int(rand_seed or str(datetime.date.today().toordinal()))
    idx = (seed_val + slot * 3) % len(TAROT_CARDS)
    return TAROT_CARDS[idx]

@app.post("/api/daewoon-report")
def get_daewoon_report(req: dict):
    user_name = req.get("name", "고객")
    return {
        "title": f"👑 {user_name}님의 자미두수 & 10년 대운 심층 리포트",
        "content": f"""
        <div style="display: flex; flex-direction: column; gap: 12px; font-size: 12px; color: #334155; line-height: 1.6; text-align: left;">
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 14px; padding: 12px;">
                <h4 style="font-size: 13px; font-weight: 800; color: #0F172A; border-bottom: 1px solid #E2E8F0; padding-bottom: 6px; margin-bottom: 8px;">
                    🌐 1. {user_name}님의 평생 생애 주기별 대운맥(大運脈) 흐름
                </h4>
                <div style="display: flex; flex-direction: column; gap: 6px; font-size: 11px;">
                    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 8px;">
                        <p style="font-weight: 700; color: #0F172A;">🌱 [유년기 (년주 기반 / 0세 ~ 19세) : 기틀 형성기]</p>
                        <p style="color: #475569; margin-top: 2px;">탐구심과 지적 호기심이 왕성했던 시기로 내면의 뼈대를 공고히 하던 유년기입니다.</p>
                    </div>
                    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 8px;">
                        <p style="font-weight: 700; color: #0F172A;">🌿 [청년기 (월주 기반 / 20세 ~ 39세) : 도약 탐색기]</p>
                        <p style="color: #475569; margin-top: 2px;">전문 역량을 갈고닦으며 중년의 성공을 위한 튼튼한 발판을 마련했습니다.</p>
                    </div>
                    <div style="background: #FEF3C7; border: 1px solid #FCD34D; border-radius: 10px; padding: 8px;">
                        <p style="font-weight: 800; color: #78350F;">🔥 [중장년기 (*현재 일주 기반 / 40세 ~ 59세) : 황금 자산 결실기]</p>
                        <p style="color: #92400E; margin-top: 2px;"><strong>{user_name}님 인생 최고 하이라이트 구간입니다.</strong> 사회적 주도권을 잡고 자산 확장이 거침없이 일어납니다.</p>
                    </div>
                    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 8px;">
                        <p style="font-weight: 700; color: #0F172A;">🍎 [말년기 (시주 기반 / 60세 이후) : 태평성대기]</p>
                        <p style="color: #475569; margin-top: 2px;">평생 축적한 부와 지혜로 안락하고 평온한 노후를 누립니다.</p>
                    </div>
                </div>
            </div>

            <div style="background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 14px; padding: 12px;">
                <h4 style="font-size: 13px; font-weight: 800; color: #78350F; border-bottom: 1px solid #FCD34D; padding-bottom: 6px; margin-bottom: 8px;">
                    📈 2. {user_name}님의 현재 10년 대운 정밀 감명 (43세 ~ 52세)
                </h4>
                <p style="margin-bottom: 4px;"><strong>[대운의 본질과 주도권]</strong> 丁火 일간에 천을귀인(天乙貴人)과 유금(酉金) 편재의 기운이 굳건히 결합하는 시기입니다. 과거에 수동적으로 끌려가던 입장에서 벗어나, 조직과 사업의 핵심 결정권을 쥐고 인생의 황금기를 설계하는 10년입니다.</p>
                <p><strong>[세운별 핵심 분기점 및 행동 가이드]</strong>
                <br>• <strong>44~45세 (자산 포트폴리오 재편):</strong> 불필요한 고정 지출을 정돈하고 안전 자산을 확보하는 최적기.
                <br>• <strong>46~48세 (대운의 정점 및 비상):</strong> 강력한 조력자의 등장과 함께 직위와 명예가 수직 상승하는 황금 전환점.</p>
            </div>
        </div>
        """
    }

@app.post("/api/theme-report")
def get_theme_report(req: dict):
    theme = req.get("theme", "wealth")
    sub_opt = req.get("sub_option", "기본")
    user_name = req.get("name", "고객")
    
    titles = {
        "wealth": f"💰 {user_name}님의 평생 재물 그릇 & 금고운 리포트",
        "love": f"💖 {user_name}님의 평생 애정운 & 인연법 ({sub_opt} 맞춤)",
        "business": f"🏢 {user_name}님의 사업 & 직업 성공 대길운 ({sub_opt} 맞춤)",
        "health": f"🌿 {user_name}님의 평생 오행 체질 & 건강 개운법"
    }

    contents = {
        "wealth": f"""
        <div style="display: flex; flex-direction: column; gap: 10px; font-size: 12px; color: #334155; line-height: 1.6; text-align: left;">
            <div style="background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 12px; padding: 10px;">
                <p style="font-weight: 800; color: #78350F; font-size: 12px;">[재물 그릇] '금고형' 자산 축적 원국</p>
                <p style="font-size: 11px; color: #92400E; margin-top: 2px;">체계적인 현금 흐름을 통해 부를 쌓아 올리는 황금 금고 사주입니다.</p>
            </div>
            <div>
                <p style="font-weight: 700; color: #0F172A;">1. {user_name}님 맞춤 자산 포트폴리오</p>
                <p style="font-size: 11px; color: #475569; margin-top: 2px;">실물 부동산 및 우량 배당 자산 중심 배분이 가장 안전합니다.</p>
            </div>
        </div>
        """,
        "love": f"""
        <div style="display: flex; flex-direction: column; gap: 10px; font-size: 12px; color: #334155; line-height: 1.6; text-align: left;">
            <div style="background: #FFF1F2; border: 1px solid #FECDD3; border-radius: 12px; padding: 10px;">
                <p style="font-weight: 800; color: #881337; font-size: 12px;">[현재 상태: {sub_opt}] 맞춤 애정 감명</p>
                <p style="font-size: 11px; color: #9F1239; margin-top: 2px;">현재 {user_name}님의 기운은 내면의 깊은 신뢰와 유대감을 형성하기에 가장 안정적인 상태입니다.</p>
            </div>
            <div>
                <p style="font-weight: 700; color: #0F172A;">1. 나에게 운명적으로 맞는 평생 배필의 특징</p>
                <p style="font-size: 11px; color: #475569; margin-top: 2px;">대화가 깊이 통하고 배려심이 깊은 인품의 소유자와 고품격 궁합을 이룹니다.</p>
            </div>
        </div>
        """,
        "business": f"""
        <div style="display: flex; flex-direction: column; gap: 10px; font-size: 12px; color: #334155; line-height: 1.6; text-align: left;">
            <div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 12px; padding: 10px;">
                <p style="font-weight: 800; color: #1E3A8A; font-size: 12px;">[직업군 상태: {sub_opt}] 대길 성공 로드맵</p>
                <p style="font-size: 11px; color: #1E40AF; margin-top: 2px;">치밀한 기획력과 실행력이 결합되어 핵심 수장으로 두각을 나타낼 사주입니다.</p>
            </div>
            <div>
                <p style="font-weight: 700; color: #0F172A;">1. 성공을 보장하는 대박 직무 분야</p>
                <p style="font-size: 11px; color: #475569; margin-top: 2px;">전문 컨설팅, IT/기술 기획, 브랜드 매니지먼트 등 시스템을 조율하는 영역에서 역량이 극대화됩니다.</p>
            </div>
        </div>
        """,
        "health": f"""
        <div style="display: flex; flex-direction: column; gap: 10px; font-size: 12px; color: #334155; line-height: 1.6; text-align: left;">
            <div style="background: #ECFDF5; border: 1px solid #A7F3D0; border-radius: 12px; padding: 10px;">
                <p style="font-weight: 800; color: #065F46; font-size: 12px;">[오행 체질 진단] 활력 왕성 체질</p>
                <p style="font-size: 11px; color: #047857; margin-top: 2px;">생명력은 왕성하나 체내 수분 및 진액 관리가 평생 건강의 핵심 키입니다.</p>
            </div>
            <div>
                <p style="font-weight: 700; color: #0F172A;">1. 100세 건강을 완성하는 일상 개운 루틴</p>
                <p style="font-size: 11px; color: #475569; margin-top: 2px;">취침 전 10분간의 따뜻한 족욕과 미온수 섭취로 수승화강 루틴을 실천하세요.</p>
            </div>
        </div>
        """
    }
    
    return {
        "title": titles.get(theme, "심층 리포트"),
        "content": contents.get(theme, "<p>리포트 내용을 불러오는 중입니다.</p>")
    }
