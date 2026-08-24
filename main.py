import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import os

app = FastAPI(title="운세의 신 PRO API", version="3.0.0")

# 60갑자 및 천간/지지 상수
CHEONGAN = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
CHEONGAN_HANJA = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
JIJI = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]
JIJI_HANJA = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
ANIMALS = ["쥐", "소", "호랑이", "토끼", "용", "뱀", "말", "양", "원숭이", "닭", "개", "돼지"]
OHENG = ["목", "화", "토", "금", "수"]

# 지장간 (초기, 중기, 정기)
JIJANGGAN_MAP = {
    "子": {"cho": "壬 (임)", "jung": "-", "jung_gi": "癸 (계)"},
    "丑": {"cho": "癸 (계)", "jung": "辛 (신)", "jung_gi": "己 (기)"},
    "寅": {"cho": "戊 (무)", "jung": "丙 (병)", "jung_gi": "甲 (갑)"},
    "卯": {"cho": "甲 (갑)", "jung": "-", "jung_gi": "乙 (을)"},
    "辰": {"cho": "乙 (을)", "jung": "癸 (계)", "jung_gi": "戊 (무)"},
    "巳": {"cho": "戊 (무)", "jung": "庚 (경)", "jung_gi": "丙 (병)"},
    "午": {"cho": "丙 (병)", "jung": "己 (기)", "jung_gi": "丁 (정)"},
    "未": {"cho": "丁 (정)", "jung": "乙 (을)", "jung_gi": "己 (기)"},
    "申": {"cho": "戊 (무)", "jung": "壬 (임)", "jung_gi": "庚 (경)"},
    "酉": {"cho": "庚 (경)", "jung": "-", "jung_gi": "辛 (신)"},
    "戌": {"cho": "辛 (신)", "jung": "丁 (정)", "jung_gi": "戊 (무)"},
    "亥": {"cho": "戊 (무)", "jung": "甲 (갑)", "jung_gi": "壬 (임)"}
}

# 12종 고유 부적 마스터
TALISMAN_LIST = [
    {"title": "재물만복부 (萬福符)", "chinese": "勅令 · 萬福大吉", "power": "재물 증식 · 금전운 대통", "desc": "사방에서 금전과 복록이 샘솟듯 모여드는 강력한 재물 비급 부적입니다."},
    {"title": "금고수호부 (金庫守護符)", "chinese": "勅令 · 金庫安穩", "power": "자산 방어 · 누수 차단", "desc": "새어나가는 헛돈을 철통같이 막아주고 보유 자산을 굳건히 지켜줍니다."},
    {"title": "사업대성부 (事業大成符)", "chinese": "勅令 · 萬事亨通", "power": "사업 번창 · 계약 성사", "desc": "막혔던 활로를 시원하게 뚫어주고 거래와 사업 번창을 돕는 부적입니다."},
    {"title": "인연화합부 (因緣和合符)", "chinese": "勅令 · 夫妻和合", "power": "애정 화합 · 갈등 해소", "desc": "인연 사이의 오해와 마찰을 씻어내고 깊은 신뢰와 온기를 이어줍니다."},
    {"title": "도화매혹부 (桃花魅惑符)", "chinese": "勅令 · 桃花發顯", "power": "매력 극대화 · 이성 호감", "desc": "본연의 치명적인 매력을 드러내어 좋은 인연들의 호감을 사로잡습니다."},
    {"title": "소원성취부 (所願成就符)", "chinese": "勅令 · 如意滿成", "power": "소원 만성 · 장애 극복", "desc": "오랫동안 품어온 염원을 현실로 이끌어내고 난관을 극복하게 돕습니다."},
    {"title": "천우신조부 (天佑神助符)", "chinese": "勅令 · 貴人助勢", "power": "귀인 조력 · 위기 탈출", "desc": "절체절명의 순간 하늘의 도움과 결정적인 귀인의 손길을 연결합니다."},
    {"title": "관운승진부 (官運昇進符)", "chinese": "勅令 · 官祿大吉", "power": "승진 합격 · 명예 상승", "desc": "직장 내 인정과 승진, 영전의 기운을 강력하게 끌어올려 줍니다."},
    {"title": "장원급제부 (壯元及第符)", "chinese": "勅令 · 文運昌盛", "power": "시험 합격 · 집중력 강화", "desc": "두뇌를 맑게 하고 시험과 심사에서 최고의 역량을 발휘하게 합니다."},
    {"title": "벽사소재부 (辟邪消災符)", "chinese": "勅令 · 凶厄退去", "power": "액운 소멸 · 삼재 퇴치", "desc": "칠성검의 서슬 퍼런 기운으로 몸을 맴도는 액운과 살성을 일시에 벱니다."},
    {"title": "칠성무병부 (七星無病符)", "chinese": "勅令 · 壽命延長", "power": "건강 회복 · 무병 장수", "desc": "북두칠성의 생명 에너지를 받아 신체의 기혈을 돕고 건강을 지킵니다."},
    {"title": "심신안정부 (心身安定符)", "chinese": "勅令 · 淸心安寧", "power": "불안 해소 · 숙면 평온", "desc": "혼란한 마음에 태극의 안정을 불어넣어 평온과 숙면을 선사합니다."}
]

