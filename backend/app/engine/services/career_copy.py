"""일·커리어 테마운(4단 구조)의 달하 에디터 카피와 조립 로직.

1단 기질 진단   (무료)  3~4문장, 공백 포함 180~220자
2단 결정적 경고 (무료)  박스 2개, 각 50~70자
────────── 2,900원 페이월 ──────────
3단 타이밍      (유료)  핵심 변곡점 2~3개 월, 각 50~70자
4단 실천 3원칙  (유료)  불렛 3개, 각 40~50자

이 모듈은 '엔진을 모르는' 순수 카피·조립 계층이다. 엔진 값(십신 개수, 월별 흐름 점수)은
career.py 가 계산해서 넘기고, 여기서는 문장을 고르고 규격을 검증한다.
금기어(HR 어휘)는 tests/test_career.py 가 은행 전체를 annual_copy.find_banned 로 검사한다.
"""
from __future__ import annotations

COPY_VERSION = "dalha-career-1"
SCHEMA = "dalha.theme.career.v1"
PRICE_KRW = 2900

SPEC = {
    "tier1_chars": (180, 220),
    "tier1_sentences": (3, 4),
    "tier2_boxes": 2,
    "tier2_chars": (50, 70),
    "tier3_months": (2, 3),
    "tier3_chars": (50, 70),
    "tier4_bullets": 3,
    "tier4_chars": (40, 50),
    "headline_max": 16,
    "trap_title_max": 12,
}

GROUPS = ("officer", "output", "wealth", "peers", "resource", "balanced")
TRACKS = ("career", "business")
STATUS_TRACK = {"직장인": "career", "취업/이직": "career", "사업가": "business", "창업": "business"}
DEFAULT_STATUS = "직장인"

# 십신 → 일하는 방식의 큰 줄기. 동률이면 위에 적힌 순서가 앞선다.
GROUP_OF_TEN_GOD = {
    "direct_officer": "officer", "seven_killings": "officer",
    "eating_god": "output", "hurting_officer": "output",
    "direct_wealth": "wealth", "indirect_wealth": "wealth",
    "peer": "peers", "rob_wealth": "peers",
    "direct_resource": "resource", "indirect_resource": "resource",
}


def lead_group(counts: dict) -> str:
    """십신 개수에서 가장 두드러진 줄기를 고른다. 하나도 없으면 'balanced'."""
    totals = {g: 0 for g in GROUPS if g != "balanced"}
    for god, n in counts.items():
        g = GROUP_OF_TEN_GOD.get(god)
        if g:
            totals[g] += n
    best = max(totals, key=totals.get)   # 동률이면 dict 순서(= GROUPS 순서)가 앞선 쪽
    return best if totals[best] else "balanced"


def strength_key(strength: str | None) -> str:
    if strength in {"weak", "extremely_weak"}:
        return "weak"
    if strength in {"strong", "extremely_strong"}:
        return "strong"
    return "balanced"


# ---------------------------------------------------------------------------
# 1단: 기질 진단. 문장 네 개를 이어 붙인다 (A 강점 · B 일하는 방식 · C 기운의 세기 · D 한 줄 마무리).
#      어미는 ~니다 → ~요 → ~니다 → ~법이죠 로 번갈아 간다. 합계는 모든 조합에서 180~220자(실측 190~205).
# ---------------------------------------------------------------------------
HEADLINES = {
    "officer": "책임으로 믿음을 얻는 사람",
    "output": "만들어 내는 손이 강한 사람",
    "wealth": "현실을 읽는 감각의 사람",
    "peers": "내 기준으로 걷는 사람",
    "resource": "배움으로 깊어지는 사람",
    "balanced": "고르게 갖춘 균형의 사람",
}

