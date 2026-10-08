"""Conservative Korean renderer for the lifetime-overall product surface.

구성 원칙 (달하 에디터 톤 · 현재 대운 중심)
- 지나간 대운은 풀이를 보여주지 않는다. 한 줄 칩(PAST_CHIP)으로만 남긴다.
- 현재 10년 대운만 3문단(헤드라인 + 핵심 분석 + 실천 팁)으로 무료 공개한다.
- 다음 대운부터는 티저 한 줄과 잠금 표시만 싣는다.
  ※ 블러는 화면 효과일 뿐이라 HTML에 본문이 들어 있으면 개발자도구로 그대로 보인다.
    그래서 잠긴 대운은 '본문 자체'를 HTML과 evidence_summary 어디에도 넣지 않는다.
- 엔진 밖(reading_editorial·annual_editorial)에서 온 문장은 금기어 필터를 한 번 거친다.
"""

from __future__ import annotations

from html import escape
from app.engine.services.reading_editorial import DETAIL, traits, section, paragraphs
from app.engine.services.annual_editorial import GROUPS, GENERAL_TITLES, scene
from app.engine.services.annual_copy import sanitize_paragraph
from app.engine.services import lifetime_copy as copy

from app.engine.core.models import MyeongriCoreResult
from app.engine.semantic.applied import recommended_directions
from app.engine.services.applied_guidance import state_basis
from app.engine.semantic import build_service_query
from app.engine.semantic.overall import select_overall_domains, OVERALL_VERSION


LIFETIME_NARRATIVE_VERSION = "lifetime-present-v3"
SHOW_PAST_CHIP = True  # False 로 두면 지나간 대운은 흔적도 남기지 않는다.


_STRUCTURE = {
    "peer": "비견 구조",
    "rob_wealth": "겁재 구조",
    "eating_god": "식신 구조",
    "hurting_officer": "상관 구조",
    "direct_wealth": "정재 구조",
    "indirect_wealth": "편재 구조",
    "direct_officer": "정관 구조",
    "seven_killings": "편관 구조",
    "direct_resource": "정인 구조",
    "indirect_resource": "편인 구조",
}
_STRENGTH = {
    "extremely_weak": "매우 신약",
    "weak": "신약",
    "balanced": "중화에 가까움",
    "strong": "신강",
    "extremely_strong": "매우 신강",
}
_CLIMATE = {
    "very_cold_wet": "매우 차고 습한 환경",
    "cold_wet": "차고 습한 환경",
    "cool_dry": "서늘하고 건조한 환경",
    "mild_wet": "온화하나 습한 환경",
    "mild_balanced": "한난조습이 비교적 고른 환경",
    "warm_dry": "따뜻하고 건조한 환경",
    "hot_dry": "덥고 건조한 환경",
    "very_hot_dry": "매우 덥고 건조한 환경",
}
_OPERATION = {
    "warm": "차가운 기운을 덥히기",
    "cool": "과열을 식히기",
    "moisten": "건조함을 완화하기",
    "stabilize": "습한 흐름을 안정시키기",
    "support": "일간의 기반을 보강하기",
    "drain": "강한 기운을 생산적인 활동으로 풀기",
    "mediate": "충돌하는 기운 사이를 통관하기",
    "protect": "원국의 핵심 구조를 보호하기",
    "resolve_conflict": "겹치는 충돌 관계를 먼저 정리하기",
    "preserve_balance": "현재 균형을 무리하게 흔들지 않기",
    "preserve_special_structure": "확인된 특수구조의 흐름을 보존하기",
}
_TEN_GOD = {
    "peer": "비견",
    "rob_wealth": "겁재",
    "eating_god": "식신",
    "hurting_officer": "상관",
    "direct_wealth": "정재",
    "indirect_wealth": "편재",
    "direct_officer": "정관",
    "seven_killings": "편관",
    "direct_resource": "정인",
    "indirect_resource": "편인",
}
_TOPIC = {
    "ordinary_structure": "격국",
    "special_structure": "특수구조",
    "strength": "신강·신약",
    "climate": "조후",
    "pathology": "구조적 병목",
    "mediation": "통관",
    "current_luck_cycle": "현재 대운",
    "shensha": "보조 신살",
}


