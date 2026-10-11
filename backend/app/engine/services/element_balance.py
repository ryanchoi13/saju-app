"""생활 추천용 보완 오행: 타고난 균형(원국) + 오늘의 기운(일진)을 함께 본다.

코어(synthesis)의 용신 판정은 보수적이라 대부분 '보류(pending)'로 남는다. 그 판정은 건드리지 않는다.
여기서는 색·음식·소품 같은 생활 추천에 쓰려고, 코어가 이미 계산한 사실만으로 '보완 방향'을 추정한다.

  원국 점수 = 오행 구성 비율의 과부족 + 조후(차고 더움·습하고 건조함) + 강약(판정된 경우에만)
  오늘 점수 = 원국 점수(0~5로 정규화) + 일진 천간·지지 오행 + 일지의 계절감

용신 확정이 아니라 생활 추천을 위한 추정이며, 결과에 source 와 근거를 함께 남긴다.
"""
from __future__ import annotations

ELEMENTS = ("木", "火", "土", "金", "水")
GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}      # 我生 (식상)
CONTROLS = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}       # 我克 (재성)
GENERATED_BY = {v: k for k, v in GENERATES.items()}                          # 生我 (인성)
CONTROLLED_BY = {v: k for k, v in CONTROLS.items()}                          # 克我 (관성)

BALANCE_VERSION = "element-balance-v1"

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

    order = sorted(ELEMENTS, key=lambda e: (-scores[e], share[e], ELEMENTS.index(e)))
    return dict(version=BALANCE_VERSION, source="service_balance_estimate",
                composition=share, scores={e: round(scores[e], 2) for e in ELEMENTS},
                primary=order[0], secondary=order[1], ranking=order,
                reasons={e: reasons[e] for e in ELEMENTS if reasons[e]},
                strength_used=strength in {"weak", "extremely_weak", "strong", "extremely_strong"},
                climate=dict(temperature=temperature, moisture=moisture))


def daily_blend(natal: dict, daily_stem_element: str, daily_branch: str) -> dict:
    """원국 보완 방향과 오늘 일진을 같은 눈금(0~5 대 0~5)으로 더한다."""
    raw = natal["scores"]
    low, high = min(raw.values()), max(raw.values())
    span = (high - low) or 1
    base = {e: (raw[e] - low) / span * 5 for e in ELEMENTS}
    today = {e: 0.0 for e in ELEMENTS}
    branch_element = _BRANCH_ELEMENT[daily_branch]
    today[daily_stem_element] += 3
    today[branch_element] += 2
    if daily_branch in _HOT_BRANCHES:
        today["水"] += 1.5
    elif daily_branch in _COLD_BRANCHES:
        today["火"] += 1.5
    # 오늘 들어온 기운이 원국에서 이미 넘치는 오행이면, 그 힘을 받아 흘려보내는 오행(我生)을 돕는다.
    if raw.get(daily_stem_element, 0) < 0:
        today[daily_stem_element] -= 3
        today[GENERATES[daily_stem_element]] += 2
    total = {e: base[e] + today[e] for e in ELEMENTS}
    order = sorted(ELEMENTS, key=lambda e: (-total[e], -base[e], ELEMENTS.index(e)))
    return dict(element=order[0], second=order[1], natal_primary=natal["primary"],
                from_natal=order[0] == natal["primary"],
                scores={e: round(total[e], 2) for e in ELEMENTS},
                natal_part={e: round(base[e], 2) for e in ELEMENTS},
                daily_part={e: round(today[e], 2) for e in ELEMENTS})
