"""오늘의 운세 길흉 등급 — 산식 v2.1 + 분위수 매핑 + 분야 편차 (2026-10-24 설계안·보정안).

하루의 체감은 일진 × 원국이다. 대운·세운·월운과의 관계는 점수에서 뺀다(월운 지지는 삼합·방합을
완성하는 셋째 글자로만 끼어든다). 사람별 평균을 50으로 맞추는 정규화는 하지 않는다.

  raw   = Σ 요소 가중치 (충·형·해파·합 × 위치 계수, 일간 충·극·합, 결핍·과다 또는 억부, 12운성, 신살)
  표시  = raw 의 모집단 누적 분위 F 를 50~100 으로 옮긴 값. 분포 목표 15/20/30/20/15.
  단계  = 나쁨 50~59 · 주의 60~69 · 보통 70~79 · 좋음 80~89 · 아주 좋음 90~100

용신(억부)은 코어 strength_state 가 strong/weak 일 때만 켠다(W=10). 조후·통관의 보류는 그대로 두고,
undetermined 는 결핍·과다 항목이 대신한다. 억부와 결핍·과다 합이 같은 날에 걸리면 절댓값이 큰 쪽 하나만 쓴다.
코어(core/facts/diagnostics/synthesis)는 읽기만 한다.
"""
from __future__ import annotations

import math
from datetime import date
from functools import lru_cache

from lunar_python import Solar

from app.engine.constants import GAN_WUXING, ZHI_WUXING
from app.engine.core.models import MyeongriCoreResult, PillarFact
from app.engine.facts.hidden_stems import get_hidden_stems
from app.engine.facts.relationship_candidates import calculate_relationship_candidates
from app.engine.facts.ten_gods import get_ten_god
from app.engine.facts.twelve_stages import get_twelve_stage
from app.engine.services.element_balance import composition, CONTROLS, CONTROLLED_BY, GENERATES, GENERATED_BY
from app.engine.shensha.engine import _DAY_STEM_RULES

SCORE_VERSION = "daily-score-v2.1-yong10"

# ---------------------------------------------------------------------------
# 산식 상수
# ---------------------------------------------------------------------------
NATAL_PILLARS = ("year", "month", "day", "hour")
POSITION_WEIGHT = {"day": 1.0, "month": 0.75, "year": 0.4, "hour": 0.4}
SIX_COMBINATION_W = {"day": 15, "month": 11, "year": 6, "hour": 6}   # v2.1: 육합 12 → 15 (일지 기준)
THREE_COMBINATION_W = 15
STEM_CLASH_PAIRS = {frozenset(p) for p in ("甲庚", "乙辛", "丙壬", "丁癸")}
STAGE_W = {"birth": 4, "official": 4, "prosperity": 4, "death": -4, "tomb": -4, "extinction": -4}
STAGE_DIRECTION = {"birth": "up", "official": "up", "prosperity": "up",
                   "death": "down", "tomb": "down", "extinction": "down"}
YANGIN = {"甲": "卯", "乙": "寅", "丙": "午", "丁": "巳", "戊": "午", "己": "巳",
          "庚": "酉", "辛": "申", "壬": "子", "癸": "亥"}
BAEKHO = frozenset({"甲辰", "乙未", "丙戌", "丁丑", "戊辰", "壬戌", "癸丑"})   # 백호대살 7일주
FILL_CAP, OVER_CAP = 10, -8
YONG_W = 10                       # 억부 가중치. 15면 일지 형+백호 날을 좋음으로 뒤집어 버린다(보정안 C-3).
YONG_STRONG = {"strong", "extremely_strong"}
YONG_WEAK = {"weak", "extremely_weak"}

# 단계 경계와 분포 목표(누적 분위 → 표시 점수). 15/20/30/20/15.
GRADE_BANDS = (("나쁨", 50, 59), ("주의", 60, 69), ("보통", 70, 79), ("좋음", 80, 89), ("아주 좋음", 90, 100))
DISPLAY_KNOTS = ((0.0, 50.0), (0.15, 59.5), (0.35, 69.5), (0.65, 79.5), (0.85, 89.5), (1.0, 100.0))
GRADES = tuple(g for g, _, _ in GRADE_BANDS)

