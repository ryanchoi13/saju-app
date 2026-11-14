"""일·커리어 테마운 (4단 구조 · 2,900원 페이월).

1단 기질 진단 · 2단 결정적 경고 → 무료
3단 타이밍 · 4단 실천 3원칙   → is_unlocked=True 일 때만 본문을 만든다.

보안 원칙
- 잠금 상태에서는 3·4단의 '본문'을 HTML, evidence_summary, 반환 dict 어디에도 싣지 않는다.
  (블러는 화면 효과일 뿐이라 본문이 들어 있으면 개발자도구로 보인다.)
- 잠금 상태에서는 3단 계산(월별 엔진 호출)도 하지 않는다. 그래서 티저에는 '몇 곳'이라는 숫자를 쓰지 않는다.
- is_unlocked 는 반드시 서버가 결제 내역에서 계산해 넘겨야 한다. 요청 파라미터를 그대로 넘기지 말 것.
"""

from __future__ import annotations

from collections import Counter
from datetime import date
from html import escape

from app.engine.core.models import MyeongriCoreResult
from app.engine.calendar import to_solar
from app.engine.semantic import build_service_query
from app.engine.semantic.queries import profile_ten_gods
from app.engine.services.applied_guidance import direction_advice, state_basis
from app.engine.services.annual_copy import sanitize_paragraph, seed_from
from app.engine.services import career_copy as copy
from app.engine.services import theme_timing
from app.engine.services import career_sections as sec
from app.engine.services.theme_core import CLASH, YEOKMA, hidden_tally, tally
from app.engine.services import daily_score
from app.engine.services.daily_score import _god_group, calendar_ganji
from app.engine.services.element_balance import composition, element_tiers, natal_balance
from app.engine.constants import GAN_KO, GAN_WUXING, ZHI_KO
from app.engine.facts.ten_gods import get_ten_god

CAREER_NARRATIVE_VERSION = "career-v3"  # 11/13: 칸 10개 · 분량 3배 · 12달 등급

_TEN_GOD = {
    "peer": "비견", "rob_wealth": "겁재", "eating_god": "식신",
    "hurting_officer": "상관", "direct_wealth": "정재",
    "indirect_wealth": "편재", "direct_officer": "정관",
    "seven_killings": "편관", "direct_resource": "정인",
    "indirect_resource": "편인",
}
# 월별 흐름에서 '일' 신호로 읽을 도메인. 직장·이직은 일과 배움, 사업·창업은 일과 돈.
# (도메인 → 테마 매핑과 같은 결의 가정이며, 엔진의 실제 의미와 다르면 여기를 고친다.)
# 대운 주제 문구. reading_editorial.cycle_focus 가 이 이름으로 임포트한다(삭제 금지).
_CYCLE_TOPIC = {
    "direct_officer": "공식 역할·책임·평가 기준을 안정적으로 관리하는 일",
    "seven_killings": "압박과 변화 속에서 우선순위를 정하고 결정하는 일",
    "direct_wealth": "예산·계약·일정처럼 확인할 수 있는 결과를 관리하는 일",
    "indirect_wealth": "고객·시장·거래 기회를 살피고 활동 범위를 조절하는 일",
    "eating_god": "상품·서비스·기술을 꾸준한 결과물로 만드는 일",
    "hurting_officer": "기존 방식을 개선하고 제안을 설득력 있게 전달하는 일",
    "peer": "독립적인 전문성과 협업 역할의 경계를 정하는 일",
    "rob_wealth": "경쟁·협업 속 권한·비용·역할을 나누는 기준을 분명히 하는 일",
    "direct_resource": "학습·문서·자격을 실제 업무 기반으로 축적하는 일",
    "indirect_resource": "새 관점과 정보를 작게 시험해 업무 방식으로 정착시키는 일",
}

