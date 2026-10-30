"""#188 (2026-10-19): review records for the two selector-only fleece drawings.

all-064/all-065 moved from stored-only provenance into the normalised registry in
PR-4A without changing their drawing or scope hashes.
Candidate hashes no longer include `status`, and the role is `role or role_draft`, so
activating a reviewed candidate keeps its record. The two real records were
re-approved on #188 (2026-10-19) after 4A-0 added explicit base colours; the obsolete
pre-colour records remain available through Git history rather than the runtime input file.
"""
import json
import shutil
from copy import deepcopy
from pathlib import Path

import pytest

from fashion_v2 import candidate_registry
from fashion_v2 import candidate_reviews as cr
from fashion_v2 import illustration_assets as ia
from fashion_v2.illustration_resolver import SHAPES

ROOT = Path(__file__).resolve().parents[2]
FEMALE, MALE = "pending-female-winter-casual-fleece", "pending-male-winter-casual-fleece"
PAIRS = ((FEMALE, "all-064"), (MALE, "all-065"))


def record(candidate_id, drawing_id):
    """In-memory only. Never written to candidate_reviews.json."""
    return {"candidate_id": candidate_id, "drawing_id": drawing_id,
            "drawing_version": cr.drawing_version(drawing_id),
            "scope_version": cr.scope_version(candidate_id, drawing_id),
            "temp_range": {"min": 5, "max_exclusive": "open"}, "rain": "unknown", "snow": "unknown",
            "steps": list(cr.REQUIRED_STEPS), "evidence": "test fixture (not a real approval)", "date": "2026-10-19"}


def swap_candidate(monkeypatch, candidate_id, mutate):
    changed = deepcopy(list(candidate_registry.CANDIDATES))
    for c in changed:
        if c["candidate_id"] == candidate_id:
            mutate(c)
    monkeypatch.setattr(candidate_registry, "CANDIDATES", tuple(changed))


def registry_copy(monkeypatch, mutate):
    data = deepcopy(ia.load_registry())
    for entry in data:
        mutate(entry)
    monkeypatch.setattr(ia, "load_registry", lambda path=ia.REGISTRY_FILE: data)


# ---------------- registered selector drawings can be hashed ----------------

@pytest.mark.parametrize("candidate_id,drawing_id", PAIRS)
def test_selector_pairs_get_drawing_and_scope_versions(candidate_id, drawing_id):
    assert len(cr.drawing_version(drawing_id)) == 16
    assert len(cr.scope_version(candidate_id, drawing_id)) == 16
    rec = record(candidate_id, drawing_id)
    assert cr.validate_record(rec) == []
    assert cr.find_review([rec], candidate_id, drawing_id) is rec


@pytest.mark.parametrize("drawing_id", ["all-064", "all-065"])
def test_selector_definition_comes_from_the_registry_and_is_selectable(drawing_id):
    definition = cr._drawing_definition(drawing_id)
    entry = next(e for e in ia.load_registry() if e["id"] == drawing_id)
    assert definition["shape"] == entry["shape"]
    assert definition["slots"] == entry["slots"]
    assert definition["linkedSuit"] is False
    assert definition["outer_type"] == "fleece"
    # Decided on #188 (2026-10-19) before any real record, so the hash no longer moves for it.
    assert definition["outer_length"] == "short"
    assert definition["temperature_rule"]["min_inclusive"] == 5 and "max_exclusive" not in definition["temperature_rule"]
    assert SHAPES[drawing_id] == entry["shape"]


EVIDENCE = "https://github.com/ryanchoi13/saju-app/issues/188#issuecomment-6264128137"
APPROVED = {  # base-colour values the owner re-approved on #188 (2026-10-19)
    "all-064": (FEMALE, "f54766ef35fa967b", "803aec9d2824144e"),
    "all-065": (MALE, "b946e4a377875872", "74a2889f271ca2b7"),
}


