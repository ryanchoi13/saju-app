import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional
import os

app = FastAPI(title="운세의 신 PRO API", version="3.5.0")

CHEONGAN_HANJA = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
JIJI_HANJA = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 천간/지지 오행 매핑
CHEONGAN_ELEMENTS = {"甲": "wood", "乙": "wood", "丙": "fire", "丁": "fire", "戊": "earth", "己": "earth", "庚": "metal", "辛": "metal", "壬": "water", "癸": "water"}
JIJI_ELEMENTS = {"子": "water", "丑": "earth", "寅": "wood", "卯": "wood", "辰": "earth", "巳": "fire", "午": "fire", "未": "earth", "申": "metal", "酉": "metal", "戌": "earth", "亥": "water"}

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

    # 오행 8자 동적 분석 (년/월/일/시 천간+지지 8자 기반)
    pillars_cg_jj = [y_cg, y_jj, m_cg, m_jj, d_cg, d_jj]
    if h_cg != "-":
        pillars_cg_jj.extend([h_cg, h_jj])
        
    elem_counts = {"wood": 0, "fire": 0, "earth": 0, "metal": 0, "water": 0}
    total_count = len(pillars_cg_jj)
    
    for char in pillars_cg_jj:
        if char in CHEONGAN_ELEMENTS:
            elem_counts[CHEONGAN_ELEMENTS[char]] += 1
        elif char in JIJI_ELEMENTS:
            elem_counts[JIJI_ELEMENTS[char]] += 1
            
    elem_percentages = {
        k: round((v / total_count) * 100, 1) for k, v in elem_counts.items()
    }

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
def get_daewoon_report(req: dict):
    user_name = req.get("name", "최정오")
    return {
        "title": f"👑 {user_name}님의 자미두수 & 10년 대운 심층 리포트",
        "content": f"""
        <div class='space-y-5 text-xs text-slate-800 leading-relaxed text-left'>
            <!-- 1. 4단계 평생 생애 주기별 대운맥 흐름 -->
            <div class='bg-slate-50 p-4 rounded-2xl border border-slate-200 space-y-3'>
                <h4 class='text-sm font-black text-slate-900 flex items-center gap-1.5 border-b pb-2 border-slate-200'>
                    <span>🌐 1. {user_name}님의 평생 생애 주기별 대운맥(大運脈) 흐름</span>
                </h4>
                <div class='space-y-2 text-[11px]'>
                    <div class='p-2.5 bg-white rounded-xl border border-slate-200 space-y-1'>
                        <p class='font-bold text-slate-900'>🌱 [유년기 (년주 기반 / 0세 ~ 19세) : 기틀 형성 및 학업기]</p>
                        <p class='text-slate-600 leading-normal'>탐구심과 지적 호기심이 왕성했던 시기로, 다재다능한 감각을 기르며 내면의 뼈대를 공고히 하던 유년기입니다. 인성(印星)의 조력을 받아 학업 및 기초 소양 구축에 유익했던 기반 형성기입니다.</p>
                    </div>
                    <div class='p-2.5 bg-white rounded-xl border border-slate-200 space-y-1'>
                        <p class='font-bold text-slate-900'>🌿 [청년기 (월주 기반 / 20세 ~ 39세) : 도약과 실전 탐색기]</p>
                        <p class='text-slate-600 leading-normal'>사회로 진출하여 다양한 시행착오와 도전을 통해 자신만의 전문 역량을 갈고닦던 시기입니다. 시련 속에서도 결단력과 추진력을 길러 중년의 큰 성공을 위한 튼튼한 발판을 마련했습니다.</p>
                    </div>
                    <div class='p-2.5 bg-amber-50 rounded-xl border border-amber-300 space-y-1'>
                        <p class='font-bold text-amber-950'>🔥 [중장년기 (*현재 40세 ~ 59세) : 황금 비상 및 자산 결실기]</p>
                        <p class='text-amber-900 leading-normal'><strong>{user_name}님 사주 인생의 최고 하이라이트 구간입니다.</strong> 일주(日柱)의 천을귀인과 유금(酉金) 편재가 왕성하게 결합하여, 사회적 주도권을 완전히 잡고 커리어 상승과 자산 확장이 거침없이 일어나는 황금 비상기입니다.</p>
                    </div>
                    <div class='p-2.5 bg-white rounded-xl border border-slate-200 space-y-1'>
                        <p class='font-bold text-slate-900'>🍎 [말년기 (시주 기반 / 60세 이후) : 태평성대 및 완숙기]</p>
                        <p class='text-slate-600 leading-normal'>평생 축적한 지혜와 부를 바탕으로 명예로운 노후를 완성하는 시기입니다. 자손 복과 문서운이 풍족하여 안락하고 평온한 정토를 누리게 됩니다.</p>
                    </div>
                </div>
            </div>

            <!-- 2. 현재 10년 대운 정밀 감명 & 조언/개운법 -->
            <div class='bg-amber-50/90 p-4 rounded-2xl border border-amber-200 space-y-3'>
                <h4 class='text-sm font-black text-amber-950 flex items-center gap-1.5 border-b pb-2 border-amber-300'>
                    <span>📈 2. {user_name}님의 현재 10년 대운 정밀 감명 (43세 ~ 52세)</span>
                </h4>
                <p><strong>[대운의 본질과 주도권]</strong> 丁火 일간에 천을귀인(天乙貴人)과 유금(酉金) 편재의 기운이 굳건히 결합하는 시기입니다. 과거에 수동적으로 끌려가던 입장에서 벗어나, 조직과 사업의 핵심 결정권을 쥐고 인생의 황금기를 설계하는 10년입니다.</p>
                <p><strong>[세운별 핵심 분기점 및 행동 가이드]</strong> 
                <br>• <strong>44~45세 (자산 포트폴리오 재편):</strong> 불필요한 고정 지출을 정돈하고 부동산 및 문서 형태의 안전 자산을 확보하는 최적기.
                <br>• <strong>46~48세 (대운의 정점 및 비상):</strong> 강력한 조력자의 등장과 함께 사회적 직위와 명예가 수직 상승하는 황금 전환점.
                <br>• <strong>49~52세 (수확 및 시스템 수성):</strong> 무리한 확장보다 구축된 시스템을 안정화하여 평생의 은퇴 자금을 완비하는 시기.</p>
                <div class='p-3 bg-white rounded-xl border border-amber-200 space-y-1 text-[11px] text-amber-950'>
                    <p class='font-bold'>💡 대운 성공 조언 & 개운 실천 가이드:</p>
                    <p>• 남의 말에 현혹된 위험한 투자를 경계하고, 본인이 직접 검증한 문서/시스템 자산에 집중하십시오.</p>
                    <p>• 주중 수요일이나 목요일 오전에 서남쪽 방향에서 만나는 귀인과의 협상이 자산 증식의 큰 열쇠가 됩니다.</p>
                </div>
            </div>

            <!-- 3. 평생 귀인/상극 인연 & 종합 개운 비급 -->
            <div class='bg-emerald-50/90 p-4 rounded-2xl border border-emerald-200 space-y-3'>
                <h4 class='text-sm font-black text-emerald-950 flex items-center gap-1.5 border-b pb-2 border-emerald-300'>
                    <span>🤝 3. {user_name}님의 평생 귀인/상극 인연 & 종합 개운 비급</span>
                </h4>
                <div class='space-y-1.5'>
                    <p class='text-emerald-900 font-bold'>🌟 평생 나를 돕는 귀인: 쥐띠, 소띠, 뱀띠 (서북쪽 및 동남쪽 방향)</p>
                    <p class='text-slate-600 text-[11px] leading-normal'>감정적으로 흔들릴 때 차분하게 중심을 잡아주며, 법률, 세무, 대형 계약 등 결정적 순간에 실질적인 해결책을 안겨주는 평생의 동반자입니다.</p>
                </div>
                <div class='pt-2 border-t border-emerald-200 space-y-1.5'>
                    <p class='text-rose-700 font-bold'>⚠️ 평생 주의해야 할 상극 인연: 호랑이띠, 토끼띠</p>
                    <p class='text-slate-600 text-[11px] leading-normal'>성향이 지나치게 강해 사소한 의견 차이로도 자존심 싸움이 번질 수 있습니다. 금전 거래나 동업 시 반드시 공증과 서면 계약을 철저히 하십시오.</p>
                </div>
                <div class='pt-2 border-t border-emerald-200 space-y-1.5 text-[11px]'>
                    <p class='font-bold text-emerald-950'>🎨 오행 체질 맞춤 개운 비급 (색상/방향/음식):</p>
                    <p>• <strong>행운의 색상:</strong> 아이보리, 스카이 블루, 황금색 계열 의상 및 소품 추천.</p>
                    <p>• <strong>개운 음식:</strong> 미온수, 검은콩, 견과류, 신선한 야채 중심 식단으로 수(水)기운 보강.</p>
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
    
    if theme == "wealth":
        return {
            "title": f"💰 {user_name}님의 평생 재물 그릇 & 금고운 심층 리포트",
            "content": f"""
            <div class='space-y-4 text-xs text-slate-700 leading-relaxed text-left p-1'>
                <div class='p-3.5 bg-amber-50 rounded-2xl border border-amber-200 space-y-1'>
                    <p class='font-bold text-amber-950 text-sm'>[재물 그릇의 본질] '금고형' 자산 축적 원국</p>
                    <p class='text-[11px] text-amber-900'>일확천금의 위험한 투기보다 체계적인 시스템과 현금 흐름을 통해 복리로 부를 쌓아 올리는 대기만성형 황금 금고를 타고났습니다.</p>
                </div>
                
                <div class='space-y-2'>
                    <p class='font-bold text-slate-900 text-xs'>1. {user_name}님 맞춤 최적 자산 포트폴리오 전략</p>
                    <p class='text-[11px] text-slate-600 leading-normal'>변동성이 극심한 주식 단타나 코인 등 리스크가 높은 자산은 재물 유실을 유발하기 쉽습니다. 실물 부동산(상가, 토지, 안정적 주거 자산) 및 배당형 우량 자산에 전체 자산의 70% 이상을 배분할 때 손실 없이 안정적인 우상향 그래프를 그립니다.</p>
                </div>

                <div class='space-y-2'>
                    <p class='font-bold text-slate-900 text-xs'>2. 재물운이 폭발하는 인생 최고의 대박 타이밍</p>
                    <p class='text-[11px] text-slate-600 leading-normal'>40대 중후반과 50대 초반 구간에 강력한 문서운(印星/財星)이 연이어 들어옵니다. 이 시기에 계약한 계약서나 보유 부동산의 가치가 최소 2배 이상 수직 상승하는 퀀텀점프의 기회를 맞이하게 됩니다.</p>
                </div>

                <div class='space-y-2'>
                    <p class='font-bold text-slate-900 text-xs'>3. 손재수(損財數) 및 헛돈 방어 개운 비방</p>
                    <p class='text-[11px] text-slate-600 leading-normal'>지인이나 가까운 친족 간의 구두 금전 대여는 절대 금물입니다. 집 안이나 사무실의 서남쪽 방향에 황금빛 소품이나 금속 재질의 인테리어를 배치하고, 노란색 계열의 지갑을 사용할 때 새어나가는 재물의 기운을 완벽하게 차단할 수 있습니다.</p>
                </div>
            </div>
            """
        }
    elif theme == "love":
        return {
            "title": f"💖 {user_name}님의 평생 애정운 & 인연법 ({sub_opt} 맞춤)",
            "content": f"""
            <div class='space-y-4 text-xs text-slate-700 leading-relaxed text-left p-1'>
                <div class='p-3.5 bg-rose-50 rounded-2xl border border-rose-200 space-y-1'>
                    <p class='font-bold text-rose-950 text-sm'>[현재 상태: {sub_opt}] 맞춤 애정 정밀 감명</p>
                    <p class='text-[11px] text-rose-900'>현재 {user_name}님의 기운은 내면의 깊은 신뢰와 유대감을 형성하기에 가장 안정적이고 온화한 상태입니다.</p>
                </div>

                <div class='space-y-2'>
                    <p class='font-bold text-slate-900 text-xs'>1. 나에게 운명적으로 맞는 평생 배필의 특징</p>
                    <p class='text-[11px] text-slate-600 leading-normal'>겉치레나 화려한 언변보다는 대화가 깊이 통하고 배려심이 깊으며, {user_name}님의 열정적이고 주도적인 성향을 묵묵히 품어주는 차분한 인품의 소유자와 가장 고품격 궁합을 이룹니다.</p>
                </div>

                <div class='space-y-2'>
                    <p class='font-bold text-slate-900 text-xs'>2. 시기별 애정 흐름 및 관계 발전 가이드</p>
                    <p class='text-[11px] text-slate-600 leading-normal'>상반기에는 서로의 가치관을 확인하며 소통의 깊이를 더하고, 하반기로 갈수록 두 사람 사이의 현실적 결속력(미래 설계, 공동 자산 관리, 안정적 결혼 생활)이 매우 단단해지는 대길의 흐름입니다.</p>
                </div>

                <div class='space-y-2'>
                    <p class='font-bold text-slate-900 text-xs'>3. 인연의 온도를 평생 유지하는 핵심 처세법</p>
                    <p class='text-[11px] text-slate-600 leading-normal'>서운한 감정이 생겼을 때는 즉각적으로 대립하기보다 하루의 여유를 두고 차분히 감정을 정리한 뒤 대화하는 것이 애정운의 불꽃을 평생 지키는 최고의 비결입니다.</p>
                </div>
            </div>
            """
        }
    elif theme == "business":
        return {
            "title": f"🏢 {user_name}님의 사업 & 직업 성공 대길운 ({sub_opt} 맞춤)",
            "content": f"""
            <div class='space-y-4 text-xs text-slate-700 leading-relaxed text-left p-1'>
                <div class='p-3.5 bg-blue-50 rounded-2xl border border-blue-200 space-y-1'>
                    <p class='font-bold text-blue-950 text-sm'>[직업군 상태: {sub_opt}] 대길 성공 로드맵</p>
                    <p class='text-[11px] text-blue-900'>치밀한 기획력과 디테일한 실행력이 완벽히 결합되어 어떤 조직이나 분야에서든 핵심 수장으로 두각을 나타낼 사주 구조입니다.</p>
                </div>

                <div class='space-y-2'>
                    <p class='font-bold text-slate-900 text-xs'>1. 성공을 보장하는 대박 직무/사업 분야</p>
                    <p class='text-[11px] text-slate-600 leading-normal'>전문 컨설팅, IT/기술 기획, 유통 및 브랜드 매니지먼트, 자산 관리, 인재 개발 등 체계적인 시스템을 구축하고 사람과 자원을 연결하는 영역에서 귀하의 능력이 최고 가치로 환산됩니다.</p>
                </div>

                <div class='space-y-2'>
                    <p class='font-bold text-slate-900 text-xs'>2. 승진/이직/창업 성공의 최적 타이밍</p>
                    <p class='text-[11px] text-slate-600 leading-normal'>가을과 겨울로 넘어가는 환절기 구간에 나를 강력히 끌어주는 결정적 귀인(상사, 거대 파트너사)이 등장합니다. 이 시기 추진하는 신규 사업이나 이직은 성공 확률이 3배 이상 높아집니다.</p>
                </div>

                <div class='space-y-2'>
                    <p class='font-bold text-slate-900 text-xs'>3. 사업적 성공을 완성하는 리더십 지침</p>
                    <p class='text-[11px] text-slate-600 leading-normal'>모든 실무를 본인이 직접 도맡으려 하지 말고, 검증된 신뢰할 수 있는 파트너에게 과감하게 역할을 위임하고 전체 판을 조율할 때 성과의 규모가 비약적으로 확장됩니다.</p>
                </div>
            </div>
            """
        }
    else: # health
        return {
            "title": f"🌿 {user_name}님의 평생 오행 체질 & 건강 개운법",
            "content": f"""
            <div class='space-y-4 text-xs text-slate-700 leading-relaxed text-left p-1'>
                <div class='p-3.5 bg-emerald-50 rounded-2xl border border-emerald-200 space-y-1'>
                    <p class='font-bold text-emerald-950 text-sm'>[오행 체질 진단] 화(火)·토(土) 왕성 체질</p>
                    <p class='text-[11px] text-emerald-900'>대사 활동과 생명력은 매우 왕성하나, 상대적으로 수(水)와 금(金) 기운이 빠르게 소모될 수 있는 체질적 특성을 지녔습니다.</p>
                </div>

                <div class='space-y-2'>
                    <p class='font-bold text-slate-900 text-xs'>1. 평생 집중 관리해야 할 취약 장기</p>
                    <p class='text-[11px] text-slate-600 leading-normal'>심혈관계의 과도한 열기를 조절하고, 신장, 방광, 관절 및 호흡기 계통의 수분을 충분히 보충하는 생활 습관이 평생 장수와 활력의 핵심 열쇠입니다.</p>
                </div>

                <div class='space-y-2'>
                    <p class='font-bold text-slate-900 text-xs'>2. 체질을 다스리는 맞춤 섭생 가이드</p>
                    <p class='text-[11px] text-slate-600 leading-normal'>자극적이고 과도하게 매운 음식이나 차가운 음료는 피하십시오. 검은깨, 검은콩, 해조류, 미온수 등 신장 기능을 보강하는 블랙푸드를 식단에 적극 곁들이는 것이 좋습니다.</p>
                </div>

                <div class='space-y-2'>
                    <p class='font-bold text-slate-900 text-xs'>3. 100세 건강을 완성하는 일상 개운 루틴</p>
                    <p class='text-[11px] text-slate-600 leading-normal'>매일 취침 전 10분간의 따뜻한 족욕이나 가벼운 명상을 통해 머리의 상기된 열을 발끝으로 내리는 수승화강(水昇火降) 루틴을 실천하면 수면의 질이 획기적으로 개선됩니다.</p>
                </div>
            </div>
            """
        }
