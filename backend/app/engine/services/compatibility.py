"""Two-person compatibility report derived from two Myeongri core results."""

from __future__ import annotations

import re
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
_EL_OBJ = {"木": "목(木)을", "火": "화(火)를", "土": "토(土)를", "金": "금(金)을", "水": "수(水)를"}


def _this_year(core) -> int:
    raw = (core.timing.daily or {}).get("date") if getattr(core, "timing", None) else None
    try:
        return _date.fromisoformat(raw).year if raw else _date.today().year
    except (TypeError, ValueError):
        return _date.today().year


def _years_text(years: list[int]) -> str:
    return "·".join(str(y) for y in years[:-1]) + (f"·{years[-1]}년" if len(years) > 1 else f"{years[-1]}년")


_CROSS_KIND = {"육합": ("six", "intact"), "충": ("clash", None), "형": ("punish", None), "해": ("harm", None), "파": ("break", None)}


_TAG = {"day": "가까운 자리", "month": "생활·일 자리", "year": "집안·배경 자리"}
SHOW = 2    # 이 세기부터 본문에 쓴다(세기 1은 점수와 근거 상자에만)
FULL = 3    # 이 세기부터 팁까지 쓴다(세기 2는 결론 + 장면)


def _climate_kind(sig: dict) -> str | None:
    tl, tr = sig["climate"]["L"], sig["climate"]["R"]
    return "opposite" if {tl, tr} == {"cold", "hot"} else tl if tl == tr and tl in {"hot", "cold"} else None


def _roles(sig: dict, a: str, b: str) -> dict:
    """방향이 있는 신호에서 누가 어느 쪽인지. 방향이 없으면 그 열쇠를 넣지 않는다."""
    gl, gr = GROUP.get(sig["gods"]["l_sees_r"]), GROUP.get(sig["gods"]["r_sees_l"])
    out: dict = {}
    if gl in _cc.MOVER_GROUPS:
        out["mover"] = a
    elif gr in _cc.MOVER_GROUPS:
        out["mover"] = b
    if sig["stem_rel"] == "control":
        out["s"], out["w"] = (a, b) if gl == "wealth" else (b, a)
    if sig["stem_rel"] == "generate":
        out["g"], out["r"] = (a, b) if gl == "output" else (b, a)
    if _climate_kind(sig) == "opposite":
        out["c"], out["h"] = (a, b) if sig["climate"]["L"] == "cold" else (b, a)
    return out


