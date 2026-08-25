import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import Optional
import os
import random

app = FastAPI(title="운세의 신 PRO API", version="10.0.1")

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

OHEANG_CURATION_MAP = {
    "wood": {
        "color": "에메랄드 그린 / 포레스트 올리브", "number": "3, 8", "direction": "정동쪽 (청룡 방위)",
        "style": "편안한 린넨 셔츠 또는 그린 톤 캐주얼", "menu": "신선한 샐러드와 녹차, 담백한 채식 식단",
        "mindset": "새로운 시작에 열린 자세를 갖고 적극 소통하기", "action": "아침 시간 가벼운 스트레칭과 산책하기"
    },
    "fire": {
        "color": "크림슨 레드 / 로즈 골드", "number": "2, 7", "direction": "정남쪽 (주작 방위)",
        "style": "포인트가 있는 화려한 니트나 레드 계열 타이", "menu": "따뜻한 국물 요리와 비타민 과일",
        "mindset": "열정을 당당하게 피력하고 사람들에게 미소 짓기", "action": "점심 식사 후 햇볕을 10분간 쬐며 활력 충전하기"
    },
    "earth": {
        "color": "웜 베이지 / 머스터드 옐로우", "number": "5, 10", "direction": "동북쪽 및 중앙 (황룡 방위)",
        "style": "단정하고 포근한 브라운 톤 재킷이나 코트", "menu": "속이 편안한 단호박죽과 잡곡밥",
        "mindset": "약속을 철저히 지키고 중심을 단단히 유지하기", "action": "주변 책상과 지갑 안의 영수증을 깔끔히 정리하기"
    },
    "metal": {
        "color": "스노우 화이트 / 실버 그레이", "number": "4, 9", "direction": "정서쪽 (백호 방위)",
        "style": "각 잡힌 화이트 셔츠와 세련된 메탈 시계", "menu": "도라지차, 신선한 견과류와 고단백 생선 요리",
        "mindset": "맺고 끊음을 명확히 하고 군더더기 없는 대화하기", "action": "오늘 완료해야 할 우선순위 3가지 메모하기"
    },
    "water": {
        "color": "미드나잇 블루 / 딥 네이비", "number": "1, 6", "direction": "정북쪽 (현무 방위)",
        "style": "세련된 네이비 셋업이나 부드러운 머플러", "menu": "맑은 미역국, 검은콩 두유와 미온수 섭취",
        "mindset": "상대의 의견을 깊이 경청하고 유연하게 대처하기", "action": "취침 전 따뜻한 족욕과 잔잔한 명상하기"
    }
}

TALISMAN_OHEANG_MAP = {
    "wood": {"type": "wood", "title": "사업대성부 (事業亨通符)", "power": "추진력 강화 · 사업 번창 · 승진운", "desc": "사주에 부족한 木(성장과 개척)의 활력을 불어넣어 막힌 활로를 뚫고 사업과 직무에서 강력한 주도권을 쥐게 하는 비급 부적입니다."},
    "fire": {"type": "fire", "title": "소원성취부 (心想事成符)", "power": "열정 회복 · 명예 상승 · 소원 성취", "desc": "사주에 부족한 火(열정과 확산)의 빛을 밝혀 어둠을 몰아내고 오랫동안 염원하던 소망을 일사천리로 성취시키는 전통 부적입니다."},
    "earth": {"type": "earth", "title": "금고수호부 (金庫安穩符)", "power": "자산 방어 · 누수 차단 · 재물 안착", "desc": "사주에 부족한 土(포용과 저장)의 단단한 대지를 마련하여 헛돈 지출을 막고 평생의 자산을 굳건하게 지켜주는 금고 수호 부적입니다."},
    "metal": {"type": "metal", "title": "재물만복부 (萬福大吉符)", "power": "재물 증식 · 금전운 대통 · 투자 대박", "desc": "사주에 부족한 金(결단과 결실)의 황금 기운을 채워 사방에서 금전과 복록이 샘솟듯 쏟아지게 하는 전통 경면주사 수제 부적입니다."},
    "water": {"type": "water", "title": "천생화합부 (萬事和合符)", "power": "인연 결속 · 애정 화합 · 인간관계 개선", "desc": "사주에 부족한 水(지혜와 융합)의 부드러운 유대감을 채워 엇갈린 인연을 묶어주고 귀인의 조력을 이끌어내는 화합 비급 부적입니다."}
}

