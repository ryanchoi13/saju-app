"""평생운세 v3 조립기 (B안 v3, 2026-10-23 결정).

원국표 → 1. 원국 지도 → 2. 타고난 결 → 3. 먼저 보는 것 → 4. 분야별 → 5. 인생의 흐름 → 6. 한마디.
- 성격 행 선택·장면·검증은 '지금의 나'(now_me) 를 그대로 쓴다.
- 풀이가 먼저, 근거는 문단 끝 '왜 그런가요' 접힘으로.
- 다음 대운 본문은 만들지 않는다(티저 한 줄만). 표에는 나이·간지·십성 이름만 싣는다.
- 문단마다 validate_paragraph 를 거친다. 통과하지 못하면 ValueError — lifetime.py 가 옛 v4 로 되돌린다.
"""

from __future__ import annotations

from collections import Counter
from datetime import date
from html import escape

from app.engine.constants import GAN_WUXING
from app.engine.core.models import MyeongriCoreResult
from app.engine.korean import josa
from app.engine.services.annual_copy import ending_family, seed_from
from app.engine.services import lifetime_copy as cycle_copy
from app.engine.services import lifetime_v3_copy as copy
from app.engine.services import now_me_copy as bank
from app.engine.services.now_me import (
    ELEMENT_ORDER, natal_profile, select_rows, shensha_rows, _group_row, _element_row,
    _evidence_text, _scene,
)

V3_VERSION = "lifetime-v3"
ZHI = "子丑寅卯辰巳午未申酉戌亥"
CLASH = {a: b for a, b in ("子午", "丑未", "寅申", "卯酉", "辰戌", "巳亥", "午子", "未丑", "申寅", "酉卯", "戌辰", "亥巳")}
CLIMATE_KO = {
    "very_cold_wet": "매우 차고 습함", "cold_wet": "차고 습함", "cool_dry": "서늘하고 건조함",
    "mild_wet": "온화하나 습함", "mild_balanced": "한난조습 고름", "warm_dry": "따뜻하고 건조함",
    "hot_dry": "덥고 건조함", "very_hot_dry": "매우 덥고 건조함",
}
HOT = {"warm_dry", "hot_dry", "very_hot_dry"}
COLD = {"very_cold_wet", "cold_wet", "cool_dry"}


def _p(sentences, *, allow_absolute=False, droppable=(), where="") -> str:
    """문장 목록을 한 문단으로. 검증에 걸리면 droppable(장면) 문장부터 빼 본다."""
    sentences = [s for s in sentences if s]
    text = " ".join(sentences)
    if bank.validate_paragraph(text, allow_absolute=allow_absolute):
        sentences = [s for i, s in enumerate(sentences) if i not in droppable]
        text = " ".join(sentences)
    issues = bank.validate_paragraph(text, allow_absolute=allow_absolute)
    if issues:
        raise ValueError(f"lifetime_v3 {where}: {issues}")
    return text


def _why(*lines: str) -> str:
    body = "".join(f"<p>{escape(line)}</p>" for line in lines if line)
    return f'<details class="lifetime-why"><summary>{copy.WHY_LABEL}</summary>{body}</details>'


def _section(sid: str, number: int, inner: str) -> str:
    return (f'<section class="lifetime-v3-section" data-lifetime-section="{sid}">'
            f'<h3>{number}. {escape(copy.SECTION_TITLES[sid])}</h3>{inner}</section>')


# ---------------------------------------------------------------------------
# 원국표
# ---------------------------------------------------------------------------
def _hidden_by_pillar(core: MyeongriCoreResult) -> dict[str, list[str]]:
    order = {"residual": 0, "middle": 1, "main": 2}
    out: dict[str, list[tuple[int, str]]] = {}
    for fact in core.natal_facts.ten_gods.hidden:
        role = fact.hidden_role.value if fact.hidden_role is not None else "main"
        out.setdefault(fact.pillar, []).append((order.get(role, 2), fact.stem))
    return {k: [s for _, s in sorted(v)] for k, v in out.items()}


def _hidden_counts(core: MyeongriCoreResult) -> Counter:
    """정기(겉면에 이미 센 글자)를 뺀 지장간 오행 개수."""
    counts: Counter = Counter()
    for fact in core.natal_facts.ten_gods.hidden:
        if fact.hidden_role is not None and fact.hidden_role.value == "main":
            continue
        counts[GAN_WUXING[fact.stem]] += 1
    return counts


