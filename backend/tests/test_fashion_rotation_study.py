"""Regression tests for the non-production rotation study (#190 review items 2 and 3)."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("fashion_rotation_study", ROOT / "scripts" / "fashion_rotation_study.py")
study = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(study)

USER = {"id": "u", "gender": "male"}
WARM = {"temp": 3.0}


def c(cid, role, composition, outer="coat"):
    return study.cand(cid, "male", "casual", role, composition, outer, False)


# ---- item 2: a kept role survives a shortage ----

def test_kept_trendy_survives_when_only_same_composition_basic_exists():
    b, t = c("b", "basic", "SAME"), c("t", "trendy", "SAME")
    res = study.choose([b, t], USER, "casual", WARM, "d1", [], "hierarchical", keep={"trendy": t})
    assert res["trendy"] is t and res["basic"] is None
    assert res["shortage"] == "basic_missing"


def test_kept_basic_survives_when_only_same_composition_trendy_exists():
    b, t = c("b", "basic", "SAME"), c("t", "trendy", "SAME")
    res = study.choose([b, t], USER, "casual", WARM, "d1", [], "hierarchical", keep={"basic": b})
    assert res["basic"] is b and res["trendy"] is None
    assert res["shortage"] == "trendy_missing"


def test_kept_role_stays_and_only_the_other_role_is_chosen():
    b, t1, t2 = c("b", "basic", "B"), c("t1", "trendy", "T1"), c("t2", "trendy", "T2")
    res = study.choose([b, t1, t2], USER, "casual", WARM, "d1", [], "hierarchical", keep={"basic": b})
    assert res["basic"] is b and res["trendy"] in (t1, t2) and res["shortage"] is None


def test_no_candidate_at_all():
    res = study.choose([], USER, "casual", WARM, "d1", [], "hierarchical")
    assert res == {"basic": None, "trendy": None, "shortage": "no_candidate", "relaxed": [], "notes": []}


def test_revisit_replaces_only_the_violating_role():
    pool = [c("puffer", "basic", "P", "short_puffer"), c("fleece", "basic", "F", "fleece"),
            c("coat", "trendy", "C")]
    visits = [{"date": "2026-12-01", "weather": {"temp": 3.0}},
              {"date": "2026-12-01", "weather": {"temp": 6.0}}]
    first, second = [r for r in study.run(pool, visits, "hierarchical") if r["user"] == "male-28" and r["tpo"] == "casual"]
    assert (first["basic"], first["trendy"]) == ("puffer", "coat")
    assert (second["basic"], second["trendy"]) == ("fleece", "coat") and second["changed"]


# ---- item 3: one identity for windows, repeats and counts ----

def test_same_composition_with_a_different_id_is_penalised():
    a, a2, other = c("a", "basic", "FORMULA"), c("a2", "basic", "FORMULA"), c("x", "basic", "OTHER")
    history = [{"date": "d0", "basic": a, "trendy": None}]
    assert study.role_penalty("composition", a2, "basic", history, n=2)[0] == 1
    assert study.role_penalty("composition", other, "basic", history, n=2)[0] == 0


def test_window_is_bounded_by_distinct_compositions():
    a, a2 = c("a", "basic", "SAME"), c("a2", "basic", "SAME")
    history = [{"date": "d0", "basic": a, "trendy": None}]
    # Two ids but one composition -> n = 1 -> no alternative -> no penalty and a note.
    assert study.role_penalty("composition", a2, "basic", history, n=1)[0] == 0
    res = study.choose([a, a2, c("t", "trendy", "T")], USER, "casual", WARM, "d1", history, "composition")
    assert "no_alternative_basic" in res["notes"]


def test_repeat_metric_counts_compositions_not_ids():
    rows = []
    for day, cid in (("2026-12-01", "a"), ("2026-12-02", "a2")):
        rows.append(dict(user="u", tpo="casual", date=day, label="", changed=False, basic=cid, trendy=None,
                         basic_outer="coat", trendy_outer=None, basic_composition="FORMULA", trendy_composition=None,
                         shortage="trendy_missing", relaxed=[], notes=[], violation=False))
    m = study.metrics(rows)
    assert m["same_composition_as_previous_day"] == 1
    assert m["same_composition_rate_excl_first_day"] == 1.0
    assert m["longest_same_composition_streak_days"] == 2


def test_committed_study_output_is_current():
    assert study.OUT.read_text() == __import__("json").dumps(
        study.build(), ensure_ascii=False, indent=1, sort_keys=True) + "\n"
