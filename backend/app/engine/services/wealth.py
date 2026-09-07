"""Lifetime wealth report backed by natal facts and every daeyun cycle."""

from __future__ import annotations

from collections import Counter
from html import escape

from app.engine.core.models import MyeongriCoreResult
from app.engine.semantic import build_service_query


_ELEMENT = {"木": "목", "火": "화", "土": "토", "金": "금", "水": "수"}
_CONTROLS = {"木": "土", "火": "金", "土": "水", "金": "木", "水": "火"}
_TEN_GOD = {
    "peer": "비견", "rob_wealth": "겁재", "eating_god": "식신",
    "hurting_officer": "상관", "direct_wealth": "정재",
    "indirect_wealth": "편재", "direct_officer": "정관",
    "seven_killings": "편관", "direct_resource": "정인",
    "indirect_resource": "편인",
}
_CYCLE_TOPIC = {
    "direct_wealth": "예산·계약·고정 수입처럼 관리 가능한 성과",
    "indirect_wealth": "거래·시장·새 기회처럼 변동성이 있는 자원",
    "eating_god": "꾸준히 만든 상품·서비스·기술을 결과로 연결하는 과정",
    "hurting_officer": "새로운 제안과 개선을 수익 구조로 시험하는 과정",
    "peer": "독립성과 공동 자원의 경계를 정하는 일",
    "rob_wealth": "경쟁·협업 속 비용과 몫을 분명히 하는 일",
    "direct_officer": "책임·규정·계약 조건을 지키며 기반을 안정시키는 일",
    "seven_killings": "압박 속에서도 손실 한도와 결정 순서를 지키는 일",
    "direct_resource": "학습·문서·자격을 미래 수입의 기반으로 쌓는 일",
    "indirect_resource": "새 정보와 아이디어를 작게 검증하는 일",
}
_PHASES = (
    ("초년기", 1, 2, "돈에 대한 습관과 자립의 기준을 배우는 구간"),
    ("청년기", 3, 4, "일과 수입의 방식을 구체화하고 시행착오를 자산으로 바꾸는 구간"),
    ("중장년기", 5, 7, "성과를 키우는 동시에 보유 자원과 책임을 재정비하는 구간"),
    ("말년기", 8, 99, "축적한 자원을 지키고 경험을 다음 역할로 연결하는 구간"),
)
_RELATION_CAUTION = {
    "branch_clash", "branch_punishment", "branch_harm", "branch_break", "stem_control",
}


def _natal_style(counts: Counter) -> tuple[str, str]:
    direct = counts["direct_wealth"]
    indirect = counts["indirect_wealth"]
    output = counts["eating_god"] + counts["hurting_officer"]
    if direct > indirect:
        style = "정재 쪽이 더 드러나므로 계획·예산·반복 가능한 수입 구조를 관리하는 방식이 기본축이 되기 쉽습니다."
    elif indirect > direct:
        style = "편재 쪽이 더 드러나므로 사람·거래·시장 변화에서 기회를 찾는 방식이 기본축이 되기 쉽습니다."
    elif direct or indirect:
        style = "정재와 편재가 함께 보여 안정적인 관리와 새로운 기회 탐색을 병행하는 구조입니다."
    else:
        style = "재성이 겉으로 강하게 드러난 구조는 아니어서, 돈 자체보다 기술·관계·역할을 먼저 만들고 수입으로 연결하는 과정이 중요합니다."
    output_text = (
        "식신·상관도 확인되어, 자신이 만든 상품·서비스·표현을 현실적인 결과로 연결하는 통로가 있습니다."
        if output else
        "생산과 표현의 통로가 자동으로 수익을 보장하지 않으므로, 결과물을 실제 거래와 반복 수입으로 연결하는 설계가 필요합니다."
    )
    return style, output_text


def _balance_advice(strength: str | None) -> str:
    if strength in {"weak", "extremely_weak"}:
        return "원국이 신약한 편에서는 기회 규모보다 감당할 체력·시간·현금흐름을 먼저 확인하는 것이 재물을 지키는 핵심입니다."
    if strength in {"strong", "extremely_strong"}:
        return "원국이 신강한 편에서는 생각과 추진력을 실제 상품·계약·성과로 내보낼 때 재물 흐름이 구체화되기 쉽습니다. 다만 확장 속도와 회수 계획을 함께 봐야 합니다."
    return "원국의 균형을 유지하려면 수입 확대와 안전장치를 함께 설계하고, 한쪽으로 지나치게 기울지 않도록 주기적으로 점검하는 편이 좋습니다."


