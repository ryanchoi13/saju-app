"""Lifetime health-rhythm report backed by climate and structural diagnostics."""

from __future__ import annotations

from html import escape

from app.engine.core.models import MyeongriCoreResult
from app.engine.semantic import build_service_query


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
_CYCLE_RHYTHM = {
    "peer": "자기 주도 일정이 늘기 쉬워, 혼자 감당하는 범위와 휴식 경계를 함께 정하는 일",
    "rob_wealth": "경쟁·협업으로 생활 리듬이 흔들리지 않도록 시간과 부담을 나누는 일",
    "eating_god": "꾸준한 활동·식사·돌봄의 리듬을 생활에 정착시키는 일",
    "hurting_officer": "변화와 표현에 에너지를 많이 쓸 때 회복 시간을 함께 확보하는 일",
    "direct_wealth": "일정·지출·생활 습관을 측정 가능한 방식으로 관리하는 일",
    "indirect_wealth": "활동 범위가 넓어질수록 무리한 약속과 이동을 조절하는 일",
    "direct_officer": "책임이 늘어도 기본 생활 루틴을 뒤로 미루지 않는 일",
    "seven_killings": "압박과 빠른 결정이 이어질 때 긴장과 휴식의 전환을 의식하는 일",
    "direct_resource": "수면·휴식·배움처럼 회복을 돕는 시간을 안정적으로 확보하는 일",
    "indirect_resource": "생각이 많아질 때 정보 탐색과 실제 휴식을 구분하는 일",
}
_RELATION_CAUTION = {
    "branch_clash", "branch_punishment", "branch_harm", "branch_break", "stem_control",
}
_PHASES = (
    ("초년기", 1, 2, "생활 습관과 회복 방식의 기초가 자리 잡는 구간"),
    ("청년기", 3, 4, "활동량과 책임이 늘며 자기 관리 방식을 구체화하는 구간"),
    ("중장년기", 5, 6, "성과와 책임 속에서 소모와 회복의 균형을 다시 잡는 구간"),
    ("말년기", 7, 9, "무리한 확장보다 지속 가능한 생활 리듬을 지키는 구간"),
)


def _strength_guide(state: str | None) -> str:
    if state in {"weak", "extremely_weak"}:
        return "활동 범위를 한꺼번에 넓히기보다 수면·식사·도움받을 자원을 먼저 확보하고, 회복 정도에 맞춰 일정을 늘리는 편이 좋습니다."
    if state in {"strong", "extremely_strong"}:
        return "추진력이 오래 이어질 수 있지만 피로 신호를 뒤로 미루기 쉬우므로, 규칙적인 활동과 멈추는 시간을 일정에 함께 넣는 편이 좋습니다."
    return "활동과 회복이 어느 한쪽으로 쏠리지 않도록 기본 수면·식사·움직임을 꾸준히 유지하는 편이 좋습니다."


def _operation_guide(query: dict) -> str:
    operations = query["synthesis"].get("favorable_operations", [])
    labels = list(dict.fromkeys(
        _OPERATION[item["operation"]]
        for item in operations
        if item.get("operation") in _OPERATION
    ))
    if not labels:
        return "특정 보완법을 억지로 더하기보다 현재 생활의 수면·식사·활동 균형을 기록하고, 반복해서 무너지는 지점을 먼저 확인하세요."
    return "<br>".join(f"· {label}" for label in labels[:3])


def _cycle_card(cycle: dict, current_index: int | None) -> str:
    active = cycle.get("index") == current_index
    changes = cycle.get("relationship_changes", [])
    has_caution = any(item.get("type") in _RELATION_CAUTION for item in changes)
    caution = (
        "원국과의 충돌·변경 후보도 있어 여러 큰 일정을 한꺼번에 겹치지 않도록 조정하세요."
        if has_caution else
        "이 흐름만으로 건강 상태를 단정하지 말고 실제 생활 기록과 몸의 변화를 함께 살펴보세요."
    )
    god = cycle["ten_god"]
    return f"""
    <div style="border:1px solid {'#86EFAC' if active else '#E2E8F0'};background:{'#F0FDF4' if active else '#FFFFFF'};border-radius:10px;padding:10px;">
      <div style="font-size:13px;font-weight:800;color:#0F172A;">{cycle['start_age']}~{cycle['end_age']}세 · {cycle['pillar']['ganji']}{' · 현재' if active else ''}</div>
      <p style="font-size:12.5px;color:#475569;margin:5px 0 0;line-height:1.68;">이 시기에는 <strong>{_CYCLE_RHYTHM.get(god, '활동과 회복의 자리를 다시 조정하는 일')}</strong>이 생활관리의 중심 주제가 됩니다. {caution}</p>
    </div>"""


def _phases_html(cycles: list[dict], current_index: int | None) -> str:
    groups = []
    for name, start, end, description in _PHASES:
        phase_cycles = [cycle for cycle in cycles if start <= cycle.get("index", 0) <= end]
        if not phase_cycles:
            continue
        active = current_index is not None and start <= current_index <= end
        ages = f'{phase_cycles[0]["start_age"]}~{phase_cycles[-1]["end_age"]}세'
        cards = "".join(_cycle_card(cycle, current_index) for cycle in phase_cycles)
        groups.append(f"""
        <details {'open' if active else ''} style="border:1px solid {'#86EFAC' if active else '#E2E8F0'};border-radius:13px;background:{'#F0FDF4' if active else '#F8FAFC'};padding:11px 12px;">
          <summary style="cursor:pointer;font-size:14px;font-weight:800;color:#0F172A;">{name} · {ages}{' · 현재 구간' if active else ''}</summary>
          <p style="font-size:12.5px;color:#64748B;margin:7px 0 9px;">{description}입니다.</p>
          <div style="display:grid;gap:7px;">{cards}</div>
        </details>""")
    return "".join(groups)


