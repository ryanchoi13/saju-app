"""평생운세 v3 조립기 (B안 v3, 2026-10-23 결정).

원국표 → 1. 원국 지도 → 2. 타고난 결 → 3. 먼저 보는 것 → 4. 분야별 → 5. 인생의 흐름 → 6. 한마디.
- 성격 행 선택·장면·검증은 '지금의 나'(now_me) 를 그대로 쓴다.
- 풀이가 먼저, 근거는 문단 끝 '풀이 근거' 접힘으로.
- 다음 대운 본문은 만들지 않는다(티저 한 줄만). 표에는 나이·간지·십성 이름만 싣는다.
- 문단마다 validate_paragraph 를 거친다. 통과하지 못하면 ValueError — lifetime.py 가 옛 v4 로 되돌린다.
"""

from __future__ import annotations

import re
from collections import Counter
from datetime import date
from html import escape

from app.engine.constants import GAN_KO, GAN_WUXING, ZHI_KO
from app.engine.core.models import MyeongriCoreResult
from app.engine.korean import josa
from app.engine.services.annual_copy import seed_from, split_sentences
from app.engine.services import lifetime_v3_copy as copy
from app.engine.services import now_me_copy as bank
from app.engine.services import lifetime_flow as flow
from app.engine.services.now_me import (
    ELEMENT_ORDER, natal_profile, select_rows, shensha_rows, _group_row, _element_row,
    _evidence_text, LINK_HREF,
)

V3_VERSION = "lifetime-v3"
CLIMATE_KO = {
    "very_cold_wet": "매우 차고 습함", "cold_wet": "차고 습함", "cool_dry": "서늘하고 건조함",
    "mild_wet": "온화하나 습함", "mild_balanced": "한난조습 고름", "warm_dry": "따뜻하고 건조함",
    "hot_dry": "덥고 건조함", "very_hot_dry": "매우 덥고 건조함",
}
HOT = {"warm_dry", "hot_dry", "very_hot_dry"}
COLD = {"very_cold_wet", "cold_wet", "cool_dry"}


SENTENCE_LIMIT = 80          # 앉아서 읽는 긴 글이라 두 절까지(10/23). 매일 보는 문구의 46자보다 길다.
EVENT_BANNED = ("사고", "이혼", "파국")   # 지나온 길에서도 쓰지 않는 사건 말(헌장 10/23)


def check_paragraph(text: str, allow_absolute: bool = False) -> list[str]:
    """now_me_copy.validate_paragraph 와 같은 규칙에서 문장 길이만 80자로 늘린 검사."""
    issues = [i for i in bank.validate_paragraph(text, allow_absolute=allow_absolute) if not i.startswith("문장이 깁니다")]
    for sentence in split_sentences(text):
        if len(sentence) > SENTENCE_LIMIT:
            issues.append(f"문장이 깁니다({len(sentence)}): {sentence}")
    issues += [f"사건 말 '{w}'" for w in EVENT_BANNED if w in text]
    return issues


def _p(sentences, *, allow_absolute=False, droppable=(), where="") -> str:
    """문장 목록을 한 문단으로. 검증에 걸리면 droppable(장면) 문장부터 빼 본다."""
    sentences = [s for s in sentences if s]
    text = " ".join(sentences)
    if check_paragraph(text, allow_absolute=allow_absolute):
        sentences = [s for i, s in enumerate(sentences) if i not in droppable]
        text = " ".join(sentences)
    issues = check_paragraph(text, allow_absolute=allow_absolute)
    if issues:
        raise ValueError(f"lifetime_v3 {where}: {issues}")
    return text


def _j(word: str, pair: str) -> str:
    """_jo() 결과에서 조사만. '금(金)'처럼 괄호 한자가 붙으면 앞의 한글로 고른다."""
    base = re.sub(r"\([^)]*\)$", "", word) or word
    return josa(base, pair)[len(base):]


def _jo(word: str, pair: str) -> str:
    return word + _j(word, pair)


def _why(*lines: str) -> str:
    """풀이 근거 — 접지 않고 본문 아래에 작은 글씨로 바로 보인다(11/02 정오님)."""
    lines = [escape(line) for line in lines if line]
    if not lines:
        return ""
    first = f'<span class="lifetime-why-label">{copy.WHY_LABEL}</span> {lines[0]}'
    body = "".join(f"<p>{t}</p>" for t in [first] + lines[1:])
    return f'<div class="lifetime-why">{body}</div>'


def _section(sid: str, number: int, inner: str) -> str:
    return (f'<section class="lifetime-v3-section" data-lifetime-section="{sid}">'
            f'<h3>{number}. {escape(copy.SECTION_TITLES[sid])}</h3>{inner}</section>')


# ---------------------------------------------------------------------------
# 원국표
# ---------------------------------------------------------------------------
def _hidden_by_pillar(core: MyeongriCoreResult) -> dict[str, list[str]]:
    order = {"main": 0, "middle": 1, "residual": 2}
    out: dict[str, list[tuple[int, str]]] = {}
    for fact in core.natal_facts.ten_gods.hidden:
        role = fact.hidden_role.value if fact.hidden_role is not None else "main"
        out.setdefault(fact.pillar, []).append((order.get(role, 0), fact.stem))
    return {k: [s for _, s in sorted(v)] for k, v in out.items()}


def _hidden_counts(core: MyeongriCoreResult) -> Counter:
    """정기(겉면에 이미 센 글자)를 뺀 지장간 오행 개수."""
    counts: Counter = Counter()
    for fact in core.natal_facts.ten_gods.hidden:
        if fact.hidden_role is not None and fact.hidden_role.value == "main":
            continue
        counts[GAN_WUXING[fact.stem]] += 1
    return counts


ELEMENT_CLASS = {"木": "wood", "火": "fire", "土": "earth", "金": "metal", "水": "water"}