def _candidates(sig: dict, variant: str, a: str, b: str, shensha: list[dict], interactions: list[dict] | None = None, lover: bool = False) -> list[dict]:
    ex = 1 if variant == "work" else 0
    roles = _roles(sig, a, b)
    out: list[dict] = []

    def add(good: bool, weight: int, hook: str, scene: str = "", tip: str = "", outer: bool = False, tag: str = "", hash_: str = ""):
        out.append({"good": good, "weight": weight, "first": hook, "scene": scene, "extra": tip, "outer": outer, "tag": tag, "hash": hash_})

    for slot, info in sig["branches"].items():
        kind, state = info["kind"], info["state"]
        entry = _cc.KIND.get((kind, state) if kind == "six" else (kind, None))
        if not entry:
            continue
        good, hook, scene, close_tip, work_tip, hash_ = entry
        weight = _cc.SLOT_WEIGHT[variant][slot] + (1 if state == "intact" else 0)
        add(good, weight, f"{_cc.SLOT[variant][slot]} {hook}", scene, work_tip if ex else close_tip, outer=slot in {"year", "month"}, tag=_TAG[slot], hash_=hash_)
    used = {(i["kind"], i["state"] if i["kind"] == "six" else None) for i in sig["branches"].values() if i["kind"]}
    crossed = 0
    for item in sorted(interactions or [], key=lambda i: -i["importance"]):
        key = _CROSS_KIND.get(item["kind"])
        if not key or item["left"] == item["right"] or item["importance"] < 2 or key in used or crossed >= 2:
            continue
        used.add(key)
        crossed += 1
        # 엇갈려 만나는 자리는 세기 1 — 점수에만 넣고 본문에는 쓰지 않는다(약한 신호는 생략).
        add(_cc.KIND[key][0], 1, f"cross:{item['kind']}:{item['left']}:{item['right']}", tag="엇갈려 만나는 자리")
    if sig["stem_rel"] == "six":
        hook, scene, close_tip, work_tip, hash_ = _cc.STEM_SIX
        add(True, 3 if variant == "close" else 2, hook, scene, work_tip if ex else close_tip, tag="서로를 보는 눈", hash_=hash_)
    elif sig["stem_rel"] == "control" and "s" in roles:
        hook, scene, tip, hash_ = (x.format(s=roles["s"], w=roles["w"]) for x in _cc.STEM_CONTROL[variant])
        add(False, 3 if variant == "close" else 2, hook, scene, tip, tag="서로를 보는 눈", hash_=hash_)
    for who, other, els in ((a, b, sig["fills_l"]), (b, a, sig["fills_r"])):
        for el in els[:1]:
            add(True, 2, _cc.FILL.format(x=who, y=other, el=_EL_OBJ[el], effect=_cc.EL_FILL[el]),
                _cc.FILL_SCENE[el].format(x=who, y=other), tag="서로 채워 주는 기운", hash_=_cc.FILL_HASH)
    kind = _climate_kind(sig)
    if kind:
        good, hook, close_scene, work_scene, close_tip, work_tip, hash_ = _cc.CLIMATE[kind]
        fmt = {"c": roles.get("c", ""), "h": roles.get("h", "")}
        very = sig["climate"]["very"]["L"] or sig["climate"]["very"]["R"]
        add(good, 3 + (1 if very else 0), hook.format(**fmt), (work_scene if ex else close_scene).format(**fmt),
            (work_tip if ex else close_tip).format(**fmt), tag="두 사람의 온도", hash_=hash_)
    for el in sig["heavy_both"][:1]:
        if (el, kind) in {("火", "hot"), ("水", "cold")}:
            continue  # 조후 문장과 같은 말이라 한 번만 쓴다
        hook, scene, tip, hash_ = _cc.EL_HEAVY[el]
        add(False, 3, hook, scene, tip, tag="함께 쏠린 기운", hash_=hash_)
    for el in sig["lack_both"][:1]:
        hook, hash_ = _cc.EL_LACK[el]
        add(False, 2, hook, _cc.EL_LACK_SCENE[el], tag="함께 빈 기운", hash_=hash_)
    kinds = {x["kind"]: x for x in sorted(shensha, key=lambda i: i["importance"])}  # 같은 종류는 가장 센 것이 남는다
    if "원진살" in kinds and kinds["원진살"]["importance"] >= 2:
        _, hook, close_scene, work_scene, close_tip, work_tip, hash_ = _cc.SHENSHA["wonjin"]
        add(False, 3, hook, work_scene if ex else close_scene, work_tip if ex else close_tip, tag="서로 거슬리는 기운", hash_=hash_)
    if variant == "close" and not lover and "도화살" in kinds and kinds["도화살"]["importance"] >= 2:  # 동업 풀이에는 쓰지 않는다
        add(True, 2, _cc.SHENSHA["dohwa"][1], _cc.DOHWA_SCENE, tag="서로 끌리는 매력", hash_=_cc.SHENSHA["dohwa"][6])
    return out


def _pick(cands: list[dict], good: bool, limit: int = 4) -> list[dict]:
    pool = sorted((c for c in cands if c["good"] is good and not c.get("outer") and c["weight"] >= SHOW), key=lambda c: -c["weight"])
    seen, out = set(), []
    for c in pool:
        if c["first"] in seen:
            continue
        seen.add(c["first"])
        out.append(c)
    return out[:limit]


def _ranked(items: list[dict], used: set | None = None) -> list[str]:
    """센 신호(세기 3↑)는 결론 + 장면 + 팁, 세기 2는 결론 + 장면, 세기 1은 쓰지 않는다. 같은 팁은 한 번만."""
    texts = []
    used = set() if used is None else used
    for c in items:
        if c["weight"] < SHOW:
            continue
        scene = c["scene"] if c["scene"] and c["scene"] not in used else ""   # 같은 관계가 두 자리에 있어도 장면은 한 번만
        used.add(c["scene"])
        if c["weight"] < FULL:          # 세기 2: 결론 + 장면(팁은 붙이지 않는다). 11/23 분량 보강
            texts.append(" ".join(x for x in (c["first"], scene) if x))
            continue
        tip = c["extra"] if c["extra"] and c["extra"] not in used else ""
        used.add(c["extra"])
        texts.append(" ".join(x for x in (c["first"], scene, tip) if x))
    return texts


