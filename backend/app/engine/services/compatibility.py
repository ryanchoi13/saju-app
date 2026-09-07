"""Two-person compatibility report derived from two Myeongri core results."""

from __future__ import annotations

from html import escape
from itertools import product

from app.engine.constants import GAN_WUXING
from app.engine.core.models import MyeongriCoreResult
from app.engine.facts.ten_gods import get_ten_god


_GENERATES = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
_CONTROLS = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
_STEM_COMBINATION = {frozenset(pair) for pair in ("甲己", "乙庚", "丙辛", "丁壬", "戊癸")}
_BRANCH_RULES = (
    ("육합", {frozenset(pair) for pair in ("子丑", "寅亥", "卯戌", "辰酉", "巳申", "午未")}, "서로 다른 방식을 연결하고 접점을 만들기 쉬운 관계 후보"),
    ("충", {frozenset(pair) for pair in ("子午", "丑未", "寅申", "卯酉", "辰戌", "巳亥")}, "생활 방식이나 결정 속도가 맞부딪힐 수 있어 조율이 필요한 관계 후보"),
    ("해", {frozenset(pair) for pair in ("子未", "丑午", "寅巳", "卯辰", "申亥", "酉戌")}, "의도를 추측하면 오해가 쌓일 수 있어 확인이 필요한 관계 후보"),
    ("파", {frozenset(pair) for pair in ("子酉", "丑辰", "寅亥", "卯午", "巳申", "未戌")}, "합의한 방식이 중간에 달라지지 않도록 기준을 분명히 할 관계 후보"),
    ("형", {frozenset(pair) for pair in ("子卯", "寅巳", "巳申", "申寅", "丑戌", "戌未", "未丑")}, "반복되는 긴장이나 고집을 규칙과 거리 조절로 다룰 관계 후보"),
)
_PILLAR_LABEL = {"year": "년주", "month": "월주", "day": "일주", "hour": "시주"}
_TEN_GOD = {
    "peer": "비견", "rob_wealth": "겁재", "eating_god": "식신",
    "hurting_officer": "상관", "direct_wealth": "정재", "indirect_wealth": "편재",
    "direct_officer": "정관", "seven_killings": "편관",
    "direct_resource": "정인", "indirect_resource": "편인",
}
_TEN_GOD_ROLE = {
    "peer": "나와 비슷해 편하지만 경쟁심도 자극하는 사람",
    "rob_wealth": "활력과 승부욕을 끌어내지만 주도권을 다투기 쉬운 사람",
    "eating_god": "편안함과 즐거움을 표현하게 하는 사람",
    "hurting_officer": "솔직한 표현과 변화를 끌어내지만 말이 날카로워질 수 있는 사람",
    "direct_wealth": "생활의 안정과 책임을 구체적으로 생각하게 하는 사람",
    "indirect_wealth": "새로운 경험과 활동 반경을 넓혀 주는 사람",
    "direct_officer": "신뢰와 약속을 중요하게 느끼게 하는 사람",
    "seven_killings": "강한 끌림과 긴장을 함께 일으킬 수 있는 사람",
    "direct_resource": "이해받고 보호받는 느낌을 주기 쉬운 사람",
    "indirect_resource": "생각을 깊게 만들지만 속마음을 추측하게 할 수 있는 사람",
}
_RELATION_GUIDE = {
    "연인 / 결혼": "감정의 크기보다 연락·시간·돈·가족처럼 반복되는 생활 기준을 구체적으로 맞추세요.",
    "동업 / 비즈니스": "역할·의사결정권·정산 기준을 문서로 나누고, 의견 충돌과 책임 문제를 분리해 다루세요.",
    "친구 / 지인": "친밀함과 의무의 범위를 서로 같다고 가정하지 말고 연락과 부탁의 경계를 확인하세요.",
}


