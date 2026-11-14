"""Lifetime wealth report backed by natal facts and every daeyun cycle."""

from __future__ import annotations

from collections import Counter
from html import escape

from app.engine.core.models import MyeongriCoreResult
from app.engine.services.applied_guidance import direction_advice, state_basis
from app.engine.semantic import build_service_query


_ELEMENT = {"木": "목", "火": "화", "土": "토", "金": "금", "水": "수"}
_CONTROLS = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}
_TEN_GOD = {
    "peer": "비견", "rob_wealth": "겁재", "eating_god": "식신",
    "hurting_officer": "상관", "direct_wealth": "정재",
    "indirect_wealth": "편재", "direct_officer": "정관",
    "seven_killings": "편관", "direct_resource": "정인",
    "indirect_resource": "편인",
}
_CYCLE_TOPIC = {
    "direct_wealth": "예산·계약·고정 수입처럼 관리 가능한 결과",
    "indirect_wealth": "거래·시장·새 기회처럼 변동성이 있는 자원",
    "eating_god": "꾸준히 만든 상품·서비스·기술을 결과로 연결하는 과정",
    "hurting_officer": "새로운 제안과 개선을 수익 구조로 시험하는 과정",
    "peer": "독립성과 공동 자원의 경계를 정하는 일",
    "rob_wealth": "경쟁·협업 속 비용과 각자 맡을 부분을 분명히 하는 일",
    "direct_officer": "책임·규정·계약 조건을 지키며 기반을 안정시키는 일",
    "seven_killings": "압박 속에서도 잃어도 되는 금액의 범위와 결정 순서를 지키는 일",
    "direct_resource": "학습·문서·자격을 미래 수입의 기반으로 쌓는 일",
    "indirect_resource": "새 정보와 아이디어를 작게 검증하는 일",
}
_PHASES = (
    ("초년기", 1, 2, "돈에 대한 습관과 자립의 기준을 배우는 구간"),
    ("청년기", 3, 4, "일과 수입의 방식을 구체화하고 시행착오를 자산으로 바꾸는 구간"),
    ("중장년기", 5, 6, "결과를 키우는 동시에 보유 자원과 책임을 재정비하는 구간"),
    ("말년기", 7, 9, "축적한 자원을 지키고 경험을 다음 역할로 연결하는 구간"),
)
_RELATION_CAUTION = {
    "branch_clash", "branch_punishment", "branch_harm", "branch_break", "stem_control",
}


def _natal_style(counts: Counter) -> tuple[str, str]:
    direct = counts["direct_wealth"]
    indirect = counts["indirect_wealth"]
    output = counts["eating_god"] + counts["hurting_officer"]
    if direct > indirect:
        style = "정재 쪽이 더 드러나므로 계획·예산·반복 가능한 수입 구조를 관리하는 방식이 기본축이 되기 쉽습니다."
    elif indirect > direct:
        style = "편재 쪽이 더 드러나므로 사람·거래·시장 변화에서 기회를 찾는 방식이 기본축이 되기 쉽습니다."
    elif direct or indirect:
        style = "정재와 편재가 함께 보여 안정적인 관리와 새로운 기회 탐색을 병행하는 구조입니다."
    else:
        style = "재성이 겉으로 강하게 드러난 구조는 아니어서, 돈 자체보다 기술·관계·역할을 먼저 만들고 수입으로 연결하는 과정이 중요합니다."
    output_text = (
        "식신·상관도 확인되어, 자신이 만든 상품·서비스·표현을 현실적인 결과로 연결하는 통로가 있습니다."
        if output else
        "생산과 표현의 통로가 자동으로 수익을 보장하지 않으므로, 결과물을 실제 거래와 반복 수입으로 연결하는 설계가 필요합니다."
    )
    return style, output_text


