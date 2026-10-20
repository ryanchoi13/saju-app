"""Evidence-backed annual reader (v2): 중심 주제를 앞세운 구성.

계산·근거(timing, select_overall_domains)는 그대로 두고, 사용자에게 보이는 글만
annual_v2 문구 은행에서 고른다. 접고 펼치는 요소는 쓰지 않는다.

- 올해: 총운 → 올해의 세 가지 → 분야 5칸(엔진이 짚은 중심 분야가 맨 위)
- 월별: 한 단어 + 두 문장(사건이 아니라 태도)
- 금기어: 문구 은행은 처음부터 금기어 없이 쓰였고, annual_v2.validate_year 와
  테스트가 전수 검사한다. 같은 사람·같은 해에는 항상 같은 글이 나온다.
"""
from __future__ import annotations

import logging
from datetime import date
from html import escape

from app.engine.core.models import MyeongriCoreResult
from app.engine.timing import calculate_timing
from app.engine.calendar import to_solar
from app.engine.semantic.overall import select_overall_domains, OVERALL_VERSION
from app.engine.services.annual_editorial import NARRATIVE_VERSION, ROLE_NAMES
from app.engine.services.annual_copy import (
    CopyLedger, seed_from, flow_of,
)
from app.engine.services import annual_v2

logger = logging.getLogger("dalha.annual")


# ---------------------------------------------------------------------------
# 올해 풀이
# ---------------------------------------------------------------------------
def _annual_reading(selection):
    reading = annual_v2.compose_year(selection)
    reading["source_ids"] = sorted({s for c in selection["selected"] for s in c["source_ids"]})
    return reading


TERM_KO = {
    "小寒": "소한", "立春": "입춘", "惊蛰": "경칩", "驚蟄": "경칩", "清明": "청명", "立夏": "입하",
    "芒种": "망종", "芒種": "망종", "小暑": "소서", "立秋": "입추", "白露": "백로", "寒露": "한로",
    "立冬": "입동", "大雪": "대설",
    "XIAO_HAN": "소한", "LI_CHUN": "입춘", "JING_ZHE": "경칩", "DA_XUE": "대설",
}


def _term_period(target):
    """대표일이 속한 절기 달의 시작(절입일)과 끝. 계산하지 못하면 None (그 한 줄만 뺀다)."""
    try:
        from datetime import timedelta
        from lunar_python import Solar
        lunar = Solar.fromYmd(target.year, target.month, target.day).getLunar()
        prev, nxt = lunar.getPrevJie(), lunar.getNextJie()
        s, e = prev.getSolar(), nxt.getSolar()
        start = date(s.getYear(), s.getMonth(), s.getDay())
        end = date(e.getYear(), e.getMonth(), e.getDay()) - timedelta(days=1)
        name = TERM_KO.get(prev.getName())
        if not name or not start <= target <= end:
            return None
        return dict(name=name, start=start, end=end)
    except Exception:  # 라이브러리 버전 차이 등. 풀이 전체를 막지 않는다.
        logger.warning("절기 기간 계산 실패 target=%s", target, exc_info=True)
        return None


def _month_focus(selection):
    """그달에 엔진이 짚은 분야(primary_domains 첫째)를 v2 분야로. 없으면 그달 십성의 분야."""
    modes = {c["domain"]: c.get("mode", "base") for c in selection.get("candidates", ())}
    for domain in selection.get("primary_domains") or ():
        area = annual_v2.ENGINE_TO_AREA.get(domain)
        if area:
            return area, flow_of(modes.get(domain))
    return annual_v2.GOD_AREA.get(selection.get("focal_god"), "body"), "base"


def _monthly_reading(selection, ledger, month, year_god, target):
    area, flow = _month_focus(selection)
    return annual_v2.compose_month(ledger, month, month_god=selection.get("focal_god"), year_god=year_god,
                                   focus_area=area, flow=flow, period=_term_period(target))


# ---------------------------------------------------------------------------
# 화면 조립 (접고 펼치는 요소 없이 모두 펼쳐서 보여준다)
# ---------------------------------------------------------------------------
def _basis_note(selection, timing, representative):
    role = ROLE_NAMES.get(selection.get("focal_god"), "미정")
    ganji = timing.annual.get("pillar", {}).get("ganji", "")
    return (
        '<p class="annual-note" data-period-basis="annual">'
        f'{escape(representative.isoformat())}을 대표일로 삼은 연간 해석입니다 · {escape(ganji)} · {escape(role)}. '
        '연중 대운이 바뀌는 경우 전후 흐름을 각각 계산한 결과는 아닙니다.</p>')


