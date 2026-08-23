from __future__ import annotations

import hashlib
from datetime import date

from app.engine.constants import COLOR_BY_WUXING
from app.engine.pillars import SajuResult

THEMES = ("health", "wealth", "love", "business", "study", "career")

LOVE_STATUS = ("solo", "dating", "married", "reunion")
CAREER_STATUS = ("employee", "student", "freelance", "job_change")

THEME_KO = {
    "health": "건강운",
    "wealth": "재물운",
    "love": "애정운",
    "business": "사업운",
    "study": "학업운",
    "career": "직장운",
    "today": "오늘의 운세",
    "month": "이달의 운세",
    "year": "올해의 운세",
}


def _seed(*parts: object) -> int:
    raw = "|".join(str(p) for p in parts)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return int(digest[:12], 16)


def _pick(seed: int, items: list[str]) -> str:
    return items[seed % len(items)]


def _score(seed: int, lo: int = 58, hi: int = 97) -> int:
    return lo + (seed % (hi - lo + 1))


def _weak_element(saju: SajuResult) -> str:
    return min(saju.wuxing_percent, key=saju.wuxing_percent.get)


def _strong_element(saju: SajuResult) -> str:
    return max(saju.wuxing_percent, key=saju.wuxing_percent.get)


def lucky_bits(saju: SajuResult, when: date) -> dict:
    weak = _weak_element(saju)
    seed = _seed(saju.day.label, when.isoformat(), weak)
    colors = COLOR_BY_WUXING[weak]
    numbers = [((seed // 10) % 9) + 1, ((seed // 100) % 9) + 1]
    if numbers[0] == numbers[1]:
        numbers[1] = (numbers[1] % 9) + 1
    return {
        "color": colors[seed % len(colors)],
        "colors": colors,
        "numbers": numbers,
        "element": weak,
    }


def generate_today(saju: SajuResult, when: date, nickname: str) -> dict:
    seed = _seed("today", saju.day.label, saju.month.label, when.isoformat())
    lucky = lucky_bits(saju, when)
    score = _score(seed)
    advice = _pick(
        seed,
        [
            f"{nickname}님, 오늘은 일간 {saju.day_master}의 리듬을 따라 한 가지만 확실히 끝내는 날이 좋습니다.",
            f"부족한 {lucky['element']} 기운을 의식해 {lucky['color']}을 가까이 두면 흐름이 부드러워집니다.",
            "말보다 기록이 운을 지킵니다. 약속과 금전은 짧게 메모하세요.",
            "오전에 몸부터 깨우면 오후의 판단이 정확해집니다. 과한 확답은 피하세요.",
            f"{saju.character.title} 기질이 오늘은 강점으로 나옵니다. 본능을 믿되, 속도만 한 박자 늦추세요.",
        ],
    )
    summary = _pick(
        seed // 3,
        [
            "작은 선택이 하루의 점수를 바꿉니다. 거창한 승부보다 정리가 이득입니다.",
            "사람 운이 먼저 열립니다. 먼저 연락한 쪽에서 실마리가 옵니다.",
            "재물보다는 체력 관리가 우선입니다. 저녁에 무리하면 점수가 깎입니다.",
            "집중력이 좋은 날입니다. 미뤄 둔 숙제를 오전에 처리하세요.",
        ],
    )
    return {
        "title": THEME_KO["today"],
        "date": when.isoformat(),
        "score": score,
        "summary": summary,
        "advice": advice,
        "luckyColor": lucky["color"],
        "luckyNumbers": lucky["numbers"],
        "highlight": saju.character.vibe,
    }


def _love_text(status: str, seed: int, nickname: str) -> tuple[str, str]:
    table = {
        "solo": [
            (
                "솔로 구간에서는 '만남'보다 '선택 기준'이 먼저 정리됩니다.",
                f"{nickname}님, 오늘 스치는 호감은 재미로 두고, 반복해서 편한 사람에게 마음을 열어 보세요.",
            ),
            (
                "자기 매력이 눈에 띄는 타이밍입니다. 소개보다는 취미 자리에서 인연이 큽니다.",
                "거절을 두려워하지 마세요. 기준이 선명할수록 좋은 사람이 남습니다.",
            ),
        ],
        "dating": [
            (
                "썸·연애 중에는 밀당보다 일정이 운을 가릅니다.",
                "짧은 만남이라도 온전히 집중하면 관계가 한 단계 올라갑니다.  compar은 밤에 하지 마세요.",
            ),
            (
                "상대의 침묵을 오해하기 쉬운 흐름입니다.",
                "추측 대신 한 줄 확인이 애정운을 지킵니다. 질투는 재미로만.",
            ),
        ],
        "married": [
            (
                "기혼 애정운은 로맨스보다 생활의 온기가 핵심입니다.",
                "집안일·일정 분담을 먼저 맞추면 대화가 다시 부드러워집니다.",
            ),
            (
                "부부 사이 작은 이벤트가 생각보다 큰 점수를 줍니다.",
                "거창한 선물보다 취향을 기억해 주는 한 마디가 유효합니다.",
            ),
        ],
        "reunion": [
            (
                "이별·재회 고민은 '감정의 크기'가 아니라 '반복 패턴'으로 판단하세요.",
                "연락을 열기 전에 원하는 관계의 조건을 세 줄로 적어 보세요. 조건이 없으면 재회도 같은 결말입니다.",
            ),
            (
                "상대의 태도가 아니라 나의 회복이 먼저인 달입니다.",
                "재회 의사가 있다면 감정보다 변화 여부를 보세요. 말이 아니라 일정과 책임이 증거입니다.",
            ),
        ],
    }
    options = table.get(status, table["solo"])
    return options[seed % len(options)]


def _career_text(status: str, seed: int, theme: str) -> tuple[str, str]:
    table = {
        "employee": [
            ("직장인은 성과보다 커뮤니케이션 점수가 먼저 오릅니다.", "보고는 짧게, 근거는 숫자로. 감정적 반박은 점수를 깎습니다."),
            ("팀 운이 개인 운보다 큽니다.", "도와달라는 말을 먼저 하는 쪽이 평가에서 이깁니다."),
        ],
        "student": [
            ("학생·취준생은 정보 수집보다 한 과목/한 직무의 깊이가 이득입니다.", "원서와 포트폴리오는 오전에 손보고, 비교는 저녁에 하지 마세요."),
            ("합격운은 체력과 루틴에 붙어 있습니다.", "모의와 실제의 간격을 줄이는 훈련이 최선입니다."),
        ],
        "freelance": [
            ("사업·프리랜서는 새 계약보다 기존 고객 관리가 돈을 만듭니다.", "견적은 서두르지 말고, 범위와 수정 횟수를 문장으로 남기세요."),
            ("아이디어 운이 열립니다.", "실행 가능한 한 건만 상품화하세요. 확장은 다음 달의 몫입니다."),
        ],
        "job_change": [
            ("이직·퇴사 준비는 '탈출'이 아니라 '착지'가 운입니다.", "조건 비교표에 성장과 사람을 꼭 넣으세요. 연봉만 보면 후회가 큽니다."),
            ("면접운은 스토리 정리에서 나옵니다.", "퇴사 이유를 한 문장으로 말 못하면 아직 때가 아닙니다."),
        ],
    }
    options = table.get(status, table["employee"])
    return options[seed % len(options)]


HEALTH = [
    ("소화와 수면이 컨디션의 열쇠입니다.", "카페인 컷오프를 당기고, 저녁 산책이 건강운을 올립니다."),
    ("목·어깨 긴장이 예민한 날입니다.", "화면 시간을 끊고 스트레칭 10분이 약입니다."),
    ("면역은 무난, 과로만 피하면 됩니다.", "약속은 줄이고 수분과 단백질을 챙기세요."),
]
WEALTH = [
    ("들어오는 돈보다 새는 돈을 막는 흐름입니다.", "구독·배달·충동구매를 하루만 끊어도 점수가 오릅니다."),
    ("작은 수입 운이 있습니다.", "부수입·정산·미수금을 오늘 건드리면 좋습니다."),
    ("투자보다 현금 여유가 미덕입니다.", "큰 결제는 48시간 미루세요."),
]
BUSINESS = [
    ("파트너십 운이 개인 기세보다 큽니다.", "혼자 결정하지 말고 한 명에게 검토를 맡기세요."),
    ("홍보보다 납기와 품질이 신용을 만듭니다.", "약속한 날짜를 지키는 것이 최대의 마케팅입니다."),
]
STUDY = [
    ("집중 사이클이 짧고 깊습니다.", "50분 공부 10분 휴식. 멀티태스킹은 점수를 깎습니다."),
    ("암기보다 출제 포인트 정리가 이득입니다.", "틀린 문제만 다시 보는 것이 올해의 방법입니다."),
]
CAREER_GENERIC = [
    ("평가운은 태도가 만듭니다.", "마감 전에 중간 공유를 하면 신뢰가 쌓입니다."),
    ("새로운 역할이 스칠 수 있습니다.", "작은 일이라도 끝까지 마무리한 사람에게 기회가 갑니다."),
]


def generate_theme(
    saju: SajuResult,
    when: date,
    theme: str,
    nickname: str,
    love_status: str,
    career_status: str,
    period: str = "today",
) -> dict:
    if theme not in THEMES:
        raise ValueError("지원하지 않는 테마입니다.")
    seed = _seed(theme, period, saju.day.label, saju.year.label, when.isoformat(), love_status, career_status)
    score = _score(seed, 60, 96)
    lucky = lucky_bits(saju, when)

    if theme == "love":
        summary, advice = _love_text(love_status, seed, nickname)
    elif theme in ("wealth", "career", "business"):
        if theme == "wealth":
            summary, advice = WEALTH[seed % len(WEALTH)]
            extra_s, extra_a = _career_text(career_status, seed // 5, theme)
            advice = f"{advice} {extra_a}"
            summary = f"{summary} {extra_s}"
        else:
            summary, advice = _career_text(career_status, seed, theme)
    elif theme == "health":
        summary, advice = HEALTH[seed % len(HEALTH)]
    elif theme == "study":
        summary, advice = STUDY[seed % len(STUDY)]
    else:
        summary, advice = BUSINESS[seed % len(BUSINESS)]

    period_note = {
        "today": "하루 단위로는 작은 습관이 점수를 지킵니다.",
        "month": "한 달 단위로는 초반 정리, 중반 실행, 후반 점검이 좋습니다.",
        "year": "올해는 큰 판보다 반복 가능한 루틴이 사주를 돕습니다.",
    }[period]

    return {
        "theme": theme,
        "title": THEME_KO[theme],
        "period": period,
        "date": when.isoformat(),
        "score": score,
        "summary": summary,
        "advice": f"{advice} {period_note}",
        "luckyColor": lucky["color"],
        "luckyNumbers": lucky["numbers"],
        "branch": love_status if theme == "love" else career_status if theme in ("wealth", "career", "business") else None,
        "dayMaster": saju.day_master,
        "characterTitle": saju.character.title,
    }


def generate_period(
    saju: SajuResult,
    when: date,
    period: str,
    nickname: str,
    love_status: str,
    career_status: str,
) -> dict:
    seed = _seed(period, saju.year.label, saju.month.label, when.year, when.month)
    overall = _score(seed, 62, 94)
    themes = [generate_theme(saju, when, t, nickname, love_status, career_status, period) for t in THEMES]
    headline = {
        "month": f"{when.month}월은 {saju.character.vibe} 기질이 실전에서 시험받는 달입니다.",
        "year": f"{when.year}년은 일간 {saju.day_master}에게 기반을 다지는 해입니다. 과확장보다 한 우물이 길합니다.",
    }[period]
    return {
        "period": period,
        "title": THEME_KO[period],
        "headline": headline,
        "score": overall,
        "themes": themes,
        "advice": f"{nickname}님, {_weak_element(saju)} 기운을 의식적으로 채우면 전체 점수가 안정됩니다.",
    }