# 모집단 raw 분위수 매듭 (타이브레이크 키 기준). scripts/build_daily_score_cdf.py 가 만든다 — 가중치를 바꾸면 다시 만든다.
# 생성 2026-10-24: N = 1,000명 × 60갑자 = 60,000건(seed 20261024), 억부 ON (W=10, strong 146 · weak 128 · 보류 726),
# 산식 v2.1. raw 평균 −0.27 · 표준편차 14.56 · 범위 −65~+54. 형식 (누적 분위 F, 그 분위의 raw 키), 사이는 선형 보간.
RAW_CDF: tuple[tuple[float, float], ...] = (
    (0.0, -65.48), (0.025, -30.36), (0.05, -25.3), (0.075, -22.22),
    (0.1, -19.33), (0.125, -17.25), (0.15, -15.3), (0.175, -14.13),
    (0.2, -12.25), (0.225, -11.17), (0.25, -10.12), (0.275, -8.33),
    (0.3, -7.43), (0.325, -6.36), (0.35, -5.41), (0.375, -4.38),
    (0.4, -4.06), (0.425, -3.12), (0.45, -2.13), (0.475, -1.18),
    (0.5, 0.19), (0.525, 1.23), (0.55, 2.18), (0.575, 3.14),
    (0.6, 4.06), (0.625, 4.37), (0.65, 5.5), (0.675, 6.32),
    (0.7, 7.37), (0.725, 8.36), (0.75, 9.49), (0.775, 10.43),
    (0.8, 12.19), (0.825, 13.31), (0.85, 15.08), (0.875, 16.32),
    (0.9, 18.33), (0.925, 21.14), (0.95, 23.39), (0.975, 28.26),
    (1.0, 54.53),
)


# ---------------------------------------------------------------------------
# 일진 ↔ 원국 관계 (timing.engine 과 같은 후보 계산을 일진 하나에 대해 돌린다)
# ---------------------------------------------------------------------------
_YANG_STEMS = frozenset("甲丙戊庚壬")
_YANG_BRANCHES = frozenset("子寅辰午申戌")


def pillar_fact(ganji: str) -> PillarFact:
    stem, branch = ganji[0], ganji[1]
    return PillarFact(
        stem=stem, branch=branch, ganji=ganji,
        stem_element=GAN_WUXING[stem], stem_yin_yang="yang" if stem in _YANG_STEMS else "yin",
        branch_element=ZHI_WUXING[branch], branch_yin_yang="yang" if branch in _YANG_BRANCHES else "yin",
    )


@lru_cache(maxsize=4096)
def calendar_ganji(target: date) -> tuple[str, str, str]:
    """(세운, 월운, 일진) 간지. timing.engine 과 같은 lunar_python 계산인데 날짜마다 14ms 라 캐시한다."""
    lunar = Solar.fromYmdHms(target.year, target.month, target.day, 12, 0, 0).getLunar()
    return lunar.getYearInGanZhiExact(), lunar.getMonthInGanZhiExact(), lunar.getDayInGanZhiExact()


def day_ganji(target: date) -> str:
    """그날의 일진(달력)."""
    return calendar_ganji(target)[2]


def _overlays(core: MyeongriCoreResult, day_pillar: str, target: date) -> dict[str, PillarFact]:
    """대운·세운·월운·일진. 월운은 삼합·방합의 셋째 글자로만 점수에 끼어든다."""
    annual, monthly, _ = calendar_ganji(target)
    found: dict[str, PillarFact] = {}
    for cycle in (core.timing.luck_cycle or {}).get("cycles", []):
        if cycle.get("start_year", 0) <= target.year <= cycle.get("end_year", -1):
            found["luck_cycle"] = PillarFact.model_validate(cycle["pillar"])
            break
    found["annual"] = pillar_fact(annual)
    found["monthly"] = pillar_fact(monthly)
    found["daily"] = pillar_fact(day_pillar)
    return found