def _clean(text: str, where: str) -> str:
    """엔진 밖에서 온 문장에 금기어가 섞여 있으면 그 문장만 덜어낸다."""
    return sanitize_paragraph(text, fallback="", where=where)


def _clean_all(values, where: str) -> list[str]:
    return [v for v in (_clean(t, where) for t in values) if v]


def _operation_text(query: dict) -> str:
    items = recommended_directions(query["applied_state"])
    labels = [_OPERATION.get(item["operation"], item["operation"]) for item in items[:4]]
    return " · ".join(labels) if labels else "확정된 우선 작용 없음"


# ---------------------------------------------------------------------------
# 대운 분류: 지나간 / 현재 / 앞으로
#   '오늘 기준'의 현재 대운은 엔진(query["timing"]["luck_cycles"]["current"])을 그대로 믿는다.
#   나이를 여기서 다시 계산하면 만 나이/세는 나이 기준이 엔진과 어긋날 수 있다.
# ---------------------------------------------------------------------------
def _split_cycles(luck: dict):
    cycles = sorted(luck.get("cycles", []), key=lambda c: c.get("index", 0))
    current = luck.get("current") or {}
    current_index = current.get("index")
    if current_index is None:
        return [], None, cycles          # 현재를 못 정하면 지나간 것도 단정하지 않는다.
    past = [c for c in cycles if c.get("index", 0) < current_index]
    now = next((c for c in cycles if c.get("index") == current_index), current)
    if not all(k in now for k in ("start_age", "end_age", "pillar")):
        return [], None, cycles          # 필요한 값이 빠진 현재 대운은 쓰지 않는다.
    future = [c for c in cycles if c.get("index", 0) > current_index]
    return past, now, future


def _past_chip_html(past: list) -> str:
    if not past or not SHOW_PAST_CHIP:
        return ""
    ages = f'{past[0]["start_age"]}~{past[-1]["end_age"]}세'
    text = copy.PAST_CHIP.format(ages=ages, n=len(past))
    return (
        '<p data-lifetime-section="past-chip" data-cycle-count="%d" '
        'style="display:inline-block;margin:0 0 10px;padding:4px 11px;border-radius:999px;'
        'background:#F1F5F9;color:#64748B;font-size:12px;">%s</p>' % (len(past), escape(text))
    )


def _primary_domain(selection: dict) -> str | None:
    primary = set(selection.get("primary_domains") or ())
    for c in selection.get("selected", ()):
        if c["domain"] in primary:
            return c["domain"]
    return None


def _current_cycle_html(cycle: dict, selection: dict, past: list) -> tuple[str, dict]:
    god = selection.get("focal_god") or cycle.get("ten_god")
    reading = copy.compose_current(god, _primary_domain(selection))
    ages = f'{cycle["start_age"]}~{cycle["end_age"]}세'
    html = (
        '<section data-lifetime-section="current-cycle" data-paywall="free">'
        '<h2>지금의 대운</h2>'
        '<p class="reading-caption">구매하거나 업데이트한 시점의 흐름을 담았습니다. '
        '다시 열어도 이 내용은 유지됩니다.</p>'
        + _past_chip_html(past) +
        f'<article data-report-cycle="{cycle["index"]}" data-cycle-ages="{ages}" data-current-cycle="true" '
        'style="border:1px solid #A7F3D0;border-radius:12px;background:#ECFDF5;padding:14px;">'
        f'<div style="font-size:12px;color:#047857;font-weight:800;">{escape(ages)} · '
        f'{escape(cycle["pillar"]["ganji"])} · {escape(_TEN_GOD.get(cycle.get("ten_god"), "") or "현재 대운")}</div>'
        f'<h3 style="margin:4px 0 8px;">{escape(reading["headline"])}</h3>'
        f'<p data-cycle-paragraph="core">{escape(reading["core"])}</p>'
        f'<p data-cycle-paragraph="tip">{escape(reading["tip"])}</p>'
        '</article></section>'
    )
    return html, reading


def _no_current_html() -> str:
    return (
        '<section data-lifetime-section="current-cycle" data-paywall="free"><h2>지금의 대운</h2>'
        '<p>현재에 해당하는 대운이 계산 범위에 없어 특정 시기의 흐름을 단정하지 않았습니다. '
        '아래의 타고난 성향을 먼저 참고하고, 현실의 상황과 함께 살펴보세요.</p></section>'
    )