def _render_year(reading):
    parts = [
        '<section class="annual-overview"><h3>올해 총운</h3>',
        f'<p class="annual-lead">{escape(reading["title"])}</p>',
        f'<p>{escape(" ".join(reading["overview"]))}</p></section>',
        '<section class="annual-three"><h3>올해의 세 가지</h3>',
    ]
    for item in reading["three"]:
        parts.append(f'<p data-annual-three="{item["key"]}"><strong>{escape(item["label"])}</strong><br>'
                     f'{escape(item["text"])}</p>')
    parts.append('</section>')
    for area in reading["areas"]:
        heading = ("올해의 중심 · " if area["central"] else "") + area["label"]
        parts.append(
            f'<section class="annual-domain" data-report-domain="{area["area"]}" '
            f'data-central="{str(area["central"]).lower()}" data-flow="{area["mode"]}">'
            f'<h3 data-toc-label="{escape(area["label"], quote=True)}">{escape(heading)}</h3>'
            f'<p>{escape(area["text"])}</p></section>')
    return "".join(parts)


def _render_month_card(month, reading):
    lines = "".join(f'<li><strong>{escape(l["label"])}</strong> {escape(l["text"])}</li>' for l in reading["lines"])
    period = f'<div class="annual-month-period">{escape(reading["period"])}</div>' if reading["period"] else ""
    link = (f'<h5>올해와 이어지는 점</h5><p>{escape(reading["link"])}</p>') if reading["link"] else ""
    return (
        f'<article data-report-month="{month}" data-flow="{reading["flow"]}" class="annual-month" '
        'style="border-left:4px solid #2D6A4F">'
        f'<h4>{month}월 · {escape(reading["verdict"])}</h4>{period}'
        f'<p class="annual-month-flow">{escape(reading["flow_text"])}</p>{link}'
        f'<h5>이달의 초점 · {escape(reading["focus"]["label"])}</h5><p>{escape(reading["focus"]["text"])}</p>'
        + (f'<h5>분야별 한 줄</h5><ul class="annual-month-lines">{lines}</ul>' if lines else "") +
        f'<p class="annual-month-todo"><strong>할 일</strong> {escape(reading["do"])}<br>'
        f'<strong>피할 일</strong> {escape(reading["avoid"])}</p></article>')


def _log_validation(reading, month_readings):
    """규격 위반은 사용자에게 막지 않고 로그로만 남긴다. (문구 은행 변경 시 배포 전에 잡기 위함)"""
    for issue in annual_v2.validate_year(reading):
        logger.warning("연간 풀이 규격 위반 %s", issue)
    for idx, r in enumerate(month_readings, start=1):
        for issue in annual_v2.validate_month(r):
            logger.warning("월별 풀이 규격 위반 %s번째 %s", idx, issue)
    seen = {}
    for idx, r in enumerate(month_readings, start=1):
        for sentence in r["sentences"]:
            if sentence in seen:
                logger.warning("월별 문장 반복 %r (%s월, %s월)", sentence, seen[sentence], idx)
            seen.setdefault(sentence, idx)


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
    reading = _annual_reading(selection)

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
        month_reading = _monthly_reading(month_selection, ledger, month, selection.get("focal_god"), target)
        composed.append(month_reading)
        months.append(dict(month=month, representative_date=target.isoformat(),
                           interpretation=month_selection, reading=month_reading))
        cards.append(_render_month_card(month, month_reading))
    _log_validation(reading, composed)

    content = (
        f'<div class="annual-reading" data-overall-version="{OVERALL_VERSION}" '
        f'data-narrative-version="{NARRATIVE_VERSION}" data-copy-version="{annual_v2.COPY_V2_VERSION}" '
        f'data-report-year="{year}">'
        f'{_render_year(reading)}'
        f'{_basis_note(selection, timing, representative)}'
        '<h3>12개월 흐름</h3>'
        '<p class="annual-note" data-period-basis="monthly">각 달 15일의 절기 월주를 대표값으로 사용했습니다. '
        '출생한 달의 15일이 출생 전이면 출생일을 사용하며, 출생 전 달은 제외합니다. '
        '달마다 그달의 십성과 엔진이 짚은 분야를 바탕으로 취할 태도와 할 일을 안내합니다. '
        '달력의 1일을 운의 전환일로 보거나 월 전체의 변화, 특정 사건의 날짜를 예측한 것은 아닙니다.</p>'
        + "".join(cards) +
        '<p class="annual-note">정통 명리의 원국·대운·세운·월운을 근거로 한 해석이며, '
        '별도의 토정비결 괘 계산과는 구분됩니다. 실제 건강 상태와 중요한 결정은 '
        '현실의 정보와 전문가의 판단을 함께 확인해 주세요.</p></div>')
    return dict(
        title=f"{year}년 {escape(name)}님의 올해·월별 운세",
        content=content, engine_version=OVERALL_VERSION,
        narrative_version=NARRATIVE_VERSION, copy_version=annual_v2.COPY_V2_VERSION,
        month_schema="dalha.month.v3", report_year=year,
        evidence_summary=dict(annual=selection, natal=natal, months=months),
        reading=reading,
    )