def daily_relationships(core: MyeongriCoreResult, day_pillar: str, target: date) -> list[dict]:
    """일진이 끼는 관계 후보. 같은 글자 조합이 여러 규칙으로 잡히면 한 번만 센다(daily._daily_relationships 와 같다)."""
    combined: dict[str, PillarFact | None] = dict(core.natal_facts.pillars)
    combined.update({f"timing:{k}": v for k, v in _overlays(core, day_pillar, target).items()})
    found, seen = [], set()
    for cand in calculate_relationship_candidates(combined).items:
        members = [m.model_dump(mode="json") for m in cand.members]
        if not any(m["pillar"] == "timing:daily" for m in members):
            continue
        key = (cand.type.value, tuple(sorted(m["symbol"] for m in members)))
        if key in seen:
            continue
        seen.add(key)
        found.append({"type": cand.type.value, "members": members})
    return found


# ---------------------------------------------------------------------------
# 요소 산출
# ---------------------------------------------------------------------------
def _god_group(day_master: str, element: str) -> str:
    dm = GAN_WUXING[day_master]
    if element == dm:
        return "peer"
    if GENERATES[dm] == element:
        return "output"
    if CONTROLS[dm] == element:
        return "wealth"
    if CONTROLLED_BY[dm] == element:
        return "officer"
    return "resource"


def yong_direction(core: MyeongriCoreResult) -> str | None:
    """strong → 식상·재성·관성 희 / 비겁·인성 기, weak → 반대. 그 밖(undetermined·balanced)은 None(보류)."""
    state = str(core.synthesis.strength_state or "")
    if state in YONG_STRONG:
        return "strong"
    if state in YONG_WEAK:
        return "weak"
    return None


def yong_item(core: MyeongriCoreResult, day_pillar: str, weight: int = YONG_W) -> tuple[str, int] | None:
    direction = yong_direction(core)
    if not direction:
        return None
    dm = core.natal_facts.pillars["day"].stem
    favorable = {"output", "wealth", "officer"} if direction == "strong" else {"peer", "resource"}
    value = 0.0
    for element, w in ((GAN_WUXING[day_pillar[0]], 1.0), (ZHI_WUXING[day_pillar[1]], 0.6)):
        value += (weight if _god_group(dm, element) in favorable else -weight) * w
    value = max(-weight, min(weight, round(value)))
    return ("억부 희신" if value > 0 else "억부 기신", value)


def score_items(core: MyeongriCoreResult, day_pillar: str, target_date: date) -> list[tuple[str, int]]:
    """산식 v2.1 요소 목록 [(라벨, 가중치)]. 합이 raw 점수다."""
    pillars = core.natal_facts.pillars
    dm = pillars["day"].stem
    stem, branch = day_pillar[0], day_pillar[1]
    items: list[tuple[str, int]] = []

    for rel in daily_relationships(core, day_pillar, target_date):
        natal = [m for m in rel["members"] if m.get("pillar") in NATAL_PILLARS]
        if not natal:
            continue
        kind, pos = rel["type"], natal[0]["pillar"]
        w = POSITION_WEIGHT[pos]
        if kind == "branch_clash":
            items.append((f"{pos}지 충", round(-20 * w)))
        elif kind == "branch_punishment":
            items.append((f"{pos}지 형", round(-8 * w)))
        elif kind in ("branch_harm", "branch_break") and pos in ("day", "month"):
            items.append((f"{pos}지 해파", round(-3 * w)))
        elif kind == "branch_six_combination":
            items.append((f"{pos}지 육합", SIX_COMBINATION_W[pos]))
        elif kind == "branch_three_combination":
            items.append(("삼합", THREE_COMBINATION_W))
        elif kind == "branch_half_combination":
            items.append((f"{pos}지 반합", round(5 * w)))
        elif kind == "branch_directional_combination":
            items.append(("방합", 4))
        elif kind == "stem_combination" and pos == "day":
            items.append(("일간 천간합", 8))
        elif kind == "stem_control" and pos == "day":
            items.append(("일간 천간충", -12) if frozenset((dm, stem)) in STEM_CLASH_PAIRS else ("일간 천간극", -6))

    comp = composition(core)
    fill = over = 0.0
    for element, w in ((GAN_WUXING[stem], 1.0), (ZHI_WUXING[branch], 0.6)):
        share = comp[element]
        if share == 0:
            fill += 10 * w
        elif share < 10:
            fill += 6 * w
        elif share >= 35:
            over -= 8 * w
    balance_items: list[tuple[str, int]] = []
    if fill:
        balance_items.append(("결핍 채움", min(FILL_CAP, round(fill))))
    if over:
        balance_items.append(("과다 강화", max(OVER_CAP, round(over))))
    yong = yong_item(core, day_pillar)
    # 억부와 결핍·과다는 "이 기운이 나한테 더 필요한가"에 다른 답을 내는 장치라 겹쳐 쓰지 않는다. 큰 쪽 하나만.
    if yong and abs(yong[1]) >= abs(sum(w for _, w in balance_items)):
        items.append(yong)
    else:
        items.extend(balance_items)

    stage = get_twelve_stage(dm, branch).value
    if STAGE_W.get(stage):
        items.append((f"12운성 {stage}", STAGE_W[stage]))
    if branch in _DAY_STEM_RULES["heavenly_noble"][dm]:
        items.append(("천을귀인", 6))
    if branch in _DAY_STEM_RULES["literary_star"][dm]:
        items.append(("문창", 3))
    if branch == YANGIN[dm]:
        items.append(("양인 일진", -6))
    if day_pillar in BAEKHO:
        items.append(("백호 일진", -5))
    return items