# ---------------------------------------------------------------------------
# 다음 대운 이후: 티저 + 잠금. 본문 자리는 빈 막대(placeholder)이며 실제 문장이 아니다.
# ---------------------------------------------------------------------------
_SKELETON = (
    '<div data-locked-body="true" aria-hidden="true" style="filter:blur(3px);margin-top:8px;opacity:.55;">'
    '<span style="display:block;height:9px;margin:6px 0;border-radius:5px;background:#CBD5E1;"></span>'
    '<span style="display:block;height:9px;margin:6px 0;border-radius:5px;background:#CBD5E1;width:92%;"></span>'
    '<span style="display:block;height:9px;margin:6px 0;border-radius:5px;background:#CBD5E1;width:78%;"></span>'
    '</div>'
)


def _locked_cards_html(future: list, current_god: str | None, summaries: list) -> str:
    if not future:
        return ""
    nxt, rest = future[0], future[1:]
    summaries.append(dict(index=nxt["index"], start_age=nxt["start_age"], end_age=nxt["end_age"], state="next", locked=True))
    hook = copy.teaser(nxt["start_age"], nxt.get("ten_god"), current_god)
    parts = [
        '<section data-lifetime-section="upcoming" data-paywall="locked"><h2>다음 대운</h2>'
        f'<article data-report-cycle="{nxt["index"]}" data-cycle-ages="{nxt["start_age"]}~{nxt["end_age"]}세" '
        'data-cycle-state="next" data-locked="true" '
        'style="border:1px dashed #94A3B8;border-radius:12px;background:#F8FAFC;padding:14px;">'
        f'<div style="font-size:12px;color:#64748B;font-weight:800;">🔒 {escape(copy.LOCK_LABEL)} · '
        f'{nxt["start_age"]}~{nxt["end_age"]}세</div>'
        f'<h3 data-cycle-teaser="true" style="margin:4px 0 0;">{escape(hook)}</h3>'
        f'<p style="font-size:12.8px;color:#64748B;margin:6px 0 0;">{escape(copy.TEASER_CURIOSITY)}</p>'
        + _SKELETON +
        f'<a href="#paywall" data-paywall-cta="lifetime-cycles" style="display:inline-block;margin-top:10px;'
        f'padding:8px 14px;border-radius:9px;background:#2D6A4F;color:#fff;font-weight:700;text-decoration:none;">'
        f'{escape(copy.CTA_LABEL)}</a></article>'
    ]
    if rest:
        for c in rest:
            summaries.append(dict(index=c["index"], start_age=c["start_age"], end_age=c["end_age"], state="later", locked=True))
        ages = f'{rest[0]["start_age"]}~{rest[-1]["end_age"]}세'
        parts.append(
            f'<p data-lifetime-section="later-cycles" data-cycle-count="{len(rest)}" data-locked="true" '
            'style="margin:10px 0 0;padding:8px 12px;border-radius:10px;background:#F1F5F9;color:#64748B;font-size:12.5px;">'
            f'🔒 {escape(copy.FUTURE_REST.format(ages=ages))} · {len(rest)}개</p>')
    parts.append('</section>')
    return "".join(parts)


def _uncertainty_html(core: MyeongriCoreResult) -> str:
    if not core.uncertainty.time_unknown:
        return ""
    stable = " · ".join(
        _TOPIC.get(item["topic"], item["topic"])
        for item in core.uncertainty.stable_conclusions
    ) or "없음"
    conditional = " · ".join(
        _TOPIC.get(item["topic"], item["topic"])
        for item in core.uncertainty.conditional_conclusions
    ) or "없음"
    return f"""
    <div style="background:#FFF7ED;border:1px solid #FED7AA;padding:12px 14px;border-radius:12px;margin-top:12px;">
      <div style="font-size:13px;font-weight:800;color:#9A3412;">출생시간 미상 분석</div>
      <p style="font-size:12.5px;color:#7C2D12;margin:5px 0 0;line-height:1.65;">
        12개 시주에서 공통된 항목: {stable}<br>
        시주에 따라 달라지는 항목: {conditional}
      </p>
    </div>"""


