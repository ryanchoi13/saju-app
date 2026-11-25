"""사업 타이밍 — 5년 흐름 · 사건별 판정 · 사업 택일 (2026-11-25 정오님 요청 3번).

무엇을 하나
- five_year_flow: 앞으로 5년, 해마다 세운(그해 간지)을 원국에 대어
  '문 열기 · 판 키우기 · 동업 · 지키기' 네 사건을 좋음/보통/주의로 판정한다.
  같은 해의 '일'·'금전' 등급은 오늘의 운세와 같은 분야 규칙표(daily_domain_rules)를 세운 간지에 적용한 값이다
  (직업운 12달 등급이 월주에 같은 규칙표를 쓰는 것과 같은 방식).
- pick_days: 한 달 안에서 개업·공개·계약에 맞는 날을 고른다(사업 택일).

판정은 이름 붙은 규칙으로만 한다(숫자 가중치 금지, 11/10 원칙). 각 판정에는 걸린 규칙 이름이 붙는다.
사주는 사람의 흐름을 보는 것이라 시장·경쟁·수익 규모는 판정하지 않는다.
"""
from __future__ import annotations

import calendar as _cal
from datetime import date

from app.engine.constants import GAN_KO, GAN_WUXING, ZHI_KO
from app.engine.core.models import MyeongriCoreResult
from app.engine.services import career_copy as copy
from app.engine.services import daily_score
from app.engine.services.daily_score import _god_group, calendar_ganji
from app.engine.services.element_balance import element_tiers
from app.engine.services.theme_core import CLASH, YEOKMA, PUNISH, tally

EVENTS = ("open", "expand", "partner", "keep")
EVENT_NAME = {"open": "문 열기", "expand": "판 키우기", "partner": "동업", "keep": "지키기"}
GRADE_NAME = {"good": "좋음", "normal": "보통", "caution": "주의"}
_DOMAIN_GRADE = {"좋음": "good", "보통": "normal", "주의": "caution"}

PEER_GODS = ("peer", "rob_wealth")

# 규칙 이름 → 사용자에게 보일 이유 한 문장
RULE_TEXT = {
    "output_year": "재주를 내놓는 기운(식상)이 드는 해라, 만든 것을 세상에 내보이기 좋아요.",
    "wealth_year": "재물의 기운(재성)이 드는 해라, 거래와 매출이 움직여요.",
    "wealth_year_strong": "재물의 기운(재성)이 드는데 감당할 힘도 있어서 판을 넓혀도 버텨요.",
    "wealth_year_weak": "재물의 기운(재성)이 들지만 감당할 힘이 모자라, 판을 넓히면 버거워요.",
    "officer_year": "규칙과 책임의 기운(관성)이 드는 해라, 새던 돈을 막고 틀을 다지기 좋아요.",
    "resource_year": "문서와 배움의 기운(인성)이 드는 해라, 계약·자격·정리에 힘이 실려요.",
    "peer_year": "나와 같은 기운(비겁)이 드는 해라, 경쟁자가 늘고 돈을 나눠 갖게 돼요.",
    "natal_peers": "원국에 나와 같은 기운(비겁)이 많아, 동업에서 돈 나누는 문제로 부딪히기 쉬운 사주예요.",
    "month_clash": "일과 생활의 자리(월지)와 부딪히는 해라, 하던 방식이 흔들려요.",
    "day_clash": "나 자신의 자리(일지)와 부딪히는 해라, 몸과 가까운 관계가 바빠져요.",
    "punish": "원국과 형(刑)이 걸리는 해라, 서류와 약속에서 마찰이 생겨요.",
    "avoid_element": "그해 기운이 내게 덜 맞는 오행이라 힘이 빠져요.",
    "good_element": "그해 기운이 내게 필요한 오행이라 큰 흐름이 내 편이에요.",
    "yeokma": "역마가 드는 해라, 이동·새 제안·자리 변화가 잦아요.",
}