# ---------------------------------------------------------------------------
# raw → 표시 점수
# ---------------------------------------------------------------------------
def raw_score(items: list[tuple[str, int]]) -> float:
    """raw 정수 + 타이브레이크 소수부. 같은 raw 면 요소가 많고 세기가 큰 날이 더 극단 쪽으로 간다(소수 ≤ 0.99)."""
    raw = sum(w for _, w in items)
    frac = min(0.99, len(items) * 0.05 + sum(abs(w) for _, w in items) * 0.002)
    return raw + (frac if raw >= 0 else -frac)


def cumulative(raw: float, knots=None) -> float:
    """모집단 누적 분위 F(raw) ∈ [0, 1]. 매듭 사이는 선형 보간."""
    knots = knots or RAW_CDF
    if raw <= knots[0][1]:
        return 0.0
    if raw >= knots[-1][1]:
        return 1.0
    for (f0, k0), (f1, k1) in zip(knots, knots[1:]):
        if raw <= k1:
            if k1 == k0:
                return f1
            return f0 + (f1 - f0) * (raw - k0) / (k1 - k0)
    return 1.0


def display_from_cumulative(f: float) -> int:
    for (f0, d0), (f1, d1) in zip(DISPLAY_KNOTS, DISPLAY_KNOTS[1:]):
        if f <= f1:
            return int(math.floor(d0 + (d1 - d0) * (f - f0) / (f1 - f0) + 0.5))
    return 100


def display_score(raw: float, knots=None) -> int:
    """50~100. 모집단 분위 15/20/30/20/15 가 다섯 단계에 떨어진다."""
    return max(50, min(100, display_from_cumulative(cumulative(raw, knots))))


def grade(score: int) -> str:
    for name, lo, hi in GRADE_BANDS:
        if lo <= score <= hi:
            return name
    return "아주 좋음" if score > 100 else "나쁨"


def top_item(items: list[tuple[str, int]]) -> tuple[str, int] | None:
    return max(items, key=lambda x: (abs(x[1]), x[1] < 0)) if items else None


def confidence(items: list[tuple[str, int]]) -> str:
    """최대 요소의 세기: 강(|w|≥10) · 중(4~9) · 약(그 밖, 해·파만, 관계 없음)."""
    top = top_item(items)
    if not top or abs(top[1]) < 4 or top[0].endswith("해파"):
        return "약"
    return "강" if abs(top[1]) >= 10 else "중"


# ---------------------------------------------------------------------------
# 분야 편차 — 금전 · 사람 · 일 · 건강
# ---------------------------------------------------------------------------
DOMAINS = ("금전", "사람", "일", "건강")
STANDOUT_CAUTION, STANDOUT_GOOD = -8, 10