def _intimacy(sig: dict, kinds: dict, a: str = "", b: str = "") -> list[str]:
    """연인 풀이의 속궁합 4문단: ① 한마디 결론 + 첫 끌림 ② 다가가는 방식 ③ 밤의 흐름과 푸는 법 ④ 속도·주도권·온도. 있는 신호만 쓴다."""
    day = sig["branches"].get("day") or {}
    key = (day.get("kind"), day.get("state") if day.get("kind") == "six" else None)
    ck = _climate_kind(sig)
    roles = _roles(sig, a, b)
    stem_rel = sig.get("stem_rel")
    kind = (_cc.INTIMACY_TYPE.get(key) or _cc.INTIMACY_TYPE_STEM.get(stem_rel)
            or _cc.INTIMACY_TYPE_CLIMATE.get(ck) or _cc.INTIMACY_TYPE_DEFAULT)

    first = [f"한마디로 두 분은 {kind}예요."]
    if _cc.INTIMACY_STEM.get(stem_rel):
        first.append(_cc.INTIMACY_STEM[stem_rel].format(**{k: roles.get(k, "") for k in ("s", "w", "g", "r")}))
    if sig.get("other_stem_six") and stem_rel != "six":
        first.append(_cc.INTIMACY_STEM_OTHER)

    gods = sig["gods"]
    second = []
    pairs = ((a, b, gods["l_sees_r"]), (b, a, gods["r_sees_l"]))
    if pairs[0][2] in _cc.INTIMACY_GOD:
        second.append(_cc.INTIMACY_GOD[pairs[0][2]].format(x=a, y=b))
    if pairs[1][2] in _cc.INTIMACY_GOD:
        if pairs[1][2] == pairs[0][2]:
            second.append(_cc.INTIMACY_GOD_SAME.format(x=a, y=b))
        else:
            second.append(_cc.INTIMACY_GOD_SECOND + _cc.INTIMACY_GOD[pairs[1][2]].format(x=b, y=a))
    ta, tb = sig["self"]["L"]["top"], sig["self"]["R"]["top"]
    if ta in _cc.INTIMACY_MOOD_PHRASE and tb in _cc.INTIMACY_MOOD_PHRASE:
        pa, pb = _cc.INTIMACY_MOOD_PHRASE[ta], _cc.INTIMACY_MOOD_PHRASE[tb]
        if ta == tb:
            second.append(_cc.INTIMACY_MOOD_SAME.format(a=pa))
        else:
            second.append(_cc.INTIMACY_MOOD_DIFF.format(x=a, y=b, a=pa, b=pb))

    third = [_cc.INTIMACY_DAY.get(key, _cc.INTIMACY_DAY_NONE)]
    for who, other, els in ((a, b, sig["fills_l"]), (b, a, sig["fills_r"])):
        if els and els[0] in _cc.INTIMACY_FILL:
            line = _cc.INTIMACY_FILL[els[0]].format(x=who, y=other)
            third.append(("반대로 " + line) if len(third) > 1 else line)

    fourth = []
    sl, sr = sig["self"]["L"]["strength"], sig["self"]["R"]["strength"]
    if sl and sr:
        if sl == sr:
            fourth.append(_cc.INTIMACY_LEAD[(sl, sr)].format(a=a, b=b))
        else:
            strong, weak = (a, b) if sl == "strong" else (b, a)
            fourth.append(_cc.INTIMACY_LEAD[("mixed", None)].format(s=strong, w=weak))
    if ck:
        fourth.append(_cc.INTIMACY_CLIMATE[ck].format(c=roles.get("c", ""), h=roles.get("h", "")))
    if "도화살" in kinds and kinds["도화살"]["importance"] >= 2:
        fourth.append(_cc.INTIMACY_DOHWA)

    return _drop_repeated_sentences([" ".join(part) for part in (first, second, third, fourth) if part])


def _drop_repeated_sentences(lines: list[str]) -> list[str]:
    """두 사람이 같은 유형이면 이름만 다른 문장이 겹치므로, 이미 나온 문장은 한 번만 쓴다."""
    seen: set[str] = set()
    out = []
    for line in lines:
        kept = []
        for sentence in re.split(r"(?<=[.!?])\s+", line):
            if sentence not in seen:
                seen.add(sentence)
                kept.append(sentence)
        if kept:
            out.append(" ".join(kept))
    return out


def _raw(cands: list[dict], extra_good: int = 0) -> int:
    """신호의 세기를 더하고 뺀 값. 같은 문장은 한 번만 센다."""
    seen, total = set(), extra_good
    for c in cands:
        if c["first"] in seen:
            continue
        seen.add(c["first"])
        total += c["weight"] if c["good"] else -c["weight"]
    return total


def _score(raw: int) -> int:
    return max(25, min(95, 62 + 3 * raw))