_ELEMENT_KO = {"木": "목", "火": "화", "土": "토", "金": "금", "水": "수"}
_TIER_KO = {"good": "좋음", "ok": "무난", "avoid": "피함"}
_GROUP_KO = {"peer": "비겁", "output": "식상", "wealth": "재성", "officer": "관성", "resource": "인성"}

_TRACK_DOMAINS = {"career": ("work", "learning"), "business": ("work", "money")}


def _clean(text: str, where: str) -> str:
    return sanitize_paragraph(text, fallback="", where=where)


def _count_summary(counts: Counter, track: str) -> str:
    output = counts["eating_god"] + counts["hurting_officer"]
    wealth = counts["direct_wealth"] + counts["indirect_wealth"]
    if track == "business":
        peers = counts["peer"] + counts["rob_wealth"]
        return f"식신·상관 {output}곳, 정재·편재 {wealth}곳, 비견·겁재 {peers}곳"
    officer = counts["direct_officer"] + counts["seven_killings"]
    return f"정관·편관 {officer}곳, 식신·상관 {output}곳, 정재·편재 {wealth}곳"


def _uncertainty(core: MyeongriCoreResult) -> str:
    if not core.uncertainty.time_unknown:
        return ""
    return """
    <div style="background:#FFF7ED;border:1px solid #FED7AA;padding:12px 14px;border-radius:12px;margin-top:12px;">
      <div style="font-size:13px;font-weight:800;color:#9A3412;">생시 미상 안내</div>
      <p style="font-size:12.5px;color:#7C2D12;margin:5px 0 0;line-height:1.65;">시주에 따라 일부 십성과 관계 구조가 달라질 수 있어, 여러 시주에서 공통으로 유지되는 원국과 흐름을 중심으로 설명했습니다.</p>
    </div>"""


# ---------------------------------------------------------------------------
# 3단 계산: 월별 흐름 점수 (유료 전용)
#   점수는 '그 달 일 도메인의 mode'를 MODE_SCORE 로 옮긴 것이다.
#   join(합·결속) +2 · recovery +1 · base 0 · mixed -1 · change(충·변동) -2.
#   mode 이름만 보고 정한 해석이라, 실제 엔진 의미와 맞는지 확인이 필요하다.
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# HTML 조각
# ---------------------------------------------------------------------------
_BOX = "border:1px solid #E2E8F0;border-radius:12px;padding:12px 14px;background:#FFFFFF;"
_SKELETON = (
    '<div data-locked-body="true" aria-hidden="true" style="filter:blur(3px);margin-top:8px;opacity:.55;">'
    '<span style="display:block;height:9px;margin:6px 0;border-radius:5px;background:#CBD5E1;"></span>'
    '<span style="display:block;height:9px;margin:6px 0;border-radius:5px;background:#CBD5E1;width:92%;"></span>'
    '<span style="display:block;height:9px;margin:6px 0;border-radius:5px;background:#CBD5E1;width:78%;"></span>'
    '</div>'
)


def _section(key: str, title: str, body: str, paywall: str = "unlocked", tier: int | None = None) -> str:
    tier_attr = f' data-career-tier="{tier}"' if tier else ""
    return (f'<section data-career-section="{key}"{tier_attr} data-paywall="{paywall}">'
            f'<h2>{escape(title)}</h2>{body}</section>')


def _p(text: str, attr: str = "") -> str:
    return f'<p{attr}>{escape(text)}</p>' if text else ""


def _tier1_html(t1: dict, stem_text: str) -> str:
    return _section("nature", "일하는 기질",
                    f'<h3>{escape(t1["headline"])}</h3>{_p(t1["body"])}{_p(stem_text)}', "free", 1)


def _tier2_html(boxes: list[dict]) -> str:
    items = "".join(
        f'<div data-career-trap="{i}" style="{_BOX}">'
        f'<strong>{escape(b["title"])}</strong><p style="margin:4px 0 0;">{escape(b["text"])}</p>'
        f'<p data-career-trap-fix="{i}" style="margin:4px 0 0;">{escape(b["fix"])}</p></div>'
        for i, b in enumerate(boxes, start=1))
    return _section("traps", f"일할 때 빠지기 쉬운 함정 {len(boxes)}가지",
                    f'<div style="display:grid;gap:8px;">{items}</div>', "free", 2)