def _day_master_relation(left: str, right: str) -> str:
    le, re = GAN_WUXING[left], GAN_WUXING[right]
    if le == re:
        return "두 일간은 같은 오행이라 방향과 속도를 이해하기 쉽지만, 비슷한 고집이나 경쟁도 함께 나타날 수 있습니다."
    if _GENERATES[le] == re:
        return "첫 사람의 일간 오행이 상대 일간 오행을 생하는 방향입니다. 도움과 지원이 한쪽으로만 고정되지 않도록 주고받는 범위를 조정해야 합니다."
    if _GENERATES[re] == le:
        return "상대 일간 오행이 첫 사람의 일간 오행을 생하는 방향입니다. 받는 역할과 돕는 역할을 당연하게 여기지 않는 것이 중요합니다."
    if _CONTROLS[le] == re or _CONTROLS[re] == le:
        return "두 일간 사이에는 극의 방향이 있어 기준·속도·주도권을 두고 긴장이 생길 수 있습니다. 극 자체를 나쁨으로 단정하지 말고 역할과 경계를 분명히 해야 합니다."
    return "두 일간은 직접적인 동일·생·극보다 중간 과정이 필요한 관계입니다. 공통 목표와 구체적인 약속이 접점을 만드는 데 도움이 됩니다."


def _cross_interactions(left: MyeongriCoreResult, right: MyeongriCoreResult) -> list[dict]:
    left_pillars = [(key, value) for key, value in left.natal_facts.pillars.items() if value]
    right_pillars = [(key, value) for key, value in right.natal_facts.pillars.items() if value]
    found = []
    for (lk, lp), (rk, rp) in product(left_pillars, right_pillars):
        importance = 3 if lk == rk == "day" else 2 if "day" in {lk, rk} else 1
        if frozenset((lp.stem, rp.stem)) in _STEM_COMBINATION:
            found.append({"kind": "천간합", "left": lk, "right": rk, "symbols": lp.stem + rp.stem, "importance": importance, "meaning": "생각과 표현에서 접점을 만들 수 있는 관계 후보"})
        le, re = GAN_WUXING[lp.stem], GAN_WUXING[rp.stem]
        if _CONTROLS[le] == re or _CONTROLS[re] == le:
            found.append({"kind": "천간극", "left": lk, "right": rk, "symbols": lp.stem + rp.stem, "importance": importance, "meaning": "판단과 주도권의 차이를 조율해야 하는 관계 후보"})
        branch_pair = frozenset((lp.branch, rp.branch))
        for kind, pairs, meaning in _BRANCH_RULES:
            if branch_pair in pairs:
                found.append({"kind": kind, "left": lk, "right": rk, "symbols": lp.branch + rp.branch, "importance": importance, "meaning": meaning})
    return sorted(found, key=lambda item: (-item["importance"], item["kind"], item["symbols"]))


def _interaction_html(items: list[dict]) -> str:
    if not items:
        return '<p style="font-size:12.5px;color:#64748B;margin:0;">두 명식 사이에서 직접 확인되는 합·극·충·형·파·해가 많지 않아, 일간 관계와 각 명식의 보완 작용을 중심으로 해석했습니다.</p>'
    rows = []
    for item in items[:8]:
        rows.append(f"""<div style="border-top:1px solid #E2E8F0;padding:9px 0;"><strong style="font-size:12.5px;color:#334155;">{item['kind']} · {item['symbols']} · {_PILLAR_LABEL[item['left']]}↔{_PILLAR_LABEL[item['right']]}</strong><p style="font-size:12px;color:#64748B;margin:3px 0 0;">{item['meaning']}</p></div>""")
    return "".join(rows)


def _relationship_signals(items: list[dict]) -> tuple[list[dict], list[dict]]:
    supportive = [item for item in items if item["kind"] in {"천간합", "육합"}]
    tense = [item for item in items if item["kind"] in {"천간극", "충", "형", "해", "파"}]
    return supportive, tense


def _signal_level(items: list[dict]) -> str:
    if any(item["importance"] == 3 for item in items):
        return "뚜렷함"
    if items:
        return "보통"
    return "천천히 확인"


def _plain_reason(supportive: list[dict], tense: list[dict]) -> str:
    if supportive and tense:
        return "서로를 당기는 접점과 부딪히는 지점이 함께 있어, 끌림은 생기기 쉽지만 관계를 오래 유지하려면 생활 합의가 필요합니다."
    if supportive:
        return "서로 다른 방식을 연결하는 접점이 확인되어, 함께 있을 때 친밀감과 협력의 흐름을 만들기 비교적 쉽습니다."
    if tense:
        return "차이가 먼저 눈에 들어오는 관계라 강한 자극이 될 수 있지만, 말투와 결정 방식이 반복 갈등으로 굳지 않게 해야 합니다."
    return "강하게 붙거나 밀어내는 신호보다 서로를 알아 가는 과정이 중요한 관계입니다. 실제 대화와 생활 경험이 관계의 깊이를 좌우합니다."