def _chart_html(core, profile, hidden_counts) -> str:
    """원국표 — '나의 사주' 명식표(2026-10-31 시안 511)와 같은 마크업·클래스(assets/brand-2026/refine.css .pc-grid).

    큰 먹색 한자 + 작은 오행 점 + 읽는 법, 일주만 남색 테두리. 화면 두 곳의 표가 같은 모양이어야 한다.
    """
    pillars = core.natal_facts.pillars
    hidden = _hidden_by_pillar(core)
    cols = (("hour", "시"), ("day", "일"), ("month", "월"), ("year", "년"))

    def glyph(char, ko, element):
        if not char:   # 생시 모름 — 지어내지 않고 '모름'으로 적는다
            return '<div class="badge-elem-main badge-main-none pc-unknown">모름</div>'
        el = ELEMENT_CLASS[element]
        el_ko = copy.ELEMENT[element]["ko"]
        return (f'<div class="badge-elem-main badge-main-{el}" aria-label="{ko} {el_ko}">'
                f'<span class="pc-char">{char}</span><i class="pc-dot el-{el}" aria-hidden="true"></i>'
                f'<span class="pc-read">{ko} · {el_ko}</span></div>')

    def hidden_box(stems_):
        if not stems_:
            return '<div class="pc-hidden"><span class="pc-hidden-none">-</span></div>'
        spans = "".join(
            f'<span class="badge-jjg elem-{ELEMENT_CLASS[GAN_WUXING[s]]}">'
            f'<i class="pc-dot el-{ELEMENT_CLASS[GAN_WUXING[s]]}" aria-hidden="true"></i>{s}</span>'
            for s in stems_)
        return f'<div class="pc-hidden">{spans}</div>'

    parts = ['<div class="pc-grid lifetime-pc" role="table" aria-label="사주 여덟 글자">'
             '<div class="pc-col pc-rowhead" aria-hidden="true"><span class="pc-label">&nbsp;</span>'
             '<div class="pc-rh">천간</div><div class="pc-rh">지지</div><div class="pc-rh pc-rh-small">지장간</div></div>']
    for key, label in cols:
        p = pillars.get(key)
        day = " is-day" if key == "day" else ""
        if p is None:
            parts.append(f'<div class="pc-col{day}"><span class="pc-label">{label}</span>'
                         + glyph(None, None, None) + glyph(None, None, None) + hidden_box([]) + '</div>')
            continue
        parts.append(f'<div class="pc-col{day}"><span class="pc-label">{label}</span>'
                     + glyph(p.stem, GAN_KO[p.stem], p.stem_element)
                     + glyph(p.branch, ZHI_KO[p.branch], p.branch_element)
                     + hidden_box(hidden.get(key, [])) + '</div>')
    table = "".join(parts) + '</div>'
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
    first = [lead]
    if present:
        rest = (copy.ELEMENT[present[0]]["place"] + " " + copy.ELEMENT[present[1]]["mod"]) if len(present) > 1 \
            else copy.ELEMENT[present[0]]["mod"]
        first.append(copy.MAP_SCENE.format(season=f"{season}에 " if season else "", label=day["label"],
                                           ja=_j(day["label"], "이/가"), rest=rest,
                                           verb=copy.DAY_VERB[profile["day_master"]]))
    first.append(f"{_jo(day['label'], '은/는')} {day['trait']}")
    first.append(copy.MAP_HARMONY[_harmony([e for e in ELEMENT_ORDER if els[e]["main"] > 0])])
    p1 = _p(first, where="map.1")

    missing = [e for e in ELEMENT_ORDER if els[e]["main"] == 0]
    second, third = [], []
    if missing:
        nm = [copy.ELEMENT[e]["name"] for e in missing]
        names = (_jo(nm[0], "과/와") + " " + nm[1]) if len(nm) == 2 else ", ".join(nm)
        second.append(copy.MAP_MISSING_ONE.format(names=names, josa=_jo(names, "이/가")[len(names):]))
        hidden_plain, deep_plain = [], []
        for e in missing:
            info = copy.ELEMENT[e]
            j = _jo(info["name"], "은/는")[len(info["name"]):]
            if hidden_counts[e]:
                second.append(copy.MAP_MISSING_HIDDEN.format(name=info["name"], josa=j, power=info["power"], k=copy.COUNT_THING.get(hidden_counts[e], f"{hidden_counts[e]}개")))
                hidden_plain.append(info["plain"])
            else:
                second.append(copy.MAP_MISSING_DEEP.format(name=info["name"], josa=j, power=info["power"]))
                deep_plain.append(info["plain"])
        names = {copy.ELEMENT[e]["plain"]: copy.ELEMENT[e]["name"] for e in missing}
        for plains, tpl in ((hidden_plain, copy.MAP_MEANS_HIDDEN), (deep_plain, copy.MAP_MEANS_DEEP)):
            if plains:
                # 둘 이상이면 문장이 길어지므로 오행 이름으로 묶는다: '나무와 물의 힘'
                joined = plains[0] if len(plains) == 1 else \
                    _jo(names[plains[0]], "과/와") + " " + "·".join(names[p] for p in plains[1:]) + "의 힘"
                third.append(tpl.format(plain=joined, josa=_jo(joined, "은/는")[len(joined):]))
        third.append(copy.MAP_CLOSE_MISSING)
    else:
        second.append(copy.MAP_FULL)
        ranked = sorted(ELEMENT_ORDER, key=lambda e: -els[e]["main"])
        thick, thin = ranked[0], ranked[-1]
        if els[thick]["main"] - els[thin]["main"] >= 2:
            tn, nn = copy.ELEMENT[thick]["name"], copy.ELEMENT[thin]["name"]
            second.append(copy.MAP_FULL_TILT.format(thick=tn, thin=nn, josa1=_jo(tn, "이/가")[len(tn):],
                                                    josa2=_jo(nn, "은/는")[len(nn):]))
            for e, state in ((thick, "many"), (thin, "few")):
                if els[e]["state"] == state:
                    row = bank.ALL_ROWS[_element_row(e, state)]
                    if row["key"] not in core_keys:
                        nm = copy.ELEMENT[e]["name"]
                        lead = "그래서 " if state == "many" else f"{nm}{_j(nm, '은/는')} 얇아서 "
                        third.append(lead + row["trait"])
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


_GEN = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
_CTL = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}


def _harmony(present: list[str]) -> str:
    gens = sum(1 for a in present for b in present if _GEN[a] == b)
    ctls = sum(1 for a in present for b in present if _CTL[a] == b)
    return "grow" if gens > ctls else ("check" if ctls > gens else "mixed")


