"""Lifetime study and exam report backed by the shared Myeongri core."""

from __future__ import annotations

from collections import Counter
from html import escape

from app.engine.core.models import MyeongriCoreResult
from app.engine.services.applied_guidance import direction_advice, state_basis
from app.engine.semantic import build_service_query


_TEN_GOD = {
    "peer": "비견", "rob_wealth": "겁재", "eating_god": "식신",
    "hurting_officer": "상관", "direct_wealth": "정재",
    "indirect_wealth": "편재", "direct_officer": "정관",
    "seven_killings": "편관", "direct_resource": "정인",
    "indirect_resource": "편인",
}
_STRENGTH_GUIDE = {
    "extremely_weak": "긴 학습량을 한 번에 감당하기보다 짧은 단위로 나누고, 복습과 휴식을 먼저 고정하는 편이 좋습니다.",
    "weak": "새 범위를 넓히기 전에 기본 개념과 복습 시간을 확보하면 학습의 지속력이 좋아집니다.",
    "balanced": "이해·정리·문제풀이를 고르게 배치하되 실제 학습 기록으로 균형을 점검하는 편이 좋습니다.",
    "strong": "계획을 빠르게 밀어붙이는 힘은 있으나 익숙한 방식만 고집하지 말고 오답 검토와 피드백을 의도적으로 넣는 편이 좋습니다.",
    "extremely_strong": "학습량을 늘리는 것보다 틀린 근거를 다시 확인하고 타인의 평가 기준에 맞춰 답을 다듬는 과정이 중요합니다.",
}
_CYCLE_TOPIC = {
    "direct_resource": "교재와 기준을 차분히 익히고 반복 복습하는 일",
    "indirect_resource": "새 관점과 자료를 탐색하되 핵심 범위를 선별하는 일",
    "eating_god": "배운 내용을 꾸준히 문제풀이와 결과물로 바꾸는 일",
    "hurting_officer": "자기 언어로 설명하고 답안의 논리를 날카롭게 다듬는 일",
    "direct_officer": "정해진 일정·출제 기준·평가 규칙에 맞춰 준비하는 일",
    "seven_killings": "시간 압박 속에서도 우선순위를 정하고 실전 대응력을 기르는 일",
    "peer": "혼자 공부하는 힘과 동료 학습의 균형을 잡는 일",
    "rob_wealth": "비교와 경쟁에 흔들리지 않고 자기 진도를 지키는 일",
    "direct_wealth": "학습 시간과 진도를 측정 가능한 계획으로 관리하는 일",
    "indirect_wealth": "여러 기회를 좇기보다 시험 목적에 맞는 선택지를 추리는 일",
}
_PHASES = (
    ("초년기", 1, 2, "기초 학습 습관과 이해 방식을 만들어 가는 구간"),
    ("청년기", 3, 4, "전공·자격·진로에 맞춰 학습법을 구체화하는 구간"),
    ("중장년기", 5, 6, "실무 경험을 공부·자격·새 전문성으로 연결하는 구간"),
    ("말년기", 7, 9, "쌓인 지식을 정리하고 깊이 있는 배움으로 이어가는 구간"),
)


def _uncertainty(core: MyeongriCoreResult) -> str:
    if not core.uncertainty.time_unknown:
        return ""
    return ('<div style="background:#FFF7ED;border:1px solid #FED7AA;padding:12px 14px;border-radius:12px;margin-top:12px;">'
            '<div style="font-size:13px;font-weight:800;color:#9A3412;">생시 미상 안내</div>'
            '<p style="font-size:12.5px;color:#7C2D12;margin:5px 0 0;line-height:1.65;">시주에 따라 일부 학습 관련 십성과 강약이 달라질 수 있어, '
            '여러 시주에서 공통으로 유지되는 원국과 대운 흐름을 중심으로 설명했습니다.</p></div>')


STUDY_NARRATIVE_VERSION = "study-v3"   # 11/13: 공부 머리·방해하는 습관 무료 + 유료 8칸(옛 공통 안내 걷어 냄)

