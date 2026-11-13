"""애정운 깊이 읽기 (2026-11-13 정오님: "수박 겉핥기, 유료면 오늘의 운세보다 깊어야 한다").

정오님 결정(11/13): ① 애정운에서는 성별로 인연의 별을 정한다(남 = 재성, 여 = 관성) — 명리의 기본 해석.
                   ② 흔들린 해는 '관계가 흔들리거나 시험받은 해'까지만 쓰고 이별·이혼은 단정하지 않는다.

네 칸의 계산(모두 통용 해석을 규칙으로 옮긴 것 — 근거 문서: 프로젝트 claude/love-depth-rules-2026-11-13.md)
 1 지나온 사랑   : 18세부터 지난해까지 세운마다 '인연 점수'(천간 = 인연의 별 +2, 지지 = 일지 육합 +2 / 일지 삼합·반합 +1 / 도화 +1)
                   3점 이상이면 인연의 해, 지지가 일지를 충·형하면 흔들린 해. 인연의 해를 2년 안 간격으로 묶어 시기로 만들고,
                   시기 끝 2년 안에 흔들린 해가 있으면 함께 쓴다. 대운 천간·지지 본기에 인연의 별이 든 10년도 짚는다.
 2 배우자 자리   : 일지 본기의 십성 + 일지가 원국 다른 지지와 충·형·합인지 + 연주 기준 공망인지 + 그 자리가 인연의 별인지.
 3 되풀이되는 약점: 원국 여덟 글자(천간 + 지지 본기) 십성 개수로 고른 규칙 최대 3개(아래 _WEAK 순서) + 지나온 사랑의 '만남 뒤 바로 흔들림' 반복.
 4 동반자 시기   : 늦은 인연 신호(일지 충·공망, 인연의 별 혼잡·없음·시주에만, 남 비겁 강 / 여 상관 강) vs 이른 인연 신호
                   (인연의 별이 연주·월주에 깨끗이, 일지와 월지의 합) + 앞으로 10년 중 인연 점수가 가장 높은 해 2개.
나이는 대운 표기와 같은 세는 나이다.
"""
from __future__ import annotations

from datetime import date

from app.engine.constants import GAN_KO, ZHI_KO
from app.engine.facts.hidden_stems import get_hidden_stems
from app.engine.facts.ten_gods import get_ten_god
from app.engine.services.daily_score import calendar_ganji

STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"
SIX = {"子": "丑", "丑": "子", "寅": "亥", "亥": "寅", "卯": "戌", "戌": "卯",
       "辰": "酉", "酉": "辰", "巳": "申", "申": "巳", "午": "未", "未": "午"}
CLASH = {"子": "午", "午": "子", "丑": "未", "未": "丑", "寅": "申", "申": "寅",
         "卯": "酉", "酉": "卯", "辰": "戌", "戌": "辰", "巳": "亥", "亥": "巳"}
TRIAD = [set("申子辰"), set("寅午戌"), set("巳酉丑"), set("亥卯未")]
PEACH = {**dict.fromkeys("寅午戌", "卯"), **dict.fromkeys("申子辰", "酉"),
         **dict.fromkeys("巳酉丑", "午"), **dict.fromkeys("亥卯未", "子")}
# 형: 인사신·축술미 삼형, 자묘 상형, 진오유해 자형
PUNISH = {"寅": {"巳"}, "巳": {"申"}, "申": {"寅"}, "丑": {"戌"}, "戌": {"未"}, "未": {"丑"},
          "子": {"卯"}, "卯": {"子"}, "辰": {"辰"}, "午": {"午"}, "酉": {"酉"}, "亥": {"亥"}}


def _god(dm: str, stem: str) -> str:
    g = get_ten_god(dm, stem)
    return getattr(g, "value", str(g))


def _main(branch: str) -> str:
    return get_hidden_stems(branch).stems[0].stem


def _ko(gz: str) -> str:
    return GAN_KO.get(gz[0], "") + ZHI_KO.get(gz[1], "")


def _punishes(a: str, b: str) -> bool:
    return b in PUNISH.get(a, set()) or a in PUNISH.get(b, set())


def star_gods(gender: str) -> tuple[str, str]:
    """(정, 편) 인연의 별. 남 = 재성, 여 = 관성. 성별을 모르면 남 기준(엔진 기본값과 같음)."""
    return ("direct_officer", "seven_killings") if gender == "female" else ("direct_wealth", "indirect_wealth")


