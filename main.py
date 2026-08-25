import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional
import os

app = FastAPI(title="운세의 신 PRO API", version="4.4.0")

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

# 타로 메이저 카드 심층 해설 데이터베이스
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
        "symbolism": "흑과 백의 기둥(B와 J) 사이에 앉아 토라(TORA) 스크롤을 쥔 여사제는 이성과 감성의 조화, 표면 아래 숨겨진 본질적 진실과 영적인 직관을 상징합니다.",
        "fortune_reading": "겉으로 드러난 말보다 상대방의 숨은 의도나 상황의 이면을 꿰뚫어 보는 혜안이 극대화되는 날입니다. 성급하게 감정적으로 반응하거나 행동하기보다는, 한 걸음 물러서서 차분히 상황을 관찰할 때 가장 정확한 해답을 찾을 수 있습니다.",
        "advice": "중요한 계약이나 감정적인 결정은 하루 이틀 여유를 두고 심사숙고하세요. 비밀 유지가 필수적이며, 경솔한 발언을 삼가고 경청에 집중하는 것이 유리합니다.",
        "action_tip": "조용한 장소에서 차를 마시며 생각을 차분히 정리하는 시간을 10분간 가지세요."
    },
    {
        "name": "III. THE EMPRESS (여황제)",
        "keyword": "풍요로운 결실 · 따뜻한 포용 · 물질적 번영",
        "symbolism": "황금빛 곡식 밭에 기대앉아 12개의 별이 박힌 왕관을 쓴 여황제는 대자연의 풍요, 결실의 수확, 그리고 주변을 너그럽게 품어주는 모성애적 온정을 상징합니다.",
        "fortune_reading": "그동안 쏟아부은 노력과 인내가 풍성한 결실과 금전적 안정으로 환원되는 날입니다. 주변 사람들과의 관계가 화기애애해지고, 베푼 호의가 두 배의 행운이 되어 되돌아옵니다. 편안하고 너그러운 태도가 사람을 끌어모읍니다.",
        "advice": "혼자만의 성과에 도취되지 말고 함께 고생한 동료나 가족에게 고마움을 전하세요. 식사 대접이나 따뜻한 격려 한마디가 평생의 귀인 인연을 만듭니다.",
        "action_tip": "가장 소중한 사람에게 감사의 메시지를 보내거나 맛있는 식사를 대접하세요."
    },
    {
        "name": "IV. THE EMPEROR (황제)",
        "keyword": "확고한 리더십 · 안정된 질서 · 목표 달성",
        "symbolism": "돌로 된 굳건한 옥좌에 앉아 보주와 홀을 쥐고 있는 황제는 흔들리지 않는 원칙, 조직을 수호하는 카리스마, 그리고 세속적인 권력과 기반의 확립을 상징합니다.",
        "fortune_reading": "흐트러진 기강을 바로잡고 목표를 향해 조직을 진두지휘해야 하는 날입니다. 명확한 가이드라인과 원칙을 제시할 때 사람들의 신뢰를 얻으며, 추진 중인 일이 굳건한 반석 위에 오르게 됩니다. 결단력을 발휘하십시오.",
        "advice": "감정에 치우치지 말고 이성적이고 객관적인 데이터에 기반해 판단하세요. 지나친 고집은 경계하되, 핵심 원칙만큼은 타협 없이 밀고 나가는 뚝심이 필요합니다.",
        "action_tip": "오늘 꼭 완수해야 할 핵심 업무 3가지를 정리하고 단호하게 실행하세요."
    },
    {
        "name": "VI. THE LOVERS (연인)",
        "keyword": "진정한 교감 · 조화로운 선택 · 파트너십",
        "symbolism": "천사 라파엘의 축복 아래 서 있는 남녀는 순수한 사랑과 소통, 그리고 인생의 중대한 갈림길에서 올바른 가치관에 입각한 선택을 상징합니다.",
        "fortune_reading": "마음이 통하는 동료, 연인, 비즈니스 파트너와의 호흡이 최상으로 맞아떨어지는 날입니다. 혼자 끙끙 앓던 문제도 상대방과의 대화를 통해 명쾌한 해법을 찾게 됩니다. 화합과 협업을 통해 시너지를 창출하기에 완벽합니다.",
        "advice": "솔직한 감정과 진심을 표현하세요. 계산적인 태도를 버리고 서로의 장점을 존중하며 협력할 때 장기적으로 큰 이익과 안정을 얻게 됩니다.",
        "action_tip": "마찰이 있던 상대에게 먼저 부드러운 안부 인사를 건네며 대화의 물꼬를 트세요."
    },
    {
        "name": "X. WHEEL OF FORTUNE (운명의 수레바퀴)",
        "keyword": "행운의 전환점 · 필연적 기회 · 운명의 상승기류",
        "symbolism": "끊임없이 회전하는 수레바퀴와 사방의 4대 복음서 동물들은 우주 삼라만상의 순환, 거스를 수 없는 필연적인 운명의 전환과 새로운 도약의 사이클을 상징합니다.",
        "fortune_reading": "정체되었던 정국이 풀리고 귀하에게 유리한 상승기류의 파도가 들어오는 날입니다. 생각지도 못했던 경로에서 뜻밖의 기회나 제안이 찾아오며, 풀리지 않던 난제가 자연스럽게 해결되는 행운의 전환점입니다.",
        "advice": "익숙하고 편안한 과거의 틀에 안주하지 말고, 새롭게 다가오는 변화의 흐름에 유연하게 편승하세요. 타이밍을 놓치지 않고 빠르게 반응하는 것이 핵심입니다.",
        "action_tip": "예상치 못한 제안이나 연락이 오면 긍정적으로 검토하고 기회를 낚아채세요."
    },
    {
        "name": "XIX. THE SUN (태양)",
        "keyword": "눈부신 성공 · 생명력과 활력 · 명예와 축하",
        "symbolism": "해바라기 꽃밭 위로 환하게 떠오른 태양과 백마를 탄 어린아이는 모든 어둠과 불안의 종식, 순수한 기쁨, 그리고 만천하에 드러나는 빛나는 성취를 상징합니다.",
        "fortune_reading": "그 어떤 근심이나 장애물도 귀하의 밝은 기운을 막을 수 없는 최고의 대길(大吉)의 날입니다. 귀하의 성과가 많은 사람에게 인정받아 칭찬과 명예를 얻게 되며, 몸과 마음에 넘치는 에너지와 자신감이 가득 찹니다.",
        "advice": "마음껏 활기를 발산하고 성취를 즐기세요. 긍정적인 기운은 주변 사람들에게도 큰 힘이 되며, 더 큰 복록과 협력자를 불러들이는 자석 역할을 합니다.",
        "action_tip": "낮 시간대 10분간 햇볕을 쬐며 긍정 에너지를 충전하고 성과를 축하하세요."
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
            
    elem_percentages = {
        k: round((v / total_chars) * 100, 1) for k, v in elem_counts.items()
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