TIER1 = {
    "officer": {
        "A": {
            "career": "기준과 책임이 분명한 자리에서 믿음을 차곡차곡 쌓아 가는 힘이 먼저 드러나는 사주입니다.",
            "business": "기준과 책임이 분명한 운영의 틀을 세울 때 누구보다 안정적으로 힘을 내는 사주입니다.",
        },
        "B": {
            "career": "맡은 일의 범위와 기대가 또렷할수록 몰입이 깊어지고 주변의 신뢰도 자연스럽게 따라와요.",
            "business": "해야 할 일과 맡길 일의 선이 또렷할수록 사업의 중심이 흔들리지 않고 한결 단단해져요.",
        },
        "D": "원칙을 지키는 반듯함이 결국 가장 오래 가는 든든한 무기가 되는 법이죠.",
    },
    "output": {
        "A": {
            "career": "머릿속의 생각과 기술을 눈에 보이는 결과물로 바꿔 내는 힘이 먼저 드러나는 사주입니다.",
            "business": "아이디어와 기술을 손에 잡히는 상품과 서비스로 바꿔 내는 힘이 가장 앞서는 사주입니다.",
        },
        "B": {
            "career": "더 나은 방식을 떠올리고 직접 고쳐 보는 과정에서 일의 재미와 속도가 함께 쑥쑥 올라가요.",
            "business": "고객의 불편을 발견하고 직접 고쳐 보는 과정에서 사업의 재미와 속도가 함께 쑥쑥 올라가요.",
        },
        "D": "표현하고 개선하는 부지런한 손길이 곧 나만의 일하는 색깔이 되는 법이죠.",
    },
    "wealth": {
        "A": {
            "career": "일정과 자원, 사람의 움직임을 현실적으로 헤아려 흐름을 잡는 감각이 두드러진 사주입니다.",
            "business": "돈과 시간, 사람의 흐름을 현실적으로 헤아려 판을 짜 나가는 감각이 두드러진 사주입니다.",
        },
        "B": {
            "career": "눈앞의 조건을 정확히 따져 보고 움직일 때 불필요한 돌아감이 줄고 결과도 한층 선명해져요.",
            "business": "눈앞의 숫자와 조건을 정확히 따져 보고 움직일 때 불필요한 돌아감이 줄고 판단도 선명해져요.",
        },
        "D": "현실을 바라보는 눈이 밝을수록 내가 고를 수 있는 선택의 폭도 넓어지는 법이죠.",
    },
    "peers": {
        "A": {
            "career": "스스로 판단하고 자기만의 방식으로 길을 개척하는 힘이 가장 먼저 눈에 띄는 사주입니다.",
            "business": "스스로 판단하고 자기 방식으로 사업의 길을 여는 힘이 가장 먼저 눈에 띄는 사주입니다.",
        },
        "B": {
            "career": "주도권이 내게 있다고 느낄 때 집중이 깊어지지만 함께하는 사람과의 역할 조율이 변수가 돼요.",
            "business": "주도권이 내게 있다고 느낄 때 추진력이 붙지만 동업자나 팀원과의 역할 조율이 변수가 돼요.",
        },
        "D": "혼자 달리는 힘과 함께 걷는 지혜를 모두 가질 때 더 멀리 가는 법이죠.",
    },
    "resource": {
        "A": {
            "career": "배우고 정리한 것을 일의 바탕으로 삼아 차분히 깊이를 더해 가는 힘이 앞서는 사주입니다.",
            "business": "배우고 정리한 것을 사업의 바탕으로 삼아 차분히 깊이를 더해 가는 힘이 앞서는 사주입니다.",
        },
        "B": {
            "career": "충분히 이해하고 준비했다는 확신이 설 때 움직임이 가벼워지고 판단도 한결 흔들림이 없어요.",
            "business": "충분히 이해하고 준비했다는 확신이 설 때 결단이 가벼워지고 판단도 한결 흔들림이 없어요.",
        },
        "D": "차곡차곡 쌓아 둔 앎은 위기의 순간에 가장 든든한 뒷심이 되어 주는 법이죠.",
    },
    "balanced": {
        "A": {
            "career": "한쪽으로 크게 쏠리기보다 여러 힘이 고르게 갖춰져 상황에 맞춰 역할을 바꾸는 사주입니다.",
            "business": "한쪽으로 크게 쏠리기보다 여러 힘이 고르게 갖춰져 상황에 맞춰 운영을 바꾸는 사주입니다.",
        },
        "B": {
            "career": "어떤 자리에서도 적응은 빠르지만 내가 진짜 원하는 방향을 스스로 정하는 일이 숙제예요.",
            "business": "어떤 국면에서도 적응은 빠르지만 사업이 가야 할 방향을 스스로 정하는 일이 큰 숙제예요.",
        },
        "D": "두루 갖춘 균형감이 때로는 무엇보다 큰 경쟁력이 되어 주는 법이죠.",
    },
}