def today_of(core: MyeongriCoreResult) -> date:
    """풀이를 보는 날(엔진에 넘긴 target_date). 없으면 오늘."""
    raw = (core.timing.daily or {}).get("date") if core.timing else None
    return date.fromisoformat(raw) if raw else date.today()


def _cycles(core: MyeongriCoreResult) -> list[dict]:
    lc = core.timing.model_dump(mode="json").get("luck_cycle") or {}
    return lc.get("cycles") or []


def cycle_for_year(core: MyeongriCoreResult, year: int) -> dict | None:
    for c in _cycles(core):
        if c["start_year"] <= year <= c["end_year"]:
            return c
    return None


def natal_peer_count(core: MyeongriCoreResult) -> int:
    t = tally(core, PEER_GODS)
    return sum(t.values())


def _strength(core: MyeongriCoreResult) -> str:
    s = str(core.synthesis.strength_state or "")
    return copy.strength_key(s) if copy.strength_decided(s) else "unknown"


def judge_pillar(core: MyeongriCoreResult, ganji: str) -> dict:
    """한 간지(세운·월운·일진 무엇이든)를 원국에 대어 네 사건을 판정한다."""
    p = core.natal_facts.pillars
    dm = p["day"].stem
    tiers = element_tiers(core)["tiers"]
    stem, branch = ganji[0], ganji[1]
    group = _god_group(dm, GAN_WUXING[stem])
    tier = tiers[GAN_WUXING[stem]]
    strength = _strength(core)
    peers = natal_peer_count(core)

    marks = []
    if CLASH.get(p["month"].branch) == branch:
        marks.append("month_clash")
    if CLASH.get(p["day"].branch) == branch:
        marks.append("day_clash")
    if any(branch in PUNISH.get(p[pos].branch, set()) for pos in ("year", "month", "day")):
        marks.append("punish")
    if branch in {YEOKMA[p["year"].branch], YEOKMA[p["day"].branch]}:
        marks.append("yeokma")
    element_rule = "good_element" if tier == "good" else "avoid_element" if tier == "avoid" else None

    out: dict[str, dict] = {}

    # 문 열기(창업·공개·출시)
    good, bad = [], []
    if group == "output":
        good.append("output_year")
    elif group == "wealth" and strength != "weak":
        good.append("wealth_year")
    if group == "peer":
        bad.append("peer_year")
    if "month_clash" in marks:
        bad.append("month_clash")
    if tier == "avoid":
        bad.append("avoid_element")
    out["open"] = _grade(good, bad, element_rule)

    # 판 키우기(투자·확장·큰 지출)
    good, bad = [], []
    if group == "wealth":
        (good if strength == "strong" else bad if strength == "weak" else good).append(
            "wealth_year_strong" if strength == "strong" else "wealth_year_weak" if strength == "weak" else "wealth_year")
    if group == "peer":
        bad.append("peer_year")
    if "month_clash" in marks:
        bad.append("month_clash")
    if tier == "avoid":
        bad.append("avoid_element")
    out["expand"] = _grade(good, bad, element_rule)

    # 동업(공동 투자·지분 나누기)
    good, bad = [], []
    if group == "peer":
        bad.append("peer_year")
    if peers >= 2:
        bad.append("natal_peers")
    if group in ("officer", "resource") and peers < 2:
        good.append("officer_year" if group == "officer" else "resource_year")
    if "punish" in marks:
        bad.append("punish")
    out["partner"] = _grade(good, bad, None)

    # 지키기(정리·내실·문서)
    good, bad = [], []
    if group == "officer":
        good.append("officer_year")
    elif group == "resource":
        good.append("resource_year")
    if group == "peer":
        bad.append("peer_year")
    out["keep"] = _grade(good, bad, None)

    return dict(ganji=ganji, group=group, element_tier=tier, marks=marks, events=out)