# 타로 카드 마스터
TAROT_CARDS = [
    {"name": "0. THE FOOL (바보)", "keyword": "새로운 시작, 순수한 모험", "overview": "망설임을 내려놓고 가벼운 마음으로 첫발을 내딛기 좋은 타이밍입니다.", "action": "계산보다 직관을 믿고 가볍게 시도해보세요."},
    {"name": "I. THE MAGICIAN (마법사)", "keyword": "창조적 재능, 무한한 잠재력", "overview": "당신이 가진 모든 도구와 능력을 온전히 발휘할 수 있는 역동적인 날입니다.", "action": "주도권을 쥐고 자신의 실력을 솔직하게 드러내세요."},
    {"name": "II. THE HIGH PRIESTESS (여사제)", "keyword": "깊은 통찰력, 내면의 직관", "overview": "성급히 행동하기보다 상황을 조용히 관찰하며 내면의 지혜를 모을 때입니다.", "action": "비밀을 지키고 직관의 소리에 귀 기울이세요."},
    {"name": "III. THE EMPRESS (여황제)", "keyword": "풍요, 사랑과 결실", "overview": "노력했던 일들이 따뜻한 결실과 풍요로움으로 되돌아오는 날입니다.", "action": "주변에 온정을 나누고 여유로운 미소를 머금으세요."},
    {"name": "IV. THE EMPEROR (황제)", "keyword": "확고한 통제력, 책임감", "overview": "원칙과 확고한 기준을 세워 상황을 리드해야 하는 날입니다.", "action": "약속을 철저히 지키고 단호하게 결정하세요."},
    {"name": "VI. THE LOVERS (연인)", "keyword": "진정한 교감, 조화로운 선택", "overview": "사람들과의 호흡이 환상적으로 맞아떨어지며 기분 좋은 유대가 형성됩니다.", "action": "마음을 솔직하게 표현하고 협력의 손을 잡으세요."},
    {"name": "X. WHEEL OF FORTUNE (운명의 수레바퀴)", "keyword": "행운의 전환점, 기회", "overview": "정체되었던 흐름이 풀리고 생각지 못한 기회의 바람이 불어옵니다.", "action": "변화의 파도에 유연하게 몸을 맡기세요."},
    {"name": "XIX. THE SUN (태양)", "keyword": "눈부신 성공, 활력", "overview": "어둠이 걷히고 모든 것이 투명하게 빛나는 최고의 긍정 에너지입니다.", "action": "자신감을 갖고 당당하게 하루를 만끽하세요."}
]

class SajuRequest(BaseModel):
    name: str
    year: int
    month: int
    day: int
    calendar_type: Optional[str] = "solar" # solar, lunar, leap
    sijin_index: Optional[int] = 5
    is_unknown_time: Optional[bool] = False

@app.get("/")
def serve_home():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return HTMLResponse("<h2>운세의 신 PRO 인덱스 파일 준비 중입니다.</h2>")

