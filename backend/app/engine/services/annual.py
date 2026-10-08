"""Evidence-backed annual reader with a separate, reviewed conversational voice.

계산·근거(timing, select_overall_domains)는 그대로 두고, 사용자에게 보이는 문장만
달하 마스터 프롬프트 규격으로 만든다.

- 월별 풀이: Hero 테마 1개(약 60%) + Sub 한줄 노트 3개(약 40%)  (annual_copy.compose_month)
- 금기어: 카피 은행은 처음부터 금기어 없이 쓰였고, 엔진 밖에서 오는 문단은
  sanitize_paragraph 로 한 번 더 걸러 낸다.
- 매달 같은 면책 문구를 카드마다 붙이지 않고, 12개월 안내문에 한 번만 둔다.
"""
from __future__ import annotations

import logging
from datetime import date
from html import escape

from app.engine.core.models import MyeongriCoreResult
from app.engine.timing import calculate_timing
from app.engine.calendar import to_solar
from app.engine.semantic.overall import select_overall_domains, OVERALL_VERSION
from app.engine.services.annual_editorial import (
    NARRATIVE_VERSION, GROUPS, ROLE_NAMES, ROLES, FALLBACK_ROLE,
    GENERAL_TITLES, OVERVIEW, scene,
)
from app.engine.services.reading_editorial import DETAIL, traits
from app.engine.services.annual_copy import (
    COPY_VERSION, SCHEMA, THEME_KEYS, DOMAIN_TO_THEME,
    SECONDARY, CLOSING, CopyLedger, seed_from, flow_of, compose_month,
    validate_month, audit_year, sanitize_paragraph,
)

logger = logging.getLogger("dalha.annual")


# ---------------------------------------------------------------------------
# 공통 도우미
# ---------------------------------------------------------------------------
def _clean(text, where):
    """엔진 밖에서 온 문장에 금기어가 섞여 있으면 그 문장만 덜어낸다."""
    return sanitize_paragraph(text, fallback="", where=where)


def _paragraphs(values):
    return "".join(f"<p>{escape(value)}</p>" for value in values if value)


def _candidate(selection, domain):
    return next((c for c in selection["candidates"] if c["domain"] == domain), None)


def _basis(candidate):
    return {
        "kind": "scoped_interpretation" if candidate else "general_guidance",
        "source_ids": list(candidate["source_ids"]) if candidate else [],
        "mode": candidate.get("mode", "base") if candidate else None,
    }


# ---------------------------------------------------------------------------
# 연간 풀이 (문단 구성은 기존과 같고, 외부 문장만 걸러 낸다)
# ---------------------------------------------------------------------------
def _domain_readings(selection):
    result = []
    for domain, label in GROUPS:
        candidate = _candidate(selection, domain)
        raw = [scene(candidate)] if candidate else []
        raw.extend(DETAIL[domain])
        paragraphs = [p for p in (_clean(t, f"annual.domain.{domain}") for t in raw) if p]
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
    raw = [opening, *traits(selection.get("focal_god"))[:2]]
    for candidate in selected:
        if primary and candidate is primary[0]:
            continue
        raw.append(SECONDARY[candidate['domain']])
    if primary and primary[0].get('mode') in {'join', 'change', 'mixed', 'recovery'}:
        raw.append(scene(primary[0]))
    raw.append(role[3])
    raw.append(CLOSING.get(primary[0]['domain'] if primary else 'self', CLOSING['self']))
    paragraphs = [p for p in (_clean(t, "annual.overview") for t in raw) if p]
    return dict(title=lead[0], paragraphs=paragraphs,
                source_ids=sorted({s for c in selected for s in c["source_ids"]}),
                domains=_domain_readings(selection))


# ---------------------------------------------------------------------------
# 월별 풀이: Hero 1 + Sub 3
# ---------------------------------------------------------------------------
def _hero_theme(selection, month):
    """엔진이 짚은 분야에서 Hero 테마를 고른다. 근거가 없으면 달마다 돌아가며 고른다.

    우선순위: primary_domains → selected → candidates → 순환(THEME_KEYS[(month-1) % 4]).
    DOMAIN_TO_THEME 은 도메인 이름을 보고 추정한 매핑이라, 엔진 쪽 의미와 다르면 여기서 고쳐야 한다.
    Returns (theme, candidate_or_None).
    """
    primary = set(selection.get("primary_domains") or ())
    pools = (
        [c for c in selection.get("selected", ()) if c["domain"] in primary],
        list(selection.get("selected", ())),
        list(selection.get("candidates", ())),
    )
    for pool in pools:
        for c in pool:
            theme = DOMAIN_TO_THEME.get(c["domain"])
            if theme:
                return theme, c
    return THEME_KEYS[(month - 1) % len(THEME_KEYS)], None


def _theme_basis(selection, theme):
    """해당 테마에 속하는 후보들의 근거 id (Sub 노트의 근거 표기용)."""
    cands = [c for c in selection.get("candidates", ()) if DOMAIN_TO_THEME.get(c["domain"]) == theme]
    ids = sorted({s for c in cands for s in c["source_ids"]})
    return {
        "kind": "scoped_interpretation" if cands else "general_guidance",
        "source_ids": ids,
        "mode": cands[0].get("mode", "base") if cands else None,
    }


def _monthly_reading(selection, ledger, month):
    theme, cand = _hero_theme(selection, month)
    flow = flow_of(cand.get("mode") if cand else None)
    reading = compose_month(ledger, month, theme, flow)
    reading["hero"].update(_theme_basis(selection, theme))
    for sub in reading["subs"]:
        sub.update(_theme_basis(selection, sub["theme"]))
    reading["flow"] = flow
    return reading


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


