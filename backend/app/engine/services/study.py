"""Lifetime study and exam report backed by the shared Myeongri core."""

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
_STRENGTH_GUIDE = {
    "extremely_weak": "긴 학습량을 한 번에 감당하기보다 짧은 단위로 나누고, 복습과 휴식을 먼저 고정하는 편이 좋습니다.",
    "weak": "새 범위를 넓히기 전에 기본 개념과 복습 시간을 확보하면 학습의 지속력이 좋아집니다.",
    "balanced": "이해·정리·문제풀이를 고르게 배치하되 실제 성과 기록으로 균형을 점검하는 편이 좋습니다.",
    "strong": "계획을 빠르게 밀어붙이는 힘은 있으나 익숙한 방식만 고집하지 말고 오답 검토와 피드백을 의도적으로 넣는 편이 좋습니다.",
    "extremely_strong": "학습량을 늘리는 것보다 틀린 근거를 다시 확인하고 타인의 평가 기준에 맞춰 답을 다듬는 과정이 중요합니다.",
}
_CYCLE_TOPIC = {
    "direct_resource": "교재와 기준을 차분히 익히고 반복 복습하는 일",
    "indirect_resource": "새 관점과 자료를 탐색하되 핵심 범위를 선별하는 일",
    "eating_god": "배운 내용을 꾸준히 문제풀이와 결과물로 바꾸는 일",
    "hurting_officer": "자기 언어로 설명하고 답안의 논리를 날카롭게 다듬는 일",
    "direct_officer": "정해진 일정·출제 기준·평가 규칙에 맞춰 준비하는 일",
    "seven_killings": "시간 압박 속에서도 우선순위를 정하고 실전 대응력을 기르는 일",
    "peer": "혼자 공부하는 힘과 동료 학습의 균형을 잡는 일",
    "rob_wealth": "비교와 경쟁에 흔들리지 않고 자기 진도를 지키는 일",
    "direct_wealth": "학습 시간과 진도를 측정 가능한 계획으로 관리하는 일",
    "indirect_wealth": "여러 기회를 좇기보다 시험 목적에 맞는 선택지를 추리는 일",
}
_PHASES = (
    ("초년기", 1, 2, "기초 학습 습관과 이해 방식을 만들어 가는 구간"),
    ("청년기", 3, 4, "전공·자격·진로에 맞춰 학습법을 구체화하는 구간"),
    ("중장년기", 5, 6, "실무 경험을 공부·자격·새 전문성으로 연결하는 구간"),
    ("말년기", 7, 9, "쌓인 지식을 정리하고 깊이 있는 배움으로 이어가는 구간"),
)


def _learning_style(counts: Counter) -> str:
    groups = {
        "input": counts["direct_resource"] + counts["indirect_resource"],
        "output": counts["eating_god"] + counts["hurting_officer"],
        "discipline": counts["direct_officer"] + counts["seven_killings"],
    }
    if not any(groups.values()):
        return "학습 관련 십성이 겉으로 강하게 드러나지 않으므로 한 가지 성향을 단정하기보다 실제 공부 기록과 원국 전체 구조를 함께 살펴야 합니다."
    leading = max(groups, key=groups.get)
    return {
        "input": "자료를 받아들이고 의미를 연결하는 힘이 먼저 드러납니다. 읽기에서 끝내지 않고 요약과 문제풀이로 이해를 확인하는 과정이 중요합니다.",
        "output": "배운 내용을 말·글·문제풀이로 꺼낼 때 학습이 선명해지는 흐름입니다. 기본 개념을 건너뛰지 않도록 범위표와 복습 기준을 함께 두는 편이 좋습니다.",
        "discipline": "목표와 평가 기준이 분명할 때 집중력을 조직하기 쉬운 흐름입니다. 압박만 높이지 말고 작은 마감과 실전 연습으로 규율을 나누어 쓰는 편이 좋습니다.",
    }[leading]


def _cycle_card(cycle: dict, current_index: int | None) -> str:
    active = cycle.get("index") == current_index
    god = cycle["ten_god"]
    return f"""
    <div style="border:1px solid {'#93C5FD' if active else '#E2E8F0'};background:{'#EFF6FF' if active else '#FFFFFF'};border-radius:10px;padding:10px;">
      <div style="font-size:13px;font-weight:800;color:#0F172A;">{cycle['start_age']}~{cycle['end_age']}세 · {cycle['pillar']['ganji']} · {_TEN_GOD.get(god, god)}{' · 현재' if active else ''}</div>
      <p style="font-size:12.5px;color:#475569;margin:5px 0 0;line-height:1.68;">이 시기에는 <strong>{_CYCLE_TOPIC.get(god, '배움의 목적과 방식을 다시 조정하는 일')}</strong>이 중심 주제가 됩니다. 이 흐름 하나만으로 합격·불합격을 확정하지 말고 준비량과 시험 조건을 함께 살펴보세요.</p>
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
      <p style="font-size:12.5px;color:#7C2D12;margin:5px 0 0;line-height:1.65;">시주에 따라 일부 학습 관련 십성과 강약이 달라질 수 있어, 여러 시주에서 공통으로 유지되는 원국과 대운 흐름을 중심으로 설명했습니다.</p>
    </div>"""


