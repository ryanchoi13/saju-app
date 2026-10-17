"""Human review records for outfit candidates (#188 PR-3, non-production).

Flow agreed on #188 (2026-10-17, owner approved): ChatGPT drafts the style/composition
review, Claude checks drawing/attribute/rule consistency, the owner gives the final
yes on an image comparison sheet. Only then is a record added to
`candidate_reviews.json`. The file starts EMPTY: no candidate is reviewed yet.

What a record is bound to (any change makes the record stale; it is never inherited):
- drawing_version: hash of the shipped webp + mask files.
- scope_version:   hash of the reviewed *definition*: the candidate's material fields
  (gender, TPO, scope, role, form, components) and the drawing's registered geometry,
  colour slots and outer attributes. Free-text fields (notes, known_issues, role_basis)
  and component order are excluded, so editing a description does not invalidate.

Temperature range in a record:
- Both `min` and `max_exclusive` must be present. Each is a finite number, or the
  string "open" meaning "explicitly reviewed: no bound on this side". Missing, None or
  {} is NOT a review. At least one side must be a number (an all-open range is not a
  reviewed range).
- An owner-policy type rule (short puffer < 5, long puffer < 0, fleece/quilted >= 5) is
  applied first; a record can only narrow it, never widen it.
- For outers with no policy rule (coat, blazer, ...) the reviewed range is the only
  source of a temperature range.
Rain / snow: "suitable" must be recorded explicitly; anything else blocks on a rain /
snow day. Legacy shoe swaps are not a review.

Step names and `evidence` are checked for presence only. They are not proof of
approval: the approval itself lives in the linked evidence (e.g. the #188 comment where
the owner confirmed). Synthetic study inputs are never written here.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from fashion_v2.illustration_assets import ASSET_DIR, load_registry

REVIEWS_FILE = Path(__file__).with_name("candidate_reviews.json")
REQUIRED_STEPS = ("chatgpt_style_draft", "claude_consistency_check", "owner_final")
WEATHER_VALUES = ("suitable", "unsuitable", "unknown")
OPEN = "open"
REQUIRED_KEYS = ("candidate_id", "drawing_id", "drawing_version", "scope_version", "temp_range",
                 "rain", "snow", "steps", "evidence", "date")
MATERIAL_COMPONENT_KEYS = ("slot", "source_label", "source_color", "material", "wear_mode", "suit_group")


def _hash(value) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]


def drawing_version(drawing_id: str) -> str:
    digest = hashlib.sha256()
    for path in (ASSET_DIR / f"{drawing_id}.webp", ASSET_DIR / f"{drawing_id}-layers.png"):
        digest.update(path.read_bytes())
    return digest.hexdigest()[:16]


def _candidate_definition(candidate_id: str) -> dict:
    from fashion_v2.candidate_registry import CANDIDATES
    cand = next((c for c in CANDIDATES if c["candidate_id"] == candidate_id), None)
    if cand is None:
        raise ValueError(f"unknown candidate {candidate_id!r}")
    components = sorted(({k: comp.get(k) for k in MATERIAL_COMPONENT_KEYS} for comp in cand["components"]),
                        key=lambda c: json.dumps(c, ensure_ascii=False, sort_keys=True))
    return {k: cand.get(k) for k in ("candidate_id", "status", "gender", "tpo", "scope", "role", "form")} | {
        "components": components}


def _drawing_definition(drawing_id: str) -> dict:
    from fashion_v2.illustration_resolver import drawing_attributes
    base = "06" if drawing_id == "10" else drawing_id
    entry = next((e for e in load_registry() if e["id"] == base), None)
    if entry is None:
        raise ValueError(f"unknown drawing {drawing_id!r}")
    attrs = drawing_attributes(drawing_id)
    return {"id": drawing_id, "shape": entry["shape"], "slots": entry["slots"],
            "linkedSuit": entry.get("linkedSuit"), "outer_type": attrs["outer_type"]["value"],
            "outer_length": attrs["outer_length"]["value"], "temperature_rule": attrs["temperature_rule"]}


def scope_version(candidate_id: str, drawing_id: str) -> str:
    return _hash({"candidate": _candidate_definition(candidate_id), "drawing": _drawing_definition(drawing_id)})


def load_reviews(path: Path = REVIEWS_FILE) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return list(data["reviews"])


def reviews_fingerprint(reviews) -> str:
    return _hash(sorted((json.dumps(r, ensure_ascii=False, sort_keys=True) for r in reviews)))


def _bound(value):
    """Return (ok, number_or_None_for_open)."""
    if value == OPEN:
        return True, None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        return False, None
    return True, float(value)


def validate_record(record) -> list[str]:
    if not isinstance(record, dict):
        return ["record must be an object"]
    problems = [f"missing {k}" for k in REQUIRED_KEYS if k not in record]
    if problems:
        return problems
    if not isinstance(record["steps"], list) or set(record["steps"]) != set(REQUIRED_STEPS):
        problems.append("all three review steps are required")
    if not isinstance(record["evidence"], str) or not record["evidence"].strip():
        problems.append("evidence (e.g. the approval comment URL) is required")
    if record["rain"] not in WEATHER_VALUES or record["snow"] not in WEATHER_VALUES:
        problems.append("rain/snow must be suitable, unsuitable or unknown")
    temp = record["temp_range"]
    if not isinstance(temp, dict) or set(temp) != {"min", "max_exclusive"}:
        problems.append("temp_range needs exactly min and max_exclusive (number or 'open')")
        return problems
    ok_low, low = _bound(temp["min"])
    ok_high, high = _bound(temp["max_exclusive"])
    if not ok_low or not ok_high:
        problems.append("temp_range bounds must be finite numbers or 'open'")
    elif low is None and high is None:
        problems.append("temp_range cannot be open on both sides")
    elif low is not None and high is not None and not low < high:
        problems.append("temp_range min must be below max_exclusive")
    return problems


def find_review(reviews, candidate_id: str, drawing_id: str):
    """The valid record for this candidate + drawing + current file and definition, or None."""
    file_version = drawing_version(drawing_id)
    definition = scope_version(candidate_id, drawing_id)
    for record in reviews:
        if not isinstance(record, dict):
            continue
        if (record.get("candidate_id"), record.get("drawing_id")) != (candidate_id, drawing_id):
            continue
        if record.get("drawing_version") != file_version or record.get("scope_version") != definition:
            continue
        if validate_record(record):
            continue
        return record
    return None


def in_reviewed_range(record: dict, apparent_c: float) -> bool:
    _, low = _bound(record["temp_range"]["min"])
    _, high = _bound(record["temp_range"]["max_exclusive"])
    return (low is None or apparent_c >= low) and (high is None or apparent_c < high)