# #188 winter set, owner-approved 2026-10-20 with the independent-review step set.
# Evidence: the #188 comment recording the owner's chat approval and the independent review.
WINTER_EVIDENCE = "https://github.com/ryanchoi13/saju-app/issues/188#issuecomment-6287640226"
WINTER_STEPS = ["independent_style_review", "claude_consistency_check", "owner_final"]
# 2026-10-20 23:24 owner: loafers (all-070) and pumps (all-074) avoid snow; rain unchanged.
SNOW_CHANGED = {"all-070", "all-074"}
SNOW_EVIDENCE = "https://github.com/ryanchoi13/saju-app/issues/188#issuecomment-6293149718"
WINTER_APPROVED = {  # drawing -> (candidate, drawing_version, scope_version, temp_range, rain/snow)
    "all-066": ("pending-female-winter-casual-shearling", "0da5d658911bc4d3", "b5c3dfd3394dbae7",
                {"min": "open", "max_exclusive": 5}, "unsuitable"),
    "all-067": ("pending-male-winter-casual-longpadding", "0409ce025ab18202", "7c35330a1a6a73cb",
                {"min": "open", "max_exclusive": 0}, "suitable"),
    "all-068": ("pending-male-winter-casual-shearling", "420d52c006a5bad2", "26cc3b75fbe74d89",
                {"min": "open", "max_exclusive": 5}, "unsuitable"),
    "all-069": ("pending-male-winter-business_casual-turtleneck", "8c152ea5af752ef8", "dbdc8f198259d9d9",
                {"min": "open", "max_exclusive": 9}, "suitable"),
    "all-070": ("pending-male-winter-business_casual-halfzip", "5b39ce7a73113bbd", "4b4e4e4363f6e6f7",
                {"min": "open", "max_exclusive": 9}, "suitable"),
    "all-071": ("pending-male-winter-business_formal-longpadding", "40c6ff27db373597", "23dee15b74cc3e2a",
                {"min": "open", "max_exclusive": 0}, "suitable"),
    "all-072": ("pending-male-winter-business_formal-coat-derby", "76c82957b735c0e3", "5be7dff4ddc63650",
                {"min": "open", "max_exclusive": 9}, "suitable"),
    "all-073": ("pending-female-winter-casual-longpadding", "b5f0e03e1b11cc32", "10116d61f200b18b",
                {"min": "open", "max_exclusive": 0}, "suitable"),
    "all-074": ("pending-female-winter-business_formal-knit", "9025149262235b76", "b47b03c6a103e996",
                {"min": "open", "max_exclusive": 9}, "suitable"),
    "all-075": ("pending-female-winter-business_casual-quilted", "4b1234a748d1e2c0", "bcc7d1f4e6e9de95",
                {"min": 5, "max_exclusive": 11}, "unsuitable"),
    "all-076": ("pending-female-winter-casual-coat-dress", "5eee99effa8ab560", "8c7392a71f787939",
                {"min": "open", "max_exclusive": 9}, "unsuitable"),
}


def test_real_review_file_holds_exactly_the_current_approved_records():
    reviews = cr.load_reviews()
    assert sorted(r["drawing_id"] for r in reviews) == sorted(set(APPROVED) | set(WINTER_APPROVED))
    assert len(reviews) == 13
    for r in reviews:
        assert cr.validate_record(r) == []
        if r["drawing_id"] in APPROVED:
            candidate_id, drawing_version, scope_version = APPROVED[r["drawing_id"]]
            assert r["temp_range"] == {"min": 7, "max_exclusive": 11}
            assert r["rain"] == r["snow"] == "unsuitable"
            assert r["steps"] == list(cr.REQUIRED_STEPS) and r["evidence"] == EVIDENCE
            assert r["date"] == "2026-10-19"
            assert [t for t in (6.9, 7, 10.9, 11) if cr.in_reviewed_range(r, t)] == [7, 10.9]
        else:
            candidate_id, drawing_version, scope_version, temp_range, weather = WINTER_APPROVED[r["drawing_id"]]
            assert r["temp_range"] == temp_range
            if r["drawing_id"] in SNOW_CHANGED:
                assert (r["rain"], r["snow"]) == (weather, "unsuitable")
                assert r["steps"] == WINTER_STEPS and r["evidence"] == SNOW_EVIDENCE
            else:
                assert r["rain"] == r["snow"] == weather
                assert r["steps"] == WINTER_STEPS and r["evidence"] == WINTER_EVIDENCE
            assert r["date"] == "2026-10-20"
        assert (r["candidate_id"], r["drawing_version"], r["scope_version"]) == (candidate_id, drawing_version, scope_version)
        assert cr.scope_version(candidate_id, r["drawing_id"]) == scope_version
        assert cr.drawing_version(r["drawing_id"]) == drawing_version
        assert cr.find_review(reviews, candidate_id, r["drawing_id"]) is r


def test_records_are_current_for_active_selector_candidates_only():
    from fashion_v2 import outfit_selector as sel
    for candidate_id in [v[0] for v in APPROVED.values()] + [v[0] for v in WINTER_APPROVED.values()]:
        record = next(c for c in candidate_registry.CANDIDATES if c["candidate_id"] == candidate_id)
        assert record["status"] == "active" and record["source"] == candidate_registry.SELECTOR_SOURCE
        assert candidate_id in sel._ROLE_OF


# ---------------- ownership ----------------

@pytest.mark.parametrize("candidate_id,drawing_id", [
    (MALE, "all-064"), (FEMALE, "all-065"), ("male-winter-casual-daily", "all-064")])
def test_direct_drawing_only_with_its_owner(candidate_id, drawing_id):
    with pytest.raises(ValueError, match="belongs to"):
        cr.scope_version(candidate_id, drawing_id)
    assert cr.find_review([], candidate_id, drawing_id) is None


