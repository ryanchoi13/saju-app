"""생활 추천용 보완 오행: 타고난 균형(원국) + 오늘의 기운(일진)을 함께 본다.

코어(synthesis)의 용신 판정은 보수적이라 대부분 '보류(pending)'로 남는다. 그 판정은 건드리지 않는다.
여기서는 색·음식·소품 같은 생활 추천에 쓰려고, 코어가 이미 계산한 사실만으로 '보완 방향'을 추정한다.

  원국 순위(method) — 2026-11-05 정오님 결정:
    eokbu          강약 방향이 있는 사람. 점수 카드와 같은 억부 기신을 맨 뒤로, 나머지는 아래 점수 순
    gungtong_johu  강약 보류자. 『궁통보감』 조후용신 1·2순위 → 비율·조후 점수 순 → 원문이 꺼린 오행 →
                   원국 35% 이상 오행(점수 카드 '과다 강화'와 같은 기준) 순
  원국 점수 = 오행 구성 비율의 과부족 + 조후(차고 더움·습하고 건조함) + 강약(판정된 경우에만)
  오늘 점수 = 원국 층(eokbu: 점수를 0~5로 정규화 / gungtong: 순위 눈금 5·3.5·2·1·0) + 일진 천간·지지 오행 + 일지의 계절감

용신 확정이 아니라 생활 추천을 위한 추정이며, 결과에 source 와 근거를 함께 남긴다.
"""
from __future__ import annotations

ELEMENTS = ("木", "火", "土", "金", "水")
GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}      # 我生 (식상)
CONTROLS = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}       # 我克 (재성)
GENERATED_BY = {v: k for k, v in GENERATES.items()}                          # 生我 (인성)
CONTROLLED_BY = {v: k for k, v in CONTROLS.items()}                          # 克我 (관성)

BALANCE_VERSION = "element-balance-v3"

# 억부 방향(2026-11-05 정오님): 강약 방향이 있는 사람은 오늘의 운세 점수(daily_score.yong_item)와
# 같은 방향을 따른다. 점수 카드가 '억부 기신'이라 부르는 오행은 보완 순위 맨 아래로 내린다.
# 방향이 없으면(강약 보류) 궁통보감 조후용신으로 정한다(11/5, 아래 _gungtong). 점수 카드의 억부는 여전히 꺼져 있다.
EOKBU_STRONG = {"strong", "extremely_strong"}
EOKBU_WEAK = {"weak", "extremely_weak"}


def eokbu_avoid(day_master: str, strength: str) -> set[str]:
    """강약 방향에서 기신이 되는 오행. 신강 → 비겁·인성, 신약 → 식상·재성·관성, 그 밖 → 없음."""
    if strength in EOKBU_STRONG:
        return {day_master, GENERATED_BY[day_master]}
    if strength in EOKBU_WEAK:
        return {GENERATES[day_master], CONTROLS[day_master], CONTROLLED_BY[day_master]}
    return set()

_HIDDEN_WEIGHTS = {
    "子": {"main": 1.0},
    "丑": {"main": 0.6, "middle": 0.3, "residual": 0.1},
    "寅": {"main": 16 / 30, "middle": 7 / 30, "residual": 7 / 30},
    "卯": {"main": 1.0},
    "辰": {"main": 0.6, "middle": 0.3, "residual": 0.1},
    "巳": {"main": 16 / 30, "middle": 7 / 30, "residual": 7 / 30},
    "午": {"main": 0.7, "middle": 0.3},
    "未": {"main": 0.6, "middle": 0.3, "residual": 0.1},
    "申": {"main": 16 / 30, "middle": 7 / 30, "residual": 7 / 30},
    "酉": {"main": 1.0},
    "戌": {"main": 0.6, "middle": 0.1, "residual": 0.3},
    "亥": {"main": 0.7, "middle": 0.3},
}
_BRANCH_ELEMENT = {"子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
                   "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水"}
_HOT_BRANCHES = {"巳", "午", "未"}
_COLD_BRANCHES = {"亥", "子", "丑"}


def composition(core) -> dict[str, float]:
    """천간 1칸 + 지지 1칸(지장간 비중 배분). 화면의 오행 비율과 같은 방식."""
    counts = {e: 0.0 for e in ELEMENTS}
    for name, pillar in core.natal_facts.pillars.items():
        if pillar is None:
            continue
        counts[pillar.stem_element] += 1
        hidden = core.natal_facts.hidden_stems.get(name)
        weights = _HIDDEN_WEIGHTS.get(pillar.branch, {})
        stems = hidden.stems if hidden else []
        if not stems:
            counts[_BRANCH_ELEMENT[pillar.branch]] += 1
        for item in stems:
            counts[item.element] += weights.get(getattr(item.role, "value", item.role), 0)
    total = sum(counts.values()) or 1
    return {e: round(v / total * 100, 1) for e, v in counts.items()}


