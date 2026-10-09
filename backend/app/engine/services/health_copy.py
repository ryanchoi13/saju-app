"""건강·웰빙 테마운(4단 구조)의 달하 에디터 카피와 조립 로직.

1단 에너지 흐름 진단 (무료)  3~4문장, 공백 포함 180~220자
2단 컨디션 함정 (무료)  박스 2개, 각 50~70자
────────── 2,900원 페이월 ──────────
3단 바이오리듬 타이밍 (유료)  충전의 달 / 쉼이 필수인 달 2~3곳, 각 50~70자
4단 생활 활력 3원칙 (유료)  수면·스트레칭·차/식사 루틴 3개, 각 40~50자

집필 헌칙 (절대): 이 서비스는 의료 서비스가 아니다.
- 병명·질병·진단·치료·처방·수술·약 복용 등 의학 어휘와 특정 질환의 발생 단정, 공포 조장 표현을 쓰지 않는다.
  find_medical_flagged 가 은행 전체를 전수 검사하고(tests/test_health.py),
  health.py 는 엔진 밖에서 온 문장에도 같은 필터를 한 번 더 건다.
- 신체 장기의 손상이 아니라 에너지 소모·피로감·수면 리듬·마음의 소진이라는 '생활 리듬' 관점으로만 쓴다.
- 차·식사 문구는 효능을 말하지 않고 '쉬는 시간을 만드는 습관'으로만 쓴다.

월별 점수 계산과 변곡점 선택은 career_copy 의 것을 그대로 쓴다. 세 테마가 끝났으므로
다음 정리 때 theme_common 으로 옮기는 것을 권한다.
"""
from __future__ import annotations

import re

from app.engine.services.annual_copy import split_sentences, find_banned
from app.engine.services.career_copy import MODE_SCORE, choose_inflections  # noqa: F401  (health.py 가 사용)

COPY_VERSION = "dalha-health-1"
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

# ---------------------------------------------------------------------------
# 의학 표현 필터
#   - 한글 낱말 속에 우연히 들어간 글자는 걸리지 않게 한다. ("약속", "약간", "의사결정", "암기" 등)
#   - 목록은 사용자가 준 어휘에 같은 결의 어휘를 더한 것이다. 필요하면 가감해도 된다.
# ---------------------------------------------------------------------------
_MEDICAL_SOURCES = (
    r"병명", r"질병", r"질환", r"염증",
    r"(?<![가-힣])암(?:이|은|을|의|에|과|도)?(?![가-힣])", r"(?:위|간|폐|유방|대장|갑상선|췌장)암", r"종양",
    r"진단", r"치료", r"처방", r"수술", r"복용", r"투약", r"약물", r"알약", r"먹는\s*약",
    r"약을\s*(?:먹|드시|복용)",
    r"병원", r"(?<![가-힣])의사(?:에게|와|의|가|는|를|선생님)?(?![가-힣])", r"진료", r"검진", r"응급", r"입원",
    r"증상", r"통증", r"환자", r"후유증", r"합병증", r"완치", r"재발", r"악화",
    r"혈압", r"혈당", r"당뇨", r"콜레스테롤", r"감염", r"바이러스", r"항생제",
    r"우울증", r"불면증", r"공황장애", r"수면장애", r"불안장애", r"식이장애",
    r"면역", r"혈액순환", r"해독", r"디톡스",
    r"치명", r"사망", r"요절", r"단명", r"급사",
)
MEDICAL_PATTERNS = tuple(re.compile(p) for p in _MEDICAL_SOURCES)


def find_medical(text: str) -> list[str]:
    found = []
    for pattern in MEDICAL_PATTERNS:
        m = pattern.search(text or "")
        if m:
            found.append(m.group(0))
    return found


def find_medical_flagged(text: str) -> list[str]:
    """의학 표현 + 달하 HR 금기어 둘 다."""
    return find_medical(text) + find_banned(text)


def sanitize(text: str) -> str:
    """엔진 밖에서 온 문단에서 의학 표현이 든 문장만 덜어낸다. 걸리지 않으면 원문 그대로."""
    if not text:
        return ""
    sentences = split_sentences(text)
    kept = [s for s in sentences if not find_medical_flagged(s)]
    return text if len(kept) == len(sentences) else " ".join(kept)


