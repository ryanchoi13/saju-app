"""'지금의 나' 조립기 (lifetime-present-v4, 스펙 v0 2026-10-22).

원국 사실(natal_facts)만으로 비유 사전 행을 고르고, 섹션 0~4를 HTML 로 조립한다.
- 엔진 코어는 건드리지 않는다. 양인·홍염·시주 신뢰도는 여기서 계산한다.
- 문단마다 validate_paragraph 를 거친다. 장면 문장을 빼도 통과하지 못하면 ValueError 를 올린다
  (lifetime.py 가 받아서 옛 성향 본문으로 되돌린다).
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from html import escape

from app.engine.constants import GAN_WUXING
from app.engine.core.models import MyeongriCoreResult
from app.engine.services.annual_copy import ending_family, seed_from
from app.engine.services import now_me_copy as copy

NOW_ME_VERSION = "now-me-v1"

ELEMENT_ORDER = ("木", "火", "土", "金", "水")
PILLAR_ORDER = ("year", "month", "day", "hour")
_GROUP_OF = {
    "peer": "비겁", "rob_wealth": "비겁",
    "eating_god": "식상", "hurting_officer": "식상",
    "indirect_wealth": "재성", "direct_wealth": "재성",
    "seven_killings": "관성", "direct_officer": "관성",
    "indirect_resource": "인성", "direct_resource": "인성",
}
_GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
_CONTROLS = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}

# 양인(羊刃): 양간만 둔다. 음간(乙→辰, 丁·己→未, 辛→戌, 癸→丑 등)은 유파마다 달라 쓰지 않는다.
YANGIN_BRANCH = {"甲": "卯", "丙": "午", "戊": "午", "庚": "酉", "壬": "子"}
# 홍염(紅艶): 교과서 통용 조견. 출처 미확보(사전 C2 비고).
HONGYEOM_BRANCH = {"甲": "午", "乙": "申", "丙": "寅", "丁": "未", "戊": "辰",
                   "己": "辰", "庚": "戌", "辛": "酉", "壬": "子", "癸": "申"}
LINK_HREF = {"gunghap": "#concern-gunghap", "business": "#concern-business"}


# ---------------------------------------------------------------------------
# 1. 원국 프로필
# ---------------------------------------------------------------------------
def _group_elements(day_element: str) -> dict[str, str]:
    """일간 오행 기준으로 십성 그룹이 가리키는 오행."""
    controlled_by = next(k for k, v in _CONTROLS.items() if v == day_element)
    generated_by = next(k for k, v in _GENERATES.items() if v == day_element)
    return {"비겁": day_element, "식상": _GENERATES[day_element], "재성": _CONTROLS[day_element],
            "관성": controlled_by, "인성": generated_by}


def hour_confidence(core: MyeongriCoreResult) -> str:
    """시주 신뢰도. 시주 없음 → unknown, 평균태양시가 홀수 시 경계(01,03,…,23시)에서 15분 안쪽 → low."""
    if core.natal_facts.pillars.get("hour") is None:
        return "unknown"
    raw = (core.natal_facts.calendar or {}).get("solar_time_used")
    if not raw:
        return "unknown"
    try:
        moment = datetime.fromisoformat(raw)
    except ValueError:
        return "unknown"
    minutes = moment.hour * 60 + moment.minute
    distance = min(abs(minutes - 60 * h) for h in range(-1, 25, 2))  # -1h/25h 로 자정 너머 경계도 본다
    return "low" if distance < 15 else "high"


def natal_profile(core: MyeongriCoreResult) -> dict:
    facts = core.natal_facts
    day = facts.day_master
    pillars = {k: v for k, v in facts.pillars.items() if v is not None}

    element_main: Counter = Counter()
    element_hidden: set[str] = set()
    group_main: Counter = Counter()
    group_hidden: set[str] = set()
    god_main: Counter = Counter()
    branches: dict[str, str] = {}

    for name in PILLAR_ORDER:
        pillar = pillars.get(name)
        if pillar is None:
            continue
        element_main[pillar.stem_element] += 1
        branches[name] = pillar.branch
    for fact in facts.ten_gods.visible:
        if fact.ten_god.value == "day_master":
            continue
        group_main[_GROUP_OF[fact.ten_god.value]] += 1
        god_main[fact.ten_god.value] += 1
    for fact in facts.ten_gods.hidden:
        group = _GROUP_OF[fact.ten_god.value]
        element = GAN_WUXING[fact.stem]
        element_hidden.add(element)
        if fact.hidden_role is not None and fact.hidden_role.value == "main":
            element_main[element] += 1
            group_main[group] += 1
            god_main[fact.ten_god.value] += 1
        else:
            group_hidden.add(group)

    def element_state(count: int) -> str:
        if count >= 3:
            return "many"
        if count == 0:
            return "none"
        return "few" if count == 1 else "middle"

    elements = {
        e: {"main": element_main[e], "state": element_state(element_main[e]), "hidden": e in element_hidden}
        for e in ELEMENT_ORDER
    }
    groups = {
        g: {"main": group_main[g],
            "state": "many" if group_main[g] >= 2 else ("none" if group_main[g] == 0 else "middle"),
            "hidden": g in group_hidden}
        for g in ("비겁", "식상", "재성", "관성", "인성")
    }
    month_branch = branches.get("month")
    yangin_branch = YANGIN_BRANCH.get(day.stem)
    natal_shensha = {s.name for s in core.shensha if "natal" in s.source}
    confidence = hour_confidence(core)
    officer_main = groups["관성"]["main"]
    officer_hidden = groups["관성"]["hidden"]
    return {
        "day_master": day.stem,
        "day_element": day.element,
        "pillars": {k: pillars[k].ganji for k in PILLAR_ORDER if k in pillars},
        "glyphs": len(pillars) * 2,
        "elements": elements,
        "groups": groups,
        "gods": dict(god_main),
        "rob_wealth": god_main["rob_wealth"],
        "yangin": {"month": yangin_branch is not None and month_branch == yangin_branch,
                   "any": yangin_branch is not None and yangin_branch in branches.values(),
                   "branch": yangin_branch},
        "hongyeom": HONGYEOM_BRANCH.get(day.stem) in branches.values(),
        "peach_blossom": "peach_blossom" in natal_shensha,
        "flower_canopy": "flower_canopy" in natal_shensha,
        "crowd_rob_wealth": group_main["재성"] >= 2 and god_main["rob_wealth"] >= 1,
        "no_officer": officer_main == 0 and not officer_hidden,
        "officer_hidden_only": officer_main == 0 and officer_hidden,
        "hour_confidence": confidence,
        "group_elements": _group_elements(day.element),
    }


# ---------------------------------------------------------------------------
# 2. 행 선택 (스펙 §3 우선순위: B16 > B11 > B17/B18 > A 없음 > A 많음 > B 발달 > B 없음 > A 적음)
# ---------------------------------------------------------------------------
def _evidence_text(row: dict, profile: dict) -> str:
    key = row["key"]
    if key == "B16":
        return row["evidence"].format(n=profile["groups"]["재성"]["main"], m=profile["rob_wealth"])
    if key == "B11":
        where = (f"월지 {profile['pillars']['month'][1]} 겁재" if profile["yangin"]["month"]
                 else f"겁재 {profile['rob_wealth']}")
        return row["evidence"].format(where=where)
    if key == "B18" and profile["hour_confidence"] != "high":
        return "관성 적음"
    if "element" in row:
        info = profile["elements"][row["element"]]
        return row["evidence"].format(n=info["main"], hidden="겉면 없음" if info["hidden"] else "없음")
    if "group" in row:
        info = profile["groups"][row["group"]]
        return row["evidence"].format(n=info["main"], hidden="겉면 없음" if info["hidden"] else "없음")
    return row["evidence"]


def select_rows(profile: dict) -> list[dict]:
    """해당하는 행을 우선순위대로 돌려준다. 같은 대상 중복은 하나만 남긴다."""
    rows = copy.ALL_ROWS
    picked: list[dict] = []
    used_groups: set[str] = set()
    used_elements: set[str] = set()
    group_element = profile["group_elements"]
    low_hour = profile["hour_confidence"] != "high"

    def take(key: str):
        row = rows[key]
        picked.append(row)
        if "group" in row:
            used_groups.add(row["group"])
        if "element" in row:
            used_elements.add(row["element"])

    strong_rob = profile["rob_wealth"] >= 1 and (profile["yangin"]["month"] or profile["rob_wealth"] >= 2)
    if strong_rob:
        take("B11")                                   # 성격은 겁재·양인이 먼저(10/23). 사전 '겁재 ≥1, 특히 월지 양인' — 겁재 하나만으로는 고르지 않는다
    if profile["crowd_rob_wealth"]:
        take("B16")                                   # 재성·겁재 두 그룹을 함께 덮는다. B11 뒤에 오면 '뒷면' 문단 재료가 된다
        used_groups.add("비겁")
    if profile["no_officer"] and not low_hour:
        take("B17")
    elif profile["groups"]["관성"]["main"] == 0:
        take("B18")                                   # 시주 신뢰도 낮으면 B17 대신 B18 문구(단정 없음)
    # A 없음 → 같은 오행의 B 없음 행은 뒤에서 거른다
    for e in ELEMENT_ORDER:
        if profile["elements"][e]["state"] == "none" and e not in used_elements:
            take(_element_row(e, "none"))
    # B 발달이 같은 오행을 가리키면 A 많음을 버린다(甲 일간의 A4·B3 등)
    many_groups = {g for g, info in profile["groups"].items() if info["state"] == "many"}
    for e in ELEMENT_ORDER:
        if profile["elements"][e]["state"] != "many" or e in used_elements:
            continue
        if any(group_element[g] == e for g in many_groups):
            continue
        take(_element_row(e, "many"))
    for g in ("비겁", "식상", "재성", "관성", "인성"):
        if profile["groups"][g]["state"] == "many" and g not in used_groups:
            take(_group_row(g, "many"))
    for g in ("비겁", "식상", "재성", "인성"):          # 관성 없음은 B17/B18 이 맡는다
        if profile["groups"][g]["state"] == "none" and g not in used_groups \
                and group_element[g] not in used_elements:
            take(_group_row(g, "none"))
    # 맨 끝 안전망: 시주 미상(5글자)에서 많음·없음·발달이 하나도 없을 수 있다 → A 적음 행(정기 1)
    for e in ELEMENT_ORDER:
        if profile["elements"][e]["state"] == "few" and e not in used_elements:
            take(_element_row(e, "few"))
    return picked


def _element_row(element: str, state: str) -> str:
    return next(r["key"] for r in copy.ELEMENT_ROWS if r["element"] == element and r["state"] == state)


def _group_row(group: str, state: str) -> str:
    return next(r["key"] for r in copy.TEN_GOD_ROWS if r.get("group") == group and r["state"] == state)


def shensha_rows(profile: dict) -> list[dict]:
    out = []
    if profile["peach_blossom"]:
        out.append(copy.ALL_ROWS["C1"])
    if profile["hongyeom"]:
        out.append(copy.ALL_ROWS["C2"])
    if profile["flower_canopy"]:
        out.append(copy.ALL_ROWS["C3"])
    return out


# ---------------------------------------------------------------------------
# 3. 문단 조립
# ---------------------------------------------------------------------------
def _pick(pool, seed: int, shift: int):
    return pool[(seed >> shift) % len(pool)]


def _scene(row: dict, seed: int, shift: int, avoid_ending: str, exclude: str | None = None) -> str | None:
    pool = copy.SCENES.get(row.get("scene_key") or "")
    if not pool:
        return None
    start = (seed >> shift) % len(pool)
    ordered = [pool[(start + i) % len(pool)] for i in range(len(pool))]
    ordered = [s for s in ordered if s != exclude] or ordered
    for s in ordered:                                 # 같은 어미 연속을 피한다
        if ending_family(s) != avoid_ending:
            return s
    return ordered[0]


def _validated(sentences: list[str], scene_index: int | None, allow_absolute: bool, where: str) -> str:
    text = " ".join(s for s in sentences if s)
    issues = copy.validate_paragraph(text, allow_absolute=allow_absolute)
    if issues and scene_index is not None:
        trimmed = [s for i, s in enumerate(sentences) if i != scene_index]
        text = " ".join(s for s in trimmed if s)
        issues = copy.validate_paragraph(text, allow_absolute=allow_absolute)
    if issues:
        raise ValueError(f"now_me {where}: {issues}")
    return text


def _chapter(row: dict, label: str, body: str, evidence: str) -> str:
    return (f'<article class="reading-chapter now-me-chapter" data-now-me-row="{escape(row["key"])}">'
            f'<h3>{escape(label, quote=False)}</h3><p>{escape(body)}</p>'
            f'<small class="now-me-evidence">원국 · {escape(evidence)}</small></article>')


def _section(section_id: str, inner: str) -> str:
    title = copy.SECTION_TITLES[section_id]
    return (f'<div class="now-me-section" data-now-me-section="{section_id}">'
            f'<p class="now-me-section-title">{escape(title)}</p>{inner}</div>')


def _line(section_id: str, text: str, link: str, evidence: str) -> str:
    return _section(section_id,
                    f'<p class="now-me-line">{escape(text)} '
                    f'<a class="now-me-link" href="{LINK_HREF[link]}" data-now-me-link="{link}">'
                    f'{escape(copy.LINK_LABELS[link])}</a></p>'
                    f'<small class="now-me-evidence">원국 · {escape(evidence)}</small>')


def build_now_me(core: MyeongriCoreResult, user_name: str) -> dict:
    profile = natal_profile(core)
    seed = seed_from(*profile["pillars"].values())
    name = escape(user_name or "회원")
    ordered = select_rows(profile)
    if not ordered:
        raise ValueError("now_me: 해당하는 사전 행이 없습니다")
    sections: list[dict] = []
    used_keys: set[str] = set()

    # 0. 머리말 — 표 D 는 여기서만
    day_row = copy.DAY_MASTER_ROWS[profile["day_master"]]
    pillars_text = " ".join(profile["pillars"].values())
    lead = (f'<p class="now-me-lead">{name}님의 원국은 <strong>{escape(day_row["label"])}</strong>입니다. '
            f'<span class="now-me-pillars">{escape(pillars_text)}</span></p>')
    sections.append({"id": "lead", "row": day_row["key"]})

    # 1. 타고난 결 — 장점(성향+장면 2) + 뒷면(뒷면+팁)
    top = ordered[0]
    used_keys.add(top["key"])
    allow = bool(top.get("allow_absolute"))
    trait_ending = ending_family(top["trait"])
    scene_a = _scene(top, seed, 3, trait_ending)
    scene_b = _scene(top, seed, 7, ending_family(scene_a or top["trait"]), exclude=scene_a)
    strong_sentences = [top["trait"], scene_a or "", scene_b or ""]
    strong = _validated(strong_sentences, 1, allow, f"core.{top['key']}")
    # 뒷면: B11(겁재·양인) 다음에 B16(군겁쟁재)이 있으면 그 뒷면·팁을 쓴다 — 같은 겁재의 두 얼굴
    flip_row = top
    if top["key"] == "B11" and len(ordered) > 1 and ordered[1]["key"] == "B16":
        flip_row = ordered[1]
        used_keys.add(flip_row["key"])
    flip = _validated([flip_row["flip"], flip_row["tip"]], None, bool(flip_row.get("allow_absolute")),
                      f"flip.{flip_row['key']}")
    evidence_top = _evidence_text(top, profile)
    evidence_flip = _evidence_text(flip_row, profile)
    core_html = (_chapter(top, f"'{top['label']}'", strong, evidence_top)
                 + _chapter(flip_row, copy.FLIP_FRAME.format(label=top["label"]), flip, evidence_flip))
    sections.append({"id": "core", "row": top["key"], "flip_row": flip_row["key"], "evidence": evidence_top})

    # 2. 사람들이 먼저 보는 것 — 식상·재성·비겁 발달 행, 없으면 도화·홍염, 그래도 없으면 남은 행
    visible_groups = sorted(("식상", "재성", "비겁"),
                            key=lambda g: -profile["groups"][g]["main"])
    candidates = [copy.ALL_ROWS[_group_row(g, "many")] for g in visible_groups
                  if profile["groups"][g]["state"] == "many"]
    candidates += shensha_rows(profile)
    candidates += [r for r in ordered if r.get("state") in ("many", "few") or r["key"] == "B11"]
    second = next((r for r in candidates if r["key"] not in used_keys
                   and not ("B16" in (top["key"], flip_row["key"]) and r.get("group") in ("재성", "비겁"))), None)
    first_seen_html = ""
    if second is not None:
        used_keys.add(second["key"])
        allow2 = bool(second.get("allow_absolute"))
        scene = _scene(second, seed, 11, ending_family(second["trait"]))
        body = _validated([second["trait"], scene or "", second["tip"]], 1, allow2, f"first-seen.{second['key']}")
        evidence2 = _evidence_text(second, profile)
        first_seen_html = _section("first-seen", _chapter(second, f"'{second['label']}'", body, evidence2))
        sections.append({"id": "first-seen", "row": second["key"], "evidence": evidence2})

    # 3. 곁에 두면 편한 사람 — 첫 결핍 오행의 '사람' 항목
    lacking = next((copy.ALL_ROWS[_element_row(e, "none")] for e in ELEMENT_ORDER
                    if profile["elements"][e]["state"] == "none"), None)
    if lacking is not None:
        people_text = lacking["people"]
        people_evidence = _evidence_text(lacking, profile)
        people_row = lacking["key"]
    else:
        people_text, people_evidence, people_row = copy.PEOPLE_NEUTRAL, "오행 결핍 없음", None
    _validated([people_text], None, False, "people")
    people_html = _line("people", people_text, "gunghap", people_evidence)
    sections.append({"id": "people", "row": people_row, "evidence": people_evidence})

    # 4. 힘이 나는 자리 — 관성 유무
    officer = profile["groups"]["관성"]
    if officer["state"] == "many":
        place_key, place_evidence = "organized", f"관성 {officer['main']}"
    elif officer["main"] == 0 and profile["hour_confidence"] == "high":
        place_key = "autonomous"
        place_evidence = "관성 없음" if profile["no_officer"] else "관성 겉면 없음"
    elif officer["main"] == 0:
        place_key, place_evidence = "neutral", "관성 적음"
    else:
        place_key, place_evidence = "neutral", f"관성 {officer['main']}"
    place_text = copy.PLACE_LINES[place_key]
    _validated([place_text], None, False, "place")
    place_html = _line("place", place_text, "business", place_evidence)
    sections.append({"id": "place", "row": place_key, "evidence": place_evidence})

    html = lead + _section("core", core_html) + first_seen_html + people_html + place_html
    evidence = {
        "profile": {k: v for k, v in profile.items() if k != "group_elements"},
        "ordered_rows": [r["key"] for r in ordered],
        "hour_confidence": profile["hour_confidence"],
    }
    return {"html": html, "sections": sections, "evidence": evidence,
            "copy_version": copy.COPY_VERSION, "version": NOW_ME_VERSION}
