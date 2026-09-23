"""Evidence-backed annual reader with a separate, reviewed conversational voice."""
from __future__ import annotations

from datetime import date
from html import escape

from app.engine.core.models import MyeongriCoreResult
from app.engine.timing import calculate_timing
from app.engine.calendar import to_solar
from app.engine.semantic.overall import select_overall_domains, OVERALL_VERSION
from app.engine.services.annual_editorial import (
    NARRATIVE_VERSION, GROUPS, ROLE_NAMES, ROLES, FALLBACK_ROLE,
    GENERAL_TITLES, MONTH_ADVICE, MONTH_MODE, OVERVIEW, role_family, scene,
)
from app.engine.services.reading_editorial import DETAIL, traits

SECONDARY = {
    "relationships": "자신의 경험을 다른 사람과 나누는 일도 중요합니다. 누군가 비슷한 일을 시작한다면 그동안 익힌 방법이나 시행착오를 들려주세요. 반대로 막히는 일이 생기면 도움을 구해보세요. 모든 답을 혼자 찾아야 하는 것은 아닙니다.",
    "money": "하고 싶은 일을 오래 이어가려면 비용도 함께 살펴야 합니다. 시작할 때 들어가는 돈뿐 아니라 계속 유지할 때의 부담도 적어보세요. 쓸 수 있는 범위를 정해두면 기대가 커져도 무리한 선택을 줄일 수 있습니다.",
    "work": "이런 선택은 일을 맡고 진행하는 방식과도 이어집니다. 좋은 결과를 내고 싶다면 무엇을 언제까지 마칠지 먼저 정해보세요. 함께하는 사람이 있다면 서로 기대하는 결과까지 맞춰두는 편이 좋습니다.",
    "love": "바쁜 가운데서도 가까운 사람과 마음을 나누는 시간은 챙겨주세요. 하고 싶은 이야기나 함께할 일이 있다면 먼저 꺼내보세요. 상대가 알아주기만 기다리지 않고 직접 표현할 때 서로를 이해하기 쉽습니다.",
    "wellbeing": "계획을 이어가려면 쉬는 시간도 필요합니다. 새로운 일을 더할 때는 기존 일정에서 무엇을 줄일지 함께 생각해 보세요. 시간이 모자랄 때마다 잠과 식사를 미루는 방식으로 버티지는 마세요.",
    "learning": "직접 해보면서 부족한 점이 보이면 그 부분을 배워보세요. 처음부터 모든 것을 알아야 하는 것은 아닙니다. 해보고 질문하고 다시 적용하는 과정을 반복하면 자신에게 필요한 공부도 분명해집니다.",
    "enjoyment": "성과와 상관없이 즐길 수 있는 일도 하나쯤 가져보세요. 잠깐이라도 좋아하는 활동을 직접 해보면 무엇이 자신에게 즐거운지 알 수 있습니다. 잘해야 한다는 부담 때문에 시작을 미룰 필요는 없어요.",
    "self": "그 과정에서도 자신이 원하는 것은 분명히 해주세요. 상대의 의견을 듣는 것과 모든 결정을 맡기는 것은 다릅니다. 함께 맞출 부분과 스스로 정할 부분을 나누면 불필요하게 마음을 쓰는 일이 줄어듭니다.",
    "change": "생활 환경을 바꾸는 선택까지 이어진다면 실제 조건을 따로 확인해 보세요. 이동 시간과 유지 비용을 알아보고, 지금의 생활에서 꼭 지키고 싶은 부분도 생각해 두는 편이 좋습니다.",
}
CLOSING = {
    "enjoyment": "올해는 얼마나 많은 일을 했는지보다 하고 싶던 일을 실제로 해봤는지가 더 중요합니다. 미뤄둔 활동을 시작하거나 해오던 작업을 마무리하는 것부터 해보세요. 직접 해본 경험이 쌓이면 앞으로 더 해보고 싶은 일도 분명해질 거예요.",
    "work": "올해는 모든 일을 잘하려고 애쓰기보다 잘할 수 있는 일에 힘을 모아보세요. 해낸 일은 분명히 알리고 그에 맞는 대우도 이야기하는 겁니다. 바쁘게만 보낸 해가 아니라 자신의 경험과 성과가 남는 해로 만들어보세요.",
    "money": "올해는 더 많이 얻는 것만큼 이미 가진 것을 잘 관리하는 데 의미를 두세요. 정산할 일 하나, 줄일 비용 하나부터 챙겨보면 됩니다. 눈에 보이는 변화가 작더라도 직접 관리할 수 있는 부분을 늘리는 것이 출발점입니다.",
    "relationships": "올해는 혼자 잘해내려는 마음을 조금 내려놓아도 좋겠습니다. 필요한 도움은 구하고 자신이 잘하는 일은 나눠주세요. 서로에게 무리 없는 방식으로 도움을 주고받을 때 관계도 편안해집니다.",
    "love": "올해는 상대의 마음을 오래 짐작하기보다 자신의 마음을 솔직하게 전해보세요. 함께할 시간을 만들고 불편한 점도 차분히 이야기하는 겁니다. 자신과 상대 모두에게 편안한 관계를 만들어가는 데 집중하면 좋겠습니다.",
    "wellbeing": "올해는 일정을 더 채우기보다 편안하게 이어갈 수 있는 생활을 만들어보세요. 바쁠 때도 지킬 작은 습관 하나부터 시작하면 됩니다. 쉴 시간을 지키는 것도 자신에게 필요한 일을 해내는 방법입니다.",
    "learning": "올해의 배움은 직접 해본 경험으로 남겨보세요. 많은 자료를 모으는 것보다 작은 결과 하나를 완성하는 데 의미를 두는 겁니다. 처음보다 무엇을 더 잘하게 됐는지 스스로 확인할 수 있으면 충분히 좋은 출발입니다.",
    "self": "올해는 남의 기대에 맞추는 일과 자신이 원하는 일을 구분해 보세요. 선택의 이유를 스스로 설명할 수 있다면 다른 의견을 들어도 덜 흔들립니다. 작은 결정부터 자신에게 맞는 기준을 지켜가면 좋겠습니다.",
    "change": "올해는 무엇을 바꿀지와 무엇을 지킬지를 함께 정해보세요. 새로운 환경에서도 자신에게 필요한 생활을 이어갈 수 있어야 합니다. 조급하게 모든 것을 바꾸기보다 확인한 조건 안에서 한 걸음씩 움직여보세요.",
}


