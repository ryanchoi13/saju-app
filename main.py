import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional
import os

app = FastAPI(title="운세의 신 PRO API", version="3.4.0")

CHEONGAN_HANJA = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
JIJI_HANJA = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

JIJANGGAN_MAP = {
    "子": "癸 (계)", "丑": "己 (기)", "寅": "甲 (갑)", "卯": "乙 (을)",
    "辰": "戊 (무)", "巳": "丙 (병)", "午": "丁 (정)", "未": "己 (기)",
    "申": "庚 (경)", "酉": "辛 (신)", "戌": "戊 (무)", "亥": "壬 (임)"
}

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

TALISMAN_LIST = [
    {"title": "재물만복부 (萬福符)", "chinese": "勅令 · 萬福大吉", "power": "재물 증식 · 금전운 대통", "desc": "사방에서 금전과 복록이 샘솟듯 모여드는 강력한 재물 비급 부적입니다."},
    {"title": "금고수호부 (金庫守護符)", "chinese": "勅令 · 金庫安穩", "power": "자산 방어 · 누수 차단", "desc": "새어나가는 헛돈을 철통같이 막아주고 보유 자산을 굳건히 지켜줍니다."},
    {"title": "사업대성부 (事業大成符)", "chinese": "勅令 · 萬事亨通", "power": "사업 번창 · 계약 성사", "desc": "막혔던 활로를 시원하게 뚫어주고 거래와 사업 번창을 돕는 부적입니다."},
    {"title": "관운승진부 (官運昇進符)", "chinese": "勅令 · 官祿大吉", "power": "승진 합격 · 명예 상승", "desc": "직장 내 인정과 승진, 영전의 기운을 강력하게 끌어올려 줍니다."},
    {"title": "천우신조부 (天佑神助符)", "chinese": "勅令 · 貴人助勢", "power": "귀인 조력 · 위기 탈출", "desc": "절체절명의 순간 하늘의 도움과 결정적인 귀인의 손길을 연결합니다."},
    {"title": "벽사소재부 (辟邪消災符)", "chinese": "勅令 · 凶厄退去", "power": "액운 소멸 · 삼재 퇴치", "desc": "칠성검의 서슬 퍼런 기운으로 몸을 맴도는 액운과 살성을 일시에 벱니다."}
]

