# -*- coding: utf-8 -*-
from datetime import datetime, date

CHEONGAN = ["갑", "을", "병", "정", "무", "기", "경", "신", "임", "계"]
JIJI = ["자", "축", "인", "묘", "진", "사", "오", "미", "신", "유", "술", "해"]

OHENG_MAP = {
    "갑": "목", "을": "목", "인": "목", "묘": "목",
    "병": "화", "정": "화", "사": "화", "오": "화",
    "무": "토", "기": "토", "진": "토", "술": "토", "축": "토", "미": "토",
    "경": "금", "신": "금", "신(申)": "금", "유": "금",
    "임": "수", "계": "수", "해": "수", "자": "수"
}

CHARACTER_TRAITS = {
    "갑": {
        "title": "당당하고 곧은 거목 (뿌리 깊은 리더형)",
        "icon": "🌲",
        "mbti": "ENTJ",
        "trait": "추진력과 리더십이 뛰어나며 명예와 신의를 중시합니다.",
        "element_desc": "양목(陽木)",
        "traits": ["추진력", "리더십", "책임감", "승부욕"],
        "work_style": "주도적으로 프로젝트를 이끌며 기틀을 세울 때 성과를 냅니다.",
        "romance_style": "신뢰와 편안함을 바탕으로 듬직하게 챙겨주는 스타일.",
        "best_match": "己토 (안정적인 조력자)",
        "worst_match": "庚금 (직설적인 통제자)"
    },
    "을": {
        "title": "유연하고 강인한 담쟁이 (외유내강 적응형)",
        "icon": "🌿",
        "mbti": "ENFP",
        "trait": "친화력과 적응력이 뛰어나며 어떤 환경에서도 싹을 틔웁니다.",
        "element_desc": "음목(陰木)",
        "traits": ["유연성", "친화력", "생명력", "재치"],
        "work_style": "네트워킹과 기획 역량을 바탕으로 관계 속에서 성장합니다.",
        "romance_style": "섬세하게 공감해주고 다정하게 챙겨주는 따뜻한 스타일.",
        "best_match": "庚금 (강인한 수호자)",
        "worst_match": "辛금 (날카로운 비판자)"
    },
    "병": {
        "title": "세상을 밝히는 태양 (열정적인 메이커)",
        "icon": "☀️",
        "mbti": "ENFJ",
        "trait": "솔직 담백하고 에너지가 넘치며 주변에 긍정적 영향력을 줍니다.",
        "element_desc": "양화(陽火)",
        "traits": ["열정", "솔직함", "표현력", "자신감"],
        "work_style": "동기부여와 팀의 분위기를 이끌며 큰 무대에서 활약합니다.",
        "romance_style": "감정을 숨김없이 솔직하게 표현하며 헌신적인 스타일.",
        "best_match": "辛금 (지혜로운 파트너)",
        "worst_match": "壬수 (통제하기 힘든 변수)"
    },
    "정": {
        "title": "어둠을 밝히는 등불 (사려 깊은 장인)",
        "icon": "🕯️",
        "mbti": "INFJ",
        "trait": "따뜻하고 섬세하며 한 분야에 대한 깊은 집중력을 가집니다.",
        "element_desc": "음화(陰火)",
        "traits": ["섬세함", "집중력", "배려심", "전문성"],
        "work_style": "디테일이 중요한 전문 분야나 정밀한 연구·개발에 적합합니다.",
        "romance_style": "은은하고 깊은 정으로 오랫동안 마음을 다하는 스타일.",
        "best_match": "壬수 (품이 넓은 지원자)",
        "worst_match": "癸수 (감정 기복 유발자)"
    },
    "무": {
        "title": "흔들림 없는 큰 산 (듬직한 수호자)",
        "icon": "⛰️",
        "mbti": "ISTJ",
        "trait": "포용력이 크고 신뢰감이 깊으며 중심을 단단히 잡아줍니다.",
        "element_desc": "양토(陽土)",
        "traits": ["신뢰감", "포용력", "안정성", "뚝심"],
        "work_style": "장기적인 프로젝트를 묵묵히 완수하며 리스크를 관리합니다.",
        "romance_style": "말보다는 행동으로 보여주며 변함없는 버팀목이 되어주는 스타일.",
        "best_match": "癸수 (영감을 주는 동반자)",
        "worst_match": "甲목 (간섭이 많은 성향)"
    },
    "기": {
        "title": "생명을 키우는 옥토 (현실적 전략가)",
        "icon": "🌾",
        "mbti": "ISFJ",
        "trait": "현실 감각과 포용력이 뛰어나며 실리를 잘 챙깁니다.",
        "element_desc": "음토(陰土)",
        "traits": ["현실감각", "성실함", "적응력", "실리추구"],
        "work_style": "실무와 자원 관리에 능하며 안정적인 결실을 만듭니다.",
        "romance_style": "소소한 일상을 함께 나누며 실질적인 챙김을 주는 스타일.",
        "best_match": "甲목 (방향을 잡아주는 멘토)",
        "worst_match": "乙목 (예측 불가능한 성향)"
    },
    "경": {
        "title": "단단한 바위와 원석 (결단력 있는 개척자)",
        "icon": "🪙",
        "mbti": "ESTJ",
        "trait": "의리와 결단력이 돋보이며 목표를 향해 과감히 전진합니다.",
        "element_desc": "양금(陽金)",
        "traits": ["결단력", "추진력", "의리", "원칙주의"],
        "work_style": "신속한 판단과 단호한 실행력으로 위기 상황을 돌파합니다.",
        "romance_style": "확실한 감정 표현과 든든한 보호 본능을 보여주는 스타일.",
        "best_match": "乙목 (부드러운 조율자)",
        "worst_match": "丙화 (충돌이 잦은 성향)"
    },
    "신": {
        "title": "정교하게 세공된 보석 (감각적인 완벽주의자)",
        "icon": "💎",
        "mbti": "INTJ",
        "trait": "예리한 통찰력과 세련된 감각을 갖춘 완벽주의자입니다.",
        "element_desc": "음금(陰金)",
        "traits": ["통찰력", "정교함", "자존감", "미적감각"],
        "work_style": "높은 기준과 전문 지식을 요구하는 고난도 영역에 강합니다.",
        "romance_style": "지적 대화와 서로의 프라이버시를 존중하는 세련된 연애를 선호.",
        "best_match": "丙화 (빛을 밝혀주는 존재)",
        "worst_match": "丁화 (간섭과 마찰)"
    },
    "임": {
        "title": "넓고 깊은 바다 (지혜로운 전략가)",
        "icon": "🌊",
        "mbti": "INTP",
        "trait": "지혜롭고 유연하며 스케일이 큰 안목을 가지고 있습니다.",
        "element_desc": "양수(陽水)",
        "traits": ["지혜", "통찰력", "유연성", "큰그릇"],
        "work_style": "거시적인 전략과 기획, 흐름을 읽는 사업 분야에 능합니다.",
        "romance_style": "넓은 마음으로 상대를 수용하고 지적 공감대를 나누는 스타일.",
        "best_match": "丁화 (온기를 주는 파트너)",
        "worst_match": "戊토 (자유를 제한하는 성향)"
    },
    "계": {
        "title": "만물을 적시는 단비 (직관적인 힐러)",
        "icon": "💧",
        "mbti": "INFP",
        "trait": "섬세한 감수성과 뛰어난 직관으로 사람의 마음을 읽습니다.",
        "element_desc": "음수(陰水)",
        "traits": ["감수성", "직관력", "공감능력", "친화력"],
        "work_style": "창의적인 아이디어와 정서적 교감이 필요한 분야에 탁월합니다.",
        "romance_style": "깊은 감정적 교감과 배려를 바탕으로 진심을 다하는 스타일.",
        "best_match": "戊토 (든든한 안식처)",
        "worst_match": "己토 (방향성 상실 유발자)"
    }
}

