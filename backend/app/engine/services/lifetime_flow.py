"""평생운세 v3 — 대운·세운과 원국의 관계 계산 (지나온 길·지금·다음).

엔진 timing 은 대운↔원국 관계 후보만 주고, 과거 세운·천간충 4쌍·삼형·삼합 완성은 없다.
여기서 조견표로 직접 계산한다(엔진 코어는 건드리지 않음).

나이는 엔진과 같은 세는 나이: age = 연도 - 출생 연도 + 1 (대운 start_age 와 일치).
세운 간지는 연 단위((연도-4) 기준)로 잡는다. 입춘 전후 몇 주의 차이는 '무렵'으로 표현해 흡수한다.
"""

from __future__ import annotations

from app.engine.constants import GAN_WUXING, ZHI_WUXING

GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"
POSITIONS = ("year", "month", "day", "hour")

BRANCH_CLASH = {frozenset(p) for p in ("子午", "丑未", "寅申", "卯酉", "辰戌", "巳亥")}
BRANCH_SIX = {frozenset(p) for p in ("子丑", "寅亥", "卯戌", "辰酉", "巳申", "午未")}
STEM_CLASH = {frozenset(p) for p in ("甲庚", "乙辛", "丙壬", "丁癸")}
STEM_COMBINE = {frozenset(p) for p in ("甲己", "乙庚", "丙辛", "丁壬", "戊癸")}
# 삼합(局)과 그 오행
TRIPLES = {"申子辰": "水", "亥卯未": "木", "寅午戌": "火", "巳酉丑": "金"}
# 삼형: 세 글자가 다 모이면 완성. 2자 형은 子卯 와 삼형의 두 글자.
TRIPLE_PUNISH = ("寅巳申", "丑戌未")
PAIR_PUNISH = {frozenset("子卯")} | {frozenset(p) for t in TRIPLE_PUNISH for p in (t[:2], t[1:], t[0] + t[2])}

GOD_GROUP = {
    "peer": "비겁", "rob_wealth": "비겁", "eating_god": "식상", "hurting_officer": "식상",
    "indirect_wealth": "재성", "direct_wealth": "재성", "seven_killings": "관성",
    "direct_officer": "관성", "indirect_resource": "인성", "direct_resource": "인성",
}


def year_pillar(year: int) -> tuple[str, str]:
    return GAN[(year - 4) % 10], ZHI[(year - 4) % 12]


def _branch_relations(x: str, natal: dict[str, str]) -> list[tuple[str, str]]:
    """x 지지가 원국 각 자리 지지와 맺는 (관계, 자리) 목록. 관계: clash / six / punish."""
    out = []
    for pos, b in natal.items():
        pair = frozenset((x, b))
        if x == b:
            continue
        if pair in BRANCH_CLASH:
            out.append(("clash", pos))
        if pair in BRANCH_SIX:
            out.append(("six", pos))
        if pair in PAIR_PUNISH:
            out.append(("punish", pos))
    return out


def _completes_triple(extra: list[str], natal: dict[str, str]) -> list[str]:
    """extra(대운·세운 지지)가 더해져 새로 완성되는 삼합 오행. 원국만으로 이미 완성된 것은 뺀다."""
    natal_set = set(natal.values())
    full = natal_set | set(extra)
    done = []
    for chars, element in TRIPLES.items():
        if set(chars) <= full and not set(chars) <= natal_set:
            done.append(element)
    return done


def _completes_punish(extra: list[str], natal: dict[str, str]) -> bool:
    natal_set = set(natal.values())
    full = natal_set | set(extra)
    return any(set(t) <= full and not set(t) <= natal_set for t in TRIPLE_PUNISH)