def natal_counts(core) -> dict:
    """원국 여덟 글자(천간 3 + 지지 본기 4, 일간 제외) 십성 개수와 자리."""
    p = core.natal_facts.pillars
    dm = p["day"].stem
    out: dict[str, list[str]] = {}
    for pos in ("year", "month", "day", "hour"):
        pil = p.get(pos)
        if pil is None:
            continue
        if pos != "day":
            out.setdefault(_god(dm, pil.stem), []).append(f"{pos}_stem")
        out.setdefault(_god(dm, _main(pil.branch)), []).append(f"{pos}_branch")
    return out


def year_signal(core, gz: str, gender: str) -> tuple[int, bool, list[str]]:
    """세운 하나의 (인연 점수, 흔들림 여부, 이유)."""
    p = core.natal_facts.pillars
    dm, db = p["day"].stem, p["day"].branch
    stars = star_gods(gender)
    score, why = 0, []
    if _god(dm, gz[0]) in stars:
        score += 2
        why.append("star")
    if SIX[db] == gz[1]:
        score += 2
        why.append("six")
    elif any(db in t and gz[1] in t and db != gz[1] for t in TRIAD):
        score += 1
        why.append("triad")
    peaches = {PEACH[p["year"].branch], PEACH[db]}
    if gz[1] in peaches:
        score += 1
        why.append("peach")
    shake = CLASH[db] == gz[1] or _punishes(db, gz[1])
    return score, shake, why


def _year_gz(y: int) -> str:
    return calendar_ganji(date(y, 6, 15))[0]


def past_love(core, gender: str, birth_year: int, this_year: int) -> dict:
    periods, cur = [], None
    shakes = {}
    for y in range(birth_year + 17, this_year):            # 세는 나이 18세부터 지난해까지
        gz = _year_gz(y)
        score, shake, why = year_signal(core, gz, gender)
        if shake:
            shakes[y] = gz
        if score >= 3:
            if cur and y - cur["end"] <= 2:
                cur["end"] = y
                cur["why"] |= set(why)
            else:
                cur = dict(start=y, end=y, why=set(why))
                periods.append(cur)
    for per in periods:
        per["shake"] = next((y for y in sorted(shakes) if per["end"] <= y <= per["end"] + 2 and y >= per["start"]), None)
    # 대운에 인연의 별이 든 10년(지나간 것과 지금)
    stars = star_gods(gender)
    dm = core.natal_facts.pillars["day"].stem
    cycles = []
    for c in (core.timing.luck_cycle or {}).get("cycles", []):
        if c.get("start_year", 9999) > this_year or c.get("end_age", 0) < 18:
            continue
        pil = c["pillar"]
        if _god(dm, pil["stem"]) in stars or _god(dm, _main(pil["branch"])) in stars:
            cycles.append((c["start_age"], c["end_age"]))
    # 인연 대운에 들어선 해: 이어진 인연 대운 묶음의 첫해만(28~47세면 28세 한 번)
    entries, prev_end = [], None
    for c in sorted((core.timing.luck_cycle or {}).get("cycles", []), key=lambda c: c.get("start_age", 0)):
        if (c.get("start_age", 0), c.get("end_age", 0)) in cycles:
            if prev_end is None or c["start_age"] != prev_end + 1:
                if c.get("start_year") and birth_year + 17 <= c["start_year"] < this_year:
                    entries.append(c["start_year"])
            prev_end = c["end_age"]
    # 시기 뒤에 붙지 않은 따로 선 충의 해(형은 작은 신호라 따로 세우지 않는다)
    used = {per["shake"] for per in periods if per.get("shake")}
    dm_branch = core.natal_facts.pillars["day"].branch
    moves = [y for y, gz in shakes.items() if y not in used and CLASH[dm_branch] == gz[1]]
    # 11/13 정오님 실제(2005 양다리 끝에 상대가 다른 남자에게, 2024 밀당 끝에 무산): 비겁(비견·겁재) 세운 = 인연을 두고
    # 경쟁자·자존심 싸움(군겁쟁재). 비겁 해만으로 세우면 아무 일 없던 해(2014·2015)도 잡혀서, 다른 사건이 있는 해에만 덧붙인다.
    event_years = {y for per in periods for y in range(per["start"], per["end"] + 1)}
    event_years |= {per["shake"] for per in periods if per.get("shake")} | set(entries) | set(moves)
    rivals = sorted(y for y in event_years if _god(dm, _year_gz(y)[0]) in ("peer", "rob_wealth"))
    for per in periods:
        per["kind"] = "heart" if "star" in per.pop("why") else "popular"
    return dict(periods=periods, shakes=shakes, star_cycles=cycles, entries=entries, moves=moves, rivals=rivals)