# ---------------------------------------------------------------------------
# 엔진 값 → 카피 키
# ---------------------------------------------------------------------------
CLIMATES = ("cold", "cool", "mild", "hot", "neutral")
CLIMATE_GROUP = {
    "very_cold_wet": "cold", "cold_wet": "cold",
    "cool_dry": "cool", "cool_balanced": "cool",
    "mild_wet": "mild", "mild_balanced": "mild",
    "warm_dry": "hot", "hot_dry": "hot", "very_hot_dry": "hot",
}
PATHOLOGIES = ("overload", "climate", "transition", "bound", "depletion", "excess", "steady")
PATHOLOGY_GROUP = {
    "structural_damage": "overload", "conflict": "overload",
    "climate_extreme": "climate",
    "blocked_flow": "transition",
    "bound_element": "bound",
    "unstable_root": "depletion", "deficiency": "depletion",
    "excess": "excess",
    "no_critical_bottleneck": "steady",
}
STRENGTHS = ("weak", "balanced", "strong")


def climate_key(conclusion: str | None) -> str:
    return CLIMATE_GROUP.get(conclusion or "", "neutral")


def pathology_key(conclusion: str | None) -> str:
    return PATHOLOGY_GROUP.get(conclusion or "", "steady")


def strength_key(strength: str | None) -> str:
    if strength in {"weak", "extremely_weak"}:
        return "weak"
    if strength in {"strong", "extremely_strong"}:
        return "strong"
    return "balanced"


# ---------------------------------------------------------------------------
# 1단: 에너지 흐름 진단. A(기운의 결, ~니다) · B(체력·회복 패턴, ~요) · C(소모 요인, ~니다) · D(마무리, ~법이죠)
# ---------------------------------------------------------------------------
HEADLINES = {
    "cold": "천천히 데워지는 에너지",
    "cool": "맑게 깊어지는 에너지",
    "mild": "고르게 흐르는 에너지",
    "hot": "빠르게 타오르는 에너지",
    "neutral": "나만의 리듬을 찾는 에너지",
}
TIER1_A = {
    "cold": "타고난 에너지가 서늘하고 차분한 편이라 시동은 천천히 걸리지만 한번 달아오르면 오래 가는 사주입니다.",
    "cool": "타고난 에너지가 서늘하고 맑은 편이라 차분하게 집중하며 오래 버티는 힘이 있는 사주입니다.",
    "mild": "타고난 에너지가 온화하고 고르게 흐르는 편이라 큰 기복 없이 하루를 이어 가는 사주입니다.",
    "hot": "타고난 에너지가 따뜻하고 활발한 편이라 시작이 빠르고 몰입하면 쉬는 것도 잊는 사주입니다.",
    "neutral": "타고난 에너지의 결이 한쪽으로 크게 치우치지 않아 상황에 맞춰 리듬을 바꾸는 사주입니다.",
}
TIER1_B = {
    "weak": "기운이 가벼운 편이라 체력을 아껴 쓰고 충분히 쉰 날에 힘이 훨씬 잘 올라오는 회복 패턴이에요.",
    "balanced": "기운이 고른 편이라 활동과 쉼을 번갈아 두면 무리 없이 컨디션을 오래 이어 가는 패턴이에요.",
    "strong": "기운이 든든한 편이라 피곤하다는 신호를 뒤로 미루기 쉬워서 멈추는 시간을 일부러 넣어야 해요.",
}
TIER1_C = {
    "overload": "여러 요구와 역할이 한꺼번에 몰릴 때 에너지 소모가 커지기 쉬워서 일정을 나누어 두는 편이 좋습니다.",
    "climate": "한쪽으로 치우친 환경의 결을 누그러뜨리는 생활 리듬을 만들면 컨디션이 한결 안정적으로 이어집니다.",
    "transition": "활동과 쉼의 전환이 매끄럽지 않을 수 있어서 일과 일 사이에 짧은 전환 시간을 두면 좋습니다.",
    "bound": "한 가지 역할이나 관계에 시간과 신경이 오래 묶이지 않도록 가끔 스스로 점검해 보면 좋습니다.",
    "depletion": "기초 체력과 시간, 도움받을 곳을 먼저 든든하게 해 두면 에너지의 바닥이 한결 깊어집니다.",
    "excess": "강한 추진력을 규칙적인 활동과 쉼으로 나누어 쓰면 에너지가 오래도록 고르게 이어집니다.",
    "steady": "지금은 우선순위가 높은 소모 요인이 두드러지지 않으니 지금의 생활 리듬을 차분히 지켜 가면 좋습니다.",
}
TIER1_D = {
    "cold": "서두르지 않고 천천히 데워 가는 시간이 결국 가장 오래 가는 힘이 되는 법이죠.",
    "cool": "맑게 가라앉는 시간을 충분히 가질수록 집중이 더 깊어지는 법이죠.",
    "mild": "고른 리듬을 꾸준히 지켜 가는 힘이 때로는 가장 큰 활력이 되는 법이죠.",
    "hot": "달아오른 에너지를 식혀 주는 쉼표가 있어야 불꽃도 오래 가는 법이죠.",
    "neutral": "내게 맞는 리듬을 찾아 가는 과정 자체가 이미 좋은 회복이 되는 법이죠.",
}

