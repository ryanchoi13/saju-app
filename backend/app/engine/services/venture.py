"""사업운 테마 (2026-11-25). 무료 2칸 + 유료 8칸, 다른 테마운과 같은 220복채·같은 잠금 원칙.

보안 원칙(직업·애정·건강·재물·학업과 같음)
- is_unlocked 는 키워드 전용이며 `is True` 일 때만 유료 칸을 만든다. 잠금 상태에서는 유료 본문을 어디에도 싣지 않고,
  5년·월별 계산도 하지 않는다.
판정은 business_fit(일의 성격·업종) · business_timing(5년·택일)의 이름 붙은 규칙만 쓴다.
"""
from __future__ import annotations

from datetime import date
from html import escape

from app.engine.constants import GAN_KO, GAN_WUXING, ZHI_KO
from app.engine.core.models import MyeongriCoreResult
from app.engine.services import business_fit as bf
from app.engine.services import business_timing as bt
from app.engine.services import career_copy as ccopy
from app.engine.services import theme_timing
from app.engine.services import venture_sections as sec
from app.engine.services.daily_score import _god_group, calendar_ganji
from app.engine.services.element_balance import element_tiers, natal_balance
from app.engine.services.theme_core import hidden_tally, tally
from app.engine.services.theme_voice import with_hashtags

VENTURE_NARRATIVE_VERSION = "venture-v1"

_BOX = "border:1px solid #E2E8F0;border-radius:12px;padding:12px 14px;background:#FFFFFF;"
_SKELETON = ('<div aria-hidden="true" style="margin-top:10px;display:grid;gap:6px;">'
             + "".join(f'<div style="height:10px;width:{w}%;background:#E2E8F0;border-radius:6px;"></div>' for w in (92, 78, 85))
             + "</div>")
_PEERS = {"peer": "peers"}
_TEN_GOD_GROUP = {
    "eating_god": "output", "hurting_officer": "output", "direct_wealth": "wealth", "indirect_wealth": "wealth",
    "direct_officer": "officer", "seven_killings": "officer", "direct_resource": "resource",
    "indirect_resource": "resource", "peer": "peers", "rob_wealth": "peers",
}


def _sec(key: str, title: str, body: str, paywall: str = "unlocked") -> str:
    return f'<section data-venture-section="{key}" data-paywall="{paywall}"><h2>{escape(title)}</h2>{body}</section>'


def _p(text: str) -> str:
    return f"<p>{escape(text)}</p>" if text else ""


def _ko(ganji: str) -> str:
    return GAN_KO.get(ganji[0], "") + ZHI_KO.get(ganji[1], "")


def _join_years(ys: list[int]) -> str:
    return "·".join(f"{y}년" for y in ys)


def _strength(core: MyeongriCoreResult) -> str | None:
    s = str(core.synthesis.strength_state or "")
    return ccopy.strength_key(s) if ccopy.strength_decided(s) else None


def _analyse(core: MyeongriCoreResult) -> dict:
    counts = tally(core)
    lead = ccopy.lead_group(counts, hidden_tally(core))
    strength = _strength(core)
    peers = bt.natal_peer_count(core)
    rob = counts.get("rob_wealth", 0)
    wealth = counts.get("direct_wealth", 0) + counts.get("indirect_wealth", 0)
    output = counts.get("eating_god", 0) + counts.get("hurting_officer", 0)
    traps = []
    cond = {
        "partner": peers >= 2,
        "big_bet": rob >= 1 and wealth >= 1,
        "many": lead in ("wealth", "output") and wealth + output >= 3,
        "heavy": strength == "weak" and wealth >= 2,
        "alone": strength == "strong",
        "price": output >= 2 and wealth == 0,
        "prep": lead == "resource",
        "rules": lead == "officer",
    }
    for k, hit in cond.items():
        if hit and len(traps) < 3:
            traps.append(k)
    for k in sec.TRAP_FILL:
        if len(traps) >= 3:
            break
        if k not in traps:
            traps.append(k)
    return dict(lead=lead, strength=strength, peers=peers, rob=rob, wealth=wealth, output=output, traps=traps,
                counts={k: v for k, v in counts.items()})