def _grade(good: list[str], bad: list[str], element_rule: str | None) -> dict:
    """좋은 규칙만 있으면 좋음, 나쁜 규칙이 있으면 주의(좋은 규칙과 겹치면 보통), 둘 다 없으면 보통."""
    if good and not bad:
        g = "good"
    elif bad and not good:
        g = "caution"
    else:
        g = "normal"
    rules = good + bad
    if element_rule and element_rule not in rules and g != "normal":
        rules.append(element_rule)
    return dict(grade=g, rules=rules, reasons=[RULE_TEXT[r] for r in rules])


def five_year_flow(core: MyeongriCoreResult, start_year: int, years: int = 5) -> list[dict]:
    """앞으로 N년. 세운 간지는 그해 6월 15일 기준(입춘 이후 한가운데)으로 잡는다."""
    rows = []
    for y in range(start_year, start_year + years):
        target = date(y, 6, 15)
        year_gz = calendar_ganji(target)[0]
        judged = judge_pillar(core, year_gz)
        r = daily_score.evaluate(core, year_gz, target)
        domains = r["domain_rules"]
        cyc = cycle_for_year(core, y)
        rows.append(dict(
            year=y, ganji=year_gz, ganji_ko=GAN_KO.get(year_gz[0], "") + ZHI_KO.get(year_gz[1], ""),
            group=judged["group"], element_tier=judged["element_tier"], marks=judged["marks"],
            work=_DOMAIN_GRADE.get(domains["일"]["tier"], "normal"),
            money=_DOMAIN_GRADE.get(domains["금전"]["tier"], "normal"),
            cycle=(cyc or {}).get("pillar", {}).get("ganji"), cycle_god=(cyc or {}).get("ten_god"),
            events=judged["events"],
        ))
    return rows


def pick_days(core: MyeongriCoreResult, year: int, month: int, purpose: str = "open", n: int = 5) -> list[dict]:
    """사업 택일. purpose: open(개업·공개) · contract(계약·서명).

    빼는 날: 일지·월지와 충하는 날, 그날 천간이 피할 오행인 날, 비겁 날(open), 그날 '일' 등급이 주의인 날.
    고르는 순서: 맞는 십성의 날 → 그날 '일'·'금전' 등급 → 오늘의 운세 점수.
    """
    p = core.natal_facts.pillars
    dm = p["day"].stem
    tiers = element_tiers(core)["tiers"]
    want = ("output", "wealth") if purpose == "open" else ("resource", "officer", "wealth")
    picked = []
    for d in range(1, _cal.monthrange(year, month)[1] + 1):
        target = date(year, month, d)
        day_gz = calendar_ganji(target)[2]
        stem, branch = day_gz[0], day_gz[1]
        if branch in (CLASH.get(p["day"].branch), CLASH.get(p["month"].branch)):
            continue
        if tiers[GAN_WUXING[stem]] == "avoid":
            continue
        group = _god_group(dm, GAN_WUXING[stem])
        if group == "peer" and purpose == "open":
            continue
        r = daily_score.evaluate(core, day_gz, target)
        work = r["domain_rules"]["일"]["tier"]
        money = r["domain_rules"]["금전"]["tier"]
        if work == "주의":
            continue
        reasons = []
        if group in want:
            reasons.append({"output": "만든 것을 내보이는 기운(식상)의 날", "wealth": "거래가 움직이는 기운(재성)의 날",
                            "officer": "약속과 신뢰의 기운(관성)의 날", "resource": "문서의 기운(인성)의 날"}[group])
        if tiers[GAN_WUXING[stem]] == "good":
            reasons.append("내게 필요한 오행의 날")
        if work == "좋음":
            reasons.append("일 흐름이 좋은 날")
        if money == "좋음":
            reasons.append("금전 흐름이 좋은 날")
        rank = (group in want, work == "좋음", money == "좋음", tiers[GAN_WUXING[stem]] == "good", r["score"])
        picked.append(dict(date=target.isoformat(), ganji=day_gz, score=r["score"], reasons=reasons, _rank=rank))
    picked.sort(key=lambda x: x["_rank"], reverse=True)
    out = picked[:n]
    for x in out:
        x.pop("_rank")
    return sorted(out, key=lambda x: x["date"])
