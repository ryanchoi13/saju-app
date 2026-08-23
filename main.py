from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import os
import random
from saju_engine import calculate_saju, CHEONGAN, JIJI, OHENG_MAP

app = FastAPI()

# ============================================================
# [정통 명리학 12지지 지장간 매핑 테이블]
# ============================================================
JIJANGGAN_MAP = {
    "자": {"chars": ["임", "계"], "display": "壬 · 癸", "hidden_power": "깊은 지혜와 치밀한 전략, 은밀한 자산 증식력"},
    "축": {"chars": ["계", "신", "기"], "display": "癸 · 辛 · 己", "hidden_power": "비상금 창고(금고)와 끈질긴 인내력, 축적의 힘"},
    "인": {"chars": ["무", "병", "갑"], "display": "戊 · 丙 · 甲", "hidden_power": "새로운 판을 여는 기획력과 숨겨진 사업가적 야망"},
    "묘": {"chars": ["갑", "을"], "display": "甲 · 乙", "hidden_power": "생명력 넘치는 적응력과 탁월한 대인관계 공감술"},
    "진": {"chars": ["을", "계", "무"], "display": "乙 · 癸 · 戊", "hidden_power": "다재다능한 팔방미인 기질과 숨은 문서(부동산) 복"},
    "사": {"chars": ["무", "경", "병"], "display": "戊 · 庚 · 丙", "hidden_power": "순간 포착력과 통찰력, 위기를 기회로 바꾸는 순발력"},
    "오": {"chars": ["병", "기", "정"], "display": "丙 · 己 · 丁", "hidden_power": "강렬한 카리스마와 사람을 끄는 은밀한 도화/스타성"},
    "미": {"chars": ["정", "을", "기"], "display": "丁 · 乙 · 己", "hidden_power": "따뜻한 포용력과 실속을 챙기는 자수성가형 생활력"},
    "신": {"chars": ["무", "임", "경"], "display": "戊 · 壬 · 庚", "hidden_power": "결단력과 글로벌 활동력, 다재다능한 기술적 감각"},
    "유": {"chars": ["경", "신"], "display": "庚 · 辛", "hidden_power": "예리한 심미안과 오차 없는 정확성, 장인정신"},
    "술": {"chars": ["신", "정", "무"], "display": "辛 · 丁 · 戊", "hidden_power": "신의와 의리, 전문 자격증과 문서로 지키는 자산 복"},
    "해": {"chars": ["무", "갑", "임"], "display": "戊 · 甲 · 壬", "hidden_power": "대범한 스케일과 해외/원거리 개척력, 무한한 잠재력"}
}

def analyze_jijanggan_profile(pillars: dict, user_day_gan: str):
    result = {}
    all_hidden_chars = []
    
    for position in ["year", "month", "day", "hour"]:
        pillar_val = pillars.get(position)
        if pillar_val and len(pillar_val) >= 2:
            ji_char = pillar_val[1]
            jg_info = JIJANGGAN_MAP.get(ji_char, {"chars": ["갑"], "display": "-", "hidden_power": "잠재력 발휘"})
            result[position] = {
                "ji": ji_char,
                "display": jg_info["display"],
                "power": jg_info["hidden_power"]
            }
            all_hidden_chars.extend(jg_info["chars"])
        else:
            result[position] = {"ji": "-", "display": "-", "power": "-"}

    hidden_summary = "겉으로 보이는 기운 뒤 내면에는 지장간에 숨겨진 복(재물/지혜/결단력)이 깔려 있어, 위기 순간마다 강력한 비상 동력이 발동합니다."
    if "신" in all_hidden_chars or "경" in all_hidden_chars:
        hidden_summary = "겉으로 보이는 이미지 뒤 내면에는 단단한 결단력과 실속 자산을 지켜내는 암장된 재물복이 깔려 있습니다."
    elif "임" in all_hidden_chars or "계" in all_hidden_chars:
        hidden_summary = "겉으로 드러난 행동 뒤 내면에는 깊은 지혜와 통찰력이 깔려 있어, 판세를 정확히 읽고 성과를 불려 나갑니다."
    elif "병" in all_hidden_chars or "정" in all_hidden_chars:
        hidden_summary = "겉으로는 차분해 보여도 내면에는 꺼지지 않는 열정이 깔려 있어, 한 번 마음먹은 목표는 끝내 이뤄내는 뒷심이 탁월합니다."

    return {
        "pillars": result,
        "summary": hidden_summary,
        "core_hidden_power": result["day"]["power"]
    }

ZAMIDUSU_STARS = {
    "갑": {"wealth": ("무곡(武曲)성", "재물 통로가 단단하고 자수성가로 목돈을 축적하는 강인한 금고성"), "career": ("태양(太陽)성", "공공성 높은 프로젝트나 대외 영향력을 펼쳐 이름을 떨치는 명예성"), "love": ("천부(天府)성", "마음이 넓고 가정을 든든하게 받쳐주는 포용력 있는 배우자 인연"), "health": ("천량(天梁)성", "위기 시 병을 극복하는 재생력이 뛰어나나 간/신경성 피로 주의")},
    "을": {"wealth": ("천기(天機)성", "지략과 기획력으로 틈새 시장의 부를 포착하는 스마트형 재물성"), "career": ("천동(天同)성", "친화력과 부드러운 협상술로 성과를 거두는 웰빙 커리어성"), "love": ("태음(太陰)성", "섬세하고 다정다감하며 정서적 교감이 깊은 쉼터형 배우자"), "health": ("거문(巨門)성", "스트레스가 위장/호흡기로 이어지기 쉬워 멘탈 힐링 필수")},
    "병": {"wealth": ("염정(廉貞)성", "전문 기술과 독보적 브랜딩으로 큰 파이를 거두는 개척형 재물성"), "career": ("무곡(武曲)성", "결단력과 총괄 지휘력으로 판을 주도하는 리더십 관록성"), "love": ("파군(破軍)성", "열정적이고 솔직하며 서로의 도전을 응원하는 파트너"), "health": ("탐랑(貪狼)성", "심혈관계 순환과 간 피로 관리가 활력의 핵심")},
    "정": {"wealth": ("태음(太陰)성", "부동산 및 은밀한 문서 자산으로 자산을 안전하게 불리는 정재성"), "career": ("천부(天府)성", "안정된 조직 기반과 시스템 운영에서 최고 역량을 발휘하는 관록성"), "love": ("천상(天相)성", "예의 바르고 신의가 두터워 사회적 품격을 높여주는 귀인 배우자"), "health": ("태양(太陽)성", "안구 피로와 혈압 변동을 주의하고 규칙적 유산소 운동 권장")},
    "무": {"wealth": ("자미(紫微)성", "제왕의 기운으로 대규모 자산을 관할하고 품격을 지키는 큰 재물성"), "career": ("칠살(七殺)성", "강한 카리스마와 독자적 결단으로 성취를 쟁취하는 돌파형 관록성"), "love": ("무곡(武曲)성", "과묵하지만 실질적 경제력과 생활력이 든든한 배우자"), "health": ("천기(天機)성", "소화기 비위 밸런스와 관절 유연성 확보 필수")},
    "기": {"wealth": ("천부(天府)성", "헛돈을 쓰지 않고 차곡차곡 모아 안전 자산으로 지키는 금고형 재물성"), "career": ("천량(天梁)성", "전문 멘토, 자격증, 관리자로서 신뢰와 존경을 받는 관록성"), "love": ("천동(天同)성", "온화하고 편안하며 일상의 소소한 행복을 함께하는 파트너"), "health": ("염정(廉貞)성", "혈액 순환과 피부 면역 관리에 집중할 때 건강 대길")},
    "경": {"wealth": ("칠살(七殺)성", "승부사 기질과 과감한 투자 감각으로 자산 퀀텀 점프를 노리는 편재성"), "career": ("자미(紫微)성", "조직의 우두머리나 대표로서 독보적 존재감을 발휘하는 명예성"), "love": ("태양(太陽)성", "대외적으로 당당하고 나를 자랑스럽게 여겨주는 배우자"), "health": ("파군(破軍)성", "폐/기관지 및 대장 건강을 챙기고 충분한 수분 섭취 권장")},
    "신": {"wealth": ("파군(破軍)성", "낡은 판을 깨고 혁신적인 아이템으로 새로운 재물맥을 뚫는 창조형 재물성"), "career": ("염정(廉貞)성", "정밀한 기술 감각과 예술적 심미안으로 두각을 나타내는 관록성"), "love": ("천부(天府)성", "내실이 단단하고 꼼꼼하게 살림을 지켜주는 든든한 동반자"), "health": ("천량(天梁)성", "척추/골격계 바른 자세 유지와 스트레칭 루틴화 필요")},
    "임": {"wealth": ("탐랑(貪狼)성", "글로벌 유통과 다방면의 재능으로 유동 자금을 끌어당기는 확장형 재물성"), "career": ("거문(巨門)성", "말과 글, 지식 콘텐츠 및 브랜딩으로 설득력을 극대화하는 관록성"), "love": ("천기(天機)성", "지적 대화가 잘 통하고 센스 넘치는 영리한 배우자"), "health": ("태음(太陰)성", "신장/방광 비뇨기 계통 순환과 숙면 관리 필수")},
    "계": {"wealth": ("거문(巨門)성", "연구 분석, 전문 자문, 깊은 통찰력으로 마르지 않는 샘물을 만드는 재물성"), "career": ("태음(太陰)성", "섬세한 기획과 내실 있는 관리력으로 인정받는 안정된 관록성"), "love": ("천상(天相)성", "성실하고 다정하며 언제나 내 편이 되어주는 따뜻한 배우자"), "health": ("무곡(武曲)성", "하체 보온과 기혈 순환에 좋은 온욕 습관 권장")}
}

@app.get("/")
def home():
    file_path = os.path.join(os.path.dirname(__file__), "index.html")
    return FileResponse(file_path)

@app.get("/manifest.json")
def get_manifest():
    file_path = os.path.join(os.path.dirname(__file__), "manifest.json")
    return FileResponse(file_path, media_type="application/json")

@app.get("/sw.js")
def get_sw():
    file_path = os.path.join(os.path.dirname(__file__), "sw.js")
    return FileResponse(file_path, media_type="application/javascript")

class SajuRequest(BaseModel):
    name: str
    year: int
    month: int
    day: int
    sijin_index: Optional[int] = None
    is_unknown_time: bool = False

class LoveReportRequest(BaseModel):
    user_name: str
    user_year: int
    user_month: int
    user_day: int
    user_sijin: Optional[int] = None
    love_status: str

class WealthReportRequest(BaseModel):
    user_name: str
    user_year: int
    user_month: int
    user_day: int
    user_sijin: Optional[int] = None
    career_status: str

class BusinessRequest(BaseModel):
    user_name: str
    user_year: int
    user_month: int
    user_day: int
    user_sijin: Optional[int] = None
    career_status: str

class HealthRequest(BaseModel):
    user_name: str
    user_year: int
    user_month: int
    user_day: int
    user_sijin: Optional[int] = None

class GunghapRequest(BaseModel):
    user_year: int
    user_month: int
    user_day: int
    user_sijin: Optional[int] = None
    target_name: str
    target_year: int
    target_month: int
    target_day: int
    target_sijin: Optional[int] = None

class HeartRequest(BaseModel):
    user_year: int
    user_month: int
    user_day: int
    target_name: str
    target_year: int
    target_month: int
    target_day: int

class CareerRequest(BaseModel):
    user_name: str
    user_year: int
    user_month: int
    user_day: int
    user_sijin: Optional[int] = None
    career_status: str

CHEONGAN_HAP = {("갑", "기"), ("을", "경"), ("병", "신"), ("정", "임"), ("무", "계")}
JIJI_YUKHAP = {("자", "축"), ("인", "해"), ("묘", "술"), ("진", "유"), ("사", "신"), ("오", "미")}
JIJI_SAMHAP = {("신", "자"), ("자", "진"), ("해", "묘"), ("묘", "미"), ("인", "오"), ("오", "술"), ("사", "유"), ("유", "축")}
JIJI_CHUNG = {("자", "오"), ("축", "미"), ("인", "신"), ("묘", "유"), ("진", "술"), ("사", "해")}

def is_pair_in_set(set_data, a, b):
    return (a, b) in set_data or (b, a) in set_data

