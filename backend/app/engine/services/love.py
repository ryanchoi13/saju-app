"""Lifetime love and relationship report backed by the shared Myeongri core."""

from __future__ import annotations

from collections import Counter
from html import escape

from app.engine.core.models import MyeongriCoreResult
from app.engine.semantic import build_service_query


_TEN_GOD = {
    "peer": "비견", "rob_wealth": "겁재", "direct_wealth": "정재",
    "indirect_wealth": "편재", "direct_officer": "정관",
    "seven_killings": "편관",
}
_RELATION_LABEL = {
    "stem_combination": "천간합", "stem_control": "천간극",
    "branch_six_combination": "육합", "branch_clash": "충",
    "branch_three_combination": "삼합", "branch_half_combination": "반합",
    "branch_directional_combination": "방합", "branch_punishment": "형",
    "branch_harm": "해", "branch_break": "파",
}
_PHASES = (
    ("초년기", 1, 2, "가족·친구 관계에서 거리와 신뢰의 기준을 익히는 구간"),
    ("청년기", 3, 4, "만남의 방식과 오래 유지할 관계의 기준을 구체화하는 구간"),
    ("중장년기", 5, 6, "관계의 책임·생활 리듬·공동 목표를 함께 조정하는 구간"),
    ("말년기", 7, 9, "쌓인 인연을 돌보고 편안한 관계 방식을 정리하는 구간"),
)
_CYCLE_TOPIC = {
    "direct_wealth": "약속과 생활의 안정성을 현실적으로 맞추는 일",
    "indirect_wealth": "만남의 폭과 관계의 변화를 유연하게 다루는 일",
    "direct_officer": "책임·신뢰·관계의 기준을 분명히 하는 일",
    "seven_killings": "긴장이나 빠른 변화 속에서 경계를 지키는 일",
    "peer": "나와 상대의 독립성을 함께 존중하는 일",
    "rob_wealth": "경쟁심·주도권·시간 배분을 공정하게 조율하는 일",
    "eating_god": "편안한 대화와 일상의 즐거움을 꾸준히 나누는 일",
    "hurting_officer": "솔직한 표현이 비판으로 들리지 않도록 전달하는 일",
    "direct_resource": "상대의 말을 충분히 듣고 신뢰를 축적하는 일",
    "indirect_resource": "혼자 해석하기보다 생각을 확인하며 소통하는 일",
}
_CAUTION_RELATIONS = {
    "branch_clash", "branch_punishment", "branch_harm", "branch_break", "stem_control",
}
_STATUS_GUIDE = {
    "솔로": (
        "새 인연을 볼 때의 기준",
        "빠른 호감보다 대화의 일관성, 약속을 지키는 태도, 생활 리듬의 호환성을 차례로 확인하세요. 만남의 가능성은 명식만으로 확정할 수 없습니다.",
    ),
    "썸/짝사랑": (
        "관계를 확인하는 방법",
        "상대의 반응을 혼자 해석하기보다 부담 없는 질문과 구체적인 약속으로 서로의 의사를 확인하세요. 애매함이 길어지면 내가 지킬 시간과 감정의 경계도 정하는 편이 좋습니다.",
    ),
    "연애중": (
        "현재 관계에서의 활용",
        "감정의 크기보다 반복되는 소통 방식과 갈등 뒤의 회복 과정을 살펴보세요. 중요한 기대와 생활 계획은 추측하지 말고 말로 확인하는 것이 좋습니다.",
    ),
    "기혼": (
        "부부 관계에서의 활용",
        "역할·돈·가족·휴식처럼 생활에 연결된 주제는 책임 범위를 구체적으로 나누고, 해결 대화와 정서적인 대화를 구분해 시간을 마련하세요.",
    ),
}


