"""궁합 v2: 두 사람의 원국을 맞대어 읽는 신호 계산 (2026-11-20).

문장은 compat_copy.py, 화면 조립은 compatibility.py. 여기서는 사실만 계산한다.

- 점수를 매기지 않는다. 신호가 있으면 신호로, 없으면 없는 대로 둔다(억지로 칸을 채우지 않는다).
- 십성: get_ten_god(내 일간, 상대 일간) = 상대가 나에게 어떤 별인가.
- 합이 '온전한가': 두 사람 원국 어디든 합의 두 글자 중 하나를 충하는 글자가 있으면 방해(disturbed),
  합의 짝이 다른 자리에 하나 더 있으면 다툼(contested, 쟁합). 합화(오행이 바뀜)는 판정하지 않는다.
- 시간 미상: 시주가 없으면 6글자로만 보고, 대운·세운은 날짜만으로 계산되므로 그대로 쓴다.
- 세운은 올해부터 10년. 각자의 오행 3단계(element_tiers)로 '함께 좋은 해·함께 힘든 해·한 사람만 힘든 해'를 가른다.
"""
from __future__ import annotations

from app.engine.constants import GAN_WUXING
from app.engine.facts.ten_gods import get_ten_god
from app.engine.services.element_balance import ELEMENTS, composition, element_tiers
from app.engine.services.theme_core import CLASH, SIX, TRIAD, punishes, year_gz

GROUP = {
    "peer": "peer", "rob_wealth": "peer", "eating_god": "output", "hurting_officer": "output",
    "direct_wealth": "wealth", "indirect_wealth": "wealth", "direct_officer": "officer",
    "seven_killings": "officer", "direct_resource": "resource", "indirect_resource": "resource",
}
_HARM = {frozenset(p) for p in ("子未", "丑午", "寅巳", "卯辰", "申亥", "酉戌")}
_BREAK = {frozenset(p) for p in ("子酉", "丑辰", "寅亥", "卯午", "巳申", "未戌")}
_STEM_SIX = {frozenset(p) for p in ("甲己", "乙庚", "丙辛", "丁壬", "戊癸")}
_GEN = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
_CTL = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
HEAVY = 35.0     # 오행 편중(점수 카드 '과다 강화'와 같은 기준)
LACK = 10.0      # 부족
FILL = 22.0      # 상대 원국에서 그 오행이 이만큼 있어야 '채워 준다'고 본다
POS = ("year", "month", "day", "hour")


def _pillars(core) -> dict:
    return {k: v for k, v in core.natal_facts.pillars.items() if v}


def god(dm: str, stem: str) -> str:
    g = get_ten_god(dm, stem)
    return getattr(g, "value", str(g))


def branch_kind(a: str, b: str) -> str | None:
    """두 지지의 관계 하나(우선순위: 같음 > 육합 > 충 > 형 > 해 > 파 > 삼합 반합)."""
    if a == b:
        return "same"
    pair = frozenset((a, b))
    if SIX.get(a) == b:
        return "six"
    if CLASH.get(a) == b:
        return "clash"
    if punishes(a, b):
        return "punish"
    if pair in _HARM:
        return "harm"
    if pair in _BREAK:
        return "break"
    if any(a in t and b in t for t in TRIAD):
        return "triad"
    return None


def six_state(left: dict, right: dict, lk: str, rk: str) -> str:
    """육합이 온전한가: intact / disturbed(충으로 깨짐) / contested(쟁합)."""
    a, b = left[lk].branch, right[rk].branch
    others = [p.branch for k, p in left.items() if k != lk] + [p.branch for k, p in right.items() if k != rk]
    if any(CLASH.get(br) in (a, b) for br in others):
        return "disturbed"
    if any(br in (a, b) for br in others):  # 같은 글자가 하나 더 있음 → 한 글자가 두 곳과 합(쟁합)
        return "contested"
    return "intact"


def element_picture(core) -> dict:
    share = composition(core)
    tiers = element_tiers(core)["tiers"]
    return {
        "share": share, "tiers": tiers,
        "heavy": [e for e in ELEMENTS if share[e] >= HEAVY],
        "lack": [e for e in ELEMENTS if share[e] < LACK],
        "good": [e for e in ELEMENTS if tiers[e] == "good"],
    }


def _year_rows(left, right, el_l, el_r, start_year: int, n: int = 10) -> list[dict]:
    rows = []
    dl, dr = left.natal_facts.pillars["day"].branch, right.natal_facts.pillars["day"].branch
    for y in range(start_year, start_year + n):
        gz = year_gz(y)
        stem_el, br = GAN_WUXING[gz[0]], gz[1]
        row = {"year": y, "ganji": gz}
        for side, el, db in (("L", el_l, dl), ("R", el_r, dr)):
            tier = el["tiers"][stem_el]
            clash = CLASH.get(br) == db
            row[side] = "good" if (tier == "good" and not clash) else "hard" if (tier == "avoid" or clash) else "ok"
        rows.append(row)
    return rows


