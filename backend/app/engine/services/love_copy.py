"""애정·관계 테마운(4단 구조)의 달하 에디터 카피와 조립 로직.

1단 소통 기질 진단 (무료)  3문장
2단 관계 습관의 함정 (무료)  박스 2개, 각 50~70자
────────── 페이월 ──────────
잘 맞는 사람·부딪히기 쉬운 사람 (유료)  일지 육합·충 (11/06 추가)
3단 관계 타이밍 (유료)  핵심 변곡점 2~3개 월, 각 50~70자
지금의 사랑 (유료)  솔로·썸 칸 / 연애 중이거나 부부 칸 (11/06 추가)
4단 다정한 관계 3원칙 (유료)  불렛 3개, 각 40~50자

연애 상태는 고르지 않는다(11/04 정오님). status 인자는 옛 호출 호환용으로만 받고 문장에 쓰지 않는다.
설계: 프로젝트 문서 claude/love-expansion-design-2026-11-06.md

집필 헌칙 (절대)
- 이별·이혼·외도·결혼 시기 같은 극단적이거나 미래를 단정하는 표현은 쓰지 않는다.
  tests/test_love.py 가 은행 전체를 find_sensitive 로 전수 검사하고,
  love.py 는 엔진 밖에서 온 문장에도 같은 필터를 한 번 더 건다.
- 2단 경고는 상대나 외부 사건이 아니라 '내가 관계 속에서 반복하는 습관'만 짚는다.
- 월별 문장은 사건 예측이 아니라 '마음을 나누기 좋은 / 천천히 이야기할' 방향 제시다.

월별 점수 계산과 변곡점 선택은 career_copy 의 것을 그대로 쓴다(세 테마가 같은 규칙).
세 번째 테마(건강)까지 만든 뒤 theme_common 으로 옮기는 편이 낫다.
"""
from __future__ import annotations

import re

from app.engine.services.annual_copy import split_sentences, find_banned
from app.engine.services.career_copy import MODE_SCORE, choose_inflections  # noqa: F401  (love.py 가 사용)

COPY_VERSION = "dalha-love-2"
PRICE_KRW = 2900

SPEC = {
    "tier1_chars": (120, 200),
    "tier1_sentences": (3, 3),
    "tier2_chars": (50, 70),
    "tier3_months": (2, 3),
    "tier3_chars": (50, 70),
    "tier4_chars": (40, 50),
    "headline_max": 16,
    "trap_title_max": 12,
}

DEFAULT_STATUS = "솔로"
STATUSES = ("솔로", "썸/짝사랑", "연애중", "기혼")

# ---------------------------------------------------------------------------
# 민감 표현 필터
# ---------------------------------------------------------------------------
_SENSITIVE_SOURCES = (
    r"이별", r"이혼", r"별거", r"외도", r"불륜", r"바람기", r"바람\s*(?:을|이)?\s*피",
    r"결별", r"파혼", r"재혼", r"헤어\s*(?:지|질|져|졌|짐)", r"결혼", r"혼인", r"배신",
)
SENSITIVE_PATTERNS = tuple(re.compile(p) for p in _SENSITIVE_SOURCES)


def find_sensitive(text: str) -> list[str]:
    found = []
    for pattern in SENSITIVE_PATTERNS:
        m = pattern.search(text or "")
        if m:
            found.append(m.group(0))
    return found


def find_flagged(text: str) -> list[str]:
    """HR 금기어 + 민감 표현 둘 다."""
    return find_banned(text) + find_sensitive(text)


def sanitize(text: str) -> str:
    """엔진 밖에서 온 문단에서 금기어/민감 표현이 든 문장만 덜어낸다. 걸리지 않으면 원문 그대로."""
    if not text:
        return ""
    sentences = split_sentences(text)
    kept = [s for s in sentences if not find_flagged(s)]
    return text if len(kept) == len(sentences) else " ".join(kept)