def _boundary_html() -> str:
    return '<hr data-paywall-boundary="career" style="border:0;border-top:1px dashed #94A3B8;margin:18px 0;">'


def _locked_html() -> str:
    # 11/14: 잠긴 목록도 풀이 안 번호(01·02 무료 칸 다음 03부터)와 같게 매긴다.
    titles = "".join(f'<li data-career-locked="{k}"><span class="locked-num">{i:02d}</span> {escape(t)}</li>' for i, (k, t) in enumerate(sec.LOCKED_SECTIONS, 3))
    return (
        '<section data-career-tier="3" data-paywall="locked" data-locked="true" '
        'style="border:1px dashed #94A3B8;border-radius:12px;background:#F8FAFC;padding:14px;margin-bottom:8px;">'
        f'<div style="font-size:12px;color:#64748B;font-weight:800;">🔒 {escape(copy.LOCK_LABEL)}</div>'
        f'<h2 style="margin:4px 0 0;">이어지는 풀이</h2>'
        f'<p data-career-teaser="3" style="margin:6px 0 0;">{escape(sec.LOCKED_TEASER)}</p>'
        f'<ul data-locked-toc style="list-style:none;padding-left:0;margin:6px 0 0;">{titles}</ul>{_SKELETON}</section>'
        f'<a href="{copy.PAYWALL_HREF}" data-paywall-cta="theme-career" style="display:inline-block;margin-top:6px;'
        'padding:10px 16px;border-radius:10px;background:#2D6A4F;color:#fff;font-weight:700;text-decoration:none;">'
        f'{escape(copy.cta_label())}</a>')


def _pair(items: list[tuple[str, str, str]]) -> str:
    return "".join(
        f'<div data-career-{attr} style="{_BOX}"><strong>{escape(t)}</strong><p style="margin:4px 0 0;">{escape(x)}</p></div>'
        for attr, t, x in items)


def _unlocked_html(d: dict) -> str:
    out = [
        _section("workplace", "나에게 맞는 일터", _p(d["workplace"]) + _p(d["workplace_strength"])),
        _section("jobs", "잘 맞는 일의 종류", _p(d["job_kind"]) + _p(d["fields"])),
        _section("money", "돈을 버는 방식",
                 f'<h3>{escape(d["money_title"])}</h3>' + _p(d["money"]) + _p(d["money_tail"])),
        _section("people", "함께 일하는 사람",
                 f'<div style="display:grid;gap:8px;">'
                 + _pair([("helper", sec.HELPER_TITLE, d["helper"]), ("hard", sec.HARD_TITLE, d["hard"])])
                 + '</div>'),
        _section("cycle", "이번 10년의 일",
                 f'<h3>{escape(d["cycle_head"])}</h3>' + _p(d["cycle"]) + _p(d["cycle_tier"]) + _p(d["cycle_next"]))
        if d["cycle"] else "",
    ]
    months = d["months"]
    rows = "".join(
        f'<li data-career-month="{m["y"]}-{m["m"]:02d}" data-month-grade="{m["grade"]}">'
        f'<strong>{escape(m["display"])} · {escape(m["label"])}</strong> {escape(m["line"])}</li>'
        for m in months)
    keys = "".join(
        f'<div data-career-key-month="{k["y"]}-{k["m"]:02d}" style="{_BOX}">'
        f'<strong>{escape(k["display"])} · {escape(k["label"])}</strong>'
        f'<p style="margin:4px 0 0;">{escape(k["text"])}</p></div>'
        for k in d["key_months"])
    keys_html = (f'<h3>눈여겨볼 달</h3><div style="display:grid;gap:8px;">{keys}</div>' if keys
                 else _p(sec.NO_KEY_MONTH, ' data-career-key-month="none"'))
    year_html = (f'<h3>{escape(d["year_head"])}</h3>' + _p(d["year"])) if d["year"] else ""
    out.append(_section("months", "앞으로 12개월 일의 흐름",
                        f'<p class="reading-caption">{escape(d["month_caption"])}</p>' + year_html
                        + f'<h3>달별 흐름</h3><ul style="padding-left:18px;">{rows}</ul>' + keys_html))
    out.append(_section("move", "자리가 움직이는 달", _p(d["move"])))
    items = "".join(f'<li data-career-action="{i}">{escape(b)}</li>' for i, b in enumerate(d["bullets"], start=1))
    out.append(_section("actions", "일을 지키는 실천", f'<ol>{items}</ol>'))
    return "".join(out)