def _love_path(supportive: list[dict], tense: list[dict]) -> tuple[str, str]:
    if supportive and tense:
        return (
            "호감과 긴장감이 함께 움직이는 편입니다. 서로의 차이를 매력으로 느낄 때 사랑이 빠르게 깊어질 수 있습니다.",
            "익숙해진 뒤에는 같은 차이가 간섭이나 무시로 느껴질 수 있습니다. 감정이 커졌을 때 결론부터 내리기보다 사실·기분·요청을 나눠 말하는 방식이 필요합니다.",
        )
    if supportive:
        return (
            "편안함과 공감이 애정으로 이어지기 쉬운 편입니다. 작은 약속을 지키고 함께하는 일상을 늘릴수록 관계가 깊어집니다.",
            "편안함을 당연하게 여기면 표현이 줄어 관계가 식었다고 오해할 수 있습니다. 고마움과 애정을 말과 행동으로 계속 확인하는 것이 중요합니다.",
        )
    if tense:
        return (
            "서로에게 없는 면을 강하게 의식하며 끌릴 수 있습니다. 존중받는다는 확신이 생길 때 애정이 깊어집니다.",
            "통제, 지적, 일방적인 결정이 반복되면 사랑보다 피로가 앞설 수 있습니다. 다툼의 승패보다 각자의 선택권을 지켜야 회복이 가능합니다.",
        )
    return (
        "첫인상의 강도보다 신뢰가 쌓이면서 애정이 깊어지는 유형입니다. 함께 겪은 경험과 꾸준한 연락이 중요합니다.",
        "관계를 알아서 유지될 것이라 생각하면 정서적 거리가 생길 수 있습니다. 중요한 감정과 기대를 먼저 말하는 습관이 필요합니다.",
    )


def _favorable_overlap(core: MyeongriCoreResult, other: MyeongriCoreResult) -> str:
    wanted = set(core.semantic_state.favorable_elements)
    present = {item.element for item in other.natal_facts.element_inventory.occurrences}
    overlap = wanted & present
    if not wanted:
        return "현재 코어가 특정 유리 오행을 확정하지 않아 상대 명식의 보완 작용도 단정하지 않습니다."
    if overlap:
        return f"상대 명식에는 이쪽 종합판단의 유리 작용과 겹치는 오행({', '.join(sorted(overlap))})이 관찰됩니다. 다만 존재만으로 실제 보완이나 좋은 궁합이 확정되는 것은 아닙니다."
    return "상대 명식의 오행 존재만으로 이쪽의 유리 작용을 직접 보완한다고 보기 어렵습니다. 필요한 생활 역할을 말과 행동으로 조정하는 편이 중요합니다."