# ---------------------------------------------------------------------------
# 줄기 (십신 → 애정 표현·소통 기질)
# ---------------------------------------------------------------------------
GROUPS = ("trust", "reality", "independence", "expression", "care", "balanced")
GROUP_OF_TEN_GOD = {
    "direct_officer": "trust", "seven_killings": "trust",
    "direct_wealth": "reality", "indirect_wealth": "reality",
    "peer": "independence", "rob_wealth": "independence",
    "eating_god": "expression", "hurting_officer": "expression",
    "direct_resource": "care", "indirect_resource": "care",
}


def lead_group(counts: dict) -> str:
    totals = {g: 0 for g in GROUPS if g != "balanced"}
    for god, n in counts.items():
        g = GROUP_OF_TEN_GOD.get(god)
        if g:
            totals[g] += n
    best = max(totals, key=totals.get)   # 동률이면 GROUPS 순서가 앞선 줄기
    return best if totals[best] else "balanced"


HEADLINES = {
    "trust": "믿음으로 마음을 여는 사람",
    "reality": "일상으로 사랑을 건네는 사람",
    "independence": "거리를 존중하는 사랑",
    "expression": "말로 온기를 전하는 사람",
    "care": "귀 기울여 마음 여는 사람",
    "balanced": "두루 맞춰 가는 사람",
}

