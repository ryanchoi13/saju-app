"""테마운 공용 판정 엔진 (2026-11-14).

직업·애정·건강·재물·학업 풀이가 같은 기준으로 원국을 읽도록 한곳에 모은다.
여기 규칙을 고치면 다섯 테마가 함께 바뀐다.

- 십성 세기: 원국 여덟 글자(천간 3 + 지지 본기 4, 일간 제외). 지장간 중기·여기는 세지 않는다.
  (11/13 애정운 깊이 규칙에서 정한 기준. 지장간에만 있는 별은 각 테마가 '숨어 있음'으로 따로 읽는다.)
- 지지 관계표: 육합·충·삼합·형·도화.
- 세운 간지: 그해 6월 15일 기준(입춘 앞뒤 혼동 없음).
- 겁재 강함: 여덟 글자에 겁재 2자리 이상, 또는 월지 본기가 겁재.
"""
from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Iterable

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
YEOKMA = {**dict.fromkeys("寅午戌", "申"), **dict.fromkeys("申子辰", "寅"),
          **dict.fromkeys("巳酉丑", "亥"), **dict.fromkeys("亥卯未", "巳")}


def god(dm: str, stem: str) -> str:
    g = get_ten_god(dm, stem)
    return getattr(g, "value", str(g))


def main_qi(branch: str) -> str:
    """지지 본기(지장간 첫 글자)."""
    return get_hidden_stems(branch).stems[0].stem


def ko(gz: str) -> str:
    return GAN_KO.get(gz[0], "") + ZHI_KO.get(gz[1], "")


def punishes(a: str, b: str) -> bool:
    return b in PUNISH.get(a, set()) or a in PUNISH.get(b, set())


def year_gz(y: int) -> str:
    return calendar_ganji(date(y, 6, 15))[0]


def natal_counts(core) -> dict[str, list[str]]:
    """원국 여덟 글자(천간 3 + 지지 본기 4, 일간 제외) 십성 → 놓인 자리 목록."""
    p = core.natal_facts.pillars
    dm = p["day"].stem
    out: dict[str, list[str]] = {}
    for pos in ("year", "month", "day", "hour"):
        pil = p.get(pos)
        if pil is None:
            continue
        if pos != "day":
            out.setdefault(god(dm, pil.stem), []).append(f"{pos}_stem")
        out.setdefault(god(dm, main_qi(pil.branch)), []).append(f"{pos}_branch")
    return out


def tally(core, gods: Iterable[str] | None = None) -> Counter:
    """여덟 글자 십성 개수. gods 를 주면 그 십성만 센다(테마마다 보는 별만 고를 때)."""
    keep = set(gods) if gods else None
    return Counter({g: len(v) for g, v in natal_counts(core).items() if keep is None or g in keep})


def hidden_tally(core, gods: Iterable[str] | None = None) -> Counter:
    """지장간 중기·여기(본기 제외) 십성 개수 — 여덟 글자가 같을 때만 쓰는 보조 근거."""
    keep = set(gods) if gods else None
    p = core.natal_facts.pillars
    dm = p["day"].stem
    out: Counter = Counter()
    for pos in ("year", "month", "day", "hour"):
        pil = p.get(pos)
        if pil is None:
            continue
        for item in get_hidden_stems(pil.branch).stems[1:]:
            g = god(dm, item.stem)
            if keep is None or g in keep:
                out[g] += 1
    return out


def rob_heavy(counts: dict[str, list[str]]) -> bool:
    """겁재 강한 원국(군겁쟁재 경계): 여덟 글자에 겁재 2자리 이상, 또는 월지 본기가 겁재."""
    rob = counts.get("rob_wealth", [])
    return len(rob) >= 2 or "month_branch" in rob
