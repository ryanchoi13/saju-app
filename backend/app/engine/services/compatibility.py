"""Two-person compatibility report derived from two Myeongri core results."""

from __future__ import annotations

from html import escape
from app.engine.services.reading_editorial import THEME_VERSION as VERSION, section, paragraphs
from itertools import product

from app.engine.constants import GAN_WUXING
from app.engine.semantic.applied import build_applied_state, recommended_directions
from app.engine.core.models import MyeongriCoreResult
from app.engine.facts.ten_gods import get_ten_god
from app.engine.relationships.compatibility_shensha import calculate_relationship_shensha


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
    "동업 / 비즈니스": "역할·의사결정권·비용을 나누는 기준을 문서로 나누고, 의견 충돌과 책임 문제를 분리해 다루세요.",
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
    found.extend(calculate_relationship_shensha(left.natal_facts.pillars, right.natal_facts.pillars))
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
    tense = [item for item in items if item["kind"] in {"천간극", "충", "형", "해", "파", "원진살"}]
    return supportive, tense


def _signal_level(items: list[dict]) -> str:
    if any(item["importance"] == 3 for item in items):
        return "뚜렷함"
    if items:
        return "보통"
    return "천천히 확인"


def _plain_reason(supportive: list[dict], tense: list[dict]) -> str:
    day_wonjin = [item for item in tense if item["kind"] == "원진살" and item["importance"] == 3]
    independently_corroborated = any(
        other is not wonjin
        and not (
            other["kind"] == "해"
            and other["left"] == wonjin["left"]
            and other["right"] == wonjin["right"]
            and frozenset(other["symbols"]) == frozenset(wonjin["symbols"])
        )
        for wonjin in day_wonjin
        for other in tense
    )
    if day_wonjin and independently_corroborated:
        return "끌림과 별개로 감정을 묵히면 관계가 빠르게 틀어질 수 있습니다. 이 궁합은 서운함을 오래 쌓아 두면 안 됩니다."
    if supportive and tense:
        return "서로를 당기는 접점과 부딪히는 지점이 함께 있어, 끌림은 생기기 쉽지만 관계를 오래 유지하려면 생활 합의가 필요합니다."
    if supportive:
        return "서로 다른 방식을 연결하는 접점이 확인되어, 함께 있을 때 친밀감과 협력의 흐름을 만들기 비교적 쉽습니다."
    if tense:
        return "차이가 먼저 눈에 들어오는 관계라 강한 자극이 될 수 있지만, 말투와 결정 방식이 반복 갈등으로 굳지 않게 해야 합니다."
    return "강하게 붙거나 밀어내는 신호보다 서로를 알아 가는 과정이 중요한 관계입니다. 실제 대화와 생활 경험이 관계의 깊이를 좌우합니다."


def _shensha_positions(core: MyeongriCoreResult, name: str) -> list[str]:
    support_key = f"shensha:{name}"
    positions = []
    for item in core.evidence:
        if support_key not in item.supports:
            continue
        for match in item.source_values.get("natal_matches", []):
            position = match.get("position")
            if position and position not in positions:
                positions.append(position)
    return positions