TIER1_STRENGTH = {
    "weak": {
        "career": "기운이 가벼운 편이라 일을 한꺼번에 늘리기보다 쉴 시간과 도움받을 곳을 먼저 챙길 때 힘이 납니다.",
        "business": "기운이 가벼운 편이라 사업을 한꺼번에 넓히기보다 쉴 시간과 도움받을 곳을 먼저 챙길 때 힘이 납니다.",
    },
    "balanced": {
        "career": "기운이 고른 편이라 속도를 올릴 때와 내릴 때를 번갈아 두면 오래 무리 없이 일할 수 있습니다.",
        "business": "기운이 고른 편이라 속도를 올릴 때와 내릴 때를 번갈아 두면 오래 무리 없이 운영할 수 있습니다.",
    },
    "strong": {
        "career": "기운이 든든한 편이라 추진력은 넉넉하니 혼자 정하는 범위가 커지지 않게 의견을 구하면 좋습니다.",
        "business": "기운이 든든한 편이라 추진력은 넉넉하니 혼자 정하는 범위가 커지지 않게 의견을 구하면 좋습니다.",
    },
}

# ---------------------------------------------------------------------------
# 2단: 결정적 경고. 줄기마다 후보 3개 중 2개를 고른다. (제목 ≤12자 + 50~70자 문장)
# ---------------------------------------------------------------------------
TRAPS = {
    "officer": (
        ("혼자 짊어지기", "맡은 일을 끝까지 혼자 책임지려다 도움을 청할 때를 놓치고, 어느새 지쳐 버리는 일이 반복돼요."),
        ("굳어 버린 기준", "내가 세운 기준이 너무 단단해져서 새로운 방식이나 동료의 제안을 일단 밀어내는 일이 잦아요."),
        ("알리지 못하기", "성실하게 해내고도 알리는 데는 서툴러서, 정작 필요한 순간에 내가 한 일이 가려지는 일이 생겨요."),
    ),
    "output": (
        ("말이 앞서기", "좋은 생각이 떠오르면 정리되기 전에 먼저 꺼내 버려서, 설득할 수 있었던 기회를 스스로 줄이곤 해요."),
        ("끝맺음 미루기", "새로운 시도에 마음이 먼저 가는 바람에, 하던 일의 마무리가 자꾸 뒤로 밀리는 일이 되풀이돼요."),
        ("날 선 지적", "고치고 싶은 점이 눈에 띄면 말투가 날카로워져서, 좋은 뜻으로 한 말이 오히려 오해를 사기도 해요."),
    ),
    "wealth": (
        ("조건에 갇히기", "눈앞의 조건만 따지다 보면 오래 두고 쌓일 배움과 관계의 가치를 놓치고 지나가는 일이 있어요."),
        ("기회 쫓아가기", "그럴듯한 기회가 보이면 준비보다 속도가 앞서서, 이것저것 손을 대다가 힘이 흩어지곤 해요."),
        ("쉬지 못하는 점검", "챙길 것이 많다 보니 늘 따지고 점검하느라, 정작 쉬어야 할 시간까지 일이 슬며시 파고들어요."),
    ),
    "peers": (
        ("혼자 결정하기", "내 판단을 믿는 만큼 의논 없이 정하고 나아가다가, 나중에 조율해야 할 일이 더 커지는 일이 반복돼요."),
        ("경쟁에 힘 쏟기", "비교할 대상이 눈에 들어오면 일 자체보다 이기려는 마음에 에너지를 쓰다가 쉽게 지쳐 버려요."),
        ("도움 사양하기", "스스로 해내려는 마음이 강해서 도움 제안을 사양하다가, 일이 괜히 길어지는 경우가 많아요."),
    ),
    "resource": (
        ("준비만 길어지기", "충분히 알고 시작하려다 준비 기간이 자꾸 길어져서, 움직일 적기를 놓치는 일이 되풀이돼요."),
        ("생각이 많아지기", "이럴 수도 저럴 수도 있다는 생각이 깊어져서, 결정을 미루는 사이 선택지가 줄어들기도 해요."),
        ("아는 것에 머물기", "익숙한 방식과 자료에 기대다 보니, 새로운 방법을 시험해 볼 기회가 슬그머니 지나가 버려요."),
    ),
    "balanced": (
        ("방향이 흐려지기", "무엇이든 잘 맞추다 보니 내가 정말 원하는 방향이 흐려져서, 남의 일정에 끌려가는 날이 많아져요."),
        ("눈치 보기", "주변의 기대를 두루 살피느라 내 의견을 말할 순간을 놓치고, 속으로만 쌓아 두는 일이 있어요."),
        ("역할이 늘어나기", "부탁을 잘 들어주다 보니 어느새 맡은 역할이 늘어나서, 정작 중요한 일이 뒤로 밀리곤 해요."),
    ),
}