def _bits(core) -> tuple[dict | None, str | None]:
    """(지금 대운, 조후 상태). 한 번 만든 질의에서 함께 꺼낸다."""
    from app.engine.semantic import build_service_query

    q = build_service_query(core, "lifetime_overall")
    cur = (q["timing"]["luck_cycles"] or {}).get("current")
    climate = (q["synthesis"].get("climate_state") or {}).get("state")
    if not cur:
        return None, climate
    return ({"god": cur["ten_god"], "group": GROUP.get(cur["ten_god"]), "start_age": cur["start_age"],
             "end_age": cur["end_age"], "ganji": cur["pillar"]["ganji"], "element": cur["pillar"]["stem_element"]}, climate)


_COLD = {"very_cold_wet", "cold_wet", "cool_dry"}
_HOT = {"warm_dry", "hot_dry", "very_hot_dry"}


def temperature(state: str | None) -> str:
    return "cold" if state in _COLD else "hot" if state in _HOT else "mild"


def needed_elements(core, el: dict) -> list[str]:
    """이 사람에게 필요한 오행. 종합 판단(applied state)이 방향을 확정했으면 그것을, 아니면 3단계 '좋음'을 쓴다."""
    from app.engine.semantic.applied import build_applied_state, recommended_directions

    wanted = {e for d in recommended_directions(build_applied_state(core, "natal")) for e in d.get("elements", [])}
    picked = [e for e in ELEMENTS if e in wanted]
    return picked or list(el["good"])


def _self(core, el: dict) -> dict:
    strength = str(core.synthesis.strength_state or "")
    kind = "strong" if strength in {"strong", "extremely_strong"} else "weak" if strength in {"weak", "extremely_weak"} else None
    top = max(ELEMENTS, key=lambda e: el["share"][e])
    return {"top": top, "strength": kind}


def analyze_pair(left, right, this_year: int) -> dict:
    lp, rp = _pillars(left), _pillars(right)
    ldm, rdm = lp["day"].stem, rp["day"].stem
    l_sees_r, r_sees_l = god(ldm, rdm), god(rdm, ldm)
    # 자리별 지지 관계 (같은 자리끼리: 일·월·년)
    branches = {}
    for k in ("day", "month", "year"):
        if k in lp and k in rp:
            kind = branch_kind(lp[k].branch, rp[k].branch)
            branches[k] = {"kind": kind, "pair": lp[k].branch + rp[k].branch,
                           "state": six_state(lp, rp, k, k) if kind == "six" else None}
    # 일간끼리
    le, re_ = GAN_WUXING[ldm], GAN_WUXING[rdm]
    if frozenset((ldm, rdm)) in _STEM_SIX:
        stem_rel = "six"
    elif le == re_:
        stem_rel = "same"
    elif _CTL[le] == re_ or _CTL[re_] == le:
        stem_rel = "control"
    elif _GEN[le] == re_ or _GEN[re_] == le:
        stem_rel = "generate"
    else:
        stem_rel = None
    # 다른 자리 천간합(일간합 제외) — 한 쌍만 센다
    other_stem_six = None
    for lk, a in lp.items():
        for rk, b in rp.items():
            if (lk, rk) != ("day", "day") and frozenset((a.stem, b.stem)) in _STEM_SIX and "day" in (lk, rk):
                other_stem_six = {"left": lk, "right": rk, "pair": a.stem + b.stem}
                break
        if other_stem_six:
            break
    el_l, el_r = element_picture(left), element_picture(right)
    need_l, need_r = needed_elements(left, el_l), needed_elements(right, el_r)
    fills_l = [e for e in need_l if el_r["share"][e] >= FILL][:2]
    fills_r = [e for e in need_r if el_l["share"][e] >= FILL][:2]
    heavy_both = [e for e in el_l["heavy"] if e in el_r["heavy"]]
    lack_both = [e for e in el_l["lack"] if e in el_r["lack"]]
    (cl, clim_l), (cr, clim_r) = _bits(left), _bits(right)
    return {
        "gods": {"l_sees_r": l_sees_r, "r_sees_l": r_sees_l},
        "stem_rel": stem_rel, "other_stem_six": other_stem_six,
        "branches": branches,
        "el_l": el_l, "el_r": el_r, "fills_l": fills_l, "fills_r": fills_r,
        "heavy_both": heavy_both, "lack_both": lack_both,
        "cycles": {"L": cl, "R": cr},
        "climate": {"L": temperature(clim_l), "R": temperature(clim_r),
                    "very": {"L": bool(clim_l and clim_l.startswith("very")), "R": bool(clim_r and clim_r.startswith("very"))}},
        "need": {"L": need_l, "R": need_r},
        "years": _year_rows(left, right, el_l, el_r, this_year),
        "self": {"L": _self(left, el_l), "R": _self(right, el_r)},
        "time_unknown": {"L": bool(left.uncertainty.time_unknown), "R": bool(right.uncertainty.time_unknown)},
    }
