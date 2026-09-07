"""Lifetime career and business report backed by the shared Myeongri core."""

from __future__ import annotations

from collections import Counter
from html import escape

from app.engine.core.models import MyeongriCoreResult
from app.engine.semantic import build_service_query


_TEN_GOD = {
    "peer": "비견", "rob_wealth": "겁재", "eating_god": "식신",
    "hurting_officer": "상관", "direct_wealth": "정재",
    "indirect_wealth": "편재", "direct_officer": "정관",
    "seven_killings": "편관", "direct_resource": "정인",
    "indirect_resource": "편인",
}
_PHASES = (
    ("초년기", 1, 2, "일하는 습관과 역할의 기준을 익히는 구간"),
    ("청년기", 3, 4, "전문성과 진로 방향을 구체화하는 구간"),
    ("중장년기", 5, 7, "성과·책임·운영 범위를 함께 조정하는 구간"),
    ("말년기", 8, 99, "축적한 경험을 관리·전수·새 역할로 연결하는 구간"),
)
_CYCLE_TOPIC = {
    "direct_officer": "공식 역할·책임·평가 기준을 안정적으로 관리하는 일",
    "seven_killings": "압박과 변화 속에서 우선순위를 정하고 결정하는 일",
    "direct_wealth": "예산·계약·일정처럼 측정 가능한 성과를 관리하는 일",
    "indirect_wealth": "고객·시장·거래 기회를 살피고 활동 범위를 조절하는 일",
    "eating_god": "상품·서비스·기술을 꾸준한 결과물로 만드는 일",
    "hurting_officer": "기존 방식을 개선하고 제안을 설득력 있게 전달하는 일",
    "peer": "독립적인 전문성과 협업 역할의 경계를 정하는 일",
    "rob_wealth": "경쟁·협업 속 권한·비용·성과 배분을 분명히 하는 일",
    "direct_resource": "학습·문서·자격을 실제 업무 기반으로 축적하는 일",
    "indirect_resource": "새 관점과 정보를 작게 시험해 업무 방식으로 정착시키는 일",
}
_RELATION_CAUTION = {
    "branch_clash", "branch_punishment", "branch_harm", "branch_break", "stem_control",
}
_STATUS_GUIDE = {
    "직장인": (
        "현재 역할에서의 활용",
        "평가받을 결과와 맡을 책임을 먼저 구분하고, 협업 과정과 성과를 기록으로 남기는 편이 좋습니다. 승진 가능성은 명식 하나로 확정하지 않고 실제 조직 기준·실적·공석과 함께 판단해야 합니다.",
    ),
    "취업/이직": (
        "취업·이직에서의 활용",
        "직함보다 반복해서 잘할 수 있는 역할과 업무 환경을 먼저 좁히고, 경력·기술을 확인 가능한 결과물로 정리하세요. 이동 시점은 채용 조건과 생활 여건까지 확인한 뒤 정하는 편이 안전합니다.",
    ),
    "사업가": (
        "사업 운영에서의 활용",
        "매출 기회와 함께 원가·현금흐름·회수 기간을 확인하고, 동업이나 위임이 있다면 권한과 책임을 문서로 분명히 하세요. 확장은 반복 가능한 운영 방식이 확인된 뒤가 좋습니다.",
    ),
    "창업": (
        "창업 준비에서의 활용",
        "아이디어의 크기보다 실제 고객 반응을 작은 비용으로 검증하고, 고정비·손실 한도·철수 기준을 먼저 세우세요. 명리 흐름은 사업성 검증과 자금 계획을 대신하지 않습니다.",
    ),
}


def _mode(status: str) -> str:
    return "business" if status in {"사업가", "창업"} else "career"


