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
    assert len(active) == len(templates) + 2 == 58
    for template in templates:
        record = active[template["id"]]
        assert record["gender"] == template["gender"]
        assert record["tpo"] == template["tpo"]
        assert record["legacy_role"] == template["look_role"]
        assert [c["source_label"] for c in record["components"]] == [i["label"] for i in template["items"]]


def test_roles_only_carry_over_the_legacy_slot():
    for record in reg.active_candidates():
        if record["source"] == reg.SELECTOR_SOURCE:
            assert record["role"] == record["role_draft"] == "basic"
            assert record["role_basis"] == "owner_decision_2026-10-18"
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
    assert report["registry_entries"] == 65
    assert report["files"] == 66 and report["conditional_files"] == ["10"]


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
    assert summary["registry_entries"] == 65


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
    import main
    spec = importlib.util.spec_from_file_location(
        "fashion_illustration_coverage", ROOT / "scripts" / "fashion_illustration_coverage.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.ELEMENT_WEAR_TONES == main._ELEMENT_WEAR_TONES
    assert module.TONGGUAN_TONE == main._TONGGUAN_TONE
    equal_pairs = {(a, b) for a, b in module.live_sample_pairs() if a == b}
    assert equal_pairs == {(tone, tone) for tone in main._TONGGUAN_TONE.values()}
