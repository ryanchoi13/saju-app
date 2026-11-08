"""올해 운세 보강(2026-11-08) — 사람마다 근거가 다른 세 단락.

  A. 올해가 내 사주에 닿는 자리 : 올해 간지 × 원국(충·육합·반합·삼합·형·자형, 일간 천간충·합)
  B. 올해와 보완 기운          : '나의 사주' 화면과 같은 보완 기운(element_balance.natal_balance)
  C. 대운 속의 올해            : 지금 대운의 십성 무리 ↔ 올해 십성 무리의 생극, 몇 번째 해

설계: 프로젝트 문서 annual-year-boost-design-2026-11-08 (정오님 승인 11/8).
- 파·해는 쓰지 않는다(10/11 톤 판정에서 뺀 기준과 같음). 반합은 왕지(子午卯酉)가 낀 두 글자만
- 자리마다 관계 하나, 무게 순 최대 둘. 관계가 없으면 없다고 짧게 쓴다(지어내지 않음)
- 문체·길이·금기는 annual_v2.validate_year 가 함께 검사한다(문장 46자 이내, 시점 표현·얼버무림 금지)
- 엔진 코어는 건드리지 않고, 같은 입력이면 항상 같은 글
"""
from __future__ import annotations

from app.engine.constants import GAN_WUXING, ZHI_WUXING
from app.engine.services.lifetime_flow import (
    BRANCH_CLASH, BRANCH_SIX, PAIR_PUNISH, TRIPLES, STEM_CLASH, STEM_COMBINE, GOD_GROUP,
    _completes_punish, _completes_triple,
)

TOUCH_VERSION = "annual-touch-1"

READ = dict(zip("甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥",
                "갑을병정무기경신임계자축인묘진사오미신유술해"))
EL_LABEL = {"木": "목(木)", "火": "화(火)", "土": "토(土)", "金": "금(金)", "水": "수(水)"}
POS_NAME = {"year": "년지", "month": "월지", "day": "일지", "hour": "시지"}
WANG = set("子午卯酉")
SELF_PUNISH = set("辰午酉亥")


def _has_final(ch: str) -> bool:
    """글자(한자는 한글 읽기, 괄호 표기는 앞 글자)의 받침 여부."""
    syl = READ.get(ch, ch)[-1]
    code = ord(syl) - 0xAC00
    return 0 <= code < 11172 and code % 28 != 0


def _j(word: str, pair: str) -> str:
    """조사. pair 예: '과와', '이가', '은는', '을를'. 괄호 표기면 괄호 앞 글자로 판단."""
    base = word.split("(")[0] if "(" in word else word
    return word + (pair[0] if _has_final(base[-1]) else pair[1])


# ---------------------------------------------------------------------------
# A. 닿는 자리
# ---------------------------------------------------------------------------
WEIGHT = {"stem_clash": 5, "triple_punish": 4.5, "clash": 4, "triple": 3.5, "punish": 3,
          "six": 2.5, "half": 2, "self": 2, "stem_combine": 2}

ATTITUDE = {
    "clash": dict(
        year="윗사람·집안과 부딪히는 일은 한 박자 늦춰 대응하세요.",
        month="일터의 변화에 휩쓸리기보다 일의 순서를 먼저 정하세요.",
        day="가까운 사람과 나누는 말은 평소보다 한 번 더 고르세요.",
        hour="세워 둔 계획은 고집하기보다 고쳐 쓸 여지를 두세요."),
    "six": dict(
        year="윗사람·집안과 이어진 인연을 가볍게 넘기지 마세요.",
        month="일터에서 함께할 사람을 고르는 눈을 믿으세요.",
        day="가까운 관계에 마음을 쓰는 만큼 생활이 단단해집니다.",
        hour="미뤄 둔 계획을 다른 사람과 함께 다시 꺼내 보세요."),
    "half": dict(
        year="윗사람에게서 받은 것을 내 방식으로 다시 써 보세요.",
        month="일터에서 맡은 일의 방향을 한쪽으로 모아 보세요.",
        day="생활 가까이에서 시작한 일이 힘을 얻는 해입니다.",
        hour="멀리 둔 계획 하나를 골라 구체적으로 적어 보세요."),
    "punish": dict(
        year="윗사람과 얽힌 일은 서로의 기준부터 확인하세요.",
        month="일터의 규칙과 약속을 평소보다 꼼꼼히 챙기세요.",
        day="가까운 사이일수록 서운함을 쌓아 두지 마세요.",
        hour="계획을 몰아서 처리하지 말고 나눠서 진행하세요."),
    "self": dict(
        year="익숙한 방식을 되풀이하며 스스로를 몰아붙이지 마세요.",
        month="같은 일을 되풀이하다 지치지 않게 속도를 조절하세요.",
        day="같은 기운이 겹치니 쉬는 시간을 일정에 넣어 두세요.",
        hour="욕심을 겹쳐 세우지 말고 계획을 하나씩 끝내세요."),
}
TRIPLE_ATTITUDE = {
    "木": "새로 시작하고 키워 가는 일에 힘을 모으세요.",
    "火": "드러내고 표현하는 일에 힘을 모으세요.",
    "土": "벌여 둔 일을 묶고 다지는 데 힘을 모으세요.",
    "金": "기준을 세우고 정리하는 일에 힘을 모으세요.",
    "水": "배우고 살피며 흐름을 읽는 데 힘을 모으세요.",
}
STEM_CLASH_ATTITUDE = "나를 흔드는 요구에는 기준부터 세우고 답하세요."
STEM_COMBINE_ATTITUDE = "끌리는 제안일수록 원래 목표와 맞는지 따져 보세요."
TRIPLE_PUNISH_ATTITUDE = "무리한 약속을 피하고 규칙을 평소보다 엄격히 지키세요."
NO_TOUCH = ("올해 글자는 원국과 부딪히거나 묶이는 자리가 없습니다.",
            "큰 흔들림 없이 타고난 결이 그대로 드러나는 해입니다.")