def build_compatibility_report(left: MyeongriCoreResult, right: MyeongriCoreResult, left_name: str, right_name: str, relation: str) -> dict[str, str]:
    """Compare two cores without a fixed score or deterministic relationship claim."""
    ln, rn = escape(left_name or "회원"), escape(right_name or "상대방")
    safe_relation = relation if relation in _RELATION_GUIDE else "친구 / 지인"
    left_dm, right_dm = left.natal_facts.day_master, right.natal_facts.day_master
    interactions = _cross_interactions(left, right)
    supportive, tense = _relationship_signals(interactions)
    left_to_right = get_ten_god(left_dm.stem, right_dm.stem).value
    right_to_left = get_ten_god(right_dm.stem, left_dm.stem).value
    closeness_level = _signal_level(supportive)
    conflict_level = _signal_level(tense)
    relationship_summary = _plain_reason(supportive, tense)
    deepening, cooling = _love_path(supportive, tense)
    left_view = _TEN_GOD_ROLE.get(left_to_right, "서로의 반응을 천천히 확인하게 하는 사람")
    right_view = _TEN_GOD_ROLE.get(right_to_left, "서로의 반응을 천천히 확인하게 하는 사람")
    marriage_text = (
        "결혼생활에서는 감정의 크기보다 돈, 집안일, 개인 시간, 양가 가족의 경계를 미리 합의하는 것이 중요합니다. "
        + ("두 사람은 접점과 긴장이 함께 있어 규칙을 합의하면 결속력이 생기지만, 한쪽 방식으로 밀어붙이면 피로가 커질 수 있습니다." if supportive and tense else
           "두 사람은 친밀감을 생활의 협력으로 옮기기 좋은 편이지만, 역할을 말하지 않아도 알 것이라 기대하면 서운함이 쌓일 수 있습니다." if supportive else
           "두 사람은 차이를 관리하는 방식이 결혼의 안정성을 좌우합니다. 반복되는 갈등 주제에 합의가 가능할 때 결혼을 구체적으로 검토하는 편이 좋습니다." if tense else
           "명식의 강한 신호보다 실제 생활 검증이 더 중요합니다. 동거 방식, 재정, 갈등 회복을 충분히 경험한 뒤 결정하는 편이 좋습니다.")
    )
    money_text = (
        "둘이 힘을 합칠 때의 장점은 한 사람의 부족한 관점을 상대가 보완할 가능성에 있습니다. "
        + ("다만 협력과 주도권 충돌이 함께 보이므로, 공동재산·투자·대출은 담당자와 최종 결정권, 손실 한도를 먼저 정해야 합니다." if tense else
           "협력의 흐름은 비교적 자연스럽지만, 친밀함과 재정 책임을 섞지 말고 공동비용과 개인자금을 구분하는 것이 좋습니다.")
        + " 두 사람의 사주만으로 부의 규모나 투자 성공을 보장할 수는 없습니다."
    )
    child_text = (
        "아이가 관계를 좋아지게 하거나 나쁘게 만든다고 단정할 수는 없습니다. 다만 부모가 된 뒤에는 애정보다 수면, 돌봄, 교육관, 비용 분담이 관계에 더 직접적으로 작용합니다. "
        + ("두 사람은 의견 충돌 신호가 있어 임신·출산 전 돌봄 시간과 훈육 원칙을 구체적으로 정해 두는 것이 특히 중요합니다." if tense else
           "두 사람은 협력의 접점을 살릴 수 있으므로 돌봄 역할을 공평하게 가시화하면 관계의 결속을 높이는 쪽으로 작용할 수 있습니다.")
        + " 임신 가능성이나 실제 자녀와의 궁합은 이 두 사람의 명식만으로 판단하지 않습니다."
    )
    unknown = left.uncertainty.time_unknown or right.uncertainty.time_unknown
    uncertainty = (
        '<div style="background:#FFF7ED;border:1px solid #FED7AA;padding:12px 14px;border-radius:12px;margin-top:12px;"><strong style="font-size:13px;color:#9A3412;">생시 미상 안내</strong><p style="font-size:12.5px;color:#7C2D12;margin:5px 0 0;">한 사람 이상 출생시간을 몰라 시주 사이의 관계는 조건부입니다. 확인 가능한 년·월·일주와 여러 시주에서 공통인 결론을 중심으로 설명했습니다.</p></div>'
        if unknown else ""
    )
    title = f"{ln}님 & {rn}님 정통 사주 궁합 감명서"
    content = f"""
    <div style="text-align:left;line-height:1.78;color:#1E293B;">
      <div style="background:#FFF1F2;border-left:4px solid #E11D48;padding:16px;border-radius:14px;margin-bottom:14px;">
        <h4 style="font-size:16px;font-weight:800;color:#9F1239;margin:0 0 6px;">두 사람의 궁합, 먼저 답하면</h4>
        <p style="font-size:13.5px;color:#BE123C;margin:0;">{relationship_summary}</p>
      </div>
      <div style="display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin-bottom:14px;">
        <div style="background:#F8FAFC;border:1px solid #E2E8F0;padding:11px;border-radius:12px;"><span style="font-size:11.5px;color:#64748B;">친밀감의 접점</span><p style="font-size:14px;font-weight:800;margin:2px 0 0;">{closeness_level}</p></div>
        <div style="background:#F8FAFC;border:1px solid #E2E8F0;padding:11px;border-radius:12px;"><span style="font-size:11.5px;color:#64748B;">갈등 조율 필요</span><p style="font-size:14px;font-weight:800;margin:2px 0 0;">{conflict_level}</p></div>
      </div>
      <div style="display:grid;gap:10px;margin-bottom:14px;">
        <div style="background:#FFFFFF;border:1px solid #E2E8F0;padding:14px;border-radius:13px;"><h5 style="font-size:14px;font-weight:800;margin:0 0 5px;">서로를 어떻게 느끼는가</h5><p style="font-size:13px;color:#475569;margin:0;">{ln}님은 {rn}님을 <strong>{left_view}</strong>으로 느끼기 쉽습니다. 반대로 {rn}님은 {ln}님을 <strong>{right_view}</strong>으로 받아들이기 쉽습니다. 두 사람의 애정량을 수치로 재는 뜻이 아니라, 상대 앞에서 어떤 감정과 역할이 먼저 활성화되는지를 보여줍니다.</p></div>
        <div style="background:#FFFFFF;border:1px solid #E2E8F0;padding:14px;border-radius:13px;"><h5 style="font-size:14px;font-weight:800;margin:0 0 5px;">사랑이 깊어지는 방식</h5><p style="font-size:13px;color:#475569;margin:0;">{deepening}</p></div>
        <div style="background:#FFFFFF;border:1px solid #E2E8F0;padding:14px;border-radius:13px;"><h5 style="font-size:14px;font-weight:800;margin:0 0 5px;">사랑이 식을 수 있는 지점</h5><p style="font-size:13px;color:#475569;margin:0;">{cooling}</p></div>
        <div style="background:#FFFFFF;border:1px solid #E2E8F0;padding:14px;border-radius:13px;"><h5 style="font-size:14px;font-weight:800;margin:0 0 5px;">결혼하면 어떤가</h5><p style="font-size:13px;color:#475569;margin:0;">{marriage_text}</p></div>
        <div style="background:#FFFFFF;border:1px solid #E2E8F0;padding:14px;border-radius:13px;"><h5 style="font-size:14px;font-weight:800;margin:0 0 5px;">함께 돈을 만들고 지키는 힘</h5><p style="font-size:13px;color:#475569;margin:0;">{money_text}</p></div>
        <div style="background:#FFFFFF;border:1px solid #E2E8F0;padding:14px;border-radius:13px;"><h5 style="font-size:14px;font-weight:800;margin:0 0 5px;">자녀와 부모 역할</h5><p style="font-size:13px;color:#475569;margin:0;">{child_text}</p></div>
        <div style="background:#FFF7ED;border:1px solid #FED7AA;padding:14px;border-radius:13px;"><h5 style="font-size:14px;font-weight:800;color:#9A3412;margin:0 0 5px;">지금 두 사람에게 필요한 것</h5><p style="font-size:13px;color:#C2410C;margin:0;">{_RELATION_GUIDE[safe_relation]}</p></div>
      </div>
      <details style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:13px;padding:12px 14px;">
        <summary style="font-size:13px;font-weight:800;color:#334155;cursor:pointer;">판단 근거 보기 · 명리 용어 포함</summary>
        <p style="font-size:12.5px;color:#64748B;margin:10px 0;">두 사람의 원국을 각각 계산한 뒤 일간 관계, 상대 일간이 만드는 십성 역할, 서로 다른 명식 사이의 천간합·천간극과 지지의 합·충·형·파·해를 함께 비교했습니다.</p>
        <p style="font-size:12.5px;color:#475569;margin:0 0 8px;"><strong>{ln} → {rn}</strong>: {_TEN_GOD.get(left_to_right, left_to_right)} · <strong>{rn} → {ln}</strong>: {_TEN_GOD.get(right_to_left, right_to_left)}</p>
        <p style="font-size:12.5px;color:#64748B;margin:0 0 10px;">일간 관계: {_day_master_relation(left_dm.stem, right_dm.stem)}</p>
        {_interaction_html(interactions)}
        <p style="font-size:12.5px;color:#64748B;margin:10px 0 0;"><strong>{ln}님 보완 관점</strong>: {_favorable_overlap(left, right)}<br><strong>{rn}님 보완 관점</strong>: {_favorable_overlap(right, left)}</p>
      </details>
      {uncertainty}
      <p style="font-size:11.5px;color:#94A3B8;margin:12px 0 0;">이 리포트는 두 사람의 명식에서 확인되는 상호작용을 현실의 관계 언어로 번역한 참고 자료입니다. 사랑의 크기, 결혼·이별, 임신·출산, 재산의 규모를 확정하지 않으며 실제 관계와 선택이 명리 판단보다 우선합니다.</p>
    </div>
    """
    return {"title": title, "content": content}