def _render_domains(rows):
    parts = []
    for row in rows:
        title = row["label"] + " · " + row["title"]
        parts.append(
            f'<section data-report-domain="{row["domain"]}" data-reading-kind="{row["kind"]}" class="annual-domain">'
            f'<h3 data-toc-label="{escape(row["label"], quote=True)}">{escape(title)}</h3>'
            f'{_paragraphs(row["paragraphs"])}</section>')
    return "".join(parts)


def _render_month_card(month, target, reading, month_selection, month_timing):
    hero, subs = reading["hero"], reading["subs"]
    sub_items = "".join(
        f'<li data-month-theme="{s["theme"]}" data-reading-kind="{s["kind"]}">'
        f'<strong>{escape(s["label"])}</strong> {escape(s["note"])}</li>'
        for s in subs)
    return (
        f'<article data-report-month="{month}" data-flow="{reading["flow"]}" class="annual-month" '
        'style="border-left:4px solid #2D6A4F">'
        f'<h4>{month}월 · {escape(reading["headline"])}</h4>'
        f'<section data-month-theme="{hero["theme"]}" data-month-role="hero" '
        f'data-reading-kind="{hero["kind"]}" class="annual-hero">'
        f'<h5 data-toc-label="{escape(hero["label"], quote=True)}">{escape(hero["label"])}</h5>'
        f'<p>{escape(hero["body"])}</p></section>'
        f'<ul class="annual-subs" data-month-role="sub">{sub_items}</ul>'
        f'{_evidence_html(month_selection, month_timing, target)}</article>')


def _log_validation(month_readings):
    """규격 위반은 사용자에게 막지 않고 로그로만 남긴다. (카피 은행 변경 시 배포 전에 잡기 위함)"""
    for idx, r in enumerate(month_readings, start=1):
        for issue in validate_month(r):
            logger.warning("월 풀이 규격 위반 month_index=%s %s", idx, issue)
    for issue in audit_year(month_readings):
        logger.warning("연간 문장 반복 %s", issue)


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

    # 같은 사람·같은 해에는 항상 같은 글, 다른 사람이면 다른 글이 되도록 시드를 고정한다.
    ledger = CopyLedger(seed_from(birth_date.isoformat(), year))
    months, cards, composed = [], [], []
    for month in range(1, 13):
        target = date(year, month, 15)
        if target < birth_date:
            if (year, month) < (birth_date.year, birth_date.month):
                cards.append(f'<article data-report-month="{month}" class="annual-month" style="border-left:4px solid #2D6A4F"><h4>{month}월 · 출생 전 기간</h4></article>')
                continue
            target = birth_date
        month_timing, _, _ = calculate_timing(core.input, core.natal_facts.pillars, target_date=target)
        month_selection = select_overall_domains(core, "monthly", timing=month_timing)
        month_reading = _monthly_reading(month_selection, ledger, month)
        composed.append(month_reading)
        months.append(dict(month=month, representative_date=target.isoformat(),
                           interpretation=month_selection, reading=month_reading))
        cards.append(_render_month_card(month, target, month_reading, month_selection, month_timing))
    _log_validation(composed)

    content = (
        f'<div class="annual-reading" data-overall-version="{OVERALL_VERSION}" '
        f'data-narrative-version="{NARRATIVE_VERSION}" data-copy-version="{COPY_VERSION}" '
        f'data-report-year="{year}">'
        '<section class="annual-overview"><h3>올해 총운</h3>'
        f'<p class="annual-note" data-period-basis="annual">{representative.isoformat()}을 대표일로 삼은 연간 해석입니다. '
        '연중 대운이 바뀌는 경우 전후 흐름을 각각 계산한 결과는 아닙니다.</p>'
        f'<h4>{escape(reading["title"])}</h4>{_paragraphs(reading["paragraphs"])}'
        f'{_evidence_html(selection, timing, representative)}</section>'
        '<p class="annual-note">분야별로 계산에서 드러나는 주제와 생활 조언을 구분해 읽어보세요. '
        '직업이나 관계의 예시는 현재 상황에 맞는 부분을 참고하면 됩니다.</p>'
        f'{_render_domains(reading["domains"])}'
        '<h3>12개월 흐름</h3>'
        '<p class="annual-note" data-period-basis="monthly">각 달 15일의 절기 월주를 대표값으로 사용했습니다. '
        '출생한 달의 15일이 출생 전이면 출생일을 사용하며, 출생 전 달은 제외합니다. '
        '달마다 가장 두드러진 주제 하나를 길게, 나머지 세 주제는 한 줄로 짚었습니다. '
        '달력의 1일을 운의 전환일로 보거나 월 전체의 변화, 특정 사건의 날짜를 예측한 것은 아닙니다.</p>'
        + "".join(cards) +
        '<p class="annual-note">정통 명리의 원국·대운·세운·월운을 근거로 한 해석이며, '
        '별도의 토정비결 괘 계산과는 구분됩니다. 실제 건강 상태와 중요한 결정은 '
        '현실의 정보와 전문가의 판단을 함께 확인해 주세요.</p></div>')
    return dict(
        title=f"{year}년 {escape(name)}님의 올해·월별 운세",
        content=content, engine_version=OVERALL_VERSION,
        narrative_version=NARRATIVE_VERSION, copy_version=COPY_VERSION,
        month_schema=SCHEMA, report_year=year,
        evidence_summary=dict(annual=selection, natal=natal, months=months),
        reading=reading,
    )