SAJU_MBTI_PROFILES = {
    "갑": {
        "title": "푸른 소나무 호랑이",
        "stem_name": "갑목(甲木)",
        "element_desc": "목(木) · 양목",
        "icon": "🌲",
        "trait": "당당한 리더십과 곧게 뻗어나가는 개척자의 기질",
        "mbti": "ENTJ",
        "traits": ["추진력", "우두머리 기질", "솔직담백", "명예욕"],
        "work_style": "지시받기보다 프로젝트를 총괄하고 기틀을 세울 때 폭발적인 성과를 냅니다.",
        "romance_style": "겉은 무뚝뚝하지만 뒤에서 든든하게 챙겨주는 신뢰 중심의 츤데레 스타일.",
        "best_match": "己토 (안정적인 조력자)",
        "worst_match": "庚금 (정면충돌하는 통제자)"
    },
    "을": {
        "title": "초원을 달리는 바람사슴",
        "stem_name": "을목(乙木)",
        "element_desc": "목(木) · 음목",
        "icon": "🌿",
        "trait": "척박한 환경도 극복하는 뛰어난 생명력과 적응력",
        "mbti": "ENFP",
        "traits": ["생활력", "친화력", "임기응변", "공감능력"],
        "work_style": "네트워킹과 분위기 메이킹에 탁월하며 위기에서 유연하게 대안을 찾습니다.",
        "romance_style": "상대의 감정을 섬세하게 살피며 다정다감한 케어를 아끼지 않는 타입.",
        "best_match": "庚금 (든든한 버팀목)",
        "worst_match": "辛금 (예리하게 상처 주는 날)"
    },
    "병": {
        "title": "태양을 품은 붉은 불사조",
        "stem_name": "병화(丙火)",
        "element_desc": "화(火) · 양화",
        "icon": "🔥",
        "trait": "세상을 환하게 비추는 열정과 투명하고 솔직한 에너지",
        "mbti": "ESFP",
        "traits": ["열정", "투명함", "스케일", "사교성"],
        "work_style": "비전을 제시하고 대중 앞에 서는 브랜딩/마케팅 분야에서 탁월합니다.",
        "romance_style": "좋아하면 직진하는 불도저. 감정을 숨기지 않고 아낌없이 쏟아붓습니다.",
        "best_match": "辛금 (매력을 끄는 조화)",
        "worst_match": "壬수 (스케일로 맞부딪히는 파도)"
    },
    "정": {
        "title": "달빛 아래 지혜로운 올빼미",
        "stem_name": "정화(丁火)",
        "element_desc": "화(火) · 음화",
        "icon": "🕯️",
        "trait": "어둠을 은은히 밝히는 등불처럼 내면의 지혜와 깊은 통찰력",
        "mbti": "INFJ",
        "traits": ["통찰력", "헌신", "감수성", "예술적 감각"],
        "work_style": "1:1 심층 상담, 연구, 디테일이 필요한 전문 영역에 최적화.",
        "romance_style": "한번 맺은 인연에는 한없는 헌신과 깊은 교감을 보입니다.",
        "best_match": "壬수 (감정이 통하는 호흡)",
        "worst_match": "癸수 (열정을 식히는 비)"
    },
    "무": {
        "title": "흔들리지 않는 황금 곰",
        "stem_name": "무토(戊土)",
        "element_desc": "토(土) · 양토",
        "icon": "⛰️",
        "trait": "광활한 대지처럼 묵직한 존재감과 흔들림 없는 신뢰감",
        "mbti": "ESTJ",
        "traits": ["포용력", "신뢰감", "무게감", "현실감각"],
        "work_style": "자산 관리, 인프라 운영, 시스템 구축 등 안정적인 질서 유지에 강합니다.",
        "romance_style": "한결같은 태도와 현실적인 든든함으로 사랑을 지킵니다.",
        "best_match": "癸수 (땅을 적시는 단비)",
        "worst_match": "甲목 (뿌리로 땅을 가르는 부담)"
    },
    "기": {
        "title": "들판을 가꾸는 황금 다람쥐",
        "stem_name": "기토(己土)",
        "element_desc": "토(土) · 음토",
        "icon": "🌾",
        "trait": "모든 생명을 길러내는 밭흙처럼 세심하고 따뜻한 힐러",
        "mbti": "ISFJ",
        "traits": ["세심함", "배려심", "실속추구", "적응력"],
        "work_style": "실무 관리, 인사, 고객 관리 등 정교함과 안정감이 필요한 업무에 적합합니다.",
        "romance_style": "상대의 생활을 세심하게 챙기며 편안한 일상을 만들어줍니다.",
        "best_match": "甲목 (나를 이끄는 나무)",
        "worst_match": "乙목 (기운을 뺏는 잡초)"
    },
    "경": {
        "title": "정의로운 백색 표범",
        "stem_name": "경금(庚金)",
        "element_desc": "금(金) · 양금",
        "icon": "🪙",
        "trait": "거대한 바위처럼 맺고 끊음이 확실한 원칙과 결단의 수호자",
        "mbti": "ISTJ",
        "traits": ["결단력", "의리", "원칙주의", "돌파력"],
        "work_style": "품질 관리, 법률, 보안 등 명확한 기준과 규율이 필요한 분야에 탁월합니다.",
        "romance_style": "말보다 행동으로 보여주며, 내 사람이라 생각되면 끝까지 지켜냅니다.",
        "best_match": "乙목 (냉철함을 녹이는 부드러움)",
        "worst_match": "丙화 (나를 녹이려는 불)"
    },
    "신": {
        "title": "반짝이는 은빛 유니콘",
        "stem_name": "신금(辛金)",
        "element_desc": "금(金) · 음금",
        "icon": "💎",
        "trait": "정교하게 다듬어진 보석처럼 섬세한 감각과 완벽주의",
        "mbti": "ISTP",
        "traits": ["예리함", "완벽주의", "심미안", "자존심"],
        "work_style": "UI/UX 디자인, 프로그래밍, 기술 정밀 분석 등 전문 기술 영역에서 최고 역량 발휘.",
        "romance_style": "선별된 소수에게만 곁을 주며 깔끔하고 독립적인 거리를 유지합니다.",
        "best_match": "丙화 (나를 비추는 조명)",
        "worst_match": "丁화 (보석을 그을리는 불)"
    },
    "임": {
        "title": "드넓은 대양의 푸른 고래",
        "stem_name": "임수(壬水)",
        "element_desc": "수(水) · 양수",
        "icon": "🌊",
        "trait": "큰 바다처럼 고정관념에 얽매이지 않는 지략과 호기심",
        "mbti": "ENTP",
        "traits": ["유연성", "임기응변", "지략", "호기심"],
        "work_style": "사업 기획, 신사업 발굴, 투자 등 자유도와 창의성이 높은 환경에서 빛납니다.",
        "romance_style": "지적 대화가 통하는 상대에게 끌리며 신선한 자극을 주고받길 원합니다.",
        "best_match": "丁화 (영감을 완성하는 불꽃)",
        "worst_match": "戊토 (흐름을 막는 댐)"
    },
    "계": {
        "title": "밤하늘을 적시는 은빛 여우",
        "stem_name": "계수(癸水)",
        "element_desc": "수(水) · 음수",
        "icon": "💧",
        "trait": "이슬비처럼 조용히 스며들어 전체를 파악하는 깊은 지혜",
        "mbti": "INTP",
        "traits": ["관찰력", "지혜", "다정함", "직관"],
        "work_style": "데이터 분석, 연구 개발, 심층 기획 등 몰입하여 깊이를 파고드는 직무에 최적.",
        "romance_style": "마음 깊은 교감을 소중히 여기며 묵묵히 지지해 주는 온화한 사랑을 합니다.",
        "best_match": "戊토 (나를 품어주는 둑)",
        "worst_match": "己토 (물을 흐리는 흙)"
    }
}

def get_character_and_shinsal(day_gan: str, user_ji_list: list):
    profile = SAJU_MBTI_PROFILES.get(day_gan, SAJU_MBTI_PROFILES["갑"])

    shinsal_list = []
    ji_str = "".join(user_ji_list)
    if any(k in ji_str for k in ["자", "오", "묘", "유"]):
        shinsal_list.append({"name": "도화살 (桃花殺)", "desc": "사람을 끌어당기는 치명적 매력과 스타성", "tag": "인기/매력"})
    if any(k in ji_str for k in ["인", "신", "사", "해"]):
        shinsal_list.append({"name": "역마살 (驛馬殺)", "desc": "활동 무대를 넓혀 세상을 누비는 개척력", "tag": "이동/성장"})
    if any(k in ji_str for k in ["진", "술", "축", "미"]):
        shinsal_list.append({"name": "화개살 (華蓋殺)", "desc": "예술적 감수성과 지적 전문성, 명예운", "tag": "예술/전문직"})
    shinsal_list.append({"name": "천을귀인 (天乙貴人)", "desc": "위기마다 결정적 은인이 나타나는 최고 길신", "tag": "인생수호"})

    return {
        "title": profile["title"],
        "stem_name": profile["stem_name"],
        "element_desc": profile["element_desc"],
        "icon": profile["icon"],
        "trait": profile["trait"],
        "mbti": profile["mbti"],
        "traits": profile["traits"],
        "work_style": profile["work_style"],
        "romance_style": profile["romance_style"],
        "best_match": profile["best_match"],
        "worst_match": profile["worst_match"],
        "shinsal": shinsal_list
    }

