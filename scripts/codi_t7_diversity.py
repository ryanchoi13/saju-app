"""코디 시험 T7 — 다양성 재기 (2026-11-24).

공식집 v1(docs/codi-knowledge/cases/formula-book.md)의 한국 FW-겨울 12칸만으로
착장을 30번(30일) 만들고, 몇 가지가 나오는지·같은 것이 얼마나 반복되는지·
표준에서 벗어나는 날이 있는지 센다.

- 색: 실제 엔진(fashion_v2.daily_colors.todays_lucky_tones)이 2026-11-25부터 30일 동안
  낸 행운 색 두 개를 쓴다. 표본은 20대 여성 1명·40대 남성 1명(고정 시드).
- 착장 틀·아이템 후보: 공식집에서 ★★ 이상인 기본·변형만 옮겼다(★·✕는 넣지 않음).
- 고르는 법: 칸마다 고정 시드로 무작위. 기본 착장은 변형보다 두 배 자주 뽑는다(크부장 판단).
- 행운 색 놓는 법: 공식집 2절 표 + 칸별 "행운 색" 줄. 공통 규칙 2(서로 다른 강한 색 두 개 금지)와
  엔진의 튀는 색 규칙(남성 35+ 아우터·하의·신발 금지)을 지킨다. 놓을 자리가 없으면 그 색은 뺀다.

실행: python3 scripts/codi_t7_diversity.py  (backend 의존성 필요: pip install -r requirements.txt)
"""
import datetime as dt
import json
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "backend"), str(ROOT)]

START = dt.date(2026, 11, 25)
DAYS = 30

# ---- 색 분류 (공식집 2절) ----
NEUTRAL = {"gray", "mid_gray", "charcoal", "black", "navy", "denim", "beige", "camel", "brown", "khaki", "olive"}
# 밝은 무채(흰·아이보리·라이트 그레이)는 공식집 2절의 "가라앉은 색"이 아니다 → 아우터가 아니라 이너·상의·하의로
LIGHT = {"white", "ivory", "light_gray"}
# 이름에 색이 박힌 아이템은 행운 색을 받지 않는다(예: 블랙 데님, 갈색 부츠)
COLOR_WORDS = ("블랙", "검정", "차콜", "갈색", "브라운", "흰", "회색", "네이비", "아이보리", "베이지", "인디고", "연청", "중청", "짙은 데님", "올리브", "갈회색", "파스텔", "밝은")
SOFT = {"sky", "lavender", "pink", "butter", "sage"}
DEEP = {"burgundy", "plum", "rust", "forest", "teal", "terracotta", "mustard"}
VIVID = {"red", "coral"}
FAMILY = {"burgundy": "red", "coral": "red", "red": "red", "pink": "red", "plum": "purple", "lavender": "purple",
          "rust": "earth", "terracotta": "earth", "mustard": "earth", "forest": "green", "teal": "teal",
          "sky": "blue", "butter": "yellow", "sage": "green"}
# 엔진 튀는 색 규칙: LOUD 계열 중 버건디·플럼·카멜·카키 예외
MALE_LOUD = {"coral", "red", "pink", "lavender", "butter"}


def kind(c):
    if c in NEUTRAL:
        return "neutral"
    if c in LIGHT:
        return "light"
    if c in SOFT:
        return "soft"
    if c in DEEP:
        return "deep"
    return "vivid"


