"""User-facing annual and monthly report backed by ordered Myeongri timing layers."""

from __future__ import annotations

from datetime import date
from html import escape

from app.engine.core.models import MyeongriCoreResult
from app.engine.timing import calculate_timing


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
_ELEMENT = {"木": "목", "火": "화", "土": "토", "金": "금", "水": "수"}
_THEME = {
    "peer": ("자기 기준과 주도권", "혼자 밀어붙이기보다 역할을 분명히 나누는 편이 좋습니다."),
    "rob_wealth": ("경쟁·협업과 몫의 배분", "성과와 비용의 기준을 시작 전에 합의하는 편이 안전합니다."),
    "eating_god": ("꾸준한 생산과 결과물", "속도보다 완성도와 반복 가능한 방식을 만드는 데 힘을 쓰세요."),
    "hurting_officer": ("표현·개선과 기존 방식의 변화", "좋은 제안도 표현이 날카로우면 마찰이 생길 수 있어 전달 방식을 다듬는 것이 중요합니다."),
    "direct_wealth": ("예산·계약과 눈에 보이는 성과", "수입뿐 아니라 지출과 회수 일정까지 함께 관리하면 실속을 지키기 좋습니다."),
    "indirect_wealth": ("시장 기회와 활동 범위의 확장", "기회가 넓어질수록 선택 기준과 감당할 범위를 먼저 정하세요."),
    "direct_officer": ("책임·원칙과 공식적인 역할", "기준을 지키되 책임을 혼자 떠안지 않도록 범위를 분명히 하세요."),
    "seven_killings": ("압박 속 결단과 실행", "급할수록 우선순위를 줄이고 확인 절차를 남기는 편이 좋습니다."),
    "direct_resource": ("학습·문서와 안정적인 보강", "배운 것을 실제 일과 생활에 적용하는 단계까지 연결해 보세요."),
    "indirect_resource": ("새 관점·탐색과 재정비", "아이디어를 넓히되 검증되지 않은 판단은 작은 시험부터 시작하세요."),
}
_MONTH_ACTION = {
    "peer": "협업할 일과 혼자 결정할 일을 구분해 보세요.",
    "rob_wealth": "공동 비용과 역할 분담을 문서로 남기면 좋습니다.",
    "eating_god": "작은 결과물을 꾸준히 쌓는 일정이 잘 맞습니다.",
    "hurting_officer": "개선안을 말하기 전에 상대가 받아들일 순서를 정해 보세요.",
    "direct_wealth": "예산과 계약 조건을 숫자로 다시 확인해 보세요.",
    "indirect_wealth": "새 제안은 범위를 작게 시험한 뒤 넓히는 편이 좋습니다.",
    "direct_officer": "마감과 책임 범위를 먼저 정리해 두세요.",
    "seven_killings": "급한 일일수록 확인 목록을 짧게라도 남겨 두세요.",
    "direct_resource": "자료를 정리하고 배운 것을 실제 업무에 적용해 보세요.",
    "indirect_resource": "새 아이디어는 한 가지 가설부터 검증해 보세요.",
}


def _topic(god: str) -> tuple[str, str]:
    return _THEME.get(god, ("현재의 선택과 조정", "결과를 단정하기보다 실제 상황을 확인하며 움직이세요."))


def _annual_sections(annual_god: str, cycle_god: str | None) -> dict[str, str]:
    annual_topic, annual_advice = _topic(annual_god)
    cycle_topic, _ = _topic(cycle_god) if cycle_god else ("장기 흐름", "")
    money = {
        "direct_wealth": "수입·지출·회수 계획을 구체화하기 좋은 주제가 전면에 옵니다.",
        "indirect_wealth": "새 거래나 활동 반경을 넓힐 기회가 보이지만, 변동성 관리가 함께 필요합니다.",
        "eating_god": "당장의 큰 결론보다 꾸준히 만든 결과물이 재물 흐름의 기반이 됩니다.",
        "hurting_officer": "새 방식과 제안이 수입 경로를 넓힐 수 있으나 조건 검토가 먼저입니다.",
    }.get(annual_god, "큰 승부보다 현재 자원과 고정 지출을 점검하며 선택의 여지를 남기는 편이 좋습니다.")
    career = {
        "direct_officer": "공식 역할과 책임이 부각됩니다. 기준과 보고 체계를 잘 세우면 안정적인 성과로 이어지기 쉽습니다.",
        "seven_killings": "빠른 판단을 요구받는 상황이 늘 수 있습니다. 결정권과 책임 범위를 함께 확인하세요.",
        "peer": "내 기준과 전문성을 드러낼 일이 많아집니다. 동료와의 역할 경계를 분명히 할수록 효율적입니다.",
        "rob_wealth": "경쟁과 협업이 동시에 커질 수 있습니다. 성과 배분 원칙을 미리 정하는 것이 중요합니다.",
        "eating_god": "꾸준한 생산과 서비스 품질이 평판을 만드는 해입니다. 반복 가능한 운영 방식을 남겨 보세요.",
        "hurting_officer": "낡은 방식을 개선하고 의견을 드러내는 힘이 커집니다. 표현의 순서를 다듬으면 제안이 더 잘 전달됩니다.",
    }.get(annual_god, "배우고 정리한 것을 실제 역할과 결과물로 연결할 때 흐름을 활용하기 좋습니다.")
    relation = (
        f"올해는 {annual_topic}이 관계에서도 드러납니다. 상대의 반응을 예측하기보다 역할·기대·기한을 말로 확인하면 불필요한 오해를 줄일 수 있습니다."
    )
    rhythm = (
        f"연간의 {annual_topic}과 대운의 {cycle_topic}이 함께 작동합니다. "
        f"{annual_advice} 활동량이 늘 때일수록 휴식과 재검토 시간을 일정 안에 먼저 넣어 두세요."
    )
    return {"money": money, "career": career, "relation": relation, "rhythm": rhythm}


