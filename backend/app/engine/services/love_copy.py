"""애정·관계 테마운(4단 구조)의 달하 에디터 카피와 조립 로직.

1단 소통 기질 진단 (무료)  3~4문장, 공백 포함 180~220자
2단 관계 습관의 함정 (무료)  박스 2개, 각 50~70자
────────── 2,900원 페이월 ──────────
3단 관계 타이밍 (유료)  핵심 변곡점 2~3개 월, 각 50~70자
4단 다정한 관계 3원칙 (유료)  불렛 3개, 각 40~50자

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

COPY_VERSION = "dalha-love-1"
PRICE_KRW = 2900

SPEC = {
    "tier1_chars": (180, 220),
    "tier1_sentences": (3, 4),
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
TIER1_STATUS = {
    "솔로": "지금은 새 인연을 맞이하는 시기이니 빠른 호감보다 대화의 결과 생활의 리듬이 맞는지 천천히 살피면 좋습니다.",
    "썸/짝사랑": "지금은 마음을 확인해 가는 시기이니 혼자 해석하기보다 가벼운 질문과 구체적인 약속으로 나누면 좋습니다.",
    "연애중": "지금은 서로를 알아 가는 시기이니 감정의 크기보다 대화하고 회복하는 방식을 함께 살피면 좋습니다.",
    "기혼": "지금은 생활을 함께 꾸리는 시기이니 역할과 휴식을 구체적으로 나누고 대화의 시간을 따로 두면 좋습니다.",
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
    ("opportunity", "솔로"): (
        "새로운 사람과 대화가 자연스럽게 이어지기 쉬운 달이라, 모임이나 소개 자리에 가볍게 나가 보기 좋아요.",
        "마음이 열리고 표현이 부드러워지는 달이니, 평소 관심 있던 활동이나 모임에 먼저 참여해 보세요.",
        "주변 사람과의 대화가 따뜻하게 이어지는 달이라, 지인을 통한 만남 제안에 열린 마음으로 답해 보세요.",
    ),
    ("caution", "솔로"): (
        "마음이 앞서기 쉬운 달이라, 첫인상으로 결론을 내리기보다 몇 번 더 만나며 천천히 알아가 보세요.",
        "기대와 현실이 엇갈리기 쉬운 달이니, 상대의 말과 행동이 한결같은지 차분히 지켜보는 편이 좋아요.",
        "감정의 기복이 커지기 쉬운 달이라, 중요한 결정은 하루 묵히고 충분히 쉬며 마음을 가라앉혀 보세요.",
    ),
    ("opportunity", "썸/짝사랑"): (
        "마음을 표현하기에 분위기가 부드러운 달이라, 가벼운 안부나 식사 약속으로 먼저 다가가 보세요.",
        "대화의 호흡이 잘 맞기 쉬운 달이니, 부담 없는 질문과 구체적인 약속으로 마음을 확인해 보세요.",
        "서로의 반응이 따뜻하게 이어지기 쉬운 달이라, 미뤄 둔 이야기를 편안하게 꺼내 볼 만해요.",
    ),
    ("caution", "썸/짝사랑"): (
        "마음이 앞서기 쉬운 달이라, 상대의 반응을 혼자 해석하기보다 한 번 더 편하게 물어보는 편이 좋아요.",
        "기대가 커지기 쉬운 달이니, 결론을 서두르지 말고 내 시간과 감정의 경계를 먼저 지켜 보세요.",
        "오해가 생기기 쉬운 달이라, 중요한 말은 문자보다 목소리로 전하고 반응은 하루 뒤에 확인해 보세요.",
    ),
    ("opportunity", "연애중"): (
        "서로에게 마음을 표현하기 좋은 달이라, 함께 보낼 시간과 앞으로의 계획을 편하게 이야기해 보세요.",
        "대화가 부드럽게 풀리는 달이니, 그동안 미뤄 둔 고마움과 기대를 서로 솔직하게 나눠 보세요.",
        "함께하는 일상이 즐거워지기 쉬운 달이라, 새로운 곳에서 하는 작은 데이트를 계획해 보세요.",
    ),
    ("caution", "연애중"): (
        "감정이 예민해지기 쉬운 달이라, 서운함이 생기면 그 자리에서 결론내지 말고 시간을 두고 이야기해 보세요.",
        "기대가 엇갈리기 쉬운 달이니, 추측하지 말고 원하는 것을 구체적으로 말로 확인해 보는 편이 좋아요.",
        "각자 바빠지기 쉬운 달이라, 짧더라도 매일 안부를 나눌 시간을 먼저 정해 두는 편이 좋아요.",
    ),
    ("opportunity", "기혼"): (
        "서로를 향한 마음이 부드럽게 오가는 달이라, 함께하는 시간을 따로 마련해 정서적인 대화를 나눠 보세요.",
        "생활의 호흡이 잘 맞는 달이니, 미뤄 둔 집안 계획이나 역할 분담을 편안하게 상의해 보세요.",
        "서로에게 고마움을 전하기 좋은 달이라, 평소 하지 못한 말을 짧은 편지나 메시지로 건네 보세요.",
    ),
    ("caution", "기혼"): (
        "생활의 피로가 쌓이기 쉬운 달이라, 해결이 필요한 이야기와 마음을 돌보는 이야기를 나눠서 해 보세요.",
        "역할과 기대가 엇갈리기 쉬운 달이니, 중요한 이야기는 컨디션이 좋은 때를 골라 차분히 시작해 보세요.",
        "예민함이 커지기 쉬운 달이라, 말하기 전에 잠시 숨을 고르고 상대의 입장을 먼저 한 번 물어보세요.",
    ),
}
NO_INFLECTION = (
    "올해는 유난히 갈리는 달이 많지 않아요. 잔잔하게 이어지는 해이니 달마다 안부와 대화를 고르게 나눠 보세요."
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
STATUS_BULLET = {
    "솔로": "새 인연을 만나면 약속을 지키는 모습과 대화의 일관성부터 차분히 살펴보세요.",
    "썸/짝사랑": "애매함이 길어지면 내가 지킬 시간과 감정의 선을 먼저 스스로 정해 두세요.",
    "연애중": "중요한 기대와 앞으로의 계획은 혼자 추측하지 말고 서로 말로 확인해 보세요.",
    "기혼": "돈과 역할, 가족 이야기는 책임 범위를 나누어서 구체적으로 정해 보세요.",
}

# 잠금 영역 문구
LOCK_LABEL = "잠긴 풀이"
TEASER_TIER3 = "올해 마음이 잘 통하는 달과 천천히 이야기할 달을 열두 달의 흐름으로 정리해 두었어요."
TEASER_TIER4 = "오늘부터 해 볼 수 있는 다정한 관계 3원칙이 준비되어 있어요."
CTA_TEMPLATE = "{price:,}원으로 올해 관계의 타이밍 열어보기"
PAYWALL_HREF = "#paywall-theme-love"


def cta_label() -> str:
    return CTA_TEMPLATE.format(price=PRICE_KRW)


# ---------------------------------------------------------------------------
# 조립
# ---------------------------------------------------------------------------
def safe_status(status: str) -> str:
    return status if status in STATUSES else DEFAULT_STATUS


def compose_tier1(group: str, status: str) -> dict:
    g = group if group in TIER1 else "balanced"
    block = TIER1[g]
    sentences = [block["A"], block["B"], TIER1_STATUS[safe_status(status)], block["D"]]
    body = " ".join(sentences)
    return dict(headline=HEADLINES[g], body=body, char_count=len(body), sentence_count=len(sentences), group=g)


def compose_tier2(group: str, seed: int) -> list[dict]:
    pool = TRAPS[group if group in TRAPS else "balanced"]
    first = seed % len(pool)
    second = (first + 1 + (seed // 3) % (len(pool) - 1)) % len(pool)
    return [dict(title=pool[i][0], text=pool[i][1], char_count=len(pool[i][1])) for i in (first, second)]


def compose_tier3(inflections: list[tuple[int, str]], status: str, seed: int) -> list[dict]:
    st = safe_status(status)
    used: dict[str, set[int]] = {"opportunity": set(), "caution": set()}
    result = []
    for month, kind in inflections:
        pool = MONTH_TEXT[(kind, st)]
        i = (seed + month) % len(pool)
        while i in used[kind]:
            i = (i + 1) % len(pool)
        used[kind].add(i)
        result.append(dict(month=month, kind=kind, label=KIND_LABEL[kind], text=pool[i], char_count=len(pool[i])))
    return result


def compose_tier4(group: str, status: str) -> list[str]:
    g = group if group in GROUP_BULLETS else "balanced"
    return [*GROUP_BULLETS[g], STATUS_BULLET[safe_status(status)]]
