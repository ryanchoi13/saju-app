"""Conservative Korean renderer for the lifetime-overall product surface."""

from __future__ import annotations

from html import escape
from app.engine.services.reading_editorial import VERSION, DETAIL, traits, section, paragraphs, cycle_paragraphs
from app.engine.services.annual_editorial import GROUPS, GENERAL_TITLES, scene

from app.engine.core.models import MyeongriCoreResult
from app.engine.semantic.applied import recommended_directions
from app.engine.services.applied_guidance import state_basis
from app.engine.semantic import build_service_query
from app.engine.semantic.overall import select_overall_domains, OVERALL_VERSION
from app.engine.services.overall_narrative import render_overall, subjects_html, _object_particle


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
_CONFIDENCE = {
    "high": "높음",
    "medium": "중간",
    "low": "낮음",
    "undetermined": "판정 보류",
}
_TEN_GOD_MEANING = {
    "peer": "자기 기준·독립성과 동료 관계",
    "rob_wealth": "경쟁·협업과 성과 배분",
    "eating_god": "꾸준한 생산·돌봄과 결과물",
    "hurting_officer": "표현·개선과 기존 방식의 변화",
    "direct_wealth": "예산·계약과 안정적인 성과 관리",
    "indirect_wealth": "시장 기회·거래와 활동 범위 확장",
    "direct_officer": "책임·원칙과 공식적인 역할",
    "seven_killings": "압박 속 판단·결단과 실행",
    "direct_resource": "학습·문서와 안정적인 보강",
    "indirect_resource": "새 관점·탐색과 재정비",
}
_STRUCTURE_MEANING = {
    "peer": "스스로 기준을 세우고 주도권을 잡는 성향이 삶의 중심에 놓이기 쉽습니다.",
    "rob_wealth": "사람과 자원을 함께 움직이며 경쟁과 협업의 균형을 배우는 과정이 중요합니다.",
    "eating_god": "꾸준히 만들고 돌보며 결과물을 쌓는 방식에서 강점이 드러나기 쉽습니다.",
    "hurting_officer": "문제를 발견하고 더 나은 방식으로 바꾸려는 표현력과 개선 욕구가 두드러집니다.",
    "direct_wealth": "현실적인 기준으로 자원·약속·성과를 안정적으로 관리하는 힘이 중요합니다.",
    "indirect_wealth": "사람과 시장의 변화를 읽고 기회를 연결하는 활동성이 중심 주제가 되기 쉽습니다.",
    "direct_officer": "원칙과 책임을 지키며 신뢰를 쌓는 방식이 사회적 역할과 연결되기 쉽습니다.",
    "seven_killings": "압박이 있는 환경에서 결단하고 돌파하는 힘을 어떻게 조절하느냐가 중요합니다.",
    "direct_resource": "배우고 정리한 내용을 바탕으로 안정적인 기반을 만드는 과정이 중요합니다.",
    "indirect_resource": "익숙한 답보다 새로운 관점과 탐색을 통해 길을 찾는 성향이 나타나기 쉽습니다.",
}
_RELATION_MEANING = {
    "stem_combination": "관심사나 역할이 묶이는 흐름",
    "stem_control": "책임과 주도권을 조절할 흐름",
    "branch_six_combination": "협력과 결속이 커지는 흐름",
    "branch_clash": "이동·변경·재조정이 필요한 흐름",
    "branch_three_combination": "여러 조건이 한 방향으로 모이는 흐름",
    "branch_half_combination": "일부 조건이 먼저 연결되는 흐름",
    "branch_directional_combination": "환경 전체의 색깔이 강해지는 흐름",
    "branch_punishment": "반복되는 압박이나 습관을 점검할 흐름",
    "branch_harm": "말하지 않은 기대와 오해를 살필 흐름",
    "branch_break": "기존 약속이나 방식을 보완할 흐름",
}
_PHASES = (
    ("초년기", 1, 2, "기초 환경과 생활 습관이 자리 잡는 시기"),
    ("청년기", 3, 4, "진로·관계·독립의 방향을 구체화하는 시기"),
    ("중장년기", 5, 6, "역할과 성과를 확장하고 재정비하는 시기"),
    ("말년기", 7, 9, "쌓아 온 경험을 정리하고 전하는 시기"),
)


def _operation_text(query: dict) -> str:
    items = recommended_directions(query["applied_state"])
    labels = [_OPERATION.get(item["operation"], item["operation"]) for item in items[:4]]
    return " · ".join(labels) if labels else "확정된 우선 작용 없음"


def _cycle_narrative(interpretation: dict) -> str:
    selected = interpretation["selected"]
    primary = next((c for c in selected if c["domain"] in interpretation["primary_domains"]), None)
    values = cycle_paragraphs(interpretation.get("focal_god"), primary["domain"] if primary else "self")
    if primary:
        values.append(scene(primary))
    return escape(" ".join(values))


def _cycle_card(cycle: dict, current_index: int | None, interpretation: dict) -> str:
    active = cycle.get("index") == current_index
    marker = " · 현재 대운" if active else ""
    style = "background:#ECFDF5;border-color:#A7F3D0;" if active else "background:#FFFFFF;"
    return (
        f'<div data-report-cycle="{cycle["index"]}" data-cycle-ages="{cycle["start_age"]}~{cycle["end_age"]}세" '
        f'data-current-cycle="{str(active).lower()}" style="border:1px solid #E2E8F0;border-radius:10px;padding:11px;{style}">'
        f'<div style="font-weight:800;color:#0F172A;">'
        f'{cycle["start_age"]}~{cycle["end_age"]}세 · {cycle["pillar"]["ganji"]}'
        f'<span style="color:#047857;">{marker}</span></div>'
        f'<div style="font-size:12px;color:#64748B;margin-top:2px;">'
        f'{_TEN_GOD.get(cycle["ten_god"], cycle["ten_god"])}의 흐름</div>'
        f'<p style="font-size:12.8px;color:#475569;margin:6px 0 0;line-height:1.7;">'
        f'{_cycle_narrative(interpretation)}</p></div>'
    )