# ---------------------------------------------------------------------------
# 2·3. 성격 행 → 문단
# ---------------------------------------------------------------------------
LABEL_LINES = (   # 소단락마다 같은 문장이 반복되지 않게 순서대로 돌려 쓴다(11/01)
    "이러한 결을 '{label}'에 빗댑니다.",
    "'{label}'{i}라는 이름은 이 모습에서 왔어요.",
    "그래서 '{label}'{i}라고 불러요.",
    "이 결에 붙인 이름이 '{label}'입니다.",
)


def _label_line(label: str, style: int) -> str:
    tpl = LABEL_LINES[style % len(LABEL_LINES)]
    return tpl.format(label=label, i=_j(label, "이/"))


def _meaning(row, profile, style: int = 0) -> list[str]:
    key = row["key"]
    if key == "B11":
        el = copy.ELEMENT[profile["day_element"]]["name"]
        lines = (["태어난 달에 나와 같은 기운이 가장 날카롭게 섭니다."] if profile["yangin"]["month"]
                 else ["나와 같은 기운이면서 결이 다른 글자(겁재)가 곁에 여럿 섭니다."])
        lines.append(f"같은 {el} 기운이 빽빽이 어깨를 맞댄 모양이에요.")
    elif key in copy.MEANING:
        lines = list(copy.MEANING[key])
    elif "element" in row:
        info = copy.ELEMENT[row["element"]]
        n = profile["elements"][row["element"]]["main"]
        name = info["name"]
        if row["state"] == "many":
            lines = [f"{_glyphs(profile)} 가운데 {_jo(name, '이/가')} {copy.COUNT_THING.get(n, f'{n}개')}로 두텁습니다.",
                     f"{_jo(info['plain'], '이/가')} 바탕에 깔린 사람이에요."]
        elif row["state"] == "few":
            lines = [f"{_jo(name, '은/는')} {_glyphs(profile)}에 하나뿐입니다.",
                     f"{_jo(info['plain'], '을/를')} 아껴 쓰는 사람이에요."]
        else:
            lines = [f"겉면 {_glyphs(profile)}에 {_jo(name, '이/가')} 한 글자도 없습니다.",
                     f"{_jo(info['plain'], '은/는')} 밖에서 빌려 오는 사람이에요."]
    else:
        g = copy.GROUP[row["group"]]
        n = profile["groups"][row["group"]]["main"]
        if row["state"] == "many":
            lines = [f"{_jo(g['what'], '이/가')} {_glyphs(profile)}에 {copy.COUNT_THING.get(n, f'{n}개')} 있습니다.",
                     f"사주는 이를 {_jo(g['plain'], '으로/로')} 읽어요."]
        else:
            lines = [f"{_jo(g['what'], '이/가')} 겉면에 보이지 않습니다.",
                     f"{_jo(g['plain'], '은/는')} 밖에서 채우는 편이에요."]
    lines.append(_label_line(row["label"], style))
    return lines


def _why_row(row, profile) -> list[str]:
    key = row["key"]
    if key == "B11":
        where = "월지에 있어" if profile["yangin"]["month"] else f"{profile['rob_wealth']}개 있어"
        first = copy.WHY[key].format(where=where)
    elif key == "B18":
        first = copy.WHY[key].format(glyphs=_glyphs(profile))
    elif key in copy.WHY:
        first = copy.WHY[key]
    elif "element" in row:
        nm = copy.ELEMENT[row["element"]]["name"]
        first = f"천간·지지를 오행으로 세면 {_jo(nm, '이/가')} 정기 {profile['elements'][row['element']]['main']}개입니다."
    else:
        g = copy.GROUP[row["group"]]
        first = f"십성으로 보면 {row['group']}({g['members']})이 정기 {profile['groups'][row['group']]['main']}개입니다."
    return [first, "원국 · " + _evidence_text(row, profile)]


def _row_block(row, profile, seed, shift, heading, *, with_flip=True, style: int = 0) -> str:
    allow = bool(row.get("allow_absolute"))
    meaning = _meaning(row, profile, style)
    # 장면은 한 문장. 따로 고른 장면 두 개를 붙이면 서로 딴 얘기가 된다(10/30).
    pool = copy.SCENE_FLOW.get(row.get("scene_key") or "")
    scene = pool[(seed >> shift) % len(pool)] if pool else ""
    base = len(meaning)
    p1 = _p(meaning + [row["trait"], scene], allow_absolute=allow,
            droppable=(base + 1,), where=f"row.{row['key']}")
    paras = [p1]
    if with_flip:
        flip = row["flip"] if row["flip"].startswith("다만") else "다만 " + row["flip"]
        tip = copy.TIP_LIFETIME.get(row["key"]) or _no_today(row["tip"])
        paras.append(_p([copy.SHINE.get(row["key"], ""), flip, tip],
                        allow_absolute=allow, droppable=(0,), where=f"flip.{row['key']}"))
    body = "".join(f"<p>{escape(t)}</p>" for t in paras)
    return (f'<article class="lifetime-sub" data-now-me-row="{escape(row["key"])}">'
            f'<h4>{escape(heading)}</h4>{body}' + _why(*_why_row(row, profile)) + '</article>')


def _no_today(tip: str) -> str:
    """사전의 팁은 매일 보는 문구라 '오늘'로 시작한다. 평생운세에서는 떼고 쓴다."""
    return tip.replace("오늘은 ", "").replace("오늘 ", "")


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
    strong = [r for r in ordered[1:] if r.get("state") != "few"]
    weak = [r for r in ordered[1:] if r.get("state") == "few"]
    for row in strong + weak:
        if len(picks) + (1 if pair else 0) >= 3:
            break
        if row["key"] in used:
            continue
        if row.get("state") == "few" and len(picks) + (1 if pair else 0) >= 2:
            break
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