def _chart_html(core, profile, hidden_counts) -> str:
    pillars = core.natal_facts.pillars
    hidden = _hidden_by_pillar(core)
    cols = (("hour", "時"), ("day", "日"), ("month", "月"), ("year", "年"))
    head = "".join(f"<th>{label}</th>" for _, label in cols)

    def cell(text, strong=False):
        return f"<td>{'<strong>' + text + '</strong>' if strong else text}</td>"

    stems, branches, hides = [], [], []
    for key, _ in cols:
        p = pillars.get(key)
        if p is None:
            stems.append(cell("모름")); branches.append(cell("모름")); hides.append(cell("—"))
            continue
        stems.append(cell(f"{p.stem} {copy.ELEMENT[p.stem_element]['name']}", strong=key == "day"))
        branches.append(cell(f"{p.branch} {copy.ELEMENT[p.branch_element]['name']}"))
        hides.append(cell(" ".join(hidden.get(key, [])) or "—"))
    table = ('<table class="lifetime-chart"><thead><tr><th></th>' + head + '</tr></thead><tbody>'
             '<tr><th>천간</th>' + "".join(stems) + '</tr><tr><th>지지</th>' + "".join(branches) + '</tr>'
             '<tr><th>지장간</th>' + "".join(hides) + '</tr></tbody></table>')
    surface = " · ".join(f"{copy.ELEMENT[e]['name']} {profile['elements'][e]['main']}" for e in ELEMENT_ORDER)
    lines = [f"겉면 {_glyphs(profile)}: {surface}"]
    missing = [e for e in ELEMENT_ORDER if profile["elements"][e]["main"] == 0]
    if missing:
        deep = " · ".join(f"{copy.ELEMENT[e]['name']} {hidden_counts[e]}" for e in missing)
        lines.append(f"글자 속(지장간)까지: {deep}")
    return table + "".join(f'<p class="lifetime-chart-count">{escape(l)}</p>' for l in lines)


def _glyphs(profile) -> str:
    return "여덟 글자" if profile["glyphs"] >= 8 else "여섯 글자"