def _climate(state: str | None) -> tuple[str | None, str | None]:
    if not state:
        return None, None
    parts = state.split("_")
    moisture = parts[-1] if parts[-1] in {"wet", "dry"} else None
    temperature = "_".join(parts[:-1]) if moisture else state
    return temperature, moisture


def natal_balance(core) -> dict:
    share = composition(core)
    scores = {e: 0.0 for e in ELEMENTS}
    reasons: dict[str, list[str]] = {e: [] for e in ELEMENTS}

    def add(element, value, reason):
        scores[element] += value
        reasons[element].append(reason)

    for e, s in share.items():
        if s == 0:
            add(e, 3, "deficient")
        elif s < 10:
            add(e, 2, "scarce")
        elif s < 15:
            add(e, 1, "light")
        elif s >= 35:
            add(e, -2, "excess")
        elif s >= 28:
            add(e, -1, "heavy")

    temperature, moisture = _climate((core.synthesis.climate_state or {}).get("state"))
    if temperature in {"very_cold", "cold"}:
        add("火", 3 if temperature == "very_cold" else 2.5, "climate_cold")
        add("木", 1, "climate_cold")
    elif temperature == "cool":
        add("火", 1.5, "climate_cool")
    elif temperature in {"very_hot", "hot"}:
        add("水", 3 if temperature == "very_hot" else 2.5, "climate_hot")
        add("金", 1, "climate_hot")
    elif temperature == "warm":
        add("水", 1.5, "climate_warm")
    if moisture == "wet":
        add("火", 0.5, "climate_wet")
        add("土", 0.5, "climate_wet")
    elif moisture == "dry":
        add("水", 0.5, "climate_dry")
        add("金", 0.5, "climate_dry")

    day_master = core.natal_facts.pillars["day"].stem_element
    strength = str(core.synthesis.strength_state or "")
    if strength in {"weak", "extremely_weak"}:
        add(GENERATED_BY[day_master], 2, "strength_weak")
        add(day_master, 1, "strength_weak")
    elif strength in {"strong", "extremely_strong"}:
        add(GENERATES[day_master], 2, "strength_strong")
        add(CONTROLS[day_master], 1.5, "strength_strong")
        add(CONTROLLED_BY[day_master], 1, "strength_strong")

    avoid = eokbu_avoid(day_master, strength)
    for e in avoid:
        reasons[e].append("eokbu_avoid")
    # 억부 기신은 점수와 상관없이 뒤로. 점수는 그대로 남겨 근거를 볼 수 있게 한다.
    order = sorted(ELEMENTS, key=lambda e: (e in avoid, -scores[e], share[e], ELEMENTS.index(e)))
    method, blend_base, overflow = ("eokbu" if avoid else "composition_climate"), None, None
    johu = None if avoid else _gungtong(core)
    if johu:
        # 강약 보류자(2026-11-05 정오님 결정): 『궁통보감』 조후용신 1·2순위를 앞에 세운다.
        # - 원국에 이미 35% 이상인 오행은 점수 카드가 '과다 강화'로 감점하는 오행이라 맨 뒤로(한 화면 모순 방지)
        # - 원문이 꺼린 천간의 오행은 그 앞(단, 1·2순위로 쓰는 오행과 같으면 꺼림을 무시)
        # - 나머지는 비율 + 조후 점수 순서
        method = "gungtong_johu"
        picks, shunned = johu
        overflow = [e for e in ELEMENTS if share[e] >= EXCESS_SHARE]
        head = [e for e in picks if e not in overflow]
        for rank, e in enumerate(head):
            reasons[e].append(f"gungtong_rank{rank + 1}")
        shunned = [e for e in shunned if e not in head and e not in overflow]
        for e in shunned:
            reasons[e].append("gungtong_avoid")
        for e in overflow:
            reasons[e].append("excess_share")
        rest = [e for e in order if e not in head and e not in shunned and e not in overflow]
        order = head + rest + [e for e in order if e in shunned] + [e for e in order if e in overflow]
        blend_base = {e: _JOHU_BASE[i] for i, e in enumerate(order)}
    return dict(version=BALANCE_VERSION, source="service_balance_estimate", method=method,
                composition=share, scores={e: round(scores[e], 2) for e in ELEMENTS},
                primary=order[0], secondary=order[1], ranking=order,
                reasons={e: reasons[e] for e in ELEMENTS if reasons[e]},
                strength_used=strength in EOKBU_STRONG | EOKBU_WEAK,
                eokbu_avoid=sorted(avoid, key=ELEMENTS.index),
                blend_base=blend_base, overflow=overflow,
                climate=dict(temperature=temperature, moisture=moisture))


