"""옷 칸마다 색을 정한다. 입력은 오늘의 행운 색, 입는 사람, 칸 목록, 최근 기록. 출력은 칸별 색과 그 근거.

원칙(2026-10-28~30 정오님)
- 근거 있는 규칙(rules.json)만 쓴다. 규칙이 없는 칸은 '근거 없음'으로 표시해 모르는 영역을 드러낸다.
- 도안에 고정된 기본색(네이비 바지·버건디 넥타이 등)을 쓰지 않는다. 바탕색도 여기서 정한다.
- 같은 주인공 색이 이틀 연속 나오지 않게 한다(서비스 규칙).
"""
import colorsys
import json
from functools import lru_cache
from pathlib import Path

from fashion_v2.svg_recommendation import PALETTE

RULES_PATH = Path(__file__).with_name("rules.json")

# 바탕색 후보. 어느 칸에 어느 바탕색을 쓰는지는 아직 근거가 없다(커버리지 지도 '바탕색으로 쓰는 색' 빈칸).
# 그래서 이 후보로 채운 칸은 evidence=None 으로 표시된다.
BASE_CANDIDATES = ("black", "charcoal", "navy", "gray", "ivory", "white", "beige")
AREA_ORDER = {"small": 0, "medium": 1, "large": 2}


@lru_cache(maxsize=1)
def load_rules():
    data = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    return {r["id"]: r for r in data["rules"]}


def tone_class(color) -> str:
    """팔레트 색의 톤 분류(크부장 판단: HSL 경계값. 지식서 01장 '톤 분류표'가 나오면 그 표로 바꾼다)."""
    if color.get("family") == "neutral" or color["id"] in {"black", "charcoal", "navy"}:
        return "neutral"
    r, g, b = (int(color["hex"][i:i + 2], 16) / 255 for i in (1, 3, 5))
    _, l, s = colorsys.rgb_to_hls(r, g, b)
    if l < 0.32:
        return "dark"
    if color.get("kind") == "vivid" or (s >= 0.55 and l <= 0.68):
        return "vivid"
    if l >= 0.72:
        return "light"
    return "dull"


def _subdued(color) -> bool:
    return tone_class(color) in {"dull", "dark", "neutral"}


def _evidence(rule_ids):
    rules = load_rules()
    grades = [e["grade"] for rid in rule_ids for e in rules[rid]["evidence"]]
    return max(grades) if grades else None  # 여러 규칙에 기대면 가장 약한 근거가 그 칸의 등급


def plan_outfit_colors(slots, lucky, wearer=None, recent_heroes=()):
    """slots: [{'slot': 'top', 'area': 'medium'}, ...]
    lucky: 오늘의 행운 색 팔레트 항목 1~3개(첫째가 주인공 후보)
    recent_heroes: 최근 며칠의 주인공 색 id (가장 최근이 끝)
    """
    lucky = [c for c in lucky if c]
    if not lucky:
        raise ValueError("행운 색이 없습니다")
    hero, others = lucky[0], lucky[1:]
    service_rules = []
    if recent_heroes and hero["id"] == recent_heroes[-1] and others and others[0]["id"] != hero["id"]:
        hero, others = others[0], [lucky[0]] + others[1:]
        service_rules.append("no-hero-repeat")

    free = sorted(slots, key=lambda s: AREA_ORDER[s["area"]])
    placed, unplaced = {}, []

    def take(prefer_small):
        pool = free if prefer_small else list(reversed(free))
        for s in pool:
            if s["area"] != "large" or not prefer_small:
                free.remove(s)
                return s
        return None

    # 1) 주인공 색: 비비드면 좁은 칸, 아니면 중간 칸부터 (vivid-small-area)
    vivid = tone_class(hero) == "vivid"
    slot = take(prefer_small=vivid) if vivid else next((s for s in free if s["area"] == "medium"), None)
    if slot and slot in free:
        free.remove(slot)
    if slot:
        placed[slot["slot"]] = dict(color=hero["id"], source="lucky", rules=["vivid-small-area"] + service_rules)
    else:
        unplaced.append(hero["id"])

    # 2) 다른 행운 색: 둘 중 하나가 가라앉은 톤일 때만 옷에 놓는다 (pair-one-subdued)
    for c in others:
        if not (_subdued(hero) or _subdued(c)):
            unplaced.append(c["id"])
            continue
        s = take(prefer_small=tone_class(c) == "vivid")
        if s is None:
            unplaced.append(c["id"])
            continue
        placed[s["slot"]] = dict(color=c["id"], source="lucky", rules=["pair-one-subdued", "vivid-small-area"])

    # 3) 남은 칸: 바탕색. 칸별 근거가 아직 없어 evidence=None (커버리지 빈칸)
    used = {p["color"] for p in placed.values()}
    base = [k for k in BASE_CANDIDATES if k not in used]
    for i, s in enumerate(list(free)):
        placed[s["slot"]] = dict(color=base[i % len(base)], source="base", rules=[])

    for p in placed.values():
        p["evidence"] = _evidence([r for r in p["rules"] if r in load_rules()])
    return dict(hero=hero["id"], slots=placed, unplaced=unplaced,
                gaps=sorted(k for k, p in placed.items() if p["evidence"] is None))