# ---------------------------------------------------------------------------
# 1. 원국 지도
# ---------------------------------------------------------------------------
def _map(core, profile, hidden_counts, core_keys) -> tuple[str, dict]:
    day = bank.DAY_MASTER_ROWS[profile["day_master"]]
    month = core.natal_facts.pillars.get("month")
    season = copy.SEASON.get(month.branch, "") if month else ""
    els = profile["elements"]
    present = [e for e in sorted(ELEMENT_ORDER, key=lambda e: -els[e]["main"])
               if els[e]["main"] > 0 and e != profile["day_element"]][:2]
    lead = copy.MAP_LEAD if profile["glyphs"] >= 8 else copy.MAP_LEAD_SIX
    where = f"{season}에 " if season else ""
    first = [lead, f"그림으로 옮기면 {where}{josa(day['label'], '이/가')} 보이는 풍경입니다."]
    if present:
        clauses = [copy.ELEMENT[e]["scene"] for e in present[:-1]] + [copy.ELEMENT[present[-1]]["scene_end"]]
        first.append("그 곁으로 " + " ".join(clauses) + ".")
    first.append(f"{josa(day['label'], '은/는')} {day['trait']}")
    p1 = _p(first, where="map.1")

    missing = [e for e in ELEMENT_ORDER if els[e]["main"] == 0]
    second, third = [], []
    if missing:
        names = "와 ".join(copy.ELEMENT[e]["name"] for e in missing) if len(missing) == 2 else \
            ", ".join(copy.ELEMENT[e]["name"] for e in missing)
        second.append(copy.MAP_MISSING_ONE.format(names=names, josa=josa(names, "이/가")[len(names):]))
        hidden_plain, deep_plain = [], []
        for e in missing:
            info = copy.ELEMENT[e]
            j = josa(info["name"], "은/는")[len(info["name"]):]
            if hidden_counts[e]:
                second.append(copy.MAP_MISSING_HIDDEN.format(name=info["name"], josa=j, power=info["power"], k=hidden_counts[e]))
                hidden_plain.append(info["plain"])
            else:
                second.append(copy.MAP_MISSING_DEEP.format(name=info["name"], josa=j, power=info["power"]))
                deep_plain.append(info["plain"])
        names = {copy.ELEMENT[e]["plain"]: copy.ELEMENT[e]["name"] for e in missing}
        for plains, tpl in ((hidden_plain, copy.MAP_MEANS_HIDDEN), (deep_plain, copy.MAP_MEANS_DEEP)):
            if plains:
                # 둘 이상이면 문장이 길어지므로 오행 이름으로 묶는다: '나무와 물의 힘'
                joined = plains[0] if len(plains) == 1 else \
                    josa(names[plains[0]], "과/와") + " " + "·".join(names[p] for p in plains[1:]) + "의 힘"
                third.append(tpl.format(plain=joined, josa=josa(joined, "은/는")[len(joined):]))
        third[0] = "그래서 " + third[0]
        third.append(copy.MAP_CLOSE_MISSING)
    else:
        second.append(copy.MAP_FULL)
        ranked = sorted(ELEMENT_ORDER, key=lambda e: -els[e]["main"])
        thick, thin = ranked[0], ranked[-1]
        if els[thick]["main"] - els[thin]["main"] >= 2:
            tn, nn = copy.ELEMENT[thick]["name"], copy.ELEMENT[thin]["name"]
            second.append(copy.MAP_FULL_TILT.format(thick=tn, thin=nn, josa1=josa(tn, "이/가")[len(tn):],
                                                    josa2=josa(nn, "은/는")[len(nn):]))
            for e, state in ((thick, "many"), (thin, "few")):
                if els[e]["state"] == state:
                    row = bank.ALL_ROWS[_element_row(e, state)]
                    if row["key"] not in core_keys:
                        third.append(("그래서 " if not third else "") + row["trait"])
        else:
            second.append(copy.MAP_FULL_EVEN)
            third.append(copy.MAP_EVEN_MEANS)
        third.append(copy.MAP_CLOSE)
    p2 = _p(second, where="map.2")
    p3 = _p(third, where="map.3")
    counts = " ".join(f"{e}{els[e]['main']}" for e in ELEMENT_ORDER)
    why = [f"천간·지지 {_glyphs(profile)}를 오행으로 세면 {counts}입니다."]
    if missing:
        why.append("지장간까지 보면 " + " · ".join(f"{e} {hidden_counts[e]}" for e in missing) + "입니다.")
    html = f"<p>{escape(p1)}</p><p>{escape(p2)}</p><p>{escape(p3)}</p>" + _why(*why)
    return html, {"missing": missing, "present": present}


# ---------------------------------------------------------------------------
# 2·3. 성격 행 → 문단
# ---------------------------------------------------------------------------
def _meaning(row, profile) -> list[str]:
    key = row["key"]
    if key in copy.MEANING:
        lines = list(copy.MEANING[key])
    elif "element" in row:
        info = copy.ELEMENT[row["element"]]
        n = profile["elements"][row["element"]]["main"]
        name = info["name"]
        if row["state"] == "many":
            lines = [f"{_glyphs(profile)} 가운데 {josa(name, '이/가')} {n}개로 두텁습니다.",
                     f"{josa(info['plain'], '이/가')} 바탕에 깔린 사람이에요."]
        elif row["state"] == "few":
            lines = [f"{josa(name, '은/는')} {_glyphs(profile)}에 하나뿐입니다.",
                     f"{josa(info['plain'], '을/를')} 아껴 쓰는 사람이에요."]
        else:
            lines = [f"겉면 {_glyphs(profile)}에 {josa(name, '이/가')} 한 글자도 없습니다.",
                     f"{josa(info['plain'], '은/는')} 밖에서 빌려 오는 사람이에요."]
    else:
        g = copy.GROUP[row["group"]]
        n = profile["groups"][row["group"]]["main"]
        if row["state"] == "many":
            lines = [f"{josa(g['what'], '이/가')} {_glyphs(profile)}에 {n}개 있습니다.",
                     f"사주는 이를 {josa(g['plain'], '으로/로')} 읽어요."]
        else:
            lines = [f"{josa(g['what'], '이/가')} 겉면에 보이지 않습니다.",
                     f"{josa(g['plain'], '은/는')} 밖에서 채우는 편이에요."]
    lines.append(f"그래서 이 결을 '{row['label']}'에 빗댑니다.")
    return lines


