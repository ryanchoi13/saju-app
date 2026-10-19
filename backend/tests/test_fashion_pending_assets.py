"""#188 fleece pilot: stored-only drawings and review-pending candidates.

all-064 (art-017, female) and all-065 (art-001, male) are kept in the repository but are
NOT registered in catalog-data.js, so the client matcher can never pick them, and their
candidates are review_pending, so the selector never reads them in strict or study mode.
Activation needs, in order: owner review record, temperature upper bound, screen
registration (PR-4) and a live template.
"""
import ast
import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from fashion_v2 import candidate_registry as reg
from fashion_v2 import outfit_selector as sel
from fashion_v2.illustration_assets import (
    ASSET_DIR, CONDITIONAL_VARIANTS, PENDING_FILES, inspect_assets, load_registry, png_size, webp_size)
from fashion_v2.svg_recommendation import PALETTE, canonical_name
from fashion_v2.weather_outfit import thermal_band

ROOT = Path(__file__).resolve().parents[2]
PROVENANCE = {e["id"]: e for e in json.loads((ASSET_DIR / "expansion-provenance.json").read_text(encoding="utf-8"))}
RECORD = json.loads((ROOT / "docs" / "fashion" / "pending-assets-check.json").read_text(encoding="utf-8"))
PENDING_IDS = set(PENDING_FILES.values())
BLOCKERS = ["owner_review_record", "temperature_upper_bound_undecided", "catalog_registration", "live_template"]


def _pending_records():
    return [c for c in reg.CANDIDATES if c["candidate_id"] in PENDING_IDS]


def test_pending_drawings_are_stored_but_never_registered():
    registry_ids = {e["id"] for e in load_registry()}
    assert set(PENDING_FILES) == {"all-064", "all-065"}
    assert not set(PENDING_FILES) & registry_ids
    report = inspect_assets()
    assert report["problems"] == []
    assert report["registry_entries"] == 63 and report["files"] == 64
    assert report["pending_files"] == ["all-064", "all-065"]
    for file_id in PENDING_FILES:
        assert webp_size(ASSET_DIR / f"{file_id}.webp") == png_size(ASSET_DIR / f"{file_id}-layers.png") == (768, 768)


def test_client_files_do_not_mention_pending_drawings():
    for name in ("catalog-data.js", "catalog.js", "adapter.js", "renderer.js"):
        text = (ASSET_DIR / name).read_text(encoding="utf-8")
        assert not any(file_id in text for file_id in PENDING_FILES), name


def test_pending_candidates_are_inactive_with_all_four_blockers():
    records = _pending_records()
    assert {c["illustration_id"]: c["candidate_id"] for c in records} == PENDING_FILES
    for record in records:
        assert record["status"] == "review_pending" and record["source"] == "pending_drawing"
        assert record["role"] is None and record["role_draft"] == "basic"
        assert record["activation_blockers"] == BLOCKERS
        expected = ({"outer": "ivory", "top": "white", "bottom": "navy", "shoes": "white"}
                    if record["gender"] == "female" else
                    {"outer": "ivory", "top": "white", "bottom": "charcoal", "shoes": "white"})
        assert {c["slot"]: c["source_color"] for c in record["components"]} == expected
    assert not PENDING_IDS & {c["candidate_id"] for c in reg.active_candidates()}


def test_pending_candidate_cannot_be_active():
    changed = deepcopy(list(reg.CANDIDATES))
    for c in changed:
        if c["candidate_id"] == "pending-male-winter-casual-fleece":
            c.update(status="active", role="basic")
    problems = reg.validate_candidates(changed)
    assert "pending-male-winter-casual-fleece: active candidate points at pending drawing all-065" in problems


def test_pending_drawing_belongs_to_one_candidate():
    changed = deepcopy(list(reg.CANDIDATES))
    for c in changed:
        if c["candidate_id"] == "pending-female-winter-casual-fleece":
            c["illustration_id"] = "all-065"
    assert any("belongs to pending-male-winter-casual-fleece" in p for p in reg.validate_candidates(changed))