def classify_cycle(cycle: dict, profile: dict, natal: dict[str, str], day_stem: str) -> dict:
    """대운 하나의 유형과 근거. 판정 순서: 결핍 채움 → 일간 충 → 일지·월지 충 → 일간 합 → 과다 → 묶임(일지 육합·삼합) → 강화 → 조용함."""
    pillar = cycle.get("pillar") or {}
    stem, branch = pillar.get("stem"), pillar.get("branch")
    stem_el = pillar.get("stem_element") or (GAN_WUXING.get(stem) if stem else None)
    branch_el = pillar.get("branch_element") or (ZHI_WUXING.get(branch) if branch else None)
    els = profile["elements"]
    rel = _branch_relations(branch, natal) if branch else []
    stem_rel = None
    if stem and frozenset((stem, day_stem)) in STEM_CLASH:
        stem_rel = "clash"
    elif stem and frozenset((stem, day_stem)) in STEM_COMBINE:
        stem_rel = "combine"
    fills = [e for e in dict.fromkeys((stem_el, branch_el)) if e and els[e]["state"] == "none"]
    thick = [e for e in dict.fromkeys((stem_el, branch_el)) if e and els[e]["state"] == "many"]
    grow = [e for e in dict.fromkeys((stem_el, branch_el)) if e and els[e]["main"] in (1, 2)]
    clash_pos = [pos for kind, pos in rel if kind == "clash"]
    six_pos = [pos for kind, pos in rel if kind == "six"]
    triples = _completes_triple([branch] if branch else [], natal)

    if fills:
        kind = "fill"                                  # 원국에 없던 기운이 들어오는 것이 가장 큰 이야기
    elif stem_rel == "clash":
        kind = "stem_clash"
    elif "day" in clash_pos or "month" in clash_pos:
        kind = "clash"
    elif stem_rel == "combine":
        kind = "stem_combine"
    elif thick:
        kind = "thick"
    elif "day" in six_pos or triples:
        kind = "bond"
    elif grow:
        kind = "grow"
    else:
        kind = "quiet"
    return {
        "kind": kind, "stem": stem, "branch": branch, "stem_element": stem_el, "branch_element": branch_el,
        "fills": fills, "thick": thick, "grow": grow, "clash_pos": clash_pos, "six_pos": six_pos,
        "triples": triples, "stem_rel": stem_rel, "relations": rel,
        "new_power": bool(fills), "group": GOD_GROUP.get(cycle.get("ten_god") or "", None),
    }


def shaken_years(cycle: dict, natal: dict[str, str], day_stem: str, birth_year: int,
                 until_year: int, limit: int = 2) -> list[dict]:
    """대운 안에서 원국이 크게 걸리는 해(세운). until_year 이전 해만 본다(미래 사건은 쓰지 않는다).

    점수: 일간 천간충 3 · 일지/월지 충 3 · 년지/시지 충 2 · 대운지와 함께 같은 자리를 침 +1
          삼형 완성 3 · 삼합 완성 2 · 일간 합 1 · 대운 첫해 +1(점수가 있을 때만)
    3점 이상만, 높은 순(같으면 늦은 해) 최대 limit 개를 연도순으로 돌려준다.
    """
    start, end = cycle.get("start_year"), cycle.get("end_year")
    if not isinstance(start, int) or not isinstance(end, int):
        return []
    cycle_branch = (cycle.get("pillar") or {}).get("branch")
    cycle_clash_pos = {pos for kind, pos in _branch_relations(cycle_branch, natal) if kind == "clash"} if cycle_branch else set()
    found = []
    for year in range(start, min(end, until_year - 1) + 1):
        stem, branch = year_pillar(year)
        score, kinds = 0, []
        if frozenset((stem, day_stem)) in STEM_CLASH:
            score += 3
            kinds.append("stem_clash")
        for kind, pos in _branch_relations(branch, natal):
            if kind != "clash":
                continue
            score += 3 if pos in ("day", "month") else 2
            kinds.append(f"clash:{pos}")
            if pos in cycle_clash_pos:
                score += 1
        extra = [branch] + ([cycle_branch] if cycle_branch else [])
        if _completes_punish(extra, natal):
            score += 3
            kinds.append("triple_punish")
        triples = _completes_triple(extra, natal)
        if triples:
            score += 2
            kinds.append(f"triple:{triples[0]}")
        if frozenset((stem, day_stem)) in STEM_COMBINE:
            score += 1
            kinds.append("stem_combine")
        if score and year == start:
            score += 1
        if score >= 3:
            found.append({"year": year, "age": year - birth_year + 1, "score": score, "kinds": kinds,
                          "ganji": stem + branch})
    found.sort(key=lambda y: (-y["score"], -y["year"]))
    return sorted(found[:limit], key=lambda y: y["year"])