def _balance_advice(strength: str | None) -> str:
    if strength in {"weak", "extremely_weak"}:
        return "원국이 신약한 편에서는 기회 규모보다 감당할 체력·시간·현금흐름을 먼저 확인하는 것이 재물을 지키는 핵심입니다."
    if strength in {"strong", "extremely_strong"}:
        return "원국이 신강한 편에서는 생각과 추진력을 실제 상품·계약·결과로 내보낼 때 재물 흐름이 구체화되기 쉽습니다. 다만 확장 속도와 회수 계획을 함께 봐야 합니다."
    return "원국의 균형을 유지하려면 수입 확대와 안전장치를 함께 설계하고, 한쪽으로 지나치게 기울지 않도록 주기적으로 점검하는 편이 좋습니다."


def _cycle_card(cycle: dict, current_index: int | None) -> str:
    active = cycle.get("index") == current_index
    god = cycle["ten_god"]
    topic = _CYCLE_TOPIC.get(god, "현재 가진 자원과 역할을 다시 배치하는 일")
    changes = cycle.get("relationship_changes", [])
    caution_count = sum(item.get("type") in _RELATION_CAUTION for item in changes)
    caution = (
        "원국과의 충돌·조정 신호도 있어 큰 금액이나 장기 계약은 조건과 책임 범위를 한 번 더 확인하는 편이 좋습니다."
        if caution_count else
        "관계 변화만으로 길흉을 단정하지 말고 실제 수입·지출·계약 상태를 함께 확인하세요."
    )
    return f"""
    <div style="border:1px solid {'#6EE7B7' if active else '#E2E8F0'};background:{'#ECFDF5' if active else '#FFFFFF'};border-radius:10px;padding:10px;">
      <div style="font-size:13px;font-weight:800;color:#0F172A;">{cycle['start_age']}~{cycle['end_age']}세 · {cycle['pillar']['ganji']} · {_TEN_GOD.get(god, god)}{' · 현재' if active else ''}</div>
      <p style="font-size:12.5px;color:#475569;margin:5px 0 0;line-height:1.68;">이 시기에는 <strong>{topic}</strong>이 재물 관리의 중심이 됩니다. {caution}</p>
    </div>"""


def _phases_html(cycles: list[dict], current_index: int | None) -> str:
    groups = []
    for name, start, end, description in _PHASES:
        phase_cycles = [cycle for cycle in cycles if start <= cycle.get("index", 0) <= end]
        if not phase_cycles:
            continue
        active = current_index is not None and start <= current_index <= end
        ages = f'{phase_cycles[0]["start_age"]}~{phase_cycles[-1]["end_age"]}세'
        cards = "".join(_cycle_card(cycle, current_index) for cycle in phase_cycles)
        groups.append(f"""
        <details {'open' if active else ''} style="border:1px solid {'#FCD34D' if active else '#E2E8F0'};border-radius:13px;background:{'#FFFBEB' if active else '#F8FAFC'};padding:11px 12px;">
          <summary style="cursor:pointer;font-size:14px;font-weight:800;color:#0F172A;">{name} · {ages}{' · 현재 구간' if active else ''}</summary>
          <p style="font-size:12.5px;color:#64748B;margin:7px 0 9px;">{description}입니다.</p>
          <div style="display:grid;gap:7px;">{cards}</div>
        </details>""")
    return "".join(groups)


def _uncertainty(core: MyeongriCoreResult) -> str:
    if not core.uncertainty.time_unknown:
        return ""
    return """
    <div style="background:#FFF7ED;border:1px solid #FED7AA;padding:12px 14px;border-radius:12px;margin-top:12px;">
      <div style="font-size:13px;font-weight:800;color:#9A3412;">생시 미상 안내</div>
      <p style="font-size:12.5px;color:#7C2D12;margin:5px 0 0;line-height:1.65;">시주에 들어올 재성·식상과 일부 관계는 달라질 수 있으므로, 공통으로 유지되는 원국과 대운 흐름만 확정적으로 설명했습니다.</p>
    </div>"""


WEALTH_NARRATIVE_VERSION = "wealth-v3"   # 11/13: 돈 그릇·새는 습관 무료 + 유료 8칸(옛 공통 안내 걷어 냄)

