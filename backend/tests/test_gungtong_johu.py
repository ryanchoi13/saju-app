"""강약 보류자의 보완 오행 = 『궁통보감』 조후용신 1·2순위 (2026-11-05 정오님 결정).

결정 문서: 프로젝트 claude/decisions-2026-11-05-strength.md (B')
- 1·2순위 다음은 비율·조후 점수 순, 원문이 꺼린 오행은 그 뒤, 원국 35% 이상 오행은 맨 뒤
  (점수 카드 '과다 강화'와 같은 기준 — 한 화면에서 같은 오행을 권하고 감점하지 않게)
- 강약 방향이 있는 사람은 억부 그대로(이 표를 쓰지 않음)
"""
import csv
import datetime as dt
import pathlib
import random

from app.engine.constants import GAN_WUXING
from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.services import daily_score
from app.engine.services.element_balance import (
    ELEMENTS, EXCESS_SHARE, daily_blend, eokbu_avoid, natal_balance,
)
from app.engine.services.gungtong_johu import CONDITIONS, GUNGTONG_JOHU, choose

STEMS, BRANCHES = "甲乙丙丁戊己庚辛壬癸", "子丑寅卯辰巳午未申酉戌亥"
CSV_PATH = pathlib.Path(__file__).resolve().parents[2] / "docs" / "engine" / "gungtong-johu.csv"


def _stems(text):
    return tuple(ch for ch in text if ch in STEMS)


def test_table_covers_all_120_cells_with_real_stems():
    assert set(GUNGTONG_JOHU) == {(s, b) for s in STEMS for b in BRANCHES}
    for (stem, branch), (primary, secondary, shunned, checked) in GUNGTONG_JOHU.items():
        assert primary in STEMS and (secondary is None or secondary in STEMS)
        assert all(s in STEMS for s in shunned) and isinstance(checked, bool)


def test_table_matches_the_evidence_csv():
    """코드 표와 근거 CSV(docs/engine/gungtong-johu.csv)가 어긋나지 않게."""
    rows = list(csv.DictReader(CSV_PATH.open(encoding="utf-8-sig")))
    assert len(rows) == 120
    for r in rows:
        primary, secondary, shunned, checked = GUNGTONG_JOHU[(r["day_stem"], r["month_branch"])]
        assert primary == r["primary"]
        assert secondary == (_stems(r["secondary"])[:1] or (None,))[0]
        assert shunned == _stems(r["avoid"])
        assert checked == (r["cross_checked"] == "true")


def test_excess_threshold_is_the_score_cards():
    source = pathlib.Path(daily_score.__file__).read_text(encoding="utf-8")
    assert f"share >= {EXCESS_SHARE}:" in source


def _core(gender, birth, hour):
    return calculate_myeongri_core(BirthInput(
        name="검사", gender=gender, birth_date=birth, calendar_type="solar", is_leap_month=False,
        birth_time=dt.time(hour, 0), time_unknown=False), target_date=dt.date(2026, 11, 5))


def _cores(n=80, seed=1105):
    rng = random.Random(seed)
    for _ in range(n):
        yield _core(rng.choice(["male", "female"]),
                    dt.date(rng.randint(1960, 2004), rng.randint(1, 12), rng.randint(1, 28)), rng.randint(0, 23))


def test_golden_case():
    # 癸 일간 午월: 원문 庚·辛(둘 다 金) → 1순위 金, 2순위는 점수 순(午월 더위 → 水)
    nb = natal_balance(_core("female", dt.date(1990, 7, 7), 9))
    assert nb["method"] == "gungtong_johu"
    assert nb["ranking"][:2] == ["金", "水"]
    assert nb["blend_base"] == {"金": 5.0, "水": 3.5, "木": 2.0, "土": 1.0, "火": 0.0}