# ---------------------------------------------------------------------------
# v3 계산 (유료 칸). 잠금 상태에서는 부르지 않는다.
# ---------------------------------------------------------------------------
_GROUP5 = {"peer": "peer", "rob_wealth": "peer", "eating_god": "output", "hurting_officer": "output",
           "direct_wealth": "wealth", "indirect_wealth": "wealth", "direct_officer": "officer",
           "seven_killings": "officer", "direct_resource": "resource", "indirect_resource": "resource"}


def _god_value(day_master: str, stem: str) -> str:
    god = get_ten_god(day_master, stem)
    return getattr(god, "value", str(god))


def _people(core: MyeongriCoreResult, tiers: dict, ranking: list[str]) -> tuple[str, str]:
    dm = core.natal_facts.pillars["day"].stem
    good = [e for e in ranking if tiers[e] == "good"]
    avoid = [e for e in reversed(ranking) if tiers[e] == "avoid"]
    helper = _god_group(dm, good[0]) if good else _god_group(dm, ranking[0])
    if avoid:
        hard = _god_group(dm, avoid[0])
    else:
        share = composition(core)
        hard = _god_group(dm, max(share, key=share.get))
    if hard == helper:
        hard = next(_god_group(dm, e) for e in reversed(ranking) if _god_group(dm, e) != helper)
    return helper, hard


def _pick_line(pool: tuple, start: int, used: set) -> str:
    """같은 문장이 12달 목록에 두 번 나오지 않게, 아직 안 쓴 변형부터 고른다(다 썼으면 처음 자리)."""
    for i in range(len(pool)):
        line = pool[(start + i) % len(pool)]
        if line not in used:
            used.add(line)
            return line
    return pool[start % len(pool)]