def _paid(core: MyeongriCoreResult, name: str, a: dict) -> tuple[str, dict]:
    today = bt.today_of(core)
    start = theme_timing.window_start(core)
    dm = core.natal_facts.pillars["day"].stem
    tiers = element_tiers(core)["tiers"]

    # 3 성격
    ranks = bf.nature_ranking(core, today.year, with_cycle=False)
    items = []
    for r in ranks:
        reason = (r["good"] or r["hard"] or r["note"] or [""])[0]
        items.append(f'<li data-venture-kind="{r["nature"]}" data-grade="{r["grade"]}"><strong>{escape(r["name"])} · '
                     f'{escape(sec.GRADE_WORD[r["grade"]])}</strong> <span>({escape(r["examples"])})</span> {escape(reason)}</li>')
    kind = _p(sec.KIND_LEAD) + '<ul style="padding-left:18px;">' + "".join(items) + "</ul>"

    # 4 업종
    res = bf.compare_options(core, [dict(category=k, capital="mid") for k in bf.CATALOG], today.year)
    groups = {"good": [], "ok": [], "hard": []}
    for o in res["options"]:
        groups[o["grade"]].append(o["name"])
    industry = _p(sec.INDUSTRY_LEAD) + "".join(
        f'<p data-venture-industry="{g}"><strong>{escape(sec.INDUSTRY_GROUP[g])}</strong> {escape(", ".join(names))}</p>'
        for g, names in groups.items() if names) + _p(sec.INDUSTRY_TAIL)

    # 5 동업
    ranking = natal_balance(core)["ranking"]
    good_el = [e for e in ranking if tiers[e] == "good"]
    helper = _PEERS.get(_god_group(dm, good_el[0]), _god_group(dm, good_el[0])) if good_el else None
    if a["peers"] >= 2:
        partner = sec.PARTNER_RISK.format(n=a["peers"])
    elif a["strength"] == "weak":
        partner = sec.PARTNER_HELP
    else:
        partner = sec.PARTNER_PLAIN
    partner_html = _p(partner) + _p(sec.PARTNER_ROLE.get(helper, ""))

    # 6 · 7 대운
    cyc = bt.cycle_for_year(core, today.year) or {}
    cyc_group = _TEN_GOD_GROUP.get(cyc.get("ten_god"))
    capital = [sec.CAPITAL_BY_CYCLE.get(cyc_group, sec.CAPITAL_KEEP)]
    if a["rob"] >= 1:
        capital.append(sec.CAPITAL_RUN)
    if a["strength"] == "weak":
        capital.append(sec.CAPITAL_WEAK)
    cycle_html = ""
    if cyc:
        g = cyc["pillar"]["ganji"]
        cycle_html = (f'<h3>{escape(sec.CYCLE_HEAD.format(start=cyc["start_age"], end=cyc["end_age"], ganji_ko=_ko(g), ganji=g))}</h3>'
                      + _p(sec.CYCLE.get(cyc_group, "")) + _p(sec.CYCLE_TIER[tiers[GAN_WUXING[g[0]]]]))

    # 8 5년
    flow = bt.five_year_flow(core, today.year + (1 if today.month >= 10 else 0))   # 4분기에 보면 다음 해부터
    rows = []
    for r in flow:
        grades = " · ".join(f'{bt.EVENT_NAME[e]} {bt.GRADE_NAME[r["events"][e]["grade"]]}' for e in sec.EVENT_ORDER)
        # 원국 비겁(natal_peers)은 해마다 같은 말이라 해별 이유에서는 뺀다(동업 칸에서 이미 말함)
        note = next((txt for e in sec.EVENT_ORDER if r["events"][e]["grade"] != "normal"
                     for rule, txt in zip(r["events"][e]["rules"], r["events"][e]["reasons"]) if rule != "natal_peers"), "")
        rows.append(f'<li data-venture-year="{r["year"]}"><strong>{r["year"]}년 {escape(_ko(r["ganji"]))}({r["ganji"]})</strong>'
                    f'<br>{escape(grades)}' + (f"<br>{escape(note)}" if note else "") + "</li>")
    open_years = [r["year"] for r in flow if r["events"]["open"]["grade"] == "good"]
    years_html = (_p(sec.YEARS_LEAD) + '<ul style="padding-left:18px;display:grid;gap:6px;">' + "".join(rows) + "</ul>"
                  + _p(sec.YEARS_BEST_OPEN.format(years=_join_years(open_years)) if open_years else sec.YEARS_NO_OPEN))

    # 9 문 열기 좋은 달과 날
    good_m, bad_m = [], []
    for y, m in theme_timing.window_months(start):
        gz = calendar_ganji(date(y, m, 15))[1]
        grade = bt.judge_pillar(core, gz)["events"]["open"]["grade"]
        (good_m if grade == "good" else bad_m if grade == "caution" else []).append((y, m))
    label = lambda ym: f"{ym[0]}년 {ym[1]}월"
    open_parts = [sec.OPEN_LEAD]
    days = []
    if good_m:
        open_parts.append(sec.OPEN_MONTHS.format(months=", ".join(label(x) for x in good_m)))
        days = bt.pick_days(core, good_m[0][0], good_m[0][1], "open", 3)
        if days:
            open_parts.append(sec.OPEN_DAYS.format(month=label(good_m[0]),
                                                   days=", ".join(f'{int(d["date"][8:])}일({_ko(d["ganji"])})' for d in days)))
            open_parts.append(sec.OPEN_DAY_TAIL)
    else:
        open_parts.append(sec.OPEN_NONE)
    if bad_m:
        open_parts.append(sec.OPEN_AVOID.format(months=", ".join(label(x) for x in bad_m[:3])))
    open_html = "".join(_p(t) for t in open_parts)

    # 10 실천
    bullets = [sec.BULLET_TEST]
    if "many" in a["traps"]:
        bullets.append(sec.BULLET_ONE)
    if a["peers"] >= 2 or a["rob"] >= 1:
        bullets.append(sec.BULLET_PARTNER)
    if open_years:
        bullets.append(sec.BULLET_OPEN_YEAR.format(year=open_years[0]))
    elif cyc_group in ("officer", "resource"):
        bullets.append(sec.BULLET_KEEP)
    bullets.append(sec.BULLET_CASH)
    bullets = bullets[:4]

    html = "".join((
        _sec("kind", sec.TITLES["kind"], kind),
        _sec("industry", sec.TITLES["industry"], industry),
        _sec("partner", sec.TITLES["partner"], partner_html),
        _sec("capital", sec.TITLES["capital"], "".join(_p(t) for t in capital)),
        _sec("cycle", sec.TITLES["cycle"], cycle_html or _p(sec.CYCLE_TIER["ok"])),
        _sec("years", sec.TITLES["years"], years_html),
        _sec("open", sec.TITLES["open"], open_html),
        _sec("actions", sec.TITLES["actions"],
             "<ol>" + "".join(f'<li data-venture-action="{i}">{escape(b)}</li>' for i, b in enumerate(bullets, 1)) + "</ol>"),
    ))
    evidence = dict(
        kinds=[dict(nature=r["nature"], grade=r["grade"], rules=r["rules"]) for r in ranks],
        industries={g: v for g, v in groups.items()},
        cycle=cyc.get("pillar", {}).get("ganji"), cycle_group=cyc_group,
        years=[dict(year=r["year"], ganji=r["ganji"], events={e: r["events"][e]["grade"] for e in sec.EVENT_ORDER}) for r in flow],
        open_months=[f"{y}-{m:02d}" for y, m in good_m], open_days=[d["date"] for d in days],
    )
    return html, evidence


