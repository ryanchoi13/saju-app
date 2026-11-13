"""애정·관계 테마운 (4단 구조 · 2,900원 페이월).

1단 소통 기질 진단 · 2단 관계 습관의 함정 → 무료
3단 관계 타이밍 · 4단 다정한 관계 3원칙   → is_unlocked=True 일 때만 본문을 만든다.

보안 원칙은 career.py 와 같다.
- 잠금 상태에서는 3·4단 '본문'을 HTML, evidence_summary, 반환 dict 어디에도 싣지 않고 월별 계산도 하지 않는다.
- is_unlocked 는 키워드 전용이며 `is True` 로만 비교한다. (status 가 위치 인자 세 번째이므로,
  위치 인자로 두면 "솔로" 같은 문자열이 참값으로 읽혀 전부 열리는 사고가 난다.)
- is_unlocked 는 서버가 결제 내역으로 계산해 넘겨야 하며, 해제된 결과를 캐시할 때는 키에 해제 여부를 넣을 것.

집필 헌칙: 이별·이혼·외도·결혼 시기 등 단정 표현 금지 (love_copy.find_sensitive).
성별/십신 로직은 이 파일에 없다. build_service_query(core, "love") 가 골라 준 focused_ten_gods 를
그대로 존중해 '표현 방식과 소통 기질'로만 옮겼다.
"""

from __future__ import annotations

from collections import Counter
from datetime import date
from html import escape

from app.engine.core.models import MyeongriCoreResult
from app.engine.calendar import to_solar
from app.engine.semantic import build_service_query
from app.engine.services.applied_guidance import direction_advice, state_basis
from app.engine.services.annual_copy import seed_from, split_sentences
from app.engine.services import love_copy as copy
from app.engine.services import theme_timing
from app.engine.services import love_sections as sec
from app.engine.services import love_depth as depth
from app.engine.services import daily_score
from app.engine.services.daily_score import _god_group
from app.engine.services.element_balance import element_tiers, natal_balance
from app.engine.constants import GAN_KO, GAN_WUXING, ZHI_KO
from app.engine.services.daily_score import calendar_ganji
from app.engine.facts.ten_gods import get_ten_god

LOVE_NARRATIVE_VERSION = "love-v4"  # 11/13: 칸 10개 · 12달 등급 (11/06 v3: 잘 맞는 사람·지금의 사랑, 상태 선택 제거)

_TEN_GOD = {
    "peer": "비견", "rob_wealth": "겁재", "eating_god": "식신",
    "hurting_officer": "상관", "direct_wealth": "정재",
    "indirect_wealth": "편재", "direct_officer": "정관",
    "seven_killings": "편관", "direct_resource": "정인",
    "indirect_resource": "편인",
}
# 대운 주제 문구. reading_editorial.cycle_focus 가 이 이름으로 임포트한다(삭제 금지).
_CYCLE_TOPIC = {
    "direct_wealth": "약속과 생활의 안정성을 현실적으로 맞추는 일",
    "indirect_wealth": "만남의 폭과 관계의 변화를 유연하게 다루는 일",
    "direct_officer": "책임·신뢰·관계의 기준을 분명히 하는 일",
    "seven_killings": "긴장이나 빠른 변화 속에서 경계를 지키는 일",
    "peer": "나와 상대의 독립성을 함께 존중하는 일",
    "rob_wealth": "경쟁심·주도권·시간 배분을 공정하게 조율하는 일",
    "eating_god": "편안한 대화와 일상의 즐거움을 꾸준히 나누는 일",
    "hurting_officer": "솔직한 표현이 비판으로 들리지 않도록 전달하는 일",
    "direct_resource": "상대의 말을 충분히 듣고 신뢰를 축적하는 일",
    "indirect_resource": "혼자 해석하기보다 생각을 확인하며 소통하는 일",
}

_RELATION_LABEL = {
    "stem_combination": "천간합", "stem_control": "천간극",
    "branch_six_combination": "육합", "branch_clash": "충",
    "branch_three_combination": "삼합", "branch_half_combination": "반합",
    "branch_directional_combination": "방합", "branch_punishment": "형",
    "branch_harm": "해", "branch_break": "파",
}
# 월별 흐름에서 '관계' 신호로 읽을 도메인. (엔진의 실제 의미와 다르면 여기를 고친다.)
_MONTH_DOMAINS = ("love", "relationships")


def _natal_relationship_summary(relationships: list[dict]) -> str:
    active = [item for item in relationships if item.get("action_status") in {"active", "resolved"}]
    conditional = [
        item for item in relationships
        if item.get("action_status") in {"conditional", "competing", "blocked"}
    ]
    day_related = [
        item for item in relationships
        if any(member.get("pillar") == "day" for member in item.get("members", []))
    ]
    labels = list(dict.fromkeys(_RELATION_LABEL.get(item.get("type"), item.get("type")) for item in day_related))
    day_text = (
        f"그중 일주와 직접 연결된 후보는 {', '.join(labels)}이며, 관계의 실제 작용 상태를 따로 판정했습니다."
        if labels else
        "일주와 직접 연결된 관계 후보가 없더라도, 이것만으로 인연의 유무나 관계의 좋고 나쁨을 판단하지 않습니다."
    )
    return (
        f"원국에서 관계 후보 {len(relationships)}건을 확인했고, 현재 규칙상 작용 또는 해소된 관계는 {len(active)}건, "
        f"조건·경쟁·차단을 함께 봐야 하는 관계는 {len(conditional)}건입니다. {day_text}"
    )