def _uncertainty(core: MyeongriCoreResult) -> str:
    if not core.uncertainty.time_unknown:
        return ""
    return """
    <div style="background:#FFF7ED;border:1px solid #FED7AA;padding:12px 14px;border-radius:12px;margin-top:12px;">
      <div style="font-size:13px;font-weight:800;color:#9A3412;">생시 미상 안내</div>
      <p style="font-size:12.5px;color:#7C2D12;margin:5px 0 0;line-height:1.65;">시주에 따라 강약과 일부 구조적 병목이 달라질 수 있어, 여러 시주에서 공통으로 유지되는 조후와 대운 흐름을 중심으로 설명했습니다.</p>
    </div>"""


def build_lifetime_health_report(
    core: MyeongriCoreResult, user_name: str
) -> dict[str, str]:
    """Render non-medical lifestyle guidance from the health query profile."""

    query = build_service_query(core, "health")
    if query["constraints"].get("medical_claim_allowed") is not False:
        raise ValueError("건강 생활흐름 리포트는 의료 주장 금지 설정이 필요합니다.")
    name = escape(user_name or "회원")
    strength = query["synthesis"].get("strength_state")
    climate = query["diagnostics"].get("climate", {})
    pathology = query["diagnostics"].get("pathology", {})
    cycles = query["timing"]["luck_cycles"].get("cycles", [])
    current = query["timing"]["luck_cycles"].get("current") or {}
    current_index = current.get("index")
    climate_text = _CLIMATE.get(climate.get("conclusion"), "조후 환경 판정 보류")
    bottleneck_text = _BOTTLENECK.get(
        pathology.get("conclusion"), "구조적 병목을 단정하기 어려운 상태"
    )
    current_text = (
        f"현재는 {current['start_age']}~{current['end_age']}세 {current['pillar']['ganji']} 대운입니다. {_CYCLE_RHYTHM.get(current['ten_god'], '활동과 회복의 자리를 다시 조정하는 일')}을 실제 생활 리듬과 함께 살펴보세요."
        if current else
        "현재 대운 구간을 확정하지 못해 원국과 전체 대운의 공통 생활 흐름만 제시합니다."
    )
    title = f"{name}님 정통 명리 평생 건강 생활흐름"
    content = f"""
    <div style="text-align:left;line-height:1.78;color:#1E293B;">
      <div style="background:#F0FDF4;border-left:4px solid #22C55E;padding:16px;border-radius:14px;margin-bottom:14px;">
        <h4 style="font-size:16px;font-weight:800;color:#166534;margin:0 0 6px;">평생 생활 리듬의 구조</h4>
        <p style="font-size:13.5px;color:#15803D;margin:0;">원국은 강약상 <strong>{_STRENGTH.get(strength, '판정 보류')}</strong>, 조후상 <strong>{climate_text}</strong>으로 읽힙니다. 이는 체질이나 질병명이 아니라 활동·소모·회복 환경을 살피기 위한 명리 판단입니다.</p>
      </div>
      <div style="display:grid;gap:10px;margin-bottom:14px;">
        <div style="background:#F8FAFC;border:1px solid #E2E8F0;padding:14px;border-radius:13px;"><h5 style="font-size:14px;font-weight:800;margin:0 0 5px;">활동과 회복의 균형</h5><p style="font-size:13px;color:#475569;margin:0;">{_strength_guide(strength)}</p></div>
        <div style="background:#F8FAFC;border:1px solid #E2E8F0;padding:14px;border-radius:13px;"><h5 style="font-size:14px;font-weight:800;margin:0 0 5px;">먼저 관리할 생활 병목</h5><p style="font-size:13px;color:#475569;margin:0;">{bottleneck_text}입니다. 여기서 병목은 질병이 아니라 생활 에너지의 흐름을 막는 구조를 뜻합니다.</p></div>
        <div style="background:#ECFDF5;border:1px solid #A7F3D0;padding:14px;border-radius:13px;"><h5 style="font-size:14px;font-weight:800;color:#065F46;margin:0 0 5px;">생활관리 방향</h5><p style="font-size:13px;color:#047857;margin:0;">{_operation_guide(query)}</p></div>
        <div style="background:#EFF6FF;border:1px solid #BFDBFE;padding:14px;border-radius:13px;"><h5 style="font-size:14px;font-weight:800;color:#1D4ED8;margin:0 0 5px;">현재 건강 생활흐름</h5><p style="font-size:13px;color:#1E40AF;margin:0;">{current_text}</p></div>
      </div>
      <h5 style="font-size:14.5px;font-weight:800;color:#0F172A;margin:0 0 4px;">생애 4단계 건강 생활흐름</h5>
      <p style="font-size:12px;color:#64748B;margin:0 0 9px;">10년 대운 계산은 유지하면서 초년·청년·중장년·말년으로 묶었고, 현재 구간을 펼쳐 표시합니다.</p>
      <div style="display:grid;gap:8px;">{_phases_html(cycles, current_index)}</div>
      {_uncertainty(core)}
      <p style="font-size:11.5px;color:#94A3B8;margin:12px 0 0;">이 리포트는 원국의 강약·조후·구조적 병목과 전체 대운을 생활관리 언어로 해석한 참고 자료입니다. 증상·질병·사고·수명을 예측하거나 의료 진단을 대신하지 않습니다. 불편한 증상이 있으면 의료진의 진료를 받으세요.</p>
    </div>
    """
    return {"title": title, "content": content}