def _relationship_style(counts: Counter) -> str:
    trust = counts["direct_officer"] + counts["seven_killings"]
    reality = counts["direct_wealth"] + counts["indirect_wealth"]
    independence = counts["peer"] + counts["rob_wealth"]
    leading = max(
        ((trust, "trust"), (reality, "reality"), (independence, "independence")),
        key=lambda item: item[0],
    )
    if not leading[0]:
        return "한 가지 십성만으로 관계 성향을 정하기보다 원국 구조와 실제 관계에서 반복되는 소통 방식을 함께 살펴보는 편이 정확합니다."
    return {
        "trust": "관계에서 책임과 신뢰의 기준을 분명히 할 때 안정감을 느끼는 성향이 먼저 드러납니다.",
        "reality": "말뿐인 호감보다 시간·약속·생활을 실제로 나누는 과정이 관계의 중요한 기준이 되기 쉽습니다.",
        "independence": "가까운 관계에서도 각자의 선택과 공간을 존중하는 방식이 중요한 축이 되기 쉽습니다.",
    }[leading[1]]


def _natal_relationship_summary(relationships: list[dict]) -> str:
    active = [item for item in relationships if item.get("action_status") in {"active", "resolved"}]
    conditional = [
        item for item in relationships
        if item.get("action_status") in {"conditional", "competing", "blocked"}
    ]
    day_related = [
        item for item in relationships
        if any(member.get("pillar") == "day" for member in item.get("members", []))
    ]
    labels = list(dict.fromkeys(_RELATION_LABEL.get(item.get("type"), item.get("type")) for item in day_related))
    day_text = (
        f"그중 일주와 직접 연결된 후보는 {', '.join(labels)}이며, 관계의 실제 작용 상태를 따로 판정했습니다."
        if labels else
        "일주와 직접 연결된 관계 후보가 없더라도, 이것만으로 인연의 유무나 관계의 좋고 나쁨을 판단하지 않습니다."
    )
    return (
        f"원국에서 관계 후보 {len(relationships)}건을 확인했고, 현재 규칙상 작용 또는 해소된 관계는 {len(active)}건, "
        f"조건·경쟁·차단을 함께 봐야 하는 관계는 {len(conditional)}건입니다. {day_text}"
    )


def _cycle_card(cycle: dict, current_index: int | None) -> str:
    active = cycle.get("index") == current_index
    god = cycle["ten_god"]
    changes = cycle.get("relationship_changes", [])
    has_caution = any(item.get("type") in _CAUTION_RELATIONS for item in changes)
    caution = (
        "원국과의 충돌·조정 신호도 있어 감정이 큰 때일수록 결론을 서두르지 말고 사실과 기대를 나누어 확인하세요."
        if has_caution else
        "이 십성 하나로 만남·결혼·이별을 정하지 말고 실제 관계의 상태와 상대의 선택을 함께 살펴보세요."
    )
    return f"""
    <div style="border:1px solid {'#FDA4AF' if active else '#E2E8F0'};background:{'#FFF1F2' if active else '#FFFFFF'};border-radius:10px;padding:10px;">
      <div style="font-size:13px;font-weight:800;color:#0F172A;">{cycle['start_age']}~{cycle['end_age']}세 · {cycle['pillar']['ganji']} · {_TEN_GOD.get(god, god)}{' · 현재' if active else ''}</div>
      <p style="font-size:12.5px;color:#475569;margin:5px 0 0;line-height:1.68;">이 시기에는 <strong>{_CYCLE_TOPIC.get(god, '관계에서 나와 상대의 자리를 다시 조정하는 일')}</strong>이 중심 주제가 됩니다. {caution}</p>
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
        <details {'open' if active else ''} style="border:1px solid {'#FDA4AF' if active else '#E2E8F0'};border-radius:13px;background:{'#FFF1F2' if active else '#F8FAFC'};padding:11px 12px;">
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
      <p style="font-size:12.5px;color:#7C2D12;margin:5px 0 0;line-height:1.65;">시주에 따라 일부 십성과 관계 후보가 달라질 수 있어, 여러 시주에서 공통으로 유지되는 원국과 대운 흐름을 중심으로 설명했습니다.</p>
    </div>"""