# 궁통보감 순서를 오늘 혼합의 원국 층(0~5)으로 옮길 때의 눈금: 1순위 5 … 5순위 0
_JOHU_BASE = (5.0, 3.5, 2.0, 1.0, 0.0)
# 원국 과다 기준 — 점수 카드(daily_score '과다 강화')와 같은 값이어야 한다(테스트로 고정)
EXCESS_SHARE = 35


def _gungtong(core) -> tuple[list[str], list[str]] | None:
    """일간 × 월지의 궁통보감 (1·2순위 오행, 꺼리는 오행). 표에 없으면 None."""
    from app.engine.constants import GAN_WUXING
    from app.engine.services.gungtong_johu import GUNGTONG_JOHU

    day, month = core.natal_facts.pillars.get("day"), core.natal_facts.pillars.get("month")
    entry = GUNGTONG_JOHU.get((day.stem, month.branch)) if day and month else None
    if not entry:
        return None
    primary, secondary, shunned, _checked = entry
    picks = [GAN_WUXING[primary]]
    if secondary and GAN_WUXING[secondary] not in picks:
        picks.append(GAN_WUXING[secondary])
    return picks, [GAN_WUXING[s] for s in shunned]


def daily_blend(natal: dict, daily_stem_element: str, daily_branch: str) -> dict:
    """원국 보완 방향과 오늘 일진을 같은 눈금(0~5 대 0~5)으로 더한다."""
    raw = natal["scores"]
    low, high = min(raw.values()), max(raw.values())
    span = (high - low) or 1
    base = natal.get("blend_base") or {e: (raw[e] - low) / span * 5 for e in ELEMENTS}
    today = {e: 0.0 for e in ELEMENTS}
    branch_element = _BRANCH_ELEMENT[daily_branch]
    today[daily_stem_element] += 3
    today[branch_element] += 2
    if daily_branch in _HOT_BRANCHES:
        today["水"] += 1.5
    elif daily_branch in _COLD_BRANCHES:
        today["火"] += 1.5
    # 오늘 들어온 기운이 원국에서 이미 넘치는 오행이면, 그 힘을 받아 흘려보내는 오행(我生)을 돕는다.
    overflow = natal.get("overflow")
    if (daily_stem_element in overflow) if overflow is not None else raw.get(daily_stem_element, 0) < 0:
        today[daily_stem_element] -= 3
        today[GENERATES[daily_stem_element]] += 2
    total = {e: base[e] + today[e] for e in ELEMENTS}
    avoid = set(natal.get("eokbu_avoid") or ())
    # 오늘 일진에 기신이 들어와도 기신을 채우라고 하지 않는다(점수 카드와 같은 방향).
    order = sorted(ELEMENTS, key=lambda e: (e in avoid, -total[e], -base[e], ELEMENTS.index(e)))
    return dict(element=order[0], second=order[1], order=order, natal_primary=natal["primary"],
                from_natal=order[0] == natal["primary"],
                scores={e: round(total[e], 2) for e in ELEMENTS},
                natal_part={e: round(base[e], 2) for e in ELEMENTS},
                daily_part={e: round(today[e], 2) for e in ELEMENTS})


# ---------------------------------------------------------------------------
# 통관(通關): 일진 지지가 내 일지·월지와 충이고 두 오행이 서로 극하는 날,
# 이기는 쪽이 낳고(生) 지는 쪽을 낳는 제3의 오행으로 두 기운을 잇는다.
#   예) 子(水)·午(火) 충 → 水克火 → 水生木·木生火 → 木
# 같은 오행끼리 부딪히는 충(辰戌·丑未, 토-토)은 이어 줄 오행이 없어 쓰지 않는다.
# 측정(120명 × 60일): 약 11% 날 = 한 달에 3일 남짓. 상극까지 넓히면 40%라 쓰지 않는다.
# ---------------------------------------------------------------------------
_CLASH_PAIRS = {frozenset(p) for p in ("子午", "丑未", "寅申", "卯酉", "辰戌", "巳亥")}


def mediator(a: str, b: str) -> str | None:
    """a·b 가 서로 극하면 둘을 잇는 오행, 아니면 None."""
    if CONTROLS[a] == b:
        return GENERATES[a]
    if CONTROLS[b] == a:
        return GENERATES[b]
    return None


def tongguan_day(core, daily_branch: str) -> dict | None:
    for position in ("day", "month"):
        pillar = core.natal_facts.pillars.get(position)
        if pillar is None or frozenset((daily_branch, pillar.branch)) not in _CLASH_PAIRS:
            continue
        today, natal = _BRANCH_ELEMENT[daily_branch], _BRANCH_ELEMENT[pillar.branch]
        element = mediator(today, natal)
        if element:
            return dict(element=element, clash=f"{daily_branch}{pillar.branch}", position=position,
                        between=[today, natal], rule="branch_clash_mediator")
    return None