def build_venture_report(core: MyeongriCoreResult, user_name: str, *, is_unlocked: bool = False) -> dict:
    unlocked = is_unlocked is True
    name = user_name or "회원"
    a = _analyse(core)
    head, body = sec.NATURE[a["lead"]]
    nature_html = f"<h3>{escape(head)}</h3>" + _p(body.format(name=name)) + _p(sec.STRENGTH.get(a["strength"], ""))
    traps_html = '<div style="display:grid;gap:8px;">' + "".join(
        f'<div data-venture-trap="{i}" style="{_BOX}"><strong>{escape(t)}</strong>'
        f'<p style="margin:4px 0 0;">{escape(x)}</p><p style="margin:4px 0 0;">{escape(f)}</p></div>'
        for i, (t, x, f) in enumerate((sec.TRAPS[k] for k in a["traps"]), 1)) + "</div>"
    free = (_sec("nature", sec.TITLES["nature"], nature_html, "free")
            + _sec("traps", sec.TITLES["traps"], traps_html, "free")
            + '<hr data-paywall-boundary="venture" style="border:0;border-top:1px dashed #94A3B8;margin:18px 0;">')
    evidence_summary = dict(natal=dict(lead_group=a["lead"], strength=a["strength"], peers=a["peers"],
                                       ten_gods=a["counts"]), traps=a["traps"])
    if unlocked:
        gated, ev = _paid(core, name, a)
        evidence_summary["v1"] = ev
    else:
        titles = "".join(f'<li data-venture-locked="{k}"><span class="locked-num">{i:02d}</span> {escape(t)}</li>'
                         for i, (k, t) in enumerate(sec.LOCKED_SECTIONS, 3))
        gated = ('<section data-venture-tier="3" data-paywall="locked" data-locked="true" '
                 'style="border:1px dashed #94A3B8;border-radius:12px;background:#F8FAFC;padding:14px;margin-bottom:8px;">'
                 '<div style="font-size:12px;color:#64748B;font-weight:800;">🔒 잠긴 풀이</div>'
                 '<h2 style="margin:4px 0 0;">이어지는 풀이</h2>'
                 f'<p data-venture-teaser="3" style="margin:6px 0 0;">{escape(sec.LOCKED_TEASER)}</p>'
                 f'<ul data-locked-toc style="list-style:none;padding-left:0;margin:6px 0 0;">{titles}</ul>{_SKELETON}</section>'
                 '<a href="#paywall-theme-venture" data-paywall-cta="theme-venture" style="display:inline-block;margin-top:6px;'
                 'padding:10px 16px;border-radius:10px;background:#1D2129;color:#fff;font-weight:700;text-decoration:none;">'
                 f'{escape(sec.CTA)}</a>')
    c = a["counts"]
    evidence = ('<details class="reading-evidence"><summary>이 풀이의 근거 · 명리 용어 포함</summary><h4>사업의 구조</h4>'
                f'<p>원국 여덟 글자(천간 3 + 지지 본기 4) 기준 식상 {a["output"]}곳, 재성 {a["wealth"]}곳, '
                f'관성 {c.get("direct_officer", 0) + c.get("seven_killings", 0)}곳, '
                f'인성 {c.get("direct_resource", 0) + c.get("indirect_resource", 0)}곳, 비겁 {a["peers"]}곳(겁재 {a["rob"]}곳).</p>'
                '<p>일의 성격은 필요한 오행(행운 색과 같은 3단계 기준)·원국에 있는 별·강약으로, '
                '해마다의 흐름은 세운 천간의 십성과 원국 지지와의 충·형으로 판정했어요. 업종과 오행의 짝은 명리에서 널리 쓰는 관례예요.</p>'
                '</details>')
    content = (f'<div class="theme-reading" data-theme="venture" data-narrative-version="{VENTURE_NARRATIVE_VERSION}" '
               f'data-unlocked="{str(unlocked).lower()}">' + free + gated + evidence
               + f'<p class="reading-caption">{escape(sec.DISCLAIMER)}</p></div>')
    content = with_hashtags(content, core)
    return {"title": f"{escape(name)}님 정통 명리 사업운", "content": content,
            "narrative_version": VENTURE_NARRATIVE_VERSION, "is_unlocked": unlocked,
            "evidence_summary": evidence_summary}