def build_lifetime_study_report(
    core: MyeongriCoreResult, user_name: str
) -> dict[str, str]:
    """Render study guidance without deterministic pass/fail claims."""

    query = build_service_query(core, "study")
    name = escape(user_name or "회원")
    counts = Counter(item["ten_god"] for item in query["natal"]["focused_ten_gods"])
    strength = query["synthesis"].get("strength_state")
    cycles = query["timing"]["luck_cycles"].get("cycles", [])
    current = query["timing"]["luck_cycles"].get("current") or {}
    current_index = current.get("index")
    current_text = (
        f"현재는 {current['start_age']}~{current['end_age']}세 {current['pillar']['ganji']} 대운이며, {_TEN_GOD.get(current['ten_god'], current['ten_god'])}의 주제가 활성화됩니다. {_CYCLE_TOPIC.get(current['ten_god'], '배움의 목적과 방식을 다시 조정하는 일')}을 현재 준비 중인 목표에 맞춰 활용하세요."
        if current else
        "현재 대운 구간을 확정하지 못해 원국과 전체 대운의 공통 학습 흐름만 제시합니다."
    )
    title = f"{name}님 정통 명리 평생 학업·시험운"
    content = f"""
    <div style="text-align:left;line-height:1.78;color:#1E293B;">
      <div style="background:#EFF6FF;border-left:4px solid #3B82F6;padding:16px;border-radius:14px;margin-bottom:14px;">
        <h4 style="font-size:16px;font-weight:800;color:#1D4ED8;margin:0 0 6px;">평생 학습 구조</h4>
        <p style="font-size:13.5px;color:#1E40AF;margin:0;">{_learning_style(counts)} 정인·편인의 이해와 흡수, 식신·상관의 표현과 문제풀이, 정관·편관의 규율과 시험 압박을 함께 살폈습니다. 십성의 개수는 지능이나 합격 점수가 아닙니다.</p>
      </div>
      <div style="display:grid;gap:10px;margin-bottom:14px;">
        <div style="background:#F8FAFC;border:1px solid #E2E8F0;padding:14px;border-radius:13px;"><h5 style="font-size:14px;font-weight:800;margin:0 0 5px;">집중력을 유지하는 방법</h5><p style="font-size:13px;color:#475569;margin:0;">{_STRENGTH_GUIDE.get(strength, '학습량과 회복 시간을 함께 기록해 집중이 반복해서 무너지는 지점을 먼저 확인하세요.')}</p></div>
        <div style="background:#F8FAFC;border:1px solid #E2E8F0;padding:14px;border-radius:13px;"><h5 style="font-size:14px;font-weight:800;margin:0 0 5px;">시험 준비의 세 축</h5><p style="font-size:13px;color:#475569;margin:0;">인성은 이해·자료·복습, 식상은 설명·답안·실전 출력, 관성은 일정·기준·시간 압박을 뜻합니다. 세 축 중 하나만 늘리기보다 약한 과정을 실제 공부 계획에 보완하는 편이 좋습니다.</p></div>
        <div style="background:#EEF2FF;border:1px solid #C7D2FE;padding:14px;border-radius:13px;"><h5 style="font-size:14px;font-weight:800;color:#4338CA;margin:0 0 5px;">현재 학업·시험 흐름</h5><p style="font-size:13px;color:#3730A3;margin:0;">{current_text}</p></div>
      </div>
      <h5 style="font-size:14.5px;font-weight:800;color:#0F172A;margin:0 0 4px;">생애 4단계 학업·시험 흐름</h5>
      <p style="font-size:12px;color:#64748B;margin:0 0 9px;">10년 대운 계산은 유지하면서 초년·청년·중장년·말년으로 묶었고, 현재 구간을 펼쳐 표시합니다.</p>
      <div style="display:grid;gap:8px;">{_phases_html(cycles, current_index)}</div>
      {_uncertainty(core)}
      <p style="font-size:11.5px;color:#94A3B8;margin:12px 0 0;">이 리포트는 원국의 학습 관련 십성·강약·구조와 전체 대운을 공부와 시험의 언어로 해석한 참고 자료입니다. 지능, 성적, 진학, 자격 취득이나 시험 합격·불합격을 확정하지 않습니다.</p>
    </div>
    """
    return {"title": title, "content": content}