def _uncertainty(core: MyeongriCoreResult) -> str:
    if not core.uncertainty.time_unknown:
        return ""
    return """
    <div style="background:#FFF7ED;border:1px solid #FED7AA;padding:12px 14px;border-radius:12px;margin-top:12px;">
      <div style="font-size:13px;font-weight:800;color:#9A3412;">생시 미상 안내</div>
      <p style="font-size:12.5px;color:#7C2D12;margin:5px 0 0;line-height:1.65;">시주에 따라 일부 십성과 관계 후보가 달라질 수 있어, 여러 시주에서 공통으로 유지되는 원국과 흐름을 중심으로 설명했습니다.</p>
    </div>"""


# ---------------------------------------------------------------------------
# 잘 맞는 사람·지금의 사랑 (11/06) 계산. 일지 = 가까운 관계 자리.
# ---------------------------------------------------------------------------
_SIX_COMBO = {"子": "丑", "丑": "子", "寅": "亥", "亥": "寅", "卯": "戌", "戌": "卯",
              "辰": "酉", "酉": "辰", "巳": "申", "申": "巳", "午": "未", "未": "午"}
_CLASH = {"子": "午", "午": "子", "丑": "未", "未": "丑", "寅": "申", "申": "寅",
          "卯": "酉", "酉": "卯", "辰": "戌", "戌": "辰", "巳": "亥", "亥": "巳"}
# 도화: 연지·일지가 속한 삼합의 욕지(寅午戌→卯, 申子辰→酉, 巳酉丑→午, 亥卯未→子)
_PEACH = {**dict.fromkeys("寅午戌", "卯"), **dict.fromkeys("申子辰", "酉"),
          **dict.fromkeys("巳酉丑", "午"), **dict.fromkeys("亥卯未", "子")}


def _ten_god_value(day_master: str, stem: str) -> str:
    god = get_ten_god(day_master, stem)
    return getattr(god, "value", str(god))


def _window_branches(core: MyeongriCoreResult) -> list[tuple[int, int, str, str]]:
    """보는 날부터 12개월, 각 달 15일의 (연, 월, 세운 간지, 월운 지지)."""
    birth = to_solar(core.input.birth_date, core.input.calendar_type, core.input.is_leap_month)
    out = []
    for y, m in theme_timing.window_months(theme_timing.window_start(core)):
        target = date(y, m, 15)
        if target < birth:
            continue
        year_gz, month_gz, _ = calendar_ganji(target)
        out.append((y, m, year_gz, month_gz[1]))
    return out


def _month_text(y: int, m: int) -> str:
    return f"{y}년 {m}월"


def _match_and_now(core: MyeongriCoreResult, name: str) -> tuple[dict, dict]:
    pillars = core.natal_facts.pillars
    day_master = pillars["day"].stem
    day_branch = pillars["day"].branch
    good_b, bad_b = _SIX_COMBO[day_branch], _CLASH[day_branch]
    match = dict(
        good=copy.MATCH_GOOD.format(name=name, person=copy.BRANCH_PERSON[good_b]),
        bad=copy.MATCH_BAD.format(name=name, person=copy.BRANCH_PERSON[bad_b]),
        evidence=dict(day_branch=day_branch, six_combination=good_b, clash=bad_b))

    months = _window_branches(core)
    # 앞으로 12개월의 세운: 기간 안에서 달이 더 많이 속한 해(같으면 뒤의 해)
    year_count = Counter(gz for _, _, gz, _ in months)
    year_gz = max(year_count, key=lambda gz: (year_count[gz], [g for _, _, g, _ in months].index(gz)))
    current = (core.timing.luck_cycle or {}).get("current") or {}
    cycle_stem = ((current.get("pillar") or {}).get("stem")) or None
    cycle_group = copy.GOD_GROUP.get(_ten_god_value(day_master, cycle_stem)) if cycle_stem else None
    year_group = copy.GOD_GROUP.get(_ten_god_value(day_master, year_gz[0]))
    if cycle_group is None or cycle_group == year_group:
        path = copy.NOW_PATH_SAME.format(path=copy.MEET_PATH[year_group])
    else:
        path = copy.NOW_PATH_TWO.format(cycle=copy.MEET_PATH[cycle_group], year=copy.MEET_PATH[year_group])

    peach_branches = {_PEACH[pillars["year"].branch], _PEACH[day_branch]}
    peach = next(((y, m, b) for y, m, _, b in months if b in peach_branches), None)
    single = [path]
    if peach:
        tpl = copy.NOW_PEACH_COMBO if peach[2] == good_b else copy.NOW_PEACH
        single.append(tpl.format(month=_month_text(peach[0], peach[1])))

    good_m = next(((y, m) for y, m, _, b in months if b == good_b), None)
    bad_m = next(((y, m) for y, m, _, b in months if b == bad_b), None)
    couple = []
    if good_m and bad_m:
        couple.append(copy.NOW_COUPLE_MONTHS.format(good=_month_text(*good_m), bad=_month_text(*bad_m)))
    talk_group = cycle_group or year_group
    couple.append(copy.NOW_TALK.format(talk=copy.TALK[talk_group]))
    now = dict(single=" ".join(single), couple=" ".join(couple),
               evidence=dict(cycle=current.get("pillar", {}).get("ganji"), cycle_group=cycle_group,
                             year=year_gz, year_group=year_group,
                             peach=[f"{y}-{m:02d}" for y, m, _ in [peach]] if peach else [],
                             good_month=f"{good_m[0]}-{good_m[1]:02d}" if good_m else None,
                             bad_month=f"{bad_m[0]}-{bad_m[1]:02d}" if bad_m else None))
    return match, now