def _triple_element(a: str, b: str) -> str | None:
    for chars, element in TRIPLES.items():
        if a in chars and b in chars:
            return element
    return None


def natal_touch(year_stem: str, year_branch: str, natal: dict[str, str], day_stem: str) -> list[dict]:
    """올해 간지가 원국에 닿는 관계. 무게 순 최대 2개, 자리마다 하나."""
    found: list[dict] = []
    if frozenset((year_stem, day_stem)) in STEM_CLASH:
        found.append(dict(kind="stem_clash", pos=None))
    elif frozenset((year_stem, day_stem)) in STEM_COMBINE:
        found.append(dict(kind="stem_combine", pos=None))
    if _completes_punish([year_branch], natal):
        found.append(dict(kind="triple_punish", pos=None))
    triples = _completes_triple([year_branch], natal)
    if triples:
        found.append(dict(kind="triple", pos=None, element=triples[0]))
    for pos in ("day", "month", "year", "hour"):          # 같은 무게면 일지 → 월지 → 년지 → 시지
        b = natal.get(pos)
        if not b:
            continue
        pair = frozenset((year_branch, b))
        if b == year_branch:
            if b in SELF_PUNISH:
                found.append(dict(kind="self", pos=pos, branch=b))
            continue
        if pair in BRANCH_CLASH:
            found.append(dict(kind="clash", pos=pos, branch=b))
        elif pair in PAIR_PUNISH:
            found.append(dict(kind="punish", pos=pos, branch=b))
        elif pair in BRANCH_SIX:
            found.append(dict(kind="six", pos=pos, branch=b))
        else:
            el = _triple_element(year_branch, b)
            if el and (year_branch in WANG or b in WANG) and el not in triples:   # 삼합이 완성되면 반합은 그 안에 든다
                found.append(dict(kind="half", pos=pos, branch=b, element=el))
    for f in found:
        f["weight"] = WEIGHT[f["kind"]] + (0.5 if f.get("pos") == "day" else 0) + (0.3 if f.get("pos") == "month" else 0)
    found.sort(key=lambda f: -f["weight"])
    return found[:2]


def touch_sentences(t: dict, year_stem: str, year_branch: str, day_stem: str) -> list[str]:
    k, pos = t["kind"], t.get("pos")
    if k == "stem_clash":
        return [f"일간 {_j(day_stem, '과와')} 올해 천간 {_j(year_stem, '이가')} 부딪히는 천간충입니다.", STEM_CLASH_ATTITUDE]
    if k == "stem_combine":
        return [f"일간 {_j(day_stem, '과와')} 올해 천간 {_j(year_stem, '이가')} 합으로 묶입니다.", STEM_COMBINE_ATTITUDE]
    if k == "triple_punish":
        return [f"올해 {_j(year_branch, '이가')} 들어와 원국에 삼형(三刑)이 완성됩니다.", TRIPLE_PUNISH_ATTITUDE]
    if k == "triple":
        el = EL_LABEL[t["element"]]
        return [f"올해 {_j(year_branch, '이가')} 원국과 삼합을 이뤄 {el} 기운이 모입니다.", TRIPLE_ATTITUDE[t["element"]]]
    where = f"{POS_NAME[pos]} {_j(t['branch'], '과와')} 올해 {_j(year_branch, '이가')}"
    first = {
        "clash": f"{where} 정면으로 부딪히는 충(沖)입니다.",
        "six": f"{where} 육합(六合)으로 묶입니다.",
        "half": f"{where} 반합해 {EL_LABEL.get(t.get('element'), '')} 쪽으로 기웁니다.",
        "punish": f"{where} 형(刑)을 이룹니다.",
        "self": f"{POS_NAME[pos]} {_j(t['branch'], '과와')} 같은 글자가 겹쳐 자형(自刑)을 이룹니다.",
    }[k]
    return [first, ATTITUDE[k][pos]]