# ---------------------------------------------------------------------------
# 3단: 타이밍. 월 문장 은행 (kind × track). 한 해 최대 3개만 쓰므로 5개면 충분하다.
#      표현은 '유리한 달 / 속도를 늦출 달'의 방향 제시이며, 결과를 보장하지 않는다.
# ---------------------------------------------------------------------------
MODE_SCORE = {"join": 2, "recovery": 1, "base": 0, "mixed": -1, "change": -2}
KIND_LABEL = {"opportunity": "흐름을 타기 좋은 달", "caution": "속도를 늦출 달"}

MONTH_TEXT = {
    ("opportunity", "career"): (
        "제안이나 새로운 만남이 들어오기 쉬운 달이라 정리해 둔 이력과 이야기를 꺼내 보기 좋아요.",
        "주변과 손발이 잘 맞아 협업이 매끄러운 달이니, 미뤄 둔 논의나 부탁이 있다면 이때 꺼내 보세요.",
        "내가 해 온 일을 알리기 좋은 흐름이라 이직이나 역할 변경 이야기를 가볍게 꺼내 볼 만해요.",
        "일의 흐름이 부드럽게 이어지는 달이라, 새 일을 시작하거나 들어온 제안을 검토하기에 알맞아요.",
        "사람들과의 호흡이 좋아지는 달이니, 중요한 면담이나 지원 일정이 있다면 이 시기로 잡아 보세요.",
    ),
    ("opportunity", "business"): (
        "협력할 사람이 모이기 쉬운 달이라, 미뤄 둔 제휴나 거래처 논의를 먼저 꺼내 보기에 좋아요.",
        "사람들과 손발이 잘 맞는 달이니, 미뤄 둔 제안이나 계약 논의를 이 시기에 차근차근 진행해 보세요.",
        "고객과 주변의 반응이 부드럽게 이어져서, 새 상품이나 서비스를 선보이기에 알맞은 달이에요.",
        "흐름이 순하게 풀리는 달이라, 오래 준비해 둔 계획을 작은 규모로 먼저 시험해 보기에 좋아요.",
        "거래와 만남이 매끄럽게 이어지는 달이니, 중요한 미팅 일정을 가능하면 이 시기에 모아 보세요.",
    ),
    ("caution", "career"): (
        "변동 신호가 큰 달이라 큰 결정을 서두르기보다, 맡은 일을 지키면서 한 템포 늦춰 보세요.",
        "의견이 엇갈리기 쉬운 달이니 중요한 말은 글로 남기고 결정은 하루 묵힌 뒤에 내려 보세요.",
        "마음이 앞서기 쉬운 달이라, 이직 서류나 계약서는 한 번 더 꼼꼼히 읽고 보내는 편이 안전해요.",
        "일정과 기대가 엇갈리기 쉬운 달이니, 새 일을 더하기보다 이미 맡은 일을 정돈하는 데 힘쓰세요.",
        "예상 밖의 변수가 끼어들기 쉬운 달이니 무리한 약속은 줄이고 여유 시간을 먼저 확보하세요.",
    ),
    ("caution", "business"): (
        "변동 신호가 큰 달이라 확장이나 큰 지출은 미루고 지금 운영하는 일을 단단히 지켜 보세요.",
        "의견이 엇갈리기 쉬운 달이니 약속과 조건은 문서로 남기고 결정은 하루 묵힌 뒤에 해 보세요.",
        "마음이 앞서기 쉬운 달이라 계약이나 투자는 조건을 다시 확인한 뒤에 움직이는 편이 안전해요.",
        "일정과 기대가 겹쳐 흔들리기 쉬운 달이니, 새 일을 늘리기보다 이미 벌인 일을 정돈하는 데 힘쓰세요.",
        "예상 밖의 변수가 끼어들기 쉬운 달이니 현금 여유를 넉넉히 두고 무리한 약속을 줄여 보세요.",
    ),
}

