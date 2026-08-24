import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import os

app = FastAPI(title="운세의 신 PRO API", version="3.3.0")

# 60갑자 및 천간/지지
CHEONGAN_HANJA = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
JIJI_HANJA = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 지장간
JIJANGGAN_MAP = {
    "子": "癸 (계)",
    "丑": "己 (기)",
    "寅": "甲 (갑)",
    "卯": "乙 (을)",
    "辰": "戊 (무)",
    "巳": "丙 (병)",
    "午": "丁 (정)",
    "未": "己 (기)",
    "申": "庚 (경)",
    "酉": "辛 (신)",
    "戌": "戊 (무)",
    "亥": "壬 (임)"
}

# 60일주 기반 동적 MBTI 매핑 사전 (태어난 날짜의 일간 기준)
DAY_MBTI_MAP = {
    "甲": {"mbti": "대담한 통솔자 (ENTJ형)", "desc": "강한 추진력과 당당한 리더십으로 조직을 이끄는 개척자"},
    "乙": {"mbti": "재기발랄한 활동가 (ENFP형)", "desc": "유연한 적응력과 풍부한 친화력으로 사람의 마음을 얻는 인재"},
    "丙": {"mbti": "자유로운 영혼의 연예인 (ESFP형)", "desc": "태양 같은 열정과 밝은 에너지로 주변을 환하게 밝히는 존재"},
    "丁": {"mbti": "용의주도한 전략가 (ENTJ형)", "desc": "치밀한 기획력과 은근한 카리스마로 목표를 완벽히 쟁취하는 지략가"},
    "戊": {"mbti": "청렴결백한 논리주의자 (ISTJ형)", "desc": "묵직한 신뢰감과 흔들리지 않는 원칙으로 책임을 다하는 맏형"},
    "己": {"mbti": "세심한 수호자 (ISFJ형)", "desc": "비옥한 땅처럼 주변을 묵묵히 품어주고 실속을 챙기는 조력자"},
    "庚": {"mbti": "엄격한 관리자 (ESTJ형)", "desc": "의리와 결단력으로 무장하여 난관을 돌파하는 단호한 실행가"},
    "辛": {"mbti": "용의주도한 완벽주의자 (INTJ형)", "desc": "보석처럼 예리한 감각과 높은 기준을 지닌 냉철한 분석가"},
    "壬": {"mbti": "뜨거운 논쟁을 즐기는 변론가 (ENTP형)", "desc": "바다처럼 넓은 지혜와 임기응변으로 판을 주도하는 아이디어 뱅크"},
    "癸": {"mbti": "선의의 옹호자 (INFJ형)", "desc": "맑은 이슬비처럼 깊은 직관과 통찰력으로 본질을 꿰뚫는 사색가"}
}

ANIMAL_MAP = {"子": "쥐", "丑": "소", "寅": "호랑이", "卯": "토끼", "辰": "용", "巳": "뱀", "午": "말", "未": "양", "申": "원숭이", "酉": "닭", "戌": "개", "亥": "돼지"}
ANIMAL_ICONS = {"쥐": "🐭", "소": "🐮", "호랑이": "🐯", "토끼": "🐰", "용": "🐲", "뱀": "🐍", "말": "🐴", "양": "🐑", "원숭이": "🐵", "닭": "🐔", "개": "🐶", "돼지": "🐷"}

# 12종 고유 부적 마스터
TALISMAN_LIST = [
    {"title": "재물만복부 (萬福符)", "chinese": "勅令 · 萬福大吉", "power": "재물 증식 · 금전운 대통", "desc": "사방에서 금전과 복록이 샘솟듯 모여드는 강력한 재물 비급 부적입니다."},
    {"title": "금고수호부 (金庫守護符)", "chinese": "勅令 · 金庫安穩", "power": "자산 방어 · 누수 차단", "desc": "새어나가는 헛돈을 철통같이 막아주고 보유 자산을 굳건히 지켜줍니다."},
    {"title": "사업대성부 (事業大成符)", "chinese": "勅令 · 萬事亨通", "power": "사업 번창 · 계약 성사", "desc": "막혔던 활로를 시원하게 뚫어주고 거래와 사업 번창을 돕는 부적입니다."},
    {"title": "관운승진부 (官運昇進符)", "chinese": "勅令 · 官祿大吉", "power": "승진 합격 · 명예 상승", "desc": "직장 내 인정과 승진, 영전의 기운을 강력하게 끌어올려 줍니다."},
    {"title": "천우신조부 (天佑神助符)", "chinese": "勅令 · 貴人助勢", "power": "귀인 조력 · 위기 탈출", "desc": "절체절명의 순간 하늘의 도움과 결정적인 귀인의 손길을 연결합니다."},
    {"title": "벽사소재부 (辟邪消災符)", "chinese": "勅令 · 凶厄退去", "power": "액운 소멸 · 삼재 퇴치", "desc": "칠성검의 서슬 퍼런 기운으로 몸을 맴도는 액운과 살성을 일시에 벱니다."}
]

