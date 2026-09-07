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
        return '<p style="font-size:13px;color:#475569;margin:0;">두 명식 사이에서 v1 규칙상 직접적인 천간합·천간극·지지 합충형파해 후보가 확인되지 않았습니다. 관계의 좋고 나쁨이 없다는 뜻은 아니며, 일간 관계와 실제 생활 방식을 함께 봐야 합니다.</p>'
    rows = []
    for item in items[:8]:
        rows.append(f"""<div style="border:1px solid #E2E8F0;border-radius:10px;padding:10px;background:#FFFFFF;"><strong style="font-size:13px;color:#0F172A;">{item['kind']} · {item['symbols']} · {_PILLAR_LABEL[item['left']]}↔{_PILLAR_LABEL[item['right']]}</strong><p style="font-size:12.5px;color:#475569;margin:4px 0 0;">{item['meaning']}입니다. 후보 하나만으로 관계의 결론을 정하지 않습니다.</p></div>""")
    return "".join(rows)


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
    left_to_right = get_ten_god(left_dm.stem, right_dm.stem).value
    right_to_left = get_ten_god(right_dm.stem, left_dm.stem).value
    unknown = left.uncertainty.time_unknown or right.uncertainty.time_unknown
    uncertainty = (
        '<div style="background:#FFF7ED;border:1px solid #FED7AA;padding:12px 14px;border-radius:12px;margin-top:12px;"><strong style="font-size:13px;color:#9A3412;">생시 미상 안내</strong><p style="font-size:12.5px;color:#7C2D12;margin:5px 0 0;">한 사람 이상 출생시간을 몰라 시주 사이의 관계는 조건부입니다. 확인 가능한 년·월·일주와 여러 시주에서 공통인 결론을 중심으로 설명했습니다.</p></div>'
        if unknown else ""
    )
    title = f"{ln}님 & {rn}님 정통 사주 궁합 감명서"
    content = f"""
    <div style="text-align:left;line-height:1.78;color:#1E293B;">
      <div style="background:#FFF1F2;border-left:4px solid #E11D48;padding:16px;border-radius:14px;margin-bottom:14px;">
        <h4 style="font-size:16px;font-weight:800;color:#9F1239;margin:0 0 6px;">두 명식의 핵심 관계 · {escape(safe_relation)}</h4>
        <p style="font-size:13.5px;color:#BE123C;margin:0;">{_day_master_relation(left_dm.stem, right_dm.stem)} 두 사람의 원국을 각각 계산한 뒤 일간의 오행 관계와 서로 다른 팔자 사이의 합·극·충·형·파·해 후보를 비교했습니다.</p>
      </div>
      <div style="display:grid;gap:10px;margin-bottom:14px;">
        <div style="background:#F8FAFC;border:1px solid #E2E8F0;padding:14px;border-radius:13px;"><h5 style="font-size:14px;font-weight:800;margin:0 0 5px;">서로를 받아들이는 방식</h5><p style="font-size:13px;color:#475569;margin:0;">{ln}님에게 {rn}님의 일간은 <strong>{_TEN_GOD.get(left_to_right, left_to_right)}</strong>, {rn}님에게 {ln}님의 일간은 <strong>{_TEN_GOD.get(right_to_left, right_to_left)}</strong> 관계로 읽힙니다. 이는 상대를 대하는 역할의 언어이며 애정의 크기나 우열이 아닙니다.</p></div>
        <div style="background:#F8FAFC;border:1px solid #E2E8F0;padding:14px;border-radius:13px;"><h5 style="font-size:14px;font-weight:800;margin:0 0 5px;">상호 보완 가능성</h5><p style="font-size:13px;color:#475569;margin:0;">{ln}님 기준: {_favorable_overlap(left, right)}<br>{rn}님 기준: {_favorable_overlap(right, left)}</p></div>
        <div style="background:#FFF7ED;border:1px solid #FED7AA;padding:14px;border-radius:13px;"><h5 style="font-size:14px;font-weight:800;color:#9A3412;margin:0 0 5px;">{escape(safe_relation)} 관계에서의 활용</h5><p style="font-size:13px;color:#C2410C;margin:0;">{_RELATION_GUIDE[safe_relation]}</p></div>
      </div>
      <h5 style="font-size:14.5px;font-weight:800;color:#0F172A;margin:0 0 8px;">두 명식 사이의 주요 관계 후보</h5>
      <div style="display:grid;gap:7px;">{_interaction_html(interactions)}</div>
      {uncertainty}
      <p style="font-size:11.5px;color:#94A3B8;margin:12px 0 0;">이 리포트는 두 사람의 명식에서 확인되는 상호작용을 관계의 언어로 번역한 참고 자료입니다. 궁합 점수, 최상의 인연, 결혼·이별·동업 성공을 확정하지 않으며 실제 선택과 동의가 명리 판단보다 우선합니다.</p>
    </div>
    """
    return {"title": title, "content": content}