def _pair_section(attr: str, heading: str, items: list[tuple[str, str]]) -> str:
    body = "".join(
        f'<div data-love-{attr}="{i}"><strong>{escape(t)}</strong><p>{escape(x)}</p></div>'
        for i, (t, x) in enumerate(items, start=1))
    return (f'<section data-love-tier="{attr}" data-paywall="unlocked"><h2>{escape(heading)}</h2>'
            f'<div class="love-pair">{body}</div></section>')


# ---------------------------------------------------------------------------
# 3단 계산: 월별 흐름 점수 (유료 전용). 점수 규칙은 career 와 같다.
#   join +2 · recovery +1 · base 0 · mixed -1 · change -2  (mode 이름만 보고 정한 해석)
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# HTML 조각 (career.py 와 같은 구조. 세 테마가 끝나면 theme_common 으로 옮길 후보)
# ---------------------------------------------------------------------------
_BOX = "border:1px solid #E2E8F0;border-radius:12px;padding:12px 14px;background:#FFFFFF;"
_SKELETON = (
    '<div data-locked-body="true" aria-hidden="true" style="filter:blur(3px);margin-top:8px;opacity:.55;">'
    '<span style="display:block;height:9px;margin:6px 0;border-radius:5px;background:#CBD5E1;"></span>'
    '<span style="display:block;height:9px;margin:6px 0;border-radius:5px;background:#CBD5E1;width:92%;"></span>'
    '<span style="display:block;height:9px;margin:6px 0;border-radius:5px;background:#CBD5E1;width:78%;"></span>'
    '</div>'
)


def _section(key: str, title: str, body: str, paywall: str = "unlocked", tier: str | None = None) -> str:
    tier_attr = f' data-love-tier="{tier}"' if tier else ""
    return (f'<section data-love-section="{key}"{tier_attr} data-paywall="{paywall}">'
            f'<h2>{escape(title)}</h2>{body}</section>')


def _p(text: str, attr: str = "") -> str:
    return f'<p{attr}>{escape(text)}</p>' if text else ""


def _tier1_html(t1: dict, stem_text: str) -> str:
    return _section("nature", "소통 기질 진단",
                    f'<h3>{escape(t1["headline"])}</h3>{_p(t1["body"])}{_p(stem_text)}', "free", "1")


def _tier2_html(boxes: list[dict]) -> str:
    items = "".join(
        f'<div data-love-trap="{i}" style="{_BOX}">'
        f'<strong>{escape(b["title"])}</strong><p style="margin:4px 0 0;">{escape(b["text"])}</p>'
        f'<p data-love-trap-fix="{i}" style="margin:4px 0 0;">{escape(b["fix"])}</p></div>'
        for i, b in enumerate(boxes, start=1))
    return _section("traps", f"관계에서 반복하기 쉬운 습관 {len(boxes)}가지",
                    f'<div style="display:grid;gap:8px;">{items}</div>', "free", "2")


def _boundary_html() -> str:
    return ('<hr data-paywall-boundary="love" '
            'style="border:0;border-top:1px dashed #94A3B8;margin:18px 0;">')


def _locked_html() -> str:
    titles = "".join(f'<li data-love-locked="{k}">{escape(t)}</li>' for k, t in sec.LOCKED_SECTIONS)
    return (
        '<section data-love-tier="3" data-paywall="locked" data-locked="true" '
        'style="border:1px dashed #94A3B8;border-radius:12px;background:#F8FAFC;padding:14px;margin-bottom:8px;">'
        f'<div style="font-size:12px;color:#64748B;font-weight:800;">🔒 {escape(copy.LOCK_LABEL)}</div>'
        '<h2 style="margin:4px 0 0;">이어지는 풀이</h2>'
        f'<p data-love-teaser="3" style="margin:6px 0 0;">{escape(sec.LOCKED_TEASER)}</p>'
        f'<ul style="padding-left:18px;margin:6px 0 0;">{titles}</ul>{_SKELETON}</section>'
        f'<a href="{copy.PAYWALL_HREF}" data-paywall-cta="theme-love" style="display:inline-block;margin-top:6px;'
        'padding:10px 16px;border-radius:10px;background:#2D6A4F;color:#fff;font-weight:700;text-decoration:none;">'
        f'{escape(copy.cta_label())}</a>')


def _pair_section(attr: str, heading: str, items: list[tuple[str, str]]) -> str:
    body = "".join(
        f'<div data-love-{attr}="{i}"><strong>{escape(t)}</strong><p>{escape(x)}</p></div>'
        for i, (t, x) in enumerate(items, start=1))
    return (f'<section data-love-section="{attr}" data-love-tier="{attr}" data-paywall="unlocked"><h2>{escape(heading)}</h2>'
            f'<div class="love-pair">{body}</div></section>')


