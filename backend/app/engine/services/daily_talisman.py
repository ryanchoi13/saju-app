"""오늘의 부적 명세 (2026-11-17 정오님 결정).

부적은 그날의 뜻을 글로 풀지 않는다. 서버는 "어떤 부적을 그릴지"만 정하고(이 모듈), 화면(assets/talisman.js)이
같은 명세로 같은 그림을 그린다. 같은 날 같은 계정이면 같은 그림이다.

고르는 순서(하루에 하나):
  1. 튀는 분야가 있으면 분야(금전·사람·일) × 방향(좋음·주의) — 오늘의 운세가 제목 옆에 붙이는 분야와 같다.
     건강은 분야 판정 순서(사람 → 건강 → 금전 → 일)와 문턱 때문에 튀는 분야가 된 적이 없어(150명 × 45일 0건) 부적을 두지 않는다.
     혹시 나오면 신살 쪽으로 간다.
  2. 없으면 그날 일지 기준 12신살 × 그날 등급(좋음·보통·주의).
오행 한자(작은 글자)는 항상 행운 색 1칸과 같은 오행(luck_element)이다.

가운데 합자 부품 이름은 assets/talisman.js 의 PARTS 와 같아야 한다(tests/test_daily_talisman.py 가 맞춰 본다).
부품 이름은 화면 그림의 이름일 뿐 한자 뜻을 맞춘 것이 아니다. 그날의 뜻은 카드가 말하고 부적은 말하지 않는다.
"""
from __future__ import annotations

import hashlib
from datetime import date

from app.engine.services import daily_shinsal

SPEC_VERSION = 1

GOOD_GRADES = frozenset({"좋음", "아주 좋음"})
BAD_GRADES = frozenset({"주의", "나쁨"})

_ELEMENT = {"木": "wood", "火": "fire", "土": "earth", "金": "metal", "水": "water"}

# 분야 → 화면 분야 이름. 건강은 일부러 뺐다(위 설명).
_DOMAIN = {"금전": "money", "사람": "people", "애정·관계": "people", "일": "work"}

# (분야, 방향) → 가운데 합자 부품 3개(위에서 아래로)
DOMAIN_PARTS: dict[tuple[str, str], tuple[str, str, str]] = {
    ("money", "good"): ("yu", "bei", "tian"),
    ("money", "caution"): ("tian", "kou", "bei"),
    ("people", "good"): ("ren2", "yue", "ja"),
    ("people", "caution"): ("ren", "kou", "tian"),
    ("work", "good"): ("gok", "ladder", "ri"),
    ("work", "caution"): ("ladder", "kou", "to"),
}

# 12신살(일지 기준) → 가운데 합자 부품 3개. 방향(좋음·보통·주의)이 달라도 합자는 같고 모양(틀)이 달라진다.
SHINSAL_PARTS: dict[str, tuple[str, str, str]] = {
    "지살": ("to", "mu", "ri"),
    "년살": ("ri", "ren2", "hwa"),
    "월살": ("yue", "kou", "to"),
    "망신": ("ri", "yu", "an"),
    "장성": ("gok", "ren", "ja"),
    "반안": ("an", "tian", "kou"),
    "역마": ("wave", "ren", "cross"),
    "육해": ("dots", "ladder", "chuan"),
    "화개": ("kou", "spiral", "yue"),
    "겁살": ("cross", "su", "hwa"),
    "재살": ("bei", "kou", "ladder"),
    "천살": ("yu", "ren", "an"),
}

# 신살이 부적 위성 글자를 고를 때 쓰는 분야(그림 질감용)
_SHINSAL_DOMAIN = {"지살": "work", "월살": "work", "장성": "work", "천살": "work",
                   "년살": "people", "재살": "people", "겁살": "money"}