def get_dynamic_fortune(user_day_gan: str, user_name: str):
    today = datetime.now()
    base_date = datetime(1900, 1, 1)
    diff_days = (today - base_date).days
    
    today_gan_idx = (diff_days + 0) % 10
    today_ji_idx = (diff_days + 4) % 12
    today_gan = CHEONGAN[today_gan_idx]
    today_ji = JIJI[today_ji_idx]
    today_iljin_name = f"{today_gan}{today_ji}일"
    
    user_idx = CHEONGAN.index(user_day_gan) if user_day_gan in CHEONGAN else 0
    day_seed = (diff_days * 7 + user_idx * 13 + today.day * 3)
    
    shipshin_list = [
        ("비견(比肩)의 날", 86, "동료나 친구와의 유대가 강해지는 날입니다. 협업할 때 2배의 성과가 납니다."),
        ("겁재(劫財)의 날", 81, "승부욕이 샘솟는 날입니다. 지출을 조심하고 내실을 다지면 이득이 됩니다."),
        ("식신(食神)의 날", 94, "창의적인 영감과 먹복이 넘치는 날입니다. 기획이나 표현을 마음껏 표출하세요."),
        ("상관(傷官)의 날", 89, "언변과 순발력이 빛나는 날입니다. 솔직하고 재치 있는 대화가 호감을 부릅니다."),
        ("편재(偏財)의 날", 95, "뜻밖의 금전 기회나 유쾌한 제안이 들어오는 길일입니다. 과감한 판단이 유리합니다."),
        ("정재(正財)의 날", 97, "노력한 만큼 확실한 보상과 결실이 따르는 재물 대길일입니다. 안목이 빛납니다."),
        ("편관(偏官)의 날", 78, "책임감이 무거워지지만 이를 완수했을 때 큰 인정을 받습니다. 침착함을 유지하세요."),
        ("정관(正官)의 날", 91, "규율과 명예운이 높아지는 날입니다. 중요한 서류나 계약 진행에 최적입니다."),
        ("편인(偏印)의 날", 87, "직관력과 예리한 통찰력이 돋보이는 날입니다. 새로운 아이디어를 정리하세요."),
        ("정인(印星)의 날", 93, "윗사람이나 귀인의 전폭적인 지원을 받는 따뜻한 날입니다. 순리대로 진행하세요.")
    ]
    
    theme_tuple = shipshin_list[(diff_days + user_idx) % len(shipshin_list)]
    theme_label, base_score, daily_advice = theme_tuple
    calculated_daily_score = min(max(base_score + (day_seed % 7) - 3, 68), 99)

    colors_pool = [
        "포레스트 그린 / 민트", "선명한 코랄 레드 / 와인", "따뜻한 베이지 / 머스타드", 
        "클래식 화이트 / 실버", "딥 네이비 / 스카이블루", "올리브 그린 / 앰버", "로즈 골드 / 파스텔 핑크"
    ]
    fashions_pool = [
        "편안하면서 단정한 린넨 셔츠나 내추럴 룩", "포인트 컬러 니트나 스마트 캐주얼",
        "차분한 톤온톤 슬랙스와 신뢰감 주는 룩", "각이 살아있는 테일러드 재킷이나 모던 모노톤",
        "루즈핏 셔츠나 부드러운 소재의 데일리 룩", "깔끔한 화이트 셔츠와 가벼운 스니커즈 조합"
    ]
    items_pool = [
        "가죽 시계/지갑", "은은한 향수, 안경", "나무/패브릭 소재 소품", 
        "실버 링, 메탈 프레임 펜", "텀블러, 실크 스카프", "노란색 가죽 키링, 태블릿"
    ]
    directions_pool = ["동쪽 및 동남쪽", "남쪽", "중앙 및 동북쪽", "서쪽 및 북서쪽", "북쪽"]
    
    menus_pool = [
        "따뜻하고 구수한 차돌 된장찌개", "상큼한 샐러드와 건강한 쌈밥정식",
        "매콤달콤한 제육볶음이나 불고기", "속을 차분하게 풀어주는 영양 전복죽",
        "담백한 삼계탕이나 나주곰탕", "시원한 해물칼국수나 모둠초밥",
        "고소한 계란말이와 김치찌개 조합", "따뜻한 카페라떼와 과일 에이드",
        "노릇하게 구운 생선구이 정식", "부드러운 단호박죽과 잡곡밥",
        "얼큰한 해물 순두부찌개", "신선한 입맛을 돋우는 청포도 리코타 샐러드"
    ]

    lucky_color = colors_pool[day_seed % len(colors_pool)]
    fashion_style = fashions_pool[(day_seed + 1) % len(fashions_pool)]
    lucky_item = items_pool[(day_seed + 2) % len(items_pool)]
    lucky_direction = directions_pool[(day_seed + 3) % len(directions_pool)]
    recommended_menu = menus_pool[(day_seed + 4) % len(menus_pool)]

    talisman_types = [
        {"title": "재물만복부 (財物萬福符)", "desc": "금고의 문을 열고 새는 돈을 막아주는 황금 기운", "chinese": "財運大吉\n聚財如山", "power": "재물통로 개운 · 자산 증식"},
        {"title": "만사형통부 (萬事亨通符)", "desc": "막힌 판을 시원하게 뚫어주는 개척과 번영의 기운", "chinese": "萬事亨通\n百事如意", "power": "소원 성취 · 장벽 돌파"},
        {"title": "천우신조부 (天佑神助符)", "desc": "결정적인 순간 귀인의 손길을 이어주는 수호 기운", "chinese": "天乙貴人\n逢凶化吉", "power": "귀인 조력 · 위기 탈출"},
        {"title": "연리지합부 (連理枝合符)", "desc": "서로의 마음을 묶어 깊은 신뢰를 채우는 인연 기운", "chinese": "夫婦和合\n百緣結實", "power": "인연 화합 · 부부 금슬"}
    ]
    talisman_data = talisman_types[(day_seed + user_idx) % len(talisman_types)]

    lucky_people = [
        "나에게 긍정적 피드백을 주는 직장 선배", "오랜만에 연락 온 옛 동창", 
        "아이디어 넘치는 B형 동료", "경청해 주는 O형 지인", "연상의 멘토", "감각적인 후배"
    ]
    lucky_person = lucky_people[(today.day + user_idx) % len(lucky_people)]

    gaewoon_list = [
        "아침 기상 직후 10분간 창문을 활짝 열어 실내 탁기를 환기하세요.",
        "따뜻한 물 한 잔을 마시며 오늘 이룰 핵심 목표 1가지를 메모하세요.",
        "동료나 지인에게 먼저 따뜻한 미소로 인사를 건네보세요.",
        "책상 위나 지갑 안의 영수증을 정돈하여 재물 통로를 여세요.",
        "퇴근길 15분간 가볍게 산책하며 하루의 피로를 비워내세요."
    ]
    today_gaewoon = gaewoon_list[(today.day + today_gan_idx) % len(gaewoon_list)]

    monthly_gan_themes = {
        "갑": f"{today.month}월은 큰 나무(甲木)인 당신에게 새로운 뿌리를 내리고 가지를 뻗는 '도약과 확장'의 달입니다.\n\n📅 [월간 10일 단위 흐름]\n• 상순 (1~10일): 계획 구체화 및 환경 정돈\n• 중순 (11~20일): 귀인의 결정적 조력과 인맥 확장\n• 하순 (21~말일): 실질적 성과 회수 및 내실 다지기",
        "을": f"{today.month}월은 유연한 담쟁이(乙木)인 당신에게 든든한 지지대를 만나는 '성취'의 달입니다.\n\n📅 [월간 10일 단위 흐름]\n• 상순 (1~10일): 실속 있는 목표 설정\n• 중순 (11~20일): 협업 시너지 극대화\n• 하순 (21~말일): 재정 안정 및 지출 관리",
        "병": f"{today.month}월은 뜨거운 태양(丙火)인 당신의 열정이 널리 인정받는 '명예와 결실'의 달입니다.\n\n📅 [월간 10일 단위 흐름]\n• 상순 (1~10일): 대외 활동 및 발표 준비\n• 중순 (11~20일): 영향력 확대와 제안 유입\n• 하순 (21~말일): 결실 정리 및 에너지 충전",
        "정": f"{today.month}월은 섬세한 촛불(丁火)인 당신의 지혜가 빛을 발하는 '가치 상승'의 달입니다.\n\n📅 [월간 10일 단위 흐름]\n• 상순 (1~10일): 전문 지식/기술 연마\n• 중순 (11~20일): 신뢰 깊은 파트너십 형성\n• 하순 (21~말일): 안정된 성과 도출",
        "무": f"{today.month}월은 넓은 대지(戊土)인 당신에게 많은 사람과 기회가 모여드는 '신뢰와 포용'의 달입니다.\n\n📅 [월간 10일 단위 흐름]\n• 상순 (1~10일): 장기 프로젝트 밑그림 완성\n• 중순 (11~20일): 재물운 유입 및 계약 성사\n• 하순 (21~말일): 내실 다지기 및 리스크 점검",
        "기": f"{today.month}월은 비옥한 흙(己土)인 당신이 기른 씨앗이 열매를 맺는 '수확'의 달입니다.\n\n📅 [월간 10일 단위 흐름]\n• 상순 (1~10일): 세밀한 일정 및 예산 점검\n• 중순 (11~20일): 실질적 금전 소득 발생\n• 하순 (21~말일): 자산 보존 및 다음 달 기획",
        "경": f"{today.month}월은 단호한 바위(庚金)인 당신의 결단력이 막힌 혈을 뚫는 '돌파와 개척'의 달입니다.\n\n📅 [월간 10일 단위 흐름]\n• 상순 (1~10일): 불필요한 군더더기 정리\n• 중순 (11~20일): 경쟁 우위 선점 및 합격운\n• 하순 (21~말일): 승리의 보상 획득",
        "신": f"{today.month}월은 세련된 보석(辛金)인 당신의 진가가 드러나는 '빛과 인정'의 달입니다.\n\n📅 [월간 10일 단위 흐름]\n• 상순 (1~10일): 개인 브랜딩 및 자기계발\n• 중순 (11~20일): 주목받는 기회와 칭찬\n• 하순 (21~말일): 품격 있는 휴식과 보상",
        "임": f"{today.month}월은 큰 바다(壬水)인 당신의 깊은 통찰력이 파도를 타는 '대도약'의 달입니다.\n\n📅 [월간 10일 단위 흐름]\n• 상순 (1~10일): 원거리/글로벌 기회 탐색\n• 중순 (11~20일): 대규모 유통 및 거래 성사\n• 하순 (21~말일): 자금 회수 및 시스템화",
        "계": f"{today.month}월은 촉촉한 봄비(癸水)인 당신의 감수성이 대지를 적시는 '창조와 감동'의 달입니다.\n\n📅 [월간 10일 단위 흐름]\n• 상순 (1~10일): 번뜩이는 아이디어 구체화\n• 중순 (11~20일): 감성 소통과 인연 유입\n• 하순 (21~말일): 안정된 결실 안착"
    }

    month_theme = monthly_gan_themes.get(user_day_gan, f"{today.month}월은 당신의 타고난 잠재력이 활짝 피어나는 도약의 달입니다.")
    month_score = min(max(80 + ((user_idx * 4 + today.month * 2) % 18), 70), 98)

    year_score = min(max(78 + ((user_idx + today.year) * 5) % 20, 75), 99)
    year_trend = (
        f"【 {today.year}년 {user_name} 님을 위한 마스터 신년 총운 리포트 】\n\n"
        f"올해 {today.year}년은 당신의 타고난 '{user_day_gan}'의 기운이 하늘과 땅의 조화를 만나 인생의 거대한 변곡점을 통과하는 대운의 해입니다.\n\n"
        "📊 [2026년 4분기별 정밀 운세 흐름도]\n"
        "• 1분기 (1~3월) : [입춘대길 - 씨앗을 뿌리는 시기]\n"
        "  - 정체되어 있던 기운이 풀리며 새로운 환경이 열립니다. 과감한 도전보다 기초 공사에 집중하세요.\n\n"
        "• 2분기 (4~6월) : [개화결실 - 기운의 폭발적 상승]\n"
        "  - 실력이 대외적으로 인정받으며 재물과 명예운이 동시에 상승합니다. 귀인의 조언을 적극 수용하세요.\n\n"
        "• 3분기 (7~9월) : [만사형통 - 성과의 가시화]\n"
        "  - 올해의 하이라이트 구간입니다. 계약, 승진, 자산 증식 등 실질적 수확을 거두게 됩니다.\n\n"
        "• 4분기 (10~12월) : [갈무리 - 결실 보존과 내실 다지기]\n"
        "  - 얻은 성과를 안전하게 지키고 무리한 투자를 경계해야 하는 안정기입니다."
    )

    return {
        "daily": {
            "title": f"{today.strftime('%Y년 %m월 %d일')} [{today_iljin_name}] 오늘의 운세",
            "score": calculated_daily_score,
            "advice": f"【 오늘의 테마: {theme_label} 】\n{daily_advice}",
            "lucky_color": lucky_color,
            "lucky_number": (today.day * 7 + user_idx) % 9 + 1,
            "fashion_style": fashion_style,
            "lucky_item": lucky_item,
            "lucky_direction": lucky_direction,
            "recommended_menu": recommended_menu,
            "talisman": talisman_data,
            "lucky_person": lucky_person,
            "today_gaewoon": today_gaewoon,
            "love_advice": f"오늘 {today_iljin_name}의 기운은 당신의 타고난 매력을 드러내 줍니다. 따뜻한 미소가 호감을 부릅니다.",
            "career_advice": f"오늘 {theme_label}의 흐름에 맞춰 집중력을 발휘하면 기대 이상의 업무 성취를 거둡니다.",
            "health_advice": "충분한 수분 섭취와 바른 자세 유지가 기운의 순환을 돕습니다.",
            "study_advice": "오늘 배운 핵심 개념 3가지를 정리해 두면 장기 기억으로 전환됩니다."
        },
        "monthly": {
            "title": f"{today.year}년 {today.month}월 [{user_day_gan} 일간] 이달의 심층 운세",
            "score": month_score,
            "theme": month_theme,
            "love_advice": f"이번 {today.month}월은 진솔한 마음을 나눌수록 관계가 급진전되는 호운기입니다.",
            "career_advice": "주도적으로 프로젝트를 이끌어갈 때 상사의 전폭적인 지원을 받습니다.",
            "health_advice": "환절기 면역력 강화를 위해 가벼운 유산소 운동을 병행하세요.",
            "study_advice": "10일 단위 목표치를 쪼개어 실천하면 계획을 100% 달성합니다."
        },
        "yearly": {
            "title": f"{today.year}년 한 해 대운 마스터 총운",
            "score": year_score,
            "main_trend": year_trend,
            "love_advice": "평생을 함께할 깊은 인연을 맺거나 기존 관계가 성숙해지는 축복의 해입니다.",
            "career_advice": "커리어의 정점을 찍는 도약의 해로 이직, 승진, 사업 확장에 대길합니다.",
            "health_advice": "바쁜 일정 속에서도 멘탈 관리와 정기 검진을 챙겨야 체력이 운을 받쳐줍니다.",
            "study_advice": "지적 집중력이 절정에 달해 자격증, 학위 취득, 시험 합격의 쾌거를 이룹니다."
        }
    }