def _unlocked_html(d: dict, match: dict, now: dict) -> str:
    g = d["group"]
    out = [
        _section("charm", sec.CHARM_HEADING, "".join(_p(x) for x in d["charm"].split("\n\n"))),
        _section("past", sec.PAST_HEADING,
                 _p(d["depth"]["past"]["intro"])
                 + ("<ul>" + "".join(f'<li data-love-past="{i}">{escape(t)}</li>'
                                     for i, t in enumerate(d["depth"]["past"]["items"], start=1)) + "</ul>"
                    if d["depth"]["past"]["items"] else "")
                 + _p(d["depth"]["past"]["tail"])),
        _section("palace", sec.PALACE_HEADING, "".join(_p(t) for t in d["depth"]["palace"])),
        _section("weak", sec.WEAK_HEADING,
                 '<div class="love-pair">' + "".join(
                     f'<div data-love-weak="{k}"><strong>{escape(t)}</strong><p>{escape(b)}</p>'
                     f'<p data-love-weak-fix="{k}">{escape(f)}</p></div>' for k, t, b, f in d["depth"]["weak"]) + '</div>'
                 if d["depth"]["weak"] else _p(sec.WEAK_NONE)),
        _pair_section("match", copy.MATCH_HEADING,
                      [(copy.MATCH_GOOD_TITLE, match["good"]), (copy.MATCH_BAD_TITLE, match["bad"])]),
        _pair_section("makeup", sec.MAKEUP_HEADING,
                      [(sec.MAKEUP_TITLE, sec.MAKEUP[g]), (sec.PARTNER_TITLE, sec.PARTNER[g])]),
        _section("remedy", sec.REMEDY_HEADING, "".join(
            f'<div data-love-remedy="{k}"><strong>{escape(t)}</strong><p>{escape(x)}</p></div>'
            for k, t, x in (("key", sec.KEY_TITLE, d["remedy"]["key"]), ("crisis", sec.CRISIS_TITLE, d["remedy"]["crisis"]),
                            ("luck", sec.LUCK_TITLE, d["remedy"]["luck"])) if x).join(('<div class="love-pair">', '</div>'))),
        _pair_section("now", copy.NOW_HEADING,
                      [(copy.NOW_SINGLE_TITLE, now["single"]), (copy.NOW_COUPLE_TITLE, now["couple"])]),
        _section("partner", sec.PARTNER_HEADING, "".join(_p(t) for t in d["depth"]["partner"])),
    ]
    if d["cycle"]:
        out.append(_section("cycle", "이번 10년의 사랑",
                            f'<h3>{escape(d["cycle_head"])}</h3>' + _p(d["cycle"]) + _p(d["cycle_tier"]) + _p(d["cycle_next"])))
    rows = "".join(
        f'<li data-love-month="{m["y"]}-{m["m"]:02d}" data-month-grade="{m["grade"]}">'
        f'<strong>{escape(m["display"])} · {escape(m["label"])}</strong> {escape(m["line"])}</li>'
        for m in d["months"])
    keys = "".join(
        f'<div data-love-key-month="{k["y"]}-{k["m"]:02d}" style="{_BOX}">'
        f'<strong>{escape(k["display"])} · {escape(k["label"])}</strong>'
        f'<p style="margin:4px 0 0;">{escape(k["text"])}</p></div>'
        for k in d["key_months"])
    keys_html = (f'<h3>눈여겨볼 달</h3><div style="display:grid;gap:8px;">{keys}</div>' if keys
                 else _p(sec.NO_KEY_MONTH, ' data-love-key-month="none"'))
    year_html = (f'<h3>{escape(d["year_head"])}</h3>' + _p(d["year"])) if d["year"] else ""
    out.append(_section("months", "앞으로 12개월 관계의 타이밍",
                        f'<p class="reading-caption">{escape(d["month_caption"])}</p>' + year_html
                        + f'<h3>달별 흐름</h3><ul style="padding-left:18px;">{rows}</ul>' + keys_html, tier="3"))
    out.append(_section("place", "함께 가면 좋은 곳", _p(d["place"])))
    items = "".join(f'<li data-love-action="{i}">{escape(b)}</li>' for i, b in enumerate(d["bullets"], start=1))
    out.append(_section("actions", "다정한 관계를 위한 실천", f'<ol>{items}</ol>', tier="4"))
    return "".join(out)


# ---------------------------------------------------------------------------
# v4 계산 (유료 칸). 잠금 상태에서는 부르지 않는다.
# ---------------------------------------------------------------------------
_GENDER_RULE = "이성 인연의 기운"   # 성별로 배우자 별을 정하는 규칙 — 애정운에서는 쓰지 않는다(헌칙)


def _love_tier(rule: dict) -> tuple[str, str | None]:
    good = [r for r in rule["good"] if r != _GENDER_RULE]
    if rule["tier"] == "주의":
        return "caution", (rule["bad"] or [None])[0]
    if rule["tier"] == "좋음" and good:
        return "good", good[0]
    return "normal", None


def _pick_line(pool: tuple, start: int, used: set) -> str:
    """같은 문장이 12달 목록에 두 번 나오지 않게, 아직 안 쓴 변형부터 고른다(다 썼으면 처음 자리)."""
    for i in range(len(pool)):
        line = pool[(start + i) % len(pool)]
        if line not in used:
            used.add(line)
            return line
    return pool[start % len(pool)]