def _work_style(counts: Counter, mode: str) -> str:
    values = {
        "officer": counts["direct_officer"] + counts["seven_killings"],
        "output": counts["eating_god"] + counts["hurting_officer"],
        "wealth": counts["direct_wealth"] + counts["indirect_wealth"],
        "peers": counts["peer"] + counts["rob_wealth"],
    }
    leading = max(values, key=values.get)
    if not values[leading]:
        return "한 가지 십성만으로 직업을 정하기보다 강약·구조와 실제 경력에서 반복되는 강점을 함께 확인하는 편이 정확합니다."
    descriptions = {
        "officer": "책임 범위와 기준이 분명한 역할에서 안정적으로 성과를 쌓는 성향이 먼저 드러납니다.",
        "output": "기술·표현·개선을 실제 결과물로 만드는 역할에서 강점을 쓰기 쉽습니다.",
        "wealth": "고객·자원·일정·성과를 현실적으로 관리하는 역할이 중요한 축이 됩니다.",
        "peers": "독립적인 판단과 동료·파트너 사이의 역할 조정이 일의 성패에 큰 영향을 줍니다.",
    }
    suffix = (
        " 사업에서는 이 성향을 고객 가치와 반복 가능한 운영 구조로 바꾸는 과정이 필요합니다."
        if mode == "business" else
        " 직장에서는 이 성향을 조직이 확인할 수 있는 역할과 결과로 보여주는 과정이 필요합니다."
    )
    return descriptions[leading] + suffix


def _balance_advice(strength: str | None) -> str:
    if strength in {"weak", "extremely_weak"}:
        return "신약한 편에서는 역할이나 사업 범위를 한꺼번에 넓히기보다 체력·시간·지원 자원을 먼저 확보하는 것이 중요합니다."
    if strength in {"strong", "extremely_strong"}:
        return "신강한 편에서는 주도력을 실제 결과로 내보내는 힘이 있으나, 혼자 결정하는 범위가 커지지 않도록 검토와 피드백 절차를 두는 편이 좋습니다."
    return "균형을 유지하려면 성과 확대와 회복·재검토 시간을 함께 배치하고, 한 역할에 책임이 과도하게 몰리지 않도록 조정하세요."


def _count_summary(counts: Counter, mode: str) -> str:
    output = counts["eating_god"] + counts["hurting_officer"]
    wealth = counts["direct_wealth"] + counts["indirect_wealth"]
    if mode == "business":
        peers = counts["peer"] + counts["rob_wealth"]
        return f"식신·상관 {output}곳, 정재·편재 {wealth}곳, 비견·겁재 {peers}곳"
    officer = counts["direct_officer"] + counts["seven_killings"]
    return f"정관·편관 {officer}곳, 식신·상관 {output}곳, 정재·편재 {wealth}곳"


def _cycle_card(cycle: dict, current_index: int | None, mode: str) -> str:
    active = cycle.get("index") == current_index
    god = cycle["ten_god"]
    topic = _CYCLE_TOPIC.get(god, "현재 자원과 역할을 다시 배치하는 일")
    changes = cycle.get("relationship_changes", [])
    has_caution = any(item.get("type") in _RELATION_CAUTION for item in changes)
    caution = (
        "원국과의 충돌·조정 신호도 있어 이동·확장·계약은 조건과 책임 범위를 한 번 더 확인하세요."
        if has_caution else
        "이 십성 하나로 성패를 정하지 말고 실제 역할·시장·조직 조건과 함께 판단하세요."
    )
    context = "사업 운영" if mode == "business" else "직업 선택과 역할 수행"
    return f"""
    <div style="border:1px solid {'#93C5FD' if active else '#E2E8F0'};background:{'#EFF6FF' if active else '#FFFFFF'};border-radius:10px;padding:10px;">
      <div style="font-size:13px;font-weight:800;color:#0F172A;">{cycle['start_age']}~{cycle['end_age']}세 · {cycle['pillar']['ganji']} · {_TEN_GOD.get(god, god)}{' · 현재' if active else ''}</div>
      <p style="font-size:12.5px;color:#475569;margin:5px 0 0;line-height:1.68;">이 시기에는 <strong>{topic}</strong>이 {context}의 중심 주제가 됩니다. {caution}</p>
    </div>"""


