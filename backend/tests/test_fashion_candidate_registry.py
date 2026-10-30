"""Stage-1 candidate records and illustration integrity (issue #188).

These tests add structure and checks only. They also pin that the live
recommendation path does not read the new registry yet, so outputs are unchanged.
"""
import ast
import json
from pathlib import Path

from fashion_v2 import candidate_registry as reg
from fashion_v2.candidate_activation import activation_problems
from fashion_v2.illustration_assets import (
    CONDITIONAL_VARIANTS, PENDING_FILES, inspect_assets, load_registry, png_size, webp_size, ASSET_DIR)
from fashion_v2.template_catalog import TEMPLATES
from fashion_v2.weather_catalog import WARM_TRANSITION_LOOKS

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / "docs" / "fashion" / "illustration-coverage-baseline.json"


def test_every_existing_template_is_exactly_one_active_candidate():
    active = {c["candidate_id"]: c for c in reg.active_candidates()}
    templates = list(TEMPLATES) + list(WARM_TRANSITION_LOOKS)
    # + the two #188 fleece candidates and the eleven #188 winter-set candidates (selector only).
    assert len(active) == len(templates) + 2 + 11 == 69
    assert set(active) - {t["id"] for t in templates} == {
        c["candidate_id"] for c in reg.active_candidates() if c["source"] == reg.SELECTOR_SOURCE}
    for template in templates:
        record = active[template["id"]]
        assert record["gender"] == template["gender"]
        assert record["tpo"] == template["tpo"]
        assert record["legacy_role"] == template["look_role"]
        assert [c["source_label"] for c in record["components"]] == [i["label"] for i in template["items"]]


FLEECE_IDS = ("pending-female-winter-casual-fleece", "pending-male-winter-casual-fleece")
# #188 winter set (2026-10-20): roles from the owner-approved list.
WINTER_SET_ROLES = {
    "pending-female-winter-casual-shearling": "trendy",
    "pending-male-winter-casual-longpadding": "basic",
    "pending-male-winter-casual-shearling": "trendy",
    "pending-male-winter-business_casual-turtleneck": "trendy",
    "pending-male-winter-business_casual-halfzip": "basic",
    "pending-male-winter-business_formal-longpadding": "trendy",
    "pending-male-winter-business_formal-coat-derby": "basic",
    "pending-female-winter-casual-longpadding": "basic",
    "pending-female-winter-business_formal-knit": "trendy",
    "pending-female-winter-business_casual-quilted": "trendy",
    "pending-female-winter-casual-coat-dress": "trendy",
}
SELECTOR_ROLES = {**{c: "basic" for c in FLEECE_IDS}, **WINTER_SET_ROLES}
SELECTOR_ROLE_BASIS = {**{c: "owner_decision_2026-10-18" for c in FLEECE_IDS},
                       **{c: "owner_scope_2026-10-20" for c in WINTER_SET_ROLES}}


def test_roles_only_carry_over_the_legacy_slot():
    assert {r["candidate_id"] for r in reg.active_candidates() if r["source"] == reg.SELECTOR_SOURCE} == set(
        SELECTOR_ROLES)
    for record in reg.active_candidates():
        if record["source"] == reg.SELECTOR_SOURCE:
            assert record["role"] == record["role_draft"] == SELECTOR_ROLES[record["candidate_id"]]
            assert record["role_basis"] == SELECTOR_ROLE_BASIS[record["candidate_id"]]
        else:
            assert record["role"] == {"daily": "basic", "trend": "trendy"}[record["legacy_role"]]
            assert record["role_basis"] == "legacy_daily_trend_slot"
        assert record["editorial_formula_id"] is None


def test_component_references_are_explicit_but_unmapped():
    for record in reg.active_candidates():
        for component in record["components"]:
            assert component["reference_item_id"] is None
            assert component["applied_color_source"] == "runtime:color_strategy.placements"
            assert "key" not in component  # item-{i} position keys are not identifiers


def test_pending_candidates_stay_inactive_and_point_at_drawn_assets():
    # Records for already registered drawings (stage 1). The #188 fleece pilot records point at
    # stored-only drawings and are checked in test_fashion_pending_assets.py.
    pending = [c for c in reg.CANDIDATES if c["status"] == "review_pending" and c["source"] == "existing_illustration"]
    assert {c["illustration_id"] for c in pending} == {"all-054", "all-055", "all-056"}
    registry_ids = {e["id"] for e in load_registry()}
    for record in pending:
        assert record["role"] is None and record["components"] == []
        assert set(record["activation_blockers"]) >= {"temperature_material_review", "per_colour_qa"}
        assert record["illustration_id"] in registry_ids


def test_registry_is_consistent_with_observed_coverage():
    observed = reg.observed_illustrations()
    registry_ids = {e["id"] for e in load_registry()}
    file_ids = registry_ids | set(CONDITIONAL_VARIANTS) | set(PENDING_FILES)
    assert reg.validate_candidates(observed=observed, registry_ids=registry_ids, file_ids=file_ids) == []


def test_selector_candidate_activation_guard_passes_as_one_unit():
    assert activation_problems() == []


def test_illustration_files_match_registry_and_sizes():
    report = inspect_assets()
    assert report["problems"] == []
    assert report["registry_entries"] == 76  # 65 + all-066..all-076 (#188 winter set)
    assert report["files"] == 77 and report["conditional_files"] == ["10"]


def test_header_size_readers_handle_every_shipped_file():
    for path in ASSET_DIR.glob("*.webp"):
        width, height = webp_size(path)
        assert width > 0 and height > 0
    for path in ASSET_DIR.glob("*-layers.png"):
        width, height = png_size(path)
        assert width > 0 and height > 0


def test_baseline_records_full_live_sample_match():
    summary = json.loads(BASELINE.read_text(encoding="utf-8"))
    live = summary["groups"]["live_sample"]
    assert live["errors"] == 0 and live["unmatched"] == 0
    assert live["recommendations"] == live["matched"] > 0
    assert summary["registry_entries"] == 76


def test_legacy_builder_stays_independent_from_the_selector_registry():
    banned = {"fashion_v2.candidate_registry", "fashion_v2.illustration_assets",
              "fashion_v2.candidate_templates", "fashion_v2.outfit_selector"}
    for path in [ROOT / "fashion_v2" / name for name in (
            "svg_recommendation.py", "template_catalog.py", "weather_catalog.py")]:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
        imported |= {a.name for node in ast.walk(tree) if isinstance(node, ast.Import) for a in node.names}
        assert not imported & banned


def test_coverage_script_pools_match_main():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "fashion_illustration_coverage", ROOT / "scripts" / "fashion_illustration_coverage.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    from fashion_v2 import daily_colors
    assert module.ELEMENT_WEAR_TONES is daily_colors.ELEMENT_WEAR_TONES
    assert module.TONGGUAN_TONE is daily_colors.TONGGUAN_TONE
    equal_pairs = {(a, b) for a, b in module.live_sample_pairs() if a == b}
    assert equal_pairs == {(tone, tone) for tone in daily_colors.TONGGUAN_TONE.values()}
