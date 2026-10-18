"""Slot-by-slot comparison of the #188 pending drawings with their base drawings.

Writes docs/fashion/pending-assets-check.json. The record is tied to the exact files by
sha256, so the pytest check (which has no image libraries in CI) can confirm the shipped
bytes are the ones that were measured. Needs Pillow, numpy and scipy (local only):

    python scripts/fashion_pending_mask_check.py          # rewrite the record
    python scripts/fashion_pending_mask_check.py --check  # fail if the record is stale

Rules agreed on #188 (2026-10-18): slots that the edit kept must stay within ±3% of the
base pixel count with IoU >= 0.95 (0.90-0.95 = keep for eye review, < 0.90 = reject).
Changed slots are recorded only.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets" / "dalha-illustrations"
RECORD = ROOT / "docs" / "fashion" / "pending-assets-check.json"
PAIRS = {  # pending drawing -> (base drawing, kept slots)
    "all-064": ("all-025", ("bottomColor", "shoeColor")),
    "all-065": ("all-061", ("bottomColor", "shoeColor")),
}
TOLERANCE, IOU_PASS, IOU_REVIEW = 0.03, 0.95, 0.90


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def measure() -> dict:
    import numpy as np
    from PIL import Image

    provenance = {e["id"]: e for e in json.loads((ASSETS / "expansion-provenance.json").read_text(encoding="utf-8"))}

    def slots(i):
        r = np.asarray(Image.open(ASSETS / f"{i}-layers.png").convert("RGB"))[..., 0] % 100  # 100+n = cuff of n
        return r, [s["field"] for s in provenance[i]["slots"]]

    out = {}
    for new, (base, kept) in PAIRS.items():
        (nr, nf), (br, bf) = slots(new), slots(base)
        rows = {}
        for field in sorted(set(nf) | set(bf)):
            n, b = nr == nf.index(field) + 1, br == bf.index(field) + 1
            change = (int(n.sum()) - int(b.sum())) / max(int(b.sum()), 1)
            iou = float((n & b).sum()) / max(float((n | b).sum()), 1.0)
            row = {"kept": field in kept, "base_px": int(b.sum()), "new_px": int(n.sum()),
                   "change": round(change, 4), "iou": round(iou, 4)}
            if field in kept:
                row["verdict"] = ("pass" if abs(change) <= TOLERANCE and iou >= IOU_PASS else
                                  "eye_review" if abs(change) <= TOLERANCE and iou >= IOU_REVIEW else "reject")
            rows[field] = row
        out[new] = {"base": base, "files": {name: sha256(ASSETS / name) for name in (f"{new}.webp", f"{new}-layers.png")},
                    "slots": rows}
    return {"rules": {"kept_change_max": TOLERANCE, "iou_pass": IOU_PASS, "iou_eye_review": IOU_REVIEW},
            "drawings": out}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    record = measure()
    text = json.dumps(record, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if RECORD.read_text(encoding="utf-8") != text:
            print("pending-assets-check.json is stale", file=sys.stderr)
            return 1
        print("pending assets record is current")
        return 0
    RECORD.write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