def _months(core: MyeongriCoreResult, seed: int, start: tuple[int, int] | None = None) -> tuple[list[dict], list[dict], list[dict], dict]:
    """12달 등급·한 줄, 핵심 달, 움직이는 달, 세운. 등급은 오늘의 운세 '일' 분야 규칙표(월주에 적용)."""
    pillars = core.natal_facts.pillars
    dm = pillars["day"].stem
    birth = to_solar(core.input.birth_date, core.input.calendar_type, core.input.is_leap_month)
    move_branches = {YEOKMA[pillars["year"].branch]: "yeokma", YEOKMA[pillars["day"].branch]: "yeokma",
                     CLASH[pillars["month"].branch]: "clash"}
    rows, prev, used = [], None, set()
    for y, m in theme_timing.window_months(start or theme_timing.window_start(core)):
        target = date(y, m, 15)
        if target < birth:
            continue
        year_gz, month_gz, _ = calendar_ganji(target)
        r = daily_score.evaluate(core, month_gz, target)
        work = r["domain_rules"]["일"]
        grade = sec.TIER_TO_GRADE.get(work["tier"], "normal")
        group = _god_group(dm, GAN_WUXING[month_gz[0]])
        line = _pick_line(sec.MONTH_LINE[group][grade], seed + m, used)
        reasons = work["good"] if grade == "good" else work["bad"] if grade == "caution" else []
        rows.append(dict(y=y, m=m, ganji=month_gz, year_ganji=year_gz, grade=grade,
                         label=sec.GRADE_LABEL[grade], line=line, score=r["score"],
                         reason=reasons[0] if reasons else None,
                         move=move_branches.get(month_gz[1]),
                         display=theme_timing.month_label(y, m, prev)))
        prev = y

    goods = sorted((r for r in rows if r["grade"] == "good"), key=lambda r: -r["score"])
    bads = sorted((r for r in rows if r["grade"] == "caution"), key=lambda r: r["score"])
    picked = ([goods.pop(0)] if goods else []) + ([bads.pop(0)] if bads else [])
    # 셋째 달은 앞의 달과 이유가 다른 달만 고른다(같은 이유·같은 처방 문장이 두 번 나오지 않게)
    for r in sorted(goods + bads, key=lambda r: -abs(r["score"] - 75)):
        if len(picked) >= 3:
            break
        if r["reason"] not in {x["reason"] for x in picked}:
            picked.append(r)
    picked.sort(key=lambda r: (r["y"], r["m"]))
    keys = []
    for r in picked:
        reason = sec.WORK_REASON.get(r["reason"], "")
        advice = sec.WORK_ADVICE.get(r["reason"], "")
        keys.append(dict(y=r["y"], m=r["m"], display=f'{r["y"]}년 {r["m"]}월', label=r["label"],
                         text=" ".join(t for t in (reason, advice) if t), basis=r["reason"]))   # 달 한 줄은 위 목록에 있으니 되풀이하지 않는다

    moves = [r for r in rows if r["move"]]
    count = Counter(r["year_ganji"] for r in rows)
    year_gz = max(count, key=lambda g: (count[g], [r["year_ganji"] for r in rows].index(g))) if rows else None
    year_num = Counter(r["y"] for r in rows if r["year_ganji"] == year_gz).most_common(1)[0][0] if year_gz else None
    year_move = move_branches.get(year_gz[1]) if year_gz else None
    return rows, keys, moves, dict(ganji=year_gz, year=year_num, move=year_move)