def domain_delta(core: MyeongriCoreResult, day_pillar: str, items: list[tuple[str, int]] | None = None,
                 target_date: date | None = None) -> dict[str, int]:
    """그날 십성(천간 1.0·지지 본기 0.6)과 충·형이 걸린 자리로 분야 편차를 낸다. 표시는 standout() 이 정한다."""
    pillars = core.natal_facts.pillars
    dm = pillars["day"].stem
    stem, branch = day_pillar[0], day_pillar[1]
    if items is None:
        items = score_items(core, day_pillar, target_date or date.today())
    d = {k: 0.0 for k in DOMAINS}
    main_stem = get_hidden_stems(branch).stems[0].stem
    for god, w in ((_god_group(dm, GAN_WUXING[stem]), 1.0), (_god_group(dm, GAN_WUXING[main_stem]), 0.6)):
        if god == "wealth":
            d["금전"] += 8 * w
        elif god == "officer":
            d["사람"] += 6 * w
            d["일"] += 6 * w
        elif god == "peer":
            d["사람"] -= 4 * w
        elif god == "output":
            d["일"] += 6 * w
        elif god == "resource":
            d["건강"] += 6 * w
    wealth_element = CONTROLS[GAN_WUXING[dm]]

    def is_wealth(pos: str) -> bool:
        pillar = pillars.get(pos)
        return bool(pillar) and ZHI_WUXING[pillar.branch] == wealth_element

    for name, w in items:
        if name in ("day지 충", "day지 형"):
            d["건강"] += w * 0.5
            d["사람"] += w * 0.5
            if is_wealth("day"):
                d["금전"] += w * 0.5
        elif name == "month지 충":
            d["일"] += w * 0.5
            if is_wealth("month"):
                d["금전"] += w * 0.5
        elif name == "month지 형" and is_wealth("month"):
            d["금전"] += w * 0.5
        elif name == "일간 천간충":
            d["사람"] += w * 0.5
    return {k: round(v) for k, v in d.items()}


# 좋음·아주 좋음 날의 좋은 분야 문턱(10/26 정오님: "좋은 날에도 좋은 분야를 말해 주자").
# 오늘의 이야기 분야 결(daily_story.domain_tiers: 편차 + 등급 보정 +3 ≥ +6 이면 좋음)과 같은 저울이다.
GOOD_GRADES = ("좋음", "아주 좋음")
GOOD_DAY_ADJ, GOOD_DAY_TIER = 3, 6


def standout(deltas: dict[str, int], grade_name: str | None = None) -> tuple[str, str] | None:
    """편차 ≤ −8 이면 (분야, '주의'), ≥ +10 이면 (분야, '좋음'). 둘 다면 주의 우선. 아니면 None.

    grade_name 이 좋음·아주 좋음이면 좋은 쪽 문턱이 낮아진다(편차 + 3 ≥ +6, 곧 편차 ≥ +3). 주의 쪽 문턱은 그대로다."""
    neg = min(DOMAINS, key=lambda k: deltas.get(k, 0))
    pos = max(DOMAINS, key=lambda k: deltas.get(k, 0))
    if deltas.get(neg, 0) <= STANDOUT_CAUTION:
        return neg, "주의"
    if deltas.get(pos, 0) >= STANDOUT_GOOD:
        return pos, "좋음"
    if grade_name in GOOD_GRADES and deltas.get(pos, 0) + GOOD_DAY_ADJ >= GOOD_DAY_TIER:
        return pos, "좋음"
    return None


def evaluate(core: MyeongriCoreResult, day_pillar: str, target_date: date) -> dict:
    """한 날의 점수 묶음. daily.build_daily_fortune 과 테스트가 같은 입구를 쓴다."""
    items = score_items(core, day_pillar, target_date)
    raw = raw_score(items)
    score = display_score(raw)
    deltas = domain_delta(core, day_pillar, items)
    grade_name = grade(score)
    return {
        "items": items, "raw": raw, "raw_int": sum(w for _, w in items), "score": score, "grade": grade_name,
        "confidence": confidence(items), "top": top_item(items), "domain": deltas,
        "standout": standout(deltas, grade_name),
    }