def calculate_life_chart(day_gan: str, birth_year: int):
    gan_idx = CHEONGAN.index(day_gan) if day_gan in CHEONGAN else 0
    base_scores = [68, 74, 82, 95, 88, 79, 85]
    adjusted = []
    for i, s in enumerate(base_scores):
        val = min(max(s + ((gan_idx * 3 + i * 7) % 15) - 5, 55), 98)
        adjusted.append(val)
    return {
        "labels": ["10대", "20대", "30대", "40대", "50대", "60대", "70대+"],
        "scores": adjusted,
        "peak_age": "40대 중후반 ~ 50대 (황금 전성기 구간)"
    }

@app.post("/api/analyze")
def analyze(req: SajuRequest):
    is_unknown = req.is_unknown_time or (req.sijin_index is None) or (req.sijin_index == -1)

    result = calculate_saju(
        year=req.year, month=req.month, day=req.day,
        sijin_index=req.sijin_index if not is_unknown else None, is_unknown_time=is_unknown
    )
    
    day_gan = result["day_gan"]
    user_ji_list = [result["pillars"]["year"][1], result["pillars"]["month"][1], result["pillars"]["day"][1]]
    if result["pillars"]["hour"]:
        user_ji_list.append(result["pillars"]["hour"][1])

    character_profile = get_character_and_shinsal(day_gan, user_ji_list)
    life_chart = calculate_life_chart(day_gan, req.year)
    fortune_bundle = get_dynamic_fortune(user_day_gan=day_gan, user_name=req.name)
    jijanggan_data = analyze_jijanggan_profile(result["pillars"], day_gan)
    zami_info = ZAMIDUSU_STARS.get(day_gan, ZAMIDUSU_STARS["갑"])

    current_fortune_summary = f"""• 최근 운세 총평: {req.name} 님의 현재 시점은 준비해 온 일들의 매듭이 지어지고 귀인의 조력으로 새로운 실마리가 풀리는 긍정적인 전환기입니다.
• 💰 재물운: 목돈이 차곡차곡 쌓이는 정재(正財)의 흐름이 좋아, 단기 투기보다 안전한 문서 자산으로 묶어둘 때 안정적 결실을 맺습니다.
• 💼 사업·직업운: 조직과 업무 무대에서 주도권이 강화되며, 신뢰할 만한 파트너와의 협업으로 추진 중인 계약과 프로젝트가 순조롭게 진척됩니다.
• 💖 애정·가정운: 서로의 마음에 공감하며 신뢰가 한층 깊어지는 시기로, 가정이 편안한 안식처가 되어 삶의 든든한 버팀목이 됩니다.
• 🤝 대인·관계운: 주변 사람들에게 깊은 신뢰를 얻으며, 결정적인 순간에 나를 돕는 귀인과의 인연이 활발하게 연결됩니다."""

    asset_checklist = f"""• 💰 재물·문서: 현금성 단기 자금보다 부동산이나 우량 문서 자산 형태로 안전하게 묶어두고 고정 지출 다이어트
• 💼 커리어·사회: 본인만의 전문적 주도권을 확립하고 귀인과의 협업 네트워크를 단단히 정돈
• 💖 가정·애정: 소모적인 대외 관계를 줄이고 배우자 및 가족과의 정서적 신뢰와 따뜻한 안식처 구축
• 🌿 건강·활력: 40대 대사 변화에 맞춘 2년 주기 정밀 건강 검진과 체질 맞춤 기혈 순환 스트레칭 루틴화"""

    daewoon_report = f"""
<div class="space-y-4 text-xs text-slate-800 font-normal leading-relaxed">
  <div class="bg-brand-50 border border-brand-200 rounded-2xl p-4 text-center space-y-1">
    <div class="text-xs font-bold text-brand-950">👑 {req.name} 님의 자미두수 & 10년 대운 마스터 감명서</div>
    <p class="text-[11px] text-brand-800 font-medium">동양 왕실 점성술 '자미두수 4대궁'과 대운의 계절을 완벽 해부한 평생 인생 설계도</p>
  </div>

  <div class="space-y-2">
    <div class="flex items-center space-x-2 bg-[#F8FAF7] p-2.5 rounded-xl border-l-4 border-brand-600 font-bold text-slate-900 text-xs">
      <span>📍</span><span>1. {req.name} 님의 현재 위치와 기본 운세 흐름</span>
    </div>
    <div class="p-3.5 bg-slate-50/80 border border-slate-200/60 rounded-xl text-slate-700 font-medium leading-relaxed space-y-2">
      <p>{req.name} 님은 현재 거대한 10년 대운의 중요한 도약 지점에 서 계십니다. 겉으로 드러난 기운 외에도 지장간에 암장된 숨은 복이 수면 위로 올라오는 전환기입니다.</p>
      <div class="text-brand-900 bg-brand-50 p-2.5 rounded-lg border border-brand-200 text-[11px]">
        💡 <b>내면의 지장간 복:</b> {jijanggan_data['summary']}
      </div>
      <p>독립심과 뚝심을 바탕으로 주도적 역할을 맡을 때 40대 중후반부터 사회적 명예와 재물이 퀀텀 점프하게 됩니다.</p>
    </div>
  </div>

  <div class="space-y-2">
    <div class="flex items-center space-x-2 bg-[#F8FAF7] p-2.5 rounded-xl border-l-4 border-amber-600 font-bold text-slate-900 text-xs">
      <span>🔮</span><span>2. 자미두수(紫微斗數) 4대 핵심 궁(宮) 정밀 분석</span>
    </div>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px]">
      <div class="p-3 bg-slate-50/80 border border-slate-200/60 rounded-xl space-y-1">
        <span class="font-bold text-amber-900 block">💰 재백궁(財帛宮): {zami_info['wealth'][0]}</span>
        <p class="text-slate-600 font-normal leading-snug">{zami_info['wealth'][1]}</p>
      </div>
      <div class="p-3 bg-slate-50/80 border border-slate-200/60 rounded-xl space-y-1">
        <span class="font-bold text-sky-900 block">💼 관록궁(官祿宮): {zami_info['career'][0]}</span>
        <p class="text-slate-600 font-normal leading-snug">{zami_info['career'][1]}</p>
      </div>
      <div class="p-3 bg-slate-50/80 border border-slate-200/60 rounded-xl space-y-1">
        <span class="font-bold text-rose-900 block">💖 부처궁(夫妻宮): {zami_info['love'][0]}</span>
        <p class="text-slate-600 font-normal leading-snug">{zami_info['love'][1]}</p>
      </div>
      <div class="p-3 bg-slate-50/80 border border-slate-200/60 rounded-xl space-y-1">
        <span class="font-bold text-emerald-900 block">🌿 질악궁(疾厄宮): {zami_info['health'][0]}</span>
        <p class="text-slate-600 font-normal leading-snug">{zami_info['health'][1]}</p>
      </div>
    </div>
  </div>

  <div class="space-y-2">
    <div class="flex items-center space-x-2 bg-[#F8FAF7] p-2.5 rounded-xl border-l-4 border-brand-600 font-bold text-slate-900 text-xs">
      <span>🌟</span><span>3. {req.name} 님의 현재 시점 종합 운세 흐름 (재물·사업·애정·관계)</span>
    </div>
    <div class="p-3.5 bg-slate-50/80 border border-slate-200/60 rounded-xl space-y-2 text-slate-800 font-medium text-[11px] leading-relaxed">
      <p>• <b>현재 운세 총평:</b> 그동안 차곡차곡 쌓아온 내공과 지장간의 숨은 복이 동시에 작용하는 강력한 전환점입니다.</p>
      <p>• <b>💰 재물운:</b> 지출보다는 목돈이 고이는 정재(正財)의 기운이 강하게 작용하여, 무리한 투기 대신 문서 자산이나 부동산으로 묶어둘 때 안정적 부를 불려 나갑니다.</p>
      <p>• <b>💼 사업·직업운:</b> 조직이나 사업 무대에서 본인의 주도권과 전문성이 한층 강화되며, 귀인의 조력으로 중요한 프로젝트나 계약을 차근차근 성사시킵니다.</p>
      <p>• <b>💖 애정·가정운:</b> 감정의 기복이 줄어들고 마음이 통하는 따뜻한 안식처를 구축하는 운으로, 배우자 및 연인과의 신뢰가 더욱 깊어집니다.</p>
      <p>• <b>🤝 대인·관계운:</b> 서두르지 않는 의연함이 주변 사람들에게 높은 신뢰를 주며, 결정적인 순간 나를 돕는 귀인과의 인연이 이어집니다.</p>
    </div>
  </div>

  <div class="space-y-2">
    <div class="flex items-center space-x-2 bg-[#F8FAF7] p-2.5 rounded-xl border-l-4 border-brand-600 font-bold text-slate-900 text-xs">
      <span>⚡</span><span>4. 단기적으로 다가올 기회와 주의할 변수</span>
    </div>
    <div class="p-3.5 bg-slate-50/80 border border-slate-200/60 rounded-xl space-y-1.5 text-slate-700 font-medium text-[11px]">
      <div>• <b>다가오는 기회:</b> 귀인의 조력과 새로운 계약/문서운이 크게 열려 자산 가치를 높일 기회가 다가옵니다.</div>
      <div>• <b>주의할 변수:</b> 조급한 마음에 단기 투기나 검증되지 않은 인간관계에 과도하게 의존하는 것은 피해야 합니다.</div>
    </div>
  </div>

  <div class="space-y-2">
    <div class="flex items-center space-x-2 bg-[#F8FAF7] p-2.5 rounded-xl border-l-4 border-brand-600 font-bold text-slate-900 text-xs">
      <span>🎯</span><span>5. 운의 흐름을 좋게 바꾸는 실천 액션 & 마인드셋</span>
    </div>
    <div class="p-3.5 bg-slate-50/80 border border-slate-200/60 rounded-xl space-y-1.5 text-slate-800 font-medium text-[11px]">
      <div>• <b>판단 지침:</b> 중요 결정 시 외부 소문에 휘둘리지 말고 본연의 뚝심과 직관을 믿고 소신 있게 밀고 나아가세요.</div>
      <div>• <b>행동 지침:</b> 현금보다는 실물 자산(부동산, 우량주)으로 자금을 묶어두고 내실을 다지는 자기계발을 병행하세요.</div>
      <div>• <b>마인드셋:</b> "지금의 준비가 곧 거대한 전성기의 씨앗이 된다"는 확신을 품고 차분히 기회를 포착하세요.</div>
    </div>
  </div>

  <div class="space-y-2">
    <div class="flex items-center space-x-2 bg-[#F8FAF7] p-2.5 rounded-xl border-l-4 border-brand-600 font-bold text-slate-900 text-xs">
      <span>📈</span><span>6. 생애 4대 주기별 10년 대운 로드맵 & 배우자 인연</span>
    </div>
    <div class="space-y-2">
      <div class="bg-white p-3 rounded-xl border border-brand-100 shadow-2xs space-y-1">
        <div class="font-bold text-slate-900 text-[11px] flex items-center justify-between">
          <span>• 1단계: 청년기 (10대 후반~20대)</span>
          <span class="bg-slate-100 text-slate-600 px-2 py-0.5 rounded text-[10px] font-medium">파종과 단련</span>
        </div>
        <p class="text-[11px] text-slate-600">학업과 다양한 시행착오를 거치며 내공을 다지는 시기입니다.</p>
      </div>
      <div class="bg-white p-3 rounded-xl border border-brand-100 shadow-2xs space-y-1">
        <div class="font-bold text-slate-900 text-[11px] flex items-center justify-between">
          <span>• 2단계: 중년기 (30대~40대 초반)</span>
          <span class="bg-slate-100 text-slate-600 px-2 py-0.5 rounded text-[10px] font-medium">개화와 실력검증</span>
        </div>
        <p class="text-[11px] text-slate-600">사회적 입지를 구축하고 독자적 전문 기반을 완성하는 분기점입니다.</p>
      </div>
      <div class="bg-amber-50 p-3 rounded-xl border-2 border-amber-300 shadow-2xs space-y-1">
        <div class="font-bold text-amber-950 text-[11px] flex items-center justify-between">
          <span>• 3단계: 장년기 (40대 중후반~50대) 🌟</span>
          <span class="bg-amber-500 text-white px-2 py-0.5 rounded text-[10px] font-bold">황금 전성기</span>
        </div>
        <p class="text-[11px] text-amber-900 font-medium">실력과 귀인의 조력이 맞물려 사회적 지위와 재산 규모가 폭발적으로 증가합니다.</p>
      </div>
      <div class="bg-white p-3 rounded-xl border border-brand-100 shadow-2xs space-y-1">
        <div class="font-bold text-slate-900 text-[11px] flex items-center justify-between">
          <span>• 4단계: 노년기 (60대 이후)</span>
          <span class="bg-slate-100 text-slate-600 px-2 py-0.5 rounded text-[10px] font-medium">결실과 안식</span>
        </div>
        <p class="text-[11px] text-slate-600">평생 일군 자산을 바탕으로 여유롭고 명예로운 만년운을 누립니다.</p>
      </div>
      <div class="p-3.5 bg-slate-50/80 border border-slate-200/60 rounded-xl space-y-1 text-slate-700 font-medium text-[11px] mt-2">
        <div>• <b>배우자 인연:</b> 일지에 안정적 기운이 깃들어 있어, 마음이 따뜻하고 감정 기복이 적은 지혜로운 배우자와 인연을 맺어 평생 화목한 가정을 이루게 됩니다.</div>
        <div>• <b>찰떡 인연 띠:</b> <span class="font-bold text-rose-600">양띠 (未) · 호랑이띠 (寅)</span> (서로의 기운을 채워주는 영혼의 단짝)</div>
      </div>
    </div>
  </div>

  <div class="space-y-2">
    <div class="flex items-center space-x-2 bg-[#F8FAF7] p-2.5 rounded-xl border-l-4 border-brand-600 font-bold text-slate-900 text-xs">
      <span>🔮</span><span>7. 사주 맞춤 평생 개운(開運) 인테리어 & 생활 처방</span>
    </div>
    <div class="p-3.5 bg-slate-50/80 border border-slate-200/60 rounded-xl space-y-1.5 text-slate-800 font-medium text-[11px]">
      <div>• <b>침대 머리 방향:</b> <b class="text-brand-800">동남쪽</b> 또는 <b class="text-brand-800">북쪽</b>으로 둘 때 수면 중 기운 충전이 극대화됩니다.</div>
      <div>• <b>공간 개운 소품:</b> 거실이나 집무실에 잔잔한 수경 식물이나 금속/크리스털 소품을 배치하면 막힌 기운이 뚫립니다.</div>
      <div>• <b>행운의 숫자:</b> <b>1, 6, 9</b></div>
    </div>
  </div>
</div>
"""

    return {
        "user_name": req.name,
        "character_profile": character_profile,
        "life_chart": life_chart,
        "saju_data": result,
        "jijanggan_data": jijanggan_data,
        "current_fortune_summary": current_fortune_summary,
        "asset_checklist": asset_checklist,
        "fortunes": fortune_bundle,
        "paid_reports": {
            "daewoon": daewoon_report
        }
    }