def build_lifetime_love_report(
    core: MyeongriCoreResult, user_name: str, status: str
) -> dict[str, str]:
    """Render relationship guidance without deterministic event claims."""

    query = build_service_query(core, "love")
    name = escape(user_name or "회원")
    safe_status = status if status in _STATUS_GUIDE else "솔로"
    counts = Counter(item["ten_god"] for item in query["natal"]["focused_ten_gods"])
    relationships = query["natal"]["relationships"]
    cycles = query["timing"]["luck_cycles"].get("cycles", [])
    current = query["timing"]["luck_cycles"].get("current") or {}
    current_index = current.get("index")
    guide_title, guide_text = _STATUS_GUIDE[safe_status]
    current_text = (
        f"현재는 {current['start_age']}~{current['end_age']}세 {current['pillar']['ganji']} 대운이며, {_TEN_GOD.get(current['ten_god'], current['ten_god'])}의 주제가 활성화됩니다. {_CYCLE_TOPIC.get(current['ten_god'], '관계에서 나와 상대의 자리를 다시 조정하는 일')}을 실제 상황과 함께 살펴보세요."
        if current else
        "현재 대운 구간을 확정하지 못해 원국과 전체 대운의 공통 흐름만 제시합니다."
    )
    title = f"{name}님 정통 명리 평생 애정·관계운"
    content = f"""
    <div style="text-align:left;line-height:1.78;color:#1E293B;">
      <div style="background:#FFF1F2;border-left:4px solid #E11D48;padding:16px;border-radius:14px;margin-bottom:14px;">
        <h4 style="font-size:16px;font-weight:800;color:#9F1239;margin:0 0 6px;">평생 관계의 구조 · {safe_status}</h4>
        <p style="font-size:13.5px;color:#BE123C;margin:0;">{_relationship_style(counts)} 원국의 정재·편재, 정관·편관, 비견·겁재가 드러난 위치와 관계 작용을 함께 살폈습니다. 십성의 개수는 인연의 수나 애정의 점수가 아닙니다.</p>
      </div>
      <div style="display:grid;gap:10px;margin-bottom:14px;">
        <div style="background:#F8FAFC;border:1px solid #E2E8F0;padding:14px;border-radius:13px;"><h5 style="font-size:14px;font-weight:800;margin:0 0 5px;">원국의 관계 작용</h5><p style="font-size:13px;color:#475569;margin:0;">{_natal_relationship_summary(relationships)}</p></div>
        <div style="background:#F8FAFC;border:1px solid #E2E8F0;padding:14px;border-radius:13px;"><h5 style="font-size:14px;font-weight:800;margin:0 0 5px;">{guide_title}</h5><p style="font-size:13px;color:#475569;margin:0;">{guide_text}</p></div>
        <div style="background:#FFF7ED;border:1px solid #FED7AA;padding:14px;border-radius:13px;"><h5 style="font-size:14px;font-weight:800;color:#9A3412;margin:0 0 5px;">현재 애정·관계 흐름</h5><p style="font-size:13px;color:#C2410C;margin:0;">{current_text}</p></div>
      </div>
      <h5 style="font-size:14.5px;font-weight:800;color:#0F172A;margin:0 0 4px;">생애 4단계 애정·관계 흐름</h5>
      <p style="font-size:12px;color:#64748B;margin:0 0 9px;">10년 대운 계산은 유지하면서 초년·청년·중장년·말년으로 묶었고, 현재 구간을 펼쳐 표시합니다.</p>
      <div style="display:grid;gap:8px;">{_phases_html(cycles, current_index)}</div>
      {_uncertainty(core)}
      <p style="font-size:11.5px;color:#94A3B8;margin:12px 0 0;">이 리포트는 원국·십성·관계 작용·전체 대운을 애정과 관계의 언어로 해석한 참고 자료입니다. 특정 인연, 결혼, 재회, 이별을 확정하거나 상대방의 마음을 대신 판단하지 않습니다.</p>
    </div>
    """
    return {"title": title, "content": content}