def _relationship_shensha_text(
    left: MyeongriCoreResult,
    right: MyeongriCoreResult,
    interactions: list[dict],
    ln: str,
    rn: str,
) -> str:
    sentences = []
    wonjin = [item for item in interactions if item["kind"] == "원진살"]
    peach = [item for item in interactions if item["kind"] == "도화살"]
    if any(item["importance"] == 3 for item in wonjin):
        sentences.append("두 사람의 일지에 <strong>원진살</strong>이 성립합니다. 가까울수록 사소한 서운함이 크게 남을 수 있어, 침묵이 길어지면 관계가 급격히 냉각될 수 있습니다.")
    elif wonjin:
        sentences.append("두 명식의 일부 자리에서 <strong>원진살</strong>이 확인됩니다. 상대의 의도를 추측해서 결론 내리면 오해가 길어질 수 있습니다.")
    if any(item["importance"] >= 2 for item in peach):
        sentences.append("<strong>도화살</strong>이 상대 명식과 맞물려 서로를 매력적으로 의식하기 쉽습니다. 다만 이것만으로 애정의 깊이나 외도를 판단하지는 않습니다.")
    elif peach:
        sentences.append("두 사람 사이에 약한 <strong>도화살</strong> 접점이 있어 첫인상이나 사회적인 매력이 호감에 영향을 줄 수 있습니다.")

    isolation_labels = []
    for core, name in ((left, ln), (right, rn)):
        for key, label in (("solitary_star", "고신살"), ("widow_star", "과숙살")):
            positions = _shensha_positions(core, key)
            important = [position for position in positions if position in {"month", "day"}]
            if important:
                position_text = "·".join(_PILLAR_LABEL[position] for position in important)
                isolation_labels.append(f"{name}님의 {label}({position_text})")
    if isolation_labels:
        joined = ", ".join(isolation_labels)
        sentences.append(f"{joined}이 확인됩니다. 갈등할 때 혼자 정리하려는 경향이 강해질 수 있으므로, 시간을 갖더라도 다시 대화할 시점을 정해 두는 것이 중요합니다.")
    if not sentences:
        return "현재 확인된 핵심 자리에서는 관계 판단을 크게 바꿀 만한 원진·도화·고신·과숙 신호가 두드러지지 않습니다."
    return " ".join(sentences)


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
    state = build_applied_state(core, "natal")
    wanted = {e for d in recommended_directions(state) for e in d.get("elements", [])}
    present = {item.element for item in other.natal_facts.element_inventory.occurrences}
    overlap = wanted & present
    if not wanted:
        return "현재 코어가 특정 유리 오행을 확정하지 않아 상대 명식의 보완 작용도 단정하지 않습니다."
    if overlap:
        return f"상대 명식에는 이쪽 종합판단의 유리 작용과 겹치는 오행({', '.join(sorted(overlap))})이 관찰됩니다. 다만 존재만으로 실제 보완이나 좋은 궁합이 확정되는 것은 아닙니다."
    return "상대 명식의 오행 존재만으로 이쪽의 유리 작용을 직접 보완한다고 보기 어렵습니다. 필요한 생활 역할을 말과 행동으로 조정하는 편이 중요합니다."


# ── 궁합 v2 (2026-11-20) ─────────────────────────────────────────────────────────────
# 신호 계산은 compat_signals, 문구는 compat_copy. 위의 _cross_interactions 등은 '판단 근거' 상자에만 쓴다.
import re
from datetime import date as _date

from app.engine.services import compat_copy as _cc
from app.engine.services.compat_signals import GROUP, analyze_pair

def _iyeyo(word: str) -> str:
    """받침 있으면 이에요, 없으면 예요."""
    last = word.rstrip()[-1]
    return word + ("이에요" if (ord(last) - 0xAC00) % 28 else "예요")


_EL_KO = {"木": "목(木)", "火": "화(火)", "土": "토(土)", "金": "금(金)", "水": "수(水)"}


def _this_year(core) -> int:
    raw = (core.timing.daily or {}).get("date") if getattr(core, "timing", None) else None
    try:
        return _date.fromisoformat(raw).year if raw else _date.today().year
    except (TypeError, ValueError):
        return _date.today().year


def _years_text(years: list[int]) -> str:
    return "·".join(str(y) for y in years[:-1]) + (f"·{years[-1]}년" if len(years) > 1 else f"{years[-1]}년")


_CROSS_KIND = {"육합": ("six", "intact"), "충": ("clash", None), "형": ("punish", None), "해": ("harm", None), "파": ("break", None)}