TAROT_MAJOR_DECK = [
    {"name": "0. THE FOOL (바보)", "icon": "🎒", "keyword": "새로운 시작 · 자유로운 도약 · 무한한 가능성", "overview": "가벼운 배낭 하나만을 메고 낭떠러지 앞에서도 두려움 없이 발을 내딛는 순수한 방랑자의 카드입니다. 고정관념에서 벗어나 새로운 가능성을 열어젖히는 강력한 시작의 에너지를 품고 있습니다.", "action": "그동안 망설이던 아이디어나 취미, 프로젝트가 있다면 오늘 첫 발을 떼어보세요. 직관과 호기심을 따를 때 활로가 열립니다.", "caution": "지나친 낙관으로 기본 서류나 준비를 놓치지 않도록 돌다리도 한 번은 두드려보세요."},
    {"name": "I. THE MAGICIAN (마법사)", "icon": "🪄", "keyword": "탁월한 역량 · 기회 포착 · 창조적 실행", "overview": "머리 위에 무한대(∞)의 지혜를 얹고 사원소의 도구를 자유자재로 다루는 마법사의 카드입니다. 당신에게 필요한 모든 재능과 역량이 이미 손안에 완벽히 준비되어 있음을 상징합니다.", "action": "자신의 전문성과 말솜씨를 적극 어필하세요. 제안, 발표, 협상 자리에서 당신의 카리스마가 빛을 발합니다.", "caution": "자신감이 자만으로 비치지 않도록 경청하는 태도를 유지하세요."},
    {"name": "II. THE HIGH PRIESTESS (여사제)", "icon": "📖", "keyword": "깊은 직관 · 내면의 지혜 · 통찰력", "overview": "지혜의 두 기둥 사이에 앉아 우주의 신비를 담은 두루마리를 쥔 여사제의 카드입니다. 겉으로 드러나지 않는 본질을 꿰뚫는 예리한 영감과 학문적 성취를 상징합니다.", "action": "조급하게 행동하기보다 차분히 관망하며 데이터를 분석하고 내면의 직관에 귀를 기울이세요.", "caution": "지나치게 냉정하거나 비밀스러운 태도로 주변 사람에게 거리감을 주지 않도록 주의하세요."},
    {"name": "III. THE EMPRESS (여황제)", "icon": "👑", "keyword": "풍요로운 결실 · 따뜻한 포용 · 정서적 안정", "overview": "비옥한 들판과 풍성한 곡식 사이에서 미소 짓고 있는 여황제의 카드입니다. 노력해 온 일에서 실질적인 보상과 물질적·정서적 풍요가 찾아오는 축복의 운기입니다.", "action": "스스로를 아낌없이 대접하고 주변 사람들에게 따뜻한 식사나 감사의 말을 전해보세요.", "caution": "편안함에 안주하여 나태해지거나 과도한 충동구매로 흐르지 않도록 주의하세요."},
    {"name": "IV. THE EMPEROR (황제)", "icon": "🏛️", "keyword": "강력한 리더십 · 안정된 기반 · 책임과 권위", "overview": "돌보좌 위에 당당히 앉아 왕권을 수호하는 황제의 카드입니다. 확고한 통제력과 현실적 실행력으로 자신만의 영역을 굳건히 지켜내는 지도자의 힘을 나타냅니다.", "action": "원칙을 지키며 시스템을 정비하고 결단력 있게 조직이나 업무의 질서를 확립하세요.", "caution": "융통성 없는 고집이나 독단적인 태도로 아랫사람에게 부담을 주지 않도록 주의하세요."},
    {"name": "V. THE HIEROPHANT (교황)", "icon": "📜", "keyword": "귀인의 조언 · 도덕적 신뢰 · 협력과 연대", "overview": "지혜를 전파하며 사람들을 올바른 길로 이끄는 영적 멘토의 카드입니다. 신뢰할 수 있는 스승이나 멘토, 귀인의 결정적인 조력을 받게 됨을 상징합니다.", "action": "혼자 끙끙 앓지 말고 검증된 선배나 전문가에게 자문을 구하세요. 현명한 해답을 얻게 됩니다.", "caution": "형식주의나 낡은 관습에 얽매여 새로운 변화를 거부하지 않도록 유연성을 가지세요."},
    {"name": "VI. THE LOVERS (연인)", "icon": "💖", "keyword": "달콤한 조화 · 중요한 선택 · 진실된 교감", "overview": "천사의 축복 아래 마주 본 연인의 카드입니다. 마음이 통하는 깊은 애정운의 상승과 함께 인생의 중요한 갈림길에서 현명한 선택을 내려야 함을 나타냅니다.", "action": "마음이 이끄는 파트너와 진솔한 대화를 나누고, 가치관에 맞는 선택을 단호하게 내리세요.", "caution": "단기적인 유혹이나 순간적인 쾌락에 눈이 멀어 장기적인 신뢰를 잃지 않도록 조심하세요."},
    {"name": "VII. THE CHARIOT (전차)", "icon": "🏎️", "keyword": "강한 추진력 · 장벽 돌파 · 확실한 승리", "overview": "두 마리의 스핑크스를 단단한 고삐로 통제하며 목표를 향해 돌진하는 전차의 카드입니다. 어떤 장애물도 뚫어낼 수 있는 강력한 투지와 승리의 기운이 감돕니다.", "action": "우유부단함을 버리고 과감하게 직진하세요. 미루던 결단을 내리고 집중할 때 승리를 쟁취합니다.", "caution": "속도에만 치중하다 주변 동료의 페이스를 놓치지 않도록 소통을 챙기세요."},
    {"name": "VIII. STRENGTH (힘)", "icon": "🦁", "keyword": "부드러운 카리스마 · 강인한 인내 · 내면의 통제", "overview": "사나운 사자를 완력 대신 온화한 사랑과 인내로 길들이는 여인의 카드입니다. 진정한 강함은 폭력이 아닌 부드러움과 내면의 자기 통제에서 나옴을 상징합니다.", "action": "갈등 상황에서 화를 내기보다 침착하고 성숙한 태도로 설득하세요. 반드시 상대를 감화시킵니다.", "caution": "감정을 무조건 억누르기만 하다가 속병이 나지 않도록 건강한 스트레스 해소법을 찾으세요."},
    {"name": "IX. THE HERMIT (은둔자)", "icon": "🏮", "keyword": "깊은 성찰 · 전문성 완성 · 진리의 등불", "overview": "어두운 산 정상에서 진리의 등불을 들고 묵묵히 길을 밝히는 은둔자의 카드입니다. 외로운 탐구의 시간을 거쳐 고도의 전문성과 통찰력을 완성하는 시기입니다.", "action": "불필요한 모임을 줄이고 조용히 혼자만의 시간을 가지며 공부나 기획을 깊이 파고드세요.", "caution": "세상과 지나치게 단절되어 고립되거나 타인의 조언을 완전히 무시하지 않도록 하세요."},
    {"name": "X. WHEEL OF FORTUNE (운명의 수레바퀴)", "icon": "🎡", "keyword": "기회의 전환점 · 대운의 흐름 · 숙명적 변화", "overview": "끊임없이 회전하며 계절의 변화를 만드는 거대한 운명의 수레바퀴 카드입니다. 정체되었던 흐름이 풀리고 예상치 못한 행운과 대반전의 기회가 다가오고 있습니다.", "action": "변화의 흐름을 거스르지 말고 유연하게 올라타세요. 우연한 만남이나 제안이 큰 기회가 됩니다.", "caution": "상황이 좋다고 자만하거나 방심하지 말고 운이 들어왔을 때 확실하게 결실을 챙겨두세요."},
    {"name": "XI. JUSTICE (정의)", "icon": "⚖️", "keyword": "공정한 판결 · 이성적 판단 · 균형과 계약", "overview": "한 손에는 저울을, 한 손에는 칼을 들고 엄정하게 균형을 잡는 정의의 카드입니다. 원인에 따른 명확한 결과가 따르며 공정한 법적/문서적 합의가 이뤄짐을 상징합니다.", "action": "감정에 치우치지 말고 객관적인 사실과 원칙에 입각하여 명확한 계약과 결정을 내리세요.", "caution": "너무 흑백논리로만 사람을 재단하여 주변에 냉정한 인상을 주지 않도록 배려하세요."},
    {"name": "XII. THE HANGED MAN (매달린 사람)", "icon": "🧗", "keyword": "새로운 관점 · 값진 희생 · 성장을 위한 멈춤", "overview": "나무에 거꾸로 매달려 있지만 머리 뒤로 후광이 빛나는 구도자의 카드입니다. 일시적인 정체와 희생을 통해 기존과 다른 완전히 새로운 시야를 얻게 됨을 뜻합니다.", "action": "지금 당장 일이 풀리지 않더라도 조급해하지 마세요. 발상의 전환을 통해 역발상 아이디어를 얻으세요.", "caution": "스스로를 지나치게 피해자로 만들며 무기력에 빠지지 않도록 마인드를 환기하세요."},
    {"name": "XIII. DEATH (죽음과 재생)", "icon": "🌅", "keyword": "과거의 종결 · 새로운 탄생 · 근본적 혁신", "overview": "낡은 것을 완전히 허물고 지평선 너머 찬란한 새 태양을 맞이하는 재생의 카드입니다. 낡은 습관, 비효율적인 관계를 끊어내야만 위대한 새 출발이 시작됩니다.", "action": "미련이 남은 과거의 짐을 단칼에 정리하세요. 비워내야만 새로운 행운이 그 자리를 채웁니다.", "caution": "변화가 두려워 끝난 인연이나 무의미한 일에 계속 집착하지 마세요."},
    {"name": "XIV. TEMPERANCE (절제)", "icon": "🏺", "keyword": "황금 밸런스 · 조화와 치유 · 부드러운 융합", "overview": "두 개의 컵 사이로 물을 조화롭게 따르며 기운을 순환시키는 천사의 카드입니다. 극단을 피하고 중용과 절제를 지킬 때 몸과 마음이 치유되고 일이 순조롭게 풀립니다.", "action": "일과 휴식, 지출과 저축의 균형을 맞추세요. 타협과 조율을 통해 최적의 합의점을 찾으세요.", "caution": "한쪽에 지나치게 과몰입하거나 과음, 과식 등 생활 리듬이 깨지지 않도록 유의하세요."},
    {"name": "XV. THE DEVIL (악마)", "icon": "⛓️", "keyword": "강한 집착 · 달콤한 유혹 · 결속의 사슬", "overview": "어둠 속에서 물질적 쾌락과 집착의 사슬로 사람을 묶어둔 악마의 카드입니다. 거부하기 힘든 강렬한 매력과 유혹이 다가오지만 통제력을 잃지 말아야 함을 경고합니다.", "action": "욕망과 야망을 긍정적인 추진력으로 바꾸어 집중하세요. 단기적인 쾌락 대신 실리를 챙기세요.", "caution": "과도한 중독, 충동적인 투자, 검증되지 않은 인간관계의 덫에 걸리지 않도록 경계하세요."},
    {"name": "XVI. THE TOWER (탑)", "icon": "⚡", "keyword": "돌발적 각성 · 환상의 붕괴 · 진실의 발견", "overview": "부실한 기초 위에 세워진 높은 탑이 번개를 맞아 무너지는 충격의 카드입니다. 거짓된 안정과 허상이 깨지며, 뼈아프지만 진짜 견고한 기초를 다시 세우게 됩니다.", "action": "예상치 못한 변수가 생기더라도 당황하지 마세요. 군더더기를 털어내고 리셋할 절호의 기회입니다.", "caution": "안전불감증을 경계하고 중요한 데이터 백업 및 건강 관리에 유의하세요."},
    {"name": "XVII. THE STAR (별)", "icon": "⭐", "keyword": "희망의 실마리 · 영감과 치유 · 밝은 비전", "overview": "어두운 밤하늘을 은은히 밝히는 찬란한 팔각 별과 생명수를 붓는 여신의 카드입니다. 오랜 고민 끝에 문제의 실마리가 풀리고 가슴 설레는 비전이 찾아옵니다.", "action": "마음의 평온을 찾고 영감을 주는 예술, 책을 접하세요. 번뜩이는 아이디어가 길잡이가 됩니다.", "caution": "이상에만 머물러 뜬구름을 잡지 않도록 오늘 당장 실천할 작은 루틴을 설정하세요."},
    {"name": "XVIII. THE MOON (달)", "icon": "🌙", "keyword": "불안의 극복 · 숨겨진 감정 · 직관적 감수성", "overview": "어두운 밤 달빛 아래 안개 낀 길을 바라보는 가재와 늑대의 카드입니다. 미래에 대한 막연한 불안과 착각이 들 수 있으나 내면의 직관을 믿고 나아가야 함을 뜻합니다.", "action": "실체 없는 두려움에 위축되지 마세요. 감정을 일기나 예술로 표현하며 멘탈을 정돈하세요.", "caution": "소문이나 오해에 휘둘리지 말고 객관적인 팩트가 확인될 때까지 결정을 유보하세요."},
    {"name": "XIX. THE SUN (태양)", "icon": "☀️", "keyword": "명쾌한 성공 · 기쁨과 활력 · 진실의 빛", "overview": "환한 태양빛 아래 해바라기 밭을 달리는 순수한 아이의 카드입니다. 어둠과 오해가 걷히고 모든 것이 명쾌하고 긍정적인 방향으로 결실을 맺는 최고의 길조입니다.", "action": "당당하게 당신의 존재감을 드러내세요. 밝은 미소와 긍정 에너지가 귀인을 부릅니다.", "caution": "숨길 것이 없는 투명한 기운이므로 솔직함은 지키되 보안 사항은 철저히 지키세요."},
    {"name": "XX. JUDGEMENT (심판)", "icon": "🎺", "keyword": "부활과 보상 · 결정적 소식 · 결실의 나팔", "overview": "하늘에서 천사가 나팔을 불며 지난 과거의 노력에 대해 정당한 보상을 내리는 부활의 카드입니다. 기다리던 합격 소식, 재회의 연락 등 기쁜 통보가 찾아옵니다.", "action": "결정적인 연락이나 기회가 왔을 때 주저 없이 잡으세요. 과거의 노력이 빛을 발합니다.", "caution": "과거의 실패 트라우마에 얽매여 다가온 황금 같은 기회를 놓치지 마세요."},
    {"name": "XXI. THE WORLD (세계)", "icon": "🌍", "keyword": "완벽한 완성 · 대단원의 막 · 글로벌 도약", "overview": "월계수 화환 한가운데에서 승리의 춤을 추는 여신의 카드입니다. 타로 여정의 최종 완성으로서 하나의 거대한 목표를 성공적으로 완수하고 더 넓은 세상으로 도약함을 상징합니다.", "action": "추진 중인 프로젝트를 깔끔하게 매듭짓고 성취의 기쁨을 누리세요. 다음 무대를 준비하세요.", "caution": "완성에 취해 자만에 빠지지 말고 겸손한 태도로 더 높은 다음 여정을 기획하세요."}
]