_BOX = "border:1px solid #E2E8F0;border-radius:12px;padding:12px 14px;background:#FFFFFF;"
_SKELETON = (
    '<div data-locked-body="true" aria-hidden="true" style="filter:blur(3px);margin-top:8px;opacity:.55;">'
    '<span style="display:block;height:9px;margin:6px 0;border-radius:5px;background:#CBD5E1;"></span>'
    '<span style="display:block;height:9px;margin:6px 0;border-radius:5px;background:#CBD5E1;width:92%;"></span>'
    '<span style="display:block;height:9px;margin:6px 0;border-radius:5px;background:#CBD5E1;width:78%;"></span>'
    '</div>')
_POS = {"year_stem": "year", "year_branch": "year", "month_stem": "month", "month_branch": "month",
        "day_branch": "day", "hour_stem": "hour", "hour_branch": "hour"}
_WEALTH = ("direct_wealth", "indirect_wealth")
_OUTPUT = ("eating_god", "hurting_officer")
_PEERS = ("peer", "rob_wealth")
_RESOURCE = ("direct_resource", "indirect_resource")
_OFFICER = ("direct_officer", "seven_killings")


def _sec_html(key: str, title: str, body: str, paywall: str = "unlocked", tier: str | None = None) -> str:
    t = f' data-wealth-tier="{tier}"' if tier else ""
    return f'<section data-wealth-section="{key}"{t} data-paywall="{paywall}"><h2>{escape(title)}</h2>{body}</section>'


def _p(text: str, attr: str = "") -> str:
    return f"<p{attr}>{escape(text)}</p>" if text else ""


def _span(birth_year: int, a: int, b: int) -> str:
    return f"{a - birth_year + 1}세({a}년)" if a == b else f"{a - birth_year + 1}~{b - birth_year + 1}세({a}~{b}년)"


def _pick_line(pool, start, used):
    for i in range(len(pool)):
        line = pool[(start + i) % len(pool)]
        if line not in used:
            used.add(line)
            return line
    return ""


def _analyse(core: MyeongriCoreResult, query: dict) -> dict:
    from app.engine.services.theme_core import natal_counts, rob_heavy as _rob_heavy
    counts = natal_counts(core)
    n = {k: len(v) for k, v in counts.items()}
    tot = lambda gods: sum(n.get(g, 0) for g in gods)
    strength = query["synthesis"].get("strength_state")
    weak = strength in ("weak", "extremely_weak")
    strong = strength in ("strong", "extremely_strong")
    w, o, pe, r, of = tot(_WEALTH), tot(_OUTPUT), tot(_PEERS), tot(_RESOURCE), tot(_OFFICER)
    if w == 0:
        vessel = "none"
    elif w >= 3 and weak:
        vessel = "heavy"
    elif pe >= 3:
        vessel = "rival"
    elif o >= 1 and not weak:
        vessel = "output"
    elif strong and w <= 1:
        vessel = "strong"
    else:
        vessel = "even"
    d, i = n.get("direct_wealth", 0), n.get("indirect_wealth", 0)
    style = "both" if d and i and abs(d - i) <= 0 else ("direct" if d > i else "indirect" if i > d else "none")
    leak_score = {"share": pe if (pe >= 2 or n.get("rob_wealth", 0) >= 2) else 0, "spend": o if o >= 2 else 0,
                  "bigbet": i if i >= 2 else 0, "delay": r if r >= 2 else 0, "face": of if of >= 2 else 0,
                  "chase": w if (w >= 3 and weak) else 0}
    leaks = [k for k, v in sorted(leak_score.items(), key=lambda kv: -kv[1]) if v][:3]
    for extra in ("small", "spend", "share", "bigbet"):
        if len(leaks) >= 3:
            break
        if extra not in leaks:
            leaks.append(extra)
    positions = []
    for g in _WEALTH:
        for pos in counts.get(g, []):
            if _POS[pos] not in positions:
                positions.append(_POS[pos])
    positions.sort(key=("year", "month", "day", "hour").index)
    rob_heavy = _rob_heavy(counts)
    invest_rank = sorted((("indirect", i), ("direct", d), ("output", o), ("resource", r), ("officer", of), ("peer", pe)),
                         key=lambda kv: -kv[1])
    invest = [k for k, v in invest_rank if v and not (k == "output" and rob_heavy)][:2] or ["direct"]
    people = "rival" if (pe >= 3 or n.get("rob_wealth", 0) >= 2) else ("some" if pe else "alone")
    spouse = "day_branch" in counts.get("direct_wealth", []) + counts.get("indirect_wealth", [])
    return dict(counts=counts, n=n, strength=strength, rob_heavy=rob_heavy, weak=weak, strong=strong, vessel=vessel, style=style, leaks=leaks,
                positions=positions, invest=invest, people=people, spouse=spouse)


