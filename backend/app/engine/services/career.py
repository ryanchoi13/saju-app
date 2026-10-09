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
from app.engine.timing import calculate_timing
from app.engine.semantic import build_service_query
from app.engine.semantic.overall import select_overall_domains
from app.engine.services.applied_guidance import direction_advice, state_basis
from app.engine.services.annual_copy import sanitize_paragraph, seed_from
from app.engine.services import career_copy as copy

CAREER_NARRATIVE_VERSION = "career-4tier-v1"

_TEN_GOD = {
    "peer": "비견", "rob_wealth": "겁재", "eating_god": "식신",
    "hurting_officer": "상관", "direct_wealth": "정재",
    "indirect_wealth": "편재", "direct_officer": "정관",
    "seven_killings": "편관", "direct_resource": "정인",
    "indirect_resource": "편인",
}
# 월별 흐름에서 '일' 신호로 읽을 도메인. 직장·이직은 일과 배움, 사업·창업은 일과 돈.
# (도메인 → 테마 매핑과 같은 결의 가정이며, 엔진의 실제 의미와 다르면 여기를 고친다.)
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
def _month_candidate(selection: dict, track: str):
    domains = _TRACK_DOMAINS[track]
    primary = set(selection.get("primary_domains") or ())
    pool = [c for c in selection.get("selected", ()) if c["domain"] in domains]
    pool.sort(key=lambda c: (c["domain"] not in primary, domains.index(c["domain"])))
    return pool[0] if pool else None


def _month_scores(core: MyeongriCoreResult, year: int, track: str) -> tuple[dict[int, int], dict[int, dict]]:
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
        cand = _month_candidate(selection, track)
        mode = cand.get("mode") if cand else None
        scores[month] = copy.MODE_SCORE.get(mode, 0)
        details[month] = dict(mode=mode, source_ids=list(cand["source_ids"]) if cand else [],
                              domain=cand["domain"] if cand else None)
    return scores, details


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


def _tier1_html(t1: dict) -> str:
    return (
        '<section data-career-tier="1" data-paywall="free"><h2>기질 진단</h2>'
        f'<h3>{escape(t1["headline"])}</h3><p>{escape(t1["body"])}</p></section>')


def _tier2_html(boxes: list[dict]) -> str:
    items = "".join(
        f'<div data-career-trap="{i}" style="{_BOX}">'
        f'<strong>{escape(b["title"])}</strong><p style="margin:4px 0 0;">{escape(b["text"])}</p></div>'
        for i, b in enumerate(boxes, start=1))
    return (
        '<section data-career-tier="2" data-paywall="free"><h2>일할 때 자주 빠지는 함정 2가지</h2>'
        f'<div style="display:grid;gap:8px;">{items}</div></section>')


def _boundary_html() -> str:
    return '<hr data-paywall-boundary="career" style="border:0;border-top:1px dashed #94A3B8;margin:18px 0;">'


def _locked_html(n_months: int) -> str:
    def block(tier: int, title: str, teaser: str) -> str:
        return (
            f'<section data-career-tier="{tier}" data-paywall="locked" data-locked="true" '
            'style="border:1px dashed #94A3B8;border-radius:12px;background:#F8FAFC;padding:14px;margin-bottom:8px;">'
            f'<div style="font-size:12px;color:#64748B;font-weight:800;">🔒 {escape(copy.LOCK_LABEL)}</div>'
            f'<h2 style="margin:4px 0 0;">{escape(title)}</h2>'
            f'<p data-career-teaser="{tier}" style="margin:6px 0 0;">{escape(teaser)}</p>{_SKELETON}</section>')
    return (
        block(3, "올해 일의 타이밍", copy.teaser_tier3(n_months))
        + block(4, "커리어를 지키는 실천 3원칙", copy.TEASER_TIER4)
        + f'<a href="{copy.PAYWALL_HREF}" data-paywall-cta="theme-career" style="display:inline-block;margin-top:6px;'
          'padding:10px 16px;border-radius:10px;background:#2D6A4F;color:#fff;font-weight:700;text-decoration:none;">'
          f'{escape(copy.cta_label())}</a>')


def _unlocked_html(months: list[dict], bullets: list[str], year: int) -> str:
    if months:
        rows = "".join(
            f'<li data-career-month="{m["month"]}" data-month-kind="{m["kind"]}">'
            f'<strong>{m["month"]}월 · {escape(m["label"])}</strong><br>{escape(m["text"])}</li>'
            for m in months)
        body = f'<ul style="padding-left:18px;">{rows}</ul>'
    else:
        body = f'<p data-career-month="none">{escape(copy.NO_INFLECTION)}</p>'
    tier3 = (f'<section data-career-tier="3" data-paywall="unlocked"><h2>올해 일의 타이밍</h2>'
             f'<p class="reading-caption">{year}년 각 달 15일의 절기 월주를 기준으로 짚었습니다. 특정 사건의 날짜를 예측한 것은 아닙니다.</p>'
             f'{body}</section>')
    items = "".join(f'<li data-career-action="{i}">{escape(b)}</li>' for i, b in enumerate(bullets, start=1))
    tier4 = f'<section data-career-tier="4" data-paywall="unlocked"><h2>커리어를 지키는 실천 3원칙</h2><ol>{items}</ol></section>'
    return tier3 + tier4


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
    year = year or date.today().year

    focused = query["natal"]["focused_ten_gods"]
    counts = Counter(item["ten_god"] for item in focused)
    strength = query["synthesis"].get("strength_state")
    group = copy.lead_group(counts)
    birth = to_solar(core.input.birth_date, core.input.calendar_type, core.input.is_leap_month)
    seed = seed_from(birth.isoformat(), "career", safe_status, year)

    t1 = copy.compose_tier1(group, track, strength)
    t2 = copy.compose_tier2(group, seed)

    evidence_summary = dict(
        natal=dict(lead_group=group, strength=strength, status=safe_status,
                   ten_gods={_TEN_GOD.get(k, k): v for k, v in counts.items()}),
        copy_ids=dict(tier1=group, tier2=[b["title"] for b in t2]),
    )

    if unlocked:
        scores, details = _month_scores(core, year, track)
        months = copy.compose_tier3(copy.choose_inflections(scores), track, seed)
        bullets = copy.compose_tier4(group, safe_status)
        gated = _unlocked_html(months, bullets, year)
        evidence_summary["months"] = [dict(month=m["month"], kind=m["kind"], **details.get(m["month"], {})) for m in months]
        advice = _clean(direction_advice(query["applied_state"], "career", ""), "career.evidence")
        evidence_extra = f'<p>{escape(advice)}</p>' if advice else ""
    else:
        # 티저의 '몇 곳'은 정확히 알려면 월별 계산이 필요하다. 미결제 상태에서는 계산하지 않고
        # 숫자 없이 일반 문구를 쓴다. (숫자로 호기심을 키우고 싶으면 서버 캐시로 계산해 넘기는 쪽이 낫다.)
        gated = _locked_html(0)
        evidence_extra = ""

    evidence = (
        '<details class="reading-evidence"><summary>이 풀이의 근거 · 명리 용어 포함</summary>'
        f'<p>{escape(safe_status)} 기준 · {escape(_count_summary(counts, track))}</p>{evidence_extra}</details>')

    content = (
        f'<div class="theme-reading" data-theme="career" data-narrative-version="{CAREER_NARRATIVE_VERSION}" '
        f'data-copy-version="{copy.COPY_VERSION}" data-unlocked="{str(unlocked).lower()}">'
        + _tier1_html(t1) + _tier2_html(t2)
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
