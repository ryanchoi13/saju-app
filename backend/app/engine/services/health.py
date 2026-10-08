"""건강·웰빙 테마운 (4단 구조 · 2,900원 페이월). 의료 서비스가 아니라 '생활 리듬' 풀이다.

1단 에너지 흐름 진단 · 2단 컨디션 함정 → 무료
3단 바이오리듬 타이밍 · 4단 생활 활력 3원칙 → is_unlocked=True 일 때만 본문을 만든다.

보안 원칙은 career.py / love.py 와 같다.
- 잠금 상태에서는 3·4단 '본문'을 HTML, evidence_summary, 반환 dict 어디에도 싣지 않고 월별 계산도 하지 않는다.
- is_unlocked 는 키워드 전용이며 `is True` 로만 비교한다. (status 계열 문자열이 참값으로 읽혀 전부 열리는 사고 방지)
- is_unlocked 는 서버가 결제 내역으로 계산해 넘겨야 하며, 해제된 결과를 캐시할 때는 키에 해제 여부를 넣을 것.

의료 주장 금지:
- build_service_query 가 medical_claim_allowed 를 False 로 주지 않으면 ValueError (기존 가드 유지).
- 카피 은행은 tests/test_health.py 가 find_medical_flagged 로 전수 검사하고,
  엔진 밖에서 온 문장은 여기서 health_copy.sanitize 로 한 번 더 거른다.
"""

from __future__ import annotations

from datetime import date
from html import escape

from app.engine.core.models import MyeongriCoreResult
from app.engine.calendar import to_solar
from app.engine.timing import calculate_timing
from app.engine.semantic import build_service_query
from app.engine.semantic.overall import select_overall_domains
from app.engine.semantic.applied import recommended_directions
from app.engine.services.applied_guidance import state_basis
from app.engine.services.annual_copy import seed_from
from app.engine.services import health_copy as copy

HEALTH_NARRATIVE_VERSION = "health-4tier-v1"

_STRENGTH = {
    "extremely_weak": "매우 신약", "weak": "신약",
    "balanced": "중화에 가까움", "strong": "신강",
    "extremely_strong": "매우 신강",
}
_CLIMATE = {
    "very_cold_wet": "매우 차고 습한 환경", "cold_wet": "차고 습한 환경",
    "cool_balanced": "서늘하나 한난조습이 비교적 고른 환경",
    "cool_dry": "서늘하고 건조한 환경", "mild_wet": "온화하나 습한 환경",
    "mild_balanced": "한난조습이 비교적 고른 환경",
    "warm_dry": "따뜻하고 건조한 환경", "hot_dry": "덥고 건조한 환경",
    "very_hot_dry": "매우 덥고 건조한 환경",
}
_BOTTLENECK = {
    "structural_damage": "생활의 기본 틀이 외부 변화와 충돌할 때 리듬이 흔들리기 쉬운 구조",
    "climate_extreme": "한난조습의 치우침을 먼저 완화해야 하는 구조",
    "conflict": "여러 요구와 역할이 동시에 경쟁해 소모가 커지기 쉬운 구조",
    "blocked_flow": "활동과 회복의 전환이 매끄럽지 않아 일정 조절이 필요한 구조",
    "bound_element": "한 역할이나 관계에 에너지가 오래 묶이지 않도록 점검할 구조",
    "unstable_root": "기초 체력·시간·도움 자원을 먼저 확보해야 하는 구조",
    "deficiency": "무리한 확장보다 회복 여력을 우선해야 하는 구조",
    "excess": "강한 추진력을 규칙적인 활동과 휴식으로 나누어 써야 하는 구조",
    "no_critical_bottleneck": "현재 규칙에서 우선순위가 높은 구조적 병목은 확인되지 않음",
}
_OPERATION = {
    "warm": "차갑고 정체되는 생활 패턴을 피하고 일정한 수면·식사·움직임으로 리듬을 덥히기",
    "cool": "과열된 일정과 긴장을 오래 끌지 않고 활동 사이에 회복 시간을 두기",
    "moisten": "건조한 환경과 과도한 소모를 피하고 수분·휴식 환경을 꾸준히 관리하기",
    "stabilize": "불규칙한 생활을 줄이고 가벼운 활동과 휴식의 시간을 일정하게 맞추기",
    "support": "해야 할 일을 늘리기 전에 수면·식사·도움받을 자원을 먼저 확보하기",
    "drain": "쌓인 에너지를 무리 없는 규칙적 활동과 실제 결과물로 분산하기",
    "mediate": "서로 충돌하는 일정 사이에 전환·정리 시간을 두어 과부하를 줄이기",
    "protect": "생활의 기본 루틴을 먼저 지키고 큰 변화는 한 번에 겹치지 않게 하기",
    "resolve_conflict": "동시에 맡은 역할의 우선순위를 정하고 불필요한 부담을 덜어내기",
    "release_binding": "한 역할에 시간과 신경이 오래 묶이지 않는지 주기적으로 점검하기",
    "preserve_balance": "현재 유지되는 균형을 무리한 보완이나 극단적인 습관으로 흔들지 않기",
}
# 월별 흐름에서 '컨디션' 신호로 읽을 도메인. (엔진의 실제 의미와 다르면 여기를 고친다.)
_MONTH_DOMAINS = ("wellbeing", "enjoyment")


