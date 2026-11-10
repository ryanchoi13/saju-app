"""분야 결 규칙표 (11/10 정오님: "숫자 더하기 대신 이름 붙은 규칙으로").

예전 daily_score.domain_delta 는 십성·충형에 무게를 더해 ±6 문턱으로 좋음·보통·주의를 갈랐다.
무게에 근거가 없었고, 빠진 규칙(비겁 날의 탈재)이 보이지 않았다(금전 보통 81%·주의 2%).
여기서는 분야마다 이름 붙은 조건으로 결을 정하고, 걸린 이유를 함께 돌려준다.

- 십성은 천간으로 들어온 것만 판정에 쓴다. 지지 본기까지 세면 하루에 두 십성이 걸려 금전·건강 주의가 40%를 넘었다.
  지지 본기로만 들어온 기운은 '보통'의 기울기(lean: 위/아래)로만 쓴다(헌장: 근거가 중간이면 기울기).
- 강약(daily_score.yong_direction)이 보류인 사람은 "필요한 기운인가"를 궁통보감 조후로 본다(정오님 11/10 추천안 1).
- 재성이 들어오는데 신약(재다신약)은 하루 일진 하나로 흉까지 보지 않는다(추천안 2). 재고는 넣지 않음(추천안 3).
- 좋음·주의가 함께 걸리면 주의. 등급과 반대로 가는 분야가 둘 이상이면 가장 센 하나만 남기고 나머지는
  기울기 있는 보통으로 내린다(11/10 정오님 (가)).
"""
from __future__ import annotations

from app.engine.constants import GAN_WUXING, ZHI_WUXING
from app.engine.core.models import MyeongriCoreResult, TenGod
from app.engine.facts.hidden_stems import get_hidden_stems
from app.engine.facts.ten_gods import get_ten_god
from app.engine.services.element_balance import CONTROLS, EXCESS_SHARE, _gungtong, composition

RULES_VERSION = "domain-rules-v1"
DOMAINS = ("금전", "사람", "일", "건강")
GOOD_GRADES, BAD_GRADES = ("좋음", "아주 좋음"), ("주의", "나쁨")

GROUP = {
    TenGod.PEER: "peer", TenGod.ROB_WEALTH: "peer",
    TenGod.EATING_GOD: "output", TenGod.HURTING_OFFICER: "output",
    TenGod.INDIRECT_WEALTH: "wealth", TenGod.DIRECT_WEALTH: "wealth",
    TenGod.SEVEN_KILLINGS: "officer", TenGod.DIRECT_OFFICER: "officer",
    TenGod.INDIRECT_RESOURCE: "resource", TenGod.DIRECT_RESOURCE: "resource",
}

# 이유의 세기 — 엇갈림 정리((가))와 튀는 분야 고르기에만 쓴다. 3 = 원국 자리를 직접 치는 충(형은 2).
SEVERITY = {
    "일지 충": 3, "재성 자리 충": 3, "월지 충": 3,          # 충은 자리를 깨고, 형은 긁는다
    "일지 형": 2, "재성 자리 형": 2, "월지 형": 2,
    "일간 천간충": 2, "비겁 · 탈재": 2, "관성 · 압박": 2, "양인·백호": 2,
    "상관견관": 1, "넘치는 오행이 또 들어옴": 1,
    "재성 유입 · 감당할 힘": 2, "비겁 · 감당할 힘": 2, "식상생재": 2, "일지 합": 2, "일간 천간합": 2,
    "관성 · 감당": 2, "식상 · 해낸 일": 2, "인성 · 도움": 2,
    "이성 인연의 기운": 1, "인성 · 회복": 1,
    "관성 · 필요한 기운": 1, "식상 · 필요한 기운": 1, "인성 · 필요한 기운": 1,
}
DOMAIN_ORDER = ("사람", "건강", "금전", "일")      # 세기가 같을 때 먼저 말할 분야(일지 = 배우자 자리라 사람이 먼저)


def _arrival(dm: str, stem: str) -> tuple[TenGod, str]:
    return get_ten_god(dm, stem), GAN_WUXING[stem]