@app.get("/api/daily-tarot")
def get_daily_tarot():
    card = random.choice(TAROT_MAJOR_DECK)
    return card

@app.post("/api/health-fortune")
def calculate_health_fortune(req: HealthRequest):
    u_saju = calculate_saju(req.user_year, req.user_month, req.user_day, req.user_sijin)
    u_gan = u_saju["day_gan"]
    u_oheng = OHENG_MAP.get(u_gan, "목")

    oheng_organ_map = {
        "목": ("간(肝) · 담낭 · 신경계 · 시력", "눈의 피로, 어깨 결림, 만성 피로 및 스트레스성 신경 과민", "녹황색 채소, 매실, 결명자차, 브로콜리"),
        "화": ("심장(心) · 소장 · 혈관계 · 혈압", "가슴 두근거림, 열감, 불면증 및 혈압 변동", "토마토, 비트, 오미자차, 붉은 파프리카"),
        "토": ("비위(脾胃) · 소화기 · 위장 · 대사", "위장 장애, 소화 불량, 복부 팽만감 및 식후 피로", "단호박, 양배추, 마, 대추차, 생강차"),
        "금": ("폐(肺) · 대장 · 호흡기 · 피부", "기관지염, 환절기 비염, 피부 건조증 및 대장 과민", "도라지, 배, 연근, 무, 흰 목이버섯"),
        "수": ("신장(腎) · 방광 · 생식기 · 골격/허리", "허리 통증, 수족 냉증, 부종 및 하체 피로", "검은콩, 흑임자, 블루베리, 미역, 해조류")
    }

    target_organ, weak_symptoms, good_foods = oheng_organ_map.get(u_oheng, ("간/소화기", "피로 누적", "신선한 채소와 따뜻한 차"))

    report = f"""
<div class="space-y-4 text-xs text-slate-800 font-normal leading-relaxed">
  <div class="bg-brand-50 border border-brand-200 rounded-2xl p-4 text-center space-y-1">
    <div class="text-xs font-bold text-brand-950">🌿 {req.user_name} 님의 평생 체질 진단 & 건강 개운 리포트</div>
    <p class="text-[11px] text-brand-800 font-medium">선천적 취약 장기 진단과 신체 4대 핵심 영역별 평생 관리 솔루션</p>
  </div>

  <div class="space-y-2">
    <div class="flex items-center space-x-2 bg-[#F8FAF7] p-2.5 rounded-xl border-l-4 border-brand-600 font-bold text-brand-950 text-xs">
      <span>🩺</span><span>1. 타고난 오행 체질과 취약 장기 분석</span>
    </div>
    <div class="p-3.5 bg-slate-50/80 rounded-xl space-y-1 text-slate-700 font-medium text-[11px]">
      <div>• 선천적 관리 1순위 장기: <b class="text-brand-800">{target_organ}</b></div>
      <div>• 에너지 저하 시 나타나는 주요 신호: {weak_symptoms}</div>
    </div>
  </div>

  <div class="space-y-2">
    <div class="flex items-center space-x-2 bg-[#F8FAF7] p-2.5 rounded-xl border-l-4 border-brand-600 font-bold text-brand-950 text-xs">
      <span>💡</span><span>2. 신체 4대 핵심 영역별 평생 관리 솔루션</span>
    </div>
    <div class="space-y-2">
      <div class="bg-white p-3 rounded-xl border border-brand-100 shadow-2xs space-y-1">
        <div class="font-bold text-slate-900 text-[11px]">⚡ 피로 및 면역 관리</div>
        <p class="text-[11px] text-slate-600 font-normal">수면 1시간 전 스마트폰 사용을 줄이고, 주 2~3회 온욕(40도 15분)으로 체온을 올려 자율신경 밸런스를 유지하세요.</p>
      </div>
      <div class="bg-white p-3 rounded-xl border border-brand-100 shadow-2xs space-y-1">
        <div class="font-bold text-slate-900 text-[11px]">🍲 소화기 및 위장 관리</div>
        <p class="text-[11px] text-slate-600 font-normal">찬 음료를 멀리하고 식사 후 최소 10분간 가벼운 산책으로 토(土)의 비위 순환 기운을 돕는 것이 가장 좋습니다.</p>
      </div>
      <div class="bg-white p-3 rounded-xl border border-brand-100 shadow-2xs space-y-1">
        <div class="font-bold text-slate-900 text-[11px]">🦴 척추, 관절 및 골격계</div>
        <p class="text-[11px] text-slate-600 font-normal">기상 직후 가벼운 척추 롤링 스트레칭을 루틴화하고, 40대 이후부터는 체중 부하를 줄여주는 걷기나 수영을 권장합니다.</p>
      </div>
      <div class="bg-white p-3 rounded-xl border border-brand-100 shadow-2xs space-y-1">
        <div class="font-bold text-slate-900 text-[11px]">🧠 수면 리듬 및 멘탈 힐링</div>
        <p class="text-[11px] text-slate-600 font-normal">오전 중 15분 이상 자연 햇볕을 쬐어 멜라토닌 분비를 돕고, 침실에 은은한 라벤더·우디향을 두면 숙면에 큰 도움이 됩니다.</p>
      </div>
    </div>
  </div>

  <div class="space-y-2">
    <div class="flex items-center space-x-2 bg-[#F8FAF7] p-2.5 rounded-xl border-l-4 border-brand-600 font-bold text-brand-950 text-xs">
      <span>📅</span><span>3. 생애 주기별 건강 주의 구간</span>
    </div>
    <div class="p-3.5 bg-slate-50/80 rounded-xl space-y-1.5 text-slate-700 font-medium text-[11px]">
      <div>• <b>청장년기 (30~40대)</b>: 과로성 만성 피로와 위장 장애 관리 집중, 2년 주기 종합 검진 권장</div>
      <div>• <b>중노년기 (50대 이후)</b>: 심혈관계 및 관절 유연성 확보 필수, 주 3회 규칙적 유산소 운동</div>
      <div>• <b>계절별 주의 시기</b>: 일교차가 큰 환절기(봄/가을) 면역 관리가 1년 건강을 좌우합니다.</div>
    </div>
  </div>

  <div class="space-y-2">
    <div class="flex items-center space-x-2 bg-[#F8FAF7] p-2.5 rounded-xl border-l-4 border-brand-600 font-bold text-brand-950 text-xs">
      <span>🍵</span><span>4. 나를 살리는 보양 식단 & 맞춤 운동 처방</span>
    </div>
    <div class="p-3.5 bg-brand-50/70 border border-brand-200 rounded-xl space-y-1.5 text-slate-800 font-medium text-[11px]">
      <div>• <b>추천 보양 식재료</b>: <b class="text-brand-900">{good_foods}</b></div>
      <div>• <b>최적의 운동법</b>: 무리한 중량 운동보다 요가, 필라테스, 빠른 걷기, 수영 등 기혈 순환 운동</div>
      <div>• <b>행운의 힐링 컬러</b>: 포레스트 그린, 올리브 톤</div>
    </div>
  </div>
</div>
"""

    return {
        "score": 93,
        "report": report
    }