def test_owner_must_also_point_at_the_drawing(monkeypatch):
    rec = record(MALE, "all-065")
    swap_candidate(monkeypatch, MALE, lambda c: c.update(illustration_id="all-061"))
    with pytest.raises(ValueError, match="belongs to"):
        cr.scope_version(MALE, "all-065")
    assert cr.find_review([rec], MALE, "all-065") is None


def test_unknown_drawings_are_rejected():
    with pytest.raises(ValueError, match="unknown drawing"):
        cr.scope_version(MALE, "all-999")


# ---------------- staleness ----------------

@pytest.mark.parametrize("mutate", [
    lambda c: c["components"][0].update(source_label="플리스 후드 집업"),
    lambda c: c.update(role="trendy"),
    lambda c: c.update(gender="female"),
], ids=["component", "role", "gender"])
def test_candidate_definition_change_makes_record_stale(monkeypatch, mutate):
    rec = record(MALE, "all-065")
    swap_candidate(monkeypatch, MALE, mutate)
    assert cr.find_review([rec], MALE, "all-065") is None


@pytest.mark.parametrize("mutate", [
    lambda e: e["shape"].update(outerOpen=False),
    lambda e: e["shape"].update(top="맨투맨"),
    lambda e: e["slots"].reverse(),
    lambda e: e["slots"].__setitem__(0, "overOuter.color"),
], ids=["outerOpen", "top", "slot-order", "slot-field"])
def test_registry_definition_change_makes_record_stale(monkeypatch, mutate):
    rec = record(MALE, "all-065")
    registry_copy(monkeypatch, lambda e: mutate(e) if e["id"] == "all-065" else None)
    assert cr.find_review([rec], MALE, "all-065") is None


@pytest.mark.parametrize("suffix", [".webp", "-layers.png"])
def test_drawing_or_mask_bytes_change_makes_record_stale(tmp_path, monkeypatch, suffix):
    rec = record(FEMALE, "all-064")
    for name in ("all-064.webp", "all-064-layers.png"):
        shutil.copy(ia.ASSET_DIR / name, tmp_path / name)
    target = tmp_path / f"all-064{suffix}"
    target.write_bytes(target.read_bytes() + b"\0")
    monkeypatch.setattr(cr, "ASSET_DIR", tmp_path)
    assert cr.find_review([rec], FEMALE, "all-064") is None


def test_free_text_and_component_order_edits_keep_the_record(monkeypatch):
    rec = record(MALE, "all-065")
    swap_candidate(monkeypatch, MALE, lambda c: (c.update(known_issues=["note"], plan_id="renamed"),
                                                 c["components"].reverse()))
    assert cr.find_review([rec], MALE, "all-065") is rec


# ---------------- lifecycle keeps the registered hash ----------------

@pytest.mark.parametrize("candidate_id,drawing_id", PAIRS)
def test_activation_keeps_the_record_but_role_change_does_not(monkeypatch, candidate_id, drawing_id):
    rec = record(candidate_id, drawing_id)
    swap_candidate(monkeypatch, candidate_id, lambda c: c.update(status="active", role="basic"))
    assert cr.find_review([rec], candidate_id, drawing_id) is rec
    swap_candidate(monkeypatch, candidate_id, lambda c: c.update(status="active", role="trendy"))
    assert cr.find_review([rec], candidate_id, drawing_id) is None


@pytest.mark.parametrize("candidate_id,drawing_id", PAIRS)
def test_registered_selector_hashes_are_the_pinned_approved_values(candidate_id, drawing_id):
    _, drawing_hash, scope_hash = APPROVED[drawing_id]
    assert cr.drawing_version(drawing_id) == drawing_hash
    assert cr.scope_version(candidate_id, drawing_id) == scope_hash


def test_registered_and_pending_at_once_is_an_error(monkeypatch):
    monkeypatch.setitem(ia.PENDING_FILES, "all-065", MALE)
    with pytest.raises(ValueError, match="both registered and pending"):
        ia.drawing_definition("all-065")


# ---------------- registered drawings are unchanged ----------------

def test_registered_drawing_definitions_match_the_registry():
    for entry in ia.load_registry():
        definition = cr._drawing_definition(entry["id"])
        assert {k: definition[k] for k in ("shape", "slots", "linkedSuit")} == {
            "shape": entry["shape"], "slots": entry["slots"], "linkedSuit": entry.get("linkedSuit")}
    assert cr._drawing_definition("10")["shape"] == cr._drawing_definition("06")["shape"]


def test_candidate_hash_ignores_status_only():
    for c in candidate_registry.CANDIDATES:
        definition = cr._candidate_definition(c["candidate_id"])
        assert "status" not in definition
        assert definition["role"] == (c.get("role") or c.get("role_draft"))
