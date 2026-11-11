"""오늘의 운세 길흉 등급 — 산식 v2.1 + 분위수 매핑 + 분야 편차 (2026-10-24 설계안·보정안).

하루의 체감은 일진 × 원국이다. 대운·세운·월운과의 관계는 점수에서 뺀다(월운 지지는 삼합·방합을
완성하는 셋째 글자로만 끼어든다). 사람별 평균을 50으로 맞추는 정규화는 하지 않는다.

  raw   = Σ 요소 가중치 (충·형·해파·합 × 위치 계수, 일간 충·극·합, 오행 3단계(필요한 기운), 12운성, 신살)
  표시  = raw 의 모집단 누적 분위 F 를 50~100 으로 옮긴 값. 분포 목표 15/20/30/20/15.
  단계  = 나쁨 50~59 · 주의 60~69 · 보통 70~79 · 좋음 80~89 · 아주 좋음 90~100

2026-11-11 정오님: 억부(강약 방향 있을 때)·결핍·과다 항목을 '오행 3단계'(tier_item) 하나로 바꿨다.
억부·조후·원국 비율 세 틀이 함께 판정하고 행운 색(fashion_v2.daily_colors)과 같은 판정을 쓴다 — 한 화면 안의 모순 방지.
yong_item 은 다른 화면(평생운세 등)이 강약 방향 판정을 쓰려고 남겨 둔다.
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

SCORE_VERSION = "daily-score-v2.2-tiers10"

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
TIER_W = 10                      # 오행 3단계 가중치(2026-11-11). 억부 W=10 과 같은 크기로 시작.
YONG_W = 10                       # 억부 가중치. 15면 일지 형+백호 날을 좋음으로 뒤집어 버린다(보정안 C-3).
YONG_STRONG = {"strong", "extremely_strong"}
YONG_WEAK = {"weak", "extremely_weak"}

# 단계 경계와 분포 목표(누적 분위 → 표시 점수). 15/20/30/20/15.
GRADE_BANDS = (("나쁨", 50, 59), ("주의", 60, 69), ("보통", 70, 79), ("좋음", 80, 89), ("아주 좋음", 90, 100))
DISPLAY_KNOTS = ((0.0, 50.0), (0.15, 59.5), (0.35, 69.5), (0.65, 79.5), (0.85, 89.5), (1.0, 100.0))
GRADES = tuple(g for g, _, _ in GRADE_BANDS)

# 모집단 raw 분위수 매듭 (타이브레이크 키 기준). scripts/build_daily_score_cdf.py 가 만든다 — 가중치를 바꾸면 다시 만든다.
# 생성 2026-11-11(오행 3단계 항목으로 교체 후 재생성): N = 1,000명 × 60갑자 = 60,000건(seed 20261024), 산식 v2.2.
# raw 평균 4.11 · 표준편차 14.34 · 범위 −58~+54. (이전 2026-10-24 v2.1 억부: 평균 −0.27 · 표준편차 14.56)
# 형식 (누적 분위 F, 그 분위의 raw 키), 사이는 선형 보간.
RAW_CDF: tuple[tuple[float, float], ...] = (
    (0.0, -58.47), (0.025, -26.21), (0.05, -21.19), (0.075, -17.35),
    (0.1, -15.13), (0.125, -12.33), (0.15, -10.46), (0.175, -9.23),
    (0.2, -8.07), (0.225, -6.25), (0.25, -5.2), (0.275, -4.18),
    (0.3, -3.12), (0.325, -2.12), (0.35, -1.18), (0.375, 0.26),
    (0.4, 1.3), (0.425, 2.19), (0.45, 3.18), (0.475, 4.13),
    (0.5, 5.06), (0.525, 6.06), (0.55, 6.25), (0.575, 7.25),
    (0.6, 8.19), (0.625, 9.23), (0.65, 10.12), (0.675, 10.45),
    (0.7, 12.12), (0.725, 12.62), (0.75, 14.13), (0.775, 15.18),
    (0.8, 16.2), (0.825, 17.31), (0.85, 19.19), (0.875, 20.36),
    (0.9, 22.36), (0.925, 25.15), (0.95, 27.38), (0.975, 31.55),
    (1.0, 54.46),
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


def tier_item(core: MyeongriCoreResult, day_pillar: str, weight: int = TIER_W) -> tuple[str, int] | None:
    """오늘 들어온 기운이 나한테 필요한가 — 행운 색과 같은 오행 3단계(element_balance.element_tiers, 2026-11-11 정오님).

    천간(1.0)·지지 본기(0.6) 오행이 좋음이면 +, 피함이면 −, 무난(틀끼리 의견이 갈림)이면 0. ±weight 로 자른다.
    예전 억부 항목(yong_item)과 결핍·과다 항목을 이 하나로 대신한다(억부 하나만 따르면 행운 색과 어긋났다).
    라벨은 기존 문구 은행을 그대로 쓰도록, 그 오행에 표를 던진 틀로 고른다:
      + 억부 찬성 → '억부 희신' / 비율 찬성 → '결핍 채움' / 조후만 → '억부 희신'(문구가 '필요한 기운'이라 맞다)
      − 억부 반대 → '억부 기신' / 비율 반대 → '과다 강화' / 그 밖 → '억부 기신'
    """
    from app.engine.services.element_balance import TIER_AVOID, TIER_GOOD

    info = _tiers_cached(core)
    tiers, votes = info["tiers"], info["votes"]
    signed = []
    for element, w in ((GAN_WUXING[day_pillar[0]], 1.0), (ZHI_WUXING[day_pillar[1]], 0.6)):
        sign = 1 if tiers[element] == TIER_GOOD else -1 if tiers[element] == TIER_AVOID else 0
        signed.append((element, sign, w))
    value = max(-weight, min(weight, round(sum(sign * weight * w for _, sign, w in signed))))
    if not value:
        return None
    lead = next(e for e, sign, _ in signed if sign == (1 if value > 0 else -1))
    lenses = {name for name, v in votes[lead] if (v > 0) == (value > 0)}
    if value > 0:
        label = "억부 희신" if "eokbu" in lenses or "share" not in lenses else "결핍 채움"
    else:
        label = "억부 기신" if "eokbu" in lenses or "share" not in lenses else "과다 강화"
    return (label, value)


def _tiers_cached(core: MyeongriCoreResult) -> dict:
    """원국은 그대로라 한 core 에서 한 번만 계산한다(연간 리포트는 12번 부른다)."""
    from app.engine.services.element_balance import element_tiers

    cached = getattr(core, "_dalha_element_tiers", None)
    if cached is None:
        cached = element_tiers(core)
        try:
            object.__setattr__(core, "_dalha_element_tiers", cached)
        except Exception:
            pass
    return cached


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

    tier = tier_item(core, day_pillar)
    if tier:
        items.append(tier)

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
    # 11/10: 분야 결은 이름 붙은 규칙표(daily_domain_rules)가 정한다. deltas 는 몸 신호(daily_story body_flag)와 옛 호환용으로만 남긴다
    from app.engine.services import daily_domain_rules as DR
    rules = DR.evaluate_domains(core, day_pillar, items, yong_direction(core), grade_name)
    return {
        "items": items, "raw": raw, "raw_int": sum(w for _, w in items), "score": score, "grade": grade_name,
        "confidence": confidence(items), "top": top_item(items), "domain": deltas,
        "domain_rules": rules, "standout": DR.standout(rules, grade_name),
    }