@app.post("/api/love-fortune")
def calculate_love_fortune(req: LoveReportRequest):
    u_saju = calculate_saju(req.user_year, req.user_month, req.user_day, req.user_sijin)
    u_gan = u_saju["day_gan"]
    u_ji = u_saju["pillars"]["day"][1]

    deep_status_diagnostics = {
        "솔로": (
            "🔍 [현재 솔로 상태 정밀 심리/환경 진단]\n"
            "• 현재 심리 상태: 새로운 만남을 원하지만 상처받을까 봐 마음의 문을 반쯤 닫아둔 상태입니다. 기준치가 은연중에 높아져 작은 단점도 크게 보기 쉽습니다.\n\n"
            "💡 [당장 이번 달 실행해야 할 3단계 현실 처방전]\n"
            "1. 만남 반경 확장: 기존 생활 동선에서 벗어나 운동, 소모임에 월 2회 참여하세요.\n"
            "2. 리액션 3초 법칙: 호감 가는 상대에게 눈을 맞추고 3초간 미소를 지어보세요.\n"
            "3. 완벽주의 내려놓기: 첫인상에서 100점을 찾으려 하지 말고 3번은 만나보세요."
        ),
        "썸/연애중": (
            "🔍 [현재 썸/연애중 상태 정밀 진단]\n"
            "• 현재 관계의 핵심 병목: 익숙해지며 초기의 긴장감이 줄고 사소한 말투나 연락 빈도에서 서운함이 축적되고 있습니다.\n\n"
            "💡 [관계를 깊은 결속/결혼으로 이끄는 3단계 처방전]\n"
            "1. 인정과 칭찬 먼저 하기: 상대방의 수고로움에 '고마워'라는 언어적 표현을 아끼지 마세요.\n"
            "2. 둘만의 미래 프로젝트 설정: 여행 계획 등 함께 달성할 목표를 세우세요.\n"
            "3. 나-전달법 화법: '왜 너는 그래?' 대신 '내 기분은 이랬어'로 소통하세요."
        ),
        "기혼": (
            "🔍 [현재 기혼 상태 정밀 진단]\n"
            "• 현재 가정의 에너지 흐름: 경제적 안정은 잡혔으나 로맨스보다 동지애와 책임감의 비중이 커져 대화가 사무적으로 변하기 쉽습니다.\n\n"
            "💡 [가정의 화목과 부부 금슬을 높이는 3단계 처방전]\n"
            "1. 주 1회 '둘만의 1시간' 확보: 가사/자녀 외에 서로의 감정을 나누는 차 한잔의 시간을 가지세요.\n"
            "2. 연애 시절 추억 환기: 예전에 자주 가던 장소를 다시 찾아보세요.\n"
            "3. 침실 풍수 정돈: 침대 머리 방향을 밝게 정돈하고 은은한 조명을 두세요."
        ),
        "재회희망": (
            "🔍 [현재 재회 희망 상태 정밀 진단]\n"
            "• 상대방과 본인의 기운: 상대방은 일상에 적응하며 방어벽을 세운 상태이며, 본인은 미련과 후회가 절정인 구간입니다.\n\n"
            "💡 [재회 확률을 끌어올리는 3단계 처방전]\n"
            "1. 침묵의 쿨다운 (최소 3~4주): 지금 매달리지 말고 연락을 끊고 SNS를 정돈하세요.\n"
            "2. 매력의 재구축: 외모 변화와 활력 있는 에너지로 호기심을 유발하세요.\n"
            "3. 명분 있는 연락: 실용적이고 부담 없는 핑계로 접근하세요."
        )
    }

    status_block = deep_status_diagnostics.get(req.love_status, "나를 소중히 여길 때 품격 있는 인연이 다가옵니다.")

    report = f"""
<div class="space-y-4 text-xs text-slate-800 font-normal leading-relaxed">
  <div class="bg-rose-50 border border-rose-200 rounded-2xl p-4 text-center space-y-1">
    <div class="text-xs font-bold text-rose-950">💖 {req.user_name} 님의 평생 애정/결혼운 정밀 감명서</div>
    <p class="text-[11px] text-rose-800 font-medium">타고난 배우자복과 현재 애정 상태 맞춤 실전 처방전</p>
  </div>

  <div class="space-y-2">
    <div class="flex items-center space-x-2 bg-[#F8FAF7] p-2.5 rounded-xl border-l-4 border-rose-500 font-bold text-rose-950 text-xs">
      <span>💍</span><span>1. 타고난 연애 기질과 도화/홍염살 분석</span>
    </div>
    <div class="p-3.5 bg-slate-50/80 rounded-xl text-slate-700 font-medium leading-relaxed">
      당신은 일간 '{u_gan}'의 고유한 매력과 일지 '{u_ji}'의 온화한 배우자궁을 타고났습니다. 한번 마음을 열면 깊은 헌신과 배려를 아끼지 않는 순정파 기질로, 상대방에게 안정감과 따뜻한 쉼터를 제공하는 최고의 연애/결혼 파트너입니다.
    </div>
  </div>

  <div class="space-y-2">
    <div class="flex items-center space-x-2 bg-[#F8FAF7] p-2.5 rounded-xl border-l-4 border-rose-500 font-bold text-rose-950 text-xs">
      <span>📍</span><span>2. 현재 상태 [{req.love_status}] 정밀 진단 & 처방전</span>
    </div>
    <div class="p-3.5 bg-slate-50/80 rounded-xl text-slate-700 font-medium whitespace-pre-line leading-relaxed">
      {status_block}
    </div>
  </div>

  <div class="space-y-2">
    <div class="flex items-center space-x-2 bg-[#F8FAF7] p-2.5 rounded-xl border-l-4 border-rose-500 font-bold text-rose-950 text-xs">
      <span>👑</span><span>3. 평생 나를 설레게 할 천생연분 띠 TOP 2</span>
    </div>
    <div class="p-3.5 bg-rose-50/60 border border-rose-200 rounded-xl space-y-1.5 text-slate-800 font-medium text-[11px]">
      <div>• 💖 <b>1순위 (영혼의 단짝)</b>: <b class="text-rose-700">양띠 (未) · 호랑이띠 (寅)</b> (대화 코드가 찰떡같이 통하는 최상 궁합)</div>
      <div>• 🌿 <b>2순위 (평온한 쉼터)</b>: <b class="text-rose-700">토끼띠 (卯) · 개띠 (戌)</b> (다정하게 가정을 지키는 안정 궁합)</div>
    </div>
  </div>
</div>
"""

    return {
        "score": 95,
        "report": report
    }

@app.post("/api/wealth-fortune")
def calculate_wealth_fortune(req: WealthReportRequest):
    u_saju = calculate_saju(req.user_year, req.user_month, req.user_day, req.user_sijin)
    u_gan = u_saju["day_gan"]

    deep_career_diagnostics = {
        "직장인": (
            "🔍 [현재 직장인 상태 재정 흐름 진단]\n"
            "• 현재 재정 병목: 고정 월급 의존으로 자산 증식 속도가 답답하며 소소한 소비로 목돈이 고이지 않는 흐름입니다.\n\n"
            "💡 [자산 점프를 위한 3단계 실전 솔루션]\n"
            "1. 강제 저축 시스템: 월급날 당일 수입의 45% 이상을 자동 이체하세요.\n"
            "2. 직무 전문성 레버리지: 업무 성과를 포트폴리오화하여 연봉 협상 실탄을 만드세요.\n"
            "3. 부동산 스터디: 실물 부동산 안목을 기르세요."
        ),
        "취준/이직": (
            "🔍 [현재 취준/이직 상태 재정 흐름 진단]\n"
            "• 현재 재정 병목: 수입 공백으로 불안감이 크며 조급함에 첫 단추를 잘못 끼울 위험이 있습니다.\n\n"
            "💡 [연봉 가치를 극대화하는 3단계 솔루션]\n"
            "1. 직무 전문성 환경 우선: 초봉 몇백만 원보다 커리어를 키울 환경을 택하세요.\n"
            "2. 이력서 정량화: 수치화된 성과와 기술을 첫 단락에 배치하세요.\n"
            "3. 규칙적 루틴: 9 to 6 준비 루틴을 직장인처럼 유지하세요."
        ),
        "사업자": (
            "🔍 [현재 사업자 상태 재정 흐름 진단]\n"
            "• 현재 재정 병목: 매출 대비 고정비 지출이 커서 순이익률이 낮거나 개인 자산화가 지연되고 있습니다.\n\n"
            "💡 [개인 자산 안전 전환 3단계 솔루션]\n"
            "1. 개인 명의 부동산 분산: 법인 잉여금을 개인 명의 실물 자산으로 옮겨두세요.\n"
            "2. 고정비 다이어트: 3개월 이상 기여 없는 비효율 비용을 정리하세요.\n"
            "3. 핵심 고객 락인: 매출의 80%를 만드는 VIP 리텐션을 구축하세요."
        ),
        "프리랜서": (
            "🔍 [현재 프리랜서 상태 재정 흐름 진단]\n"
            "• 현재 재정 병목: 프로젝트 수주에 따라 월별 수입 기복이 심해 장기 자산 설계가 어렵습니다.\n\n"
            "💡 [단가를 높이고 자동화 수익을 만드는 3단계 솔루션]\n"
            "1. 패키지형 서비스 전환: 단순 노동형 외주를 줄이고 기획 포함 고단가로 전환하세요.\n"
            "2. 디지털 지식 자산 구축: 지속 판매 상품을 만드세요.\n"
            "3. 6개월 비상자금 확보: 월 생활비 6배를 CMA에 예치하세요."
        )
    }

    career_block = deep_career_diagnostics.get(req.career_status, "안정적인 자산 파이프라인을 구축하세요.")

    report = f"""
<div class="space-y-4 text-xs text-slate-800 font-normal leading-relaxed">
  <div class="bg-brand-50 border border-brand-200 rounded-2xl p-4 text-center space-y-1">
    <div class="text-xs font-bold text-brand-950">💰 {req.user_name} 님의 평생 재물 그릇 & 부동산 자산운 리포트</div>
    <p class="text-[11px] text-brand-800 font-medium">타고난 재물 크기와 현재 직업 맞춤 자산 증식 로드맵</p>
  </div>

  <div class="space-y-2">
    <div class="flex items-center space-x-2 bg-[#F8FAF7] p-2.5 rounded-xl border-l-4 border-brand-600 font-bold text-brand-950 text-xs">
      <span>💎</span><span>1. 타고난 재물 그릇(財運)의 성격과 크기</span>
    </div>
    <div class="p-3.5 bg-slate-50/80 rounded-xl text-slate-700 font-medium leading-relaxed">
      당신은 새어 나가는 편재보다 차곡차곡 쌓여 거대한 자산이 되는 <b class="text-brand-800">정재(正財)</b>의 그릇을 타고났습니다. 현금 통장보다 문서나 부동산으로 묶어둘 때 부가 3배 이상 불어나는 자수성가형 부자 사주입니다.
    </div>
  </div>

  <div class="space-y-2">
    <div class="flex items-center space-x-2 bg-[#F8FAF7] p-2.5 rounded-xl border-l-4 border-brand-600 font-bold text-brand-950 text-xs">
      <span>📊</span><span>2. 현재 상태 [{req.career_status}] 재정 진단 & 처방전</span>
    </div>
    <div class="p-3.5 bg-slate-50/80 rounded-xl text-slate-700 font-medium whitespace-pre-line leading-relaxed">
      {career_block}
    </div>
  </div>

  <div class="space-y-2">
    <div class="flex items-center space-x-2 bg-[#F8FAF7] p-2.5 rounded-xl border-l-4 border-brand-600 font-bold text-brand-950 text-xs">
      <span>📈</span><span>3. 자산 포트폴리오 적합도 TOP 3</span>
    </div>
    <div class="p-3.5 bg-brand-50/60 border border-brand-200 rounded-xl space-y-1 text-slate-800 font-medium text-[11px]">
      <div>🥇 <b>1위 부동산/문서운</b>: 적합도 97% (강력 추천)</div>
      <div>🥈 <b>2위 우량주 가치투자</b>: 적합도 89%</div>
      <div>🥉 <b>3위 지식 기반 창업</b>: 적합도 82%</div>
      <div class="text-rose-600 font-bold pt-1">🚫 비추천: 단타 코인 / 파생상품 (손실 위험 94%)</div>
    </div>
  </div>
</div>
"""

    return {
        "score": 96,
        "report": report
    }