# ---------------------------------------------------------------------------
# 2단: 컨디션 함정. 피로가 쌓일 때 내가 반복하는 생활 습관. (제목 ≤12자 + 50~70자)
# ---------------------------------------------------------------------------
TRAPS = {
    "overload": (
        ("한꺼번에 하기", "피곤할수록 해야 할 일을 한꺼번에 몰아서 처리하려다, 쉬는 시간이 가장 먼저 사라지곤 해요."),
        ("끼니 건너뛰기", "바쁜 날이면 식사를 대충 넘기고 버티다가, 저녁이 되면 한꺼번에 기운이 빠지는 일이 반복돼요."),
        ("거절 미루기", "부탁이 들어오면 일정을 따져 보기 전에 먼저 받아들였다가, 뒤늦게 지쳐서 쉬고 싶어지는 일이 반복돼요."),
    ),
    "climate": (
        ("같은 환경 고집", "덥든 춥든 불편한 환경을 그냥 참고 넘기다 보면, 어느새 컨디션이 가라앉는 일이 되풀이돼요."),
        ("계절 무시하기", "계절이 바뀌어도 생활 리듬을 예전 그대로 두다가, 몸이 무겁게 느껴진 뒤에야 조정하곤 해요."),
        ("한쪽으로 쏠리기", "차가운 것이나 뜨거운 것에 습관처럼 손이 가서, 하루의 리듬이 한쪽으로 쏠리는 날이 있어요."),
    ),
    "transition": (
        ("쉬는 척 일하기", "쉬는 시간에도 휴대폰으로 일을 확인하느라, 전환이 안 된 채로 하루가 이어지는 일이 반복돼요."),
        ("퇴근 후 이어지기", "일이 끝난 뒤에도 머릿속에서 일을 놓지 못해, 잠자리에 누운 뒤에야 생각이 많아지곤 해요."),
        ("몰아서 쉬기", "평소에는 쉼 없이 달리다가 주말이 되면 몰아서 쉬느라, 한 주의 리듬이 자꾸 들쭉날쭉해져요."),
    ),
    "bound": (
        ("한 곳에 묶이기", "한 사람이나 한 가지 일에 신경이 오래 묶여, 나를 돌보는 시간이 뒤로 밀리는 일이 반복돼요."),
        ("걱정 붙들기", "이미 지나간 일을 계속 되짚어 곱씹느라 잠들기 직전까지 마음이 쉬지 못하는 날이 이어지곤 해요."),
        ("내 시간 양보하기", "남의 일정에 맞추느라 내 쉬는 시간을 계속 양보하다가, 마음의 힘이 조용히 소모되곤 해요."),
    ),
    "depletion": (
        ("바닥까지 쓰기", "에너지가 바닥나기 직전까지 버티다 한 번에 무너져서, 다시 올라오는 데 오래 걸리는 일이 반복돼요."),
        ("잠부터 줄이기", "할 일이 많아지면 가장 먼저 잠을 줄여서, 다음 날의 집중력까지 함께 줄어드는 일이 많아요."),
        ("혼자 버티기", "힘들어도 도움을 청하기가 어려워 혼자 끝까지 버티다가, 마음의 여유가 먼저 바닥나곤 해요."),
    ),
    "excess": (
        ("속도 올리기", "일이 잘 풀릴수록 속도를 더 올리다가, 쉬어야 할 때를 알아차리지 못하는 일이 되풀이돼요."),
        ("신호 무시하기", "피곤하다는 느낌을 의지로 눌러 두다가, 어느 순간 한꺼번에 몰려와 주저앉듯 쉬게 되곤 해요."),
        ("쉼을 아까워하기", "쉬는 시간이 아깝다고 느껴 일정을 빼곡히 채우다가, 몸보다 마음이 먼저 지쳐 버리기도 해요."),
    ),
    "steady": (
        ("기록 없이 넘기기", "컨디션이 괜찮을 때는 생활을 돌아보지 않고 넘기다가, 리듬이 흐트러진 뒤에야 원인을 찾곤 해요."),
        ("익숙함에 기대기", "잘 지내고 있다는 생각에 규칙을 느슨하게 풀어 두다가, 리듬이 조금씩 흔들리는 일이 있어요."),
        ("비교하며 달리기", "주변 사람들의 속도와 나를 비교하며 따라가다가, 내 리듬보다 빠르게 에너지를 써 버리곤 하죠."),
    ),
}