def _paragraphs(values):
    return "".join(f"<p>{escape(value)}</p>" for value in values)


def _candidate(selection, domain):
    return next((c for c in selection["candidates"] if c["domain"] == domain), None)


def _basis(candidate):
    return {
        "kind": "scoped_interpretation" if candidate else "general_guidance",
        "source_ids": list(candidate["source_ids"]) if candidate else [],
        "mode": candidate.get("mode", "base") if candidate else None,
    }


def _domain_readings(selection, *, monthly=False):
    result = []
    family = role_family(selection.get("focal_god"))
    for domain, label in GROUPS:
        candidate = _candidate(selection, domain)
        if monthly:
            mode = candidate.get('mode') if candidate else None
            paragraphs = [MONTH_MODE.get((domain, mode), MONTH_ADVICE[family][domain])]
        else:
            paragraphs = [scene(candidate)] if candidate else []
            paragraphs.extend(DETAIL[domain])
        result.append(dict(domain=domain, label=label, title=GENERAL_TITLES[domain],
                           paragraphs=paragraphs, **_basis(candidate)))
    return result


def _annual_reading(selection, natal, name):
    role = ROLES.get(selection.get("focal_god"), FALLBACK_ROLE)
    selected = selection["selected"]
    primary = [c for c in selected if c['domain'] in selection['primary_domains']]
    lead = OVERVIEW[primary[0]['domain']] if primary else (role[0], role[1])
    opening = f"올해는 {name}님이 " + lead[1] if primary else f"{name}님, " + lead[1]
    # Complete a thought before introducing the next subject. Calculation
    # explanations belong in evidence, not between user-facing paragraphs.
    paragraphs = [opening, *traits(selection.get("focal_god"))[:2]]
    for candidate in selected:
        if primary and candidate is primary[0]:
            continue
        paragraphs.append(SECONDARY[candidate['domain']])
    if primary and primary[0].get('mode') in {'join', 'change', 'mixed', 'recovery'}:
        paragraphs.append(scene(primary[0]))
    paragraphs.append(role[3])
    paragraphs.append(CLOSING.get(primary[0]['domain'] if primary else 'self', CLOSING['self']))
    return dict(title=lead[0], paragraphs=paragraphs,
                source_ids=sorted({s for c in selected for s in c["source_ids"]}),
                domains=_domain_readings(selection))


def _monthly_reading(selection, annual_selection, month, name):
    role = ROLES.get(selection.get("focal_god"), FALLBACK_ROLE)
    primary = [c for c in selection["selected"] if c["domain"] in selection["primary_domains"]]
    paragraphs = [role[2], traits(selection.get("focal_god"))[1]]
    paragraphs.extend(scene(c) for c in primary)
    paragraphs.append(role[3])
    return dict(title=role[0], paragraphs=paragraphs,
                source_ids=sorted({s for c in primary for s in c["source_ids"]}),
                domains=_domain_readings(selection, monthly=True))