def _candidates(sig: dict, variant: str, a: str, b: str, shensha: list[dict], interactions: list[dict] | None = None) -> list[dict]:
    ex = 1 if variant == "work" else 0
    out: list[dict] = []

    def add(good: bool, weight: int, first: str, extra: str):
        out.append({"good": good, "weight": weight, "first": first, "extra": extra})

    for slot, info in sig["branches"].items():
        kind, state = info["kind"], info["state"]
        entry = _cc.KIND.get((kind, state) if kind == "six" else (kind, None))
        if not entry:
            continue
        good, first, close_extra, work_extra = entry
        weight = _cc.SLOT_WEIGHT[variant][slot] + (1 if state == "intact" else 0)
        add(good, weight, f"{_cc.SLOT[variant][slot]} {first}", work_extra if ex else close_extra)
    used = {(i["kind"], i["state"] if i["kind"] == "six" else None) for i in sig["branches"].values() if i["kind"]}
    crossed = 0
    for item in sorted(interactions or [], key=lambda i: -i["importance"]):
        key = _CROSS_KIND.get(item["kind"])
        if not key or item["left"] == item["right"] or item["importance"] < 2 or key in used or crossed >= 2:
            continue
        good, first, close_extra, work_extra = _cc.KIND[key]
        used.add(key)
        crossed += 1
        where = f"{a}님의 {_cc.ROLE[item['left']]}, {b}님의 {_cc.ROLE[item['right']]}가 만나는 곳에서는"
        add(good, 1, f"{where} {re.sub(r'^두 사람[은이] ', '', first)}", work_extra if ex else close_extra)
    stem = _cc.STEM_CAND.get(sig["stem_rel"])
    if stem:
        add(stem[0], 3 if variant == "close" else 2, stem[1], stem[3] if ex else stem[2])
    for who, other, els in ((a, b, sig["fills_l"]), (b, a, sig["fills_r"])):
        for el in els[:1]:
            extra = (f"{who}님이 약한 부분은 {other}님에게 맡겨 보세요." if ex
                     else f"{who}님이 지칠 때는 {other}님과 함께하는 시간을 일부러 늘려 보세요.")
            add(True, 2, f"{other}님의 원국에는 {who}님에게 필요한 {_EL_KO[el]} 기운이 넉넉해서, 곁에 있으면 {who}님은 {_cc.EL_FILL[el]}.", extra)
    tl, tr = sig["climate"]["L"], sig["climate"]["R"]
    kind = "opposite" if {tl, tr} == {"cold", "hot"} else tl if tl == tr and tl in {"hot", "cold"} else None
    if kind:
        good, first, close_extra, work_extra = _cc.CLIMATE[kind]
        very = sig["climate"]["very"]["L"] or sig["climate"]["very"]["R"]
        add(good, 3 + (1 if very else 0), first, work_extra if ex else close_extra)
    for el in sig["heavy_both"][:1]:
        if (el, kind) in {("火", "hot"), ("水", "cold")}:
            continue  # 조후 문장과 같은 말이라 한 번만 쓴다
        text, tip = _cc.EL_HEAVY[el]
        add(False, 3, f"두 사람 모두 {_EL_KO[el]} 기운이 강해서 {text}.", tip)
    for el in sig["lack_both"][:1]:
        text, tip = _cc.EL_LACK[el]
        add(False, 2, f"두 사람 모두 {_EL_KO[el]} 기운이 비어 있어 {text}.", tip)
    kinds = {x["kind"]: x for x in sorted(shensha, key=lambda i: i["importance"])}  # 같은 종류는 가장 센 것이 남는다
    if "원진살" in kinds and kinds["원진살"]["importance"] >= 2:
        _, first, close_extra, work_extra = _cc.SHENSHA["wonjin"]
        add(False, 3, first, work_extra if ex else close_extra)
    if variant == "close" and "도화살" in kinds and kinds["도화살"]["importance"] >= 2:  # 동업 풀이에는 쓰지 않는다
        _, first, close_extra, work_extra = _cc.SHENSHA["dohwa"]
        add(True, 2, first, work_extra if ex else close_extra)
    return out


def _pick(cands: list[dict], good: bool, limit: int = 4) -> list[dict]:
    pool = sorted((c for c in cands if c["good"] is good), key=lambda c: -c["weight"])
    seen, out = set(), []
    for c in pool:
        if c["first"] in seen:
            continue
        seen.add(c["first"])
        out.append(c)
    return out[:limit]


def _ranked(items: list[dict]) -> list[str]:
    """센 신호 둘은 두 문장(풀이 + 처방), 나머지는 한 문장. 같은 처방 문장은 한 번만. 신호가 없으면 아무것도 채우지 않는다."""
    texts, used = [], set()
    for i, c in enumerate(items):
        extra = c["extra"] if i < 2 and c["extra"] not in used else ""
        used.add(c["extra"])
        texts.append(f"{c['first']} {extra}".strip())
    return texts