# 타로 카드
TAROT_CARDS = [
    {"name": "0. THE FOOL (바보)", "keyword": "새로운 시작, 순수한 모험", "overview": "망설임을 내려놓고 가벼운 마음으로 첫발을 내딛기 좋은 타이밍입니다.", "action": "계산보다 직관을 믿고 가볍게 시도해보세요."},
    {"name": "I. THE MAGICIAN (마법사)", "keyword": "창조적 재능, 무한한 잠재력", "overview": "당신이 가진 모든 도구와 능력을 온전히 발휘할 수 있는 역동적인 날입니다.", "action": "주도권을 쥐고 자신의 실력을 솔직하게 드러내세요."},
    {"name": "VI. THE LOVERS (연인)", "keyword": "진정한 교감, 조화로운 선택", "overview": "사람들과의 호흡이 환상적으로 맞아떨어지며 기분 좋은 유대가 형성됩니다.", "action": "마음을 솔직하게 표현하고 협력의 손을 잡으세요."},
    {"name": "X. WHEEL OF FORTUNE (운명의 수레바퀴)", "keyword": "행운의 전환점, 기회", "overview": "정체되었던 흐름이 풀리고 생각지 못한 기회의 바람이 불어옵니다.", "action": "변화의 파도에 유연하게 몸을 맡기세요."}
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
    return HTMLResponse("<h2>운세의 신 PRO 인덱스 파일 준비 중입니다.</h2>")

@app.post("/api/analyze")
def analyze_saju(req: SajuRequest):
    # 1. 태어난 날짜 기반 정밀 60갑자 일주(日柱) 산출
    base_date = datetime.date(1900, 1, 1)
    target_date = datetime.date(req.year, req.month, req.day)
    diff_days = (target_date - base_date).days
    
    d_cg_idx = (diff_days + 3) % 10
    d_jj_idx = (diff_days + 9) % 12
    
    d_cg = CHEONGAN_HANJA[d_cg_idx]
    d_jj = JIJI_HANJA[d_jj_idx]
    d_animal = ANIMAL_MAP[d_jj]

    # 년주/월주/시주 산출
    year_offset = (req.year - 4) % 60
    y_cg, y_jj = CHEONGAN_HANJA[year_offset % 10], JIJI_HANJA[year_offset % 12]
    m_cg, m_jj = CHEONGAN_HANJA[(req.month + 2) % 10], JIJI_HANJA[(req.month + 1) % 12]
    
    if req.is_unknown_time or req.sijin_index is None or req.sijin_index < 0:
        h_pillar, h_cg, h_jj = "時未詳", "-", "-"
    else:
        h_cg = CHEONGAN_HANJA[(d_cg_idx * 2 + req.sijin_index) % 10]
        h_jj = JIJI_HANJA[req.sijin_index]
        h_pillar = f"{h_cg}{h_jj}"

    # 2. 생년월일에 따른 100% 동적 사주 MBTI & 동물 심볼 계산
    user_mbti = DAY_MBTI_MAP.get(d_cg, {"mbti": "용의주도한 전략가 (ENTJ형)", "desc": "목표를 향해 나아가는 전략적 사주"})
    user_animal_icon = ANIMAL_ICONS.get(d_animal, "🐯")

    # 3. 풍성해진 오늘의 일진 본문 (양 3배 확장)
    daily_advice_rich = (
        "금빛 기운이 서서히 솟구치며 정체되었던 일들의 막힌 혈을 시원하게 뚫어주는 대길(大吉)의 하루입니다.\n\n"
        "오전에는 뜻밖의 반가운 소식이나 귀인의 연락이 닿아 오랫동안 계획했던 일에 강한 추진력이 실리게 됩니다. 서두르지 말고 주변과의 대화에 귀를 기울이세요.\n\n"
        "오후로 넘어가며 결단력과 판단력이 극대화되므로, 중요한 협상이나 문서 계약 관련 업무를 처리하기에 최적의 타이밍입니다. "
        "다만 자신감이 과해질 수 있으니 상대의 의견을 한 번 더 경청하는 유연함을 발휘한다면 결실과 명예를 동시에 거머쥘 수 있습니다."
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
            "elements": {"wood": 25, "fire": 30, "earth": 20, "metal": 15, "water": 10}
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
            "mindset": "상대의 말에 한 번 더 공감하고, 내 주장은 부드럽고 명확하게 전달하기",
            "action": "오전 중 따뜻한 차 한 잔을 마시며 핵심 목표 3가지를 메모하세요.",
            "talisman": TALISMAN_LIST[0]
        }
    }

