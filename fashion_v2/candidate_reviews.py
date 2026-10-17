"""Human review records for outfit candidates (#188 PR-3, non-production).

Flow agreed on #188 (2026-10-17, owner approved): ChatGPT drafts the style/composition
review, Claude checks drawing/attribute/rule consistency, the owner gives the final
yes on an image comparison sheet. Only then is a record added to
`candidate_reviews.json`. The file starts EMPTY: no candidate is reviewed yet.

A record belongs to one candidate + one drawing + one drawing *version* (hash of the
shipped webp and mask). If the drawing file changes, the old record no longer applies.

Temperature composition (what a record may and may not do):
- An owner-policy type rule (short puffer < 5, long puffer < 0, fleece/quilted >= 5)
  is always applied first. A record can only NARROW it, never widen it: if the policy
  blocks, the result is blocked whatever the record says.
- For outers with no policy rule (coat, blazer, ...), the reviewed range is the only
  source of a temperature range. No record -> no range -> not allowed in strict mode.
- Rain / snow: "suitable" must be recorded explicitly; anything else blocks on a rain /
  snow day (decision 3 on #188). Legacy shoe swaps are not a review.
Synthetic study inputs are never written here.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from fashion_v2.illustration_assets import ASSET_DIR

REVIEWS_FILE = Path(__file__).with_name("candidate_reviews.json")
REQUIRED_STEPS = ("chatgpt_style_draft", "claude_consistency_check", "owner_final")
WEATHER_VALUES = ("suitable", "unsuitable", "unknown")


def drawing_version(drawing_id: str) -> str:
    digest = hashlib.sha256()
    for path in (ASSET_DIR / f"{drawing_id}.webp", ASSET_DIR / f"{drawing_id}-layers.png"):
        digest.update(path.read_bytes())
    return digest.hexdigest()[:16]


def load_reviews(path: Path = REVIEWS_FILE) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return list(data["reviews"])


def validate_record(record: dict) -> list[str]:
    problems = []
    for key in ("candidate_id", "drawing_id", "drawing_version", "temp_range", "rain", "snow", "steps", "date"):
        if key not in record:
            problems.append(f"missing {key}")
    if problems:
        return problems
    if set(record["steps"]) != set(REQUIRED_STEPS):
        problems.append("all three review steps are required")
    if record["rain"] not in WEATHER_VALUES or record["snow"] not in WEATHER_VALUES:
        problems.append("rain/snow must be suitable, unsuitable or unknown")
    low, high = record["temp_range"].get("min"), record["temp_range"].get("max_exclusive")
    if low is not None and high is not None and not low < high:
        problems.append("temp_range min must be below max_exclusive")
    return problems


def find_review(reviews, candidate_id: str, drawing_id: str):
    """The valid record for this candidate + drawing + current file version, or None."""
    current = drawing_version(drawing_id)
    for record in reviews:
        if (record.get("candidate_id"), record.get("drawing_id")) != (candidate_id, drawing_id):
            continue
        if record.get("drawing_version") != current or validate_record(record):
            continue
        return record
    return None


def in_reviewed_range(record: dict, apparent_c: float) -> bool:
    low, high = record["temp_range"].get("min"), record["temp_range"].get("max_exclusive")
    return (low is None or apparent_c >= low) and (high is None or apparent_c < high)