def _domains(core, profile, climate, number: int, name: str = "회원") -> tuple[str, dict]:
    g, els = profile["groups"], profile["elements"]
    chosen: dict[str, tuple[list[str], str, str]] = {}
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
    # 애정 — 일지(가까운 관계 자리) + 끌림 신살 + 곁에 두면 편한 사람
    love: list[str] = []
    palace = _day_palace_group(core)
    if palace:
        love += list(copy.LOVE_PALACE[palace])
    charm = "both" if profile["peach_blossom"] and profile["hongyeom"] else \
        ("peach" if profile["peach_blossom"] else ("red" if profile["hongyeom"] else None))
    if charm:
        love.append(copy.LOVE_CHARM[charm])
    missing = [e for e in ELEMENT_ORDER if els[e]["state"] == "none"]
    if missing:
        mates = [copy.LOVE_MATE[e] for e in missing[:2]]
        names = copy.ELEMENT[missing[0]]["name"] if len(missing) == 1 else \
            _jo(copy.ELEMENT[missing[0]]["name"], "과/와") + " " + copy.ELEMENT[missing[1]]["name"]
        love.append(copy.LOVE_MATE_WHY.format(name="{name}", names=names, ja=_j(names, "이/가")))
        if len(mates) == 1:
            love.append(copy.LOVE_MATE_LINE.format(mate=mates[0]))
        else:
            love += [copy.LOVE_MATE_TWO[0].format(a=mates[0]), copy.LOVE_MATE_TWO[1].format(b=mates[1][0].upper() + mates[1][1:])]
    else:
        love.append(copy.LOVE_MATE_NEUTRAL)
    love_ev = ("일지 " + (palace or "확인 불가")) + (" · 도화" if profile["peach_blossom"] else "") + \
        (" · 홍염" if profile["hongyeom"] else "") + ("".join(f" · {e} 없음" for e in missing))
    chosen["love"] = (love, love_ev, palace or "none")
    # 일
    many = [x for x in ("식상", "관성", "인성", "재성", "비겁") if g[x]["state"] == "many"]
    work = [bank.PLACE_LINES[_place_key(profile)]]
    work += list(copy.WORK_GROUP[many[0]]) if many else [copy.WORK_NEUTRAL]
    if g["관성"]["main"] == 0 and (not many or many[0] != "관성"):
        work.append(copy.WORK_HIDDEN_OFFICER)
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
    people = list(copy.PEOPLE[k])
    if profile["flower_canopy"]:
        canopy = copy.PEOPLE_CANOPY if k == "rob_many" else copy.PEOPLE_CANOPY.replace("그러면서도 ", "한편 ")
        people.insert(min(2, len(people)), canopy)
    chosen["people"] = (people, f"비겁 {g['비겁']['main']} · 인성 {g['인성']['main']}" + (" · 화개" if profile["flower_canopy"] else ""), k)
    # 몸과 쉼 — 의학 표현 없이 생활 리듬으로만
    if els["水"]["state"] == "none":
        k = "lack_water"
    elif els["火"]["state"] == "many" or (climate in HOT and els["火"]["main"] >= 1):
        k = "hot"
    elif climate in COLD and els["火"]["state"] != "many":
        k = "cold"
    elif g["인성"]["main"] == 0:
        k = "no_resource"
    elif els["土"]["state"] == "many":
        k = "earth"
    else:
        k = "neutral"
    chosen["rest"] = (list(copy.REST[k]), f"水 {els['水']['main']} · 火 {els['火']['main']} · 인성 {g['인성']['main']} · "
                      + CLIMATE_KO.get(climate or "", "조후 판정 보류"), k)

    parts = [f"<p>{escape(copy.DOMAIN_INTRO)}</p>"]
    for i, (key, title) in enumerate(copy.DOMAIN_TITLES, 1):
        lines, ev, _ = chosen[key]
        text = _p([line.format(name=name) for line in lines], where=f"domain.{key}")
        link = ""
        if key in ("love", "work"):
            target = "gunghap" if key == "love" else "business"
            link = (f' <a class="now-me-link" href="{LINK_HREF[target]}" data-now-me-link="{target}">'
                    f'{escape(bank.LINK_LABELS[target])}</a>')
        parts.append(f'<article class="lifetime-sub" data-domain="{key}"><h4>{number}-{i}. {escape(title)}</h4>'
                     f'<p>{escape(text)}{link}</p><small class="now-me-evidence">원국 · {escape(ev)}</small></article>')
    return "".join(parts), {k: v[2] for k, v in chosen.items()}


# ---------------------------------------------------------------------------
# 5. 인생의 흐름
# ---------------------------------------------------------------------------
def _flow_ctx(core, profile) -> dict:
    natal = {k: v.branch for k, v in core.natal_facts.pillars.items() if v is not None}
    solar = (core.natal_facts.calendar or {}).get("solar_date") or ""
    birth_year = int(solar[:4]) if solar[:4].isdigit() else None
    return {"natal": natal, "day_stem": core.natal_facts.day_master.stem, "birth_year": birth_year}


def _kind_first(info: dict, table: dict, seen: Counter | None = None, young=False) -> tuple[str, str]:
    """유형 첫 문장과, 뒤따를 문장 키. clash 는 자리별 키(clash:day 등)로 돌려준다."""
    kind = info["kind"]
    after_key = kind
    if kind == "fill":
        e = info["fills"][0]
        name = copy.ELEMENT[e]["name"]
        key = "fill"
        if seen is not None:
            seen[f"fill:{e}"] += 1
            if seen[f"fill:{e}"] > 1:
                key = "fill_again"
        return table[key].format(name=name, ja=_j(name, "이/가")), after_key
    if kind in ("thick", "grow"):
        e = (info["thick"] or info["grow"])[0]
        name = copy.ELEMENT[e]["name"]
        return table[kind].format(name=name, ja=_j(name, "이/가")), after_key
    if kind == "clash":
        pos = "day" if "day" in info["clash_pos"] else "month"
        label = copy.POSITION[pos]
        return table[kind].format(pos=label, jp=_j(label, "을/를")), f"clash:{pos}"
    return table[kind], after_key


