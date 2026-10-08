"""Tab 1 홈 '오늘의 이야기'·'시간대 팁'·'오늘 뭐 입지?'의 달하 에디터 카피와 조립 로직.

섹션 1  오늘의 이야기   3~4문장, 공백 포함 180~220자.  ~합니다 / ~해요 / ~해보세요 / ~인 법이죠 순서
        시간대 팁       오전·오후·저녁 1줄씩, 각 25~45자
섹션 3  오늘 뭐 입지?   행운 오행 컬러 기반 2-track — 베이직 / 포인트

집필 헌칙: 인사고과식 HR 어휘(annual_copy.find_banned)와 의학 표현(health_copy.find_medical)을 쓰지 않는다.
카피는 '결정론적 은행'이며 런타임에 LLM을 부르지 않는다. 같은 날·같은 사람이면 같은 글이 나오고,
날짜가 바뀌면 문장 변형이 돌아간다.

입력 신호는 daily.py 가 이미 계산한 값만 쓴다.
  lead  = overall["primary_domains"][0] → DOMAIN_TO_THEME → 5갈래(건강·휴식/애정·관계/일/지출·생활/균형)
  tone  = 오늘 일진과 원국 사이의 독립 관계 수(supportive vs tension) → lift / careful / calm
"""
from __future__ import annotations

from app.engine.services.annual_copy import DOMAIN_TO_THEME, find_banned, split_sentences, seed_from  # noqa: F401
from app.engine.services.health_copy import find_medical

COPY_VERSION = "dalha-daily-1"

SPEC = {
    "story_chars": (180, 220),
    "story_sentences": (3, 4),
    "tip_chars": (25, 45),
    "headline_max": 16,
}

LEADS = ("health_rest", "love_relation", "career", "spend_life", "balance")
TONES = ("lift", "careful", "calm")
SLOTS = (("morning", "오전"), ("afternoon", "오후"), ("evening", "저녁"))
ELEMENT_KO = {"木": "목", "火": "화", "土": "토", "金": "금", "水": "수"}


def find_flagged(text: str) -> list[str]:
    """HR 금기어 + 의학 표현."""
    return find_banned(text) + find_medical(text)


def sanitize(text: str) -> str:
    """엔진 밖(overall_narrative 등)에서 온 문단에서 금기 문장만 덜어낸다. 걸리지 않으면 원문 그대로."""
    if not text:
        return ""
    sentences = split_sentences(text)
    kept = [s for s in sentences if not find_flagged(s)]
    return text if len(kept) == len(sentences) else " ".join(kept)


def lead_key(primary_domains) -> str:
    for domain in primary_domains or ():
        theme = DOMAIN_TO_THEME.get(domain)
        if theme in LEADS:
            return theme
    return "balance"


def tone_key(supportive: int, tension: int) -> str:
    if supportive > tension:
        return "lift"
    if tension > supportive:
        return "careful"
    return "calm"


def slot_for_hour(hour: int | None) -> str | None:
    if hour is None:
        return None
    if 4 <= hour < 12:
        return "morning"
    if 12 <= hour < 18:
        return "afternoon"
    return "evening"


