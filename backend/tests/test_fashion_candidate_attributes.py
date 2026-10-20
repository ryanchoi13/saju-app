"""PR-2 (#188): candidate attributes, live matcher check, independent constraint oracle.

None of this changes live output: the recommendation path does not import these
modules (pinned below), and the legacy rule violations are reproduced, not hidden.
"""
import ast
import os
import shutil
from pathlib import Path

import pytest

from fashion_v2 import candidate_constraints as cc
from fashion_v2.candidate_attributes import ATTRIBUTES, OBSERVED_OUTER_LENGTH, policy_rule
from fashion_v2.candidate_registry import active_candidates, observed_illustrations

ROOT = Path(__file__).resolve().parents[2]


# ---------- attributes ----------

def test_every_active_candidate_has_attributes_with_sources():
    assert set(ATTRIBUTES) == {c["candidate_id"] for c in active_candidates()}
    for cid, attrs in ATTRIBUTES.items():
        assert attrs["suitability_review"] == "not_reviewed", cid
        assert attrs["snow"] == {"value": "unknown", "source": "unknown"}, cid
        assert attrs["rain"]["value"] == "unknown", cid
        for key in ("outer_type", "outer_length"):
            assert set(attrs[key]) == {"value", "source"}, (cid, key)


def test_only_owner_policy_rules_are_attached():
    ruled = {cid: a["temperature_rule"] for cid, a in ATTRIBUTES.items() if a["temperature_rule"]}
    short_puffer = {
        "male-winter-casual-daily", "male-winter-business_casual-trend", "male-winter-business_formal-trend",
        "female-winter-casual-daily", "female-winter-business_casual-trend"}
    fleece = {"pending-female-winter-casual-fleece", "pending-male-winter-casual-fleece"}
    # #188 winter set (2026-10-20): long padding < 0, shearling < 5 (new owner rule), quilted >= 5.
    long_puffer = {"pending-male-winter-casual-longpadding", "pending-male-winter-business_formal-longpadding",
                   "pending-female-winter-casual-longpadding"}
    shearling = {"pending-female-winter-casual-shearling", "pending-male-winter-casual-shearling"}
    quilted = {"pending-female-winter-business_casual-quilted"}
    assert set(ruled) == short_puffer | fleece | long_puffer | shearling | quilted
    expected_rule = {**{c: policy_rule("puffer", "short") for c in short_puffer},
                     **{c: policy_rule("fleece", None) for c in fleece},
                     **{c: policy_rule("puffer", "long") for c in long_puffer},
                     **{c: policy_rule("shearling", None) for c in shearling},
                     **{c: policy_rule("quilted", None) for c in quilted}}
    for candidate_id, rule in ruled.items():
        assert rule["source"] == ("owner_policy_2026-10-20" if candidate_id in shearling else "owner_policy_2026-10-15")
        assert rule == expected_rule[candidate_id]
    assert policy_rule("puffer", "long")["max_exclusive"] == 0
    assert policy_rule("shearling", None)["max_exclusive"] == 5
    # Coats, blazers, etc. have no confirmed rule: that is "unknown", not "allowed".
    assert ATTRIBUTES["male-winter-casual-trend"]["temperature_rule"] is None
    for coat in ("pending-male-winter-business_casual-turtleneck", "pending-male-winter-business_casual-halfzip",
                 "pending-male-winter-business_formal-coat-derby", "pending-female-winter-business_formal-knit",
                 "pending-female-winter-casual-coat-dress"):
        assert ATTRIBUTES[coat]["outer_type"]["value"] == "coat", coat
        assert ATTRIBUTES[coat]["temperature_rule"] is None, coat


def test_puffer_lengths_come_from_observed_drawings_only():
    for cid, attrs in ATTRIBUTES.items():
        if attrs["outer_length"]["value"] in ("short", "long"):
            length = attrs["outer_length"]["value"]
            assert attrs["outer_length"]["source"].startswith("asset_observed_2026-10-")
            assert all(OBSERVED_OUTER_LENGTH.get(d) == length
                       for d, kind in attrs["drawing_outer_types"].items() if kind == attrs["outer_type"]["value"])
    # The only long outers are the three #188 long-padding drawings, observed 2026-10-20.
    long_outer = {cid: a for cid, a in ATTRIBUTES.items() if a["outer_length"]["value"] == "long"}
    assert {cid: a["drawings"] for cid, a in long_outer.items()} == {
        "pending-male-winter-casual-longpadding": ["all-067"],
        "pending-male-winter-business_formal-longpadding": ["all-071"],
        "pending-female-winter-casual-longpadding": ["all-073"]}
    for attrs in long_outer.values():
        assert attrs["outer_type"]["value"] == "puffer"
        assert attrs["outer_length"]["source"] == "asset_observed_2026-10-20"


def test_long_puffer_label_conflict_is_recorded_not_fixed():
    attrs = ATTRIBUTES["male-winter-business_formal-trend"]
    assert attrs["outer_label"] == "비즈니스 롱 패딩"
    assert attrs["outer_length"]["value"] == "short"
    assert "all-023" in attrs["label_conflict"]


def test_branch_that_swaps_the_outer_is_flagged():
    attrs = ATTRIBUTES["female-winter-casual-trend"]
    assert attrs["outer_type"]["value"] == "coat"
    assert attrs["outer_varies_by_branch"] is True
    assert attrs["drawing_outer_types"]["all-055"] == "puffer"


# ---------- independent oracle ----------