JIJANGGAN_DATA = {
    "자": {"display": "임(10) / 계(20)", "main": "계"},
    "축": {"display": "계(9) / 신(3) / 기(18)", "main": "기"},
    "인": {"display": "무(7) / 병(7) / 갑(16)", "main": "갑"},
    "묘": {"display": "갑(10) / 을(20)", "main": "을"},
    "진": {"display": "을(9) / 계(3) / 무(18)", "main": "무"},
    "사": {"display": "무(7) / 경(7) / 병(16)", "main": "병"},
    "오": {"display": "병(10) / 기(9) / 정(11)", "main": "정"},
    "미": {"display": "정(9) / 을(3) / 기(18)", "main": "기"},
    "신": {"display": "무(7) / 임(7) / 경(16)", "main": "경"},
    "유": {"display": "경(10) / 신(20)", "main": "신"},
    "술": {"display": "신(9) / 정(3) / 무(18)", "main": "무"},
    "해": {"display": "무(7) / 갑(7) / 임(16)", "main": "임"}
}

def calculate_saju_pillars(year: int, month: int, day: int, sijin_index: int = None):
    # 1. 년주 (입춘 기준 간략 보정: 2월 4일 이전이면 전년도 간지)
    effective_year = year if not (month == 1 or (month == 2 and day < 4)) else year - 1
    y_gan = CHEONGAN[(effective_year - 4) % 10]
    y_ji = JIJI[(effective_year - 4) % 12]
    year_pillar = f"{y_gan}{y_ji}"

    # 2. 월주 (24절기 절입 기준 월지 계산)
    # 각 월별 절입일 대략치: 1월(소한 1/6), 2월(입춘 2/4), 3월(경칩 3/6), 4월(청명 4/5), 5월(입하 5/6), 6월(망종 6/6),
    # 7월(소서 7/7), 8월(입추 8/8), 9월(백로 9/8), 10월(한로 10/8), 11월(입동 11/7), 12월(대설 12/7)
    cutoff_days = [0, 6, 4, 6, 5, 6, 6, 7, 8, 8, 8, 7, 7]
    if day < cutoff_days[month]:
        solar_month_idx = (month + 9) % 12  # 이전 절기 월
    else:
        solar_month_idx = (month + 10) % 12 # 인월(寅:2)부터 시작하는 절기 월 인덱스

    m_ji = JIJI[solar_month_idx]
    
    # 년간에 따른 월간 시작음
    y_gan_idx = CHEONGAN.index(y_gan)
    m_gan_base = {0: 2, 5: 2, 1: 4, 6: 4, 2: 6, 7: 6, 3: 8, 8: 8, 4: 0, 9: 0}[y_gan_idx]
    # 인월(index 2) 기준 몇 번째 달인지 계산
    month_offset = (solar_month_idx - 2) % 12
    m_gan = CHEONGAN[(m_gan_base + month_offset) % 10]
    month_pillar = f"{m_gan}{m_ji}"

    # 3. 일주 (1900-01-01 = 갑술(甲戌)일 정확한 일진 공식)
    base_date = date(1900, 1, 1)
    target_date = date(year, month, day)
    diff = (target_date - base_date).days
    
    # 1900년 1월 1일은 갑(0) 술(10)일
    d_gan = CHEONGAN[(diff + 0) % 10]
    d_ji = JIJI[(diff + 10) % 12]
    day_pillar = f"{d_gan}{d_ji}"

    # 4. 시주
    if sijin_index is not None and 0 <= sijin_index < 12:
        h_ji = JIJI[sijin_index]
        d_gan_idx = CHEONGAN.index(d_gan)
        d_gan_base = {0: 0, 5: 0, 1: 2, 6: 2, 2: 4, 7: 4, 3: 6, 8: 6, 4: 8, 9: 8}[d_gan_idx]
        h_gan = CHEONGAN[(d_gan_base + sijin_index) % 10]
        hour_pillar = f"{h_gan}{h_ji}"
    else:
        hour_pillar = None

    # 오행 매핑
    elements = [
        OHENG_MAP.get(y_gan, "토"), OHENG_MAP.get(y_ji, "화"),
        OHENG_MAP.get(m_gan, "목"), OHENG_MAP.get(m_ji, "목"),
        OHENG_MAP.get(d_gan, "목"), OHENG_MAP.get(d_ji, "토")
    ]
    if hour_pillar:
        elements.extend([OHENG_MAP.get(hour_pillar[0], "토"), OHENG_MAP.get(hour_pillar[1], "화")])

    total_count = len(elements)
    oheng_ratio = {
        "목": round((elements.count("목") / total_count) * 100),
        "화": round((elements.count("화") / total_count) * 100),
        "토": round((elements.count("토") / total_count) * 100),
        "금": round((elements.count("금") / total_count) * 100),
        "수": round((elements.count("수") / total_count) * 100),
    }

    pillars_data = {
        "year": year_pillar,
        "month": month_pillar,
        "day": day_pillar,
        "hour": hour_pillar
    }

    character = CHARACTER_TRAITS.get(d_gan, CHARACTER_TRAITS["갑"])
    character["stem_name"] = f"{d_gan}목" if d_gan in ["갑", "을"] else (
        f"{d_gan}화" if d_gan in ["병", "정"] else (
            f"{d_gan}토" if d_gan in ["무", "기"] else (
                f"{d_gan}금" if d_gan in ["경", "신"] else f"{d_gan}수"
            )
        )
    )

    character["shinsal"] = [
        {"name": "천을귀인(天乙貴人)", "tag": "최고의 길신", "desc": "위기 순간마다 예상치 못한 귀인의 조력으로 돌파구를 찾습니다."},
        {"name": "문창귀인(文昌貴人)", "tag": "지혜·문서운", "desc": "명석한 판단력과 뛰어난 문서 기획 능력으로 자산을 축적합니다."},
        {"name": "역마살(驛馬殺)", "tag": "활동·무대전환", "desc": "활동 무대를 넓게 쓸수록 기회와 재물이 크게 팽창합니다."},
        {"name": "화개살(華蓋殺)", "tag": "전문성·예술", "desc": "독창적인 통찰력과 한 분야의 독점적 전문성을 완성합니다."}
    ]

    jijanggan = {
        "pillars": {
            "year": {"display": JIJANGGAN_DATA.get(y_ji, {}).get("display", "-")},
            "month": {"display": JIJANGGAN_DATA.get(m_ji, {}).get("display", "-")},
            "day": {"display": JIJANGGAN_DATA.get(d_ji, {}).get("display", "-")},
            "hour": {"display": JIJANGGAN_DATA.get(hour_pillar[1], {}).get("display", "-")} if hour_pillar else None
        }
    }

    life_chart = {
        "labels": ["10대", "20대", "30대", "40대", "50대", "60대", "70대"],
        "scores": [68, 76, 85, 96, 91, 88, 82]
    }

    return {
        "pillars": pillars_data,
        "oheng_ratio": oheng_ratio,
        "character": character,
        "jijanggan": jijanggan,
        "life_chart": life_chart,
        "day_stem": d_gan
    }
