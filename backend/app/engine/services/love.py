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
from app.engine.services.annual_copy import seed_from
from app.engine.services import love_copy as copy
from app.engine.services import theme_timing
from app.engine.services.daily_score import calendar_ganji
from app.engine.facts.ten_gods import get_ten_god

LOVE_NARRATIVE_VERSION = "love-v3"  # 11/06: 잘 맞는 사람·지금의 사랑 추가, 연애 상태 선택 제거

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


def _tier1_html(t1: dict) -> str:
    return (
        '<section data-love-tier="1" data-paywall="free"><h2>소통 기질 진단</h2>'
        f'<h3>{escape(t1["headline"])}</h3><p>{escape(t1["body"])}</p></section>')


def _tier2_html(boxes: list[dict]) -> str:
    items = "".join(
        f'<div data-love-trap="{i}" style="{_BOX}">'
        f'<strong>{escape(b["title"])}</strong><p style="margin:4px 0 0;">{escape(b["text"])}</p></div>'
        for i, b in enumerate(boxes, start=1))
    return (
        '<section data-love-tier="2" data-paywall="free"><h2>관계에서 반복하기 쉬운 습관 2가지</h2>'
        f'<div style="display:grid;gap:8px;">{items}</div></section>')


def _boundary_html() -> str:
    return ('<hr data-paywall-boundary="love" '
            'style="border:0;border-top:1px dashed #94A3B8;margin:18px 0;">')


def _locked_html() -> str:
    def block(tier: int, title: str, teaser: str) -> str:
        return (
            f'<section data-love-tier="{tier}" data-paywall="locked" data-locked="true" '
            'style="border:1px dashed #94A3B8;border-radius:12px;background:#F8FAFC;padding:14px;margin-bottom:8px;">'
            f'<div style="font-size:12px;color:#64748B;font-weight:800;">🔒 {escape(copy.LOCK_LABEL)}</div>'
            f'<h2 style="margin:4px 0 0;">{escape(title)}</h2>'
            f'<p data-love-teaser="{tier}" style="margin:6px 0 0;">{escape(teaser)}</p>{_SKELETON}</section>')
    return (
        block(3, "앞으로 12개월 관계의 타이밍", copy.TEASER_TIER3)
        + block(4, "다정한 관계 3원칙", copy.TEASER_TIER4)
        + f'<a href="{copy.PAYWALL_HREF}" data-paywall-cta="theme-love" style="display:inline-block;margin-top:6px;'
          'padding:10px 16px;border-radius:10px;background:#2D6A4F;color:#fff;font-weight:700;text-decoration:none;">'
          f'{escape(copy.cta_label())}</a>')


def _unlocked_html(t3: dict, bullets: list[str], match: dict, now: dict) -> str:
    match_html = _pair_section("match", copy.MATCH_HEADING,
                               [(copy.MATCH_GOOD_TITLE, match["good"]), (copy.MATCH_BAD_TITLE, match["bad"])])
    tier3 = theme_timing.tier3_html(t3, "love", "앞으로 12개월 관계의 타이밍",
                                    "상대의 선택이나 특정 사건을 예측한 것은 아닙니다.", copy.NO_INFLECTION)
    now_html = _pair_section("now", copy.NOW_HEADING,
                             [(copy.NOW_SINGLE_TITLE, now["single"]), (copy.NOW_COUPLE_TITLE, now["couple"])])
    items = "".join(f'<li data-love-action="{i}">{escape(b)}</li>' for i, b in enumerate(bullets, start=1))
    tier4 = f'<section data-love-tier="4" data-paywall="unlocked"><h2>다정한 관계 3원칙</h2><ol>{items}</ol></section>'
    return match_html + tier3 + now_html + tier4


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
    t2 = copy.compose_tier2(group, seed)

    evidence_summary = dict(
        natal=dict(lead_group=group,
                   ten_gods={_TEN_GOD.get(k, k): v for k, v in counts.items()}),
        copy_ids=dict(tier1=group, tier2=[b["title"] for b in t2]),
    )

    if unlocked:
        t3 = theme_timing.build_tier3(core, "love", _MONTH_DOMAINS,
                                      lambda inf: copy.compose_tier3(inf, safe_status, seed), year=fixed_year)
        bullets = copy.compose_tier4(group, safe_status)
        match, now = _match_and_now(core, user_name or "회원")
        gated = _unlocked_html(t3, bullets, match, now)
        evidence_summary["match"] = match["evidence"]
        evidence_summary["now"] = now["evidence"]
        evidence_summary["months"] = t3["evidence_months"]
        evidence_summary["years"] = t3["evidence_years"]
        advice = copy.sanitize(direction_advice(query["applied_state"], "love", ""))
        evidence_extra = f'<p>{escape(advice)}</p>' if advice else ""
        me, ne = match["evidence"], now["evidence"]
        basis = (f"잘 맞는 사람: 일지 {me['day_branch']}의 육합 {me['six_combination']} · "
                 f"부딪히기 쉬운 사람: 일지 {me['day_branch']}의 충 {me['clash']} · "
                 f"인연이 들어오는 길: 지금 대운 {ne['cycle'] or '-'}({ne['cycle_group'] or '-'}), "
                 f"앞으로 12개월의 세운 {ne['year']}({ne['year_group']})")
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
        + _tier1_html(t1) + _tier2_html(t2) + _boundary_html() + gated
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