# ---------------------------------------------------------------------------
# B. 보완 기운
# ---------------------------------------------------------------------------
REASON = {
    "strong": "넘치는 힘을 덜어 주는 기운이 한 해 내내 흐릅니다.",
    "weak": "모자란 힘을 보태 주는 기운이 한 해 내내 흐릅니다.",
    "johu": "태어난 계절의 치우침을 바로잡는 기운이 들어옵니다.",
}


def balance_sentences(year_stem: str, year_branch: str, balance: dict, strength: str) -> tuple[str, list[str]]:
    ganji = year_stem + year_branch
    year_els = list(dict.fromkeys((GAN_WUXING[year_stem], ZHI_WUXING[year_branch])))
    ranking = balance["ranking"]
    side = "strong" if strength in {"strong", "extremely_strong"} else "weak" if strength in {"weak", "extremely_weak"} else "johu"
    for rank, label in ((0, "보완 기운"), (1, "두 번째 보완 기운")):
        if ranking[rank] in year_els:
            el = EL_LABEL[ranking[rank]]
            return ("support", [f"올해 {ganji}에는 {label} {_j(el, '이가')} 들어 있습니다.", REASON[side]])
    overflow = [e for e in year_els if e in (balance.get("overflow") or [])]
    if overflow:
        el = EL_LABEL[overflow[0]]
        return ("overflow", [f"올해 {ganji}의 {_j(el, '은는')} 원국에 이미 넉넉한 기운입니다.",
                             "같은 기운이 더해지니 하던 방식을 덜어내 보세요."])
    avoid = [e for e in year_els if e in (balance.get("eokbu_avoid") or [])]
    if avoid and side == "strong":
        el = EL_LABEL[avoid[0]]
        return ("avoid", [f"올해 {ganji}의 {_j(el, '은는')} 강한 일간을 더 키우는 기운입니다.",
                          "힘이 넘칠수록 혼자 끌고 가지 말고 나누세요."])
    if avoid and side == "weak":
        el = EL_LABEL[avoid[0]]
        return ("avoid", [f"올해 {ganji}의 {_j(el, '은는')} 약한 일간의 힘을 빼는 기운입니다.",
                          "일을 늘리기보다 체력과 기반을 먼저 챙기세요."])
    el = EL_LABEL[ranking[0]]
    return ("neutral", [f"올해 {ganji}의 기운은 보완 기운 {_j(el, '과와')} 겹치지 않습니다.",
                        "보완 기운은 생활 속 색과 습관으로 채워 가세요."])


# ---------------------------------------------------------------------------
# C. 대운 속의 올해
# ---------------------------------------------------------------------------
GROUP_ORDER = ("비겁", "식상", "재성", "관성", "인성")       # 앞이 뒤를 생한다
GROUP_DESC = {
    "비겁": "내 힘을 키우는", "식상": "드러내고 만드는", "재성": "벌고 꾸리는",
    "관성": "책임을 지는", "인성": "배우고 채우는",
}
ORDINAL = ("첫", "두", "세", "네", "다섯", "여섯", "일곱", "여덟", "아홉", "열")
LINK = {
    "same": ("올해도 같은 결이 겹쳐 대운의 색이 더 짙어집니다.",
             "한쪽으로 쏠리지 않게 다른 생활도 함께 챙기세요."),
    "year_feeds": ("올해의 {Y}{Yj} 대운의 {C}{Cj2} 키워 줍니다.",
                   "올해 들인 노력이 대운의 큰 흐름에 보탬이 됩니다."),
    "cycle_feeds": ("대운의 {C}{Cj} 올해의 {Y}{Yj2} 받쳐 줍니다.",
                    "큰 흐름이 받쳐 주니 올해 일에 힘을 아끼지 마세요."),
    "year_controls": ("올해의 {Y}{Yj} 대운의 {C}{Cj2} 다스립니다.",
                      "대운이 주는 무게를 올해의 힘으로 풀어내세요."),
    "cycle_controls": ("대운의 {C}{Cj} 올해의 {Y}{Yj2} 누릅니다.",
                       "올해 하고 싶은 일은 대운의 과제와 맞춰 고르세요."),
}
ROLE = {
    "peer": "비견", "rob_wealth": "겁재", "eating_god": "식신", "hurting_officer": "상관",
    "direct_wealth": "정재", "indirect_wealth": "편재", "direct_officer": "정관",
    "seven_killings": "편관", "direct_resource": "정인", "indirect_resource": "편인",
}