@app.post("/api/analyze")
def analyze_saju(req: SajuRequest):
    # 1. 4기둥 명식 계산 (음력 보정 및 60갑자 산출)
    year_offset = (req.year - 4) % 60
    y_cg = CHEONGAN_HANJA[year_offset % 10]
    y_jj = JIJI_HANJA[year_offset % 12]
    y_animal = ANIMALS[year_offset % 12]

    m_cg = CHEONGAN_HANJA[(req.month + 2) % 10]
    m_jj = JIJI_HANJA[(req.month + 1) % 12]

    # 일주 산출
    d_seed = (req.year * 365 + req.month * 30 + req.day + (1 if req.calendar_type != 'solar' else 0)) % 60
    d_cg = CHEONGAN_HANJA[d_seed % 10]
    d_jj = JIJI_HANJA[d_seed % 12]
    d_animal = ANIMALS[d_seed % 12]

    # 시주 산출
    if req.is_unknown_time or req.sijin_index is None or req.sijin_index < 0:
        h_pillar = "時未詳"
        h_cg = "-"
        h_jj = "-"
    else:
        h_cg = CHEONGAN_HANJA[(d_seed % 10 * 2 + req.sijin_index) % 10]
        h_jj = JIJI_HANJA[req.sijin_index]
        h_pillar = f"{h_cg}{h_jj}"

    # 2. 사주 MBTI & 수호 동물 매핑
    mbti_types = [
        {"type": "솔직담백 열정 불꽃러 (ESTP형)", "desc": "도전적이고 거침없는 추진력을 자랑하는 개척자"},
        {"type": "단단한 현실주의 바위 (ISTJ형)", "desc": "묵묵히 신뢰를 쌓아가는 든든한 맏형 같은 존재"},
        {"type": "다정다감 배려의 숲 (ENFJ형)", "desc": "주변 사람들을 품어주고 조화를 이끄는 리더"},
        {"type": "깊은 지혜의 새벽바다 (INTP형)", "desc": "통찰력이 깊고 본질을 꿰뚫어 보는 지략가"},
        {"type": "빛나는 영감의 황금별 (ENTP형)", "desc": "센스가 넘치고 어떤 환경에서도 빛을 발하는 재주꾼"}
    ]
    user_mbti = mbti_types[d_seed % len(mbti_types)]

    # 3. 평생 귀인 vs 상극 인연
    guiin_animals = ["소띠", "쥐띠", "용띠", "닭띠"][(d_seed) % 4]
    guiin_trait = "차분하고 논리적으로 내 부족한 부분을 메워주며, 결정적인 순간에 지혜로운 해결책을 제시해 주는 인연"
    
    sanggeuk_animals = ["양띠", "말띠", "개띠", "호랑이띠"][(d_seed + 2) % 4]
    sanggeuk_trait = "성격이 급하거나 감정 기복이 있어 사소한 말 한마디로 오해가 생기기 쉬우니 한 템포 쉬어가는 대화가 필요한 인연"

    # 4. 오늘의 일진 & 총평
    daily_score = 88 + (d_seed % 11)
    daily_titles = [
        "귀인의 조력으로 매듭이 풀리는 순풍의 하루",
        "금빛 기운이 서서히 솟아나는 도약의 하루",
        "지혜로운 판단이 빛을 발하는 결실의 하루",
        "뿌린 대로 거두는 든든하고 안정적인 하루"
    ]
    daily_advices = [
        "생각지 못한 제안이나 기분 좋은 소식이 찾아옵니다. 주위 사람들과의 대화 속에서 오래된 고민의 실마리를 찾게 되니 경청하는 태도를 유지하세요.",
        "정체되었던 기운이 활기를 띠며 새로운 기회가 열립니다. 망설였던 계획이 있다면 오늘 과감하게 첫걸음을 내딛는 것이 유리합니다.",
        "냉철한 이성과 직관이 조화를 이루는 날입니다. 중요한 결정이나 계약이 있다면 오늘 집중력을 발휘해 매듭지으세요.",
        "성실하게 쌓아온 신뢰가 빛을 발하는 날입니다. 서두르지 않고 묵묵히 내 페이스를 지키면 기대 이상의 안정적인 성과가 따릅니다."
    ]

    selected_talisman = TALISMAN_LIST[d_seed % len(TALISMAN_LIST)]

    return {
        "user_name": req.name,
        "saju_data": {
            "year_pillar": f"{y_cg}{y_jj} ({y_animal}띠)",
            "month_pillar": f"{m_cg}{m_jj}",
            "day_pillar": f"{d_cg}{d_jj} ({d_animal}의 날)",
            "hour_pillar": h_pillar,
            "pillars_detail": {
                "year": {"cg": y_cg, "jj": y_jj, "jjg": JIJANGGAN_MAP.get(y_jj, {})},
                "month": {"cg": m_cg, "jj": m_jj, "jjg": JIJANGGAN_MAP.get(m_jj, {})},
                "day": {"cg": d_cg, "jj": d_jj, "jjg": JIJANGGAN_MAP.get(d_jj, {})},
                "hour": {"cg": h_cg, "jj": h_jj, "jjg": JIJANGGAN_MAP.get(h_jj, {})}
            },
            "mbti": user_mbti,
            "animal_symbol": d_animal,
            "elements": {"wood": 20, "fire": 25, "earth": 20, "metal": 20, "water": 15},
            "guiin_analysis": {
                "good_animals": guiin_animals,
                "good_trait": guiin_trait,
                "bad_animals": sanggeuk_animals,
                "bad_trait": sanggeuk_trait
            }
        },
        "daily_fortune": {
            "score": daily_score,
            "title": daily_titles[d_seed % len(daily_titles)],
            "advice": daily_advices[d_seed % len(daily_advices)],
            "lucky_color": ["포레스트 그린 / 골드", "스카이 블루 / 아이보리", "웜 베이지 / 네이비", "밀키 화이트 / 코랄"][d_seed % 4],
            "lucky_number": ["3, 8", "1, 6", "5, 0", "4, 9"][d_seed % 4],
            "lucky_direction": ["동남쪽", "정북쪽", "서남쪽", "동북쪽"][d_seed % 4],
            "fashion_style": ["단정하고 깔끔한 세미 캐주얼", "부드러운 니트 또는 셔츠", "신뢰감을 주는 모노톤 셋업", "산뜻한 포인트 컬러 악세서리"][d_seed % 4],
            "recommended_menu": ["속이 편안한 한식 또는 영양 솥밥", "신선한 샐러드와 담백한 단백질 식단", "따뜻한 국물 요리와 차", "풍미가 깊은 파스타나 덮밥"][d_seed % 4],
            "mindset": "상대의 말에 한 번 더 공감하고, 내 주장은 부드럽고 명확하게 전달하기",
            "action": "오전 중 따뜻한 차 한 잔을 마시며 핵심 목표 3가지를 메모하세요.",
            "talisman": selected_talisman
        }
    }