# 1단: A(기질, ~니다) · B(표현 방식, ~요) · C(지금 상태, ~니다) · D(마무리, ~법이죠)
TIER1 = {
    "trust": {
        "A": "관계에서도 책임과 신뢰의 기준이 분명할 때 마음을 열고 깊어지는 애정 기질의 사주입니다.",
        "B": "약속을 지키고 지켜지는 모습에서 안정감을 느끼는 만큼 사랑을 말보다 태도로 보여 주는 편이에요.",
        "D": "진중한 마음이 시간이 쌓일수록 가장 깊은 다정함이 되어 주는 법이죠.",
    },
    "reality": {
        "A": "말뿐인 호감보다 시간과 생활을 실제로 나누는 일에서 사랑을 느끼고 표현하는 사주입니다.",
        "B": "함께 밥을 먹고 일정을 맞추는 사소한 순간에 마음이 쌓이는 현실적인 다정함이 있어요.",
        "D": "작은 생활의 배려가 차곡차곡 모여 큰 안정이 되어 주는 법이죠.",
    },
    "independence": {
        "A": "가까워져도 각자의 선택과 공간을 존중할 때 마음이 편안해지는 애정 기질의 사주입니다.",
        "B": "함께 있는 시간만큼 혼자 숨 쉬는 시간이 있어야 사랑이 오래 건강하게 이어지는 편이에요.",
        "D": "서로의 자리를 지켜 주는 거리감이 때로는 가장 깊은 신뢰가 되어 주는 법이죠.",
    },
    "expression": {
        "A": "느낀 것을 말과 행동으로 자연스럽게 풀어내며 분위기를 부드럽게 만드는 소통 기질의 사주입니다.",
        "B": "편안한 대화와 일상의 즐거움을 함께 나눌 때 관계가 가장 환하게 피어나는 편이에요.",
        "D": "솔직한 표현이 따뜻하게 전해질 때 마음의 거리가 가장 빠르게 줄어드는 법이죠.",
    },
    "care": {
        "A": "상대의 말을 충분히 듣고 헤아리며 천천히 믿음을 쌓아 가는 다정한 기질의 사주입니다.",
        "B": "서두르지 않고 충분히 이해한 뒤에 마음을 여는 만큼 한번 맺은 인연을 오래 아끼는 편이에요.",
        "D": "귀 기울이는 마음이 어떤 말보다 깊은 위로가 되어 주는 법이죠.",
    },
    "balanced": {
        "A": "한쪽으로 크게 쏠리기보다 여러 마음의 결이 고르게 섞여 상대에 맞춰 표현을 바꾸는 사주입니다.",
        "B": "상대에게 맞추는 데는 능숙하지만 내가 정말 원하는 관계의 모습을 말하는 일이 숙제예요.",
        "D": "두루 살피는 섬세함이 때로는 관계의 가장 큰 힘이 되어 주는 법이죠.",
    },
}
# 2단: 내가 반복하는 관계 습관. 상대 탓·외부 사건은 쓰지 않는다. (제목 ≤12자 + 50~70자)
TRAPS = {
    "trust": (
        ("기준을 앞세우기", "내가 세운 기준을 끝까지 지키려다 보니, 마음은 깊은데도 표현은 딱딱해지는 일이 반복돼요."),
        ("괜찮은 척 넘기기", "서운한 일이 생겨도 괜찮은 척 넘기다가, 쌓인 마음이 한꺼번에 차가운 태도로 나오곤 해요."),
        ("혼자 짊어지기", "관계의 무게를 혼자 짊어지려다 보니, 위로나 도움을 청하는 일이 늘 한발 늦어지는 편이에요."),
    ),
    "reality": (
        ("행동으로만 말하기", "마음은 챙김과 시간으로 표현하면서 말로는 아끼다 보니, 사랑이 충분히 전해지지 않는 때가 있어요."),
        ("계산이 앞서기", "주고받은 것을 마음속으로 가만히 따지다 보면, 다정한 순간에도 거리를 두게 되는 일이 있어요."),
        ("일정이 먼저", "바쁜 일정을 먼저 챙기다 보면 가까운 사람과의 시간이 자꾸 뒤로 밀려서 아쉬움이 쌓이곤 해요."),
    ),
    "independence": (
        ("혼자 정하기", "관계의 중요한 결정도 내 속도로 먼저 정해 버려서, 함께하는 사람이 소외감을 느끼게 될 때가 있어요."),
        ("한 걸음 물러서기", "가까워질수록 숨이 막힌다고 느껴 한 걸음 물러서다가, 마음이 식은 것 같다는 오해를 사곤 해요."),
        ("이기고 싶은 마음", "의견이 갈릴 때 이기고 싶은 마음이 올라와, 대화가 이야기가 아닌 승부처럼 흐르기도 해요."),
    ),
    "expression": (
        ("말이 앞서기", "느낀 것을 곧바로 말하다 보니 표현의 온도가 거칠어져서, 좋은 마음이 날카롭게 들릴 때가 있어요."),
        ("농담으로 넘기기", "진지한 이야기가 부담스러워 농담으로 흘리다가, 정작 중요한 속마음이 전해지지 않기도 해요."),
        ("기대를 말하지 않기", "바라는 점은 눈치로 알아주길 기다리다가, 끝내 말하지 못한 서운함이 속에 쌓이는 일이 반복돼요."),
    ),
    "care": (
        ("혼자 해석하기", "상대의 말과 표정을 오래 곱씹다가, 확인하지 않은 생각을 사실처럼 믿게 되는 일이 있어요."),
        ("맞추다 지치기", "상대의 말을 충분히 들어 주느라 내 이야기는 뒤로 미루다가, 마음이 조용히 지쳐 가곤 해요."),
        ("확신을 기다리기", "충분히 확신이 설 때까지 마음을 표현하지 않고 기다리다가, 좋은 때가 슬며시 지나가기도 해요."),
    ),
    "balanced": (
        ("맞춰 주기만 하기", "상대에게 잘 맞추다 보니, 내가 정말 원하는 것을 말할 때를 자꾸 놓치는 일이 되풀이돼요."),
        ("눈치 보기", "상대의 기분을 먼저 살피느라 솔직한 의견은 속으로만 삼켜 버리는 날이 점점 많아지곤 해요."),
        ("애매하게 두기", "좋고 싫음을 분명히 하지 않고 두루뭉술하게 두다가, 서로의 기대가 조금씩 엇갈리기도 해요."),
    ),
}

