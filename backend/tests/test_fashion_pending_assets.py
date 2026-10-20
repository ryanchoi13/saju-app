"""#188 PR-4A: reviewed fleece drawings and selector-only active candidates.

all-064 (art-017, female) and all-065 (art-001, male) are registered for the client
matcher and active in the non-production selector. The production builder remains
isolated, so registering them does not make them reachable from today's live output.
"""
import ast
import hashlib
import itertools
import json
import os
import shutil
from copy import deepcopy
from pathlib import Path

import pytest

from fashion_v2 import candidate_registry as reg
from fashion_v2 import candidate_reviews as reviews_mod
from fashion_v2 import outfit_selector as sel
from fashion_v2.candidate_activation import activation_problems, representative_drawings
from fashion_v2.candidate_templates import template_ids
from fashion_v2.illustration_assets import (
    ASSET_DIR, CONDITIONAL_VARIANTS, PENDING_FILES, inspect_assets, load_registry, png_size, webp_size)
from fashion_v2.illustration_resolver import select_illustration
from fashion_v2.svg_recommendation import PALETTE, canonical_name
from fashion_v2.weather_outfit import thermal_band

ROOT = Path(__file__).resolve().parents[2]
PROVENANCE = {e["id"]: e for e in json.loads((ASSET_DIR / "expansion-provenance.json").read_text(encoding="utf-8"))}
RECORD = json.loads((ROOT / "docs" / "fashion" / "pending-assets-check.json").read_text(encoding="utf-8"))
FLEECE_DRAWINGS = {
    "all-064": "pending-female-winter-casual-fleece",
    "all-065": "pending-male-winter-casual-fleece",
}
FLEECE_IDS = set(FLEECE_DRAWINGS.values())


def _pending_records():
    return [c for c in reg.CANDIDATES if c["candidate_id"] in FLEECE_IDS]


def test_fleece_drawings_are_registered_with_their_existing_files():
    registry_ids = {e["id"] for e in load_registry()}
    assert PENDING_FILES == {}
    assert set(FLEECE_DRAWINGS) <= registry_ids
    report = inspect_assets()
    assert report["problems"] == []
    assert report["registry_entries"] == 65 and report["files"] == 66
    assert report["pending_files"] == []
    for file_id in FLEECE_DRAWINGS:
        assert webp_size(ASSET_DIR / f"{file_id}.webp") == png_size(ASSET_DIR / f"{file_id}-layers.png") == (768, 768)


def test_only_client_registry_names_the_new_drawings():
    registry = (ASSET_DIR / "catalog-data.js").read_text(encoding="utf-8")
    assert all(file_id in registry for file_id in FLEECE_DRAWINGS)
    for name in ("catalog.js", "adapter.js", "renderer.js"):
        text = (ASSET_DIR / name).read_text(encoding="utf-8")
        assert not any(file_id in text for file_id in FLEECE_DRAWINGS), name


def test_fleece_candidates_are_active_only_in_the_selector_registry():
    records = _pending_records()
    assert {c["illustration_id"]: c["candidate_id"] for c in records} == FLEECE_DRAWINGS
    for record in records:
        assert record["status"] == "active" and record["source"] == reg.SELECTOR_SOURCE
        assert record["role"] == record["role_draft"] == "basic"
        assert not record.get("activation_blockers")
        expected = ({"outer": "ivory", "top": "white", "bottom": "navy", "shoes": "white"}
                    if record["gender"] == "female" else
                    {"outer": "ivory", "top": "white", "bottom": "charcoal", "shoes": "white"})
        assert {c["slot"]: c["source_color"] for c in record["components"]} == expected
    assert FLEECE_IDS <= {c["candidate_id"] for c in reg.active_candidates()}
    assert FLEECE_IDS == template_ids()


def test_active_candidate_cannot_keep_a_blocker_or_lose_a_base_colour():
    changed = deepcopy(list(reg.CANDIDATES))
    for c in changed:
        if c["candidate_id"] == "pending-male-winter-casual-fleece":
            c["activation_blockers"] = ["forgotten"]
            c["components"][0]["source_color"] = None
    problems = reg.validate_candidates(changed)
    assert "pending-male-winter-casual-fleece: active candidate still has blockers" in problems
    assert "pending-male-winter-casual-fleece: selector candidate needs base colours" in problems


def test_full_activation_guard_passes_after_every_dependency_is_present():
    assert activation_problems() == []


def _validate_activation(**overrides):
    registry_ids = {e["id"] for e in load_registry()}
    args = {
        "observed": reg.observed_illustrations(),
        "registry_ids": registry_ids,
        "file_ids": registry_ids | set(CONDITIONAL_VARIANTS),
        "reviews": reviews_mod.load_reviews(),
        "template_ids": template_ids(),
        "selector_drawings": representative_drawings(),
    }
    args.update(overrides)
    return reg.validate_candidates(**args)