# ---------------------------------------------------------------------------
# 섹션 1 — 오늘의 이야기.  A(흐름, ~니다) · B(기류, ~요) · C(한 가지 행동, ~세요) · D(마무리, ~법이죠)
# ---------------------------------------------------------------------------
HEADLINES = {
    "health_rest": "몸도 마음도 느긋하게",
    "love_relation": "마음이 닿는 하루",
    "career": "차근차근 풀리는 하루",
    "spend_life": "살림을 가지런히",
    "balance": "고르게 흐르는 하루",
}
STORY_A = {
    "health_rest": (
        "오늘은 몸과 마음의 속도를 천천히 맞춰 가면서 하루의 결을 고르기에 좋은 날입니다.",
        "오늘은 무언가를 채우는 일보다 잠시 멈춰 쉬어 가는 일이 스스로에게 먼저 필요한 하루입니다.",
    ),
    "love_relation": (
        "오늘은 사람 사이의 온도가 유난히 또렷하게 눈에 들어오고 마음이 오가는 하루입니다.",
        "오늘은 건네는 말 한마디의 결이 하루 전체의 분위기를 부드럽게 바꿔 놓는 날입니다.",
    ),
    "career": (
        "오늘은 맡고 있는 일의 순서를 차분히 가다듬으며 하루의 흐름을 만들기에 좋은 하루입니다.",
        "오늘은 하던 일을 한 걸음만 더 끌고 가도 마음이 한결 가벼워지고 뿌듯해지는 하루입니다.",
    ),
    "spend_life": (
        "오늘은 생활 곳곳에 흩어진 작은 살림들을 하나씩 가지런히 챙겨 두기에 알맞은 하루입니다.",
        "오늘은 쓰고 싶은 마음과 모으고 싶은 마음 사이에서 균형을 잡는 일이 중요한 하루입니다.",
    ),
    "balance": (
        "오늘은 어느 한쪽으로 크게 기울지 않고 모든 일이 고르게 흘러가는 편안한 하루입니다.",
        "오늘은 유난히 튀는 일 없이 잔잔한 물결처럼 하루가 조용하고 편안하게 이어지는 날입니다.",
    ),
}
STORY_B = {
    "lift": (
        "여기에 오늘은 주변의 흐름이 뒤에서 가볍게 등을 밀어 주듯 도와주고 있어서 든든해요.",
        "게다가 오늘은 뜻밖의 인연이나 작은 도움이 자연스럽게 곁으로 따라붙어 힘이 되어 줘요.",
    ),
    "careful": (
        "다만 오늘은 사소한 엇갈림이 평소보다 조금 더 크게 느껴질 수 있어서 여유가 필요해요.",
        "다만 오늘은 마음이 앞서면 속도가 어긋나기 쉬우니 한 박자 천천히 늦춰 가도 괜찮아요.",
    ),
    "calm": (
        "굳이 속도를 낼 필요 없이 평소에 지켜 온 나만의 리듬을 그대로 따르면 충분하고 넉넉해요.",
        "큰 변화 없이 익숙한 리듬이 곁에서 편안하게 받쳐 주는 날이라 마음이 놓이고 든든해요.",
    ),
}
STORY_C = {
    "health_rest": (
        "점심을 먹은 뒤에는 잠깐 자리에서 일어나 바깥 공기를 쐬며 숨을 고르고 와 보세요.",
        "오늘 하루 중 단 십 분만은 아무것도 하지 않고 창밖을 보며 멍하니 편안하게 쉬어 보세요.",
    ),
    "love_relation": (
        "문득 안부가 궁금했던 사람에게 부담 없는 짧은 메시지를 먼저 가볍게 한 줄 보내 보세요.",
        "고마웠던 사람에게 고맙다는 말을 한 줄이라도 정성껏 적어서 따뜻하게 건네 보세요.",
    ),
    "career": (
        "오늘 해야 할 일 중에서 가장 가벼운 것 하나부터 먼저 끝내며 시동을 걸어 보세요.",
        "오늘 할 일을 딱 세 가지로만 좁혀 두고 하나씩 차례대로 천천히 마음 편히 해 보세요.",
    ),
    "spend_life": (
        "오늘 쓴 돈과 쓰고 싶었던 마음을 저녁에 수첩이나 메모장에 한 줄로만 가볍게 적어 보세요.",
        "집 안에서 가장 어수선하게 느껴지는 한 곳을 골라 십 분만 말끔히 정리해 보세요.",
    ),
    "balance": (
        "평소에 즐겨 하던 일상의 루틴을 오늘도 그대로 편안하고 느긋하게 이어 가 보세요.",
        "좋아하는 음악을 한 곡 틀어 두고 오늘 하루를 느긋하고 여유롭게 시작해 보세요.",
    ),
}
STORY_D = {
    "lift": (
        "흐름이 좋을 때일수록 여유 한 줌을 함께 챙겨 두는 것이 오래도록 이어지는 법이죠.",
        "좋은 바람은 힘을 빼고 가볍게 올라탈수록 더 멀리까지 편안하게 데려다주는 법이죠.",
    ),
    "careful": (
        "서두르지 않고 한 박자 쉬어 가는 것이 결국에는 가장 빠르고 안전한 길인 법이죠.",
        "조심스러운 날일수록 작은 확인 하나가 나중에 큰 안심으로 돌아오곤 하는 법이죠.",
    ),
    "calm": (
        "잔잔한 날에 쌓은 작은 습관들이 차곡차곡 모여 한 해의 결을 만들어 가는 법이죠.",
        "평범한 하루를 정성껏 보내는 마음이 결국 내일을 지탱하는 가장 단단한 힘이 되는 법이죠.",
    ),
}


def _pick(pool, seed: int, shift: int):
    return pool[(seed >> shift) % len(pool)]


def compose_story(lead: str, tone: str, seed: int) -> dict:
    lead = lead if lead in LEADS else "balance"
    tone = tone if tone in TONES else "calm"
    sentences = [
        _pick(STORY_A[lead], seed, 0), _pick(STORY_B[tone], seed, 1),
        _pick(STORY_C[lead], seed, 2), _pick(STORY_D[tone], seed, 3),
    ]
    body = " ".join(sentences)
    return dict(headline=HEADLINES[lead], body=body, char_count=len(body),
                sentence_count=len(sentences), lead=lead, tone=tone)