# 3단: 월 문장 (kind × status). 한 해 최대 3개월만 쓰므로 종류별 3개면 겹치지 않는다.
KIND_LABEL = {"opportunity": "마음이 잘 통하는 달", "caution": "천천히 나눌 달"}
MONTH_TEXT = {
    "opportunity": (
        "마음을 표현하기에 분위기가 부드러운 달이라, 미뤄 둔 안부나 고마운 말을 먼저 건네 보기 좋아요.",
        "대화가 자연스럽게 이어지기 쉬운 달이라, 새로운 자리나 함께하는 약속을 가볍게 잡아 보세요.",
        "주변 사람과의 대화가 따뜻하게 이어지는 달이라, 만나자는 제안에 열린 마음으로 답해 보세요.",
    ),
    "caution": (
        "마음이 앞서기 쉬운 달이라, 상대의 반응을 혼자 해석하지 말고 한 번 더 편하게 물어보세요.",
        "기대와 현실이 엇갈리기 쉬운 달이니, 서운한 일은 그 자리에서 결론 내지 말고 하루 묵혀 보세요.",
        "예민함이 커지기 쉬운 달이라, 중요한 이야기는 컨디션이 좋은 때를 골라 차분히 시작해 보세요.",
    ),
}
NO_INFLECTION = (
    "앞으로 12개월은 유난히 갈리는 달이 많지 않아요. 잔잔하게 이어지는 시기이니 달마다 안부와 대화를 고르게 나눠 보세요."
)

# 4단: 다정한 관계 3원칙 = 줄기 2 + 상태 1. 각 40~50자.
GROUP_BULLETS = {
    "trust": (
        "기대하는 점 하나를 이번 주 안에 부드러운 말투로 상대에게 먼저 꺼내 보세요.",
        "서운한 일이 생기면 쌓아 두지 말고 그날 안에 한 문장으로 마음을 전해 보세요.",
    ),
    "reality": (
        "행동으로 챙기는 마음에 더해, 고마운 마음을 한 문장의 말로도 이번 주에 전해 보세요.",
        "함께하는 시간은 달력에 먼저 적어 두고, 다른 일정보다 앞서서 꼭 지켜 보세요.",
    ),
    "independence": (
        "함께 걸린 중요한 결정은 정하기 전에 상대의 생각을 먼저 물어보는 시간을 가져 보세요.",
        "혼자 쉬고 싶은 마음이 들 때는 언제쯤 돌아올지 상대에게 먼저 알려 주세요.",
    ),
    "expression": (
        "하고 싶은 말은 한 번 소리 내어 읽어 본 뒤에 부드러운 말투로 전해 보세요.",
        "진지한 이야기는 웃음으로 넘기지 말고 짧게라도 끝까지 이어서 해 보세요.",
    ),
    "care": (
        "궁금한 점은 혼자 짐작하지 말고 가벼운 말투로 한 번 물어서 확인해 보세요.",
        "내 이야기도 하루에 한 가지씩은 내가 먼저 꺼내 보는 연습을 해 보세요.",
    ),
    "balanced": (
        "오늘 하루 내가 정말 원했던 것이 무엇인지 저녁에 한 줄로 적어 보세요.",
        "좋고 싫음은 작은 일부터 시작해서 한 문장으로 분명하고 다정하게 말해 보세요.",
    ),
}
COMMON_BULLET = "중요한 기대와 앞으로의 계획은 혼자 짐작하지 말고 말로 한 번 확인해 보세요."