def _hidden_wealth(core) -> bool:
    from app.engine.facts.hidden_stems import get_hidden_stems
    from app.engine.facts.ten_gods import get_ten_god
    p = core.natal_facts.pillars
    dm = p["day"].stem
    for pos in ("year", "month", "day", "hour"):
        if p.get(pos) is None:
            continue
        for h in get_hidden_stems(p[pos].branch).stems[1:]:
            if getattr(get_ten_god(dm, h.stem), "value", "") in _WEALTH:
                return True
    return False


def _compose_paid(core: MyeongriCoreResult, query: dict, name: str, a: dict, seed: int, fixed_year: int | None) -> dict:
    from datetime import date
    from app.engine.calendar import to_solar
    from app.engine.constants import GAN_KO, ZHI_KO, GAN_WUXING
    from app.engine.facts.hidden_stems import get_hidden_stems
    from app.engine.facts.ten_gods import get_ten_god
    from app.engine.services import daily_score, theme_timing
    from app.engine.services import wealth_sections as sec
    from app.engine.services.daily_score import calendar_ganji
    from app.engine.services.element_balance import composition, element_tiers, natal_balance

    god = lambda stem: getattr(get_ten_god(dm, stem), "value", "")
    p = core.natal_facts.pillars
    dm = p["day"].stem
    birth = to_solar(core.input.birth_date, core.input.calendar_type, core.input.is_leap_month)
    this_year = theme_timing.window_start(core)[0]

    # 3 들어오는 길
    if a["positions"]:
        path = [sec.PATH[pos] for pos in a["positions"]]
    else:
        path = [sec.PATH_HIDDEN if _hidden_wealth(core) else sec.PATH_NONE]
    # 4 재테크
    invest = [sec.INVEST[k] for k in a["invest"]] + [sec.INVEST_ROB if a["rob_heavy"] else sec.INVEST_STRENGTH[
        "weak" if a["weak"] else "strong" if a["strong"] else "balanced"]]
    # 5 돈과 사람
    people = [sec.PEOPLE[a["people"]]] + ([sec.PEOPLE_SPOUSE] if a["spouse"] and "day" not in a["positions"] else [])

    # 6 지나온 재물 흐름
    # 일지 충은 배우자 자리라 애정운에서 읽는다(11/13 정오님 대조: 2000·2012·2024 辰년은 돈이 아니라 인연이 움직임).
    # 재물운의 '판이 바뀐 해'는 일·사회 자리(월지)와 일지 밖 재성 자리의 충으로 본다.
    wealth_branches = {p[k].branch for k in ("year", "month", "hour") if p.get(k) is not None
                       and getattr(get_ten_god(dm, get_hidden_stems(p[k].branch).stems[0].stem), "value", "") in _WEALTH}
    from app.engine.services.theme_core import CLASH as clash
    move_branches = {clash[b] for b in wealth_branches | {p["month"].branch}}
    ins, moves, outs = [], [], []
    # 제 돈을 벌기 시작하는 나이(세는 나이). 남자는 군 복무로 졸업·취업이 늦어 27세, 여자는 25세 (11/13 정오님)
    earn = 27 if getattr(core.input, "gender", "") == "male" else 25
    for y in range(birth.year + earn - 1, this_year):
        gz = calendar_ganji(date(y, 6, 15))[0]
        sg, bg = god(gz[0]), god(get_hidden_stems(gz[1]).stems[0].stem)
        if sg in _WEALTH or (sg in _OUTPUT and bg in _WEALTH):
            ins.append(y)
        if gz[1] in move_branches:
            moves.append(y)
        if sg == "rob_wealth":
            outs.append(y)
    periods = []
    for y in ins:
        if periods and y - periods[-1][1] <= 1:
            periods[-1][1] = y
        else:
            periods.append([y, y])
    p_in = (sec.PAST_FLOW, sec.PAST_FLOW_AGAIN) if a["rob_heavy"] else (sec.PAST_IN, sec.PAST_IN_AGAIN)
    dated = [(s0, p_in[0 if k == 0 else 1].format(span=_span(birth.year, s0, e0)))
             for k, (s0, e0) in enumerate(periods)]
    both = set(moves) & set(outs)
    dated += [(y, sec.PAST_MOVE_OUT.format(span=_span(birth.year, y, y))) for y in sorted(both)][:1]
    only_m, only_o = [y for y in moves if y not in both], [y for y in outs if y not in both]
    dated += [(y, sec.PAST_MOVE_AGAIN.format(span=_span(birth.year, y, y))) for y in sorted(both)][1:]
    dated += [(y, (sec.PAST_MOVE if k == 0 else sec.PAST_MOVE_AGAIN).format(span=_span(birth.year, y, y)))
              for k, y in enumerate(only_m)]
    dated += [(y, (sec.PAST_OUT if k == 0 else sec.PAST_OUT_AGAIN).format(span=_span(birth.year, y, y)))
              for k, y in enumerate(only_o)]
    dated.sort(key=lambda t: t[0])
    past = [t for _, t in dated]

    # 7 모이는 나이
    age, now_line, now_state, kinds, phases = [], "", "plain", [], []
    age_now = this_year - birth.year + 1
    for c in (core.timing.luck_cycle or {}).get("cycles", []):
        if c.get("start_age", 0) < earn - 5 or c.get("start_age", 0) > 77:
            continue                                     # 10년 중 절반 넘게 벌이 전(학생·군 복무)인 대운은 재물 시기로 읽지 않는다
        sg = god(c["pillar"]["stem"])
        state = (("flow" if a["rob_heavy"] else "gather") if sg in _WEALTH else "make" if (sg in _OUTPUT and not a["weak"])
                 else "leak" if (sg == "rob_wealth" or (sg == "peer" and not a["weak"]))
                 else "guard" if (a["rob_heavy"] and sg in _OFFICER) else "plain")
        span = f'{c["start_age"]}~{c["end_age"]}세'
        gz = GAN_KO.get(c["pillar"]["stem"], "") + ZHI_KO.get(c["pillar"]["branch"], "")
        if state != "plain":
            again = state in kinds
            tpl = {"gather": (sec.AGE_GATHER, sec.AGE_GATHER_AGAIN), "make": (sec.AGE_MAKE, sec.AGE_MAKE),
                   "leak": (sec.AGE_LEAK, sec.AGE_LEAK_AGAIN), "flow": (sec.AGE_FLOW, sec.AGE_FLOW_AGAIN),
                   "guard": (sec.AGE_GUARD, sec.AGE_GUARD_AGAIN)}[state][1 if again else 0]
            if not (state == "make" and again):
                age.append(tpl.format(span=span, ganji=gz))
            kinds.append(state)
        if state == "plain" and c["start_age"] > age_now and c["start_age"] <= 68:
            grp = ("officer" if sg in _OFFICER else "resource" if sg in _RESOURCE else "peer" if sg in _PEERS else None)
            if grp:
                age.append((sec.AGE_FUTURE_AGAIN if grp in kinds else sec.AGE_FUTURE)[grp].format(span=span, ganji=gz))
                kinds.append(grp)
        if state in ("gather", "make", "guard"):
            phases.append("early" if c["start_age"] < 38 else "middle" if c["start_age"] < 58 else "late")
        if c["start_age"] <= age_now <= c["end_age"]:
            now_state = state
            now_line = sec.AGE_NOW.format(span=span, state=sec.AGE_NOW_STATE[state])

    life = "even"
    if phases:
        top = max(("early", "middle", "late"), key=lambda k: (phases.count(k), k == "late"))
        life = top if phases.count(top) > len(phases) / 2 or len(set(phases)) == 1 else "even"
    life_line = sec.AGE_LIFE[life].format(name=name)

    # 7-3 집·문서와 큰돈
    res_n = a["n"].get("direct_resource", 0) + a["n"].get("indirect_resource", 0)
    land = _CONTROLS[GAN_WUXING[dm]] == "土"
    big = [sec.BIG_HOME["strong"] if res_n >= 2 else sec.BIG_LAND if land else sec.BIG_HOME["some" if res_n else "none"]]
    if a["rob_heavy"]:
        big = [x for x in big if x != sec.BIG_HOME["none"]] + [sec.BIG_LOCK]
    goods_y, docs_y, moves_y = [], [], []
    for y in range(this_year, this_year + 10):
        gz = calendar_ganji(date(y, 6, 15))[0]
        sg, bg = god(gz[0]), god(get_hidden_stems(gz[1]).stems[0].stem)
        if gz[1] in move_branches:
            moves_y.append(y)
        elif sg in _WEALTH or (sg in _OUTPUT and bg in _WEALTH):
            goods_y.append(y)
        elif sg in _RESOURCE:
            docs_y.append(y)
    yrs = lambda ys: "·".join(f"{y}년" for y in ys[:3])
    big.append(sec.BIG_YEARS_GOOD.format(years=yrs(goods_y)) if goods_y else sec.BIG_YEARS_NONE)
    if docs_y:
        big.append(sec.BIG_YEARS_DOC.format(years=yrs(docs_y)))
    if moves_y:
        big.append(sec.BIG_YEARS_MOVE.format(years=yrs(moves_y)))

    # 8 12개월
    start = (fixed_year, 1) if fixed_year else theme_timing.window_start(core)
    rows, prev, used = [], None, set()
    for y, m in theme_timing.window_months(start):
        target = date(y, m, 15)
        if target < birth:
            continue
        mg = calendar_ganji(target)[1]
        r = daily_score.evaluate(core, mg, target)
        h = r["domain_rules"]["금전"]
        grade = {"좋음": "good", "주의": "caution"}.get(h["tier"], "normal")
        reasons = h["good"] if grade == "good" else h["bad"] if grade == "caution" else []
        rows.append(dict(y=y, m=m, grade=grade, label=sec.GRADE_LABEL[grade], score=r["score"],
                         line=_pick_line(sec.MONTH_LINE[grade], seed + m, used), reason=reasons[0] if reasons else None,
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
                 text=" ".join(t for t in (sec.MONEY_REASON.get(r["reason"], ""), sec.MONEY_ADVICE.get(r["reason"], "")) if t))
            for r in picked if sec.MONEY_REASON.get(r["reason"])]

    # 9 개운
    tiers = element_tiers(core)["tiers"]
    comp = composition(core)
    ranking = natal_balance(core)["ranking"]
    good = [e for e in ranking if tiers[e] == "good"]
    we = _CONTROLS[GAN_WUXING[dm]]
    el = we if (tiers[we] == "good" or (tiers[we] == "ok" and comp[we] < 35)) else (good[0] if good else we)
    color = sec.COLOR[el]
    i = "이" if (ord(color[-1]) - 0xAC00) % 28 else "가"
    kaiun = [sec.KAIUN_LEAD, sec.KAIUN_COLOR.format(name=name, el=sec.ELEMENT_NAME[el], color=color, i=i), sec.KAIUN_HABIT]

    # 10 실천
    bullets = [sec.BULLET_VESSEL[a["vessel"]], sec.BULLET_AGE[now_state]]
    if goods:
        bullets.append(sec.BULLET_MONTH.format(month=f'{goods[0]["y"]}년 {goods[0]["m"]}월'))
    return dict(path=path, invest=invest, people=people, past=past, age=age, age_now=now_line, life=life_line, big=big, months=rows, keys=keys,
                month_caption=sec.MONTH_CAPTION.format(y=start[0], m=start[1]), kaiun=kaiun, bullets=bullets,
                evidence=dict(vessel=a["vessel"], rob_heavy=a["rob_heavy"], leaks=a["leaks"], positions=a["positions"], invest=a["invest"],
                              people=a["people"], ins=periods, moves=moves, outs=outs, now_state=now_state, kaiun_element=el, life=life, big_years=goods_y, doc_years=docs_y, move_years=moves_y,
                              months=[dict(month=f'{r["y"]}-{r["m"]:02d}', grade=r["grade"], reason=r["reason"]) for r in rows]))