# ---- 칸 정의: 공식집 v1의 FW-겨울, ★★ 이상 ----
# templates: (이름, 무게, {자리: 후보})
# slots: 색 종류별로 행운 색을 놓을 자리 순서. 자리 이름은 templates의 자리와 같아야 놓인다.
#   big = 가라앉은·무채 색을 받는 큰 자리, outer_like = 아우터·하의처럼 남성 튀는 색 금지 자리
CELLS = {
    "F20 미니멀": dict(
        templates=[("기본", 2, {"outer": ["오버 울 코트", "무스탕", "부클 코트"], "top": ["니트"],
                                "inner": ["흰 티 목", "셔츠 칼라"], "bottom": ["긴 스커트", "와이드 바지"],
                                "shoes": ["낮은 앵클부츠", "로퍼"], "bag": ["가방"]})],
        slots=dict(neutral=["outer", "bottom", "top"], soft=["inner", "top"], deep=["bag", "shoes"],
                   vivid=["inner", "bag"]), big=["outer", "bottom"]),
    "F20 캐주얼": dict(
        templates=[("기본", 2, {"outer": ["짧은 패딩", "짧은 재킷", "(아우터 없이) 오버 스웨트"],
                                "inner": ["흰 이너 목"], "bottom": ["와이드 데님", "스웨트 팬츠", "카고"],
                                "shoes": ["양털 부츠", "첼시 부츠"], "bag": ["가방"], "hat": ["비니", "볼캡", "-"]}),
                   ("짧은 하의 + 타이츠", 1, {"outer": ["짧은 패딩", "짧은 재킷"], "top": ["니트", "스웨트"],
                                          "bottom": ["미니 스커트", "쇼츠"], "legs": ["회색 타이츠", "검정 타이츠"],
                                          "shoes": ["롱부츠"], "bag": ["가방"]})],
        slots=dict(neutral=["outer", "bottom"], soft=["hat", "inner", "top"], deep=["bag", "top"],
                   vivid=["bag", "hat", "inner"]), big=["outer", "bottom"]),
    "F20 페미닌": dict(
        templates=[("기본", 2, {"outer": ["코트", "짧은 재킷"], "top": ["니트", "카디건"],
                                "neck": ["블라우스 칼라", "머플러", "긴 스카프"],
                                "bottom": ["퍼지는 미디 스커트", "슬림 새틴 롱스커트", "와이드 바지"],
                                "shoes": ["굽 낮은 구두", "롱부츠"], "bag": ["가방"]}),
                   ("짧은 하의 + 다리 한 겹", 1, {"outer": ["코트", "짧은 재킷"], "top": ["니트", "카디건"],
                                              "bottom": ["미니 스커트", "짧은 원피스"], "legs": ["타이츠", "니삭스"],
                                              "shoes": ["롱부츠"], "bag": ["가방"]})],
        slots=dict(neutral=["outer", "bottom"], soft=["top", "bottom", "neck"], deep=["bag", "neck"],
                   vivid=["neck", "top"]), big=["outer", "bottom"]),
    "F20 스트릿": dict(
        templates=[("기본", 2, {"outer": ["짧은 패딩", "플리스", "카디건", "(아우터 없이) 오버 스웨트"],
                                "bottom": ["와이드 트라우저", "와이드 데님", "스웨트 팬츠"],
                                "shoes": ["털 부츠", "스웨이드 부츠", "블랙 로퍼"], "hat": ["캡", "-"], "bag": ["가방"]}),
                   ("짧은 겉옷 + 긴 스커트", 1, {"outer": ["짧은 패딩", "코트", "필드 재킷"],
                                            "bottom": ["미디 스커트", "맥시 스커트"], "shoes": ["털 부츠", "블랙 로퍼"],
                                            "bag": ["가방"]}),
                   ("짧은 하의 + 레그워머", 1, {"outer": ["짧은 패딩", "플리스"], "bottom": ["미니 스커트", "쇼츠"],
                                           "legs": ["레그워머"], "shoes": ["부츠"], "bag": ["가방"]}),
                   ("스웨트 셋업", 1, {"setup": ["스웨트 셋업", "트랙 셋업"], "shoes": ["털 부츠", "운동화"],
                                     "bag": ["가방"]})],
        slots=dict(neutral=["outer", "setup", "bottom"], soft=["outer", "setup"], deep=["outer", "setup", "bag"],
                   vivid=["hat", "bag"]), big=["outer", "setup", "bottom"]),
    "F20 클래식": dict(
        templates=[("기본", 2, {"outer": ["짧은 재킷"], "top": ["니트"], "neck": ["흰·회색 터틀넥", "V넥 안 흰 이너"],
                                "bottom": ["블랙 미디 스커트", "그레이 롱스커트", "발목 바지"],
                                "shoes": ["낮은 구두"], "bag": ["블랙 가죽 가방", "브라운 가죽 가방"]}),
                   ("롱코트", 1, {"outer": ["종아리 롱코트"], "top": ["니트"], "neck": ["흰·회색 터틀넥"],
                                 "bottom": ["블랙 미디 스커트", "발목 바지"], "shoes": ["낮은 구두", "앵클부츠"],
                                 "bag": ["블랙 가죽 가방", "브라운 가죽 가방"]})],
        slots=dict(neutral=["outer", "top"], soft=["neck", "top"], deep=["bag", "shoes"], vivid=["neck"]),
        big=["outer"]),
    "F20 애슬레저": dict(
        templates=[("기본", 2, {"outer": ["짧은 경량 다운"], "bottom": ["레깅스", "트랙 팬츠", "스웨트 팬츠"],
                                "shoes": ["러닝화 + 보이는 양말"], "scarf": ["-"]}),
                   ("다운 + 비운동복 하의", 1, {"outer": ["짧은 경량 다운"], "bottom": ["데님", "플리츠 미니"],
                                            "shoes": ["러닝화 + 보이는 양말", "부츠"], "scarf": ["-"]}),
                   ("이너·하의 같은 밝은 색", 1, {"outer": ["짧은 경량 다운"], "inner": ["이너"],
                                             "bottom": ["같은 색 트랙 팬츠"], "shoes": ["러닝화"], "scarf": ["-"]})],
        slots=dict(neutral=["outer", "bottom"], soft=["outer"], deep=["scarf", "shoes"], vivid=["scarf", "shoes"]),
        big=["outer", "bottom"]),
    "M40 미니멀": dict(
        templates=[("기본", 2, {"outer": ["트러커", "블루종", "레더 재킷", "코트"], "inner": ["이너(목에 보이게)"],
                                "bottom": ["블랙·차콜 와이드", "연청 데님", "중청 데님"],
                                "shoes": ["블랙 더비", "블랙 로퍼", "블랙 첼시"], "acc": ["머플러", "가방", "-"]}),
                   ("짙은 위 + 갈색 바지", 1, {"outer": ["블루종", "코트"], "top": ["니트"], "bottom": ["갈색 와이드"],
                                           "shoes": ["블랙 더비", "블랙 로퍼"], "acc": ["머플러", "-"]}),
                   ("밝은 니트 + 짙은 아래", 1, {"outer": ["코트"], "top": ["니트"],
                                              "bottom": ["블랙·차콜 와이드"], "shoes": ["블랙 더비"], "acc": ["-"]})],
        slots=dict(neutral=["outer", "top", "inner"], soft=["inner", "top", "acc"], deep=["top", "inner", "acc"], vivid=["inner", "top", "acc"]),
        big=["outer"]),
    "M40 댄디": dict(
        templates=[("기본", 2, {"outer": ["재킷", "블루종", "코트"], "top": ["티", "크루넥 니트", "모크넥 니트"],
                                "bottom": ["블랙 와이드 슬랙스", "차콜 와이드 슬랙스"], "shoes": ["블랙 구두", "블랙 첼시"],
                                "muffler": ["머플러", "-"]}),
                   ("셋업", 1, {"setup": ["회색 셋업", "차콜 셋업", "갈회색 셋업"], "top": ["크루넥 니트", "티"],
                               "shoes": ["블랙 구두"], "muffler": ["머플러", "-"]}),
                   ("갈색 블루종", 1, {"outer": ["갈색 스웨이드 블루종", "갈색 가죽 블루종"], "top": ["니트"],
                                     "bottom": ["블랙 와이드 슬랙스"], "shoes": ["블랙 구두", "블랙 첼시"],
                                     "muffler": ["머플러", "-"]})],
        slots=dict(neutral=["outer", "setup", "top", "muffler"], soft=["top", "muffler"], deep=["top", "muffler"], vivid=["top", "muffler"]),
        big=["outer", "setup"]),
    "M40 클래식": dict(
        templates=[("기본", 1, {"outer": ["클래식 코트", "종아리 롱코트", "짧은 트래드 재킷"], "top": ["니트"],
                                "neck": ["셔츠 칼라", "터틀넥"], "bottom": ["아이보리 와이드", "짙은 데님", "정장 바지"],
                                "shoes": ["검정 가죽 구두"], "muffler": ["머플러", "-"]})],
        slots=dict(neutral=["outer", "bottom"], soft=["top", "muffler"], deep=["muffler", "top"],
                   vivid=["muffler"]), big=["outer", "bottom"]),
    "M40 캐주얼": dict(
        templates=[("기본", 1, {"outer": ["블루종", "셔츠 재킷", "짧은 패딩", "MA-1"], "inner": ["흰·회색 티 목", "후드"],
                                "bottom": ["데님", "치노", "코듀로이", "부츠컷 데님"],
                                "shoes": ["검정 가죽", "갈색 부츠", "블랙 단색 운동화"], "hat": ["볼캡", "비니", "-"],
                                "bag": ["가방", "-"]})],
        slots=dict(neutral=["outer", "bottom", "shoes"], soft=["hat", "inner"], deep=["bag", "inner"],
                   vivid=["inner", "bag", "hat"]), big=["outer", "bottom"]),
    "M40 아메카지": dict(
        templates=[("기본", 2, {"outer": ["밀리터리 재킷", "가죽 재킷", "워크 재킷", "데님 재킷"],
                                "layer": ["셔츠", "후드"], "bottom": ["인디고 데님", "블랙 데님", "올리브 카고", "베이지 치노", "치노"],
                                "shoes": ["갈색 부츠", "갈색 더비"], "pattern": ["체크 셔츠", "페어아일 니트", "-"],
                                "hat": ["비니", "볼캡", "-"]}),
                   ("짧은 다운", 1, {"outer": ["짧은 다운"], "bottom": ["와이드 데님", "와이드 카고"],
                                    "shoes": ["갈색 부츠"], "hat": ["비니", "볼캡"]})],
        slots=dict(neutral=["outer", "bottom"], soft=["hat", "layer"], deep=["layer", "hat"], vivid=["hat"]),
        big=["outer", "bottom"]),
    "M40 고프코어": dict(
        templates=[("출근·시티형", 2, {"outer": ["기능 아우터(다운)", "기능 아우터(셸)"], "top": ["니트", "셔츠", "티", "스웻"],
                                      "bottom": ["코듀로이", "치노", "카고"], "shoes": ["방한 부츠", "운동화"],
                                      "hat": ["비니", "볼캡", "-"]}),
                   ("일상·테크형", 1, {"outer": ["셸", "패딩"], "top": ["티", "플리스"],
                                     "bottom": ["파라슈트 팬츠", "나일론 카고"], "shoes": ["운동화", "부츠"],
                                     "hat": ["비니", "-"]})],
        slots=dict(neutral=["outer", "top"], soft=["outer", "top"], deep=["top", "hat"], vivid=["hat", "top"]),
        big=["outer"]),
}
MALE_FORBIDDEN_SLOTS = {"outer", "bottom", "setup", "shoes"}


