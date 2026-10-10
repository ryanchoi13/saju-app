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
from app.engine.timing import calculate_timing
from app.engine.semantic import build_service_query
from app.engine.semantic.overall import select_overall_domains
from app.engine.services.applied_guidance import direction_advice, state_basis
from app.engine.services.annual_copy import seed_from
from app.engine.services import love_copy as copy

LOVE_NARRATIVE_VERSION = "love-4tier-v1"

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
# 3단 계산: 월별 흐름 점수 (유료 전용). 점수 규칙은 career 와 같다.
#   join +2 · recovery +1 · base 0 · mixed -1 · change -2  (mode 이름만 보고 정한 해석)
# ---------------------------------------------------------------------------
def _month_candidate(selection: dict):
    primary = set(selection.get("primary_domains") or ())
    pool = [c for c in selection.get("selected", ()) if c["domain"] in _MONTH_DOMAINS]
    pool.sort(key=lambda c: (c["domain"] not in primary, _MONTH_DOMAINS.index(c["domain"])))
    return pool[0] if pool else None


def _month_scores(core: MyeongriCoreResult, year: int) -> tuple[dict[int, int], dict[int, dict]]:
    birth = to_solar(core.input.birth_date, core.input.calendar_type, core.input.is_leap_month)
    scores: dict[int, int] = {}
    details: dict[int, dict] = {}
    for month in range(1, 13):
        target = date(year, month, 15)
        if target < birth:
            if (year, month) < (birth.year, birth.month):
                continue
            target = birth
        timing, _, _ = calculate_timing(core.input, core.natal_facts.pillars, target_date=target)
        selection = select_overall_domains(core, "monthly", timing=timing)
        cand = _month_candidate(selection)
        mode = cand.get("mode") if cand else None
        scores[month] = copy.MODE_SCORE.get(mode, 0)
        details[month] = dict(mode=mode, source_ids=list(cand["source_ids"]) if cand else [],
                              domain=cand["domain"] if cand else None)
    return scores, details


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
        block(3, "올해 관계의 타이밍", copy.TEASER_TIER3)
        + block(4, "다정한 관계 3원칙", copy.TEASER_TIER4)
        + f'<a href="{copy.PAYWALL_HREF}" data-paywall-cta="theme-love" style="display:inline-block;margin-top:6px;'
          'padding:10px 16px;border-radius:10px;background:#2D6A4F;color:#fff;font-weight:700;text-decoration:none;">'
          f'{escape(copy.cta_label())}</a>')


def _unlocked_html(months: list[dict], bullets: list[str], year: int) -> str:
    if months:
        rows = "".join(
            f'<li data-love-month="{m["month"]}" data-month-kind="{m["kind"]}">'
            f'<strong>{m["month"]}월 · {escape(m["label"])}</strong><br>{escape(m["text"])}</li>'
            for m in months)
        body = f'<ul style="padding-left:18px;">{rows}</ul>'
    else:
        body = f'<p data-love-month="none">{escape(copy.NO_INFLECTION)}</p>'
    tier3 = (f'<section data-love-tier="3" data-paywall="unlocked"><h2>올해 관계의 타이밍</h2>'
             f'<p class="reading-caption">{year}년 각 달 15일의 절기 월주를 기준으로 짚었습니다. 상대의 선택이나 특정 사건을 예측한 것은 아닙니다.</p>'
             f'{body}</section>')
    items = "".join(f'<li data-love-action="{i}">{escape(b)}</li>' for i, b in enumerate(bullets, start=1))
    tier4 = f'<section data-love-tier="4" data-paywall="unlocked"><h2>다정한 관계 3원칙</h2><ol>{items}</ol></section>'
    return tier3 + tier4


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
    year = year or date.today().year

    counts = Counter(item["ten_god"] for item in query["natal"]["focused_ten_gods"])
    relationships = query["natal"]["relationships"]
    group = copy.lead_group(counts)
    birth = to_solar(core.input.birth_date, core.input.calendar_type, core.input.is_leap_month)
    seed = seed_from(birth.isoformat(), "love", safe_status, year)

    t1 = copy.compose_tier1(group, safe_status)
    t2 = copy.compose_tier2(group, seed)

    evidence_summary = dict(
        natal=dict(lead_group=group, status=safe_status,
                   ten_gods={_TEN_GOD.get(k, k): v for k, v in counts.items()}),
        copy_ids=dict(tier1=group, tier2=[b["title"] for b in t2]),
    )

    if unlocked:
        scores, details = _month_scores(core, year)
        months = copy.compose_tier3(copy.choose_inflections(scores), safe_status, seed)
        bullets = copy.compose_tier4(group, safe_status)
        gated = _unlocked_html(months, bullets, year)
        evidence_summary["months"] = [
            dict(month=m["month"], kind=m["kind"], **details.get(m["month"], {})) for m in months]
        advice = copy.sanitize(direction_advice(query["applied_state"], "love", ""))
        evidence_extra = f'<p>{escape(advice)}</p>' if advice else ""
    else:
        gated = _locked_html()
        evidence_extra = ""

    summary = copy.sanitize(_natal_relationship_summary(relationships))
    evidence = (
        '<details class="reading-evidence"><summary>이 풀이의 근거 · 명리 용어 포함</summary>'
        f'<h4>관계의 구조 · {escape(safe_status)}</h4><h5>원국의 관계 작용</h5>'
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