def _why_row(row, profile) -> list[str]:
    key = row["key"]
    if key in copy.WHY:
        first = copy.WHY[key]
    elif "element" in row:
        nm = copy.ELEMENT[row["element"]]["name"]
        first = f"천간·지지를 오행으로 세면 {josa(nm, '이/가')} 정기 {profile['elements'][row['element']]['main']}개입니다."
    else:
        g = copy.GROUP[row["group"]]
        first = f"십성으로 보면 {row['group']}({g['members']})이 정기 {profile['groups'][row['group']]['main']}개입니다."
    return [first, "원국 · " + _evidence_text(row, profile)]


def _row_block(row, profile, seed, shift, heading, *, with_flip=True) -> str:
    allow = bool(row.get("allow_absolute"))
    meaning = _meaning(row, profile)
    trait_end = ending_family(row["trait"])
    scene_a = _scene(row, seed, shift, trait_end)
    scene_b = _scene(row, seed, shift + 4, ending_family(scene_a or row["trait"]), exclude=scene_a)
    base = len(meaning)
    p1 = _p(meaning + [row["trait"], scene_a or "", scene_b or ""], allow_absolute=allow,
            droppable=(base + 1, base + 2), where=f"row.{row['key']}")
    paras = [p1]
    if with_flip:
        paras.append(_p([row["flip"], row["tip"]], allow_absolute=allow, where=f"flip.{row['key']}"))
    body = "".join(f"<p>{escape(t)}</p>" for t in paras)
    return (f'<article class="lifetime-sub" data-now-me-row="{escape(row["key"])}">'
            f'<h4>{escape(heading)}</h4>{body}' + _why(*_why_row(row, profile)) + '</article>')


def _core_rows(ordered: list[dict]) -> tuple[list[tuple[dict, str]], set[str]]:
    """(행, 표시 방식) 목록. 표시 방식: 'main' 또는 'flip-of:<라벨>'."""
    if not ordered:
        return [], set()
    top = ordered[0]
    picks: list[tuple[dict, str]] = [(top, "main")]
    used = {top["key"]}
    pair = None
    if top["key"] == "B11" and len(ordered) > 1 and ordered[1]["key"] == "B16":
        pair = ordered[1]
        used.add(pair["key"])
    for row in ordered[1:]:
        if len(picks) + (1 if pair else 0) >= 3:
            break
        if row["key"] in used:
            continue
        if pair and row.get("group") in ("재성", "비겁"):
            continue
        picks.append((row, "main"))
        used.add(row["key"])
    if pair:
        picks.append((pair, f"flip-of:{top['label']}"))
    return picks, used


# ---------------------------------------------------------------------------
# 4. 분야별
# ---------------------------------------------------------------------------
def _day_palace_group(core) -> str | None:
    for fact in core.natal_facts.ten_gods.hidden:
        if fact.pillar == "day" and fact.hidden_role is not None and fact.hidden_role.value == "main":
            return copy.GOD_GROUP.get(fact.ten_god.value)
    return None


def _place_key(profile) -> str:
    officer = profile["groups"]["관성"]
    if officer["state"] == "many":
        return "organized"
    if officer["main"] == 0 and profile["hour_confidence"] == "high":
        return "autonomous"
    return "neutral"