def build_lifetime_wealth_report(core: MyeongriCoreResult, user_name: str, *, is_unlocked: bool = False,
                                 year: int | None = None) -> dict:
    """재물운 v3. is_unlocked 는 키워드 전용이며 `is True` 일 때만 유료 칸을 만든다(직업·애정·건강과 같은 원칙)."""
    from app.engine.calendar import to_solar
    from app.engine.services.annual_copy import seed_from
    from app.engine.services import wealth_sections as sec

    unlocked = is_unlocked is True
    query = build_service_query(core, "lifetime_wealth")
    name = user_name or "회원"
    a = _analyse(core, query)
    birth = to_solar(core.input.birth_date, core.input.calendar_type, core.input.is_leap_month)
    seed = seed_from(birth.isoformat(), "wealth", year or 0)

    head, body = sec.VESSEL[a["vessel"]]
    vessel_html = f"<h3>{escape(head)}</h3>" + _p(body.format(name=name)) + _p(sec.STYLE[a["style"]])
    if a["rob_heavy"] and a["vessel"] != "rival":
        vessel_html += _p(sec.VESSEL_ROB)
    leaks_html = '<div style="display:grid;gap:8px;">' + "".join(
        f'<div data-wealth-trap="{k}" style="{_BOX}"><strong>{escape(t)}</strong>'
        f'<p style="margin:4px 0 0;">{escape(x)}</p><p data-wealth-trap-fix="{k}" style="margin:4px 0 0;">{escape(f)}</p></div>'
        for k, (t, x, f) in ((k, sec.LEAK[k]) for k in a["leaks"])) + "</div>"
    free = (_sec_html("vessel", "타고난 돈 그릇", vessel_html, "free", "1")
            + _sec_html("leaks", f"돈이 새는 습관 {len(a['leaks'])}가지", leaks_html, "free", "2")
            + '<hr data-paywall-boundary="wealth" style="border:0;border-top:1px dashed #94A3B8;margin:18px 0;">')
    evidence_summary = dict(natal=dict(vessel=a["vessel"], strength=a["strength"], ten_gods=a["n"]),
                            copy_ids=dict(tier1=a["vessel"], tier2=a["leaks"]))
    if unlocked:
        d = _compose_paid(core, query, name, a, seed, year)
        rows = "".join(
            f'<li data-wealth-month="{m["y"]}-{m["m"]:02d}" data-month-grade="{m["grade"]}">'
            f'<strong>{escape(m["display"])} · {escape(m["label"])}</strong> {escape(m["line"])}</li>' for m in d["months"])
        keys = "".join(
            f'<div data-wealth-key-month="{k["y"]}-{k["m"]:02d}" style="{_BOX}"><strong>{escape(k["display"])} · {escape(k["label"])}</strong>'
            f'<p style="margin:4px 0 0;">{escape(k["text"])}</p></div>' for k in d["keys"])
        lst = lambda key, items: "<ul>" + "".join(f'<li data-wealth-{key}="{i}">{escape(t)}</li>' for i, t in enumerate(items, 1)) + "</ul>"
        gated = "".join((
            _sec_html("path", sec.PATH_HEADING, _p(sec.PATH_LEAD) + "".join(_p(t) for t in d["path"])),
            _sec_html("invest", sec.INVEST_HEADING, "".join(_p(t) for t in d["invest"])),
            _sec_html("people", sec.PEOPLE_HEADING, "".join(_p(t) for t in d["people"])),
            _sec_html("past", sec.PAST_HEADING, (_p(sec.PAST_INTRO.format(name=name)) + lst("past", d["past"])) if d["past"] else _p(sec.PAST_NONE)),
            _sec_html("age", sec.AGE_HEADING, _p(sec.AGE_LEAD) + (lst("age", d["age"]) if d["age"] else "") + _p(d["age_now"]) + _p(d["life"])),
            _sec_html("big", sec.BIG_HEADING, "".join(_p(t) for t in d["big"])),
            _sec_html("months", "앞으로 12개월 금전 흐름", f'<p class="reading-caption">{escape(d["month_caption"])}</p>'
                      f'<ul style="padding-left:18px;">{rows}</ul>'
                      + (f'<h3>눈여겨볼 달</h3><div style="display:grid;gap:8px;">{keys}</div>' if keys else _p(sec.NO_KEY_MONTH)), tier="3"),
            _sec_html("kaiun", sec.KAIUN_HEADING, "".join(_p(t) for t in d["kaiun"])),
            _sec_html("actions", "재물을 지키는 실천",
                      "<ol>" + "".join(f'<li data-wealth-action="{i}">{escape(b)}</li>' for i, b in enumerate(d["bullets"], 1)) + "</ol>", tier="4"),
        ))
        evidence_summary["months"] = d["evidence"]["months"]
        evidence_summary["v3"] = {k: v for k, v in d["evidence"].items() if k != "months"}
    else:
        # 11/14: 잠긴 목록도 풀이 안 번호(01·02 무료 칸 다음 03부터)와 같게 매긴다.
        titles = "".join(f'<li data-wealth-locked="{k}"><span class="locked-num">{i:02d}</span> {escape(t)}</li>' for i, (k, t) in enumerate(sec.LOCKED_SECTIONS, 3))
        gated = ('<section data-wealth-tier="3" data-paywall="locked" data-locked="true" '
                 'style="border:1px dashed #94A3B8;border-radius:12px;background:#F8FAFC;padding:14px;margin-bottom:8px;">'
                 '<div style="font-size:12px;color:#64748B;font-weight:800;">🔒 잠긴 풀이</div>'
                 '<h2 style="margin:4px 0 0;">이어지는 풀이</h2>'
                 f'<p data-wealth-teaser="3" style="margin:6px 0 0;">{escape(sec.LOCKED_TEASER)}</p>'
                 f'<ul data-locked-toc style="list-style:none;padding-left:0;margin:6px 0 0;">{titles}</ul>{_SKELETON}</section>'
                 '<a href="#paywall-theme-wealth" data-paywall-cta="theme-wealth" style="display:inline-block;margin-top:6px;'
                 'padding:10px 16px;border-radius:10px;background:#2D6A4F;color:#fff;font-weight:700;text-decoration:none;">'
                 f'{escape(sec.CTA)}</a>')
    day = query["natal"]["day_master"]
    counts = a["n"]
    evidence = ('<details class="reading-evidence"><summary>이 풀이의 근거 · 명리 용어 포함</summary><h4>평생 재물 구조</h4>'
                f'<p>일간 {day["stem"]}({_ELEMENT[day["element"]]}) · 재성 {_ELEMENT[_CONTROLS[day["element"]]]}. '
                f'원국 여덟 글자(천간 3 + 지지 본기 4) 기준 정재 {counts.get("direct_wealth", 0)}곳, 편재 {counts.get("indirect_wealth", 0)}곳, '
                f'식상 {counts.get("eating_god", 0) + counts.get("hurting_officer", 0)}곳, 비겁 {counts.get("peer", 0) + counts.get("rob_wealth", 0)}곳. '
                '이 개수는 재산의 크기가 아니라 재물 주제가 드러난 위치의 수입니다.</p>'
                f'<p>{escape(direction_advice(query["applied_state"], "wealth", _balance_advice(a["strength"])))}</p></details>')
    content = (f'<div class="theme-reading" data-theme="wealth" data-narrative-version="{WEALTH_NARRATIVE_VERSION}" '
               f'data-unlocked="{str(unlocked).lower()}">' + free + gated + evidence + _uncertainty(core)
               + f'<p class="reading-caption">{escape(sec.DISCLAIMER)}</p></div>')
    return {"analysis_basis": state_basis(query["applied_state"]), "title": f"{escape(name)}님 정통 명리 평생 재물운",
            "content": content, "narrative_version": WEALTH_NARRATIVE_VERSION, "is_unlocked": unlocked,
            "evidence_summary": evidence_summary}