def _months(core: MyeongriCoreResult, seed: int, start: tuple[int, int] | None = None, skip=None) -> tuple[list[dict], list[dict], dict]:
    dm = core.natal_facts.pillars["day"].stem
    birth = to_solar(core.input.birth_date, core.input.calendar_type, core.input.is_leap_month)
    rows, prev, used = [], None, set()
    for y, m in theme_timing.window_months(start or theme_timing.window_start(core)):
        target = date(y, m, 15)
        if target < birth:
            continue
        year_gz, month_gz, _ = calendar_ganji(target)
        r = daily_score.evaluate(core, month_gz, target)
        grade, reason = _love_tier(r["domain_rules"]["사람"])
        group = _god_group(dm, GAN_WUXING[month_gz[0]])
        rows.append(dict(y=y, m=m, ganji=month_gz, year_ganji=year_gz, grade=grade,
                         label=sec.GRADE_LABEL[grade], line=_pick_line(sec.MONTH_LINE[group][grade], seed + m, used),
                         score=r["score"], reason=reason, display=theme_timing.month_label(y, m, prev)))
        prev = y
    # '지금의 사랑'이 이미 이름을 짚은 달(도화·합·충 달)은 눈여겨볼 달에서 빼서 같은 말을 되풀이하지 않는다(11/13 정오님).
    # 12달 목록에는 그대로 남으므로 두 칸이 어긋나지는 않는다.
    skip = set(skip or ())
    goods = sorted((r for r in rows if r["grade"] == "good" and (r["y"], r["m"]) not in skip), key=lambda r: -r["score"])
    bads = sorted((r for r in rows if r["grade"] == "caution" and (r["y"], r["m"]) not in skip), key=lambda r: r["score"])
    picked = ([goods.pop(0)] if goods else []) + ([bads.pop(0)] if bads else [])
    # 셋째 달은 앞의 달과 이유가 다른 달만 고른다(같은 이유·같은 처방 문장이 두 번 나오지 않게)
    for r in sorted(goods + bads, key=lambda r: -abs(r["score"] - 75)):
        if len(picked) >= 3:
            break
        if r["reason"] not in {x["reason"] for x in picked}:
            picked.append(r)
    picked.sort(key=lambda r: (r["y"], r["m"]))
    keys = [dict(y=r["y"], m=r["m"], display=f'{r["y"]}년 {r["m"]}월', label=r["label"], basis=r["reason"],
                 text=" ".join(t for t in (sec.LOVE_REASON.get(r["reason"], ""),
                                           sec.LOVE_ADVICE.get(r["reason"], "")) if t))
            for r in picked]
    count = Counter(r["year_ganji"] for r in rows)
    order = [r["year_ganji"] for r in rows]
    year_gz = max(count, key=lambda g: (count[g], -order.index(g))) if rows else None
    year_num = Counter(r["y"] for r in rows if r["year_ganji"] == year_gz).most_common(1)[0][0] if year_gz else None
    return rows, keys, dict(ganji=year_gz, year=year_num)


def _charm(core: MyeongriCoreResult, name: str) -> dict:
    """원국 도화(연지·일지 삼합의 욕지가 원국 어느 자리에 있나)와 홍염(일간 기준)."""
    p = core.natal_facts.pillars
    have = {k: p[k].branch for k in sec.PILLAR_ORDER if p.get(k) is not None}
    sources = [k for k in ("year", "day") if k in have]
    targets = {k: _PEACH[have[k]] for k in sources}
    positions = sorted({pos for t in targets.values() for pos, b in have.items() if b == t},
                       key=sec.PILLAR_ORDER.index)
    double = len(sources) == 2 and targets["year"] == targets["day"] and bool(positions)
    red_branch = sec.REDFLOWER_STEM[p["day"].stem]
    red = [pos for pos, b in have.items() if b == red_branch]
    # 도화가 운(세운)에서 들어오는 가장 가까운 해 — 일지 기준 도화(없으면 연지 기준)
    peach_branch = targets.get("day") or targets.get("year")
    this_year = theme_timing.window_start(core)[0]
    year_line, peach_year = "", None
    for y in range(this_year, this_year + 12):
        gz = calendar_ganji(date(y, 6, 15))[0]
        if gz[1] == peach_branch:
            peach_year = (y, gz)
            ko = GAN_KO.get(gz[0], "") + ZHI_KO.get(gz[1], "")
            tpl = sec.PEACH_YEAR_NOW if y == this_year else (sec.PEACH_YEAR_HAVE if positions else sec.PEACH_YEAR_NONE)
            year_line = tpl.format(year=y, ganji_ko=ko)
            break
    return dict(text=sec.charm_text(name, positions, double, bool(red), year_line), peach_branch=peach_branch,
                evidence=dict(peach_targets=targets, peach_positions=positions, redflower=red,
                              peach_year=list(peach_year) if peach_year else None))


def _age_span(birth_year: int, a: int, b: int) -> str:
    aa, bb = a - birth_year + 1, b - birth_year + 1
    return f"{aa}세({a}년)" if a == b else f"{aa}~{bb}세({a}~{b}년)"