def _domains(core, profile, climate) -> tuple[str, dict]:
    g, els = profile["groups"], profile["elements"]
    chosen = {}
    # 재물
    if profile["crowd_rob_wealth"]:
        k = "crowd"
    elif g["재성"]["state"] == "many":
        k = "many"
    elif g["식상"]["state"] == "many" and g["재성"]["main"] >= 1:
        k = "craft"
    elif g["재성"]["main"] == 0:
        k = "none"
    else:
        k = "neutral"
    chosen["money"] = (list(copy.MONEY[k]), f"재성 {g['재성']['main']} · 겁재 {profile['rob_wealth']} · 식상 {g['식상']['main']}", k)
    # 애정 — 일지 자리 + 끌림 신살 + 곁에 두면 편한 사람
    love = []
    palace = _day_palace_group(core)
    if palace:
        love.append(copy.LOVE_PALACE[palace])
    if profile["peach_blossom"] or profile["hongyeom"]:
        love.append(copy.LOVE_CHARM)
    lacking = next((bank.ALL_ROWS[_element_row(e, "none")] for e in ELEMENT_ORDER if els[e]["state"] == "none"), None)
    love.append(lacking["people"] if lacking else bank.PEOPLE_NEUTRAL)
    love_ev = ("일지 " + (palace or "확인 불가")) + (" · 도화" if profile["peach_blossom"] else "") + \
        (" · 홍염" if profile["hongyeom"] else "") + (f" · {lacking['element']} 없음" if lacking else "")
    chosen["love"] = (love, love_ev, palace or "none")
    # 일
    work = [bank.PLACE_LINES[_place_key(profile)]]
    many = [x for x in ("식상", "관성", "인성", "재성", "비겁") if g[x]["state"] == "many"]
    if many:
        work.append(copy.WORK_GROUP[many[0]])
    chosen["work"] = (work, f"관성 {g['관성']['main']}" + (f" · {many[0]} {g[many[0]]['main']}" if many and many[0] != "관성" else ""),
                      many[0] if many else "neutral")
    # 사람
    if g["비겁"]["state"] == "many":
        k = "rob_many"
    elif g["비겁"]["main"] == 0:
        k = "rob_none"
    elif g["인성"]["state"] == "many":
        k = "resource_many"
    else:
        k = "neutral"
    chosen["people"] = (list(copy.PEOPLE[k]), f"비겁 {g['비겁']['main']} · 인성 {g['인성']['main']}", k)
    # 몸과 쉼
    if els["水"]["state"] == "none" or g["인성"]["main"] == 0:
        k = "lack_rest"
    elif climate in HOT or els["火"]["state"] == "many":
        k = "hot"
    elif climate in COLD:
        k = "cold"
    elif els["土"]["state"] == "many":
        k = "earth"
    else:
        k = "neutral"
    chosen["rest"] = (list(copy.REST[k]), f"水 {els['水']['main']} · 인성 {g['인성']['main']} · " + CLIMATE_KO.get(climate or "", "조후 판정 보류"), k)

    parts = []
    for i, (key, title) in enumerate(copy.DOMAIN_TITLES, 1):
        lines, ev, _ = chosen[key]
        text = _p(lines, where=f"domain.{key}")
        parts.append(f'<article class="lifetime-sub" data-domain="{key}"><h4>{i}) {escape(title)}</h4>'
                     f'<p>{escape(text)}</p><small class="now-me-evidence">원국 · {escape(ev)}</small></article>')
    return "".join(parts), {k: v[2] for k, v in chosen.items()}


# ---------------------------------------------------------------------------
# 5. 인생의 흐름
# ---------------------------------------------------------------------------
def _link(cycle, profile, *, now=False, seen: Counter | None = None) -> tuple[str | None, str | None]:
    els = profile["elements"]
    pillar = cycle.get("pillar") or {}
    cyc = [pillar.get("stem_element"), pillar.get("branch_element")]
    for e in cyc:
        if e and els[e]["state"] == "none":
            name = copy.ELEMENT[e]["name"]
            key = f"fill:{e}"
            tpl = copy.LINK_FILL_NOW if now else _varied(seen, key, copy.LINK_FILL, copy.LINK_FILL_AGAIN)
            return (tpl.format(name=name, josa=josa(name, "이/가")[len(name):]) if tpl else None), key
    for e in cyc:
        if e and els[e]["state"] == "many":
            name = copy.ELEMENT[e]["name"]
            key = f"thick:{e}"
            tpl = copy.LINK_THICK_NOW if now else _varied(seen, key, copy.LINK_THICK, copy.LINK_THICK_AGAIN)
            return (tpl.format(name=name, josa=josa(name, "이/가")[len(name):]) if tpl else None), key
    return None, None


def _varied(seen, key, first, again):
    """같은 연결 문장이 지나온 길에 거듭 나오지 않게: 1번째 원문, 2번째 변형, 3번째부터 생략."""
    if seen is None:
        return first
    seen[key] += 1
    return {1: first, 2: again}.get(seen[key])


def _relation_line(cycle, young=False) -> str | None:
    found = set()
    for change in cycle.get("relationship_changes") or ():
        pillars = {m.get("pillar") for m in change.get("members", ())}
        for natal in ("day", "month"):
            if natal in pillars:
                found.add(f"{change.get('type')}:{natal}")
    for key in ("branch_clash:day", "branch_clash:month", "branch_six_combination:day"):
        if key in found:
            return (copy.REL_PAST_YOUNG if young else copy.REL_PAST)[key]
    return None