def _year_lines(years: list[dict], seen: Counter) -> list[str]:
    order = ("stem_clash", "clash:day", "clash:month", "triple_punish", "clash:year", "clash:hour", "triple", "stem_combine")
    out = []
    pairs = []
    for y in years:
        kinds = ["triple" if k.startswith("triple:") else k for k in y["kinds"]]
        top = next((k for k in order if k in kinds), None)
        if top is None:
            continue
        table = copy.YEAR_EVENT_CHILD if y["age"] <= 12 else (copy.YEAR_EVENT_YOUNG if y["age"] <= 19 else copy.YEAR_EVENT)
        pool = table[top]
        seen[f"year:{id(table)}:{top}"] += 1
        event = pool[(seen[f"year:{id(table)}:{top}"] - 1) % len(pool)]
        if top == "triple":
            e = next(k.split(":")[1] for k in y["kinds"] if k.startswith("triple:"))
            event = event.format(name=copy.ELEMENT[e]["name"])
        tpl = copy.YEAR_FIRST if not out else copy.YEAR_SECOND
        out.append(tpl.format(age=y["age"], event=event))
        pairs.append((y["age"], event))
    return _join_year_pair(out, pairs)


YEAR_PAIR = "{age1}세 무렵에는 {event1}, {age2}세 무렵에는 {event2}."   # 11/01: 두 해를 한 문장으로


def _join_year_pair(out: list[str], pairs: list[tuple]) -> list[str]:
    """앞의 두 해를 한 문장으로 잇는다. 어미가 '습니다'가 아니거나 80자를 넘으면 그대로 둔다."""
    if len(pairs) < 2 or not pairs[0][1].endswith("습니다"):
        return out
    (a1, e1), (a2, e2) = pairs[0], pairs[1]
    joined = YEAR_PAIR.format(age1=a1, event1=e1[:-3] + "고", age2=a2, event2=e2)
    if len(joined) > SENTENCE_LIMIT:
        return out
    return [joined] + out[2:]


def _killing_type(profile) -> str:
    """칠살 대운을 원국 조건으로 나눈다(11/02). 신강이면 식상(제살)을, 신약이면 인성(화살)을 먼저 본다."""
    weak = profile.get("strength") in ("weak", "extremely_weak")
    g = profile["groups"]
    food = g["식상"]["main"] > 0
    res = g["인성"]["main"] > 0
    wealth = g["재성"]["main"] >= 2
    if weak:
        if res:
            return "transform"
        if wealth and not food:
            return "wealth"
        return "heavy_food" if food else "heavy"
    if food:
        return "control"
    if res:
        return "transform"
    if wealth:
        return "wealth"
    return "face"


def _sk_key(sk: str) -> str:
    return copy.SK_TEXT_KEY.get(sk, sk)


_YONG_FAV = {"strong": {"output", "wealth", "officer"}, "weak": {"peer", "resource"}}
_NEG_W = {"stem_clash": -2, "clash:day": -2, "clash:month": -2, "clash:year": -1, "clash:hour": -1,
          "punish": -1, "thick": -1}


def _cycle_items(cycle, info, profile, day_stem) -> list[tuple[str, str, int]]:
    """대운 하나를 (종류, 키, 무게)로 푼다. 종류: gain·load(대운 십성) / pos·neg(그 밖). 무게 합이 결론의 방향."""
    from app.engine.services import daily_score
    god = cycle.get("ten_god") if cycle.get("ten_god") in copy.LEAD_GAIN else "peer"
    items = []
    sk = _killing_type(profile) if god == "seven_killings" else None
    if sk in ("control", "transform"):
        items.append(("gain", f"sk:{sk}", 2))
    elif sk in ("wealth", "heavy", "heavy_food"):
        items.append(("load", f"sk:{_sk_key(sk)}", -2))
    else:
        state = str(profile.get("strength") or "")
        direction = "strong" if state in daily_score.YONG_STRONG else "weak" if state in daily_score.YONG_WEAK else None
        v = 0
        if direction:
            fav = _YONG_FAV[direction]
            for el in (info.get("stem_element"), info.get("branch_element")):
                if el:
                    v += 1 if daily_score._god_group(day_stem, el) in fav else -1
        items.append(("gain", god, v) if v >= 0 else ("load", god, v))
    if info["fills"]:
        items.append(("pos", "fill", 1))
    if info["six_pos"] or info["triples"]:
        items.append(("pos", "bond", 1))
    if info["stem_rel"] == "clash":
        items.append(("neg", "stem_clash", _NEG_W["stem_clash"]))
    for pos in dict.fromkeys(info["clash_pos"]):
        items.append(("neg", f"clash:{pos}", _NEG_W[f"clash:{pos}"]))
    if any(kind == "punish" for kind, _ in info["relations"]):
        items.append(("neg", "punish", _NEG_W["punish"]))
    if info["thick"]:
        items.append(("neg", "thick", _NEG_W["thick"]))
    return items


def _lead_used_god(meta) -> bool:
    god_key = meta["items"][0][1]
    return god_key in (meta.get("main"), meta.get("concession"))


def _lead_phrase(kind, key, *, past, concessive, young_group=None) -> str:
    """한 요소의 관형절 또는 양보절."""
    if young_group and past:
        young = {"gain": copy.LEAD_YOUNG_GAIN, "load": copy.LEAD_YOUNG_LOAD}.get(kind)
        if young:
            return young[young_group][1 if concessive else 0]
        if kind == "neg" and key in copy.LEAD_YOUNG_NEG:
            return copy.LEAD_YOUNG_NEG[key][1 if concessive else 0]
    table = {"gain": copy.LEAD_GAIN, "load": copy.LEAD_LOAD, "pos": copy.LEAD_POS, "neg": copy.LEAD_NEG}[kind]
    return table[key][(2 if concessive else 0) + (1 if past else 0)]