def _link(year_group: str, cycle_group: str) -> str:
    y, c = GROUP_ORDER.index(year_group), GROUP_ORDER.index(cycle_group)
    if y == c:
        return "same"
    if (y + 1) % 5 == c:
        return "year_feeds"
    if (c + 1) % 5 == y:
        return "cycle_feeds"
    if (y + 2) % 5 == c:
        return "year_controls"
    return "cycle_controls"


def cycle_sentences(cycle: dict | None, year: int, year_god: str | None,
                    year_stem: str, year_branch: str) -> tuple[str | None, list[str]]:
    if not cycle or not (cycle.get("pillar") or {}).get("ganji"):
        return None, []
    pillar = cycle["pillar"]
    cgod, cgroup = cycle.get("ten_god"), GOD_GROUP.get(cycle.get("ten_god") or "")
    ygroup = GOD_GROUP.get(year_god or "")
    if not cgroup:
        return None, []
    ganji = pillar["ganji"]
    out = [f"대운 {ganji}{_jp(ganji[-1], '은는')} {GROUP_DESC[cgroup]} {ROLE.get(cgod, cgroup)}의 10년입니다."]
    start, end = cycle.get("start_year"), cycle.get("end_year")
    if isinstance(start, int) and 0 <= year - start < 10:
        out.append(f"올해는 그 {ORDINAL[year - start]} 번째 해입니다." if year != start else
                   "올해는 대운이 바뀌는 첫해라 생활의 틀을 새로 잡는 해입니다.")
        if isinstance(end, int) and year == end and year != start:
            out.append("대운의 마지막 해라 10년의 일을 매듭짓는 해입니다.")
    if not ygroup:
        return None, out
    kind = _link(ygroup, cgroup)
    if kind == "year_controls" and year_god == "eating_god" and cgod == "seven_killings":
        out.append("올해 식신이 대운의 편관을 다스리는 식신제살(食神制殺)입니다.")
    else:
        first, _ = LINK[kind]
        out.append(first.format(Y=ygroup, C=cgroup, Yj=_jp(ygroup, "이가"), Cj=_jp(cgroup, "이가"),
                                Yj2=_jp(ygroup, "을를"), Cj2=_jp(cgroup, "을를")))
    out.append(LINK[kind][1])
    cs, cb = pillar.get("stem"), pillar.get("branch")
    if (cs and frozenset((cs, year_stem)) in STEM_CLASH) or (cb and frozenset((cb, year_branch)) in BRANCH_CLASH):
        out.append("대운과 올해 글자가 부딪혀 흐름이 출렁이는 해입니다.")
    return kind, out


def _jp(word: str, pair: str) -> str:
    return _j(word, pair)[len(word):]


# ---------------------------------------------------------------------------
# 조립
# ---------------------------------------------------------------------------
def compose_touch(*, year: int, year_stem: str, year_branch: str, natal: dict[str, str], day_stem: str,
                  balance: dict, strength: str, cycle: dict | None, year_god: str | None) -> dict:
    touches = natal_touch(year_stem, year_branch, natal, day_stem)
    natal_paras = [touch_sentences(t, year_stem, year_branch, day_stem) for t in touches] or [list(NO_TOUCH)]
    b_kind, b_sent = balance_sentences(year_stem, year_branch, balance, strength)
    c_kind, c_sent = cycle_sentences(cycle, year, year_god, year_stem, year_branch)
    sections = [
        dict(key="natal", title="올해가 내 사주에 닿는 자리", paragraphs=natal_paras,
             kinds=[t["kind"] + (":" + t["pos"] if t.get("pos") else "") for t in touches]),
        dict(key="balance", title="올해와 보완 기운", paragraphs=[b_sent], kinds=[b_kind]),
    ]
    if c_sent:
        sections.append(dict(key="cycle", title="대운 속의 올해", paragraphs=[c_sent], kinds=[c_kind or "none"]))
    return dict(version=TOUCH_VERSION, ganji=year_stem + year_branch, sections=sections)


def touch_sentence_list(touch: dict | None) -> list[str]:
    if not touch:
        return []
    return [s for sec in touch["sections"] for para in sec["paragraphs"] for s in para]