@pytest.mark.parametrize("file_id", sorted(PENDING_FILES))
def test_components_canonicalise_to_the_drawn_shape(file_id):
    record = next(c for c in _pending_records() if c["illustration_id"] == file_id)
    shape = PROVENANCE[file_id]["shape"]
    field = {"outer": "outer", "top": "top", "bottom": "bottom", "shoes": "shoe"}
    for component in record["components"]:
        item = {"category": component["slot"], "label": component["source_label"]}
        assert canonical_name(item, record["gender"], record["tpo"]) == shape[field[component["slot"]]]
    assert shape["gender"] == record["gender"] and shape["outerMode"] == "wear" and shape["outerOpen"] is True
    assert shape["outer"] == "플리스" and shape["tuck"] == "out"


def test_provenance_marks_pending_and_records_originals():
    for file_id in PENDING_FILES:
        entry = PROVENANCE[file_id]
        assert entry["status"] == "pending"
        assert len(entry["original_sha256"]) == 64 and entry["job_id"] and entry["superseded_job_id"]
    assert PROVENANCE["all-065"]["edit_reference_job_id"] == PROVENANCE["all-064"]["job_id"]
    assert all(e.get("status") is None for k, e in PROVENANCE.items() if k not in PENDING_FILES)


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


def test_selector_never_offers_pending_candidates_or_drawings():
    assert not PENDING_IDS & set(sel._ROLE_OF)
    colors = tuple({"hex": PALETTE[k]["hex"], "name": k, "name_ko": PALETTE[k]["name"]} for k in ("navy", "beige"))
    seen = set()
    for gender in ("male", "female"):
        for tpo in ("casual", "business_casual", "business_formal"):
            for t in (-3.0, 3.0, 7.0, 10.0):
                for mode in ("strict", "study"):
                    result = sel.select({"id": "user_pending", "gender": gender, "age": 40}, tpo, "2026-12-01",
                                        colors, _weather(t), calendar_season="winter", mode=mode)
                    for role in sel.ROLES:
                        if result.get(role):
                            seen.add((result[role]["candidate_id"], result[role].get("drawing_id")))
    assert seen, "the sweep must exercise the selector"
    assert not {c for c, _ in seen} & PENDING_IDS
    assert not {d for _, d in seen} & set(PENDING_FILES)


def test_observed_and_live_matches_never_use_pending_drawings():
    observed = reg.observed_illustrations()
    used = {i for groups in observed.values() for ids in groups.values() for i in ids}
    assert not used & set(PENDING_FILES)
    assert not set(observed) & PENDING_IDS
    assert CONDITIONAL_VARIANTS.keys().isdisjoint(PENDING_FILES)


# ---------------- 2026-10-19: length and materials decided on #188 ----------------

MATERIALS = {
    "pending-female-winter-casual-fleece": [("outer", "fleece"), ("top", "cotton"), ("bottom", "denim"), ("shoes", "suede_mesh")],
    "pending-male-winter-casual-fleece": [("outer", "fleece"), ("top", "cotton"), ("bottom", "cotton"), ("shoes", "suede_mesh")],
}


def test_pending_materials_are_decided_from_the_live_vocabulary():
    from fashion_v2.template_catalog import TEMPLATES
    from fashion_v2.weather_catalog import WARM_TRANSITION_LOOKS
    live = {i["material"] for t in list(TEMPLATES) + list(WARM_TRANSITION_LOOKS) for i in t["items"]}
    for record in _pending_records():
        got = [(c["slot"], c["material"]) for c in record["components"]]
        assert got == MATERIALS[record["candidate_id"]]
        assert {m for _, m in got} <= live  # no new vocabulary


def test_pending_drawings_are_short_and_say_when_that_was_observed():
    from fashion_v2.candidate_attributes import OBSERVED_OUTER_LENGTH, observed_length_source
    from fashion_v2.candidate_reviews import _drawing_definition
    for file_id in PENDING_FILES:
        assert OBSERVED_OUTER_LENGTH[file_id] == "short"
        assert observed_length_source(file_id) == "asset_observed_2026-10-19"
        assert _drawing_definition(file_id)["outer_length"] == "short"
    assert observed_length_source("all-018") == "asset_observed_2026-10-17"  # older entries unchanged

