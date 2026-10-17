"""Fast live-pipeline check: current builder -> real catalog.js matcher (#188 PR-2).

Unlike the committed coverage baseline (a JSON snapshot), this runs the *current*
code every time: `build_svg_catalog_contexts` builds looks for a small fixed
manifest that touches the live branches, and Node runs the real client matcher
(`assets/dalha-illustrations/catalog.js`). Python then re-checks each returned
drawing's registered shape against the look geometry on its own.

The manifest is bounded (hundreds of builds, ~20 s). It is not exhaustive: one
input per branch does not prove every input. The full sweep stays in
scripts/fashion_illustration_coverage.py.

Run directly for a summary:  python -m fashion_v2.live_match_check
"""
from __future__ import annotations

import itertools
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from fashion_v2.illustration_assets import CONDITIONAL_VARIANTS, load_registry
from fashion_v2.svg_recommendation import PALETTE, build_svg_catalog_contexts
from fashion_v2.weather_outfit import THERMAL_BANDS, thermal_band

ROOT = Path(__file__).resolve().parents[1]
MATCHER = ROOT / "scripts" / "fashion_illustration_coverage.mjs"

BAND_TEMPERATURE = {key: (lower + 1 if lower != float("-inf") else -3) for lower, key, _ in THERMAL_BANDS}
CALENDAR_SEASON = {"very_hot": "summer", "hot": "summer", "warm": "summer", "mild": "spring",
                   "cool": "autumn", "chilly": "autumn", "cold": "winter", "freezing": "winter"}
WARM_BANDS = {"very_hot", "hot", "warm"}

# Branches exercised (each one is a reason the manifest exists):
LIVE_PAIRS = (("navy", "olive"), ("beige", "burgundy"), ("light_gray", "denim"))  # general colour paths
LIVE_AGES = (28, 58)                                                                # 58 -> conditional file '10'
# review_preferences.py fixtures: (pair, age that enters the branch)
FIXTURES = ((("yellow", "purple"), 25), (("cobalt", "pink"), 15), (("red", "sky"), 55), (("forest", "purple"), 55))
GEOMETRY_KEYS = ("gender", "top", "bottom", "dress", "outer", "shoe", "bag", "outerMode", "tuck", "knitNeck")


def _profile(band, rainy, carry):
    info = thermal_band(BAND_TEMPERATURE[band])
    return dict(thermal_band=info["key"], thermal_label=info["label"],
                daytime_apparent_high=BAND_TEMPERATURE[band], evening_apparent_low=BAND_TEMPERATURE[band] - 6,
                carry_light_outer=carry, rainy=rainy, guidance="", base_layer=info["base_layer"],
                catalog_season_hint=info["catalog_season_hint"], avoid_suede=rainy,
                outerwear="carry_light" if carry else info["outerwear"])


def manifest():
    runs = []
    for band in BAND_TEMPERATURE:
        for rainy, carry in itertools.product((False, True), (False, True) if band in WARM_BANDS else (False,)):
            for gender in ("male", "female"):
                for pair, age in [(p, a) for p in LIVE_PAIRS for a in LIVE_AGES] + list(FIXTURES):
                    runs.append(dict(band=band, rainy=rainy, carry=carry, gender=gender, age=age, pair=pair))
    return runs


def _colour(key):
    return {"hex": PALETTE[key]["hex"], "name": key, "name_ko": PALETTE[key]["name"]}


def build_rows():
    rows = []
    for run in manifest():
        contexts = build_svg_catalog_contexts(
            run["gender"], CALENDAR_SEASON[run["band"]], _colour(run["pair"][0]), _colour(run["pair"][1]),
            weather_profile=_profile(run["band"], run["rainy"], run["carry"]), age=run["age"])
        for tpo, payload in contexts.items():
            for look in payload["looks"]:
                rows.append({"run": run, "tpo": tpo, "candidate_id": look["id"],
                             "review_preference": look.get("review_preference"),
                             "look": {"renderer": look["renderer"], "age": look.get("age"),
                                      "garment_spec": look["garment_spec"],
                                      "items": [{"label": i["label"], "color_parts": i.get("color_parts")}
                                                for i in look["items"]]}})
    return rows


def match(rows):
    node = shutil.which("node")
    if node is None:
        raise RuntimeError("node is required for the live matcher check")
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / "rows.json"
        source.write_text(json.dumps(rows, ensure_ascii=False))
        done = subprocess.run([node, "--no-warnings", str(MATCHER), str(source)],
                              check=True, capture_output=True, text=True)
    return json.loads(done.stdout)


def geometry_agrees(spec: dict, shape: dict) -> bool:
    """Python re-check of the matcher's exact-geometry rule (independent of JS)."""
    if any((spec.get(k) or "") != (shape.get(k) or "") for k in GEOMETRY_KEYS):
        return False
    if (spec.get("outerOpen") is not False) != (shape.get("outerOpen") is not False):
        return False
    if ((spec.get("overOuter") or {}).get("name") or "") != ((shape.get("overOuter") or {}).get("name") or ""):
        return False
    return list(spec.get("accessories") or []) == list(shape.get("accessories") or [])


def check():
    rows = build_rows()
    hits = match(rows)
    shapes = {e["id"]: e["shape"] for e in load_registry()}
    for file_id, variant in CONDITIONAL_VARIANTS.items():
        shapes[file_id] = shapes[variant["base"]]
    report = {"looks": len(rows), "unmatched": [], "geometry_mismatch": [], "pairs": {},
              "review_preferences": set(), "conditional_files": set()}
    for row, hit in zip(rows, hits):
        if row["review_preference"]:
            report["review_preferences"].add(row["review_preference"])
        if not hit:
            report["unmatched"].append({k: row[k] for k in ("candidate_id", "tpo")} | {"run": row["run"]})
            continue
        if hit in CONDITIONAL_VARIANTS:
            report["conditional_files"].add(hit)
        if not geometry_agrees(row["look"]["garment_spec"], shapes[hit]):
            report["geometry_mismatch"].append({"candidate_id": row["candidate_id"], "drawing": hit})
        report["pairs"].setdefault(row["candidate_id"], set()).add(hit)
    return report


if __name__ == "__main__":
    import time
    started = time.time()
    result = check()
    print(json.dumps({"looks": result["looks"], "unmatched": len(result["unmatched"]),
                      "geometry_mismatch": len(result["geometry_mismatch"]),
                      "candidates": len(result["pairs"]),
                      "review_preferences": sorted(result["review_preferences"]),
                      "conditional_files": sorted(result["conditional_files"]),
                      "seconds": round(time.time() - started, 1)}, ensure_ascii=False))