def build_lifetime_overall_report(
    core: MyeongriCoreResult,
    user_name: str,
) -> dict[str, str]:
    """Render only claims supported by natal facts and the current luck cycle."""

    query = build_service_query(core, "lifetime_overall")
    name = escape(user_name or "회원")
    day = core.natal_facts.day_master
    structure_raw = query["synthesis"]["overall_structure"].get("ordinary")
    strength_raw = query["synthesis"].get("strength_state")
    climate_raw = query["synthesis"]["climate_state"].get("state")
    structure = _STRUCTURE.get(structure_raw, structure_raw or "판정 보류")
    strength = _STRENGTH.get(strength_raw, strength_raw or "판정 보류")
    climate = _CLIMATE.get(climate_raw, climate_raw or "판정 보류")
    luck = query["timing"]["luck_cycles"]
    direction = "순행" if luck.get("direction") == "forward" else "역행"
    title = f"{name}님 정통 명리 평생운세 · 성향과 현재"
    selection = select_overall_domains(core, "natal")
    ordinary = structure_raw

    # --- 대운: 지나간 / 현재 / 앞으로 -------------------------------------
    past, now, future = _split_cycles(luck)
    cycle_summaries: list[dict] = [
        dict(index=c["index"], start_age=c["start_age"], end_age=c["end_age"], state="past") for c in past
    ]
    current_selection = None
    current_god = None
    if now is not None:
        current_selection = select_overall_domains(core, "luck_cycle", cycle=now)
        current_god = current_selection.get("focal_god") or now.get("ten_god")
        current_html, _ = _current_cycle_html(now, current_selection, past)
        cycle_summaries.append(dict(index=now["index"], start_age=now["start_age"],
                                    end_age=now["end_age"], state="current"))
    else:
        current_html = _no_current_html()
    upcoming_html = _locked_cards_html(future, current_god, cycle_summaries)

    # --- 타고난 성향 (문장은 금기어 필터를 한 번 거친다) -------------------
    t = traits(ordinary)
    chapters = section("나를 이해하는 첫 장", _clean_all([f"{user_name or '회원'}님, " + t[0], t[1]], "nature.first"))
    chapters += section("강점을 오래 살리려면", _clean_all([t[2]], "nature.strength"))
    for domain, label in GROUPS:
        candidate = next((c for c in selection["candidates"] if c["domain"] == domain), None)
        values = ([scene(candidate)] if candidate else []) + [DETAIL[domain][2].removeprefix("하지만 ")]
        chapters += section(label + " · " + GENERAL_TITLES[domain], _clean_all(values, f"nature.{domain}"))

    content = (
        f'<div class="long-reading" data-overall-version="{OVERALL_VERSION}" '
        f'data-narrative-version="{LIFETIME_NARRATIVE_VERSION}" data-copy-version="{copy.COPY_VERSION}">'
        + current_html +
        '<section data-lifetime-section="nature"><h2>나의 타고난 성향</h2>' + chapters + '</section>'
        + upcoming_html +
        '<details class="reading-evidence"><summary>이 풀이의 근거 · 명리 용어 포함</summary>'
        f'<p>일간 {day.stem}({day.element}) · {structure} · {strength} · {climate}. 대운은 {direction}입니다.</p>'
        f'<p>원국에서 {escape(" · ".join(c["label"] for c in selection["selected"]))}을 중심 주제로 살폈습니다. '
        '분야별 설명에서는 계산으로 확인한 주제와 일상에서 활용할 조언을 함께 다룹니다.</p>'
        f'<p>종합 판단의 보완 방향: {_operation_text(query)}</p></details>'
        + _uncertainty_html(core) +
        '<p class="reading-caption">원국과 현재 대운을 바탕으로 한 해석입니다. 실제 건강과 중요한 결정은 현실의 정보도 함께 확인해 주세요.</p></div>')
    return {"analysis_basis": state_basis(query["applied_state"]), "title": title, "content": content,
            "engine_version": OVERALL_VERSION, "narrative_version": LIFETIME_NARRATIVE_VERSION,
            "copy_version": copy.COPY_VERSION,
            # 잠긴 대운의 해석 결과(selection)는 넣지 않는다: 이 dict가 클라이언트로 나가면 유료 내용이 샌다.
            "evidence_summary": {"natal": selection, "current": current_selection, "cycles": cycle_summaries}}