NO_INFLECTION = (
    "올해는 유난히 갈리는 달이 많지 않아요. 큰 파도 없이 꾸준히 쌓아 가는 해이니 달마다 속도를 고르게 가져가 보세요."
)

# ---------------------------------------------------------------------------
# 4단: 실천 3원칙. 줄기 불렛 2개 + 상태(직장인/이직/사업가/창업) 불렛 1개. 각 40~50자.
# ---------------------------------------------------------------------------
GROUP_BULLETS = {
    "officer": (
        "맡은 일의 범위를 이번 주 안에 한 장으로 적어서 팀과 먼저 맞춰 보세요.",
        "혼자 끌어안고 있는 일 하나를 골라서 이번 주 안에 누군가와 나눠 보세요.",
    ),
    "output": (
        "새 아이디어는 하루쯤 묵힌 뒤에 한 문장으로 깔끔하게 정리해서 꺼내 보세요.",
        "벌여 둔 일 중에서 하나만 골라 이번 주 안에 먼저 끝맺음부터 해 보세요.",
    ),
    "wealth": (
        "새 기회가 오면 얻는 것과 드는 것을 한 줄씩 적어 본 뒤에 답해 보세요.",
        "한 달에 한 번은 일에서 완전히 벗어나 쉬는 날을 달력에 먼저 표시해 두세요.",
    ),
    "peers": (
        "중요한 결정은 믿는 사람 한 명에게 먼저 이야기해 보고 나서 정해 보세요.",
        "함께 일을 시작하기 전에 각자 맡을 일과 기대하는 것을 말로 확인해 두세요.",
    ),
    "resource": (
        "공부와 준비에는 마감일을 정해 두고, 그날 가진 것으로 먼저 시도해 보세요.",
        "배운 것 하나를 이번 주 일에 직접 써 보고, 결과를 세 줄로 남겨 보세요.",
    ),
    "balanced": (
        "하고 싶은 일 세 가지를 적고 가장 끌리는 하나에만 먼저 시간을 쓰세요.",
        "부탁을 받으면 그 자리에서 답하지 말고, 하루쯤 생각한 뒤에 답해 보세요.",
    ),
}
STATUS_BULLET = {
    "직장인": "내가 한 일은 월말마다 한 줄씩 기록해 두면 이야기할 때 든든한 근거가 돼요.",
    "취업/이직": "지원하기 전에 내가 반복해서 잘해 온 일 세 가지를 먼저 글로 적어 보세요.",
    "사업가": "매달 들어오고 나가는 돈의 흐름을 한 번씩 점검하는 날을 미리 정해 두세요.",
    "창업": "큰 투자에 앞서 작은 비용으로 먼저 고객의 반응부터 차분히 확인해 보세요.",
}