def _shaken_year(cycle, day_branch: str | None, this_year: int) -> int | None:
    if not day_branch or day_branch not in CLASH:
        return None
    target = CLASH[day_branch]
    start, end = cycle.get("start_year"), cycle.get("end_year")
    if not isinstance(start, int) or not isinstance(end, int):
        return None
    for year in range(start, min(end, this_year - 1) + 1):
        if ZHI[(year - 4) % 12] == target:
            return year
    return None


def _flow(core, profile, past, now, future, current_selection) -> tuple[str, str | None, dict]:
    rows = []
    for c in past + ([now] if now else []) + [f for f in future if f.get("start_age", 0) < 90]:
        is_now = now is not None and c.get("index") == now.get("index")
        god = copy.GOD_KO.get(c.get("ten_god"), "")
        mark = f' <span class="lifetime-now-mark">{copy.NOW_MARK}</span>' if is_now else ""
        rows.append(f'<tr{" class=\"is-now\"" if is_now else ""}><td>{c["start_age"]}~{c["end_age"]}세</td>'
                    f'<td>{escape(c["pillar"]["ganji"])}</td><td>{escape(god)}{mark}</td></tr>')
    head = "".join(f"<th>{h}</th>" for h in copy.TABLE_HEAD)
    table = f'<table class="lifetime-cycles"><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table>'

    day = core.natal_facts.pillars.get("day")
    this_year = date.today().year
    past_items, past_meta = [], []
    seen: Counter = Counter()
    for c in past:
        young = c["end_age"] <= 20
        god = c.get("ten_god") if c.get("ten_god") in copy.PAST_ADULT else "peer"
        theme = copy.PAST_YOUNG[copy.GOD_GROUP[god]] if young else copy.PAST_ADULT[god]
        link, link_key = _link(c, profile, seen=seen)
        rel = _relation_line(c, young)
        day_clash = rel in (copy.REL_PAST["branch_clash:day"], copy.REL_PAST_YOUNG["branch_clash:day"])
        year = None if day_clash else _shaken_year(c, day.branch if day else None, this_year)
        shaken = None
        if year:
            shaken = copy.SHAKEN_YEAR[min(seen["shaken"], len(copy.SHAKEN_YEAR) - 1)].format(year=year)
            seen["shaken"] += 1
        extra = rel or shaken
        text = _p([theme, link or "", extra or ""], where=f"past.{c['index']}")
        past_items.append(f'<li><strong>{c["start_age"]}~{c["end_age"]}세 · {escape(c["pillar"]["ganji"])}</strong> {escape(text)}</li>')
        past_meta.append(dict(index=c["index"], link=link_key, relation=bool(rel), shaken_year=year))

    parts = [f"<p>{escape(copy.FLOW_INTRO)}</p>", table]
    if past_items:
        parts.append(f'<h4>{copy.PAST_TITLE}</h4><ul class="lifetime-past">{"".join(past_items)}</ul>')
    now_link_key = None
    if now is not None:
        god = (current_selection or {}).get("focal_god") or now.get("ten_god")
        reading = cycle_copy.compose_current(god, None)
        link, now_link_key = _link(now, profile, now=True)
        lead = copy.NOW_LEAD.format(start=now["start_age"], end=now["end_age"], ganji=now["pillar"]["ganji"])
        parts.append(
            f'<h4>{copy.NOW_TITLE}</h4><article data-lifetime-section="current-cycle" data-current-cycle="true" '
            f'data-report-cycle="{now["index"]}"><p class="lifetime-now-headline"><strong>{escape(reading["headline"])}</strong></p>'
            f'<p class="lifetime-now-lead">{escape(lead)}{(" " + escape(link)) if link else ""}</p>'
            f'<p>{escape(reading["core"])}</p><p>{escape(reading["tip"])}</p></article>')
    if future:
        nxt = future[0]
        current_god = now.get("ten_god") if now else None
        hook = cycle_copy.teaser(nxt["start_age"], nxt.get("ten_god"), current_god)
        parts.append(
            f'<h4>{copy.NEXT_TITLE}</h4><article data-lifetime-section="upcoming" data-locked="true" '
            f'data-report-cycle="{nxt["index"]}"><p data-cycle-teaser="true"><strong>{escape(hook)}</strong></p>'
            f'<p class="reading-caption">🔒 {escape(copy.NEXT_LOCK_NOTE)}</p>'
            f'<a href="#paywall" data-paywall-cta="lifetime-cycles">{escape(cycle_copy.CTA_LABEL)}</a></article>')
    return "".join(parts), now_link_key, {"past": past_meta}