def lucky_colors():
    from app.engine.core.models import BirthInput
    from app.engine.orchestrator import calculate_myeongri_core
    from app.engine.services.daily import build_daily_fortune
    from fashion_v2.daily_colors import todays_lucky_tones

    rng = random.Random(20261124)
    people = {"F20": ("female", dt.date(rng.randint(1997, 2006), rng.randint(1, 12), rng.randint(1, 28)), rng.randint(0, 23)),
              "M40": ("male", dt.date(rng.randint(1977, 1986), rng.randint(1, 12), rng.randint(1, 28)), rng.randint(0, 23))}
    out = {}
    for key, (g, b, h) in people.items():
        days = []
        for i in range(DAYS):
            d = START + dt.timedelta(days=i)
            core = calculate_myeongri_core(BirthInput(name="검사", gender=g, birth_date=b, calendar_type="solar",
                                                      is_leap_month=False, birth_time=dt.time(h, 0),
                                                      time_unknown=False), target_date=d)
            f = build_daily_fortune(core, "검사", d, current_hour=8, account_key=None, include_menu=False)
            lk = todays_lucky_tones(core, f, d.toordinal(), b.year * 372 + b.month * 31 + b.day)
            days.append((lk["tone_a"]["id"], lk["tone_b"]["id"]))
        out[key] = dict(gender=g, birth=str(b), days=days)
    return out


