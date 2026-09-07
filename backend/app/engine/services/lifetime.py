"""Conservative Korean renderer for the lifetime-overall product surface."""

from __future__ import annotations

from html import escape

from app.engine.core.models import MyeongriCoreResult
from app.engine.semantic import build_service_query


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
    items = query["synthesis"]["favorable_operations"]
    labels = [_OPERATION.get(item["operation"], item["operation"]) for item in items[:4]]
    return " · ".join(labels) if labels else "확정된 우선 작용 없음"


def _cycle_narrative(cycle: dict, strength: str | None) -> str:
    god = cycle["ten_god"]
    meaning = _TEN_GOD_MEANING.get(god, "새로운 역할과 선택")
    changes = cycle.get("relationship_changes", [])
    relation_labels = list(dict.fromkeys(
        _RELATION_MEANING.get(item.get("type"), "관계 재조정") for item in changes
    ))
    relation_text = (
        f" 특히 {'·'.join(relation_labels[:2])}이 함께 보여, 중요한 결정은 조건과 역할을 말로 확인하는 편이 좋습니다."
        if relation_labels else
        " 원국과의 큰 충돌 신호만으로 결론내리기보다, 실제 환경과 선택을 함께 살펴보는 시기입니다."
    )
    if strength in {"weak", "extremely_weak"} and god in {"peer", "rob_wealth", "direct_resource", "indirect_resource"}:
        balance = "기반을 보강하는 방향과 맞닿아 있어, 준비·학습·협력의 힘을 받기 쉽습니다."
    elif strength in {"strong", "extremely_strong"} and god in {"eating_god", "hurting_officer", "direct_wealth", "indirect_wealth", "direct_officer", "seven_killings"}:
        balance = "강한 원국의 힘을 일·성과·책임으로 풀어내는 방향과 맞닿습니다."
    else:
        balance = "이 십성 자체가 길흉을 결정하지 않으며, 원국의 균형과 현실의 선택에 따라 쓰임이 달라집니다."
    return f"이 대운에는 <strong>{meaning}</strong>이 중심 주제로 떠오릅니다. {balance}{relation_text}"


def _cycle_card(cycle: dict, current_index: int | None, strength: str | None) -> str:
    active = cycle.get("index") == current_index
    marker = " · 현재 대운" if active else ""
    style = "background:#ECFDF5;border-color:#A7F3D0;" if active else "background:#FFFFFF;"
    return (
        f'<div style="border:1px solid #E2E8F0;border-radius:10px;padding:11px;{style}">'
        f'<div style="font-weight:800;color:#0F172A;">'
        f'{cycle["start_age"]}~{cycle["end_age"]}세 · {cycle["pillar"]["ganji"]}'
        f'<span style="color:#047857;">{marker}</span></div>'
        f'<div style="font-size:12px;color:#64748B;margin-top:2px;">'
        f'{_TEN_GOD.get(cycle["ten_god"], cycle["ten_god"])}의 흐름</div>'
        f'<p style="font-size:12.8px;color:#475569;margin:6px 0 0;line-height:1.7;">'
        f'{_cycle_narrative(cycle, strength)}</p></div>'
    )


def _cycle_html(query: dict) -> str:
    luck = query["timing"]["luck_cycles"]
    current = luck.get("current") or {}
    current_index = current.get("index")
    strength = query["synthesis"].get("strength_state")
    cycles = luck.get("cycles", [])
    groups = []
    for phase_name, start, end, phase_desc in _PHASES:
        phase_cycles = [cycle for cycle in cycles if start <= cycle.get("index", 0) <= end]
        if not phase_cycles:
            continue
        active = current_index is not None and start <= current_index <= end
        ages = f'{phase_cycles[0]["start_age"]}~{phase_cycles[-1]["end_age"]}세'
        top_topics = list(dict.fromkeys(
            _TEN_GOD_MEANING.get(cycle["ten_god"], "역할 변화") for cycle in phase_cycles
        ))[:2]
        cards = "".join(_cycle_card(cycle, current_index, strength) for cycle in phase_cycles)
        groups.append(f"""
        <details {'open' if active else ''} style="border:1px solid {'#6EE7B7' if active else '#E2E8F0'};border-radius:13px;background:{'#F0FDF4' if active else '#F8FAFC'};padding:11px 12px;">
          <summary style="cursor:pointer;font-size:14px;font-weight:800;color:#0F172A;">
            {phase_name} · {ages}{' · 현재 구간' if active else ''}
          </summary>
          <p style="font-size:12.5px;color:#64748B;margin:7px 0 9px;line-height:1.65;">
            {phase_desc}입니다. 이 구간에서는 {'과 '.join(top_topics)}이 차례로 부각됩니다.
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
    content = f"""
    <div style="text-align:left;line-height:1.75;color:#1E293B;">
      <div style="background:#FFFBEB;border-left:4px solid #F59E0B;padding:16px;border-radius:14px;margin-bottom:14px;">
        <h4 style="font-size:16px;font-weight:800;color:#78350F;margin:0 0 6px;">원국 종합 판단</h4>
        <p style="font-size:13.5px;color:#92400E;margin:0;">
          일간은 {day.stem}({day.element})이며, 월령을 중심으로 본 기본 구조는 <strong>{structure}</strong>입니다.
          강약은 <strong>{strength}</strong>, 계절 환경은 <strong>{climate}</strong>으로 판정했습니다.
          이 결론의 종합 확신도는 <strong>{confidence}</strong>이며, 조건이 있는 항목은 확정 표현에서 제외했습니다.
        </p>
      </div>
      <div style="background:#F8FAFC;border:1px solid #E2E8F0;padding:14px;border-radius:14px;margin-bottom:14px;">
        <h5 style="font-size:14px;font-weight:800;color:#0F172A;margin:0 0 5px;">평생 기질과 선택의 기준</h5>
        <p style="font-size:13px;color:#475569;margin:0 0 8px;">{structure_meaning}</p>
        <p style="font-size:13px;color:#475569;margin:0;">
          강약과 계절 환경까지 함께 보면 평생의 핵심은 ‘강한 점을 더 키우는 것’보다
          상황에 맞게 힘을 보강하거나 풀어내는 데 있습니다. 우선 방향은
          <strong>{_operation_text(query)}</strong>입니다.
        </p>
      </div>
      <div style="margin-bottom:12px;">
        <h5 style="font-size:14px;font-weight:800;color:#0F172A;margin:0 0 4px;">생애 4단계 대운 흐름 · {direction}</h5>
        <p style="font-size:12px;color:#64748B;margin:0 0 9px;line-height:1.6;">
          계산은 10년 대운을 그대로 보존하되, 읽기 쉽도록 초년·청년·중장년·말년 네 구간으로 묶었습니다.
          현재 구간은 펼쳐 두고 나머지는 눌러서 확인할 수 있습니다.
        </p>
        <div style="display:grid;gap:8px;">{_cycle_html(query)}</div>
      </div>
      {_uncertainty_html(core)}
      <p style="font-size:11.5px;color:#94A3B8;margin:12px 0 0;">
        대운은 좋고 나쁨을 단정하는 점수가 아니라, 시기마다 어떤 역할과 선택이 부각되는지를 보여줍니다.
      </p>
    </div>
    """
    return {"title": title, "content": content}