# ---------------------------------------------------------------------------
# 잠금 영역 문구 (티저). 본문은 싣지 않는다.
# ---------------------------------------------------------------------------
LOCK_LABEL = "잠긴 풀이"
TEASER_TIER3 = "올해 일이 풀리는 달과 한 템포 늦출 달, 열두 달 가운데 {n}곳을 짚어 두었어요."
TEASER_TIER3_NONE = "올해 일의 리듬을 열두 달의 흐름으로 정리해 두었어요."
TEASER_TIER4 = "오늘부터 바로 옮길 수 있는 실천 3원칙이 준비되어 있어요."
CTA_TEMPLATE = "{price:,}원으로 올해 일의 타이밍 열어보기"
PAYWALL_HREF = "#paywall-theme-career"


def cta_label() -> str:
    return CTA_TEMPLATE.format(price=PRICE_KRW)


# ---------------------------------------------------------------------------
# 조립
# ---------------------------------------------------------------------------
def track_of(status: str) -> str:
    return STATUS_TRACK.get(status, "career")


def compose_tier1(group: str, track: str, strength: str | None) -> dict:
    g = group if group in TIER1 else "balanced"
    t = track if track in TRACKS else "career"
    block = TIER1[g]
    sentences = [block["A"][t], block["B"][t], TIER1_STRENGTH[strength_key(strength)][t], block["D"]]
    body = " ".join(sentences)
    return dict(headline=HEADLINES[g], body=body, char_count=len(body), sentence_count=len(sentences), group=g)


def compose_tier2(group: str, seed: int) -> list[dict]:
    pool = TRAPS[group if group in TRAPS else "balanced"]
    first = seed % len(pool)
    second = (first + 1 + (seed // 3) % (len(pool) - 1)) % len(pool)
    return [dict(title=pool[i][0], text=pool[i][1], char_count=len(pool[i][1])) for i in (first, second)]


def choose_inflections(scores: dict[int, int]) -> list[tuple[int, str]]:
    """월별 점수에서 핵심 변곡점 최대 3개를 뽑는다. [(월, 'opportunity'|'caution')] 를 월 순서로.

    점수 ≥ 1 이면 흐름을 타기 좋은 달, ≤ -1 이면 속도를 늦출 달 후보.
    양쪽에서 가장 두드러진 한 달씩을 먼저 잡고, 남은 자리는 점수 절댓값이 큰 쪽부터 채운다.
    아무 신호도 없으면 빈 리스트(= 억지로 만들어 내지 않는다).
    """
    opp = sorted((m for m, s in scores.items() if s >= 1), key=lambda m: (-scores[m], m))
    cau = sorted((m for m, s in scores.items() if s <= -1), key=lambda m: (scores[m], m))
    picked: list[tuple[int, str]] = []
    if opp:
        picked.append((opp.pop(0), "opportunity"))
    if cau:
        picked.append((cau.pop(0), "caution"))
    rest = [(m, "opportunity") for m in opp] + [(m, "caution") for m in cau]
    rest.sort(key=lambda x: (-abs(scores[x[0]]), x[0]))
    for item in rest:
        if len(picked) >= SPEC["tier3_months"][1]:
            break
        picked.append(item)
    return sorted(picked)


def compose_tier3(inflections: list[tuple[int, str]], track: str, seed: int) -> list[dict]:
    """월마다 문장을 배정한다. 같은 종류의 달이 여럿이어도 같은 문장이 겹치지 않는다."""
    t = track if track in TRACKS else "career"
    used: dict[str, set[int]] = {"opportunity": set(), "caution": set()}
    result = []
    for month, kind in inflections:
        pool = MONTH_TEXT[(kind, t)]
        i = (seed + month) % len(pool)
        while i in used[kind]:
            i = (i + 1) % len(pool)
        used[kind].add(i)
        result.append(dict(month=month, kind=kind, label=KIND_LABEL[kind], text=pool[i], char_count=len(pool[i])))
    return result


def compose_tier4(group: str, status: str) -> list[str]:
    g = group if group in GROUP_BULLETS else "balanced"
    s = status if status in STATUS_BULLET else DEFAULT_STATUS
    return [*GROUP_BULLETS[g], STATUS_BULLET[s]]


def teaser_tier3(n_months: int) -> str:
    return TEASER_TIER3.format(n=n_months) if n_months else TEASER_TIER3_NONE