# ---------------------------------------------------------------------------
# 잘 맞는 사람·부딪히기 쉬운 사람 (11/06): 일지(가까운 관계 자리)의 육합·충.
# 성별로 배우자 별을 정하지 않는다. 상대는 행동으로 쓴다(10/30). 띠 표기는 하지 않는다(11/06 정오님).
# 지지별 사람 묘사는 지지 성향의 통용 해석을 생활 말로 옮긴 편집 카피다.
# ---------------------------------------------------------------------------
BRANCH_PERSON = {
    "子": "말수는 적어도 생각이 깊고 이야기를 끝까지 들어 주는 사람",
    "丑": "느려 보여도 맡은 일은 끝까지 해내는 성실한 사람",
    "寅": "새로운 일을 먼저 시작하고 앞장서는 사람",
    "卯": "부드럽게 맞춰 주면서도 자기 일을 꾸준히 키워 가는 사람",
    "辰": "여러 일을 한꺼번에 챙기고 큰 그림부터 그리는 사람",
    "巳": "눈치가 빠르고 말과 판단이 빠른 사람",
    "午": "밝고 솔직해서 좋고 싫음을 바로 드러내는 사람",
    "未": "정이 많고 주변 사람을 살뜰히 챙기는 사람",
    "申": "결정이 빠르고 직접 움직여서 일을 해결하는 사람",
    "酉": "깔끔하고 기준이 분명해서 아닌 건 아니라고 말하는 사람",
    "戌": "의리가 있고 한번 맺은 관계를 오래 지키는 사람",
    "亥": "너그럽고 속이 깊어서 상대를 있는 그대로 받아 주는 사람",
}
MATCH_HEADING = "나와 잘 맞는 사람, 부딪히기 쉬운 사람"
MATCH_GOOD_TITLE = "잘 맞는 사람"
MATCH_GOOD = ("{name}님과 잘 맞는 사람은 {person}이에요. "
              "{name}님의 가까운 관계 자리와 합이 되는 기운이라, 함께 있으면 애쓰지 않아도 손발이 잘 맞아요.")
MATCH_BAD_TITLE = "부딪히기 쉬운 사람"
MATCH_BAD = ("{name}님과 자주 부딪히기 쉬운 사람은 {person}이에요. "
             "가까운 관계 자리와 맞부딪히는 기운이라 생활 방식이나 결정 속도가 엇갈리기 쉬워요. "
             "의견이 갈리면 그 자리에서 결론 내지 말고 하루 묵혀서 다시 이야기해 보세요.")

# ---------------------------------------------------------------------------
# 지금의 사랑 (11/06): 두 칸을 함께 보여 준다.
#   솔로·썸 칸 = 인연이 들어오는 길(지금 대운 + 앞으로 12개월 세운의 십성) + 도화 달
#   연애·부부 칸 = 일지와 합이 되는 달 / 충이 되는 달 + 이번 대운의 대화법
# 십성별 만남 자리는 명리 해설서에서 널리 쓰는 해석 관례다(고전 원문의 단일 규칙은 아님).
# '결혼'은 민감어 필터에 걸리므로 '부부'로 쓴다.
# ---------------------------------------------------------------------------
NOW_HEADING = "지금의 사랑"
NOW_SINGLE_TITLE = "솔로·썸이라면"
NOW_COUPLE_TITLE = "연애 중이거나 부부라면"
GOD_GROUP = {
    "peer": "비겁", "rob_wealth": "비겁", "eating_god": "식상", "hurting_officer": "식상",
    "direct_wealth": "재성", "indirect_wealth": "재성", "direct_officer": "관성",
    "seven_killings": "관성", "direct_resource": "인성", "indirect_resource": "인성",
}
MEET_PATH = {
    "비겁": "친구 모임이나 동호회처럼 또래가 모이는 자리",
    "식상": "취미나 배움 모임처럼 내가 하는 일을 보여 주는 자리",
    "재성": "일하며 자주 오가는 곳이나 생활 동선 안",
    "관성": "직장이나 공적인 자리, 격식 있는 소개",
    "인성": "윗사람이나 가족, 오래 알고 지낸 사람의 소개",
}
NOW_PATH_SAME = "지금은 {path}에서 인연이 들어오기 쉬워요. 이번 10년과 앞으로 12개월의 흐름이 같은 쪽을 가리키고 있어요."
NOW_PATH_TWO = "이번 10년은 {cycle}에서 인연이 들어오기 쉬워요. 앞으로 12개월은 {year}도 열려 있어요."
NOW_PEACH = "{month}은 도화가 들어 새로운 사람의 눈에 띄기 쉬운 달이에요."
NOW_PEACH_COMBO = "{month}은 도화가 들고 가까운 관계 자리와도 합이 되는 달이라, 새로운 사람을 만나기 가장 좋은 달이에요."
NOW_COUPLE_MONTHS = "{good}은 두 사람 사이가 한결 가까워지기 좋은 달이고, {bad}은 사소한 일로 부딪히기 쉬운 달이에요."
TALK = {
    "비겁": "각자의 시간을 지켜 주면서 함께할 일을 따로 정해 두는 게 잘 맞아요",
    "식상": "하고 싶은 말은 참지 말되, 말투를 한 번 고른 뒤 꺼내는 게 잘 맞아요",
    "재성": "돈과 시간을 쓰는 방식을 미리 같이 정해 두는 게 잘 맞아요",
    "관성": "서로 지킬 약속과 기준을 말로 분명히 해 두는 게 잘 맞아요",
    "인성": "결론을 내기 전에 상대 이야기를 끝까지 들어 주는 게 잘 맞아요",
}
NOW_TALK = "이번 10년은 {talk}."