def cycle_lead(cycle, info, profile, day_stem, *, past=False, young=False, seen=None) -> tuple[str, dict]:
    """대운 첫 문장의 몸통("…지만, …" 관형절)과 판정 메타. 말끝("10년입니다")은 부르는 쪽이 붙인다.

    주절은 기본이 대운 십성(그 10년의 주제)이다. 무게 합이 ±2 이상으로 십성 반대쪽에 기울고 그쪽에 무게 2 근거가 있을 때만
    그쪽 가장 무거운 요소가 주절이 되고, 십성은 양보절로 내려간다. 양보절은 주절 반대쪽 가장 무거운 요소.
    (형 하나·쏠림 하나 같은 약한 근거가 10년 전체의 주제를 덮지 않게 — 헌장 '근거가 약하면 쓰지 않는다')
    """
    items = _cycle_items(cycle, info, profile, day_stem)
    total = sum(w for _, _, w in items)
    god = items[0]
    young_group = copy.GOD_GROUP.get(cycle.get("ten_god")) if young else None
    if young_group not in copy.LEAD_YOUNG_GAIN:
        young_group = None
    pos = [it for it in items[1:] if it[2] > 0]
    neg = [it for it in items[1:] if it[2] < 0]
    top = lambda xs: max(xs, key=lambda it: abs(it[2])) if xs else None
    god_up = god[0] == "gain"
    # 주제를 뒤집으려면 합이 ±2 이상이고, 그쪽에 무게 2짜리(일간 충·일지/월지 충·억부 양쪽) 근거가 있어야 한다
    if total >= 2 and not god_up and abs(top(pos)[2]) >= 2:
        main, con = top(pos), god
    elif total <= -2 and god_up and abs(top(neg)[2]) >= 2:
        main, con = top(neg), god
    else:
        main = god
        con = top(neg) if god_up else top(pos)
    if total >= 2:
        verdict = "good_but" if neg or not god_up else "good"
    elif total <= -2:
        verdict = "hard_but" if pos or god_up else "hard"
    else:
        verdict = "mixed" if (pos or neg or god[2]) else "calm"
    text = _lead_phrase(main[0], main[1], past=past, concessive=False, young_group=young_group)
    if con is not None:
        con_text = _lead_phrase(con[0], con[1], past=past, concessive=True, young_group=young_group)
        if seen is not None:
            seen[f"lead_con:{con[1]}"] += 1
            if seen[f"lead_con:{con[1]}"] > 1:
                con_text = "이번에도 " + con_text      # 앞 구간과 같은 걸림을 같은 말로 되풀이하지 않는다
        text = con_text + ", " + text
    return text, {"verdict": verdict, "total": total, "items": items, "main": main[1],
                  "concession": con[1] if con is not None else None}


def _past_article(c, info, years, profile, seen: Counter, day_stem: str) -> tuple[str, dict]:
    god = c.get("ten_god") if c.get("ten_god") in copy.THEME_PAST else "peer"
    group = copy.GOD_GROUP[god]
    young = c["start_age"] <= 10                      # 어린 시절이 대부분인 첫 구간만 어린 시절 말로
    sk = _killing_type(profile) if god == "seven_killings" else None
    if young and seen["young"]:
        young = False                                 # 어린 시절 말은 첫 구간 한 번만
    seen["young"] += young
    lead_body, lead_meta = cycle_lead(c, info, profile, day_stem, past=True, young=young, seen=seen)
    lead = copy.PAST_LEAD.format(lead=lead_body)
    first, after_key = _kind_first(info, copy.KIND_PAST, seen, young)
    theme = list(copy.THEME_YOUNG[group] if young else copy.THEME_PAST[god])
    if sk and not young:
        theme = list(copy.SK_PAST.get(_sk_key(sk), theme))
    elif _lead_used_god(lead_meta):
        theme = theme[1:]                             # 첫 문장이 이미 그 십성의 10년을 말했다
    year_lines = _year_lines(years, seen)
    after = (copy.KIND_PAST_AFTER_YOUNG.get(after_key) if young else None) or copy.KIND_PAST_AFTER.get(after_key)
    if after_key.startswith("clash") and year_lines:
        after = None                                  # 흔들린 해가 같은 말을 구체적으로 한다
    if after_key in (lead_meta.get("main"), lead_meta.get("concession")):
        after = None                                  # 첫 문장이 이미 같은 말을 했다
    origin_key = "new" if info["new_power"] else "old"
    seen[f"origin:{origin_key}"] += 1
    pool = copy.ORIGIN_NEW if info["new_power"] else copy.ORIGIN_OLD
    origin = pool[0] if seen[f"origin:{origin_key}"] == 1 else (pool[1] if seen[f"origin:{origin_key}"] == 2 else "")
    if info["kind"] == "fill" and after:
        origin = ""                                   # '처음 들어온' 말을 두 번 하지 않는다
    body = _p([lead, first] + theme + [after or ""] + year_lines + [origin], where=f"past.{c['index']}")
    pillar = c["pillar"]
    why = [f"대운 {pillar['ganji']} — 천간 {pillar['stem']}({copy.GOD_KO.get(c.get('ten_god'), '')}) · 지지 {pillar['branch']}."]
    rel_text = _relation_text(info)
    if rel_text:
        why.append(rel_text)
    if sk and not young:
        why.append("칠살 대운 · " + copy.SK_WHY[sk])
    if years:
        why.append("크게 걸린 해: " + " · ".join(f"{y['year']}년 {y['ganji']}({_kinds_text(y['kinds'])})" for y in years) + ".")
    ages = f"{c['start_age']}~{c['end_age']}세"
    html = (f'<article class="lifetime-sub lifetime-past" data-report-cycle="{c["index"]}" data-cycle-state="past">'
            f'<h5>{escape(ages)} · {escape(pillar["ganji"])}</h5>'
            f'<p>{escape(body)}</p>' + _why(*why) + '</article>')
    return html, {"index": c["index"], "kind": info["kind"], "years": [y["year"] for y in years],
                  "verdict": lead_meta["verdict"]}


_KIND_KO = {"stem_clash": "일간 천간충", "clash:day": "일지 충", "clash:month": "월지 충", "clash:year": "년지 충",
            "clash:hour": "시지 충", "triple_punish": "삼형 완성", "stem_combine": "일간 합"}


def _kinds_text(kinds) -> str:
    out = []
    for k in kinds:
        if k.startswith("triple:"):
            out.append(f"{k.split(':')[1]} 삼합 완성")
        else:
            out.append(_KIND_KO.get(k, k))
    return "·".join(out)


def _relation_text(info) -> str:
    parts = []
    if info["fills"]:
        parts.append("원국에 없던 " + "·".join(info["fills"]) + " 채움")
    if info["thick"]:
        parts.append("이미 많은 " + "·".join(info["thick"]) + " 더함")
    if info["stem_rel"] == "clash":
        parts.append(f"천간 {info['stem']}이 일간과 충")
    elif info["stem_rel"] == "combine":
        parts.append(f"천간 {info['stem']}이 일간과 합")
    pos_ko = {"year": "년지", "month": "월지", "day": "일지", "hour": "시지"}
    for kind, pos in info["relations"]:
        parts.append(f"{info['branch']}–{pos_ko[pos]} " + {"clash": "충", "six": "육합", "punish": "형"}[kind])
    if info["triples"]:
        parts.append("·".join(info["triples"]) + " 삼합 완성")
    return ("원국과의 관계: " + ", ".join(parts) + ".") if parts else "원국 글자와 걸리는 충·합이 없습니다."