_BOX = "border:1px solid #E2E8F0;border-radius:12px;padding:12px 14px;background:#FFFFFF;"
_SKELETON = (
    '<div data-locked-body="true" aria-hidden="true" style="filter:blur(3px);margin-top:8px;opacity:.55;">'
    '<span style="display:block;height:9px;margin:6px 0;border-radius:5px;background:#CBD5E1;"></span>'
    '<span style="display:block;height:9px;margin:6px 0;border-radius:5px;background:#CBD5E1;width:92%;"></span>'
    '<span style="display:block;height:9px;margin:6px 0;border-radius:5px;background:#CBD5E1;width:78%;"></span>'
    '</div>')
_RES = ("direct_resource", "indirect_resource")
_OFF = ("direct_officer", "seven_killings")
_OUT = ("eating_god", "hurting_officer")
_WEA = ("direct_wealth", "indirect_wealth")
_PEE = ("peer", "rob_wealth")
_GROUP = {**{g: "resource" for g in _RES}, **{g: "officer" for g in _OFF}, **{g: "output" for g in _OUT},
          **{g: "wealth" for g in _WEA}, **{g: "peer" for g in _PEE}}


def _sec_html(key: str, title: str, body: str, paywall: str = "unlocked", tier: str | None = None) -> str:
    t = f' data-study-tier="{tier}"' if tier else ""
    return f'<section data-study-section="{key}"{t} data-paywall="{paywall}"><h2>{escape(title)}</h2>{body}</section>'


def _p(text: str, attr: str = "") -> str:
    return f"<p{attr}>{escape(text)}</p>" if text else ""


def _pick_line(pool, start, used):
    for i in range(len(pool)):
        line = pool[(start + i) % len(pool)]
        if line not in used:
            used.add(line)
            return line
    return ""


def _years(ys) -> str:
    return "·".join(f"{y}년" for y in ys[:3])


def _analyse(core: MyeongriCoreResult, query: dict) -> dict:
    from app.engine.services import love_depth
    from app.engine.shensha.engine import _DAY_STEM_RULES
    counts = love_depth.natal_counts(core)
    n = {k: len(v) for k, v in counts.items()}
    tot = lambda gods: sum(n.get(g, 0) for g in gods)
    res, off, out, wea, pee = tot(_RES), tot(_OFF), tot(_OUT), tot(_WEA), tot(_PEE)
    strength = query["synthesis"].get("strength_state")
    weak = strength in ("weak", "extremely_weak")
    strong = strength in ("strong", "extremely_strong")
    direct_r, indirect_r = n.get("direct_resource", 0), n.get("indirect_resource", 0)
    resource_kind = "absorb" if direct_r >= indirect_r else "insight"
    if off and res >= 2 and res >= out:      # 관인상생: 관성이 있고 인성이 두 자리 이상, 배움이 재주보다 작지 않을 때
        mind = "exam"
    elif res >= 2:
        mind = resource_kind
    elif out >= 2:
        mind = "make"
    elif wea >= 3:
        mind = "field"
    elif pee >= 3:
        mind = "rival"
    elif res == 1:
        mind = resource_kind
    elif out == 1:
        mind = "make"
    else:
        mind = "even"
    style = ""
    if mind == "make":
        style = "hurting_officer" if n.get("hurting_officer", 0) > n.get("eating_god", 0) else "eating_god"
    elif mind == "exam":
        style = "direct_resource" if direct_r >= indirect_r else "indirect_resource"
    p = core.natal_facts.pillars
    dm = p["day"].stem
    literary_branch = _DAY_STEM_RULES["literary_star"][dm][0]
    literary = any(p.get(k) is not None and p[k].branch == literary_branch for k in ("year", "month", "day", "hour"))
    score = {"scatter": out if out >= 2 else 0,
             "start": indirect_r + (1 if indirect_r > direct_r else 0) if indirect_r else 0,
             "prep": res if (res >= 2 and direct_r >= indirect_r) else 0,
             "busy": wea if (wea >= 3 or (wea >= 2 and res <= 1)) else 0,
             "compare": pee if pee >= 2 else 0,
             "tense": off if off >= 2 else 0,
             "skip": 1.5 if res == 0 else 0}
    leaks = [k for k, v in sorted(score.items(), key=lambda kv: -kv[1]) if v][:3]
    for extra in ("cram", "skip", "scatter", "compare"):
        if len(leaks) >= 3:
            break
        if extra not in leaks:
            leaks.append(extra)
    rank = sorted((("resource", res), ("output", out), ("officer", off), ("wealth", wea), ("peer", pee)),
                  key=lambda kv: -kv[1])
    method = [k for k, v in rank if v][:2] or ["resource"]
    if mind == "exam":
        exam = "exam"
    elif n.get("hurting_officer", 0) and off:
        exam = "clash"
    elif res >= 2:
        exam = "written"
    elif out >= 2 or (out and not res):
        exam = "practical"
    elif n.get("seven_killings", 0):
        exam = "pressure"
    else:
        exam = "even"
    return dict(counts=counts, n=n, res=res, off=off, out=out, wea=wea, pee=pee, strength=strength, weak=weak,
                strong=strong, mind=mind, style=style, literary=literary, literary_branch=literary_branch,
                leaks=leaks, method=method, exam=exam, dm=dm)