# ---------------------------------------------------------------------------
# 시간대 팁.  lead × slot × 2변형, 각 25~45자 한 줄.
# ---------------------------------------------------------------------------
TIPS = {
    "health_rest": {
        "morning": ("일어나자마자 물 한 잔을 천천히 마시며 하루를 열어 보세요.",
                    "창문을 열고 숨을 크게 세 번 쉬며 아침을 시작해요."),
        "afternoon": ("점심 뒤 십 분은 휴대폰을 내려놓고 눈을 쉬게 해 주세요.",
                      "오후에는 자리에서 일어나 가볍게 걸으며 머리를 식혀요."),
        "evening": ("저녁엔 조명을 낮추고 따뜻한 차 한 잔으로 마무리해 보세요.",
                    "잠들기 한 시간 전부터는 화면을 줄이고 느긋하게 보내요."),
    },
    "love_relation": {
        "morning": ("출근길에 마음이 가는 사람에게 짧은 안부를 보내 보세요.",
                    "아침 인사를 평소보다 한 톤 밝게 건네 봐요."),
        "afternoon": ("오후에는 대화에서 듣는 시간을 조금 더 길게 가져 보세요.",
                      "점심 자리에서 상대의 이야기를 먼저 물어봐요."),
        "evening": ("저녁에는 가까운 사람과 오늘 좋았던 일을 하나씩 나눠 봐요.",
                    "하루를 마치며 고마웠던 사람 한 명을 떠올려 보세요."),
    },
    "career": {
        "morning": ("아침에 오늘 할 일 세 가지를 종이에 적어 보세요.",
                    "하루를 열며 가장 먼저 할 일 하나만 정해 두어요."),
        "afternoon": ("오후에는 어려운 일 한 가지를 조용히 풀어 보세요.",
                      "중간에 한 번은 책상 위를 정리하고 숨을 골라요."),
        "evening": ("저녁에는 내일 아침에 할 첫 일을 한 줄로 적어 두세요.",
                    "하루를 마치며 오늘 해낸 일 한 가지를 떠올려 봐요."),
    },
    "spend_life": {
        "morning": ("아침에 오늘 쓸 곳을 가볍게 떠올리고 하루를 시작해요.",
                    "집을 나서기 전 가방과 지갑을 한 번 정돈해 보세요."),
        "afternoon": ("오후에는 사고 싶던 물건을 하루만 더 담아 두어 보세요.",
                      "점심에는 오늘의 기분에 맞는 메뉴를 천천히 골라요."),
        "evening": ("저녁에는 오늘 쓴 내역을 한 줄씩 적으며 돌아보세요.",
                    "자기 전 내일 입을 옷과 챙길 것을 미리 놓아 둬요."),
    },
    "balance": {
        "morning": ("평소처럼 좋아하는 음료 한 잔으로 아침을 열어 보세요.",
                    "오늘은 출근길 풍경을 조금 더 천천히 눈에 담아요."),
        "afternoon": ("오후에 짧은 산책으로 기분을 가볍게 환기해 보세요.",
                      "잠깐 좋아하는 노래를 한 곡 들으며 쉬어 가요."),
        "evening": ("저녁에는 하루를 돌아보며 따뜻한 샤워로 마무리해요.",
                    "오늘 하루도 잘 지냈다고 스스로에게 말해 보세요."),
    },
}


def compose_tips(lead: str, seed: int, hour: int | None = None) -> list[dict]:
    lead = lead if lead in LEADS else "balance"
    now = slot_for_hour(hour)
    out = []
    for i, (slot, label) in enumerate(SLOTS):
        text = _pick(TIPS[lead][slot], seed, 4 + i)
        out.append(dict(slot=slot, label=label, text=text, is_now=(slot == now)))
    return out


# ---------------------------------------------------------------------------
# 섹션 3 — 오늘 뭐 입지? 행운 오행 컬러 2-track.  (색, 옷) / (포인트 색, 포인트 소품)
#   색은 daily.py 의 _ELEMENT_GUIDE 색상과 같은 계열. 성별에 치우치지 않는 품목만 쓴다.
# ---------------------------------------------------------------------------
OUTFIT = {
    "木": ("올리브 그린", "면 셔츠나 니트", "청록", "스카프나 양말"),
    "火": ("소프트 코랄", "니트나 티셔츠", "레드", "양말이나 키링"),
    "土": ("베이지", "니트나 코튼 팬츠", "브라운", "벨트나 가죽 소품"),
    "金": ("화이트", "셔츠나 티셔츠", "실버", "시계나 반지"),
    "水": ("네이비", "재킷이나 슬랙스", "블랙", "가방이나 모자"),
}


def compose_outfit(element: str) -> dict:
    key = element if element in OUTFIT else "土"
    color, garment, p_color, p_item = OUTFIT[key]
    ko = ELEMENT_KO[key]
    return dict(
        element=key,
        caption=f"오늘의 컬러는 {ko}({key}) 기운에서 가져왔어요.",
        basic=dict(label="베이직", color=color,
                   text=f"{color} 톤의 {garment} 한 벌이면 하루가 편안하게 맞아 들어요."),
        point=dict(label="포인트", color=p_color,
                   text=f"포인트는 {p_color}빛 {p_item} 하나면 충분해요."),
    )