def test_activation_guard_rejects_missing_or_stale_review():
    missing = _validate_activation(reviews=[])
    assert sum("current owner review required" in p for p in missing) == 2
    stale = deepcopy(reviews_mod.load_reviews())
    stale[0]["scope_version"] = "0" * 16
    assert any(stale[0]["candidate_id"] in p and "current owner review required" in p
               for p in _validate_activation(reviews=stale))


def test_activation_guard_rejects_registration_template_and_render_gaps():
    registry_ids = {e["id"] for e in load_registry()} - {"all-065"}
    assert any("illustration not registered" in p for p in _validate_activation(
        registry_ids=registry_ids, file_ids=registry_ids | set(CONDITIONAL_VARIANTS)))
    assert sum("selector template required" in p for p in _validate_activation(template_ids=set())) == 2
    rendered = representative_drawings() | {"pending-male-winter-casual-fleece": "all-064"}
    assert any("rendered 'all-064', expected 'all-065'" in p
               for p in _validate_activation(selector_drawings=rendered))


def test_activation_guard_rejects_empty_policy_review_intersection():
    reviews = deepcopy(reviews_mod.load_reviews())
    reviews[0]["temp_range"] = {"min": -10, "max_exclusive": 4}
    assert any("review and temperature policy do not overlap" in p
               for p in _validate_activation(reviews=reviews))


@pytest.mark.parametrize("file_id", sorted(FLEECE_DRAWINGS))
def test_components_canonicalise_to_the_drawn_shape(file_id):
    record = next(c for c in _pending_records() if c["illustration_id"] == file_id)
    shape = PROVENANCE[file_id]["shape"]
    field = {"outer": "outer", "top": "top", "bottom": "bottom", "shoes": "shoe"}
    for component in record["components"]:
        item = {"category": component["slot"], "label": component["source_label"]}
        assert canonical_name(item, record["gender"], record["tpo"]) == shape[field[component["slot"]]]
    assert shape["gender"] == record["gender"] and shape["outerMode"] == "wear" and shape["outerOpen"] is True
    assert shape["outer"] == "플리스" and shape["tuck"] == "out"


def test_provenance_keeps_audit_fields_without_pending_status():
    for file_id in FLEECE_DRAWINGS:
        entry = PROVENANCE[file_id]
        assert "status" not in entry and "pending_reason" not in entry
        assert len(entry["original_sha256"]) == 64 and entry["job_id"] and entry["superseded_job_id"]
    assert PROVENANCE["all-065"]["edit_reference_job_id"] == PROVENANCE["all-064"]["job_id"]
    assert all(e.get("status") is None for e in PROVENANCE.values())


def _script_constant(script, name):
    tree = ast.parse((ROOT / "scripts" / script).read_text(encoding="utf-8"))
    return next(ast.literal_eval(n.value) for n in ast.walk(tree)
                if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == name)


def test_mask_post_processing_is_limited_to_all_065():
    assert _script_constant("build_expanded_illustration_masks.py", "SHADOW_FRINGE_NEUTRAL") == ("all-065",)


def test_jeans_drawing_gets_the_rolled_cuff_label():
    cuffs = _script_constant("mark_denim_cuffs.py", "DENIM_CUFFS")
    assert "all-064" in cuffs and "all-065" not in cuffs


def test_measured_record_matches_shipped_bytes_and_passes():
    for file_id, entry in RECORD["drawings"].items():
        for name, digest in entry["files"].items():
            assert hashlib.sha256((ASSET_DIR / name).read_bytes()).hexdigest() == digest, name
        for field, row in entry["slots"].items():
            if row["kept"]:
                assert row["verdict"] == "pass", (file_id, field)
                assert abs(row["change"]) <= 0.03 and row["iou"] >= 0.95


def _weather(t):
    band = thermal_band(t)
    profile = dict(thermal_band=band["key"], thermal_label=band["label"], daytime_apparent_high=t,
                   evening_apparent_low=t - 4, carry_light_outer=False, rainy=False, guidance="",
                   base_layer=band["base_layer"], catalog_season_hint=band["catalog_season_hint"], avoid_suede=False)
    return {"apparent_c": t, "basis": "test_fixed", "rain": False, "snow": False, "legacy_profile": profile}


@pytest.mark.parametrize("mode", ["strict", "study"])
@pytest.mark.parametrize("gender,candidate_id,drawing_id", [
    ("female", "pending-female-winter-casual-fleece", "all-064"),
    ("male", "pending-male-winter-casual-fleece", "all-065"),
])
def test_selector_offers_fleece_only_inside_the_reviewed_range(mode, gender, candidate_id, drawing_id):
    assert FLEECE_IDS <= set(sel._ROLE_OF)
    colors = tuple({"hex": PALETTE[k]["hex"], "name": k, "name_ko": PALETTE[k]["name"]} for k in ("navy", "beige"))
    reviews = reviews_mod.load_reviews()
    for t in (7.0, 10.9):
        result = sel.select({"id": "user_fleece", "gender": gender, "age": 40}, "casual", "2026-12-01",
                            colors, _weather(t), calendar_season="winter", mode=mode, reviews=reviews)
        assert (result["basic"]["candidate_id"], result["basic"]["drawing_id"]) == (candidate_id, drawing_id)
    below = sel.select({"id": "user_fleece", "gender": gender, "age": 40}, "casual", "2026-12-01",
                       colors, _weather(6.9), calendar_season="winter", mode=mode, reviews=reviews)
    assert not below.get("basic") or below["basic"]["candidate_id"] != candidate_id
    upper = sel.select({"id": "user_fleece", "gender": gender, "age": 40}, "casual", "2026-12-01",
                       colors, _weather(11.0), calendar_season="winter", mode=mode, reviews=reviews)
    assert not upper.get("basic") or upper["basic"]["candidate_id"] != candidate_id