def _compose_paid(core: MyeongriCoreResult, name: str, a: dict, seed: int, fixed_year: int | None) -> dict:
    from datetime import date
    from app.engine.calendar import to_solar
    from app.engine.constants import GAN_KO, ZHI_KO, GAN_WUXING
    from app.engine.facts.hidden_stems import get_hidden_stems
    from app.engine.facts.ten_gods import get_ten_god
    from app.engine.services import daily_score, theme_timing
    from app.engine.services import study_sections as sec
    from app.engine.services.daily_score import calendar_ganji
    from app.engine.services.element_balance import GENERATES, GENERATED_BY, composition, element_tiers, natal_balance

    dm = a["dm"]
    god = lambda stem: getattr(get_ten_god(dm, stem), "value", "")
    birth = to_solar(core.input.birth_date, core.input.calendar_type, core.input.is_leap_month)
    this_year = theme_timing.window_start(core)[0]
    tiers = element_tiers(core)["tiers"]
    comp = composition(core)
    dm_el = GAN_WUXING[dm]

    # 2-2 학교 공부와의 궁합
    fit = {"exam": 2, "absorb": 2, "insight": 1, "make": 1, "even": 1, "field": 0, "rival": 0}[a["mind"]] + (1 if a["literary"] else 0)
    school_cycle, school_span = "plain", ""
    for c in (core.timing.luck_cycle or {}).get("cycles", []):
        if c.get("start_age", 0) <= 14 <= c.get("end_age", 0):          # 중학교 무렵(세는 나이 14세)을 품은 대운
            g = _GROUP.get(god(c["pillar"]["stem"]))
            school_span = f'{c["start_age"]}~{c["end_age"]}세'
            school_cycle = ("good" if g in ("resource", "officer") or (g == "output" and not a["weak"])
                            else "busy" if g == "wealth" else "plain")
    fit += 1 if school_cycle == "good" else -1 if school_cycle == "busy" else 0
    school_level = "high" if fit >= 3 else "mid" if fit >= 1 else "other"
    school = [sec.SCHOOL[school_level]] + ([sec.SCHOOL_CYCLE[school_cycle].format(span=school_span)] if school_span else [])

    # 2-3 진로 방향 (학문 · 기술 · 예체능)
    n = a["n"]
    path_score = {
        "scholar": 2 * n.get("direct_resource", 0) + n.get("indirect_resource", 0) + (a["off"] if a["res"] else 0) + (1 if a["literary"] else 0),
        "craft": 2 * n.get("eating_god", 0) + a["wea"] + n.get("direct_officer", 0),
        "art": 2 * n.get("hurting_officer", 0) + n.get("indirect_resource", 0) + n.get("rob_wealth", 0),
    }
    order = sorted(path_score, key=lambda k: -path_score[k])
    if path_score[order[0]] - path_score[order[2]] <= 1:
        pathway = [sec.PATHWAY_LEAD, sec.PATHWAY_EVEN]
    else:
        t1, x1 = sec.PATHWAY[order[0]]
        pathway = [sec.PATHWAY_LEAD, sec.PATHWAY_FIRST.format(name=name, title=t1, text=x1)]
        if path_score[order[1]] >= 2 and path_score[order[0]] - path_score[order[1]] <= 2:
            pathway.append(sec.PATHWAY_SECOND.format(title=sec.PATHWAY[order[1]][0]))

    # 3 공부법
    method = [sec.METHOD[k] for k in a["method"]] + [sec.METHOD_STRENGTH[
        "weak" if a["weak"] else "strong" if a["strong"] else "balanced"]]

    # 4 분야
    els = []
    if a["out"]:
        els.append(GENERATES[dm_el])
    if a["res"]:
        els.append(GENERATED_BY[dm_el])
    for e in sorted(comp, key=lambda e: -comp[e]):
        if len(els) >= 2:
            break
        if e != dm_el and e not in els:
            els.append(e)
    field = [sec.FIELD_LEAD, sec.FIELD_FIRST.format(name=name, el=sec.ELEMENT_NAME[els[0]], field=sec.FIELD[els[0]]),
             sec.FIELD_SECOND.format(el=sec.ELEMENT_NAME[els[1]], field=sec.FIELD[els[1]]), sec.FIELD_NOTE]

    # 5 시험운
    exam = [sec.EXAM[a["exam"]]] + ([sec.EXAM_NO_OFFICER] if not a["off"] else [])

    # 6 나이
    age, kinds, now_line, now_state = [], [], "", "plain"
    age_now = this_year - birth.year + 1
    tpl = {"learn": (sec.AGE_LEARN, sec.AGE_LEARN_AGAIN), "exam": (sec.AGE_EXAM, sec.AGE_EXAM_AGAIN),
           "make": (sec.AGE_MAKE, sec.AGE_MAKE_AGAIN), "busy": (sec.AGE_BUSY, sec.AGE_BUSY_AGAIN)}
    age_ev = []
    for c in (core.timing.luck_cycle or {}).get("cycles", []):
        if c.get("end_age", 0) < 8 or c.get("start_age", 0) > 67:
            continue
        g = _GROUP.get(god(c["pillar"]["stem"]))
        state = ("learn" if g == "resource" else "exam" if (g == "officer" and not a["weak"])
                 else "make" if (g == "output" and not a["weak"]) else "busy" if g == "wealth" else "plain")
        span = f'{c["start_age"]}~{c["end_age"]}세'
        gz = GAN_KO.get(c["pillar"]["stem"], "") + ZHI_KO.get(c["pillar"]["branch"], "")
        if state != "plain":
            age.append(tpl[state][1 if state in kinds else 0].format(span=span, ganji=gz))
            kinds.append(state)
        if c["start_age"] <= age_now <= c["end_age"]:
            now_state = state
            now_line = sec.AGE_NOW.format(span=span, state=sec.AGE_NOW_STATE[state])
        age_ev.append(dict(span=span, state=state))

    # 7 좋은 해
    exam_y, learn_y, busy_y = [], [], []
    for y in range(this_year, this_year + 10):
        gz = calendar_ganji(date(y, 6, 15))[0]
        sg = _GROUP.get(god(gz[0]))
        bg = _GROUP.get(god(get_hidden_stems(gz[1]).stems[0].stem))
        if (sg == "officer" and (a["res"] or bg == "resource")) or (sg == "resource" and bg == "officer"):
            exam_y.append(y)
        elif sg == "resource":
            learn_y.append(y)
        elif sg == "wealth" and (a["res"] <= 1 or a["weak"]):
            busy_y.append(y)
    years = []
    if exam_y:
        years.append(sec.YEAR_GOOD.format(years=_years(exam_y)))
    if learn_y:
        years.append(sec.YEAR_LEARN.format(years=_years(learn_y)))
    if not years:
        years.append(sec.YEAR_NONE)
    if busy_y:
        years.append(sec.YEAR_BUSY.format(years=_years(busy_y)))

    # 8 12개월
    start = (fixed_year, 1) if fixed_year else theme_timing.window_start(core)
    rows, prev, used = [], None, set()
    for y, m in theme_timing.window_months(start):
        target = date(y, m, 15)
        if target < birth:
            continue
        mg = calendar_ganji(target)[1]
        g = god(mg[0])
        grp = _GROUP.get(g)
        grade, reason = "normal", None
        if grp == "resource":
            grade, reason = "good", ("관인상생" if a["mind"] == "exam" else "인성 · 배움")
        elif grp == "officer":
            if a["mind"] == "exam":
                grade, reason = "good", "관인상생"
            elif a["weak"]:
                grade, reason = "caution", "관성 · 압박"
            # 관인상생이 아닌 원국의 관성 달은 평가는 오지만 배움으로 이어 주는 힘이 약해 보통으로 둔다(좋음이 절반 가까이 되던 것)
        elif grp == "wealth" and (a["res"] == 1 or a["weak"]):     # 재극인은 인성이 약할 때 공부를 누른다
            grade, reason = "caution", "재극인"
        elif g == "hurting_officer" and a["off"]:
            grade, reason = "caution", "상관견관"
        if grade == "normal" and mg[1] == a["literary_branch"]:
            grade, reason = "good", "문창"
        score = daily_score.evaluate(core, mg, target)["score"]
        rows.append(dict(y=y, m=m, grade=grade, label=sec.GRADE_LABEL[grade], score=score, reason=reason,
                         line=_pick_line(sec.MONTH_LINE[grade], seed + m, used),
                         display=theme_timing.month_label(y, m, prev)))
        prev = y
    goods = sorted((r for r in rows if r["grade"] == "good"), key=lambda r: -r["score"])
    bads = sorted((r for r in rows if r["grade"] == "caution"), key=lambda r: r["score"])
    picked = ([goods[0]] if goods else []) + ([bads[0]] if bads else [])
    for r in sorted(goods[1:] + bads[1:], key=lambda r: -abs(r["score"] - 75)):
        if len(picked) >= 3:
            break
        if r["reason"] not in {x["reason"] for x in picked}:
            picked.append(r)
    picked.sort(key=lambda r: (r["y"], r["m"]))
    keys = [dict(y=r["y"], m=r["m"], display=f'{r["y"]}년 {r["m"]}월', label=r["label"],
                 text=f'{sec.STUDY_REASON[r["reason"]]} {sec.STUDY_ADVICE[r["reason"]]}') for r in picked]

    # 9 개운
    ranking = natal_balance(core)["ranking"]
    good = [e for e in ranking if tiers[e] == "good"]
    res_el = GENERATED_BY[dm_el]
    el = res_el if tiers[res_el] != "avoid" else (good[0] if good else res_el)
    color = sec.COLOR[el]
    i = "이" if (ord(color[-1]) - 0xAC00) % 28 else "가"
    lb = a["literary_branch"]
    kaiun = [sec.KAIUN_LEAD,
             sec.KAIUN_DESK.format(name=name, branch=lb, ko=ZHI_KO.get(lb, ""), direction=sec.DIRECTION[lb]),
             sec.KAIUN_COLOR.format(el=sec.ELEMENT_NAME[el], color=color, i=i), sec.KAIUN_HABIT]

    # 10 실천
    bullets = [sec.BULLET_MIND[a["mind"]], sec.BULLET_AGE[now_state]]
    if goods:
        bullets.append(sec.BULLET_MONTH.format(month=f'{goods[0]["y"]}년 {goods[0]["m"]}월'))
    return dict(school=school, pathway=pathway, method=method, field=field, exam=exam, age=age, age_now=now_line, years=years, months=rows, keys=keys,
                month_caption=sec.MONTH_CAPTION.format(y=start[0], m=start[1]), kaiun=kaiun, bullets=bullets,
                evidence=dict(mind=a["mind"], school=school_level, school_cycle=school_cycle, pathway=order if len(pathway) > 2 or pathway[1] != sec.PATHWAY_EVEN else [], path_score=path_score, leaks=a["leaks"], method=a["method"], fields=els, exam=a["exam"],
                              literary=a["literary"], ages=age_ev, now_state=now_state, exam_years=exam_y,
                              learn_years=learn_y, busy_years=busy_y, kaiun_element=el,
                              months=[dict(month=f'{r["y"]}-{r["m"]:02d}', grade=r["grade"], reason=r["reason"]) for r in rows]))


