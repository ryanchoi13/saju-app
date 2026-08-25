import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional
import os

app = FastAPI(title="운세의 신 PRO API", version="6.0.0")

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

# 30종 전통 경면주사 비급 부적 데이터베이스
TALISMAN_DATABASE = {
    # 1. 재물 & 금전 (6종)
    "wealth_1": {"type": "wealth", "pattern": "vault", "title": "암장금고부 (暗藏金庫符)", "power": "자산 방어 · 헛돈 누수 완벽 차단", "desc": "사주 원국의 금고를 단단히 잠그고 새어나가는 헛돈과 지출을 철통같이 방어하는 재물 수호 부적입니다."},
    "wealth_2": {"type": "wealth", "pattern": "coin", "title": "만복대길부 (萬福大吉符)", "power": "횡재수 · 사방 금전 대통", "desc": "사방에서 금전과 복록이 샘솟듯 모여들고 뜻밖의 목돈과 횡재수를 소환하는 전통 경면주사 부적입니다."},
    "wealth_3": {"type": "wealth", "pattern": "dividend", "title": "황금편재부 (黃金偏財符)", "power": "투자 대박 · 배당 수익 증식", "desc": "주식, 부동산, 투자 상품에서 탁월한 결단력을 발휘하여 수익을 극대화시키는 투자 특화 비급 부적입니다."},
    "wealth_4": {"type": "wealth", "pattern": "contract", "title": "문서취득부 (文書取得符)", "power": "부동산 당첨 · 알짜배기 문서운", "desc": "토지, 아파트 청약, 상가 등 실물 가치가 영구히 상승하는 귀한 부동산 문서를 쥐어주는 문서 부적입니다."},
    "wealth_5": {"type": "wealth", "pattern": "shield", "title": "손재소멸부 (損財消滅符)", "power": "금전 사기 예방 · 손실 방지", "desc": "빌려준 돈, 사기, 동업 손실 등 재물의 손실을 몰고 오는 탁한 악운을 깨끗이 소멸시키는 방어 부적입니다."},
    "wealth_6": {"type": "wealth", "pattern": "merchant", "title": "상업번창부 (商業繁昌符)", "power": "매출 폭발 · 단골 유치", "desc": "가게나 사업장에 손님의 발길이 끊이지 않고 일일 매출과 현금 흐름을 폭발적으로 증대시키는 상업 부적입니다."},

    # 2. 사업 & 직업 (6종)
    "business_1": {"type": "business", "pattern": "expand", "title": "사업형통부 (事業亨通符)", "power": "사업 활로 개척 · 판로 확장", "desc": "막혔던 프로젝트의 활로를 시원하게 뚫고 사업 규모를 거침없이 확장시키는 대표 사업 부적입니다."},
    "business_2": {"type": "business", "pattern": "promote", "title": "승진영전부 (昇進榮轉符)", "power": "초고속 승진 · 명예 상승", "desc": "조직 내에서 탁월한 역량을 인정받아 경쟁자를 제치고 상위 직급과 요직으로 영전시키는 출세 부적입니다."},
    "business_3": {"type": "business", "pattern": "pass", "title": "취업합격부 (就業合格符)", "power": "원서 합격 · 공채 최종 승리", "desc": "간절히 원하던 기업이나 공공기관의 시험, 면접에서 최종 합격의 영예를 안겨주는 합격 기원 부적입니다."},
    "business_4": {"type": "business", "pattern": "court", "title": "관재소멸부 (官災消滅符)", "power": "구설수 차단 · 소송 승소", "desc": "직장 내 모함, 시기 질투, 관공서 시비 및 소송 분쟁을 깔끔하게 잠재우고 승리를 이끄는 수호 부적입니다."},
    "business_5": {"type": "business", "pattern": "noble", "title": "천을귀인부 (天乙貴人符)", "power": "유력 조력자 소환 · 은인 상봉", "desc": "인생의 결정적 순간에 나타나 물심양면으로 길을 열어주는 천을귀인의 조력을 소환하는 비급 부적입니다."},
    "business_6": {"type": "business", "pattern": "deal", "title": "계약성사부 (契約成事符)", "power": "대형 계약 체결 · 납품 수주", "desc": "난항을 겪던 비즈니스 협상과 대규모 계약을 귀하에게 절대적으로 유리하게 성사시키는 협상 부적입니다."},

    # 3. 애정 & 인연 (6종)
    "love_1": {"type": "love", "pattern": "union", "title": "천생화합부 (天生和合符)", "power": "천생연분 결속 · 깊은 신뢰", "desc": "두 사람의 기운을 완벽하게 묶어 평생 서로를 존중하고 아끼는 백년가약의 인연을 맺어주는 화합 부적입니다."},
    "love_2": {"type": "love", "pattern": "charm", "title": "도화연정부 (桃花戀情符)", "power": "이성 매력 극대화 · 솔로 탈출", "desc": "숨겨진 치명적인 매력과 도화의 향기를 발현시켜 품격 높은 이성들의 호감을 이끌어내는 연애 부적입니다."},
    "love_3": {"type": "love", "pattern": "peace", "title": "원진소멸부 (怨嗔消滅符)", "power": "오해 해소 · 다툼 갈등 소멸", "desc": "연인이나 부부 사이의 사소한 오해, 성격 차이로 인한 다툼과 권태기를 눈 녹듯 사라지게 하는 평화 부적입니다."},
    "love_4": {"type": "love", "pattern": "family", "title": "부부백년부 (夫婦百年符)", "power": "가정 화목 · 자손 번창", "desc": "가정에 화목과 웃음꽃이 피어나게 하고 부부간의 애정을 신혼처럼 돈독하게 유지시키는 가정 수호 부적입니다."},
    "love_5": {"type": "love", "pattern": "reunion", "title": "재회소원부 (再會素願符)", "power": "헤어진 인연 재회 · 미련 청산", "desc": "안타깝게 엇갈렸던 인연과의 마음을 다시 연결하고 먼저 연락이 닿아 재결합을 돕는 재회 비급 부적입니다."},
    "love_6": {"type": "love", "pattern": "cut", "title": "악연차단부 (惡緣遮斷符)", "power": "악연 정리 · 스토커 퇴치", "desc": "나를 갉아먹는 유해한 인간관계와 집착하는 악연을 잡음 없이 깔끔하게 끊어내 주는 결계 부적입니다."},

    # 4. 건강 & 힐링 (6종)
    "health_1": {"type": "health", "pattern": "longevity", "title": "무병장수부 (無病長壽符)", "power": "100세 건강 · 면역력 증진", "desc": "체내의 탁한 음기를 몰아내고 오장육부의 활력을 극대화하여 평생 무병장수를 누리게 하는 장수 부적입니다."},
    "health_2": {"type": "health", "pattern": "circulation", "title": "수승화강부 (水昇火降符)", "power": "기혈 순환 · 피로 회복", "desc": "상체의 열기를 내리고 하체를 따뜻하게 하여 만성 피로와 스트레스를 씻은 듯이 회복시키는 순환 부적입니다."},
    "health_3": {"type": "health", "pattern": "mind", "title": "안심안정부 (安心安靜符)", "power": "불안 불면 해소 · 심신 평온", "desc": "복잡한 잡념과 불안감을 잠재우고 깊고 편안한 숙면을 유도하여 맑은 정신을 되찾아주는 힐링 부적입니다."},
    "health_4": {"type": "health", "pattern": "samjae", "title": "삼재소멸부 (三災消滅符)", "power": "악삼재 소멸 · 횡액 차단", "desc": "사주에 들어온 삼재팔난(三災八難)의 불운을 깨끗이 소멸시키고 복삼재로 반전시키는 최고 액막이 부적입니다."},
    "health_5": {"type": "health", "pattern": "traffic", "title": "사고방지부 (事故防止符)", "power": "교통사고 예방 · 낙상 방어", "desc": "운전 중 돌발 사고나 여행지에서의 불의의 낙상, 부상을 24시간 철통같이 막아주는 안전 호신 부적입니다."},
    "health_6": {"type": "health", "pattern": "vital", "title": "신기충만부 (神氣充滿符)", "power": "원기 회복 · 무기력 퇴치", "desc": "떨어진 체력과 의욕을 다시 불태우고 긍정적인 에너지를 가득 채워주는 활력 충전 비급 부적입니다."},

    # 5. 학업 & 소원 (6종)
    "wish_1": {"type": "wish", "pattern": "pass_exam", "title": "장원급제부 (壯元及第符)", "power": "국가고시 · 전문직 시험 수석", "desc": "공무원, 전문직, 수능 등 중요한 시험에서 실력 이상의 집중력과 운을 발휘하여 합격시키는 학업 부적입니다."},
    "wish_2": {"type": "wish", "pattern": "wisdom", "title": "지혜명철부 (智慧明徹符)", "power": "두뇌 회전 · 암기력 극대화", "desc": "복잡한 학습 내용과 기획서의 핵심을 단번에 꿰뚫는 명철한 지혜와 통찰력을 선물하는 총명 부적입니다."},
    "wish_3": {"type": "wish", "pattern": "wish_come", "title": "심상사성부 (心想事成符)", "power": "일생일대 1대 소원 성취", "desc": "마음속에 품고 있던 가장 간절한 소망 하나를 우주의 기운을 모아 기적처럼 현실로 이루어주는 소원 부적입니다."},
    "wish_4": {"type": "wish", "pattern": "all_luck", "title": "만사대길부 (萬事大吉符)", "power": "종합 운세 상승 · 대운 개방", "desc": "재물, 건강, 직업, 명예 모든 방면의 막힌 운을 동시에 열어 인생 전체를 꽃길로 이끄는 종합 대길 부적입니다."},
    "wish_5": {"type": "wish", "pattern": "reputation", "title": "명예대영부 (名譽大榮符)", "power": "대중 인기 · 사회적 권위", "desc": "자신의 이름과 브랜드가 널리 알려지고 대중의 신뢰와 높은 사회적 권위를 얻게 하는 명예 부적입니다."},
    "wish_6": {"type": "wish", "pattern": "protect", "title": "벽사소재부 (辟邪消除符)", "power": "악귀 퇴치 · 불운 척결", "desc": "주변에 맴도는 음습한 기운과 재수 없는 액운을 날카로운 경면주사의 칼날로 베어내는 벽사(辟邪) 부적입니다."}
}