def _decade(sig: dict, a: str, b: str) -> list[str]:
    cl, cr = sig["cycles"]["L"], sig["cycles"]["R"]
    lines: list[str] = []
    if cl and cr:
        lines.append(
            f"지금 {a}님은 {cl['start_age']}~{cl['end_age']}세의 {_cc.CYCLE[cl['group']]} 10년을, "
            f"{b}님은 {cr['start_age']}~{cr['end_age']}세의 {_cc.CYCLE[cr['group']]} 10년을 지나고 있어요.")
        lines.append("두 사람의 10년이 같은 결이라 서로의 사정을 이해하기 쉬워요." if cl["group"] == cr["group"]
                     else "10년의 결이 서로 달라서, 한 사람이 바쁠 때 다른 사람은 여유가 있을 수 있어요. 바쁜 쪽이 먼저 상황을 알려 주세요.")
    rows = sig["years"]
    both_good = [r["year"] for r in rows if r["L"] == "good" and r["R"] == "good"]
    both_hard = [r["year"] for r in rows if r["L"] == "hard" and r["R"] == "hard"]
    l_carry = [r["year"] for r in rows if r["L"] == "good" and r["R"] == "hard"]
    r_carry = [r["year"] for r in rows if r["R"] == "good" and r["L"] == "hard"]
    if both_good:
        lines.append(f"{_years_text(both_good[:3])}은 두 사람 모두 기운을 받는 해예요. 함께 시작하고 싶은 일이 있다면 이때 맞춰 보세요.")
    if both_hard:
        lines.append(f"{_years_text(both_hard[:3])}은 두 사람 모두 부담이 커지는 해예요. 큰 약속은 서두르지 말고 서로를 챙기는 데 쓰세요.")
    if l_carry:
        lines.append(f"{_years_text(l_carry[:2])}은 {a}님은 힘을 받지만 {b}님은 부담이 있는 해예요. {a}님이 한 걸음 더 받쳐 주세요.")
    if r_carry:
        lines.append(f"{_years_text(r_carry[:2])}은 {b}님은 힘을 받지만 {a}님은 부담이 있는 해예요. {b}님이 한 걸음 더 받쳐 주세요.")
    if not (both_good or both_hard or l_carry or r_carry):
        lines.append("앞으로 10년 동안 두 사람이 눈에 띄게 겹치는 해는 없어요. 해마다 서로의 컨디션을 한 번씩 물어봐 주세요.")
    return lines


def _evidence(sig: dict, interactions: list[dict], left, right, ln: str, rn: str) -> str:
    gods = sig["gods"]
    return (
        '<details data-theme-section="evidence" class="reading-evidence">'
        '<summary>이 풀이의 근거 · 명리 용어 포함</summary>'
        f'<p>{escape(ln)}님 기준 {escape(rn)}님은 {_TEN_GOD.get(gods["l_sees_r"], gods["l_sees_r"])}, '
        f'{escape(rn)}님 기준 {escape(ln)}님은 {_TEN_GOD.get(gods["r_sees_l"], gods["r_sees_l"])}입니다. '
        f'{_day_master_relation(left.natal_facts.day_master.stem, right.natal_facts.day_master.stem)}</p>'
        + _interaction_html(interactions) +
        '<p>합의 상태는 두 사람 원국 안의 충·같은 글자 유무로만 가르며, 오행이 바뀌는 합화는 판정하지 않습니다. '
        '세운은 올해부터 10년, 각자의 오행 3단계(좋음·무난·피함)로 봤습니다.</p></details>')


