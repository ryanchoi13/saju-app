"""Coverage evidence: does every live recommendation resolve to a drawn illustration?

Read-only. Runs the real recommendation builder (`build_svg_catalog_contexts`) over a
fixed input manifest and asks the real client matcher (`catalog.js` via Node) which
illustration each look would render. Nothing in the live path is changed.

Two input groups are kept separate so their results are never mixed up:
- live_sample: colour pairs drawn from the live element wear-tone pools in main.py,
  plus the five equal-colour pairs that its tongguan override can produce.
- review_fixture: the exact colour pairs used by fashion_v2/review_preferences.py.
  Some of these pairs can no longer occur live (see `live_possible`).

Usage:
    python scripts/fashion_illustration_coverage.py            # writes the outputs below
    python scripts/fashion_illustration_coverage.py --check    # fails if outputs would change

Outputs:
    docs/fashion/illustration-coverage-baseline.json   summary + manifest
    fashion_v2/candidate_illustrations.json            observed candidate -> illustration ids
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import subprocess
import sys
import tempfile
from multiprocessing import Pool
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fashion_v2.svg_recommendation import PALETTE, build_svg_catalog_contexts  # noqa: E402
from fashion_v2.weather_outfit import THERMAL_BANDS, thermal_band  # noqa: E402

# Mirrors main._ELEMENT_WEAR_TONES (kept in sync by a test). Copied so this script
# does not import the whole application.
ELEMENT_WEAR_TONES = {
    "金": ("light_gray", "gray", "mid_gray", "ivory", "white"),
    "水": ("navy", "black", "sky", "denim"),
    "木": ("olive", "sage", "forest", "teal"),
    "火": ("burgundy", "plum", "coral", "rust", "red", "lavender", "pink"),
    "土": ("beige", "camel", "brown", "butter"),
}
TONGGUAN_TONE = {"木": "olive", "水": "navy", "金": "mid_gray", "火": "burgundy", "土": "beige"}
LIVE_TONES = sorted({t for pool in ELEMENT_WEAR_TONES.values() for t in pool})
# Exact pairs from fashion_v2/review_preferences.py.
REVIEW_FIXTURE_PAIRS = (
    ("yellow", "purple"), ("cobalt", "pink"), ("red", "sky"), ("forest", "purple"),
)
GENDERS = ("male", "female")
LIVE_AGES = (28, 42, 58)
FIXTURE_AGES = (15, 25, 55)
# One representative apparent temperature inside each band.
BAND_TEMPERATURE = {key: (lower + 1 if lower != float("-inf") else -3) for lower, key, _ in THERMAL_BANDS}
CALENDAR_SEASON = {"very_hot": "summer", "hot": "summer", "warm": "summer", "mild": "spring",
                   "cool": "autumn", "chilly": "autumn", "cold": "winter", "freezing": "winter"}
WARM_BANDS = {"very_hot", "hot", "warm"}

BASELINE = ROOT / "docs" / "fashion" / "illustration-coverage-baseline.json"
CANDIDATE_MAP = ROOT / "fashion_v2" / "candidate_illustrations.json"
MATCHER = ROOT / "scripts" / "fashion_illustration_coverage.mjs"


def live_sample_pairs():
    """Fixed live sample, including equal pairs created by the tongguan A-colour override."""
    pairs = set()
    for first, second in itertools.product(ELEMENT_WEAR_TONES, repeat=2):
        a_pool, b_pool = ELEMENT_WEAR_TONES[first], ELEMENT_WEAR_TONES[second]
        for day in range(3):
            a = a_pool[day % len(a_pool)]
            b = b_pool[(day * 3 + 1) % len(b_pool)]
            if a == b:
                b = b_pool[(b_pool.index(b) + 1) % len(b_pool)]
            pairs.add((a, b))
    pairs.update((tone, tone) for tone in TONGGUAN_TONE.values())
    return sorted(pairs)


def profile(band, rainy, carry):
    info = thermal_band(BAND_TEMPERATURE[band])
    return dict(
        thermal_band=info["key"], thermal_label=info["label"],
        daytime_apparent_high=BAND_TEMPERATURE[band],
        evening_apparent_low=BAND_TEMPERATURE[band] - 6,
        carry_light_outer=carry, rainy=rainy, guidance="",
        base_layer=info["base_layer"], catalog_season_hint=info["catalog_season_hint"],
        avoid_suede=rainy, outerwear="carry_light" if carry else info["outerwear"])


def manifest():
    return {
        "bands": list(BAND_TEMPERATURE),
        "band_temperature": BAND_TEMPERATURE,
        "rain": [False, True],
        "carry_light_outer_bands": sorted(WARM_BANDS),
        "genders": list(GENDERS),
        "groups": {
            "live_sample": {"ages": list(LIVE_AGES), "pairs": [list(p) for p in live_sample_pairs()]},
            "review_fixture": {"ages": list(FIXTURE_AGES), "pairs": [list(p) for p in REVIEW_FIXTURE_PAIRS]},
        },
    }


def colour(key):
    return {"hex": PALETTE[key]["hex"], "name": key, "name_ko": PALETTE[key]["name"]}


def run_band(band):
    rows = []
    groups = (("live_sample", LIVE_AGES, live_sample_pairs()),
              ("review_fixture", FIXTURE_AGES, REVIEW_FIXTURE_PAIRS))
    carries = (False, True) if band in WARM_BANDS else (False,)
    for group, ages, pairs in groups:
        for rainy, carry, gender, age in itertools.product((False, True), carries, GENDERS, ages):
            weather = profile(band, rainy, carry)
            for a, b in pairs:
                base = dict(group=group, band=band, rainy=rainy, carry=carry,
                            gender=gender, age=age, a=a, b=b)
                try:
                    contexts = build_svg_catalog_contexts(
                        gender, CALENDAR_SEASON[band], colour(a), colour(b),
                        weather_profile=weather, age=age)
                except Exception as error:  # recorded, never hidden
                    rows.append({**base, "error": f"{type(error).__name__}: {error}"})
                    continue
                for tpo, payload in contexts.items():
                    for look in payload["looks"]:
                        rows.append({**base, "tpo": tpo, "number": look["recommendation_number"],
                                     "candidate_id": look["id"],
                                     "review_preference": look.get("review_preference"),
                                     "look": {"renderer": look["renderer"], "age": look.get("age"),
                                              "garment_spec": look["garment_spec"],
                                              "items": [{"label": i["label"],
                                                         "color_parts": i.get("color_parts")}
                                                        for i in look["items"]]}})
    return rows


def collect():
    workers = max(1, min(len(BAND_TEMPERATURE), os.cpu_count() or 1))
    with Pool(workers) as pool:
        chunks = pool.map(run_band, list(BAND_TEMPERATURE))
    return [row for chunk in chunks for row in chunk]


def match(rows):
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / "rows.json"
        source.write_text(json.dumps(rows, ensure_ascii=False))
        done = subprocess.run(["node", "--no-warnings", str(MATCHER), str(source)],
                              check=True, capture_output=True, text=True)
    return json.loads(done.stdout)


def summarise(rows, matched):
    from fashion_v2.illustration_assets import load_registry, CONDITIONAL_VARIANTS
    registry_ids = [entry["id"] for entry in load_registry()]
    live_tones = set(LIVE_TONES)
    groups = {}
    candidate_ids = {}
    for row, hit in zip(rows, matched):
        g = groups.setdefault(row["group"], {"recommendations": 0, "errors": 0, "matched": 0,
                                             "unmatched": 0, "unmatched_samples": [], "ids": set()})
        if "error" in row:
            g["errors"] += 1
            continue
        g["recommendations"] += 1
        if hit:
            g["matched"] += 1
            g["ids"].add(hit)
            candidate_ids.setdefault(row["candidate_id"], {}).setdefault(row["group"], set()).add(hit)
        else:
            g["unmatched"] += 1
            if len(g["unmatched_samples"]) < 10:
                g["unmatched_samples"].append({k: row[k] for k in ("band", "gender", "age", "tpo", "number", "candidate_id", "a", "b")})
    live_ids = groups.get("live_sample", {}).get("ids", set())
    fixture_ids = groups.get("review_fixture", {}).get("ids", set())
    registry = set(registry_ids)
    fixture_live_possible = {f"{a}+{b}": (a in live_tones and b in live_tones) for a, b in REVIEW_FIXTURE_PAIRS}
    summary = {
        "about": "Generated by scripts/fashion_illustration_coverage.py. Counts are observations over the manifest, not a proof for all inputs.",
        "registry_entries": len(registry_ids),
        "conditional_files": {k: v for k, v in CONDITIONAL_VARIANTS.items()},
        "groups": {name: {**{k: v for k, v in g.items() if k != "ids"},
                          "registry_entries_reached": len(g["ids"] & registry),
                          "conditional_files_reached": sorted(g["ids"] - registry)}
                   for name, g in sorted(groups.items())},
        "registry_entries_reached_live_sample": len(live_ids & registry),
        "registry_entries_reached_only_by_review_fixture": sorted((fixture_ids - live_ids) & registry),
        "registry_entries_not_reached": sorted(registry - live_ids - fixture_ids),
        "review_fixture_pairs_live_possible": fixture_live_possible,
        "manifest": manifest(),
    }
    mapping = {cid: {group: sorted(ids) for group, ids in sorted(by_group.items())}
               for cid, by_group in sorted(candidate_ids.items())}
    return summary, mapping


def dump(value):
    return json.dumps(value, ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if committed outputs differ")
    args = parser.parse_args()
    rows = collect()
    summary, mapping = summarise(rows, match(rows))
    outputs = {BASELINE: dump(summary), CANDIDATE_MAP: dump({
        "about": "Observed by scripts/fashion_illustration_coverage.py over its manifest. "
                 "Illustration ids each active candidate actually rendered. Not an editorial claim.",
        "candidates": mapping})}
    if args.check:
        stale = [str(p.relative_to(ROOT)) for p, text in outputs.items()
                 if not p.exists() or p.read_text() != text]
        if stale:
            print("coverage outputs differ: " + ", ".join(stale))
            return 1
        print("coverage outputs unchanged")
        return 0
    for path, text in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    live = summary["groups"]["live_sample"]
    print(f"live_sample: {live['recommendations']} looks, matched {live['matched']}, "
          f"unmatched {live['unmatched']}, errors {live['errors']}")
    print(f"registry {summary['registry_entries']}, reached live {summary['registry_entries_reached_live_sample']}, "
          f"fixture-only {summary['registry_entries_reached_only_by_review_fixture']}, "
          f"not reached {summary['registry_entries_not_reached']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