TAROT_CARDS = [
    {
        "name": "0. THE FOOL (바보)",
        "keyword": "새로운 시작 · 순수한 열정 · 무한한 잠재력",
        "symbolism": "화려한 옷을 입고 절벽 끝에 서 있는 청년은 세상의 관습에 얽매이지 않는 순수한 영혼과 새로운 여정의 출발을 상징합니다.",
        "fortune_reading": "오늘은 오랫동안 머뭇거리던 일의 시작 단추를 꿰기에 더없이 좋은 날입니다. 직관을 따를 때 예상 밖의 통로가 열립니다.",
        "advice": "새로운 제안에 열린 마음을 가지되 발걸음은 가볍되 시선은 주변을 살피세요.",
        "action_tip": "오늘 떠오르는 아이디어를 즉시 메모하고 먼저 안부 연락을 건네보세요."
    },
    {
        "name": "I. THE MAGICIAN (마법사)",
        "keyword": "창조적 역량 · 완벽한 주도권 · 실력 발휘",
        "symbolism": "머리 위의 무한대(∞) 기호와 제단 위의 4대 원소는 모든 도구를 통제하는 지혜와 창조력을 상징합니다.",
        "fortune_reading": "귀하의 지식과 언변, 전문 기술이 빛을 발하는 날입니다. 당당한 태도로 판을 리드하기에 최적입니다.",
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
    
    # 일주
    d_cg_idx = (diff_days + 0) % 10
    d_jj_idx = (diff_days + 10) % 12
    d_cg = CHEONGAN_HANJA[d_cg_idx]
    d_jj = JIJI_HANJA[d_jj_idx]

    # 년주
    year_offset = (req.year - 4) % 60
    y_cg_idx = year_offset % 10
    y_jj_idx = year_offset % 12
    y_cg, y_jj = CHEONGAN_HANJA[y_cg_idx], JIJI_HANJA[y_jj_idx]

    # 월주
    m_jj_idx = (req.month) % 12
    m_cg_idx = (y_cg_idx % 5 * 2 + 2 + (req.month - 2)) % 10
    m_cg, m_jj = CHEONGAN_HANJA[m_cg_idx], JIJI_HANJA[m_jj_idx]

    # 시주
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

    # 지장간 가중치 오행 계산
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

    # [핵심] 사주 원국 3요소(결핍오행 + 일간 + 당일 날짜) 다차원 조합 부적 결정 엔진 (총 30종)
    elem_category_map = {
        "metal": "wealth",
        "wood": "business",
        "water": "love",
        "fire": "health",
        "earth": "wish"
    }
    
    # 1. 가장 보충이 시급한 결핍 오행 도출
    min_elem = min(elem_percentages, key=elem_percentages.get)
    cat = elem_category_map.get(min_elem, "wealth")

    # 2. 일간(천간 10종)과 당일 일진 기반 세부 1~6번 인덱스 결정
    day_seed = (d_cg_idx + d_jj_idx + datetime.date.today().day) % 6 + 1
    talisman_lookup_key = f"{cat}_{day_seed}"
    
    user_talisman = TALISMAN_DATABASE.get(talisman_lookup_key, TALISMAN_DATABASE["wealth_1"])

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
                    <p>• <strong>오행 궁합 조화:</strong> {user_name}님 사주에 꼭 필요한 水(물)과 金(쇠)의 차분한 기운을 채워줄 수 있는 띠(쥐띠, 닭띠, 원숭이띠)와 대길연을 이룹니다.</p>
                </div>
            </div>
            <div style="background: #FFFBEB; border: 1px solid #FDE68A; border-radius: 14px; padding: 12px;">
                <p style="font-weight: 800; color: #78350F; font-size: 12px; margin-bottom: 4px;">🌹 2. 평생 화목을 완성하는 실전 관계 처세법</p>
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