TAROT_CARDS = [
    {"name": "0. THE FOOL (바보)", "keyword": "새로운 시작, 순수한 모험", "overview": "망설임을 내려놓고 가벼운 마음으로 첫발을 내딛기 좋은 타이밍입니다. 지나친 계산보다 직관을 신뢰할 때 예상치 못한 행운의 문이 열립니다.", "action": "불필요한 걱정을 비우고 오랫동안 미뤄둔 첫 단추를 꿰어보세요."},
    {"name": "I. THE MAGICIAN (마법사)", "keyword": "창조적 재능, 무한한 잠재력", "overview": "자신이 가진 모든 도구와 언변, 실력을 완벽하게 발휘할 수 있는 역동적인 날입니다. 주도권을 쥐고 사람들을 설득하기에 최적입니다.", "action": "회의나 미팅에서 주도적으로 의견을 제시하고 실력을 마음껏 드러내세요."},
    {"name": "II. THE HIGH PRIESTESS (여사제)", "keyword": "깊은 통찰, 내면의 직관", "overview": "표면적인 말 뒤에 숨겨진 상대의 본심과 상황의 본질을 꿰뚫어 보는 혜안이 빛을 발합니다. 서두르지 않고 침묵 속에 관찰하는 것이 유리합니다.", "action": "비밀을 소중히 지키고 중요한 결정은 하루 뒤로 미루며 직관을 따르세요."},
    {"name": "III. THE EMPRESS (여황제)", "keyword": "풍요로운 결실, 따뜻한 포용", "overview": "노력해 온 일들이 눈부신 결실과 물질적 풍요로 환원되는 날입니다. 주변 사람들에게 베푸는 온정이 더 큰 복록으로 되돌아옵니다.", "action": "함께 고생한 동료나 가족에게 따뜻한 격려와 식사를 대접하세요."},
    {"name": "IV. THE EMPEROR (황제)", "keyword": "확고한 통제력, 안정된 기반", "overview": "원칙과 확고한 기준을 세워 조직이나 상황을 리드해야 하는 날입니다. 흔들림 없는 책임감과 결단력이 주변의 신뢰를 완성합니다.", "action": "계획을 철저히 점검하고 명확한 가이드라인을 팀에 전달하세요."},
    {"name": "VI. THE LOVERS (연인)", "keyword": "진정한 교감, 조화로운 선택", "overview": "마음이 통하는 귀인이나 파트너와의 호흡이 완벽하게 맞아떨어집니다. 협력과 소통을 통해 혼자서는 이룰 수 없던 시너지를 창출합니다.", "action": "솔직한 감정을 표현하고 상대방과의 공통 분모를 찾아 대화를 풀어가세요."},
    {"name": "X. WHEEL OF FORTUNE (운명의 수레바퀴)", "keyword": "행운의 전환점, 필연적 기회", "overview": "정체되었던 정국이 풀리고 새로운 사이클의 행운이 찾아옵니다. 거스를 수 없는 긍정적 변화의 파도가 밀려오고 있습니다.", "action": "익숙한 방식을 고집하지 말고 새롭게 제안되는 기회를 열린 마음으로 잡으세요."},
    {"name": "XIX. THE SUN (태양)", "keyword": "눈부신 성공, 생명력과 활력", "overview": "모든 근심과 어둠이 걷히고 당신의 성과가 만천하에 드러나는 최고의 날입니다. 넘치는 활력과 자신감으로 하루를 압도할 수 있습니다.", "action": "햇볕을 쬐며 긍정 에너지를 충전하고 축하할 일을 당당히 즐기세요."}
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
    
    d_cg_idx = (diff_days + 3) % 10
    d_jj_idx = (diff_days + 9) % 12
    
    d_cg = CHEONGAN_HANJA[d_cg_idx]
    d_jj = JIJI_HANJA[d_jj_idx]
    d_animal = ANIMAL_MAP[d_jj]

    year_offset = (req.year - 4) % 60
    y_cg, y_jj = CHEONGAN_HANJA[year_offset % 10], JIJI_HANJA[year_offset % 12]
    m_cg, m_jj = CHEONGAN_HANJA[(req.month + 2) % 10], JIJI_HANJA[(req.month + 1) % 12]
    
    if req.is_unknown_time or req.sijin_index is None or req.sijin_index < 0:
        h_pillar, h_cg, h_jj = "時未詳", "-", "-"
    else:
        h_cg = CHEONGAN_HANJA[(d_cg_idx * 2 + req.sijin_index) % 10]
        h_jj = JIJI_HANJA[req.sijin_index]
        h_pillar = f"{h_cg}{h_jj}"

    user_mbti = DAY_MBTI_MAP.get(d_cg, {"mbti": "용의주도한 전략가 (ENTJ형)", "desc": "목표를 향해 나아가는 전략적 사주"})
    user_animal_icon = ANIMAL_ICONS.get(d_animal, "🐯")

    daily_advice_rich = (
        "금빛 기운이 서서히 솟구치며 정체되었던 일들의 막힌 혈을 시원하게 뚫어주는 대길(大吉)의 하루입니다.\n\n"
        "오전(09:00~12:00)에는 뜻밖의 반가운 소식이나 귀인의 연락이 닿아 오랫동안 추진해 오던 프로젝트에 강력한 가속도가 붙게 됩니다. 혼자 해결하려 애쓰기보다는 신뢰할 수 있는 동료와 의견을 나누는 과정에서 기발한 해법이 도출됩니다.\n\n"
        "오후(13:00~17:00)로 넘어가며 결단력과 판단력이 최고조에 달하므로, 계약 체결, 재무 플랜 수립, 문서 결재 등 집중을 요하는 핵심 업무를 처리하기에 최적입니다.\n\n"
        "저녁 시간대에는 지나친 자신감으로 인한 과로를 경계하고 가벼운 산책과 따뜻한 식사로 심신을 이완하면 내일의 복록까지 온전히 담아낼 수 있습니다."
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
    idx = (int(rand_seed or "1") + slot * 2) % len(TAROT_CARDS)
    return TAROT_CARDS[idx]

@app.post("/api/daewoon-report")
def get_daewoon_report():
    return {
        "title": "👑 자미두수 & 10년 대운 심층 리포트 (통합 프리미엄)",
        "content": """
        <div class='space-y-4 text-xs text-slate-800 leading-relaxed text-left'>
            <!-- 1. 현재 대운 분석 -->
            <div class='bg-amber-50/90 p-4 rounded-2xl border border-amber-200 space-y-2.5'>
                <h4 class='text-sm font-black text-amber-950 flex items-center gap-1.5'>
                    <span>📈 1. 현재 10년 대운 정밀 감명 (43세 ~ 52세 황금기)</span>
                </h4>
                <p><strong>[대운의 본질과 주도권]</strong> 丁火 일간에 천을귀인(天乙貴人)과 유금(酉金) 편재의 기운이 굳건히 결합하는 시기입니다. 과거에 수동적으로 끌려가던 입장에서 벗어나, 조직과 사업의 핵심 결정권을 쥐고 인생의 황금기를 설계하는 10년입니다.</p>
                <p><strong>[세운별 핵심 분기점]</strong> 
                <br>• <strong>44~45세:</strong> 자산 포트폴리오의 재편기. 불필요한 고정 지출을 정리하고 문서(부동산/지식재산) 형태의 안전 자산을 확보하는 최적기.
                <br>• <strong>46~48세:</strong> 대운의 정점기. 강력한 조력자의 등장과 함께 사회적 직위와 명예가 수직 상승하는 황금 전환점.
                <br>• <strong>49~52세:</strong> 수확 및 수성(守成)기. 무리한 확장보다 구축된 시스템을 안정화하여 평생의 은퇴 자금을 완비하는 시기.</p>
            </div>

            <!-- 2. 평생 대운 흐름 -->
            <div class='bg-slate-50 p-4 rounded-2xl border border-slate-200 space-y-2.5'>
                <h4 class='text-sm font-black text-slate-900 flex items-center gap-1.5'>
                    <span>🌐 2. 평생 생애 주기별 대운맥(大運脈) 흐름</span>
                </h4>
                <p><strong>[초년운 (~30세) : 기반 형성기]</strong> 다재다능한 재능을 탐색하고 다양한 환경을 겪으며 내면의 맷집과 실전 감각을 기르던 시기였습니다.</p>
                <p><strong>[중년운 (31세~55세) : 결실과 비상기]</strong> 타고난 치밀함과 리더십이 폭발하며 사회적으로 가장 큰 실적과 자산을 축적하는 대기만성형 상승 곡선입니다.</p>
                <p><strong>[말년운 (56세 이후) : 태평성대와 수호기]</strong> 지혜로운 안목으로 후진을 양성하거나 자산을 지키며 평온하고 유복한 노후를 누리게 됩니다.</p>
            </div>

            <!-- 3. 평생 귀인 vs 상극 인연 -->
            <div class='bg-emerald-50/90 p-4 rounded-2xl border border-emerald-200 space-y-2.5'>
                <h4 class='text-sm font-black text-emerald-950 flex items-center gap-1.5'>
                    <span>🤝 3. 평생의 천을귀인 vs 상극 인연 종합 처세법</span>
                </h4>
                <div class='space-y-1'>
                    <p class='text-emerald-900 font-bold'>🌟 평생 나를 돕는 귀인: 쥐띠, 소띠, 뱀띠 (서북쪽 및 동남쪽 방향)</p>
                    <p class='text-slate-600 text-[11px]'>감정적으로 흔들릴 때 차분하게 중심을 잡아주며, 법률, 세무, 대형 계약 등 결정적 순간에 실질적인 해결책을 안겨주는 평생의 동반자입니다.</p>
                </div>
                <div class='pt-2 border-t border-emerald-200 space-y-1'>
                    <p class='text-rose-700 font-bold'>⚠️ 평생 주의해야 할 상극 인연: 호랑이띠, 토끼띠</p>
                    <p class='text-slate-600 text-[11px]'>성향이 지나치게 강해 사소한 의견 차이로도 자존심 싸움이 번질 수 있습니다. 금전 거래나 동업 시 반드시 공증과 서면 계약을 철저히 하십시오.</p>
                </div>
            </div>
        </div>
        """
    }

@app.post("/api/theme-report")
def get_theme_report(req: dict):
    theme = req.get("theme", "wealth")
    sub_opt = req.get("sub_option", "기본")
    
    if theme == "wealth":
        return {
            "title": "💰 평생 재물 그릇 & 금고운 심층 리포트",
            "content": """
            <div class='space-y-3.5 text-xs text-slate-700 leading-relaxed text-left p-1'>
                <div class='p-3 bg-amber-50 rounded-xl border border-amber-200'>
                    <p class='font-bold text-amber-950 text-sm'>[재물 그릇의 본질] '금고형' 자산 축적 원국</p>
                    <p class='text-[11px] text-amber-900 mt-1'>일확천금의 투기보다 체계적인 시스템과 현금 흐름을 통해 복리로 부를 쌓아 올리는 대기만성형 금고를 타고났습니다.</p>
                </div>
                <p><strong>1. 최적의 자산 포트폴리오 전략:</strong> 변동성이 극심한 단타 매매보다는 실물 부동산(상가, 토지, 안정적 주거지) 및 배당형 우량 자산에 70% 이상을 배분할 때 자산 손실 없이 우상향합니다.</p>
                <p><strong>2. 재물운이 폭발하는 대박 시기:</strong> 40대 중후반과 50대 초반에 강력한 문서운이 들어와 보유한 자산 가치가 2배 이상 퀀텀점프하는 분기점을 맞이합니다.</p>
                <p><strong>3. 손재수(損財數) 방어 개운법:</strong> 지인 간의 구두 금전 대여를 절대 금하고, 서남쪽 방향에 황금빛 소품이나 금속 재질의 인테리어를 배치하면 재물의 누수를 완벽히 방어할 수 있습니다.</p>
            </div>
            """
        }
    elif theme == "love":
        return {
            "title": f"💖 평생 애정운 & 인연법 ({sub_opt} 맞춤)",
            "content": f"""
            <div class='space-y-3.5 text-xs text-slate-700 leading-relaxed text-left p-1'>
                <div class='p-3 bg-rose-50 rounded-xl border border-rose-200'>
                    <p class='font-bold text-rose-950 text-sm'>[현재 상태: {sub_opt}] 맞춤 애정 감명</p>
                    <p class='text-[11px] text-rose-900 mt-1'>현재 본인의 기운은 내면의 신뢰와 깊은 유대감을 형성하기에 가장 안정적인 상태입니다.</p>
                </div>
                <p><strong>1. 나와 맞는 평생 배필의 특징:</strong> 겉치레보다 대화가 통하고 배려심이 깊으며, 본인의 열정적인 성향을 묵묵히 지지해 주는 온화한 인품의 소유자와 궁합이 가장 좋습니다.</p>
                <p><strong>2. 시기별 애정운의 흐름:</strong> 상반기에는 소통의 깊이를 더하고, 하반기로 갈수록 두 사람 사이의 현실적 결속력(결혼 논의, 미래 설계)이 확고해지는 운의 흐름입니다.</p>
                <p><strong>3. 인연을 지키는 핵심 처세법:</strong> 서운한 감정이 들 때는 즉각 반응하기보다 하루의 시간을 두고 차분히 감정을 정리한 후 대화하는 것이 애정의 온도를 평생 유지하는 비결입니다.</p>
            </div>
            """
        }
    elif theme == "business":
        return {
            "title": f"🏢 사업 & 직업 성공 대길운 ({sub_opt} 맞춤)",
            "content": f"""
            <div class='space-y-3.5 text-xs text-slate-700 leading-relaxed text-left p-1'>
                <div class='p-3 bg-blue-50 rounded-xl border border-blue-200'>
                    <p class='font-bold text-blue-950 text-sm'>[직업군 상태: {sub_opt}] 성공 로드맵</p>
                    <p class='text-[11px] text-blue-900 mt-1'>기획력과 디테일한 실행력이 완벽히 결합되어 어느 조직에서든 핵심 리더로 두각을 나타낼 사주 구조입니다.</p>
                </div>
                <p><strong>1. 대박을 부르는 핵심 직무/사업 아이템:</strong> 전문 컨설팅, IT/기술 기획, 유통 및 브랜드 매니지먼트, 교육/인재 개발 등 시스템을 구축하고 사람을 연결하는 분야에서 최고의 역량을 발휘합니다.</p>
                <p><strong>2. 승진/이직/창업의 최적 타이밍:</strong> 가을과 겨울로 넘어가는 환절기 구간에 나를 강력히 추천해 주는 귀인(상사, 핵심 파트너)이 나타나며 경력의 큰 도약이 일어납니다.</p>
                <p><strong>3. 성공을 위한 실전 지침:</strong> 모든 실무를 혼자 짊어지려 하지 말고 신뢰할 수 있는 파트너에게 역할을 위임할 때 성과의 규모가 3배 이상 확장됩니다.</p>
            </div>
            """
        }
    else: # health
        return {
            "title": "🌿 평생 오행 체질 & 건강 개운법",
            "content": """
            <div class='space-y-3.5 text-xs text-slate-700 leading-relaxed text-left p-1'>
                <div class='p-3 bg-emerald-50 rounded-xl border border-emerald-200'>
                    <p class='font-bold text-emerald-950 text-sm'>[오행 체질 진단] 화(火)·토(土) 왕성 체질</p>
                    <p class='text-[11px] text-emerald-900 mt-1'>대사 활동과 열정은 넘치나, 상대적으로 수(水)와 금(金) 기운이 소모되기 쉬운 체질입니다.</p>
                </div>
                <p><strong>1. 집중 관리 취약 장기:</strong> 심혈관계의 열기를 식히고 신장, 방광 및 관절 계통의 수분을 보충하는 관리가 평생 건강의 핵심 열쇠입니다.</p>
                <p><strong>2. 맞춤 체질 섭생법:</strong> 자극적인 음식과 찬 음료를 피하고, 검은깨, 검은콩, 해조류 등 신장 기능을 보강하는 블랙푸드와 미온수를 습관화하십시오.</p>
                <p><strong>3. 일상 건강 개운 루틴:</strong> 매일 취침 전 10분간의 반신욕이나 족욕으로 머리의 상기된 열을 발끝으로 내리는 수승화강(水昇火降) 습관을 적극 권장합니다.</p>
            </div>
            """
        }