TAROT_CARDS = [
    {"name": "0. THE FOOL (바보)", "keyword": "새로운 시작 · 순수한 열정 · 무한한 잠재력", "symbolism": "절벽 끝에 선 순수한 영혼으로 관습에 얽매이지 않는 새로운 여정의 출발을 상징합니다.", "fortune_reading": "오랫동안 머뭇거리던 일의 시작 단추를 꿰기에 최적의 날입니다. 직관을 따를 때 예상 밖의 통로가 열립니다.", "advice": "새로운 제안에 열린 마음을 가지되 발걸음은 가볍고 시선은 신중히 유지하세요.", "action_tip": "떠오르는 아이디어를 즉시 메모하고 먼저 연락을 건네보세요."},
    {"name": "I. THE MAGICIAN (마법사)", "keyword": "창조적 역량 · 완벽한 주도권 · 실력 발휘", "symbolism": "머리 위의 무한대(∞) 기호와 제단 위의 4대 원소는 모든 도구를 통제하는 지혜를 뜻합니다.", "fortune_reading": "지식과 언변, 전문 기술이 빛을 발하는 날입니다. 당당한 태도로 판을 리드하기에 최적입니다.", "advice": "미팅이나 보고에서 주도적으로 의견을 제시하고 실력을 드러내세요.", "action_tip": "중요한 대화에서 본인의 핵심 주장을 명확하게 피력하세요."},
    {"name": "II. THE HIGH PRIESTESS (여사제)", "keyword": "깊은 통찰 · 직관과 혜안 · 침묵의 지혜", "symbolism": "흑과 백의 기둥 사이에 앉아 본질적 진실과 영적인 직관을 상징합니다.", "fortune_reading": "겉으로 드러난 말보다 상대방의 숨은 의도나 상황의 이면을 꿰뚫어 보는 혜안이 극대화됩니다.", "advice": "성급하게 반응하기보다는 차분히 경청하고 심사숙고하세요.", "action_tip": "조용한 장소에서 생각을 차분히 정리하는 시간을 가지세요."},
    {"name": "III. THE EMPRESS (여황제)", "keyword": "풍요와 번영 · 따뜻한 포용 · 결실의 기쁨", "symbolism": "풍성한 곡식과 석류 장식은 모성적 사랑과 물질적·정신적 풍요로움을 상징합니다.", "fortune_reading": "그동안 공들여 준비한 일에서 만족스러운 성과와 금전적 보상이 주어지는 날입니다.", "advice": "주변 사람들에게 넉넉한 마음으로 베풀면 더 큰 행운이 돌아옵니다.", "action_tip": "맛있는 식사를 대접하거나 가까운 이에게 감사 인사를 전하세요."},
    {"name": "IV. THE EMPEROR (황제)", "keyword": "확고한 권위 · 강력한 통솔 · 안정된 기반", "symbolism": "단단한 석조 왕좌는 흔들리지 않는 통치력과 엄격한 질서, 조직의 굳건함을 뜻합니다.", "fortune_reading": "자신의 영역에서 주도권을 확립하고 책임감 있게 프로젝트를 완수하기에 좋은 날입니다.", "advice": "원칙과 약속을 철저히 지키며 리더십을 발휘하세요.", "action_tip": "흐트러진 계획을 점검하고 체계적인 규율을 세우세요."},
    {"name": "VI. THE LOVERS (연인)", "keyword": "조화로운 결합 · 진정한 공감 · 올바른 선택", "symbolism": "천사의 축복 아래 선 남녀는 영혼의 교감과 중요한 인생의 선택을 상징합니다.", "fortune_reading": "인간관계와 애정 전선에 따뜻한 훈풍이 불고 협력 파트너와의 호흡이 완벽히 맞습니다.", "advice": "계산적인 이득보다는 마음의 진정성을 바탕으로 대화하세요.", "action_tip": "소중한 사람과 티타임을 가지며 솔직한 마음을 나누세요."},
    {"name": "X. WHEEL OF FORTUNE (운명의 수레바퀴)", "keyword": "행운의 반전 · 결정적 기회 · 운명의 전환점", "symbolism": "영원히 회전하는 수레바퀴는 상승과 하강, 기회의 순간을 뜻합니다.", "fortune_reading": "정체되었던 상황이 뜻밖의 계기를 통해 긍정적인 방향으로 급물살을 타게 됩니다.", "advice": "흐름에 맞서지 말고 자연스럽게 변화를 수용하여 기회를 잡으세요.", "action_tip": "오랜 지인에게 온 연락이나 새로운 제안을 긍정적으로 검토하세요."},
    {"name": "XIX. THE SUN (태양)", "keyword": "최고의 성공 · 밝은 활력 · 승리와 영광", "symbolism": "찬란하게 빛나는 태양과 백마 탄 아이는 어둠을 몰아내는 승리와 기쁨을 상징합니다.", "fortune_reading": "모든 근심이 사라지고 목표하던 일이 시원하게 성취되는 최고의 운세입니다.", "advice": "자신감을 갖고 주저 없이 전진하여 승리의 기쁨을 누리세요.", "action_tip": "야외로 나가 밝은 햇살을 맞으며 활력을 충전하세요."}
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
    
    # 1. 일주
    d_cg_idx = (diff_days + 0) % 10
    d_jj_idx = (diff_days + 10) % 12
    d_cg = CHEONGAN_HANJA[d_cg_idx]
    d_jj = JIJI_HANJA[d_jj_idx]

    # 2. 년주
    year_offset = (req.year - 4) % 60
    y_cg_idx = year_offset % 10
    y_jj_idx = year_offset % 12
    y_cg, y_jj = CHEONGAN_HANJA[y_cg_idx], JIJI_HANJA[y_jj_idx]

    # 3. 월주
    month_adj = req.month
    if req.calendar_type == "lunar":
        month_adj = (req.month + 1)
    elif req.calendar_type == "leap":
        month_adj = (req.month + 2)

    m_jj_idx = (month_adj) % 12
    m_cg_idx = (y_cg_idx % 5 * 2 + 2 + (month_adj - 2)) % 10
    m_cg, m_jj = CHEONGAN_HANJA[m_cg_idx], JIJI_HANJA[m_jj_idx]

    # 4. 시주
    if req.is_unknown_time or req.sijin_index is None or req.sijin_index < 0:
        h_pillar, h_cg, h_jj = "時未詳", "-", "-"
    else:
        h_jj_idx = req.sijin_index
        h_cg_idx = (d_cg_idx % 5 * 2 + h_jj_idx) % 10
        h_cg, h_jj = CHEONGAN_HANJA[h_cg_idx], JIJI_HANJA[h_jj_idx]
        h_pillar = f"{h_cg}{h_jj}"

    d_animal = ANIMAL_MAP.get(d_jj, "개")

    # 5. 만 나이 연산 (2026년 기준)
    current_year = 2026
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

    # 6. 오행 가중치 점수 연산
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

    # 7. 신강/신약 판정
    day_elem = CHEONGAN_ELEMENTS[d_cg]
    support_score = scores.get(day_elem, 0)
    insoeng_map = {"wood": "water", "fire": "wood", "earth": "fire", "metal": "earth", "water": "metal"}
    support_score += scores.get(insoeng_map.get(day_elem, ""), 0)
    
    singang_status = "신약(身弱) 사주" if support_score < 45 else ("신강(身强) 사주" if support_score > 65 else "중화(中和) 사주")

    # 8. 사주 결핍 오행 및 큐레이션 매핑
    min_elem = min(elem_percentages, key=elem_percentages.get)
    curation_data = OHEANG_CURATION_MAP.get(min_elem, OHEANG_CURATION_MAP["metal"])
    user_talisman = TALISMAN_OHEANG_MAP.get(min_elem, TALISMAN_OHEANG_MAP["metal"])

    # 9. 일간별 맞춤형 당일 운세 감명
    fortune_titles = {
        "甲": "우람한 거목처럼 굳은 신념으로 판을 주도하는 대길(大吉)의 하루",
        "乙": "봄바람에 피어난 꽃처럼 유연한 매력으로 귀인을 끌어당기는 하루",
        "丙": "태양 같은 열정과 빛으로 막힌 활로를 환하게 뚫어내는 하루",
        "丁": "은은한 등불처럼 치밀한 지혜로 실속과 명예를 동시에 잡는 하루",
        "戊": "묵직한 태산처럼 흔들리지 않는 신뢰로 큰 계약을 성사시키는 하루",
        "己": "비옥한 전답처럼 주변 사람들을 품고 풍성한 결실을 거두는 하루",
        "庚": "예리한 보검처럼 단호한 결단력으로 난제를 단번에 해결하는 하루",
        "辛": "빛나는 보석처럼 정교한 전문 기술과 안목으로 두각을 나타내는 하루",
        "壬": "넓은 바다처럼 유려한 지혜와 임기응변으로 난관을 돌파하는 하루",
        "癸": "생명수 같은 맑은 직관력으로 핵심 기회를 정확히 포착하는 하루"
    }
    daily_title = fortune_titles.get(d_cg, "새로운 기운이 서서히 솟아나는 도약의 하루")
    daily_score = 86 + (d_cg_idx * 3 + datetime.date.today().day) % 13

    # 변수명 수정: 문법 오류 원인이었던 3_stage_advice -> three_stage_advice로 완전 변경!
    three_stage_advice = (
        f"☀️ 오전 (06:00~12:00): 부족한 {min_elem.upper()} 기운을 불어넣어 줄 반가운 소식이나 귀인의 연락이 닿아 오랫동안 추진하던 일에 탄력이 붙습니다.\n\n"
        f"🌤️ 오후 (12:00~18:00): 본원({d_cg})의 결단력과 추진력이 극대화되는 황금 타임입니다. 중요한 협상이나 문서 계약을 적극 추진하세요.\n\n"
        f"🌙 저녁·밤 (18:00~24:00): 오늘 하루의 성과를 차분히 정리하고, 미온수를 마시며 내일의 도약을 준비하는 안정된 결실의 시간입니다."
    )

    user_mbti = DAY_MBTI_MAP.get(d_cg, {"mbti": "대담한 통솔자 (ENTJ형)", "desc": "강한 추진력과 당당한 리더십으로 조직을 이끄는 개척자 사주"})
    user_animal_icon = ANIMAL_ICONS.get(d_animal, "🐶")

    return {
        "user_name": req.name,
        "current_age": current_age,
        "singang_status": singang_status,
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
            "score": daily_score,
            "title": daily_title,
            "advice": three_stage_advice,
            "lucky_color": curation_data["color"],
            "lucky_number": curation_data["number"],
            "lucky_direction": curation_data["direction"],
            "fashion_style": curation_data["style"],
            "recommended_menu": curation_data["menu"],
            "mindset": curation_data["mindset"],
            "action": curation_data["action"],
            "talisman": user_talisman
        }
    }