def _phases_html(cycles: list[dict], current_index: int | None, mode: str) -> str:
    groups = []
    for name, start, end, description in _PHASES:
        phase_cycles = [cycle for cycle in cycles if start <= cycle.get("index", 0) <= end]
        if not phase_cycles:
            continue
        active = current_index is not None and start <= current_index <= end
        ages = f'{phase_cycles[0]["start_age"]}~{phase_cycles[-1]["end_age"]}세'
        cards = "".join(_cycle_card(cycle, current_index, mode) for cycle in phase_cycles)
        groups.append(f"""
        <details {'open' if active else ''} style="border:1px solid {'#93C5FD' if active else '#E2E8F0'};border-radius:13px;background:{'#EFF6FF' if active else '#F8FAFC'};padding:11px 12px;">
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
      <p style="font-size:12.5px;color:#7C2D12;margin:5px 0 0;line-height:1.65;">시주에 따라 일부 십성과 관계 구조가 달라질 수 있어, 여러 시주에서 공통으로 유지되는 원국과 대운 흐름을 중심으로 설명했습니다.</p>
    </div>"""


def build_lifetime_career_report(core: MyeongriCoreResult, user_name: str, status: str) -> dict[str, str]:
    """Render career/business guidance without deterministic success claims."""

    mode = _mode(status)
    query = build_service_query(core, mode)
    name = escape(user_name or "회원")
    safe_status = status if status in _STATUS_GUIDE else "직장인"
    focused = query["natal"]["focused_ten_gods"]
    counts = Counter(item["ten_god"] for item in focused)
    strength = query["synthesis"].get("strength_state")
    cycles = query["timing"]["luck_cycles"].get("cycles", [])
    current = query["timing"]["luck_cycles"].get("current") or {}
    current_index = current.get("index")
    guide_title, guide_text = _STATUS_GUIDE[safe_status]
    current_text = (
        f"현재는 {current['start_age']}~{current['end_age']}세 {current['pillar']['ganji']} 대운이며, {_TEN_GOD.get(current['ten_god'], current['ten_god'])}의 주제가 활성화됩니다. {_CYCLE_TOPIC.get(current['ten_god'], '현재 역할과 자원을 다시 배치하는 일')}을 실제 상황과 함께 살펴보세요."
        if current else
        "현재 대운 구간을 확정하지 못해 원국과 전체 대운의 공통 흐름만 제시합니다."
    )
    title = f"{name}님 정통 명리 평생 직업·사업운"
    content = f"""
    <div style="text-align:left;line-height:1.78;color:#1E293B;">
      <div style="background:#EFF6FF;border-left:4px solid #3B82F6;padding:16px;border-radius:14px;margin-bottom:14px;">
        <h4 style="font-size:16px;font-weight:800;color:#1E3A8A;margin:0 0 6px;">평생 일의 구조 · {safe_status}</h4>
        <p style="font-size:13.5px;color:#1E40AF;margin:0;">{_work_style(counts, mode)} 원국에서 이 주제와 관련해 조회한 십성이 드러난 위치는 {_count_summary(counts, mode)}입니다. 이 개수는 능력이나 성공의 점수가 아닙니다.</p>
      </div>
      <div style="display:grid;gap:10px;margin-bottom:14px;">
        <div style="background:#F8FAFC;border:1px solid #E2E8F0;padding:14px;border-radius:13px;"><h5 style="font-size:14px;font-weight:800;margin:0 0 5px;">일할 때의 균형</h5><p style="font-size:13px;color:#475569;margin:0;">{_balance_advice(strength)}</p></div>
        <div style="background:#F8FAFC;border:1px solid #E2E8F0;padding:14px;border-radius:13px;"><h5 style="font-size:14px;font-weight:800;margin:0 0 5px;">{guide_title}</h5><p style="font-size:13px;color:#475569;margin:0;">{guide_text}</p></div>
        <div style="background:#ECFDF5;border:1px solid #A7F3D0;padding:14px;border-radius:13px;"><h5 style="font-size:14px;font-weight:800;color:#065F46;margin:0 0 5px;">현재 직업·사업 흐름</h5><p style="font-size:13px;color:#047857;margin:0;">{current_text}</p></div>
      </div>
      <h5 style="font-size:14.5px;font-weight:800;color:#0F172A;margin:0 0 4px;">생애 4단계 직업·사업 흐름</h5>
      <p style="font-size:12px;color:#64748B;margin:0 0 9px;">10년 대운 계산은 유지하면서 초년·청년·중장년·말년으로 묶었고, 현재 구간을 펼쳐 표시합니다.</p>
      <div style="display:grid;gap:8px;">{_phases_html(cycles, current_index, mode)}</div>
      {_uncertainty(core)}
      <p style="font-size:11.5px;color:#94A3B8;margin:12px 0 0;">이 리포트는 원국·강약·구조·전체 대운을 직업과 사업의 언어로 해석한 참고 자료이며, 취업·승진·시험 합격·창업 성공을 보장하지 않습니다.</p>
    </div>
    """
    return {"title": title, "content": content}