# 잠금 영역 문구
LOCK_LABEL = "잠긴 풀이"
TEASER_TIER3 = "앞으로 12개월 중 마음이 잘 통하는 달과 천천히 이야기할 달을 짚어 두었어요."
TEASER_TIER4 = "오늘부터 해 볼 수 있는 다정한 관계 3원칙이 준비되어 있어요."
CTA_TEMPLATE = "앞으로 12개월 관계의 타이밍 열어보기"  # 가격은 서버(report_access.REPORT_PRICES)가 정하고 프론트가 그린다. 문구에 넣지 않는다.
PAYWALL_HREF = "#paywall-theme-love"


def cta_label() -> str:
    return CTA_TEMPLATE


# ---------------------------------------------------------------------------
# 조립
# ---------------------------------------------------------------------------
def safe_status(status: str) -> str:
    return status if status in STATUSES else DEFAULT_STATUS


def compose_tier1(group: str, status: str) -> dict:
    g = group if group in TIER1 else "balanced"
    block = TIER1[g]
    sentences = [block["A"], block["B"], block["D"]]
    body = " ".join(sentences)
    return dict(headline=HEADLINES[g], body=body, char_count=len(body), sentence_count=len(sentences), group=g)


def compose_tier2(group: str, seed: int) -> list[dict]:
    pool = TRAPS[group if group in TRAPS else "balanced"]
    first = seed % len(pool)
    second = (first + 1 + (seed // 3) % (len(pool) - 1)) % len(pool)
    return [dict(title=pool[i][0], text=pool[i][1], char_count=len(pool[i][1])) for i in (first, second)]


def compose_tier3(inflections: list[tuple[int, str]], status: str, seed: int) -> list[dict]:
    used: dict[str, set[int]] = {"opportunity": set(), "caution": set()}
    result = []
    for month, kind in inflections:
        pool = MONTH_TEXT[kind]
        i = (seed + month) % len(pool)
        while i in used[kind]:
            i = (i + 1) % len(pool)
        used[kind].add(i)
        result.append(dict(month=month, kind=kind, label=KIND_LABEL[kind], text=pool[i], char_count=len(pool[i])))
    return result


def compose_tier4(group: str, status: str) -> list[str]:
    g = group if group in GROUP_BULLETS else "balanced"
    return [*GROUP_BULLETS[g], COMMON_BULLET]