def _cycle_html(query: dict, core: MyeongriCoreResult, summaries: list) -> str:
    luck = query["timing"]["luck_cycles"]
    current = luck.get("current") or {}
    current_index = current.get("index")
    cycles = luck.get("cycles", [])
    groups = []
    for phase_name, start, end, phase_desc in _PHASES:
        phase_cycles = [cycle for cycle in cycles if start <= cycle.get("index", 0) <= end]
        if not phase_cycles:
            continue
        active = current_index is not None and start <= current_index <= end
        ages = f'{phase_cycles[0]["start_age"]}~{phase_cycles[-1]["end_age"]}세'
        interpretations = [select_overall_domains(core, "luck_cycle", cycle=c) for c in phase_cycles]
        summaries.extend(dict(index=c["index"], start_age=c["start_age"], end_age=c["end_age"],
                              interpretation=i) for c, i in zip(phase_cycles, interpretations))
        top_topics = list(dict.fromkeys(s["label"] for i in interpretations for s in i["selected"]
                                       if s["domain"] in i["primary_domains"]))
        cards = "".join(_cycle_card(c, current_index, i) for c, i in zip(phase_cycles, interpretations))
        groups.append(f"""
        <details {'open' if active else ''} style="border:1px solid {'#6EE7B7' if active else '#E2E8F0'};border-radius:13px;background:{'#F0FDF4' if active else '#F8FAFC'};padding:11px 12px;">
          <summary style="cursor:pointer;font-size:14px;font-weight:800;color:#0F172A;">
            {phase_name} · {ages}{' · 현재 구간' if active else ''}
          </summary>
          <p style="font-size:12.5px;color:#64748B;margin:7px 0 9px;line-height:1.65;">
            이 구간에서는 {' · '.join(top_topics) or '생활의 선택과 균형'}을 살펴봅니다.
          </p>
          <div style="display:grid;gap:7px;">{cards}</div>
        </details>""")
    return "".join(groups)


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
    """Render only claims supported by natal facts and all luck cycles."""

    query = build_service_query(core, "lifetime_overall")
    name = escape(user_name or "회원")
    day = core.natal_facts.day_master
    structure_raw = query["synthesis"]["overall_structure"].get("ordinary")
    strength_raw = query["synthesis"].get("strength_state")
    climate_raw = query["synthesis"]["climate_state"].get("state")
    structure = _STRUCTURE.get(structure_raw, structure_raw or "판정 보류")
    strength = _STRENGTH.get(strength_raw, strength_raw or "판정 보류")
    climate = _CLIMATE.get(climate_raw, climate_raw or "판정 보류")
    confidence_raw = query["synthesis"].get("confidence", "undetermined")
    confidence = _CONFIDENCE.get(confidence_raw, confidence_raw)
    direction = "순행" if query["timing"]["luck_cycles"].get("direction") == "forward" else "역행"
    structure_meaning = _STRUCTURE_MEANING.get(
        structure_raw,
        "원국의 구조는 한 가지 성격표가 아니라, 반복되는 선택과 대응의 중심축을 보여줍니다.",
    )
    title = f"{name}님 정통 명리 평생운세 & 10년 대운 분석"
    selection = select_overall_domains(core, "natal")
    narrative = render_overall(selection)
    cycle_summaries = []
    cycles_html = _cycle_html(query, core, cycle_summaries)
    ordinary = query["synthesis"]["overall_structure"].get("ordinary")
    chapters = section("나를 이해하는 첫 장", [f"{user_name or '회원'}님, " + traits(ordinary)[0],
                                                   traits(ordinary)[1]])
    chapters += section("강점을 오래 살리려면", [traits(ordinary)[2]])
    for domain, label in GROUPS:
        candidate = next((c for c in selection["candidates"] if c["domain"] == domain), None)
        values = ([scene(candidate)] if candidate else []) + list(DETAIL[domain])
        chapters += section(label + " · " + GENERAL_TITLES[domain], values)
    content = (
        f'<div class="long-reading" data-overall-version="{OVERALL_VERSION}" data-narrative-version="{VERSION}">'
        + chapters +
        '<h3>생애 4단계 대운 흐름</h3>'
        '<p>삶의 시기마다 관심을 둘 일과 조심할 부분을 살펴봅니다. 현재 나이에 해당하는 구간부터 확인해 보세요.</p>'
        + cycles_html +
        '<details class="reading-evidence"><summary>이 풀이의 근거 · 명리 용어 포함</summary>'
        f'<p>일간 {day.stem}({day.element}) · {structure} · {strength} · {climate}. 대운은 {direction}입니다.</p>'
        f'<p>원국에서 {escape(" · ".join(c["label"] for c in selection["selected"]))}을 중심 주제로 살폈습니다. '
        '분야별 설명에서는 계산으로 확인한 주제와 일상에서 활용할 조언을 함께 다룹니다.</p>'
        f'<p>종합 판단의 보완 방향: {_operation_text(query)}</p></details>'
        + _uncertainty_html(core) +
        '<p class="reading-caption">원국과 10년 대운을 바탕으로 한 해석입니다. 실제 건강과 중요한 결정은 현실의 정보도 함께 확인해 주세요.</p></div>')
    return {"analysis_basis": state_basis(query["applied_state"]), "title": title, "content": content, "engine_version": OVERALL_VERSION, "narrative_version": VERSION,
            "evidence_summary": {"natal": selection, "cycles": cycle_summaries}}