@app.get("/api/daily-tarot")
def get_daily_tarot(slot: int = 1, rand_seed: Optional[str] = None):
    random_idx = random.randint(0, len(TAROT_CARDS) - 1)
    return TAROT_CARDS[random_idx]

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
                <h4 style="font-size: 13px; font-weight: 700; color: #0F172A; border-bottom: 1px solid #E2E8F0; padding-bottom: 8px; margin-bottom: 10px;">
                    🌐 1. {user_name}님의 평생 생애 주기별 대운맥(大運脈) 흐름
                </h4>
                <div style="display: flex; flex-direction: column; gap: 10px; font-size: 11px;">
                    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 10px;">
                        <p style="font-weight: 700; color: #0F172A; margin-bottom: 4px;">🌱 [유년기 (0세 ~ 19세) : 기틀 형성 및 학업기]</p>
                        <p style="color: #475569; line-height: 1.65;">타고난 영민함과 지적 호기심으로 내면의 가치관과 도덕적 기틀을 확립하던 시기입니다.</p>
                    </div>
                    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 10px;">
                        <p style="font-weight: 700; color: #0F172A; margin-bottom: 4px;">🌿 [청년기 (20세 ~ 39세) : 도약 탐색 및 역량 구축기]</p>
                        <p style="color: #475569; line-height: 1.65;">사회에 진출하여 실전 경험과 전문성을 갈고닦으며 자신의 진가를 입증해 나간 시기입니다.</p>
                    </div>
                    <div style="background: #FEF3C7; border: 1.5px solid #FCD34D; border-radius: 12px; padding: 10px;">
                        <p style="font-weight: 700; color: #78350F; margin-bottom: 4px;">🔥 [중장년기 (*현재 일주 기반 / 40세 ~ 59세) : 황금 자산 결실기]</p>
                        <p style="color: #92400E; line-height: 1.65;"><strong>{user_name}님 인생 일대에서 가장 강력한 천운의 파도가 솟구치는 최고 하이라이트 구간입니다.</strong> 사회적 주도권을 잡고 자산과 명예의 결실이 폭발적으로 확장됩니다.</p>
                    </div>
                    <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 10px;">
                        <p style="font-weight: 700; color: #0F172A; margin-bottom: 4px;">🍎 [말년기 (60세 이후) : 태평성대 및 명예 완성기]</p>
                        <p style="color: #475569; line-height: 1.65;">평생 축적한 부와 지혜를 토대로 안락하고 평온한 노후를 누리며 가문 번영을 완성합니다.</p>
                    </div>
                </div>
            </div>

            <div style="background: #FFFBEB; border: 1.5px solid #FDE68A; border-radius: 16px; padding: 14px;">
                <h4 style="font-size: 13px; font-weight: 700; color: #78350F; border-bottom: 1px solid #FCD34D; padding-bottom: 8px; margin-bottom: 10px;">
                    📈 2. {user_name}님의 현재 10년 대운 정밀 감명 ({start_age}세 ~ {end_age}세)
                </h4>
                <div style="margin-bottom: 12px; line-height: 1.65;">
                    <p style="font-weight: 700; color: #92400E; margin-bottom: 3px;">[대운의 본질과 주도권]</p>
                    <p style="color: #78350F;">본원에 귀인과 재성의 기운이 결합하는 시기로, 본인이 직접 판을 설계하고 이끌어가는 독보적인 리더십이 발현되는 10년의 절정기입니다.</p>
                </div>
                <div style="display: flex; flex-direction: column; gap: 8px; font-size: 11px; background: rgba(254,243,199,0.7); border-radius: 12px; padding: 12px;">
                    <p style="font-weight: 700; color: #78350F; font-size: 11.5px; margin-bottom: 2px;">[세운별 핵심 분기점 ({start_age}세 ~ {end_age}세)]</p>
                    <p style="color: #475569; line-height: 1.55;">• <strong>{start_age}세 ~ {start_age+2}세 (도입기):</strong> 고정 비용 정돈 및 안전 자산 중심 종잣돈 재배치.</p>
                    <p style="color: #B45309; font-weight: 700; line-height: 1.55; background: #FEF3C7; padding: 4px 6px; border-radius: 6px;">• <strong>{start_age+3}세 ~ {start_age+6}세 (정점기 / ★현재 {age}세 위치):</strong> 귀인의 결정적 조력과 함께 직위·자산이 수직 상승하는 황금 전환점.</p>
                    <p style="color: #475569; line-height: 1.55;">• <strong>{start_age+7}세 ~ {end_age}세 (결실기):</strong> 성과를 안정적 시스템 수익으로 확정 짓고 차기 대운으로의 연착륙.</p>
                </div>

                <div style="margin-top: 10px; background: #FFFFFF; border: 1px solid #FCD34D; border-radius: 10px; padding: 10px;">
                    <p style="font-weight: 700; color: #78350F; font-size: 11px; margin-bottom: 3px;">🔥 [10년 대운 맞춤 개운(開運) 실천 팁]</p>
                    <p style="color: #92400E; font-size: 10.5px; line-height: 1.5;">
                        현재 대운은 귀인의 도우심이 강한 시기이므로, 혼자 모든 짐을 짊어지려 하지 말고 주변 전문가나 협력 파트너에게 적극적으로 조언을 구하고 문서를 명확히 작성할 때 재물과 명예가 더욱 공고해집니다.
                    </p>
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
        "wealth": f"💰 {user_name}님의 평생 재물운 심층 리포트",
        "love": f"💖 {user_name}님의 평생 애정운 ({sub_opt} 맞춤)",
        "business": f"🏢 {user_name}님의 사업·직업운 ({sub_opt} 맞춤)",
        "health": f"🌿 {user_name}님의 평생 건강운 리포트"
    }

    contents = {
        "wealth": f"""
        <div style="display: flex; flex-direction: column; gap: 14px; font-size: 12px; color: #334155; line-height: 1.65; text-align: left;">
            <div style="background: #FFFBEB; border: 1.5px solid #FCD34D; border-radius: 16px; padding: 14px;">
                <span style="font-size: 10px; background: #D97706; color: white; padding: 2px 6px; border-radius: 6px; font-weight: 700;">원국 정밀 감명</span>
                <h4 style="font-size: 13px; font-weight: 700; color: #78350F; margin: 4px 0 6px;">[평생 재물운] '암장(暗藏) 금고형' 자산 축적 원국</h4>
                <p style="color: #92400E; font-size: 11px; line-height: 1.6;">
                    {user_name}님의 사주는 겉으로 드러난 화려함보다 실속 있게 현금과 실물 자산을 차곡차곡 축적하는 전형적인 '황금 금고형' 구조입니다. 지장간 속에 알짜배기 재성이 은밀하게 뿌리를 내리고 있어 틈새 기회를 포착하여 자산을 불리는 능력이 탁월합니다.
                </p>
            </div>
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 14px; padding: 12px;">
                <p style="font-weight: 700; color: #0F172A; font-size: 12px; margin-bottom: 4px;">📊 1. 생애 자산 증식 3단계 로드맵</p>
                <p style="font-size: 11px; color: #475569; line-height: 1.6;">• 초년~30대: 종잣돈 축적 ➔ 40대~50대: 자산 퀀텀점프 황금기 ➔ 60대 이후: 임대/배당 태평성대</p>
            </div>
        </div>
        """,
        "love": f"""
        <div style="display: flex; flex-direction: column; gap: 14px; font-size: 12px; color: #334155; line-height: 1.65; text-align: left;">
            <div style="background: #FFF1F2; border: 1.5px solid #FECDD3; border-radius: 16px; padding: 14px;">
                <span style="font-size: 10px; background: #E11D48; color: white; padding: 2px 6px; border-radius: 6px; font-weight: 700;">상태 맞춤: {sub_opt}</span>
                <h4 style="font-size: 13px; font-weight: 700; color: #881337; margin: 4px 0 6px;">[평생 애정운] 깊은 신뢰와 상호 존중의 천생연분</h4>
                <p style="color: #9F1239; font-size: 11px; line-height: 1.6;">
                    {user_name}님의 애정 원국은 한 번 맺은 신뢰를 평생 지켜나가는 따뜻한 포용력의 소유자입니다. 상대방에게 일방적으로 맞추기보다 생각을 솔직히 공유할 때 유대감이 더욱 깊어집니다.
                </p>
            </div>
        </div>
        """,
        "business": f"""
        <div style="display: flex; flex-direction: column; gap: 14px; font-size: 12px; color: #334155; line-height: 1.65; text-align: left;">
            <div style="background: #EFF6FF; border: 1.5px solid #BFDBFE; border-radius: 16px; padding: 14px;">
                <span style="font-size: 10px; background: #2563EB; color: white; padding: 2px 6px; border-radius: 6px; font-weight: 700;">직업군 맞춤: {sub_opt}</span>
                <h4 style="font-size: 13px; font-weight: 700; color: #1E3A8A; margin: 4px 0 6px;">[사업·직업운] 치밀한 기획력과 결단력의 수장</h4>
                <p style="color: #1E40AF; font-size: 11px; line-height: 1.6;">
                    {user_name}님의 사주는 복잡한 문제의 핵심을 단번에 꿰뚫고 시스템을 정돈하는 전략가 기질을 타고났습니다. 현재 직업군({sub_opt})에서 대체 불가능한 리더로 두각을 나타냅니다.
                </p>
            </div>
        </div>
        """,
        "health": f"""
        <div style="display: flex; flex-direction: column; gap: 14px; font-size: 12px; color: #334155; line-height: 1.65; text-align: left;">
            <div style="background: #ECFDF5; border: 1.5px solid #A7F3D0; border-radius: 16px; padding: 14px;">
                <span style="font-size: 10px; background: #059669; color: white; padding: 2px 6px; border-radius: 6px; font-weight: 700;">오행 체질 정밀 분석</span>
                <h4 style="font-size: 13px; font-weight: 700; color: #065F46; margin: 4px 0 6px;">[평생 건강운] 수승화강(水昇火降) 활력 관리</h4>
                <p style="color: #047857; font-size: 11px; line-height: 1.6;">
                    {user_name}님의 오행 체질은 강인한 생명력을 갖추고 있으나 두한족열(머리는 시원하게 발은 따뜻하게)의 수칙을 유지해야 건강이 완성됩니다.
                </p>
            </div>
        </div>
        """
    }
    
    return {
        "title": titles.get(theme, "심층 리포트"),
        "content": contents.get(theme, "<p>리포트 내용을 불러오는 중입니다.</p>")
    }