def _cycle_card(cycle: dict, current_index: int | None) -> str:
    active = cycle.get("index") == current_index
    god = cycle["ten_god"]
    topic = _CYCLE_TOPIC.get(god, "현재 가진 자원과 역할을 다시 배치하는 일")
    changes = cycle.get("relationship_changes", [])
    caution_count = sum(item.get("type") in _RELATION_CAUTION for item in changes)
    caution = (
        "원국과의 충돌·조정 신호도 있어 큰 금액이나 장기 계약은 조건과 책임 범위를 한 번 더 확인하는 편이 좋습니다."
        if caution_count else
        "관계 변화만으로 길흉을 단정하지 말고 실제 수입·지출·계약 상태를 함께 확인하세요."
    )
    return f"""
    <div style="border:1px solid {'#6EE7B7' if active else '#E2E8F0'};background:{'#ECFDF5' if active else '#FFFFFF'};border-radius:10px;padding:10px;">
      <div style="font-size:13px;font-weight:800;color:#0F172A;">{cycle['start_age']}~{cycle['end_age']}세 · {cycle['pillar']['ganji']} · {_TEN_GOD.get(god, god)}{' · 현재' if active else ''}</div>
      <p style="font-size:12.5px;color:#475569;margin:5px 0 0;line-height:1.68;">이 시기에는 <strong>{topic}</strong>이 재물 관리의 중심이 됩니다. {caution}</p>
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
        <details {'open' if active else ''} style="border:1px solid {'#FCD34D' if active else '#E2E8F0'};border-radius:13px;background:{'#FFFBEB' if active else '#F8FAFC'};padding:11px 12px;">
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
      <p style="font-size:12.5px;color:#7C2D12;margin:5px 0 0;line-height:1.65;">시주에 들어올 재성·식상과 일부 관계는 달라질 수 있으므로, 공통으로 유지되는 원국과 대운 흐름만 확정적으로 설명했습니다.</p>
    </div>"""


def build_lifetime_wealth_report(core: MyeongriCoreResult, user_name: str) -> dict[str, str]:
    """Render a non-deterministic wealth reading from natal + all luck cycles."""

    query = build_service_query(core, "lifetime_wealth")
    name = escape(user_name or "회원")
    day = query["natal"]["day_master"]
    wealth_element = _CONTROLS[day["element"]]
    focused = query["natal"]["focused_ten_gods"]
    counts = Counter(item["ten_god"] for item in focused)
    style, output_text = _natal_style(counts)
    strength = query["synthesis"].get("strength_state")
    cycles = query["timing"]["luck_cycles"].get("cycles", [])
    current = query["timing"]["luck_cycles"].get("current") or {}
    current_index = current.get("index")
    current_text = (
        f"현재는 {current['start_age']}~{current['end_age']}세 {current['pillar']['ganji']} 대운이며, {_TEN_GOD.get(current['ten_god'], current['ten_god'])}의 주제가 활성화됩니다. {_CYCLE_TOPIC.get(current['ten_god'], '자원과 역할을 다시 배치하는 일')}을 실제 재정 상황과 함께 살펴보세요."
        if current else
        "현재 대운 구간을 확정하지 못해 원국과 전체 대운의 공통 흐름만 제시합니다."
    )
    title = f"{name}님 정통 명리 평생 재물운"
    content = f"""
    <div style="text-align:left;line-height:1.78;color:#1E293B;">
      <div style="background:#FFFBEB;border-left:4px solid #F59E0B;padding:16px;border-radius:14px;margin-bottom:14px;">
        <h4 style="font-size:16px;font-weight:800;color:#78350F;margin:0 0 6px;">평생 재물 구조</h4>
        <p style="font-size:13.5px;color:#92400E;margin:0;">{name}님의 일간은 {day['stem']}({_ELEMENT[day['element']]})이며, 일간이 다루는 재성은 {_ELEMENT[wealth_element]} 기운입니다. 원국에서 정재 {counts['direct_wealth']}곳, 편재 {counts['indirect_wealth']}곳, 식신·상관 {counts['eating_god'] + counts['hurting_officer']}곳을 확인했습니다. 이 개수는 재산의 크기가 아니라 재물 주제가 드러나는 위치의 수입니다.</p>
      </div>
      <div style="display:grid;gap:10px;margin-bottom:14px;">
        <div style="background:#F8FAFC;border:1px solid #E2E8F0;padding:14px;border-radius:13px;"><h5 style="font-size:14px;font-weight:800;margin:0 0 5px;">돈을 만드는 방식</h5><p style="font-size:13px;color:#475569;margin:0;">{style} {output_text}</p></div>
        <div style="background:#F8FAFC;border:1px solid #E2E8F0;padding:14px;border-radius:13px;"><h5 style="font-size:14px;font-weight:800;margin:0 0 5px;">돈을 지키는 기준</h5><p style="font-size:13px;color:#475569;margin:0;">{_balance_advice(strength)} 재물운은 수익 가능성만이 아니라 지출·부채·회수 기간·공동 책임을 함께 볼 때 현실적으로 활용할 수 있습니다.</p></div>
        <div style="background:#ECFDF5;border:1px solid #A7F3D0;padding:14px;border-radius:13px;"><h5 style="font-size:14px;font-weight:800;color:#065F46;margin:0 0 5px;">현재 재물 흐름</h5><p style="font-size:13px;color:#047857;margin:0;">{current_text}</p></div>
      </div>
      <h5 style="font-size:14.5px;font-weight:800;color:#0F172A;margin:0 0 4px;">생애 4단계 재물 흐름</h5>
      <p style="font-size:12px;color:#64748B;margin:0 0 9px;">10년 대운 계산을 유지하면서 초년·청년·중장년·말년으로 묶었습니다. 현재 구간은 펼쳐 표시합니다.</p>
      <div style="display:grid;gap:8px;">{_phases_html(cycles, current_index)}</div>
      {_uncertainty(core)}
      <p style="font-size:11.5px;color:#94A3B8;margin:12px 0 0;">이 리포트는 원국·강약·구조·전체 대운의 재성·식상 흐름을 설명하며, 특정 투자·부동산의 수익이나 손실을 보장하지 않습니다.</p>
    </div>
    """
    return {"title": title, "content": content}
