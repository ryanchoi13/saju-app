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
    DETAIL, GENERAL_TITLES, MONTH_ADVICE, MONTH_MODE, OVERVIEW, role_family, scene,
)


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
    paragraphs = [opening]
    # Natal context is explicitly an interpretation, never invented biography.
    shared = sorted(set(natal["primary_domains"]) & set(selection["primary_domains"]))
    if shared:
        shared_labels = " · ".join(c["label"] for c in selected if c["domain"] in shared)
        paragraphs.append(
            f"이렇게 읽는 이유는 기본 사주에서 살피는 {shared_labels}의 주제가 올해 흐름에도 이어지기 때문입니다. "
            "완전히 새로운 답을 찾기보다 그동안 어떤 방식이 자신에게 잘 맞았는지 돌아보세요. "
            "계속 살릴 부분과 조금 바꿔볼 부분을 나누면 올해의 선택도 구체적으로 정하기 좋습니다.")
    else:
        paragraphs.append(
            "기본 사주에서 중심이 되는 주제와 올해 먼저 살필 주제는 같지 않을 수 있습니다. "
            "익숙한 방식만 고집하기보다 지금 상황에 필요한 방법을 골라보세요. "
            "평소와 다른 선택을 하더라도 감당할 시간과 여유가 있는지 함께 확인하면 좋겠습니다.")
    # Use different elaboration in domain chapters; do not copy their paragraphs
    # into the overview. Preserve other tied/independent subjects explicitly.
    paragraphs.append(role[1])
    for candidate in selected:
        if primary and candidate is primary[0]:
            continue
        paragraphs.append(OVERVIEW[candidate['domain']][1])
    if primary and primary[0].get('mode') in {'join', 'change', 'mixed', 'recovery'}:
        paragraphs.append(scene(primary[0]))
    paragraphs.append(role[3])
    paragraphs.append(
        "한 해의 모든 일을 한꺼번에 정할 필요는 없어요. 지금 가장 신경 쓰이는 분야부터 읽어보세요. "
        "바로 해볼 일 하나와 미뤄도 되는 일 하나를 구분하면 계획을 세우기가 쉬워집니다. "
        "월별 풀이에서는 같은 주제가 그달에 어떻게 이어지는지도 함께 살펴보면 좋겠습니다.")
    return dict(title=lead[0], paragraphs=paragraphs,
                source_ids=sorted({s for c in selected for s in c["source_ids"]}),
                domains=_domain_readings(selection))


def _monthly_reading(selection, annual_selection, month, name):
    role = ROLES.get(selection.get("focal_god"), FALLBACK_ROLE)
    primary = [c for c in selection["selected"] if c["domain"] in selection["primary_domains"]]
    paragraphs = [f"{month}월 {name}님의 풀이입니다. " + role[2]]
    annual_primary = set(annual_selection["primary_domains"])
    if primary:
        labels = " · ".join(c["label"] for c in primary)
        linkage = (f"올해 살피는 주제 가운데 이번 달에는 {labels}에 조금 더 집중해 보세요."
                   if annual_primary & {c["domain"] for c in primary}
                   else f"올해 전체 흐름과 함께 이번 달에는 {labels}도 살펴볼 주제로 드러납니다.")
        paragraphs.append(linkage + " " + " ".join(scene(c) for c in primary))
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
        '합·충은 관계와 조건을 살필 단서이며, 좋은 일이나 나쁜 사건을 보장하는 뜻은 아닙니다. '
        '생활 조언으로 표시한 분야에는 특정한 사건이나 길흉 판단을 덧붙이지 않았습니다.</p></details>')


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