# ---------------------------------------------------------------------------
# 3단: 바이오리듬 타이밍. 월 문장 (kind × strength), 종류별 3개.
#      표현은 '생활 리듬의 방향 제시'이며 몸의 상태를 말하지 않는다.
# ---------------------------------------------------------------------------
KIND_LABEL = {"opportunity": "활력이 차오르는 달", "caution": "쉼이 필수인 달"}
MONTH_TEXT = {
    ("opportunity", "weak"): (
        "에너지가 천천히 차오르는 달이라, 미뤄 둔 산책이나 가벼운 운동을 시작하기에 아주 좋아요.",
        "기운이 가볍게 올라오는 달이니, 새 일을 벌이기보다 그동안 쉬며 모은 힘을 알차게 써 보세요.",
        "회복이 잘 이어지는 달이라, 규칙적인 수면과 식사 시간을 새로 만들어 두기에 가장 알맞아요.",
    ),
    ("opportunity", "balanced"): (
        "활력이 고르게 차오르는 달이라, 평소에 꼭 해 보고 싶었던 활동을 하나 더해 보기에 좋아요.",
        "몸과 마음이 가볍게 맞물리는 달이니, 미뤄 둔 정리나 운동 계획을 하나만 골라 시작해 보세요.",
        "기운이 안정적으로 이어지는 달이라, 새로운 생활 습관을 하나 들이기에 정말 알맞은 때예요.",
    ),
    ("opportunity", "strong"): (
        "에너지가 넘치게 차오르는 달이라, 활동량을 늘리되 중간중간 쉬는 시간도 함께 정해 두세요.",
        "추진력이 붙는 달이니, 미뤄 둔 일을 몰아서 하기보다 하루 분량을 나누어서 진행해 보세요.",
        "활력이 높아지는 달이라, 새로운 운동이나 취미에 도전하기 좋고 하루의 마무리는 가볍게 하세요.",
    ),
    ("caution", "weak"): (
        "에너지 소모가 커지기 쉬운 달이라, 일정을 줄이고 잠자는 시간을 무엇보다 먼저 지켜 보세요.",
        "기운이 가라앉기 쉬운 달이니, 약속을 가볍게 줄이고 혼자 쉬는 시간을 먼저 확보해 보세요.",
        "쉼이 꼭 필요한 달이라, 새로운 일을 더하기보다 하루 한 번 쉬어 가는 시간을 정해 두세요.",
    ),
    ("caution", "balanced"): (
        "에너지가 빠르게 소모되기 쉬운 달이라, 일정 사이사이에 짧은 쉼표를 먼저 넣어 두는 게 좋아요.",
        "리듬이 흔들리기 쉬운 달이니, 잠자는 시간과 식사 시간을 평소보다 더 일정하게 지켜 보세요.",
        "쉼이 필요한 달이라, 중요한 일정은 앞뒤로 여유를 두고 가볍게 움직이는 날을 만들어 보세요.",
    ),
    ("caution", "strong"): (
        "속도를 내기 쉬운 달이지만 에너지 소모가 커서, 피곤하다는 신호가 오면 바로 멈춰 보세요.",
        "일이 몰리기 쉬운 달이니, 의지로 버티기보다 쉬는 시간을 일정표에 먼저 적어 두는 편이 좋아요.",
        "무리하기 쉬운 달이라, 활동량을 한 단계 낮추고 충분히 자는 날을 의식적으로 만들어 보세요.",
    ),
}
NO_INFLECTION = (
    "올해는 충전과 쉼이 크게 갈리는 달이 많지 않아요. 잔잔하게 이어지는 해이니 달마다 수면과 식사 리듬을 고르게 지켜 보세요."
)