def _attrs(kind, length, rule=True):
    return {"outer_slot": "outer", "outer_type": {"value": kind, "source": "test"},
            "outer_length": {"value": length, "source": "test"},
            "temperature_rule": policy_rule(kind, length) if rule else None,
            "snow": {"value": "unknown", "source": "unknown"}}


@pytest.mark.parametrize("kind,length,t,expected", [
    ("puffer", "short", 4.9, cc.ALLOWED), ("puffer", "short", 5.0, cc.BLOCKED), ("puffer", "short", 5.1, cc.BLOCKED),
    ("puffer", "long", -0.1, cc.ALLOWED), ("puffer", "long", 0.0, cc.BLOCKED), ("puffer", "long", 0.1, cc.BLOCKED),
    ("fleece", None, 4.9, cc.BLOCKED), ("fleece", None, 5.0, cc.ALLOWED), ("fleece", None, 5.1, cc.ALLOWED),
    ("quilted", None, 4.9, cc.BLOCKED), ("quilted", None, 5.0, cc.ALLOWED),
])
def test_boundaries(kind, length, t, expected):
    assert cc.temperature_verdict(_attrs(kind, length), t) == expected


def test_unknowns_are_never_allowed():
    assert cc.temperature_verdict(_attrs("coat", "unknown", rule=False), 3) == cc.UNKNOWN
    assert cc.temperature_verdict(_attrs("puffer", "short"), None) == cc.UNKNOWN          # weather failure
    assert cc.temperature_verdict({**_attrs("puffer", "unknown"),
                                   "temperature_rule": policy_rule("puffer", "short")}, 3) == cc.UNKNOWN
    assert cc.snow_verdict(_attrs("coat", "unknown"), True) == cc.UNKNOWN
    assert cc.snow_verdict(_attrs("coat", "unknown"), None) == cc.UNKNOWN
    assert cc.snow_verdict(_attrs("coat", "unknown"), False) == cc.NOT_APPLICABLE


def test_legacy_cold_band_violations_are_reproduced_exactly():
    # Known failure of today's live output (puffers on 5–11°C days). Kept visible, not excepted.
    assert cc.legacy_cold_band_violations(8.0) == cc.KNOWN_LEGACY_VIOLATIONS
    # Below 5°C the same looks satisfy the confirmed rule.
    assert cc.legacy_cold_band_violations(4.9) == set()


# ---------- live pipeline -> real matcher ----------

@pytest.fixture(scope="module")
def live_report():
    if shutil.which("node") is None:
        if os.environ.get("CI"):
            pytest.fail("node is missing in CI: the live matcher check must not be skipped")
        pytest.skip("node is required (installed in CI)")
    from fashion_v2.live_match_check import check
    return check()


def test_live_looks_all_match_a_drawing(live_report):
    assert live_report["looks"] > 0
    assert live_report["checked"] == live_report["looks"]
    assert live_report["unmatched"] == []
    print(f"live matcher check: {live_report['checked']} looks checked")  # visible with -rA / -s


def _two_rows():
    # Validation runs before any row is read, so two placeholder rows are enough.
    return [{"candidate_id": "x", "tpo": "casual", "run": {}, "review_preference": None, "look": {}}] * 2


@pytest.mark.parametrize("reply,message", [
    (["all-018"], "1 results for 2 looks"),                      # short reply would drop a look
    (["all-018", "all-018", "all-018"], "3 results for 2 looks"),  # long reply
    ({"0": "all-018"}, "expected list"),
    ([7, None], "expected str or null"),
    (["no-such-drawing", None], "unknown drawing"),
])
def test_matcher_reply_is_validated_before_pairing(reply, message):
    from fashion_v2.live_match_check import MatcherResponseError, check
    with pytest.raises(MatcherResponseError, match=message):
        check(rows=_two_rows(), matcher=lambda rows: reply)


def test_returned_drawing_geometry_agrees_in_python(live_report):
    assert live_report["geometry_mismatch"] == []


def test_every_active_candidate_and_live_branch_is_exercised(live_report):
    assert set(live_report["pairs"]) == {
        c["candidate_id"] for c in active_candidates() if c["source"] != "selector_candidate"}
    assert live_report["conditional_files"] == {"10"}
    assert live_report["review_preferences"] == {
        "young-summer-yellow-purple", "teen-winter-blue-pink",
        "fifties-winter-red-blue", "fifties-formal-green-purple"}


def test_committed_observed_map_is_not_stale(live_report):
    committed = observed_illustrations()
    for cid, drawings in live_report["pairs"].items():
        known = {d for ids in committed.get(cid, {}).values() for d in ids}
        assert drawings <= known, f"{cid}: new drawings {sorted(drawings - known)} -> rerun coverage script"


# ---------- legacy live builder stays independent ----------

def test_legacy_live_builder_does_not_import_check_modules():
    banned = {"fashion_v2.candidate_registry", "fashion_v2.illustration_assets", "fashion_v2.candidate_attributes",
              "fashion_v2.candidate_constraints", "fashion_v2.live_match_check"}
    for name in ("svg_recommendation.py", "template_catalog.py", "weather_catalog.py", "weather_outfit.py",
                 "review_preferences.py", "wearable_options.py", "realwear_rules.py"):
        tree = ast.parse((ROOT / "fashion_v2" / name).read_text(encoding="utf-8"))
        imported = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        imported |= {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        assert not imported & banned, name
    main_tree = ast.parse((ROOT / "main.py").read_text(encoding="utf-8"))
    main_imports = {n.module for n in ast.walk(main_tree) if isinstance(n, ast.ImportFrom)}
    assert not main_imports & banned