def _monthly_html(core: MyeongriCoreResult, year: int) -> str:
    cards = []
    favorable = set(core.semantic_state.favorable_elements)
    for month in range(1, 13):
        timing, _, _ = calculate_timing(
            core.input,
            core.natal_facts.pillars,
            target_date=date(year, month, 15),
        )
        monthly = timing.monthly
        god = monthly["ten_god"]
        pillar = monthly["pillar"]
        element = pillar["stem_element"]
        topic, caution = _topic(god)
        balance = (
            "이 기운은 원국의 보완 방향과 겹치므로 계획한 일을 차분히 진전시키기 좋습니다."
            if element in favorable else
            "이 기운이 곧 길흉을 뜻하지는 않으므로, 무리한 확대보다 반응을 살피며 조절하세요."
        )
        cards.append(f"""
        <div style="background:#F8FAFC;border:1px solid #E2E8F0;padding:13px 14px;border-radius:12px;border-left:4px solid #2D6A4F;">
          <div style="font-size:13.5px;font-weight:800;color:#0F172A;">{month}월 · {pillar['ganji']}월 · {_TEN_GOD.get(god, god)}</div>
          <p style="font-size:13px;color:#475569;margin:5px 0 0;line-height:1.72;">
            이번 달에는 <strong>{topic}</strong>이 눈에 띕니다. {balance}
            {_MONTH_ACTION.get(god, caution)}
          </p>
        </div>""")
    return "".join(cards)


def build_annual_overall_report(
    core: MyeongriCoreResult,
    user_name: str,
    year: int,
) -> dict[str, str]:
    """Render natal + current daeyun + annual + monthly layers without fake scores."""

    name = escape(user_name or "회원")
    annual = core.timing.annual
    cycle = core.timing.luck_cycle.get("current") or {}
    annual_god = annual["ten_god"]
    cycle_god = cycle.get("ten_god")
    annual_topic, annual_advice = _topic(annual_god)
    sections = _annual_sections(annual_god, cycle_god)
    annual_pillar = annual["pillar"]
    title = f"{year} {annual_pillar['ganji']}년 {name}님 총운 & 12개월 명리 흐름"
    content = f"""
    <div style="text-align:left;line-height:1.8;color:#1E293B;">
      <div style="background:#ECFDF5;border-left:4px solid #10B981;padding:16px;border-radius:14px;margin-bottom:16px;">
        <div style="font-size:11.5px;font-weight:700;color:#059669;margin-bottom:4px;">올해 총운</div>
        <h4 style="font-size:17px;font-weight:800;color:#065F46;margin:0 0 7px;">{year} {annual_pillar['ganji']}년의 핵심 흐름</h4>
        <p style="font-size:13.5px;color:#047857;margin:0;line-height:1.75;">
          원국 위에 현재 대운과 올해 세운을 함께 놓으면 <strong>{_TEN_GOD.get(annual_god, annual_god)}</strong>,
          즉 <strong>{annual_topic}</strong>이 올해의 중심 주제로 드러납니다. {annual_advice}
          이는 확정된 사건 예고가 아니라, 올해 선택과 대응에서 반복해서 살펴볼 방향입니다.
        </p>
      </div>
      <div style="display:grid;gap:10px;margin-bottom:18px;">
        <div style="background:#FFFBEB;border:1px solid #FDE68A;padding:14px;border-radius:13px;"><h5 style="font-size:14.5px;color:#92400E;margin:0 0 5px;">재물운</h5><p style="font-size:13px;color:#78350F;margin:0;">{sections['money']}</p></div>
        <div style="background:#EFF6FF;border:1px solid #BFDBFE;padding:14px;border-radius:13px;"><h5 style="font-size:14.5px;color:#1D4ED8;margin:0 0 5px;">직장·사업운</h5><p style="font-size:13px;color:#1E40AF;margin:0;">{sections['career']}</p></div>
        <div style="background:#FFF1F2;border:1px solid #FECDD3;padding:14px;border-radius:13px;"><h5 style="font-size:14.5px;color:#BE123C;margin:0 0 5px;">관계운</h5><p style="font-size:13px;color:#9F1239;margin:0;">{sections['relation']}</p></div>
        <div style="background:#F5F3FF;border:1px solid #DDD6FE;padding:14px;border-radius:13px;"><h5 style="font-size:14.5px;color:#6D28D9;margin:0 0 5px;">생활 리듬</h5><p style="font-size:13px;color:#5B21B6;margin:0;">{sections['rhythm']}</p></div>
      </div>
      <h4 style="font-size:15.5px;font-weight:800;color:#0F172A;margin:20px 0 5px;">12개월 흐름</h4>
      <p style="font-size:12px;color:#64748B;margin:0 0 10px;">각 달 15일의 절기 월주를 대표값으로 사용해 월별 중심 기운을 읽었습니다.</p>
      <div style="display:grid;gap:9px;">{_monthly_html(core, year)}</div>
      <p style="font-size:11.5px;color:#94A3B8;margin:12px 0 0;">정통 명리의 원국·대운·세운·월운을 근거로 한 해석이며, 별도의 토정비결 괘 계산과는 구분됩니다.</p>
    </div>
    """
    return {"title": title, "content": content}