@app.get("/api/daily-tarot")
def get_daily_tarot(slot: int = 1, rand_seed: Optional[str] = None):
    idx = (int(rand_seed or "1") + slot) % len(TAROT_CARDS)
    return TAROT_CARDS[idx]

@app.post("/api/daewoon-report")
def get_daewoon_report():
    return {
        "title": "👑 자미두수 & 10년 대운 심층 리포트",
        "content": """
        <div class='space-y-4 text-xs text-slate-800 leading-relaxed'>
            <div class='bg-amber-50 p-4 rounded-2xl border border-amber-200 space-y-2'>
                <h4 class='text-sm font-black text-amber-950 flex items-center gap-1'>
                    <span>📈 1. 현재 대운 심층 분석 (40대 황금 도약기)</span>
                </h4>
                <p><strong>[현재 대운수 43세~52세]</strong> 丁火 일간에 천을귀인의 기운이 결합하여, 인생에서 가장 강력한 팽창과 자산 축적이 일어나는 황금기입니다.</p>
                <p><strong>[주요 기회와 변수]</strong> 직장 및 사업에서 주도권을 완전히 잡게 되며, 45세~47세 구간에 뜻밖의 문서운(부동산 및 자산 확장)이 크게 열립니다.</p>
            </div>

            <div class='bg-emerald-50 p-4 rounded-2xl border border-emerald-200 space-y-2'>
                <h4 class='text-sm font-black text-emerald-950 flex items-center gap-1'>
                    <span>🌐 2. 평생 대운 & 귀인/상극 인연 종합 분석</span>
                </h4>
                <p><strong>[평생의 운맥 흐름]</strong> 초년의 수련기를 지나 중년 이후 평생의 자산 금고가 완성되는 대기만성형 고품격 원국입니다.</p>
                <div class='pt-2 space-y-1.5 border-t border-emerald-200'>
                    <p class='text-emerald-900 font-bold'>🌟 평생 나를 돕는 귀인 인연: 쥐띠, 소띠, 뱀띠</p>
                    <p class='text-slate-600'>논리적이고 차분하여 내 부족한 판단을 메워주며, 법률/금융/계약 등 결정적 순간에 실질적 도움을 주는 평생의 귀인입니다.</p>
                    <p class='text-rose-700 font-bold mt-2'>⚠️ 평생 조심해야 할 상극 인연: 호랑이띠, 토끼띠</p>
                    <p class='text-slate-600'>성격이 급하거나 성향이 상충되어 감정적 마찰이나 금전적 손실을 유발하기 쉬우므로 적당한 동업 거리 유지가 필수적입니다.</p>
                </div>
            </div>
        </div>
        """
    }

@app.post("/api/theme-report")
def get_theme_report(req: dict):
    theme = req.get("theme", "wealth")
    sub_opt = req.get("sub_option", "기본")
    
    titles = {
        "wealth": "💰 평생 재물 그릇 & 금고운 심층 리포트",
        "love": f"💖 평생 애정운 & 인연법 ({sub_opt} 맞춤)",
        "business": f"🏢 사업 & 직업 성공 대길운 ({sub_opt} 맞춤)",
        "health": "🌿 평생 오행 체질 & 건강 개운법"
    }
    
    return {
        "title": titles.get(theme, "심층 리포트"),
        "content": f"""
        <div class='space-y-3 text-xs text-slate-700 leading-relaxed p-1'>
            <p class='font-bold text-slate-900 text-sm'>[{titles.get(theme)}] 감명 결과</p>
            <p>귀하의 타고난 원국과 선택하신 상태(<strong>{sub_opt}</strong>)를 밀도 있게 분석한 결과, 향후 3년 이내에 인생의 중요한 전환점을 맞이하게 됩니다.</p>
            <p>타고난 명리학적 장점을 극대화하고 단점을 보완하는 실전 액션 플랜을 통해 보다 큰 성과와 안정을 누리실 수 있습니다.</p>
        </div>
        """
    }