def build_lifetime_study_report(core: MyeongriCoreResult, user_name: str, *, is_unlocked: bool = False,
                                year: int | None = None) -> dict:
    """학업운 v3. is_unlocked 는 키워드 전용이며 `is True` 일 때만 유료 칸을 만든다(직업·애정·건강·재물과 같은 원칙)."""
    from app.engine.calendar import to_solar
    from app.engine.services.annual_copy import seed_from
    from app.engine.services import study_sections as sec

    unlocked = is_unlocked is True
    query = build_service_query(core, "study")
    name = user_name or "회원"
    a = _analyse(core, query)
    birth = to_solar(core.input.birth_date, core.input.calendar_type, core.input.is_leap_month)
    seed = seed_from(birth.isoformat(), "study", year or 0)

    head, body = sec.MIND[a["mind"]]
    mind_html = (f"<h3>{escape(head)}</h3>" + _p(body.format(name=name)) + _p(sec.STYLE.get(a["style"], ""))
                 + (_p(sec.LITERARY) if a["literary"] else ""))
    leaks_html = '<div style="display:grid;gap:8px;">' + "".join(
        f'<div data-study-trap="{k}" style="{_BOX}"><strong>{escape(t)}</strong>'
        f'<p style="margin:4px 0 0;">{escape(x)}</p><p data-study-trap-fix="{k}" style="margin:4px 0 0;">{escape(f)}</p></div>'
        for k, (t, x, f) in ((k, sec.LEAK[k]) for k in a["leaks"])) + "</div>"
    free = (_sec_html("mind", "타고난 공부 머리", mind_html, "free", "1")
            + _sec_html("leaks", f"공부를 방해하는 습관 {len(a['leaks'])}가지", leaks_html, "free", "2")
            + '<hr data-paywall-boundary="study" style="border:0;border-top:1px dashed #94A3B8;margin:18px 0;">')
    evidence_summary = dict(natal=dict(mind=a["mind"], strength=a["strength"], ten_gods=a["n"]),
                            copy_ids=dict(tier1=a["mind"], tier2=a["leaks"]))
    if unlocked:
        d = _compose_paid(core, name, a, seed, year)
        rows = "".join(
            f'<li data-study-month="{m["y"]}-{m["m"]:02d}" data-month-grade="{m["grade"]}">'
            f'<strong>{escape(m["display"])} · {escape(m["label"])}</strong> {escape(m["line"])}</li>' for m in d["months"])
        keys = "".join(
            f'<div data-study-key-month="{k["y"]}-{k["m"]:02d}" style="{_BOX}"><strong>{escape(k["display"])} · {escape(k["label"])}</strong>'
            f'<p style="margin:4px 0 0;">{escape(k["text"])}</p></div>' for k in d["keys"])
        lst = lambda key, items: "<ul>" + "".join(f'<li data-study-{key}="{i}">{escape(t)}</li>' for i, t in enumerate(items, 1)) + "</ul>"
        gated = "".join((
            _sec_html("school", sec.SCHOOL_HEADING, "".join(_p(t) for t in d["school"])),
            _sec_html("pathway", sec.PATHWAY_HEADING, "".join(_p(t) for t in d["pathway"])),
            _sec_html("method", sec.METHOD_HEADING, "".join(_p(t) for t in d["method"])),
            _sec_html("field", sec.FIELD_HEADING, "".join(_p(t) for t in d["field"])),
            _sec_html("exam", sec.EXAM_HEADING, "".join(_p(t) for t in d["exam"])),
            _sec_html("age", sec.AGE_HEADING, _p(sec.AGE_LEAD) + (lst("age", d["age"]) if d["age"] else "") + _p(d["age_now"])),
            _sec_html("year", sec.YEAR_HEADING, "".join(_p(t) for t in d["years"])),
            _sec_html("months", "앞으로 12개월 학업 흐름", f'<p class="reading-caption">{escape(d["month_caption"])}</p>'
                      f'<ul style="padding-left:18px;">{rows}</ul>'
                      + (f'<h3>눈여겨볼 달</h3><div style="display:grid;gap:8px;">{keys}</div>' if keys else _p(sec.NO_KEY_MONTH)), tier="3"),
            _sec_html("kaiun", sec.KAIUN_HEADING, "".join(_p(t) for t in d["kaiun"])),
            _sec_html("actions", "공부를 이어 가는 실천",
                      "<ol>" + "".join(f'<li data-study-action="{i}">{escape(b)}</li>' for i, b in enumerate(d["bullets"], 1)) + "</ol>", tier="4"),
        ))
        evidence_summary["months"] = d["evidence"]["months"]
        evidence_summary["v3"] = {k: v for k, v in d["evidence"].items() if k != "months"}
    else:
        titles = "".join(f'<li data-study-locked="{k}">{escape(t)}</li>' for k, t in sec.LOCKED_SECTIONS)
        gated = ('<section data-study-tier="3" data-paywall="locked" data-locked="true" '
                 'style="border:1px dashed #94A3B8;border-radius:12px;background:#F8FAFC;padding:14px;margin-bottom:8px;">'
                 '<div style="font-size:12px;color:#64748B;font-weight:800;">🔒 잠긴 풀이</div>'
                 '<h2 style="margin:4px 0 0;">이어지는 풀이</h2>'
                 f'<p data-study-teaser="3" style="margin:6px 0 0;">{escape(sec.LOCKED_TEASER)}</p>'
                 f'<ul style="padding-left:18px;margin:6px 0 0;">{titles}</ul>{_SKELETON}</section>'
                 '<a href="#paywall-theme-study" data-paywall-cta="theme-study" style="display:inline-block;margin-top:6px;'
                 'padding:10px 16px;border-radius:10px;background:#1D2129;color:#fff;font-weight:700;text-decoration:none;">'
                 f'{escape(sec.CTA)}</a>')
    n = a["n"]
    evidence = ('<details class="reading-evidence"><summary>이 풀이의 근거 · 명리 용어 포함</summary><h4>평생 학습 구조</h4>'
                f'<p>원국 여덟 글자(천간 3 + 지지 본기 4) 기준 정인 {n.get("direct_resource", 0)}곳, 편인 {n.get("indirect_resource", 0)}곳, '
                f'식상 {a["out"]}곳, 관성 {a["off"]}곳, 재성 {a["wea"]}곳, 비겁 {a["pee"]}곳. '
                f'문창귀인 {a["literary_branch"]}{"이 원국에 있음" if a["literary"] else "은 원국에 없음"}. '
                '십성의 개수는 지능이나 합격 점수가 아닙니다.</p>'
                f'<p>{escape(direction_advice(query["applied_state"], "study", _STRENGTH_GUIDE.get(a["strength"], "")))}</p></details>')
    content = (f'<div class="theme-reading" data-theme="study" data-narrative-version="{STUDY_NARRATIVE_VERSION}" '
               f'data-unlocked="{str(unlocked).lower()}">' + free + gated + evidence + _uncertainty(core)
               + f'<p class="reading-caption">{escape(sec.DISCLAIMER)}</p></div>')
    return {"analysis_basis": state_basis(query["applied_state"]), "title": f"{escape(name)}님 정통 명리 평생 학업·시험운",
            "content": content, "narrative_version": STUDY_NARRATIVE_VERSION, "is_unlocked": unlocked,
            "evidence_summary": evidence_summary}
