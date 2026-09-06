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


def _operation_text(query: dict) -> str:
    items = query["synthesis"]["favorable_operations"]
    labels = [_OPERATION.get(item["operation"], item["operation"]) for item in items[:4]]
    return " · ".join(labels) if labels else "확정된 우선 작용 없음"


def _cycle_html(query: dict) -> str:
    luck = query["timing"]["luck_cycles"]
    current = luck.get("current") or {}
    current_index = current.get("index")
    rows = []
    for cycle in luck.get("cycles", []):
        active = cycle.get("index") == current_index
        relation_count = len(cycle.get("relationship_changes", []))
        marker = "현재" if active else ""
        style = "background:#ECFDF5;border-color:#A7F3D0;" if active else ""
        rows.append(
            f'<div style="border:1px solid #E2E8F0;border-radius:10px;padding:10px;{style}">'
            f'<div style="font-weight:800;color:#0F172A;">'
            f'{cycle["start_age"]}~{cycle["end_age"]}세 · {cycle["pillar"]["ganji"]} '
            f'<span style="color:#047857;">{marker}</span></div>'
            f'<div style="font-size:12px;color:#64748B;margin-top:3px;">'
            f'활성 십성 {_TEN_GOD.get(cycle["ten_god"], cycle["ten_god"])} · '
            f'원국 관계 변화 후보 {relation_count}건</div></div>'
        )
    return "".join(rows)


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
        <h5 style="font-size:14px;font-weight:800;color:#0F172A;margin:0 0 5px;">삶의 균형을 잡는 우선 방향</h5>
        <p style="font-size:13px;color:#475569;margin:0;">{_operation_text(query)}</p>
      </div>
      <div style="margin-bottom:12px;">
        <h5 style="font-size:14px;font-weight:800;color:#0F172A;margin:0 0 8px;">10년 대운 흐름 · {direction}</h5>
        <div style="display:grid;gap:7px;">{_cycle_html(query)}</div>
      </div>
      {_uncertainty_html(core)}
      <p style="font-size:11.5px;color:#94A3B8;margin:12px 0 0;">
        대운은 좋고 나쁨을 단정하는 점수가 아니라, 원국에서 어떤 십성과 관계가 활성화되는지를 보여줍니다.
      </p>
    </div>
    """
    return {"title": title, "content": content}