def place(cell, items, colors, male):
    """행운 색 두 개를 자리에 놓는다. 반환: {자리: 색}, 뺀 색 목록, 사유."""
    used, placed, dropped, notes = set(), {}, [], []
    strong = [c for c in colors if kind(c) in ("deep", "vivid")]
    if len(strong) == 2 and FAMILY.get(strong[0]) != FAMILY.get(strong[1]):
        dropped.append(strong[1])
        notes.append("강한 색 둘(계열 다름) → 둘째 뺌")
    # 색 있는 쪽이 먼저 자리를 고르고, 무채·가라앉은 색이 남은 바탕 자리를 맡는다(공식집 2절에 더함)
    for c in sorted(colors, key=lambda c: kind(c) in ("neutral", "light")):
        if c in dropped:
            continue
        order = (cell["slots"]["soft"] + [x for x in cell["slots"]["neutral"] if x not in ("outer", "setup")]
                 if kind(c) == "light" else cell["slots"][kind(c)])
        for slot in order:
            if slot not in items or slot in used:
                continue
            if any(w in items[slot] for w in COLOR_WORDS):
                continue
            if male and c in MALE_LOUD and slot in MALE_FORBIDDEN_SLOTS:
                continue
            if items[slot] == "-":   # 공식집이 허락한 소품 자리를 이날 비워 뒀으면, 색을 위해 소품을 더한다
                notes.append(f"소품 더함({slot})")
            placed[slot] = c
            used.add(slot)
            break
        else:
            dropped.append(c)
            notes.append(f"{c}: 놓을 자리 없음")
    return placed, dropped, notes