def _compose_v3(core: MyeongriCoreResult, query: dict, name: str, group: str, track: str,
                strength: str | None, status: str, counts: Counter, seed: int, year: int | None = None) -> dict:
    start = (year, 1) if year else theme_timing.window_start(core)   # year 를 주면(옛 호출·테스트) 그해 1~12월
    dm = core.natal_facts.pillars["day"].stem
    info = element_tiers(core)
    tiers = info["tiers"]
    ranking = natal_balance(core)["ranking"]
    good = [e for e in ranking if tiers[e] == "good"][:2]
    helper, hard = _people(core, tiers, ranking)
    money = sec.money_type(counts, hidden_tally(core, profile_ten_gods(track)))

    timing = query["timing"]["luck_cycles"]
    current = timing.get("current") or {}
    god = current.get("ten_god")
    cycle = sec.CYCLE.get(god, {}).get(track, "")
    cycle_head, cycle_tier, cycle_next = "", "", ""
    if cycle:
        stem = current["pillar"]["stem"]
        cycle_head = (f'{current["start_age"]}~{current["end_age"]}세 · '
                      f'{GAN_KO.get(stem, "")}{ZHI_KO.get(current["pillar"]["branch"], "")}({current["pillar"]["ganji"]}) 대운')
        cycle_tier = sec.CYCLE_TIER[tiers[GAN_WUXING[stem]]]
        nxt = next((c for c in timing.get("cycles", []) if c.get("index") == current.get("index", -9) + 1), None)
        if nxt and nxt.get("ten_god") in sec.NEXT_SHORT:
            cycle_next = sec.NEXT_LINE.format(age=nxt["start_age"], ganji=nxt["pillar"]["ganji"],
                                              ganji_ko=GAN_KO.get(nxt["pillar"]["ganji"][0], "") + ZHI_KO.get(nxt["pillar"]["ganji"][1], ""),
                                              short=sec.NEXT_SHORT[nxt["ten_god"]])

    rows, keys, moves, year = _months(core, seed, start)
    year_text, year_head = "", ""
    if year["ganji"]:
        year_text = sec.YEAR.get(_god_value(dm, year["ganji"][0]), "")
        year_head = sec.YEAR_HEAD.format(year=year["year"], ganji_ko=GAN_KO.get(year["ganji"][0], "") + ZHI_KO.get(year["ganji"][1], ""))

    has_move, no_move = sec.MOVE_STATUS.get(status, sec.MOVE_STATUS[copy.DEFAULT_STATUS])
    if moves:
        listed = ", ".join(f'{r["y"]}년 {r["m"]}월({sec.MOVE_CAUSE[r["move"]]})' for r in moves)
        year_line = sec.MOVE_YEAR[year["move"]].format(year=year["year"]) if year.get("move") else ""
        move = " ".join(t for t in (sec.MOVE_HEAD.format(months=listed), sec.MOVE_WHY, year_line, has_move) if t)
    else:
        move = " ".join((sec.MOVE_NONE, no_move))

    # 11/13: 줄기 원칙(career_copy.GROUP_BULLETS)은 함정 칸의 대처와 겹쳐서 뺐다
    year_god = _god_value(dm, year["ganji"][0]) if year["ganji"] else None
    bullets = [sec.HELPER_BULLET[helper]]
    if god in sec.CYCLE_BULLET:
        bullets.append(sec.CYCLE_BULLET[god])
    if year_god in sec.YEAR_BULLET and year_god != god:
        bullets.append(sec.YEAR_BULLET[year_god])
    bullets.append(copy.STATUS_BULLET.get(status, copy.STATUS_BULLET[copy.DEFAULT_STATUS]))

    return dict(
        workplace=sec.WORKPLACE[group][track], workplace_strength=sec.WORKPLACE_STRENGTH[copy.strength_key(strength)],
        job_kind=sec.JOB_KIND[group], fields=sec.field_text(name, good),
        money_title=sec.MONEY_TITLE[money], money=sec.MONEY_TEXT[money], money_tail=sec.MONEY_TAIL[(money, track)],
        helper=sec.HELPER[helper], hard=sec.HARD[hard],
        cycle=cycle, cycle_head=cycle_head, cycle_tier=cycle_tier, cycle_next=cycle_next,
        year=year_text, year_head=year_head,
        month_caption=sec.MONTH_CAPTION.format(y=start[0], m=start[1]),
        months=rows, key_months=keys, move=move, bullets=bullets,
        evidence=dict(good_elements=good, tiers=tiers, helper=helper, hard=hard, money=money,
                      cycle=current.get("pillar", {}).get("ganji"), cycle_god=god, year=year,
                      months=[dict(month=f'{r["y"]}-{r["m"]:02d}', ganji=r["ganji"], grade=r["grade"],
                                   reason=r["reason"], move=r["move"]) for r in rows],
                      key_months=[k["basis"] for k in keys]),
    )