def test_pending_people_follow_the_table_with_guards():
    seen = {"gungtong_johu": 0, "eokbu": 0}
    for core in _cores():
        nb = natal_balance(core)
        seen[nb["method"]] += 1
        share, ranking = nb["composition"], nb["ranking"]
        assert sorted(ranking) == sorted(ELEMENTS)
        if nb["method"] == "eokbu":
            # 억부 경로는 바뀌지 않는다: 기신 맨 뒤, 나머지는 점수 순
            avoid = set(nb["eokbu_avoid"])
            scores = nb["scores"]
            expected = sorted(ELEMENTS, key=lambda e: (e in avoid, -scores[e], share[e], ELEMENTS.index(e)))
            assert ranking == expected and nb["blend_base"] is None and nb["overflow"] is None
            continue
        day, month = core.natal_facts.pillars["day"], core.natal_facts.pillars["month"]
        primary, secondary, shunned, _ = GUNGTONG_JOHU[(day.stem, month.branch)]
        if nb["gungtong_condition"]:   # 조건부 칸이 맞은 경우: 조건 규칙의 1·2순위(아래 조건 테스트에서 따로 검사)
            rule = next(r for r in CONDITIONS[(day.stem, month.branch)] if r[4] == nb["gungtong_condition"])
            primary, secondary = rule[2], rule[3]
        overflow = set(nb["overflow"])
        assert overflow == {e for e in ELEMENTS if share[e] >= EXCESS_SHARE}
        if GAN_WUXING[primary] not in overflow:
            assert ranking[0] == GAN_WUXING[primary]
        picks = {GAN_WUXING[primary]} | ({GAN_WUXING[secondary]} if secondary else set())
        top2 = set(ranking[:2])
        # 넘치는 오행은 다른 오행이 남아 있는 한 위 두 칸에 오지 않는다
        if len(ELEMENTS) - len(overflow) >= 2:
            assert not (top2 & overflow), (day.stem, month.branch, ranking, share)
        # 원문이 꺼린 오행은 쓰는 오행(1·2순위)이 아니면 위 두 칸에 오지 않는다
        for s in shunned:
            e = GAN_WUXING[s]
            if e not in picks:
                assert e not in top2, (day.stem, month.branch, ranking)
        assert eokbu_avoid(GAN_WUXING[day.stem], str(core.synthesis.strength_state)) == set()
    assert seen["gungtong_johu"] and seen["eokbu"]


def test_blend_moves_overflowing_day_element_to_its_outlet():
    for core in _cores(40):
        nb = natal_balance(core)
        if nb["method"] != "gungtong_johu" or not nb["overflow"]:
            continue
        e = nb["overflow"][0]
        blend = daily_blend(nb, e, "子")
        assert blend["daily_part"][e] <= 0   # 넘치는 오행이 일간으로 와도 더 채우라고 하지 않는다
        return


# ── 조건부 용신 (2026-11-06) ──


_EVEN = {e: 20.0 for e in ELEMENTS}


def test_conditions_use_real_stems_and_the_excess_threshold():
    from app.engine.services import gungtong_johu
    for key, rules in CONDITIONS.items():
        assert key in GUNGTONG_JOHU
        for kind, arg, p, s, note in rules:
            assert kind in {"second_half", "first_half", "ju", "ju_peer", "many", "many2"}
            assert p in STEMS and (s is None or s in STEMS) and note.startswith("L")
    assert gungtong_johu.MANY_SHARE == EXCESS_SHARE


def test_each_condition_switches_only_when_it_holds():
    base = dict(share=_EVEN, branches=["子", "午", "卯", "酉"], other_stems=["壬", "壬", "壬"], second_half=None)
    for (stem, branch) in CONDITIONS:
        assert choose(stem, branch, **base)[:2] == GUNGTONG_JOHU[(stem, branch)][:2], (stem, branch)
    # 절기
    assert choose("乙", "酉", **{**base, "second_half": True})[:2] == ("丙", "癸")
    assert choose("乙", "酉", **{**base, "second_half": False})[:2] == GUNGTONG_JOHU[("乙", "酉")][:2]
    assert choose("癸", "辰", **{**base, "second_half": False})[:2] == ("丙", None)
    # 국: 甲 辰월 + 巳酉丑 金局
    assert choose("甲", "辰", **{**base, "branches": ["巳", "辰", "酉", "丑"]})[:2] == ("丁", None)
    # 반합(酉丑)만으로는 국이 아니다
    assert choose("甲", "辰", **{**base, "branches": ["子", "辰", "酉", "丑"]})[:2] == GUNGTONG_JOHU[("甲", "辰")][:2]
    # 국 + 비겁 투출
    ju_wood = {**base, "branches": ["亥", "酉", "卯", "未"]}
    assert choose("甲", "酉", **ju_wood)[:2] == GUNGTONG_JOHU[("甲", "酉")][:2]
    assert choose("甲", "酉", **{**ju_wood, "other_stems": ["乙", "癸", "壬"]})[:2] == ("庚", "丁")
    # 土局 = 四庫 세 글자
    assert choose("庚", "未", **{**base, "branches": ["辰", "未", "戌", "子"]})[:2] == ("甲", "丁")
    # 많음 / 둘 합
    assert choose("甲", "戌", **{**base, "share": {**_EVEN, "木": 35.0}})[:2] == ("庚", None)
    assert choose("甲", "戌", **{**base, "share": {**_EVEN, "木": 34.9}})[:2] == GUNGTONG_JOHU[("甲", "戌")][:2]
    assert choose("乙", "午", **{**base, "share": {**_EVEN, "金": 25.0, "水": 25.0}})[:2] == ("丙", "癸")
    # 丙 亥월은 위에서부터 첫 조건: 木旺 → 庚, 水旺 → 戊
    assert choose("丙", "亥", **{**base, "share": {**_EVEN, "木": 40.0, "水": 40.0}})[:2] == ("庚", None)
    assert choose("丙", "亥", **{**base, "share": {**_EVEN, "水": 40.0}})[:2] == ("戊", None)