def run():
    colors = lucky_colors()
    report = {"colors": colors, "cells": {}}
    for name, cell in CELLS.items():
        group = name.split()[0]
        male = group == "M40"
        rng = random.Random(f"T7-{name}")
        pool = [t for t in cell["templates"] for _ in range(t[1])]
        rows = []
        for i in range(DAYS):
            tname, _, slots = rng.choice(pool)
            items = {k: rng.choice(v) for k, v in slots.items()}
            placed, dropped, notes = place(cell, items, colors[group]["days"][i], male)
            rows.append(dict(day=str(START + dt.timedelta(days=i)), template=tname, items=items,
                             colors=colors[group]["days"][i], placed=placed, dropped=dropped, notes=notes))
        comp = [json.dumps(r["items"], ensure_ascii=False, sort_keys=True) for r in rows]
        full = [c + json.dumps(r["placed"], ensure_ascii=False, sort_keys=True) for c, r in zip(comp, rows)]
        cnt = Counter(comp)
        space = 0
        for _, _, slots in cell["templates"]:
            n = 1
            for v in slots.values():
                n *= len(v)
            space += n
        report["cells"][name] = dict(
            space=space, unique_items=len(cnt), max_repeat=max(cnt.values()),
            same_as_yesterday=sum(1 for a, b in zip(comp, comp[1:]) if a == b),
            unique_full=len(set(full)), template_mix=Counter(r["template"] for r in rows),
            days_one_color=sum(1 for r in rows if len(r["dropped"]) == 1),
            days_no_color=sum(1 for r in rows if len(r["dropped"]) == 2),
            drop_reasons=Counter(("놓을 자리 없음" if ":" in n else n) for r in rows for n in r["notes"] if not n.startswith("소품")),
            addon_days=sum(1 for r in rows if any(n.startswith("소품") for n in r["notes"])),
            slot_use=Counter(s for r in rows for s in r["placed"]), rows=rows)
    return report


if __name__ == "__main__":
    rep = run()
    out = Path("/tmp/codi_t7.json")
    out.write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=dict))
    for name, r in rep["cells"].items():
        print(f"{name}: 가능한 조합 {r['space']} · 30일 중 다른 구성 {r['unique_items']} · 최다 반복 {r['max_repeat']} · "
              f"어제와 같음 {r['same_as_yesterday']} · 색까지 다른 착장 {r['unique_full']} · "
              f"한 색만 {r['days_one_color']}일 · 색 0 {r['days_no_color']}일 · 소품 더한 날 {r['addon_days']} · {dict(r['drop_reasons'])}")