def _evidence_html(selection, timing, representative):
    labels = " · ".join(c["label"] for c in selection["selected"]) or "특정 분야로 좁히지 않은 생활 조언"
    role = ROLE_NAMES.get(selection.get("focal_god"), "미정")
    pillar = timing.annual if selection["scope"] == "annual" else timing.monthly
    ganji = pillar.get("pillar", {}).get("ganji", "")
    return (
        '<details class="annual-evidence"><summary>이 풀이의 근거</summary>'
        f'<p>{escape(representative.isoformat())} 대표값 · {escape(ganji)} · {escape(role)}. '
        f'계산에서 살핀 주제: {escape(labels)}.</p>'
        '<p>원국과 해당 기간까지의 대운·세운·월운을 범위에 맞춰 살폈습니다. '
        '합·충은 관계와 조건을 살필 단서이며, 좋은 일이나 나쁜 사건을 보장하는 뜻은 아닙니다.</p></details>')


def _render_domains(rows, *, monthly=False):
    parts = []
    for row in rows:
        key = "data-month-domain" if monthly else "data-report-domain"
        heading = "h5" if monthly else "h3"
        title = row["label"] if monthly else row["label"] + " · " + row["title"]
        parts.append(
            f'<section {key}="{row["domain"]}" data-reading-kind="{row["kind"]}" class="annual-domain">'
            f'<{heading} data-toc-label="{escape(row["label"], quote=True)}">{escape(title)}</{heading}>'
            f'{_paragraphs(row["paragraphs"])}</section>')
    return "".join(parts)


def build_annual_overall_report(core: MyeongriCoreResult, user_name: str, year: int) -> dict:
    """Keep calculation/evidence unchanged; render the approved annual structure."""
    name = user_name or "회원"
    birth_date = to_solar(core.input.birth_date, core.input.calendar_type, core.input.is_leap_month)
    representative = max(date(year, 7, 1), birth_date)
    if representative.year != year:
        raise ValueError("출생 전 연도의 운세는 생성할 수 없습니다.")
    timing, _, _ = calculate_timing(core.input, core.natal_facts.pillars, target_date=representative)
    selection = select_overall_domains(core, "annual", timing=timing)
    natal = select_overall_domains(core, "natal")
    reading = _annual_reading(selection, natal, name)
    months = []
    cards = []
    for month in range(1, 13):
        target = date(year, month, 15)
        if target < birth_date:
            if (year, month) < (birth_date.year, birth_date.month):
                cards.append(f'<article data-report-month="{month}" class="annual-month" style="border-left:4px solid #2D6A4F"><h4>{month}월 · 출생 전 기간</h4></article>')
                continue
            target = birth_date
        month_timing, _, _ = calculate_timing(core.input, core.natal_facts.pillars, target_date=target)
        month_selection = select_overall_domains(core, "monthly", timing=month_timing)
        month_reading = _monthly_reading(month_selection, selection, month, name)
        months.append(dict(month=month, representative_date=target.isoformat(),
                           interpretation=month_selection, reading=month_reading))
        cards.append(
            f'<article data-report-month="{month}" class="annual-month" style="border-left:4px solid #2D6A4F">'
            f'<h4>{month}월 · {escape(month_reading["title"])}</h4>'
            f'{_paragraphs(month_reading["paragraphs"])}'
            f'{_render_domains(month_reading["domains"], monthly=True)}'
            f'{_evidence_html(month_selection, month_timing, target)}</article>')
    ganji = timing.annual["pillar"]["ganji"]
    content = (
        f'<div class="annual-reading" data-overall-version="{OVERALL_VERSION}" '
        f'data-narrative-version="{NARRATIVE_VERSION}" data-report-year="{year}">'
        '<section class="annual-overview"><h3>올해 총운</h3>'
        f'<h4>{escape(reading["title"])}</h4>{_paragraphs(reading["paragraphs"])}'
        f'{_evidence_html(selection, timing, representative)}</section>'
        '<p class="annual-note">분야별로 계산에서 드러나는 주제와 생활 조언을 구분해 읽어보세요. '
        '직업이나 관계의 예시는 현재 상황에 맞는 부분을 참고하면 됩니다.</p>'
        f'{_render_domains(reading["domains"])}'
        '<h3>12개월 흐름</h3>'
        '<p class="annual-note">각 달 15일의 절기 월주를 대표값으로 사용했습니다. '
        '달력의 1일을 운의 전환일로 보거나 특정 사건의 날짜를 정한 것은 아닙니다.</p>'
        + "".join(cards) +
        '<p class="annual-note">정통 명리의 원국·대운·세운·월운을 근거로 한 해석이며, '
        '별도의 토정비결 괘 계산과는 구분됩니다. 실제 건강 상태와 중요한 결정은 '
        '현실의 정보와 전문가의 판단을 함께 확인해 주세요.</p></div>')
    return dict(
        title=f"{year}년 {escape(name)}님의 올해·월별 운세",
        content=content, engine_version=OVERALL_VERSION,
        narrative_version=NARRATIVE_VERSION, report_year=year,
        evidence_summary=dict(annual=selection, natal=natal, months=months),
        reading=reading,
    )