# ---------------------------------------------------------------------------
# 4단: 생활 활력 3원칙 = 수면(기운 세기별) + 가벼운 스트레칭(기후별) + 차·식사 루틴(기후별). 각 40~50자.
#      차·식사는 효능을 말하지 않고 '쉬는 시간을 만드는 습관'으로만 쓴다.
# ---------------------------------------------------------------------------
BULLET_SLEEP = {
    "weak": "잠드는 시간을 이번 주만 30분 앞당기고 자기 전 화면을 내려놓아 보세요.",
    "balanced": "아침에 일어나는 시간을 매일 같게 맞추면 저녁의 잠드는 시간도 자연히 따라와요.",
    "strong": "바쁜 날일수록 잠드는 시간을 먼저 일정표에 적어 두고, 그 시간만큼은 꼭 지켜 보세요.",
}
BULLET_STRETCH = {
    "cold": "아침에 일어나면 어깨와 목을 천천히 돌리며 3분 정도 몸을 데워 보세요.",
    "cool": "점심을 먹은 뒤에는 자리에서 일어나 기지개를 켜고 복도를 천천히 걸어 보세요.",
    "mild": "한 시간에 한 번쯤은 자리에서 일어나 팔과 다리를 가볍게 풀어 주면 좋아요.",
    "hot": "저녁에는 미지근한 물을 한 잔 마시며 천천히 목과 어깨를 풀어 보는 거예요.",
    "neutral": "하루에 한 번 좋아하는 음악에 맞춰 3분만 가볍게 온몸을 쭉 풀어 보세요.",
}
BULLET_TEA = {
    "cold": "따뜻한 차 한 잔을 천천히 마시면서 오후의 쉬는 시간을 꼭 만들어 보세요.",
    "cool": "식사는 따뜻하게 천천히 먹고, 식사 뒤에도 잠깐 쉬는 시간을 가져 보세요.",
    "mild": "하루 한 끼는 천천히 앉아서 먹으며 그 시간만큼은 일을 내려놓아 보세요.",
    "hot": "시원하지만 차갑지 않은 물을 곁에 두고 틈틈이 마시며 잠시 쉬어 가세요.",
    "neutral": "좋아하는 차 한 잔으로 하루 중 나만의 쉬는 시간을 따로 정해 두어 보세요.",
}

# 잠금 영역 문구
LOCK_LABEL = "잠긴 풀이"
TEASER_TIER3 = "올해 활력이 차오르는 달과 쉼이 꼭 필요한 달을 열두 달의 흐름으로 정리해 두었어요."
TEASER_TIER4 = "오늘부터 해 볼 수 있는 생활 활력 3원칙이 준비되어 있어요."
CTA_TEMPLATE = "올해 컨디션 타이밍 열어보기"  # 가격은 서버(report_access.REPORT_PRICES)가 정하고 프론트가 그린다. 문구에 넣지 않는다.
PAYWALL_HREF = "#paywall-theme-health"
DISCLAIMER = (
    "이 풀이는 생활 리듬을 돌아보기 위한 안내이며 몸의 상태를 판단하지 않습니다. "
    "몸이 불편한 날이 이어지면 전문가와 상의해 주세요."
)
BOTTLENECK_NOTE = "여기서 병목은 몸의 상태가 아니라 명리에서 기운의 흐름을 살피는 개념입니다."


def cta_label() -> str:
    return CTA_TEMPLATE


# ---------------------------------------------------------------------------
# 조립
# ---------------------------------------------------------------------------
def compose_tier1(climate: str, strength: str | None, pathology: str) -> dict:
    c = climate if climate in CLIMATES else "neutral"
    p = pathology if pathology in PATHOLOGIES else "steady"
    sentences = [TIER1_A[c], TIER1_B[strength_key(strength)], TIER1_C[p], TIER1_D[c]]
    body = " ".join(sentences)
    return dict(headline=HEADLINES[c], body=body, char_count=len(body), sentence_count=len(sentences),
                climate=c, pathology=p)


def compose_tier2(pathology: str, seed: int) -> list[dict]:
    pool = TRAPS[pathology if pathology in TRAPS else "steady"]
    first = seed % len(pool)
    second = (first + 1 + (seed // 3) % (len(pool) - 1)) % len(pool)
    return [dict(title=pool[i][0], text=pool[i][1], char_count=len(pool[i][1])) for i in (first, second)]


def compose_tier3(inflections: list[tuple[int, str]], strength: str | None, seed: int) -> list[dict]:
    sk = strength_key(strength)
    used: dict[str, set[int]] = {"opportunity": set(), "caution": set()}
    result = []
    for month, kind in inflections:
        pool = MONTH_TEXT[(kind, sk)]
        i = (seed + month) % len(pool)
        while i in used[kind]:
            i = (i + 1) % len(pool)
        used[kind].add(i)
        result.append(dict(month=month, kind=kind, label=KIND_LABEL[kind], text=pool[i], char_count=len(pool[i])))
    return result


def compose_tier4(climate: str, strength: str | None) -> list[str]:
    c = climate if climate in CLIMATES else "neutral"
    return [BULLET_SLEEP[strength_key(strength)], BULLET_STRETCH[c], BULLET_TEA[c]]