def build_lifetime_career_report(
    core: MyeongriCoreResult,
    user_name: str,
    status: str = copy.DEFAULT_STATUS,
    *,
    is_unlocked: bool = False,
    year: int | None = None,
) -> dict:
    """Render career/business guidance without deterministic success claims.

    is_unlocked 는 키워드 전용이다. 옛 호출부가 status 를 세 번째 위치 인자로 넘기므로,
    위치 인자로 두면 문자열 status 가 참값으로 읽혀 전부 잠금 해제되는 사고가 난다.
    또한 `is True` 로만 비교하므로 "1", "yes" 같은 값으로는 열리지 않는다.
    """
    unlocked = is_unlocked is True
    safe_status = status if status in copy.STATUS_TRACK else copy.DEFAULT_STATUS
    track = copy.track_of(safe_status)
    query = build_service_query(core, track)
    name = escape(user_name or "회원")
    fixed_year = year
    year = year or theme_timing.window_start(core)[0]

    counts = tally(core, profile_ten_gods(track))   # 공용 엔진: 여덟 글자 본기만, 이 테마가 보는 별만
    strength = query["synthesis"].get("strength_state")
    group = copy.lead_group(counts, hidden_tally(core, profile_ten_gods(track)))
    birth = to_solar(core.input.birth_date, core.input.calendar_type, core.input.is_leap_month)
    seed = seed_from(birth.isoformat(), "career", safe_status, year)

    t1 = copy.compose_tier1(group, track, strength)
    stem_text = sec.STEM_WORK.get(core.natal_facts.pillars["day"].stem, "")
    pool = copy.TRAPS[group if group in copy.TRAPS else "balanced"]
    first = seed % len(pool)
    t2 = [dict(title=pool[(first + i) % len(pool)][0], text=pool[(first + i) % len(pool)][1],
               fix=sec.TRAP_FIX[pool[(first + i) % len(pool)][0]]) for i in range(len(pool))]

    evidence_summary = dict(
        natal=dict(lead_group=group, strength=strength, status=safe_status,
                   ten_gods={_TEN_GOD.get(k, k): v for k, v in counts.items()}),
        copy_ids=dict(tier1=group, tier2=[b["title"] for b in t2]),
    )

    if unlocked:
        d = _compose_v3(core, query, user_name or "회원", group, track, strength, safe_status, counts, seed, fixed_year)
        gated = _unlocked_html(d)
        ev = d["evidence"]
        evidence_summary["months"] = ev["months"]
        evidence_summary["years"] = [ev["year"]]
        evidence_summary["v3"] = {k: v for k, v in ev.items() if k not in ("months",)}
        advice = _clean(direction_advice(query["applied_state"], "career", ""), "career.evidence")
        tiers_ko = " · ".join(f'{_ELEMENT_KO[e]} {_TIER_KO[t]}' for e, t in ev["tiers"].items())
        basis = (f'오행 3단계(행운 색과 같은 기준): {tiers_ko}. '
                 f'힘이 되는 사람 = 필요한 오행의 십성({_GROUP_KO[ev["helper"]]}), '
                 f'부딪히기 쉬운 사람 = 피할 오행의 십성({_GROUP_KO[ev["hard"]]}). '
                 f'달별 등급은 각 달 15일의 월주를 오늘의 운세 \'일\' 분야 규칙표로 판정. '
                 f'움직이는 달 = 연지·일지의 역마, 월지 충.')
        evidence_extra = (f'<p>{escape(advice)}</p>' if advice else "") + f'<p data-career-basis="v3">{escape(basis)}</p>'
    else:
        gated = _locked_html()
        evidence_extra = ""

    evidence = (
        '<details class="reading-evidence"><summary>이 풀이의 근거 · 명리 용어 포함</summary>'
        f'<p>{escape(safe_status)} 기준 · {escape(_count_summary(counts, track))}</p>{evidence_extra}</details>')

    content = (
        f'<div class="theme-reading" data-theme="career" data-narrative-version="{CAREER_NARRATIVE_VERSION}" '
        f'data-copy-version="{copy.COPY_VERSION}" data-unlocked="{str(unlocked).lower()}">'
        + _tier1_html(t1, stem_text) + _tier2_html(t2)
        + _boundary_html() + gated
        + evidence + _uncertainty(core) +
        '<p class="reading-caption">원국과 흐름을 바탕으로 한 해석이며 결과를 보장하지 않습니다. '
        '중요한 결정은 현실의 조건과 전문가의 판단도 함께 확인해 주세요.</p></div>')
    return {
        "analysis_basis": state_basis(query["applied_state"]),
        "title": f"{name}님 정통 명리 직업·사업운",
        "content": content,
        "narrative_version": CAREER_NARRATIVE_VERSION,
        "copy_version": copy.COPY_VERSION,
        "is_unlocked": unlocked,
        "evidence_summary": evidence_summary,
    }