def _uncertainty(core: MyeongriCoreResult) -> str:
    if not core.uncertainty.time_unknown:
        return ""
    return """
    <div style="background:#FFF7ED;border:1px solid #FED7AA;padding:12px 14px;border-radius:12px;margin-top:12px;">
      <div style="font-size:13px;font-weight:800;color:#9A3412;">생시 미상 안내</div>
      <p style="font-size:12.5px;color:#7C2D12;margin:5px 0 0;line-height:1.65;">시주에 따라 기운의 세기와 일부 구조가 달라질 수 있어, 여러 시주에서 공통으로 유지되는 환경과 흐름을 중심으로 설명했습니다.</p>
    </div>"""


def _operation_lines(query: dict) -> list[str]:
    """유료 근거 박스용. 엔진 방향 라벨을 문장으로 옮기되 의학 표현이 들면 건너뛴다."""
    operations = recommended_directions(query["applied_state"])
    labels = list(dict.fromkeys(
        _OPERATION[item["operation"]] for item in operations if item.get("operation") in _OPERATION))
    return [x for x in labels[:3] if not copy.find_medical_flagged(x)]


# ---------------------------------------------------------------------------
# 3단 계산: 월별 흐름 점수 (유료 전용). 점수 규칙은 career 와 같다.
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
        '<section data-health-tier="1" data-paywall="free"><h2>에너지 흐름 읽기</h2>'
        f'<h3>{escape(t1["headline"])}</h3><p>{escape(t1["body"])}</p></section>')


def _tier2_html(boxes: list[dict]) -> str:
    items = "".join(
        f'<div data-health-trap="{i}" style="{_BOX}">'
        f'<strong>{escape(b["title"])}</strong><p style="margin:4px 0 0;">{escape(b["text"])}</p></div>'
        for i, b in enumerate(boxes, start=1))
    return (
        '<section data-health-tier="2" data-paywall="free"><h2>지칠 때 반복하기 쉬운 습관 2가지</h2>'
        f'<div style="display:grid;gap:8px;">{items}</div></section>')


def _boundary_html() -> str:
    return ('<hr data-paywall-boundary="health" data-price="%d" '
            'style="border:0;border-top:1px dashed #94A3B8;margin:18px 0;">' % copy.PRICE_KRW)


def _locked_html() -> str:
    def block(tier: int, title: str, teaser: str) -> str:
        return (
            f'<section data-health-tier="{tier}" data-paywall="locked" data-locked="true" '
            'style="border:1px dashed #94A3B8;border-radius:12px;background:#F8FAFC;padding:14px;margin-bottom:8px;">'
            f'<div style="font-size:12px;color:#64748B;font-weight:800;">🔒 {escape(copy.LOCK_LABEL)}</div>'
            f'<h2 style="margin:4px 0 0;">{escape(title)}</h2>'
            f'<p data-health-teaser="{tier}" style="margin:6px 0 0;">{escape(teaser)}</p>{_SKELETON}</section>')
    return (
        block(3, "올해 컨디션 타이밍", copy.TEASER_TIER3)
        + block(4, "생활 활력 3원칙", copy.TEASER_TIER4)
        + f'<a href="{copy.PAYWALL_HREF}" data-paywall-cta="theme-health" style="display:inline-block;margin-top:6px;'
          'padding:10px 16px;border-radius:10px;background:#2D6A4F;color:#fff;font-weight:700;text-decoration:none;">'
          f'{escape(copy.cta_label())}</a>')