@pytest.mark.parametrize("kind", ["rain", "snow"])
def test_reviewed_bad_weather_gets_an_explicit_unsuitable_reason(kind):
    colors = tuple({"hex": PALETTE[k]["hex"], "name": k, "name_ko": PALETTE[k]["name"]} for k in ("navy", "beige"))
    result = sel.select({"id": "user_fleece", "gender": "male", "age": 40}, "casual", "2026-12-01",
                        colors, _weather(8.0) | {kind: True}, calendar_season="winter", mode="strict",
                        reviews=reviews_mod.load_reviews())
    assert result["filtered"]["basic"][f"{kind}_unsuitable"] == 1


def _matcher_row(look):
    return {"look": {"renderer": look["renderer"], "age": look.get("age"),
                     "garment_spec": look["garment_spec"],
                     "items": [{"label": item["label"], "color_parts": item.get("color_parts")}
                               for item in look["items"]]}}


def test_every_ordered_palette_pair_including_equal_colours_resolves_to_the_reviewed_fleece_in_python_and_js():
    if shutil.which("node") is None:
        if os.environ.get("CI"):
            pytest.fail("node is missing in CI: selector matcher parity must not be skipped")
        pytest.skip("node is required (installed in CI)")
    from fashion_v2.live_match_check import match

    keys = tuple(PALETTE)
    assert len(keys) == 29
    rows, expected = [], []
    for gender, age, candidate_id, drawing_id in (
        ("female", 15, "pending-female-winter-casual-fleece", "all-064"),
        ("male", 55, "pending-male-winter-casual-fleece", "all-065"),
    ):
        template = sel._scope(gender, "casual", _weather(8.0), "winter")[candidate_id]
        user = {"id": f"palette-{gender}", "gender": gender, "age": age}
        count = 0
        for a, b in itertools.product(keys, repeat=2):
            colors = tuple({"hex": PALETTE[k]["hex"], "name": k, "name_ko": PALETTE[k]["name"]}
                           for k in (a, b))
            look = sel.render(template, "basic", user, colors, _weather(8.0), "winter")
            assert select_illustration(look) == drawing_id, (gender, a, b)
            rows.append(_matcher_row(look))
            expected.append(drawing_id)
            count += 1
        assert count == 841
    assert match(rows) == expected


def test_observed_and_live_matches_never_use_selector_only_drawings():
    observed = reg.observed_illustrations()
    used = {i for groups in observed.values() for ids in groups.values() for i in ids}
    assert not used & set(FLEECE_DRAWINGS)
    assert not set(observed) & FLEECE_IDS
    assert CONDITIONAL_VARIANTS.keys().isdisjoint(FLEECE_DRAWINGS)


# ---------------- 2026-10-19: length and materials decided on #188 ----------------

MATERIALS = {
    "pending-female-winter-casual-fleece": [("outer", "fleece"), ("top", "cotton"), ("bottom", "denim"), ("shoes", "suede_mesh")],
    "pending-male-winter-casual-fleece": [("outer", "fleece"), ("top", "cotton"), ("bottom", "cotton"), ("shoes", "suede_mesh")],
}


def test_selector_materials_are_decided_from_the_live_vocabulary():
    from fashion_v2.template_catalog import TEMPLATES
    from fashion_v2.weather_catalog import WARM_TRANSITION_LOOKS
    live = {i["material"] for t in list(TEMPLATES) + list(WARM_TRANSITION_LOOKS) for i in t["items"]}
    for record in _pending_records():
        got = [(c["slot"], c["material"]) for c in record["components"]]
        assert got == MATERIALS[record["candidate_id"]]
        assert {m for _, m in got} <= live  # no new vocabulary


def test_selector_drawings_are_short_and_say_when_that_was_observed():
    from fashion_v2.candidate_attributes import OBSERVED_OUTER_LENGTH, observed_length_source
    from fashion_v2.candidate_reviews import _drawing_definition
    for file_id in FLEECE_DRAWINGS:
        assert OBSERVED_OUTER_LENGTH[file_id] == "short"
        assert observed_length_source(file_id) == "asset_observed_2026-10-19"
        assert _drawing_definition(file_id)["outer_length"] == "short"
    assert observed_length_source("all-018") == "asset_observed_2026-10-17"  # older entries unchanged

