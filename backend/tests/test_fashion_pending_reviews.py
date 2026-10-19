"""#188 (2026-10-19): review records for stored-only (pending) drawings.

scope_version now works for all-064/all-065 through the same normalised drawing
definition that registered drawings use, so registering them later keeps the hash.
Candidate hashes no longer include `status`, and the role is `role or role_draft`, so
activating a reviewed pending candidate keeps its record. The real records for the two
pending candidates (owner final, 2026-10-19) are checked at the end of this file.
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


def provenance_copy(tmp_path, monkeypatch, mutate):
    data = json.loads(ia.PROVENANCE_FILE.read_text(encoding="utf-8"))
    for entry in data:
        mutate(entry)
    path = tmp_path / "expansion-provenance.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(ia, "PROVENANCE_FILE", path)


# ---------------- pending drawings can be hashed ----------------

@pytest.mark.parametrize("candidate_id,drawing_id", PAIRS)
def test_pending_pairs_get_drawing_and_scope_versions(candidate_id, drawing_id):
    assert len(cr.drawing_version(drawing_id)) == 16
    assert len(cr.scope_version(candidate_id, drawing_id)) == 16
    rec = record(candidate_id, drawing_id)
    assert cr.validate_record(rec) == []
    assert cr.find_review([rec], candidate_id, drawing_id) is rec


@pytest.mark.parametrize("drawing_id", ["all-064", "all-065"])
def test_pending_definition_comes_from_provenance_and_stays_unselectable(drawing_id):
    definition = cr._drawing_definition(drawing_id)
    entry = next(e for e in json.loads(ia.PROVENANCE_FILE.read_text(encoding="utf-8")) if e["id"] == drawing_id)
    assert definition["shape"] == entry["shape"]
    assert definition["slots"] == [s["field"] for s in entry["slots"]]
    assert definition["linkedSuit"] is False
    assert definition["outer_type"] == "fleece"
    # Decided on #188 (2026-10-19) before any real record, so the hash no longer moves for it.
    assert definition["outer_length"] == "short"
    assert definition["temperature_rule"]["min_inclusive"] == 5 and "max_exclusive" not in definition["temperature_rule"]
    assert drawing_id not in SHAPES  # the selection list never sees pending drawings


EVIDENCE = "https://github.com/ryanchoi13/saju-app/issues/188#issuecomment-6261822732"
APPROVED = {  # values the owner approved on #188 (2026-10-19)
    "all-064": (FEMALE, "f54766ef35fa967b", "dfc81ccffaf3add5"),
    "all-065": (MALE, "b946e4a377875872", "f1b932398b2460a7"),
}


def test_real_review_file_holds_exactly_the_two_approved_records():
    reviews = cr.load_reviews()
    assert sorted(r["drawing_id"] for r in reviews) == ["all-064", "all-065"]
    for r in reviews:
        candidate_id, drawing_version, scope_version = APPROVED[r["drawing_id"]]
        assert cr.validate_record(r) == []
        assert (r["candidate_id"], r["drawing_version"], r["scope_version"]) == (candidate_id, drawing_version, scope_version)
        assert r["temp_range"] == {"min": 7, "max_exclusive": 11}
        assert r["rain"] == r["snow"] == "unsuitable"
        assert r["steps"] == list(cr.REQUIRED_STEPS) and r["evidence"] == EVIDENCE
        assert cr.find_review(reviews, candidate_id, r["drawing_id"]) is r  # still current, not stale
        assert [t for t in (6.9, 7, 10.9, 11) if cr.in_reviewed_range(r, t)] == [7, 10.9]


def test_records_do_not_activate_the_candidates():
    from fashion_v2 import outfit_selector as sel
    for candidate_id, _, _ in APPROVED.values():
        record = next(c for c in candidate_registry.CANDIDATES if c["candidate_id"] == candidate_id)
        assert record["status"] == "review_pending" and candidate_id not in sel._ROLE_OF


# ---------------- ownership ----------------

@pytest.mark.parametrize("candidate_id,drawing_id", [
    (MALE, "all-064"), (FEMALE, "all-065"), ("male-winter-casual-daily", "all-065")])
def test_pending_drawing_only_with_its_owner(candidate_id, drawing_id):
    with pytest.raises(ValueError, match="belongs to"):
        cr.scope_version(candidate_id, drawing_id)
    assert cr.find_review([], candidate_id, drawing_id) is None


def test_owner_must_also_point_at_the_drawing(monkeypatch):
    rec = record(MALE, "all-065")
    swap_candidate(monkeypatch, MALE, lambda c: c.update(illustration_id="all-061"))
    with pytest.raises(ValueError, match="belongs to"):
        cr.scope_version(MALE, "all-065")
    assert cr.find_review([rec], MALE, "all-065") is None


def test_unknown_or_unmarked_drawings_are_rejected(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="unknown drawing"):
        cr.scope_version(MALE, "all-999")
    provenance_copy(tmp_path, monkeypatch, lambda e: e.pop("status", None) if e["id"] == "all-065" else None)
    with pytest.raises(ValueError, match="status 'pending'"):
        cr.scope_version(MALE, "all-065")


# ---------------- staleness ----------------

@pytest.mark.parametrize("mutate", [
    lambda c: c["components"][0].update(source_label="플리스 후드 집업"),
    lambda c: c.update(role_draft="trendy"),
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
    lambda e: e["slots"][0].update(field="overOuter.color"),
], ids=["outerOpen", "top", "slot-order", "slot-field"])
def test_provenance_definition_change_makes_record_stale(tmp_path, monkeypatch, mutate):
    rec = record(MALE, "all-065")
    provenance_copy(tmp_path, monkeypatch, lambda e: mutate(e) if e["id"] == "all-065" else None)
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


def test_free_text_and_order_edits_keep_the_record(tmp_path, monkeypatch):
    rec = record(MALE, "all-065")

    def edit_text(e):
        if e["id"] == "all-065":
            e.update(edit_instruction="reworded", pending_reason="reworded", source_url="https://example.invalid/x")
    provenance_copy(tmp_path, monkeypatch, edit_text)
    swap_candidate(monkeypatch, MALE, lambda c: (c.update(known_issues=["note"], plan_id="renamed"),
                                                 c["components"].reverse()))
    assert cr.find_review([rec], MALE, "all-065") is rec


# ---------------- lifecycle and registration keep the hash ----------------

@pytest.mark.parametrize("candidate_id,drawing_id", PAIRS)
def test_activation_keeps_the_record_but_role_change_does_not(monkeypatch, candidate_id, drawing_id):
    rec = record(candidate_id, drawing_id)
    swap_candidate(monkeypatch, candidate_id, lambda c: c.update(status="active", role="basic"))
    assert cr.find_review([rec], candidate_id, drawing_id) is rec
    swap_candidate(monkeypatch, candidate_id, lambda c: c.update(status="active", role="trendy"))
    assert cr.find_review([rec], candidate_id, drawing_id) is None


@pytest.mark.parametrize("candidate_id,drawing_id", PAIRS)
def test_registering_with_the_same_definition_keeps_the_hash(monkeypatch, candidate_id, drawing_id):
    before = cr.scope_version(candidate_id, drawing_id)
    pending = ia.drawing_definition(drawing_id)
    registered = ia.load_registry() + [{"id": drawing_id, "shape": pending["shape"], "slots": pending["slots"],
                                        "linkedSuit": False}]
    monkeypatch.setattr(ia, "load_registry", lambda path=ia.REGISTRY_FILE: registered)
    monkeypatch.delitem(ia.PENDING_FILES, drawing_id)
    assert ia.drawing_definition(drawing_id) == pending
    assert cr.scope_version(candidate_id, drawing_id) == before


def test_registered_and_pending_at_once_is_an_error(monkeypatch):
    pending = ia.drawing_definition("all-065")
    registered = ia.load_registry() + [{"id": "all-065", **{k: pending[k] for k in ("shape", "slots", "linkedSuit")}}]
    monkeypatch.setattr(ia, "load_registry", lambda path=ia.REGISTRY_FILE: registered)
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