def _unlocked_html(months: list[dict], bullets: list[str], year: int) -> str:
    if months:
        rows = "".join(
            f'<li data-health-month="{m["month"]}" data-month-kind="{m["kind"]}">'
            f'<strong>{m["month"]}월 · {escape(m["label"])}</strong><br>{escape(m["text"])}</li>'
            for m in months)
        body = f'<ul style="padding-left:18px;">{rows}</ul>'
    else:
        body = f'<p data-health-month="none">{escape(copy.NO_INFLECTION)}</p>'
    tier3 = (f'<section data-health-tier="3" data-paywall="unlocked"><h2>올해 컨디션 타이밍</h2>'
             f'<p class="reading-caption">{year}년 각 달 15일의 절기 월주를 기준으로 짚었습니다. 생활 리듬을 돌아보기 위한 흐름이며 몸의 상태를 말하는 것이 아닙니다.</p>'
             f'{body}</section>')
    items = "".join(f'<li data-health-action="{i}">{escape(b)}</li>' for i, b in enumerate(bullets, start=1))
    tier4 = f'<section data-health-tier="4" data-paywall="unlocked"><h2>생활 활력 3원칙</h2><ol>{items}</ol></section>'
    return tier3 + tier4


def build_lifetime_health_report(
    core: MyeongriCoreResult,
    user_name: str,
    *,
    is_unlocked: bool = False,
    year: int | None = None,
) -> dict:
    """Render non-medical lifestyle-rhythm guidance from the health query profile."""
    unlocked = is_unlocked is True
    query = build_service_query(core, "health")
    if query["constraints"].get("medical_claim_allowed") is not False:
        raise ValueError("건강 생활흐름 리포트는 의료 주장 금지 설정이 필요합니다.")
    name = escape(user_name or "회원")
    year = year or date.today().year

    strength = query["synthesis"].get("strength_state")
    climate_raw = (query["diagnostics"].get("climate") or {}).get("conclusion")
    pathology_raw = (query["diagnostics"].get("pathology") or {}).get("conclusion")
    climate = copy.climate_key(climate_raw)
    pathology = copy.pathology_key(pathology_raw)
    birth = to_solar(core.input.birth_date, core.input.calendar_type, core.input.is_leap_month)
    seed = seed_from(birth.isoformat(), "health", year)

    t1 = copy.compose_tier1(climate, strength, pathology)
    t2 = copy.compose_tier2(pathology, seed)

    evidence_summary = dict(
        natal=dict(strength=strength, climate=climate_raw, bottleneck=pathology_raw),
        copy_ids=dict(tier1=dict(climate=climate, pathology=pathology, strength=copy.strength_key(strength)),
                      tier2=[b["title"] for b in t2]),
    )

    evidence_extra = ""
    if unlocked:
        scores, details = _month_scores(core, year)
        months = copy.compose_tier3(copy.choose_inflections(scores), strength, seed)
        bullets = copy.compose_tier4(climate, strength)
        gated = _unlocked_html(months, bullets, year)
        evidence_summary["months"] = [
            dict(month=m["month"], kind=m["kind"], **details.get(m["month"], {})) for m in months]
        lines = _operation_lines(query)
        if lines:
            evidence_extra = "<p>" + "<br>".join(f"· {escape(x)}" for x in lines) + "</p>"
    else:
        gated = _locked_html()

    climate_text = _CLIMATE.get(climate_raw, "조후 환경 판정 보류")
    bottleneck_text = copy.sanitize(_BOTTLENECK.get(pathology_raw, "구조적 병목을 단정하기 어려운 상태"))
    evidence = (
        '<details class="reading-evidence"><summary>이 풀이의 근거 · 명리 용어 포함</summary>'
        '<h4>평생 생활 리듬의 구조</h4>'
        f'<p>{escape(_STRENGTH.get(strength, "판정 보류"))} · {escape(climate_text)}</p>'
        f'<h5>먼저 살필 기운의 병목</h5><p>{escape(bottleneck_text)}. {escape(copy.BOTTLENECK_NOTE)}</p>'
        f'{evidence_extra}</details>')

    content = (
        f'<div class="theme-reading" data-theme="health" data-narrative-version="{HEALTH_NARRATIVE_VERSION}" '
        f'data-copy-version="{copy.COPY_VERSION}" data-unlocked="{str(unlocked).lower()}">'
        + _tier1_html(t1) + _tier2_html(t2) + _boundary_html() + gated
        + evidence + _uncertainty(core)
        + f'<p class="reading-caption">{escape(copy.DISCLAIMER)}</p></div>')
    return {
        "analysis_basis": state_basis(query["applied_state"]),
        "title": f"{name}님 정통 명리 건강·웰빙 생활흐름",
        "content": content,
        "narrative_version": HEALTH_NARRATIVE_VERSION,
        "copy_version": copy.COPY_VERSION,
        "is_unlocked": unlocked,
        "evidence_summary": evidence_summary,
    }