def build_compatibility_report(left: MyeongriCoreResult, right: MyeongriCoreResult, left_name: str, right_name: str, relation: str) -> dict[str, str]:
    """두 사람의 원국을 맞대어 읽는 궁합. 점수·단정 없이, 신호가 있는 만큼만 쓴다(compat_signals 참고)."""
    a, b = left_name or "회원", right_name or "상대방"
    safe_relation = relation if relation in _RELATION_GUIDE else "친구 / 지인"
    variant = _cc.VARIANT[safe_relation]
    sig = analyze_pair(left, right, _this_year(left))
    interactions = _cross_interactions(left, right)
    shensha = [i for i in interactions if i["kind"] in {"원진살", "도화살"}]
    cands = _candidates(sig, variant, a, b, shensha, interactions)
    good, hard = _pick(cands, True), _pick(cands, False)
    gods = sig["gods"]
    view = _cc.VIEW[variant]
    unknown = left.uncertainty.time_unknown or right.uncertainty.time_unknown

    def sec(key: str, title: str, values: list[str]) -> str:
        return f'<section data-compat-section="{key}"><h2>{escape(title)}</h2>{paragraphs(values)}</section>'

    see = [f"{a}님에게 {b}님은 {view[gods['l_sees_r']]}으로 느껴져요.",
           f"{b}님에게 {a}님은 {view[gods['r_sees_l']]}으로 느껴져요.",
           _cc.STEM_REL[sig["stem_rel"]],
           f"{a}님이 {b}님에게 바라는 것은 {_iyeyo(_cc.NEED[variant][gods['l_sees_r']])}. "
           f"{b}님이 {a}님에게 바라는 것은 {_iyeyo(_cc.NEED[variant][gods['r_sees_l']])}."]
    fr_friction, fr_repair = _cc.FR[variant][gods["l_sees_r"]]
    fmt = {"a": a, "b": b}
    me_a, me_b = sig["self"]["L"], sig["self"]["R"]
    same_strength = me_a["strength"] == me_b["strength"]
    selfs = [f"{a}님은 {_cc.EL_SELF[me_a['top']]} 사람이에요." + ("" if same_strength else " " + _cc.STRENGTH_SELF[variant][me_a["strength"]]),
             f"{b}님은 {_cc.EL_SELF[me_b['top']]} 사람이에요. "
             + (_cc.STRENGTH_BOTH[variant][me_b["strength"]] if same_strength else _cc.STRENGTH_SELF[variant][me_b["strength"]])]
    body = sec("view", "서로가 보는 서로", see)
    body += sec("self", "각자 관계에서 보이는 모습", selfs)
    body += sec("good", "잘 맞는 점", _ranked(good) or ["두 원국을 맞대어 봐도 눈에 띄게 맞물리는 자리는 없어요. 닮은 점으로 가까워지기보다, 서로 다른 점을 알아 가며 가까워지는 사이예요."])
    body += sec("hard", "부딪히기 쉬운 점", _ranked(hard) or ["두 원국을 맞대어 봐도 크게 부딪히는 신호는 보이지 않아요. 다만 생활 방식은 짐작하지 말고 직접 물어서 알아 가세요."])
    body += sec("repair", "다툰 뒤 풀리는 법", [fr_friction.format(**fmt), fr_repair.format(**fmt)])
    body += sec("decade", "앞으로 10년, 두 사람의 흐름", _decade(sig, a, b))
    title, items = (_cc.CLOSING_FRIEND if safe_relation == "친구 / 지인" else _cc.CLOSING[variant])
    body += sec("closing", title, list(items))
    name_title = f"{escape(a)}님 & {escape(b)}님 정통 사주 궁합 감명서"
    uncertainty = (
        '<p class="reading-caption" data-compat-uncertainty="true">출생 시간을 모르는 쪽은 연·월·일 여섯 글자만으로 봤어요. '
        '시간이 확인되면 풀이가 더 정확해질 수 있어요.</p>' if unknown else "")
    content = (
        f'<div class="long-reading theme-reading" data-theme="gunghap" data-reading-status="{escape(safe_relation, quote=True)}" '
        f'data-narrative-version="{VERSION}" data-copy-version="{_cc.COPY_VERSION}">'
        + body + _evidence(sig, interactions, left, right, a, b) + uncertainty +
        '<p class="reading-caption">구매하거나 업데이트한 시점의 두 사람 정보를 바탕으로 쓴 풀이예요. 다시 열어도 저장된 내용은 유지됩니다.</p></div>')
    return {"title": name_title, "content": content, "narrative_version": VERSION}