def palace(core, query: dict, gender: str) -> dict:
    p = core.natal_facts.pillars
    dm, db = p["day"].stem, p["day"].branch
    god = _god(dm, _main(db))
    others = [p[k].branch for k in ("year", "month", "hour") if p.get(k) is not None]
    clash = any(CLASH[db] == b for b in others)
    punish = any(_punishes(db, b) for b in others)
    combo = any(SIX[db] == b or any(db in t and b in t and b != db for t in TRIAD) for b in others)
    ys, yb = STEMS.index(p["year"].stem), BRANCHES.index(p["year"].branch)
    start = (yb - ys) % 12
    void = {BRANCHES[(start + 10) % 12], BRANCHES[(start + 11) % 12]}
    return dict(god=god, clash=clash, punish=punish and not clash, combo=combo, void=db in void,
                star=god in star_gods(gender))


def weak_points(core, gender: str, strength: str | None, counts: dict, past: dict) -> list[str]:
    n = {k: len(v) for k, v in counts.items()}
    s1, s2 = star_gods(gender)
    star_total = n.get(s1, 0) + n.get(s2, 0)
    picks = []
    repeats = sum(1 for per in past["periods"] if per.get("shake"))
    if repeats >= 2:
        picks.append("timing")
    if n.get("rob_wealth", 0) >= 2 or n.get("peer", 0) + n.get("rob_wealth", 0) >= 3:
        picks.append("rival")
    if n.get(s1, 0) and n.get(s2, 0) and star_total >= (3 if gender != "female" else 2):
        picks.append("mixed")
    if n.get("direct_resource", 0) + n.get("indirect_resource", 0) >= 3:
        picks.append("think")
    if n.get("hurting_officer", 0) >= 2:
        picks.append("words")
    if star_total >= 4 and strength in ("weak", "extremely_weak"):
        picks.append("heavy")
    if star_total == 0:
        picks.append("hidden" if _star_hidden(core, gender) else "none")
    return picks[:3]


def _star_hidden(core, gender: str) -> bool:
    """겉(천간·지지 본기)에는 없고 지장간 중기·여기에만 인연의 별이 있는가."""
    p = core.natal_facts.pillars
    dm = p["day"].stem
    stars = star_gods(gender)
    for pos in ("year", "month", "day", "hour"):
        if p.get(pos) is None:
            continue
        for h in get_hidden_stems(p[pos].branch).stems[1:]:
            if _god(dm, h.stem) in stars:
                return True
    return False


def partner_timing(core, gender: str, counts: dict, pal: dict, this_year: int) -> dict:
    n = {k: len(v) for k, v in counts.items()}
    s1, s2 = star_gods(gender)
    star_pos = counts.get(s1, []) + counts.get(s2, [])
    late, early = [], []
    if pal["clash"]:
        late.append("clash")
    if pal["void"]:
        late.append("void")
    if n.get(s1, 0) and n.get(s2, 0):
        late.append("mixed")
    if not star_pos:
        late.append("none")
    elif all(x.startswith("hour") for x in star_pos):
        late.append("hour_only")
    if gender == "female" and n.get("hurting_officer", 0) >= 2:
        late.append("words")
    if gender != "female" and n.get("peer", 0) + n.get("rob_wealth", 0) >= 3:
        late.append("rival")
    if star_pos and any(x.startswith(("year", "month")) for x in star_pos) and "mixed" not in late:
        early.append("front")
    p = core.natal_facts.pillars
    if SIX[p["day"].branch] == p["month"].branch:
        early.append("month_combo")
    verdict = "late" if len(late) >= 2 and len(late) > len(early) else ("early" if early and not late else "middle")
    future = []
    for y in range(this_year, this_year + 10):
        gz = _year_gz(y)
        score, shake, _ = year_signal(core, gz, gender)
        if score >= 2 and not shake:                       # 인연의 별만 드는 해(2점)도 앞으로의 해로는 짚는다
            future.append((score, y, gz))
    future.sort(key=lambda t: (-t[0], t[1]))
    best = sorted(future[:3], key=lambda t: t[1])
    return dict(verdict=verdict, late=late, early=early,
                years=[dict(year=y, ganji=gz, ko=_ko(gz)) for _, y, gz in best])