def _needed(group: str, element: str, direction: str | None, gt) -> bool | None:
    """이 기운이 나한테 필요한가. 강약이 정해졌으면 억부, 보류면 궁통보감 조후(1·2순위 = 필요, 꺼림 = 불필요)."""
    if direction == "strong":
        return group in ("output", "wealth", "officer")
    if direction == "weak":
        return group in ("peer", "resource")
    if gt:
        picks, shunned, _ = gt
        if element in picks:
            return True
        if element in shunned:
            return False
    return None


def _god_rules(core, god: TenGod, element: str, direction, gt, comp, natal_gods, out) -> None:
    """한 십성이 들어올 때 걸리는 규칙(천간이면 판정, 지지 본기면 기울기)."""
    group = GROUP[god]
    gender = str(getattr(core.input, "gender", "") or "")
    strong, weak, undecided = direction == "strong", direction == "weak", direction is None
    need = _needed(group, element, direction, gt)
    natal_groups = {GROUP[g] for g in natal_gods if g in GROUP}
    m, s, w, h = out["금전"], out["사람"], out["일"], out["건강"]
    # 금전
    if group == "wealth" and (strong or (undecided and need)):
        m["good"].append("재성 유입 · 감당할 힘")
    if group == "output" and strong:
        m["good"].append("식상생재")
    if group == "peer" and weak:
        m["good"].append("비겁 · 감당할 힘")      # 신약: 비겁이 재물을 감당할 힘을 보탠다(득비이재)
    if group == "peer" and not weak and not (undecided and need):
        m["bad"].append("비겁 · 탈재")
    # 애정·관계
    if (gender == "male" and group == "wealth") or (gender == "female" and group == "officer"):
        s["good"].append("이성 인연의 기운")
    if gender == "female" and god == TenGod.HURTING_OFFICER and "officer" in natal_groups:
        s["bad"].append("상관견관")
    # 일
    if group == "officer" and strong:
        w["good"].append("관성 · 감당")
    if group == "output" and strong:
        w["good"].append("식상 · 해낸 일")
    if group == "resource" and weak:
        w["good"].append("인성 · 도움")
    if undecided and need:
        label = {"officer": "관성", "output": "식상", "resource": "인성"}.get(group)
        if label:
            w["good"].append(f"{label} · 필요한 기운")
    if group == "officer" and weak:
        w["bad"].append("관성 · 압박")
    if god == TenGod.HURTING_OFFICER and TenGod.DIRECT_OFFICER in natal_gods:
        w["bad"].append("상관견관")
    # 건강
    if group == "resource" and comp.get(element, 0) < EXCESS_SHARE:
        h["good"].append("인성 · 회복")
    if comp.get(element, 0) >= EXCESS_SHARE:
        h["bad"].append("넘치는 오행이 또 들어옴")


def _empty() -> dict:
    return {k: {"good": [], "bad": []} for k in DOMAINS}


def _sev(reasons: list[str]) -> int:
    return max((SEVERITY.get(r, 1) for r in reasons), default=0)


