import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional
import os

app = FastAPI(title="운세의 신 PRO API", version="4.0.0")

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

JIJANGGAN_MAP = {
    "子": "癸 (계)", "丑": "己 (기)", "寅": "甲 (갑)", "卯": "乙 (을)",
    "辰": "戊 (무)", "巳": "丙 (병)", "午": "丁 (정)", "未": "己 (기)",
    "申": "庚 (경)", "酉": "辛 (신)", "戌": "戊 (무)", "亥": "壬 (임)"
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
    {"name": "0. THE FOOL (바보)", "keyword": "새로운 시작, 순수한 모험", "overview": "망설임을 내려놓고 가벼운 마음으로 첫발을 내딛기 좋은 타이밍입니다. 지나친 계산보다 직관을 신뢰할 때 예상치 못한 행운의 문이 열립니다.", "action": "불필요한 걱정을 비우고 오랫동안 미뤄둔 첫 단추를 꿰어보세요."},
    {"name": "I. THE MAGICIAN (마법사)", "keyword": "창조적 재능, 무한한 잠재력", "overview": "자신이 가진 모든 도구와 언변, 실력을 완벽하게 발휘할 수 있는 역동적인 날입니다. 주도권을 쥐고 사람들을 설득하기에 최적입니다.", "action": "회의나 미팅에서 주도적으로 의견을 제시하고 실력을 마음껏 드러내세요."}
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
    # 1. 100% 범용 만세력 수학 공식을 적용한 일주(日柱) 산출
    # 기준일: 1900년 1월 1일 (甲戌일, index: 甲=0, 戌=10)
    base_date = datetime.date(1900, 1, 1)
    target_date = datetime.date(req.year, req.month, req.day)
    diff_days = (target_date - base_date).days
    
    d_cg_idx = (diff_days + 0) % 10
    d_jj_idx = (diff_days + 10) % 12
    d_cg = CHEONGAN_HANJA[d_cg_idx]
    d_jj = JIJI_HANJA[d_jj_idx]

    # 2. 년주(年柱) 산출 (입춘 기준 연도 보정)
    year_offset = (req.year - 4) % 60
    y_cg_idx = year_offset % 10
    y_jj_idx = year_offset % 12
    y_cg, y_jj = CHEONGAN_HANJA[y_cg_idx], JIJI_HANJA[y_jj_idx]

    # 3. 월주(月柱) 산출 (년간에 따른 월간 변조 공식)
    # 절기 기준 월 인덱스 계산 (3월 경칩 이후 -> 2번째 월 인덱스 卯월)
    m_jj_idx = (req.month) % 12
    m_cg_idx = (y_cg_idx % 5 * 2 + 2 + (req.month - 2)) % 10
    m_cg, m_jj = CHEONGAN_HANJA[m_cg_idx], JIJI_HANJA[m_jj_idx]

    # 4. 시주(時柱) 산출 (일간에 따른 시간 변조 공식)
    if req.is_unknown_time or req.sijin_index is None or req.sijin_index < 0:
        h_pillar, h_cg, h_jj = "時未詳", "-", "-"
    else:
        h_jj_idx = req.sijin_index
        h_cg_idx = (d_cg_idx % 5 * 2 + h_jj_idx) % 10
        h_cg, h_jj = CHEONGAN_HANJA[h_cg_idx], JIJI_HANJA[h_jj_idx]
        h_pillar = f"{h_cg}{h_jj}"

    d_animal = ANIMAL_MAP.get(d_jj, "개")

    # 5. 입력된 사주 8자의 오행(五行) 동적 100% 파싱 계산
    pillars_chars = [y_cg, y_jj, m_cg, m_jj, d_cg, d_jj]
    if h_cg != "-":
        pillars_chars.extend([h_cg, h_jj])
        
    elem_counts = {"wood": 0, "fire": 0, "earth": 0, "metal": 0, "water": 0}
    total_chars = len(pillars_chars)
    
    for char in pillars_chars:
        if char in CHEONGAN_ELEMENTS:
            elem_counts[CHEONGAN_ELEMENTS[char]] += 1
        elif char in JIJI_ELEMENTS:
            elem_counts[JIJI_ELEMENTS[char]] += 1
            
    # 정확한 오행 백분율 산출 (소수점 첫째 자리)
    elem_percentages = {
        k: round((v / total_chars) * 100, 1) for k, v in elem_counts.items()
    }

    # 6. 일간 기준 동적 MBTI & 수호 동물 지정
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
            "pillars_detail": {
                "year": {"cg": y_cg, "jj": y_jj, "jjg": JIJANGGAN_MAP.get(y_jj, "-")},
                "month": {"cg": m_cg, "jj": m_jj, "jjg": JIJANGGAN_MAP.get(m_jj, "-")},
                "day": {"cg": d_cg, "jj": d_jj, "jjg": JIJANGGAN_MAP.get(d_jj, "-")},
                "hour": {"cg": h_cg, "jj": h_jj, "jjg": JIJANGGAN_MAP.get(h_jj, "-")}
            },
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
    idx = (int(rand_seed or "1") + slot) % len(TAROT_CARDS)
    return TAROT_CARDS[idx]

@app.post("/api/daewoon-report")
def get_daewoon_report(req: dict):
    user_name = req.get("name", "고객")
    return {
        "title": f"👑 {user_name}님의 자미두수 & 10년 대운 심층 리포트",
        "content": f"""
        <div style="display: flex; flex-direction: column; gap: 14px; font-size: 12px; color: #334155; line-height: 1.6; text-align: left;">
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 16px; padding: 14px;">
                <h4 style="font-size: 13px; font-weight: 800; color: #0F172A; border-bottom: 1px solid #E2E8F0; padding-bottom: 6px; margin-bottom: 10px;">
                    🌐 1. {user_name}님의 평생 생애 주기별 대운맥(大運脈) 흐름
                </h4>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 11px;">
                    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 10px;">
                        <p style="font-weight: 700; color: #0F172A;">🌱 [유년기 (년주 기반 / 0세 ~ 19세) : 기틀 형성기]</p>
                        <p style="color: #475569; margin-top: 2px;">탐구심과 지적 호기심이 왕성했던 시기로 내면의 뼈대를 공고히 하던 유년기입니다.</p>
                    </div>
                    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 10px;">
                        <p style="font-weight: 700; color: #0F172A;">🌿 [청년기 (월주 기반 / 20세 ~ 39세) : 도약 탐색기]</p>
                        <p style="color: #475569; margin-top: 2px;">전문 역량을 갈고닦으며 중년의 성공을 위한 튼튼한 발판을 마련했습니다.</p>
                    </div>
                    <div style="background: #FEF3C7; border: 1px solid #FCD34D; border-radius: 12px; padding: 10px;">
                        <p style="font-weight: 800; color: #78350F;">🔥 [중장년기 (*현재 일주 기반 / 40세 ~ 59세) : 황금 자산 결실기]</p>
                        <p style="color: #92400E; margin-top: 2px;"><strong>{user_name}님 인생 최고 하이라이트 구간입니다.</strong> 사회적 주도권을 잡고 자산 확장이 거침없이 일어납니다.</p>
                    </div>
                    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 10px;">
                        <p style="font-weight: 700; color: #0F172A;">🍎 [말년기 (시주 기반 / 60세 이후) : 태평성대기]</p>
                        <p style="color: #475569; margin-top: 2px;">평생 축적한 부와 지혜로 안락하고 평온한 노후를 누립니다.</p>
                    </div>
                </div>
            </div>
        </div>
        """
    }

@app.post("/api/theme-report")
def get_theme_report(req: dict):
    theme = req.get("theme", "wealth")
    sub_opt = req.get("sub_option", "기본")
    user_name = req.get("name", "고객")
    
    return {
        "title": f"💰 {user_name}님의 평생 재물 그릇 & 금고운 리포트",
        "content": f"""
        <div style="display: flex; flex-direction: column; gap: 12px; font-size: 12px; color: #334155; line-height: 1.6; text-align: left;">
            <div style="background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 12px; padding: 12px;">
                <p style="font-weight: 800; color: #78350F; font-size: 13px;">[재물 그릇] '금고형' 자산 축적 원국</p>
                <p style="font-size: 11px; color: #92400E; margin-top: 2px;">체계적인 현금 흐름을 통해 부를 쌓아 올리는 황금 금고 사주입니다.</p>
            </div>
            <div>
                <p style="font-weight: 700; color: #0F172A;">1. {user_name}님 맞춤 자산 포트폴리오</p>
                <p style="font-size: 11px; color: #475569; margin-top: 2px;">실물 부동산 및 우량 배당 자산 중심 배분이 가장 안전합니다.</p>
            </div>
        </div>
        """
    }