def _tier(raw: int) -> tuple:
    return next(t for t in _cc.TIERS if raw >= t[0])


def _pair_image(left, right, a: str, b: str) -> tuple[str, str]:
    """두 일간의 쌍 그림: (해시태그, 그림 한 문장 + 생활 말 한 문장)."""
    ls, rs = left.natal_facts.day_master.stem, right.natal_facts.day_master.stem
    first_is_left = _cc.STEMS.index(ls) <= _cc.STEMS.index(rs)
    key = (ls + rs) if first_is_left else (rs + ls)
    tag, image, plain = _cc.PAIR[key]
    p, q = (a, b) if first_is_left else (b, a)
    return tag, f"{image} {plain}".format(p=p, q=q)


def _summary(cands: list[dict], variant: str, extra_good: int, pair: tuple[str, str]) -> str:
    raw = _raw(cands, extra_good)
    _, label, close_text, work_text = _tier(raw)
    uniq: dict[str, dict] = {}
    for c in sorted(cands, key=lambda c: -c["weight"]):
        uniq.setdefault(c["first"], c)
    goods = [c for c in uniq.values() if c["good"]]
    hards = [c for c in uniq.values() if not c["good"]]
    # 해시태그 셋: 쌍 그림 · 가장 센 맞는 신호 · 가장 센 부딪히는 신호(본문에 쓰는 신호에서만).
    tags = [pair[0]]
    top_good = next((c["hash"] for c in goods if c["weight"] >= SHOW and c["hash"]), _cc.SHENSHA["dohwa"][6] if extra_good else "")
    top_hard = next((c["hash"] for c in hards if c["weight"] >= SHOW and c["hash"]), "")
    tags += [t for t in (top_good, top_hard) if t]
    lines = [f'<p class="compat-verdict"><strong>{_score(raw)}점</strong> · {escape(label)}</p>',
             f'<p class="compat-image">{escape(pair[1])}</p>',
             f'<p class="compat-tags">{escape(" ".join("#" + t for t in tags))}</p>',
             f"<p>{escape(work_text if variant == 'work' else close_text)}</p>",
             f"<p>맞는 신호 {len(goods) + (1 if extra_good else 0)}개 · 부딪히는 신호 {len(hards)}개</p>",
             f'<p class="reading-caption">{escape(_cc.SCORE_NOTE)}</p>']
    return '<section data-compat-section="summary"><h2>한눈에 보기</h2>' + "".join(lines) + "</section>"