def _now_article(now, info, profile, missing, day_stem: str, seen=None) -> tuple[str, str]:
    god = now.get("ten_god") if now.get("ten_god") in copy.THEME_NOW else "peer"
    lead_body, lead_meta = cycle_lead(now, info, profile, day_stem, seen=seen)
    said = {lead_meta.get("main"), lead_meta.get("concession")}
    kind = info["kind"]
    first_tpl = copy.KIND_NOW[kind]
    if kind == "fill":
        e = info["fills"][0]
        el = copy.ELEMENT[e]
        lead = [copy.NOW_LEAD.format(lead=lead_body), first_tpl[0].format(name=el["name"], ja=_j(el["name"], "이/가"))]
        if e in missing:
            lead.append(first_tpl[1].format(power=el["power"], jw=_j(el["power"], "이/가")))
    elif kind in ("thick", "grow"):
        e = (info["thick"] or info["grow"])[0]
        el = copy.ELEMENT[e]
        lead = [copy.NOW_LEAD.format(lead=lead_body), first_tpl[0].format(name=el["name"], ja=_j(el["name"], "이/가")), first_tpl[1]]
    elif kind == "clash":
        pos = "day" if "day" in info["clash_pos"] else "month"
        label_pos = copy.POSITION[pos]
        lead = [copy.NOW_LEAD.format(lead=lead_body), first_tpl[0].format(pos=label_pos, jp=_j(label_pos, "을/를")), first_tpl[1]]
    else:
        lead = [copy.NOW_LEAD.format(lead=lead_body)] + list(first_tpl)
    # 보조 관계: 유형이 아닌 일지·월지 충, 일간 충을 한 문장 덧붙인다
    extra = []
    if kind != "clash":
        for pos in ("day", "month"):
            if pos in info["clash_pos"] and f"clash:{pos}" not in said:
                lp = copy.POSITION[pos]
                extra.append(copy.NOW_ALSO_CLASH.format(pos=lp))
                break
    if kind != "stem_clash" and info["stem_rel"] == "clash" and "stem_clash" not in said:
        extra.append(copy.NOW_ALSO_STEM)
    sk = _killing_type(profile) if god == "seven_killings" else None
    theme_now = copy.SK_NOW.get(_sk_key(sk), copy.THEME_NOW[god]) if sk else copy.THEME_NOW[god]
    if not (sk and _sk_key(sk) in copy.SK_NOW) and _lead_used_god(lead_meta):
        theme_now = theme_now[1:]                     # 첫 문장이 이미 그 십성의 10년을 말했다
    tip_now = copy.SK_TIP.get(_sk_key(sk), copy.TIP_NOW[god]) if sk else copy.TIP_NOW[god]
    p1 = _p(lead + list(theme_now), where="now.1")
    means_key = f"clash:{'day' if 'day' in info['clash_pos'] else 'month'}" if kind == "clash" else kind
    means = copy.MEANS_NOW.get(means_key) if means_key not in said else None
    if kind == "fill":
        name = copy.ELEMENT[info["fills"][0]]["name"]
        means = f"{name}{_j(name, '은/는')} " + means
    p2 = _p(extra + ([means] if means else []) + [tip_now], where="now.2")
    pillar = now["pillar"]
    why = [f"대운 {pillar['ganji']} — 천간 {pillar['stem']} · 지지 {pillar['branch']}, {copy.GOD_KO.get(now.get('ten_god'), '')}.",
           _relation_text(info)]
    if sk:
        why.append("칠살 대운 · " + copy.SK_WHY[sk])
    ages = f'{now["start_age"]}~{now["end_age"]}세'
    html = (f'<article class="lifetime-sub" data-lifetime-section="current-cycle" data-current-cycle="true" '
            f'data-report-cycle="{now["index"]}" data-cycle-ages="{ages}">'
            f'<h4>{escape(copy.NOW_HEADING.format(ages=ages, ganji=pillar["ganji"]))}</h4>'
            f'<p>{escape(p1)}</p><p>{escape(p2)}</p>' + _why(*why) + '</article>')
    return html, kind


def _next_article(nxt, info_next, profile, day_stem, now_info=None) -> str:
    lead_body, _ = cycle_lead(nxt, info_next, profile, day_stem)
    lines = [copy.NEXT_LEAD.format(start=nxt["start_age"], lead=lead_body)]
    if info_next["fills"]:
        e = info_next["fills"][0]
        name = copy.ELEMENT[e]["name"]
        if e in (now_info or {}).get("fills", []):
            lines.append(copy.NEXT_FILL_CONT.format(name=name))
        else:
            lines.append(copy.NEXT_FILL.format(name=name, ja=_j(name, "이/가")))
    lines.append(copy.NEXT_BRIDGE)
    text = _p(lines, where="next")
    return (f'<article class="lifetime-sub" data-lifetime-section="upcoming" data-locked="true" '
            f'data-report-cycle="{nxt["index"]}"><h4>{escape(copy.NEXT_HEADING)}</h4>'
            f'<p data-cycle-teaser="true">{escape(text)}</p>'
            f'<p class="reading-caption">🔒 {escape(copy.NEXT_LOCK_NOTE)}</p>'
            f'<a href="#paywall" data-paywall-cta="lifetime-cycles">대운 전체 풀이 열어보기</a></article>')