@app.get("/api/daily-tarot")
def get_daily_tarot(slot: int = 1, rand_seed: Optional[str] = None):
    idx = (int(rand_seed or "1") + slot * 3) % len(TAROT_CARDS)
    return TAROT_CARDS[idx]

# 테마운세 심층 리포트 (A4 1장 핵심 리포트)
@app.post("/api/theme-report")
def get_theme_report(req: dict):
    theme = req.get("theme", "wealth")
    sub_option = req.get("sub_option", "")
    
    if theme == "wealth":
        return {
            "title": "💰 평생 재물 그릇 & 금고운 심층 감명",
            "content": """
            <div class='space-y-3 leading-relaxed text-xs text-slate-700'>
                <p><strong>[타고난 재물 그릇]</strong> 귀하의 원국은 천간의 정재(正財)와 지지의 튼튼한 뿌리가 조화를 이루어, 일확천금보다는 <strong>체계적으로 자산을 축적하고 방어하는 금고형 그릇</strong>을 타고났습니다.</p>
                <p><strong>[투자 및 부동산 적합도]</strong> 변동성이 극심한 단기 투기보다는 안정적인 부동산 실물 자산 및 배당 중심의 가치 투자에서 월등한 수익률을 보입니다. 특히 40대 중반 이후 문서운이 크게 트여 자산 증식이 가속화됩니다.</p>
                <p><strong>[재물 개운 처방]</strong> 통장을 지출용과 저축용으로 철저히 분리하고, 서남쪽 방향에 황금색 또는 도자기 소품을 두면 재물의 누수를 막는 데 매우 유익합니다.</p>
            </div>
            """
        }
    elif theme == "love":
        return {
            "title": f"💖 평생 애정운 & 인연법 ({sub_option} 맞춤)",
            "content": f"""
            <div class='space-y-3 leading-relaxed text-xs text-slate-700'>
                <p><strong>[현재 상태 ({sub_option}) 분석]</strong> 현재 본인의 일간 기운이 안정화되어 있어, 상대방에게 신뢰와 따뜻한 안정감을 심어주기에 최적인 시기입니다.</p>
                <p><strong>[인연의 특징 및 배우자복]</strong> 나를 진심으로 존중해 주고 감정적 기복을 묵묵히 감싸주는 지혜롭고 바른 인품의 인연과 궁합이 가장 좋습니다. 겉모습보다는 대화가 잘 통하는 사람에게 집중하세요.</p>
                <p><strong>[애정 개운 처방]</strong> 서운한 점이 생겼을 때는 감정적으로 반응하기보다 하루 뒤 차분하게 대화로 푸는 것이 인연을 평생 지키는 비결입니다.</p>
            </div>
            """
        }
    elif theme == "business":
        return {
            "title": f"🏢 사업 & 직업 성공 대길운 ({sub_option} 맞춤)",
            "content": f"""
            <div class='space-y-3 leading-relaxed text-xs text-slate-700'>
                <p><strong>[직업/사업성 분석 ({sub_option})]</strong> 기획력과 디테일한 실행력이 뛰어나 조직 내 핵심 리더나 전문 분야 사업가로서 두각을 나타낼 사주 구조입니다.</p>
                <p><strong>[대박 전환 시기]</strong> 운의 흐름상 하반기로 갈수록 나를 끌어주는 상사나 든든한 파트너(귀인)의 조력이 붙어 추진하는 프로젝트의 성공 확률이 2배 이상 상승합니다.</p>
                <p><strong>[직업 성공 처방]</strong> 혼자 모든 것을 도맡으려 하지 말고 동료나 파트너에게 명확히 역할을 위임할 때 성과의 크기가 극대화됩니다.</p>
            </div>
            """
        }
    else: # health
        return {
            "title": "🌿 평생 오행 체질 & 건강 개운법",
            "content": """
            <div class='space-y-3 leading-relaxed text-xs text-slate-700'>
                <p><strong>[오행 체질 진단]</strong> 화(火)와 토(土) 기운이 발달하여 대사 기능이 활발하나, 상대적으로 수(水)와 금(金) 기운이 소모되기 쉬워 신장, 방광 및 호흡기 계통의 보강이 필요합니다.</p>
                <p><strong>[체질 맞춤 섭생법]</strong> 차가운 물보다는 미온수를 자주 섭취하고, 검은콩, 흑미, 견과류 등 신장 기능을 돕는 블랙푸드를 식단에 곁들이는 것이 좋습니다.</p>
                <p><strong>[건강 개운 액션]</strong> 취침 전 10분간의 가벼운 스트레칭과 명상으로 머리의 열을 발끝으로 내리는 수승화강(水昇火降) 루틴을 추천합니다.</p>
            </div>
            """
        }