def _decade(sig: dict, a: str, b: str) -> list[str]:
    cl, cr = sig["cycles"]["L"], sig["cycles"]["R"]
    d = _cc.DECADE
    lines: list[str] = []
    if cl and cr:
        lines.append(d["now"].format(a=a, b=b, la=cl["start_age"], lb=cl["end_age"], lc=_cc.CYCLE[cl["group"]],
                                     ra=cr["start_age"], rb=cr["end_age"], rc=_cc.CYCLE[cr["group"]]))
        lines.append(d["same"] if cl["group"] == cr["group"] else d["diff"])
    rows = sig["years"]
    both_good = [r["year"] for r in rows if r["L"] == "good" and r["R"] == "good"]
    both_hard = [r["year"] for r in rows if r["L"] == "hard" and r["R"] == "hard"]
    l_carry = [r["year"] for r in rows if r["L"] == "good" and r["R"] == "hard"]
    r_carry = [r["year"] for r in rows if r["R"] == "good" and r["L"] == "hard"]
    if both_good:
        lines.append(d["both_good"].format(years=_years_text(both_good[:3])))
    if both_hard:
        lines.append(d["both_hard"].format(years=_years_text(both_hard[:3])))
    if l_carry:
        lines.append(d["carry"].format(years=_years_text(l_carry[:2]), s=a, w=b))
    if r_carry:
        lines.append(d["carry"].format(years=_years_text(r_carry[:2]), s=b, w=a))
    if not (both_good or both_hard or l_carry or r_carry):
        lines.append(d["none"])
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
    """두 사람의 원국을 맞대어 읽는 궁합. 신호가 있는 만큼만 쓴다(compat_signals 참고). 문장 규칙은 compat_copy 머리말."""
    a, b = left_name or "회원", right_name or "상대방"
    safe_relation = relation if relation in _RELATION_GUIDE else "친구 / 지인"
    variant = _cc.VARIANT[safe_relation]
    lover = safe_relation == "연인 / 결혼"
    who = "lover" if lover else "work" if variant == "work" else "friend"
    titles = _cc.TITLES[who]
    sig = analyze_pair(left, right, _this_year(left))
    interactions = _cross_interactions(left, right)
    shensha = [i for i in interactions if i["kind"] in {"원진살", "도화살"}]
    cands = _candidates(sig, variant, a, b, shensha, interactions, lover=lover)
    kinds_ss = {x["kind"]: x for x in shensha}
    good, hard = _pick(cands, True), _pick(cands, False)
    gods = sig["gods"]
    view = _cc.VIEW[variant]
    unknown = left.uncertainty.time_unknown or right.uncertainty.time_unknown

    def sec(key: str, title: str, values: list[str]) -> str:
        return f'<section data-compat-section="{key}"><h2>{escape(title)}</h2>{paragraphs(values)}</section>'

    # 첫인상: 먼저 움직이는 쪽(방향이 있을 때만) → 그 사람의 눈에 비친 상대 → 반대쪽.
    mover = _roles(sig, a, b).get("mover")
    view_a = view[gods["l_sees_r"]].format(x=a, y=b)
    view_b = (_cc.VIEW_SAME.format(x=a, y=b) if gods["r_sees_l"] == gods["l_sees_r"]
              else view[gods["r_sees_l"]].format(x=b, y=a))
    if mover:
        first_view, second_view = (view_a, view_b) if mover == a else (view_b, view_a)
        see = [f"{_cc.MOVER[who].format(m=mover)} {first_view}", second_view]
    else:
        see = [f"{_cc.MOVER_NONE[who]} {view_a}", view_b]
    outer = sorted((c for c in cands if c.get("outer") and c["weight"] >= SHOW), key=lambda c: -c["weight"])[:2]
    shared: set = set()
    outer_text = _ranked(outer, shared)
    fr_friction, fr_repair = _cc.FR[variant][gods["l_sees_r"]]
    fmt = {"a": a, "b": b}
    me_a, me_b = sig["self"]["L"], sig["self"]["R"]
    same_strength = me_a["strength"] == me_b["strength"]
    st = _cc.STRENGTH_SELF[variant]
    if me_a["top"] == me_b["top"]:  # 같은 문장이 이름만 바뀌어 두 번 나오지 않게 한 번에 쓴다
        inner = [_cc.EL_SELF_SAME.format(a=a, b=b, trait=_cc.EL_SELF[me_a["top"]]) + " "
                 + (_cc.STRENGTH_BOTH[variant][me_b["strength"]] if same_strength
                    else f"{a}님은 {st[me_a['strength']]} {b}님은 {st[me_b['strength']]}")]
    else:
        inner = [f"{a}님은 {_cc.EL_SELF[me_a['top']]} 사람이에요." + ("" if same_strength else " " + st[me_a["strength"]]),
                 f"{b}님은 {_cc.EL_SELF[me_b['top']]} 사람이에요. "
                 + (_cc.STRENGTH_BOTH[variant][me_b["strength"]] if same_strength else st[me_b["strength"]])]
    inner += [
             _cc.NEED_SAME.format(need=_iyeyo(_cc.NEED[variant][gods["l_sees_r"]])) if gods["l_sees_r"] == gods["r_sees_l"] else
             f"{a}님이 {b}님에게 바라는 것은 {_iyeyo(_cc.NEED[variant][gods['l_sees_r']])}. "
             f"{b}님이 {a}님에게 바라는 것은 {_iyeyo(_cc.NEED[variant][gods['r_sees_l']])}."]
    dohwa_love = 2 if lover and "도화살" in kinds_ss and kinds_ss["도화살"]["importance"] >= 2 else 0
    body = _summary(cands, variant, dohwa_love, _pair_image(left, right, a, b))
    body += sec("outer", titles["outer"][0 if mover else 1], see + outer_text)
    if lover:  # 끌림·스킨십 이야기는 연인 풀이에만 쓴다
        body += sec("intimacy", titles["intimacy"], _intimacy(sig, kinds_ss, a, b))
    body += sec("inner", titles["inner"], inner)
    body += sec("good", titles["good"], _ranked(good, shared) or [_cc.EMPTY["good"]])
    body += sec("hard", titles["hard"], _ranked(hard, shared) or [_cc.EMPTY["hard"]])
    body += sec("repair", titles["repair"], [fr_friction.format(**fmt), fr_repair.format(**fmt),
                                             _cc.FR_AFTER[variant][gods["l_sees_r"]].format(**fmt)])
    carry = any({r["L"], r["R"]} == {"good", "hard"} for r in sig["years"])
    body += sec("decade", titles["decade"][0 if carry else 1], _decade(sig, a, b))
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
