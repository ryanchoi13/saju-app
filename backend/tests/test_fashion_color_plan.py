"""코디 색 틀(fashion_v2/color_plan) 검사. 2026-10-30."""
import datetime as dt
import json
from pathlib import Path

from fashion_v2.color_plan import load_rules, plan_outfit_colors, tone_class
from fashion_v2.color_plan.report import evaluate, measure, outfit_slots, simulate
from fashion_v2.svg_recommendation import PALETTE as P

ROOT = Path(__file__).resolve().parents[2]
SLOTS = outfit_slots("autumn")


def test_every_rule_cites_an_existing_chapter():
    chapters = {p.name[:2] for p in (ROOT / "docs" / "codi-knowledge").glob("[0-9][0-9]-*.md")}
    for rule in load_rules().values():
        assert rule["evidence"], rule["id"]
        for e in rule["evidence"]:
            assert e["chapter"] in chapters, (rule["id"], e["chapter"])
            assert e["grade"] in "ABCD"


def test_two_vivid_colors_are_never_worn_together():
    plan = plan_outfit_colors(SLOTS, [P["red"], P["cobalt"]])
    assert plan["unplaced"] == ["cobalt"]
    assert [s["color"] for s in plan["slots"].values() if s["source"] == "lucky"] == ["red"]


def test_vivid_hero_goes_to_a_small_slot():
    plan = plan_outfit_colors(SLOTS, [P["yellow"], P["navy"]])
    slot = next(k for k, v in plan["slots"].items() if v["color"] == "yellow")
    assert next(s for s in SLOTS if s["slot"] == slot)["area"] == "small"


def test_hero_does_not_repeat_from_yesterday():
    plan = plan_outfit_colors(SLOTS, [P["burgundy"], P["navy"]], recent_heroes=["burgundy"])
    assert plan["hero"] == "navy"


def test_slots_without_rules_are_reported_as_gaps():
    plan = plan_outfit_colors(SLOTS, [P["olive"], P["navy"]])
    assert set(plan["gaps"]) == {k for k, v in plan["slots"].items() if v["source"] == "base"}
    assert all(v["evidence"] for k, v in plan["slots"].items() if k not in plan["gaps"])
    assert {k for k in plan["slots"]} == {s["slot"] for s in SLOTS}


def test_tone_classes_cover_the_palette():
    assert {tone_class(c) for c in P.values()} <= {"vivid", "light", "dull", "dark", "neutral"}
    assert tone_class(P["red"]) == "vivid" and tone_class(P["navy"]) == "neutral"


def test_release_gate_blocks_until_every_check_passes():
    good = dict(hero_consecutive_repeat_rate=0.0, max_same_hero_in_14_days=3,
                vivid_pair_violations=0, evidence_share=1.0)
    assert evaluate(good)["release_ready"]
    assert not evaluate({**good, "evidence_share": 0.99})["release_ready"]
    assert not evaluate({**good, "max_same_hero_in_14_days": 4})["release_ready"]


def test_small_real_simulation_has_no_hard_violations():
    runs = simulate(dt.date(2026, 11, 1), 21, users=[("female", (2002, 4, 11), 10), ("male", (1990, 8, 17), 11),
                                                       ("male", (1984, 2, 8), 9)])
    m = measure(runs)
    assert m["outfits"] == 63
    assert m["hero_consecutive_repeat_rate"] == 0.0
    assert m["vivid_pair_violations"] == 0
    checks = json.loads((ROOT / "fashion_v2" / "color_plan" / "checks.json").read_text(encoding="utf-8"))
    assert set(evaluate(m, checks)) == {"hero_repeat", "hero_14_days", "vivid_pairs", "evidence", "release_ready"}