def _depth(core: MyeongriCoreResult, query: dict, name: str) -> dict:
    """깊이 읽기 네 칸: 지나온 사랑 · 배우자 자리 · 되풀이되는 약점 · 동반자 시기 (love_depth 계산 + 문장)."""
    gender = "female" if str(getattr(core.input, "gender", "")) == "female" else "male"
    birth_year = to_solar(core.input.birth_date, core.input.calendar_type, core.input.is_leap_month).year
    this_year = theme_timing.window_start(core)[0]
    strength = query["synthesis"].get("strength_state")
    past = depth.past_love(core, gender, birth_year, this_year)
    pal = depth.palace(core, query, gender)
    counts = depth.natal_counts(core)
    weak = depth.weak_points(core, gender, strength, counts, past)
    tim = depth.partner_timing(core, gender, counts, pal, this_year)

    # 지나온 사랑
    if past["periods"] or past.get("entries") or past.get("moves"):
        lines = [sec.PAST_INTRO.format(name=name, star=sec.STAR_NAME[gender])]
        rivals = set(past.get("rivals", []))
        seen_rival = []

        def rival_tail(years) -> str:
            hit = [y for y in years if y in rivals]
            if not hit:
                return ""
            seen_rival.append(1)
            return " " + (sec.PAST_RIVAL if len(seen_rival) == 1 else sec.PAST_RIVAL_AGAIN)

        dated = []
        popular_seen = False
        for per in past["periods"]:
            span = _age_span(birth_year, per["start"], per["end"])
            if per.get("kind") == "popular" and not popular_seen:
                t, popular_seen = sec.PAST_POPULAR.format(span=span), True
            elif per.get("kind") == "popular":
                t = sec.PAST_POPULAR.split(". ")[0].format(span=span) + "."
            else:
                t = sec.PAST_PERIOD.format(span=span)
            years = list(range(per["start"], per["end"] + 1))
            if per.get("shake"):
                t += " " + sec.PAST_SHAKE.format(age=per["shake"] - birth_year + 1, year=per["shake"])
                years.append(per["shake"])
            dated.append((per["start"], t, years))
        # 풀이 문장은 처음 한 번만, 다음부터는 짧게(같은 문장 되풀이 금지)
        dated += [(y, (sec.PAST_ENTRY if i == 0 else sec.PAST_ENTRY_AGAIN).format(span=_age_span(birth_year, y, y)), [y])
                  for i, y in enumerate(sorted(past.get("entries", [])))]
        dated += [(y, (sec.PAST_MOVE if i == 0 else sec.PAST_MOVE_AGAIN).format(span=_age_span(birth_year, y, y)), [y])
                  for i, y in enumerate(sorted(past.get("moves", [])))]
        dated.sort(key=lambda x: x[0])                  # 해 순서대로 놓은 뒤 경쟁 문장을 붙인다(처음 것만 길게)
        items = [t + rival_tail(ys) for _, t, ys in dated]
        repeat = sum(1 for per in past["periods"] if per.get("shake"))
        tail = []
        if repeat >= 2:
            tail.append(sec.PAST_REPEAT.format(n=repeat))
        if past["star_cycles"]:
            merged = []
            for a, b in past["star_cycles"]:          # 이어진 10년들은 하나로(28~37·38~47 → 28~47세)
                if merged and a == merged[-1][1] + 1:
                    merged[-1] = (merged[-1][0], b)
                else:
                    merged.append((a, b))
            spans = ", ".join(f"{a}~{b}세" for a, b in merged)
            tail.append(sec.PAST_CYCLE.format(spans=spans))
        past_html = dict(intro=" ".join(lines), items=items, tail=" ".join(tail))
    else:
        past_html = dict(intro=sec.PAST_NONE, items=[], tail="")

    # 배우자 자리
    state = (sec.PALACE_CLASH if pal["clash"] else sec.PALACE_PUNISH if pal["punish"]
             else sec.PALACE_COMBO if pal["combo"] else sec.PALACE_CALM)
    palace_text = [sec.PALACE_LEAD,
                   " ".join(t for t in (sec.PALACE_GOD[pal["god"]].format(name=name),
                                        sec.PALACE_STAR if pal["star"] else "") if t),
                   " ".join(t for t in (state, sec.PALACE_VOID if pal["void"] else "") if t)]

    # 약점
    weak_items = []
    for k in weak:
        title, body, fix = sec.WEAK[k]
        weak_items.append((k, title, body.format(pair=sec.MIXED_PAIR[gender]), fix))

    # 동반자 시기
    if tim["verdict"] == "late":
        reasons = ", ".join(sec.LATE_REASON[r] for r in tim["late"][:2])
        verdict = sec.PARTNER_LATE.format(reasons=reasons.replace(", ", "·", 1) if False else reasons, name=name)
    elif tim["verdict"] == "early":
        verdict = sec.PARTNER_EARLY.format(name=name)
    else:
        verdict = sec.PARTNER_MIDDLE.format(name=name)
    years = ", ".join(f'{y["year"]}년({y["ko"]}년)' for y in tim["years"])
    partner = [verdict, sec.PARTNER_YEARS.format(years=years) if years else sec.PARTNER_NO_YEARS]
    return dict(past=past_html, palace=palace_text, weak=weak_items, partner=partner,
                evidence=dict(gender_star=gender, periods=past["periods"], star_cycles=past["star_cycles"],
                              cycle_entries=past.get("entries", []), moves=past.get("moves", []),
                              rivals=past.get("rivals", []),
                              palace=pal, weak=weak, natal_counts={k: len(v) for k, v in counts.items()},
                              timing=dict(verdict=tim["verdict"], late=tim["late"], early=tim["early"],
                                          years=[y["year"] for y in tim["years"]])))


_RISK_OF = (("words", ("eating_god", "hurting_officer"), 3), ("rival", ("peer", "rob_wealth"), 3),
            ("money", ("direct_wealth", "indirect_wealth"), 3), ("pressure", ("direct_officer", "seven_killings"), 3))