# ---------------------------------------------------------------------------
# 조립
# ---------------------------------------------------------------------------
def build_lifetime_v3(core: MyeongriCoreResult, user_name: str, *, past, now, future,
                      current_selection, climate: str | None) -> dict:
    profile = natal_profile(core)
    seed = seed_from(*profile["pillars"].values())
    name = user_name or "회원"
    ordered = select_rows(profile)
    if not ordered:
        raise ValueError("lifetime_v3: 해당하는 사전 행이 없습니다")
    hidden_counts = _hidden_counts(core)
    core_picks, used = _core_rows(ordered)

    # 3. 먼저 보는 것 후보 (now_me 와 같은 규칙)
    visible = sorted(("식상", "재성", "비겁"), key=lambda g: -profile["groups"][g]["main"])
    cands = [bank.ALL_ROWS[_group_row(g, "many")] for g in visible if profile["groups"][g]["state"] == "many"]
    cands += shensha_rows(profile)
    cands += [r for r in ordered if r.get("state") in ("many", "few")]
    b16_used = "B16" in used
    first_seen = []
    for r in cands:
        if len(first_seen) >= 2:
            break
        if r["key"] in used or (b16_used and r.get("group") in ("재성", "비겁")):
            continue
        first_seen.append(r)
        used.add(r["key"])

    numbering = iter(range(1, 10))
    day_row = bank.DAY_MASTER_ROWS[profile["day_master"]]
    head = (f'<section class="lifetime-v3-head" data-lifetime-section="head">'
            f'<p class="now-me-lead">{escape(name)}님의 원국은 <strong>{escape(day_row["label"])}</strong>입니다.</p>'
            + _chart_html(core, profile, hidden_counts) + '</section>')

    map_html, map_meta = _map(core, profile, hidden_counts, {r["key"] for r, _ in core_picks})
    html = head + _section("map", next(numbering), map_html)

    sec = next(numbering)
    core_parts = [f"<p>{escape(copy.CORE_INTRO.format(name=name, n=len(core_picks)))}</p>"]
    for i, (row, mode) in enumerate(core_picks, 1):
        if mode == "main":
            heading = f"{sec}-{i}. '{row['label']}'"
        else:
            heading = f"{sec}-{i}. '{mode.split(':', 1)[1]}'의 뒷면 — '{row['label']}'"
        core_parts.append(_row_block(row, profile, seed, 3 + i * 2, heading))
    html += _section("core", sec, "".join(core_parts))

    if first_seen:
        sec = next(numbering)
        parts = [f"<p>{escape(copy.FIRST_SEEN_INTRO)}</p>"]
        for i, row in enumerate(first_seen, 1):
            parts.append(_row_block(row, profile, seed, 11 + i * 2, f"{sec}-{i}. '{row['label']}'"))
        html += _section("first-seen", sec, "".join(parts))

    domains_html, domain_meta = _domains(core, profile, climate)
    html += _section("domains", next(numbering), domains_html)

    flow_html, now_link, flow_meta = _flow(core, profile, past, now, future, current_selection)
    html += _section("flow", next(numbering), flow_html)

    top = core_picks[0][0]
    closing = [copy.CLOSING_LEAD.format(name=name, label=top["label"])]
    if now is not None:
        if now_link and now_link.startswith("fill:"):
            nm = copy.ELEMENT[now_link[5:]]["name"]
            closing.append(copy.CLOSING_FILL.format(name=nm, josa=josa(nm, "이/가")[len(nm):]))
        elif now_link and now_link.startswith("thick:"):
            closing.append(copy.CLOSING_THICK)
        else:
            closing.append(copy.CLOSING_GROUP[copy.GOD_GROUP.get(now.get("ten_god"), "비겁")])
    closing.append(copy.CLOSING_END if map_meta["missing"] else copy.CLOSING_END_FULL)
    html += _section("closing", next(numbering), f'<p class="lifetime-closing">{escape(_p(closing, where="closing"))}</p>')

    evidence = {
        "rows": [r["key"] for r, _ in core_picks], "first_seen": [r["key"] for r in first_seen],
        "map": map_meta, "domains": domain_meta, "flow": flow_meta, "now_link": now_link,
        "hour_confidence": profile["hour_confidence"],
    }
    return {"html": html, "evidence": evidence, "version": V3_VERSION, "copy_version": copy.COPY_VERSION}