def test_positive_cases_for_every_rule_kind():
    base = dict(share=_EVEN, branches=["子", "午", "卯", "酉"], other_stems=["壬", "壬", "壬"], second_half=None)
    many = lambda e, v=40.0: {**base, "share": {**_EVEN, e: v}}
    ju = lambda *b: {**base, "branches": list(b)}
    cases = [
        (("甲", "午"), many("木"), ("庚", "丁")), (("甲", "午"), many("金"), ("丁", None)),
        (("甲", "未"), many("木"), ("庚", "丁")),
        (("乙", "未"), {**base, "share": {**_EVEN, "金": 30.0, "水": 20.0}}, ("丙", "癸")),
        (("丙", "亥"), many("火"), ("壬", None)),
        (("丁", "辰"), ju("寅", "辰", "卯", "子"), ("庚", None)),    # 방합 寅卯辰 — 방합도 局으로(해석)
        (("丁", "巳"), many("木"), ("庚", None)),
        (("丁", "子"), many("火"), ("甲", "癸")),
        (("戊", "申"), ju("申", "申", "子", "辰"), ("甲", None)),
        (("己", "酉"), ju("巳", "酉", "丑", "子"), ("丙", "丁")),
        (("己", "亥"), many("水"), ("戊", "丙")),
        (("庚", "巳"), ju("申", "巳", "酉", "戌"), ("丁", None)),    # 방합 申酉戌
        (("庚", "申"), ju("辰", "申", "丑", "未"), ("甲", "丁")),
    ]
    for (stem, branch), ctx, want in cases:
        assert choose(stem, branch, **ctx)[:2] == want, (stem, branch)
    # 경계 바로 아래는 안 걸린다
    assert choose("乙", "午", **{**base, "share": {**_EVEN, "金": 25.0, "水": 24.9}})[:2] == GUNGTONG_JOHU[("乙", "午")][:2]
    # 癸 辰월 하반월(穀雨 뒤)은 기본 칸(丙 + 辛)
    assert choose("癸", "辰", **{**base, "second_half": True})[:2] == GUNGTONG_JOHU[("癸", "辰")][:2]
    # 절기를 모르면(None) 절기 조건은 어느 쪽도 걸리지 않는다
    assert choose("乙", "酉", **base)[:2] == GUNGTONG_JOHU[("乙", "酉")][:2]


def test_midterm_is_read_from_the_birth_moment():
    from app.engine.services.element_balance import _born_after_midterm
    before = _core("male", dt.date(1990, 9, 17), 9)   # 白露(9/8)와 秋分(9/23 14:55) 사이
    after = _core("male", dt.date(1990, 9, 27), 9)    # 秋分 뒤
    assert _born_after_midterm(before) is False and _born_after_midterm(after) is True
    assert after.natal_facts.pillars["day"].stem == "乙" and after.natal_facts.pillars["month"].branch == "酉"
    nb = natal_balance(after)
    assert nb["method"] == "gungtong_johu"
    assert nb["gungtong_condition"].startswith("L142") and nb["ranking"][0] == "火"
    # 다른 달의 중기도 시각으로 판정(谷雨 1990-04-20 앞뒤)
    assert _born_after_midterm(_core("female", dt.date(1990, 4, 10), 9)) is False
    assert _born_after_midterm(_core("female", dt.date(1990, 4, 28), 9)) is True


def test_midterm_unknown_time_on_the_term_day_is_unknown():
    from app.engine.services.element_balance import _born_after_midterm
    core = calculate_myeongri_core(BirthInput(
        name="검사", gender="male", birth_date=dt.date(1990, 9, 23), calendar_type="solar",
        is_leap_month=False, birth_time=None, time_unknown=True), target_date=dt.date(2026, 11, 5))
    assert _born_after_midterm(core) is None