def _remedy(core: MyeongriCoreResult, query: dict, name: str, counts: Counter, tiers: dict, ranking: list[str],
            peach_branch: str | None) -> dict:
    """실패 없는 연애를 위한 개운법: 관계의 열쇠(필요한 오행의 십성) · 위기의 모습(원국 구조) · 흔들리는 해 · 도화 방위."""
    dm = core.natal_facts.pillars["day"].stem
    day_branch = core.natal_facts.pillars["day"].branch
    good = [e for e in ranking if tiers[e] == "good"] or [ranking[0]]
    key_group = _god_group(dm, good[0])
    day_hit = any(r.get("type") == "branch_clash"      # 일지충만 본다(형까지 넣으면 절반 가까이가 이 갈래로 몰렸다)
                  and any(m.get("pillar") == "day" for m in r.get("members", []))
                  for r in query["natal"]["relationships"])
    risk = "clash" if day_hit else next((k for k, gods, n in _RISK_OF if sum(counts.get(g, 0) for g in gods) >= n), "drift")
    this_year = theme_timing.window_start(core)[0]
    crisis_year = ""
    for y in range(this_year, this_year + 12):
        gz = calendar_ganji(date(y, 6, 15))[0]
        if gz[1] == _CLASH[day_branch]:
            crisis_year = sec.CRISIS_YEAR.format(year=y, ganji_ko=GAN_KO.get(gz[0], "") + ZHI_KO.get(gz[1], ""))
            break
    luck = ""
    if peach_branch in sec.DIRECTION:
        luck = sec.LUCK_LINE.format(name=name, branch=peach_branch, branch_ko=sec.BRANCH_KO[peach_branch],
                                    dir=sec.DIRECTION[peach_branch])
    return dict(key=" ".join((sec.KEY_WHY, sec.KEY[key_group].format(name=name))),
                crisis=crisis_year,      # 11/13: 위기의 모습은 '되풀이되는 약점' 칸으로 옮겼다(성별 인연의 별 반영)
                luck=luck, evidence=dict(key_group=key_group, risk=risk, day_clash_natal=day_hit))


def _compose_v4(core: MyeongriCoreResult, query: dict, name: str, group: str, seed: int,
                year: int | None = None, now: dict | None = None, counts: Counter | None = None) -> dict:
    start = (year, 1) if year else theme_timing.window_start(core)   # year 를 주면(옛 호출·테스트) 그해 1~12월
    dm = core.natal_facts.pillars["day"].stem
    tiers = element_tiers(core)["tiers"]
    ranking = natal_balance(core)["ranking"]
    good = [e for e in ranking if tiers[e] == "good"][:2]

    timing = query["timing"]["luck_cycles"]
    current = timing.get("current") or {}
    god = current.get("ten_god")
    cycle = sec.CYCLE.get(god, "")
    cycle_head = cycle_tier = cycle_next = ""
    if cycle:
        pillar = current["pillar"]
        cycle_head = (f'{current["start_age"]}~{current["end_age"]}세 · '
                      f'{GAN_KO.get(pillar["stem"], "")}{ZHI_KO.get(pillar["branch"], "")}({pillar["ganji"]}) 대운')
        cycle_tier = sec.CYCLE_TIER[tiers[GAN_WUXING[pillar["stem"]]]]
        nxt = next((c for c in timing.get("cycles", []) if c.get("index") == current.get("index", -9) + 1), None)
        if nxt and nxt.get("ten_god") in sec.NEXT_SHORT:
            gz = nxt["pillar"]["ganji"]
            cycle_next = sec.NEXT_LINE.format(age=nxt["start_age"], ganji=gz,
                                              ganji_ko=GAN_KO.get(gz[0], "") + ZHI_KO.get(gz[1], ""),
                                              short=sec.NEXT_SHORT[nxt["ten_god"]])

    ne = (now or {}).get("evidence", {})
    named = [ne.get("good_month"), ne.get("bad_month"), *(ne.get("peach") or [])]
    skip = {(int(v[:4]), int(v[5:7])) for v in named if v}
    rows, keys, year = _months(core, seed, start, skip)
    year_text = year_head = ""
    if year["ganji"]:
        year_text = sec.YEAR.get(_ten_god_value(dm, year["ganji"][0]), "")
        year_head = sec.YEAR_HEAD.format(year=year["year"],
                                         ganji_ko=GAN_KO.get(year["ganji"][0], "") + ZHI_KO.get(year["ganji"][1], ""))
    charm = _charm(core, name)
    depth = _depth(core, query, name)
    remedy = _remedy(core, query, name, counts or Counter(), tiers, ranking, charm["peach_branch"])
    year_god = _ten_god_value(dm, year["ganji"][0]) if year["ganji"] else None
    bullets = [copy.COMMON_BULLET]
    if god in sec.CYCLE_BULLET:
        bullets.append(sec.CYCLE_BULLET[god])
    if year_god in sec.YEAR_BULLET and year_god != god:
        bullets.append(sec.YEAR_BULLET[year_god])
    bullets.append(sec.CHARM_BULLET[bool(charm["evidence"]["peach_positions"])])
    if good:
        bullets.append(sec.PLACE_BULLET.format(place=sec.PLACE_SHORT[good[0]]))
    return dict(
        group=group if group in sec.START else "balanced", charm=charm["text"], remedy=remedy, depth=depth,
        cycle=cycle, cycle_head=cycle_head, cycle_tier=cycle_tier, cycle_next=cycle_next,
        year=year_text, year_head=year_head, month_caption=sec.MONTH_CAPTION.format(y=start[0], m=start[1]),
        months=rows, key_months=keys, place=sec.place_text(name, good), bullets=bullets,
        evidence=dict(good_elements=good, charm=charm["evidence"], remedy=remedy["evidence"], depth=depth["evidence"], cycle=current.get("pillar", {}).get("ganji"), cycle_god=god, year=year,
                      months=[dict(month=f'{r["y"]}-{r["m"]:02d}', ganji=r["ganji"], grade=r["grade"],
                                   reason=r["reason"]) for r in rows],
                      key_months=[k["basis"] for k in keys]),
    )