@app.post("/api/daewoon-report")
def get_daewoon_report():
    return {
        "title": "👑 자미두수 & 10년 대운 심층 감명서",
        "content": """
        <div class='space-y-3 leading-relaxed text-xs text-slate-800'>
            <div class='p-3 bg-amber-50 rounded-2xl border border-amber-200 text-amber-950 font-bold'>
                🌟 현재 대운: 명예와 재물이 동시에 확장되는 '황금 도약기'
            </div>
            <p><strong>[자미두수 명궁 분석]</strong> 귀하의 명궁은 '자미성'과 '천부성'의 상조를 받아, 남 밑에서 수동적으로 일하기보다는 스스로 영역을 개척하고 사람들을 이끌 때 가장 큰 운의 복록을 누립니다.</p>
            <p><strong>[향후 10년 대운 흐름]</strong> 초반 3년은 기반을 단단히 다지는 시기이며, 4년 차부터 귀인의 강력한 서포트와 함께 재물과 지위가 수직 상승하는 대운의 분기점을 맞이합니다.</p>
            <p><strong>[대운 개운 지침]</strong> 과거의 성공 방식에 얽매이지 말고 새로운 기술과 인적 네트워크를 적극 수용하십시오. 시야를 넓힐수록 운의 그릇이 커집니다.</p>
        </div>
        """
    }