@app.post("/api/business-fortune")
def calculate_business_fortune(req: BusinessRequest):
    u_saju = calculate_saju(req.user_year, req.user_month, req.user_day, req.user_sijin)
    u_gan = u_saju["day_gan"]
    u_oheng = OHENG_MAP.get(u_gan, "목")

    item_map = {
        "목": "교육, 컨설팅, 친환경/바이오, 인테리어/가구, 출판/콘텐츠",
        "화": "IT/소프트웨어, F&B/외식업, 엔터테인먼트, 뷰티/패션, 온라인 마케팅",
        "토": "부동산 개발/중개, 공간대여/숙박, 건축자재, 농수산 유통, 프랜차이즈",
        "금": "금융/재무 컨설팅, 전문 법률/세무, 귀금속/하드웨어, 정밀기계, 물류",
        "수": "글로벌 무역, 이커머스 쇼핑몰, 주류/음료, 여행/레저, 데이터/AI 서비스"
    }

    report = f"""
<div class="space-y-4 text-xs text-slate-800 font-normal leading-relaxed">
  <div class="bg-amber-50 border border-amber-200 rounded-2xl p-4 text-center space-y-1">
    <div class="text-xs font-bold text-amber-950">🏢 {req.user_name} 님의 평생 사업운 & 대박 아이템 리포트</div>
    <p class="text-[11px] text-amber-800 font-medium">타고난 CEO 적성과 동업 성공 확률 및 대박 아이템 분석</p>
  </div>

  <div class="space-y-2">
    <div class="flex items-center space-x-2 bg-[#F8FAF7] p-2.5 rounded-xl border-l-4 border-amber-600 font-bold text-amber-950 text-xs">
      <span>👑</span><span>1. 사업가로서의 타고난 그릇 & CEO 유형</span>
    </div>
    <div class="p-3.5 bg-slate-50/80 rounded-xl text-slate-700 font-medium leading-relaxed">
      당신의 사주는 남 밑에 머물기보다 본인의 법인을 세워 주도할 때 큰돈을 만지는 <b class="text-amber-800">식신생재형 CEO</b> 사주입니다. 현장 실무와 기획에 능통하여 위기에서도 빠른 판단으로 활로를 뚫어내는 감각을 지녔습니다.
    </div>
  </div>

  <div class="space-y-2">
    <div class="flex items-center space-x-2 bg-[#F8FAF7] p-2.5 rounded-xl border-l-4 border-amber-600 font-bold text-amber-950 text-xs">
      <span>🚀</span><span>2. 나에게 돈을 벌어다 주는 대박 아이템 TOP 3</span>
    </div>
    <div class="p-3.5 bg-amber-50/60 border border-amber-200 rounded-xl space-y-1.5 text-slate-800 font-medium text-[11px]">
      <div>🥇 <b>1위 추천</b>: {item_map.get(u_oheng, '지식 서비스/이커머스')}</div>
      <div>🥈 <b>2위 추천</b>: B2B 전문 솔루션 및 외주 용역 비즈니스</div>
      <div>🥉 <b>3위 추천</b>: 구독 모델, 무인 매장 등 자동화 수익 파이프라인</div>
    </div>
  </div>
</div>
"""

    return {
        "score": 94,
        "report": report
    }

@app.post("/api/gunghap")
def calculate_gunghap(req: GunghapRequest):
    user_saju = calculate_saju(req.user_year, req.user_month, req.user_day, req.user_sijin)
    target_saju = calculate_saju(req.target_year, req.target_month, req.target_day, req.target_sijin)
    
    u_gan = user_saju["day_gan"]
    u_ji = user_saju["pillars"]["day"][1]
    t_gan = target_saju["day_gan"]
    t_ji = target_saju["pillars"]["day"][1]

    score = 82
    analysis_points = []

    if is_pair_in_set(CHEONGAN_HAP, u_gan, t_gan):
        score += 10
        analysis_points.append(f"• <b>천간 겉궁합 (98점)</b>: 천간합({u_gan}·{t_gan})으로 첫 만남부터 대화 코드가 완벽히 통하는 영적 유대를 지닙니다.")
    else:
        analysis_points.append(f"• <b>천간 겉궁합 (85점)</b>: 서로 다른 기질을 지녀 부족한 시야를 넓혀주는 페이스메이커 관계입니다.")

    if is_pair_in_set(JIJI_YUKHAP, u_ji, t_ji) or is_pair_in_set(JIJI_SAMHAP, u_ji, t_ji):
        score += 8
        analysis_points.append(f"• <b>지지 속궁합 (96점)</b>: 지지합({u_ji}·{t_ji})으로 단단히 결속되어 일상 라이프스타일에서 완벽한 안정감을 느낍니다.")
    elif is_pair_in_set(JIJI_CHUNG, u_ji, t_ji):
        score -= 5
        analysis_points.append(f"• <b>지지 속궁합 (78점)</b>: 일지상충({u_ji}·{t_ji})으로 자존심 대립이 있을 수 있으나 독립된 공간을 인정해 줄 때 매력이 배가됩니다.")
    else:
        analysis_points.append(f"• <b>지지 속궁합 (88점)</b>: 오랜 친구처럼 편안하고 온화한 일상을 공유하는 웰빙 궁합입니다.")

    score = min(max(score, 65), 99)

    report = f"""
<div class="space-y-4 text-xs text-slate-800 font-normal leading-relaxed">
  <div class="bg-rose-50 border border-rose-200 rounded-2xl p-4 text-center space-y-1">
    <div class="text-xs font-bold text-rose-950">❤️ {u_gan}(본인) 님과 {t_gan}({req.target_name}) 님의 정밀 궁합 감명서</div>
    <p class="text-[11px] text-rose-800 font-medium">정신적 겉궁합과 생활 속궁합 및 화해 솔루션</p>
  </div>

  <div class="space-y-2">
    <div class="flex items-center space-x-2 bg-[#F8FAF7] p-2.5 rounded-xl border-l-4 border-rose-500 font-bold text-rose-950 text-xs">
      <span>🔮</span><span>1. 겉궁합 & 속궁합 정밀 진단</span>
    </div>
    <div class="p-3.5 bg-slate-50/80 rounded-xl space-y-1.5 text-slate-700 font-medium text-[11px]">
      {"<br>".join(analysis_points)}
    </div>
  </div>

  <div class="space-y-2">
    <div class="flex items-center space-x-2 bg-[#F8FAF7] p-2.5 rounded-xl border-l-4 border-rose-500 font-bold text-rose-950 text-xs">
      <span>🔥</span><span>2. 갈등 발생 시 100% 즉효 화해 솔루션</span>
    </div>
    <div class="p-3.5 bg-rose-50/60 border border-rose-200 rounded-xl space-y-1 text-slate-800 font-medium text-[11px]">
      <div>1) 분위기 좋은 장소에서 얼굴을 마주 보고 대화하세요.</div>
      <div>2) '당신이 틀렸어' 대신 '내 기분은 이랬어'라는 공감 화법을 쓰면 3분 만에 풀립니다.</div>
    </div>
  </div>
</div>
"""

    return {
        "target_name": req.target_name,
        "score": score,
        "report": report
    }

@app.post("/api/heart")
def calculate_heart(req: HeartRequest):
    t_saju = calculate_saju(req.target_year, req.target_month, req.target_day)
    t_gan = t_saju["day_gan"]
    timing_months = [(datetime.now().month + i - 1) % 12 + 1 for i in [1, 3, 5]]
    
    report = f"""
<div class="space-y-4 text-xs text-slate-800 font-normal leading-relaxed">
  <div class="bg-purple-50 border border-purple-200 rounded-2xl p-4 text-center space-y-1">
    <div class="text-xs font-bold text-purple-950">💔 {req.target_name} 님의 속마음 & 재회 타이밍 리포트</div>
    <p class="text-[11px] text-purple-800 font-medium">상대방의 내면 감정과 먼저 연락 올 골든 타이밍 분석</p>
  </div>

  <div class="space-y-2">
    <div class="flex items-center space-x-2 bg-[#F8FAF7] p-2.5 rounded-xl border-l-4 border-purple-500 font-bold text-purple-950 text-xs">
      <span>💭</span><span>1. 지금 그 사람이 느끼는 진짜 속마음</span>
    </div>
    <div class="p-3.5 bg-slate-50/80 rounded-xl text-slate-700 font-medium leading-relaxed">
      상대방은 겉으로 단호해 보이지만 내면에는 자존심과 미련이 얽혀 있습니다. 당신과의 추억을 접할 때마다 강한 잔상을 느끼며, 방어벽을 깨고 먼저 다가와 주길 바라는 심리가 70% 이상 작동하고 있습니다.
    </div>
  </div>

  <div class="space-y-2">
    <div class="flex items-center space-x-2 bg-[#F8FAF7] p-2.5 rounded-xl border-l-4 border-purple-500 font-bold text-purple-950 text-xs">
      <span>📅</span><span>2. 먼저 연락 올 확률이 높은 결정적 시기</span>
    </div>
    <div class="p-3.5 bg-purple-50/60 border border-purple-200 rounded-xl space-y-1 text-slate-800 font-medium text-[11px]">
      <div>• <b>1차 골든 타이밍</b>: <b class="text-purple-700">{timing_months[0]}월 중순</b> (감정선이 가장 약해지는 보름달 전후)</div>
      <div>• <b>2차 재회 유력기</b>: <b class="text-purple-700">{timing_months[1]}월 초순</b> (당신의 빈자리를 뼈저리게 체감하는 시기)</div>
      <div>• <b>연락 가능성 지수</b>: <b class="text-rose-600">84% (매우 높음)</b></div>
    </div>
  </div>
</div>
"""
    
    return {
        "target_name": req.target_name,
        "score": 84,
        "report": report
    }

@app.post("/api/career-jump")
def calculate_career_jump(req: CareerRequest):
    u_saju = calculate_saju(req.user_year, req.user_month, req.user_day, req.user_sijin)
    
    report = f"""
<div class="space-y-4 text-xs text-slate-800 font-normal leading-relaxed">
  <div class="bg-sky-50 border border-sky-200 rounded-2xl p-4 text-center space-y-1">
    <div class="text-xs font-bold text-sky-950">💼 {req.user_name} 님의 올해 이직/취업 합격운 & 연봉 전략</div>
    <p class="text-[11px] text-sky-800 font-medium">명예 관성(官星) 기반 최적의 이직 분기 및 연봉 협상 팁</p>
  </div>

  <div class="space-y-2">
    <div class="flex items-center space-x-2 bg-[#F8FAF7] p-2.5 rounded-xl border-l-4 border-sky-500 font-bold text-sky-950 text-xs">
      <span>🎯</span><span>1. 2026년 이직/취업 합격운 매칭 지수</span>
    </div>
    <div class="p-3.5 bg-slate-50/80 rounded-xl text-slate-700 font-medium leading-relaxed">
      당신의 사주에는 조직 내 핵심 인재로 인정받는 <b class="text-sky-700">명예 관성(官星)</b>이 뚜렷합니다. 올해 연봉을 15~25% 이상 높여 이직할 최적의 분기가 열립니다.
    </div>
  </div>

  <div class="space-y-2">
    <div class="flex items-center space-x-2 bg-[#F8FAF7] p-2.5 rounded-xl border-l-4 border-sky-500 font-bold text-sky-950 text-xs">
      <span>📅</span><span>2. 연봉 협상 분기별 타임라인</span>
    </div>
    <div class="p-3.5 bg-sky-50/60 border border-sky-200 rounded-xl space-y-1 text-slate-800 font-medium text-[11px]">
      <div>• <b>1차 합격 골든존 [2분기(4~6월)]</b>: 헤드헌터 제안 및 경력직 이직 문서운 왕성</div>
      <div>• <b>2차 수확기 [3분기 후반~4분기]</b>: 15~25% 이상 점프할 수 있는 최종 협상 타이밍</div>
    </div>
  </div>
</div>
"""
    
    return {
        "score": 92,
        "report": report
    }