def build_lifetime_love_report(
    core: MyeongriCoreResult,
    user_name: str,
    status: str = copy.DEFAULT_STATUS,
    *,
    is_unlocked: bool = False,
    year: int | None = None,
) -> dict:
    """Render relationship guidance without deterministic event claims."""
    unlocked = is_unlocked is True
    safe_status = copy.safe_status(status)
    query = build_service_query(core, "love")
    name = escape(user_name or "회원")
    fixed_year = year
    year = year or theme_timing.window_start(core)[0]

    counts = Counter(item["ten_god"] for item in query["natal"]["focused_ten_gods"])
    relationships = query["natal"]["relationships"]
    group = copy.lead_group(counts)
    birth = to_solar(core.input.birth_date, core.input.calendar_type, core.input.is_leap_month)
    seed = seed_from(birth.isoformat(), "love", "-", year)  # 상태를 고르지 않으므로 씨앗에서도 뺀다

    t1 = copy.compose_tier1(group, safe_status)
    # 11/13 정오님 중복 지적: 1단 B 문장(표현 방식)은 2단 습관이 그대로 되받아 겹친다 → 기질(A)과 마무리(D)만 쓴다
    tb = copy.TIER1.get(t1.get("group", group), copy.TIER1["balanced"])
    t1 = dict(t1, body=" ".join((tb["A"], tb["D"])))
    # 일간 문단은 앞 두 문장만 — 셋째 문장(주의점)은 바로 아래 '관계 습관'과 겹친다(11/13 정오님 중복 지적)
    stem_text = " ".join(split_sentences(sec.STEM_LOVE.get(core.natal_facts.pillars["day"].stem, ""))[:2])
    pool = copy.TRAPS[group if group in copy.TRAPS else "balanced"]
    first = seed % len(pool)
    t2 = [dict(title=pool[(first + i) % len(pool)][0], text=pool[(first + i) % len(pool)][1],
               fix=sec.TRAP_FIX[pool[(first + i) % len(pool)][0]]) for i in range(len(pool))]

    evidence_summary = dict(
        natal=dict(lead_group=group,
                   ten_gods={_TEN_GOD.get(k, k): v for k, v in counts.items()}),
        copy_ids=dict(tier1=group, tier2=[b["title"] for b in t2]),
    )

    if unlocked:
        match, now = _match_and_now(core, user_name or "회원")
        d = _compose_v4(core, query, user_name or "회원", group, seed, fixed_year, now, counts)
        # '지금의 사랑'의 대화법이 개운법의 열쇠와 같은 십성 묶음이면 같은 말이 되므로 대화법 문장을 뺀다
        if copy.GOD_GROUP_EN.get(now["evidence"].get("cycle_group") or now["evidence"].get("year_group")) == d["remedy"]["evidence"]["key_group"]:
            now = dict(now, couple=now["couple"].replace(" " + copy.NOW_TALK.format(
                talk=copy.TALK[now["evidence"].get("cycle_group") or now["evidence"]["year_group"]]), ""))
        gated = _unlocked_html(d, match, now)
        evidence_summary["match"] = match["evidence"]
        evidence_summary["now"] = now["evidence"]
        evidence_summary["months"] = d["evidence"]["months"]
        evidence_summary["years"] = [d["evidence"]["year"]]
        evidence_summary["v4"] = {k: v for k, v in d["evidence"].items() if k != "months"}
        advice = copy.sanitize(direction_advice(query["applied_state"], "love", ""))
        evidence_extra = f'<p>{escape(advice)}</p>' if advice else ""
        me, ne = match["evidence"], now["evidence"]
        basis = (f"잘 맞는 사람: 일지 {me['day_branch']}의 육합 {me['six_combination']} · "
                 f"부딪히기 쉬운 사람: 일지 {me['day_branch']}의 충 {me['clash']} · "
                 f"인연이 들어오는 길: 지금 대운 {ne['cycle'] or '-'}({ne['cycle_group'] or '-'}), "
                 f"앞으로 12개월의 세운 {ne['year']}({ne['year_group']}) · "
                 f"달별 등급: 각 달 15일 월주를 오늘의 운세 '사람' 분야 규칙표로 판정(성별 규칙 제외) · "
                 f"함께 가면 좋은 곳: 행운 색과 같은 오행 3단계의 '좋음' · "
                 f"타고난 매력: 도화 = 연지·일지 삼합의 욕지 {d['evidence']['charm']['peach_targets']}, 홍염 = 일간 기준")
        evidence_extra += f'<p data-love-basis="match-now">{escape(basis)}</p>'
    else:
        gated = _locked_html()
        evidence_extra = ""

    summary = copy.sanitize(_natal_relationship_summary(relationships))
    evidence = (
        '<details class="reading-evidence"><summary>이 풀이의 근거 · 명리 용어 포함</summary>'
        f'<h4>관계의 구조</h4><h5>원국의 관계 작용</h5>'
        f'<p>{escape(summary)}</p>{evidence_extra}</details>')

    content = (
        f'<div class="theme-reading" data-theme="love" data-narrative-version="{LOVE_NARRATIVE_VERSION}" '
        f'data-copy-version="{copy.COPY_VERSION}" data-unlocked="{str(unlocked).lower()}">'
        + _tier1_html(t1, stem_text) + _tier2_html(t2) + _boundary_html() + gated
        + evidence + _uncertainty(core) +
        '<p class="reading-caption">원국과 흐름을 바탕으로 한 해석이며 상대의 마음이나 관계의 결과를 단정하지 않습니다. '
        '중요한 결정은 현실의 상황과 서로의 대화도 함께 살펴 주세요.</p></div>')
    return {
        "analysis_basis": state_basis(query["applied_state"]),
        "title": f"{name}님 정통 명리 애정·관계운",
        "content": content,
        "narrative_version": LOVE_NARRATIVE_VERSION,
        "copy_version": copy.COPY_VERSION,
        "is_unlocked": unlocked,
        "evidence_summary": evidence_summary,
    }