def evaluate_domains(core: MyeongriCoreResult, day_pillar: str, items: list[tuple[str, int]],
                     direction: str | None, grade: str | None = None) -> dict[str, dict]:
    """{분야: {"tier": 좋음|보통|주의, "lean": "위"|"아래"|None, "good": [이유], "bad": [이유], "eased": 이유|None}}.

    분야 이름은 금전·사람·일·건강(daily_score 와 같은 이름). grade 를 주면 엇갈림 정리((가))까지 한다."""
    p = core.natal_facts.pillars
    dm = p["day"].stem
    comp = composition(core)
    gt = _gungtong(core, comp) if direction is None else None
    names = {n for n, _ in items}
    natal_gods = {get_ten_god(dm, p[k].stem) for k in ("year", "month", "hour") if p.get(k)}
    natal_gods |= {get_ten_god(dm, get_hidden_stems(p[k].branch).stems[0].stem)
                   for k in ("year", "month", "day", "hour") if p.get(k)}

    out = _empty()
    god, el = _arrival(dm, day_pillar[0])
    _god_rules(core, god, el, direction, gt, comp, natal_gods, out)

    m, s, w, h = out["금전"], out["사람"], out["일"], out["건강"]
    wealth_el = CONTROLS[GAN_WUXING[dm]]
    wealth_pos = [k for k in ("year", "month", "day", "hour") if p.get(k) and ZHI_WUXING[p[k].branch] == wealth_el]
    day_hit = {"day지 충", "day지 형"} & names
    day_kind = "충" if "day지 충" in names else "형"
    for k in ("충", "형"):
        if any(f"{pos}지 {k}" in names for pos in wealth_pos):
            m["bad"].append(f"재성 자리 {k}")
            break
    if {"day지 육합", "day지 반합"} & names:          # 삼합은 어느 자리인지 몰라 뺀다
        s["good"].append("일지 합")
    if "일간 천간합" in names:
        s["good"].append("일간 천간합")
    if day_hit:
        s["bad"].append(f"일지 {day_kind}")
        h["bad"].append(f"일지 {day_kind}")
    if "일간 천간충" in names:
        s["bad"].append("일간 천간충")
    if {"month지 충", "month지 형"} & names:
        w["bad"].append("월지 충" if "month지 충" in names else "월지 형")
    if {"양인 일진", "백호 일진"} & names and day_hit:   # 양인·백호만으로는 주의로 보지 않는다(일진 신살은 근거가 약함)
        h["bad"].append("양인·백호")

    # 지지 본기로만 들어온 기운 → 보통의 기울기
    lean_out = _empty()
    main = get_hidden_stems(day_pillar[1]).stems[0].stem
    bgod, bel = _arrival(dm, main)
    _god_rules(core, bgod, bel, direction, gt, comp, natal_gods, lean_out)

    for dom, v in out.items():
        v["tier"] = "주의" if v["bad"] else ("좋음" if v["good"] else "보통")
        lv = lean_out[dom]
        v["lean"] = None
        v["lean_reason"] = None
        if v["tier"] == "보통":
            if lv["bad"]:
                v["lean"], v["lean_reason"] = "아래", lv["bad"][0]
            elif lv["good"]:
                v["lean"], v["lean_reason"] = "위", lv["good"][0]
        v["eased"] = None

    if grade:
        _ease_conflicts(out, grade)
    return out


def _ease_conflicts(out: dict, grade: str) -> None:
    """(가) 등급과 반대로 가는 분야가 둘 이상이면 가장 센 하나만 남기고 나머지는 같은 쪽 기울기의 보통으로."""
    if grade in GOOD_GRADES:
        against, lean = "주의", "아래"
    elif grade in BAD_GRADES:
        against, lean = "좋음", "위"
    else:
        return
    key = "bad" if against == "주의" else "good"
    hits = [d for d in DOMAINS if out[d]["tier"] == against]
    if len(hits) < 2:
        return
    hits.sort(key=lambda d: (-_sev(out[d][key]), DOMAIN_ORDER.index(d)))
    for d in hits[1:]:
        v = out[d]
        v["tier"], v["lean"], v["lean_reason"], v["eased"] = "보통", lean, v[key][0], v[key][0]


def standout(rules: dict, grade: str) -> tuple[str, str] | None:
    """튀는 분야: 원국 자리를 치는 주의(세기 3)가 먼저, 아니면 좋은 날의 좋음(세기 2 이상). 없으면 None."""
    bad = [d for d in DOMAINS if rules[d]["tier"] == "주의" and _sev(rules[d]["bad"]) >= 3]
    if bad:
        return min(bad, key=DOMAIN_ORDER.index), "주의"
    if grade in GOOD_GRADES:
        good = [d for d in DOMAINS if rules[d]["tier"] == "좋음" and _sev(rules[d]["good"]) >= 2]
        if good:
            return max(good, key=lambda d: (_sev(rules[d]["good"]), -DOMAIN_ORDER.index(d))), "좋음"
    return None
