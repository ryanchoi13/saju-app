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
from app.engine.services.gungtong_johu import GUNGTONG_JOHU

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