# 크게 보기 창에 붙는 이름·한 줄 설명. 그림에는 글자가 없고, 뜻은 여기서만 말한다.
# 사건을 말하지 않고 그날의 태도만 말한다(문체 헌법). 신살 이름은 화면에 쓰지 않는다.
DOMAIN_TEXT: dict[tuple[str, str], tuple[str, str]] = {
    ("money", "good"): ("곳간부", "금전 흐름이 가벼운 날의 뜻을 담았어요. 쓸 곳과 모을 곳을 먼저 나눠 보세요."),
    ("money", "caution"): ("살핌부", "씀씀이를 한 번 더 살피는 날의 뜻을 담았어요. 결제 전에 금액을 다시 확인하세요."),
    ("people", "good"): ("어울림부", "사람 사이가 가벼운 날의 뜻을 담았어요. 먼저 안부 한 줄 건네 보세요."),
    ("people", "caution"): ("말아낌부", "말이 앞서기 쉬운 날의 뜻을 담았어요. 답하기 전에 한 박자 쉬어 보세요."),
    ("work", "good"): ("첫손부", "일이 손에 붙는 날의 뜻을 담았어요. 가장 먼저 할 일 하나를 정해 보세요."),
    ("work", "caution"): ("매듭부", "새 일보다 마무리가 맞는 날의 뜻을 담았어요. 열어 둔 일 하나를 닫아 보세요."),
}
# 신살별 (이름, 뜻풀이). 뜻풀이는 daily_shinsal.GLOSS 와 같은 말이다.
SHINSAL_TEXT: dict[str, tuple[str, str]] = {
    "지살": ("첫걸음부", "새로 나서는 날"), "년살": ("눈길부", "시선이 모이는 날"),
    "월살": ("아낌부", "아껴 쓰는 날"), "망신": ("드러냄부", "있는 그대로 드러나는 날"),
    "장성": ("앞장부", "앞장서는 날"), "반안": ("제자리부", "안정을 찾는 날"),
    "역마": ("걸음부", "움직임이 많은 날"), "육해": ("잔손부", "잔손이 가는 날"),
    "화개": ("갈무리부", "혼자 정리하는 날"), "겁살": ("결단부", "결단이 필요한 날"),
    "재살": ("꼼꼼부", "꼼꼼히 따지는 날"), "천살": ("차례부", "순서를 따르는 날"),
}
_TONE_LINE = {
    "good": "오늘은 그 뜻대로 가볍게 밀어 보세요.",
    "neutral": "오늘은 곁에 두고 하루를 지내 보세요.",
    "caution": "오늘은 한 박자 늦추고 마음에 두세요.",
}


def text_for(kind: str, domain: str, shinsal: str | None, direction: str) -> tuple[str, str]:
    """(이름, 설명). 어떤 명세가 와도 빈 값을 내지 않는다."""
    if kind == "domain" and (domain, direction) in DOMAIN_TEXT:
        return DOMAIN_TEXT[(domain, direction)]
    name, gloss = SHINSAL_TEXT.get(shinsal or "", SHINSAL_TEXT["지살"])
    return name, f"{gloss}의 뜻을 붓으로 옮겼어요. {_TONE_LINE[direction]}"


def tone_of(grade: str) -> str:
    return "good" if grade in GOOD_GRADES else ("caution" if grade in BAD_GRADES else "neutral")


def seed_of(account_key: str, d: date) -> int:
    """같은 날 같은 계정이면 같은 그림이 되도록 날짜·계정에서 만든 시드."""
    return int(hashlib.md5(f"talisman|{account_key}|{d.isoformat()}".encode("utf-8")).hexdigest()[:8], 16)


def pick(*, shinsal_name: str | None, grade: str, domain_note: dict | None,
         luck_element: str, account_key: str, d: date) -> dict:
    """그날의 부적 명세. 화면이 이 값만으로 그림을 그린다."""
    element = _ELEMENT[luck_element]
    seed = seed_of(account_key, d)
    if domain_note:
        domain = _DOMAIN.get(domain_note["domain"])
        direction = "good" if domain_note["kind"] == "좋음" else "caution"
        if domain and (domain, direction) in DOMAIN_PARTS:
            name, desc = text_for("domain", domain, None, direction)
            return {"version": SPEC_VERSION, "kind": "domain", "domain": domain, "shinsal": None,
                    "dir": direction, "element": element, "layout": "dense",
                    "keys": list(DOMAIN_PARTS[(domain, direction)]), "seed": seed, "name": name, "desc": desc}
    name = shinsal_name if shinsal_name in SHINSAL_PARTS else "지살"   # 일주가 없을 때만 닿는 안전장치
    tone = tone_of(grade)
    sname, sdesc = text_for("shinsal", "", name, tone)
    return {"version": SPEC_VERSION, "kind": "shinsal", "domain": _SHINSAL_DOMAIN.get(name, "work"), "shinsal": name,
            "dir": tone, "element": element, "layout": "simple" if tone == "neutral" else "dense",
            "keys": list(SHINSAL_PARTS[name]), "seed": seed, "name": sname, "desc": sdesc}


def for_day(core, *, grade: str, domain_note: dict | None, luck_element: str, account_key: str, d: date) -> dict:
    """daily.py 가 부르는 입구. 신살 이름은 일지 기준(daily_shinsal 과 같은 판정)."""
    return pick(shinsal_name=daily_shinsal.name_of(core, d), grade=grade, domain_note=domain_note,
                luck_element=luck_element, account_key=account_key, d=d)