def _flow(core, profile, past, now, future, missing) -> tuple[str, str | None, dict]:
    ctx = _flow_ctx(core, profile)
    natal, day_stem, birth_year = ctx["natal"], ctx["day_stem"], ctx["birth_year"]
    this_year = date.today().year
    rows = []
    shown = past + ([now] if now else []) + [f for f in future if f.get("start_age", 0) < 90]
    for c in shown:
        is_now = now is not None and c.get("index") == now.get("index")
        is_next = bool(future) and c.get("index") == future[0].get("index")
        mark = copy.NOW_MARK if is_now else (copy.NEXT_MARK if is_next else (copy.PAST_MARK if c in past else ""))
        cls = ' class="is-now"' if is_now else ""
        rows.append(f'<tr{cls}><td>{c["start_age"]}~{c["end_age"]}</td>'
                    f'<td>{escape(c["pillar"]["ganji"])}</td><td>{escape(mark)}</td></tr>')
    head = "".join(f"<th>{h}</th>" for h in copy.TABLE_HEAD)
    table = f'<table class="lifetime-cycles"><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table>'

    parts = [f"<p>{escape(copy.FLOW_INTRO)}</p>", table]
    seen: Counter = Counter()
    past_meta = []
    if past:
        items = []
        for c in past:
            info = flow.classify_cycle(c, profile, natal, day_stem)
            years = flow.shaken_years(c, natal, day_stem, birth_year, this_year) if birth_year else []
            html, meta = _past_article(c, info, years, profile, seen, day_stem)
            items.append(html)
            past_meta.append(meta)
        parts.append(f'<h4>{escape(copy.PAST_TITLE)}</h4>' + "".join(items))
    now_kind = None
    now_info = None
    if now is not None:
        now_info = flow.classify_cycle(now, profile, natal, day_stem)
        html, now_kind = _now_article(now, now_info, profile, missing, day_stem, seen)
        parts.append(html)
    if future:
        parts.append(_next_article(future[0], flow.classify_cycle(future[0], profile, natal, day_stem), profile, day_stem, now_info))
    meta = {"past": past_meta, "now_kind": now_kind,
            "now_fill": (now_info or {}).get("fills", [])[:1]}
    return "".join(parts), now_kind, meta


# ---------------------------------------------------------------------------
# 조립
# ---------------------------------------------------------------------------
def build_lifetime_v3(core: MyeongriCoreResult, user_name: str, *, past, now, future,
                      current_selection, climate: str | None, strength: str | None = None) -> dict:
    profile = natal_profile(core)
    profile["strength"] = strength          # 칠살 대운 갈래 판단용(11/02)
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
    cands += [r for r in ordered if r.get("state") == "many"]
    cands += [r for r in ordered if r.get("state") == "few"]
    b16_used = "B16" in used
    first_seen = []
    for r in cands:
        if len(first_seen) >= 2 or (first_seen and r.get("state") == "few"):
            break
        if r["key"] in used or (b16_used and r.get("group") in ("재성", "비겁")):
            continue
        first_seen.append(r)
        used.add(r["key"])

    numbering = iter(range(1, 10))
    day_row = bank.DAY_MASTER_ROWS[profile["day_master"]]
    head = (f'<section class="lifetime-v3-head" data-lifetime-section="head">'
            f'<p class="now-me-lead">{escape(name)}님은 <strong>{escape(day_row["label"])}</strong>입니다.</p>'
            + _chart_html(core, profile, hidden_counts) + '</section>')

    map_html, map_meta = _map(core, profile, hidden_counts, {r["key"] for r, _ in core_picks})
    html = head + _section("map", next(numbering), map_html)

    sec = next(numbering)
    core_parts = [f"<p>{escape(copy.CORE_INTRO.format(name=name, n=copy.COUNT_KO.get(len(core_picks), len(core_picks))))}</p>"]
    for i, (row, mode) in enumerate(core_picks, 1):
        if mode == "main":
            heading = f"{sec}-{i}. '{row['label']}'"
        else:
            heading = f"{sec}-{i}. '{mode.split(':', 1)[1]}'의 뒷면 — '{row['label']}'"
        core_parts.append(_row_block(row, profile, seed, 3 + i * 2, heading, style=i - 1))
    html += _section("core", sec, "".join(core_parts))

    if first_seen:
        sec = next(numbering)
        parts = [f"<p>{escape(copy.FIRST_SEEN_INTRO)}</p>"]
        for i, row in enumerate(first_seen, 1):
            parts.append(_row_block(row, profile, seed, 11 + i * 2, f"{sec}-{i}. '{row['label']}'",
                                    style=len(core_picks) + i - 1))
        html += _section("first-seen", sec, "".join(parts))

    sec = next(numbering)
    domains_html, domain_meta = _domains(core, profile, climate, sec, name)
    html += _section("domains", sec, domains_html)

    flow_html, now_kind, flow_meta = _flow(core, profile, past, now, future, map_meta["missing"])
    html += _section("flow", next(numbering), flow_html)

    # 6. 한마디 — 일간 비유 + 대표 결 + 빌려 쓰는 것 + 지금 10년 + 마무리 한 줄
    top = core_picks[0][0]
    closing = [copy.CLOSING_LEAD.format(name=name, trait=top["trait"])]
    if map_meta["missing"]:
        lacks = [copy.LACK_PLAIN[e] for e in map_meta["missing"]]
        joined = lacks[0] if len(lacks) == 1 else _jo(lacks[0], "과/와") + " " + lacks[1]
        closing.append(copy.CLOSING_MISSING.format(lacks=_jo(joined, "은/는")))
    if now is not None and now_kind:
        god = now.get("ten_god") if now.get("ten_god") in copy.NOW_PLAIN else "peer"
        closing.append(copy.CLOSING_NOW.format(plain=copy.NOW_PLAIN[god]))
        if now_kind in copy.CLOSING_NOW_KIND:
            closing.append(copy.CLOSING_NOW_KIND[now_kind])
        if now_kind in copy.CLOSING_NUDGE:
            closing.append(copy.CLOSING_NUDGE[now_kind])
    closing.append(copy.CLOSING_APHORISM[profile["day_element"]])
    html += _section("closing", next(numbering), f'<p class="lifetime-closing">{escape(_p(closing, where="closing"))}</p>')

    evidence = {
        "rows": [r["key"] for r, _ in core_picks], "first_seen": [r["key"] for r in first_seen],
        "map": map_meta, "domains": domain_meta, "flow": flow_meta, "now_kind": now_kind,
        "hour_confidence": profile["hour_confidence"],
    }
    return {"html": html, "evidence": evidence, "version": V3_VERSION, "copy_version": copy.COPY_VERSION}
