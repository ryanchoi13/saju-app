"""Non-production rotation study for issue #188 (evidence only; not used by the app).

All weather is SYNTHETIC. Pools other than `current` are HYPOTHETICAL: the art-NNN
drawings do not exist. Temperature windows marked ASSUMPTION are study inputs, not
owner policy. Role labels come from the ChatGPT editorial draft and are not proven
by this study; the study only shows how many alternatives each role label leaves.

    python scripts/fashion_rotation_study.py            # writes docs/fashion/rotation-study.json
    python scripts/fashion_rotation_study.py --check    # fails if the output would change
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "fashion" / "rotation-study.json"
INF = float("inf")

# ---------------------------------------------------------------- pools
POLICY = {"short_puffer": (-INF, 5), "long_puffer": (-INF, 0), "fleece": (5, 11), "quilted": (5, 11)}
ASSUMED = {"coat": (-INF, 11), "shearling": (-INF, 11), "trench": (-INF, 11), "tweed_jacket": (-INF, 11)}
# fleece/quilted lower bound is owner policy; their upper bound 11 is an ASSUMPTION, as are all of ASSUMED.


def cand(cid, gender, tpo, role, composition, outer, drawn):
    """Three identities kept apart (issue #188 review):
    - id: the candidate.
    - composition: colour-free outfit composition. For drawn candidates this is the
      rendered geometry family (denim/cotton variants chosen by colour scoring count as
      one composition); for unbuilt art-NNN it is a PROXY written from the planned row,
      because no geometry exists yet.
    - editorial_formula: the reviewed style formula. Unassigned (None) for every candidate.
    Avoidance windows, repeat metrics and distinct counts all use `composition`."""
    lo, hi = POLICY.get(outer) or ASSUMED[outer]
    return dict(id=cid, gender=gender, tpo=tpo, role=role, composition=composition, editorial_formula=None,
                outer=outer, tmin=lo, tmax=hi, drawn=drawn, snow="unknown")


CURRENT = [
    cand("male-winter-casual-daily", "male", "casual", "basic", "puffer+hoodie+cotton+sneaker", "short_puffer", True),
    cand("male-winter-casual-trend", "male", "casual", "trendy", "coat+knit+denim|cotton+boots", "coat", True),
    cand("male-winter-business_casual-daily", "male", "business_casual", "basic", "coat+knit+slacks+derby", "coat", True),
    cand("male-winter-business_casual-trend", "male", "business_casual", "trendy", "cardigan+puffer+shirt+slacks+loafer", "short_puffer", True),
    cand("male-winter-business_formal-daily", "male", "business_formal", "basic", "suit+coat+shirt+tie+oxford", "coat", True),
    cand("male-winter-business_formal-trend", "male", "business_formal", "trendy", "suit+puffer+shirt+tie+derby", "short_puffer", True),
    cand("female-winter-casual-daily", "female", "casual", "basic", "puffer+knit+cotton+sneaker", "short_puffer", True),
    cand("female-winter-casual-trend", "female", "casual", "trendy", "coat+knit+cotton+ankleboot", "coat", True),
    cand("female-winter-business_casual-daily", "female", "business_casual", "basic", "coat+knit+slacks+loafer", "coat", True),
    cand("female-winter-business_casual-trend", "female", "business_casual", "trendy", "cardigan+puffer+knit+cotton+ankleboot", "short_puffer", True),
    cand("female-winter-business_formal-daily", "female", "business_formal", "basic", "suit+coat+shirt+pumps+bag", "coat", True),
    cand("female-winter-business_formal-trend", "female", "business_formal", "trendy", "suit+coat+shirt+loafer+bag", "coat", True),
]
ART_V1 = [  # ChatGPT draft 2026-10-17 07:52Z; role None = held
    cand("art-001", "male", "casual", "basic", "fleece+shirt_out+cotton+sneaker", "fleece", False),
    cand("art-002", "male", "casual", "basic", "longpuffer+hoodie+cotton+sneaker", "long_puffer", False),
    cand("art-003", "male", "casual", "trendy", "shearling+knit+denim+boots", "shearling", False),
    cand("art-004", "male", "business_casual", "basic", "coat+halfzip+slacks+loafer", "coat", False),
    cand("art-005", "male", "business_casual", "trendy", "blazer+coat+turtleneck+slacks+oxford", "coat", False),
    cand("art-007", "male", "business_formal", "basic", "suit+longpuffer+shirt+tie+derby", "long_puffer", False),
    cand("art-039", "male", "business_formal", None, "suit+coat+shirt+tie+oxford", "coat", False),
    cand("art-016", "female", "casual", "trendy", "shearling+knit+denim+ankleboot", "shearling", False),
    cand("art-017", "female", "casual", "basic", "fleece+longtee+denim+sneaker", "fleece", False),
    cand("art-018", "female", "casual", "basic", "longpuffer+knit+cotton+sneaker", "long_puffer", False),
    cand("art-T01", "female", "casual", "trendy", "coat+knitdress+tights+ankleboot+bag", "coat", False),
    cand("art-020", "female", "business_casual", "basic", "quilted+knit+slacks+ankleboot", "quilted", False),
    cand("art-021", "female", "business_formal", "basic", "suit+coat+knit+loafer+bag", "coat", False),
]
# ChatGPT 08:21Z: art-005 redefined as a basic variant (suit+coat+turtleneck), not trendy.
ART_V2 = [dict(a, role="basic", composition="suit+coat+turtleneck+oxford") if a["id"] == "art-005" else a for a in ART_V1]
# Comparison candidates named by ChatGPT 08:21Z (winter suitability UNVERIFIED -> ASSUMED window).
COMPARE = [
    cand("art-015", "male", "business_formal", "trendy", "suit+trench+shirt+tie+oxford", "trench", False),
    cand("art-026", "female", "business_casual", "trendy", "tweed_jacket+knit+slacks+loafer", "tweed_jacket", False),
]
POOLS = {"current": CURRENT, "planned_v1": CURRENT + ART_V1, "planned_v2": CURRENT + ART_V2,
         "planned_v2_compare": CURRENT + ART_V2 + COMPARE}

GENDERS, TPOS, AGES = ("male", "female"), ("casual", "business_casual", "business_formal"), (28, 42, 58)
BANDS = (("<0", -3.0), ("0–5", 3.0), ("5–11", 8.0))


# ---------------------------------------------------------------- filters
def fits(c, w):
    t = w.get("temp")
    if t is None or not (c["tmin"] <= t < c["tmax"]):
        return False
    if w.get("snow") and c["snow"] == "unknown":
        return False
    return True


def options(pool, gender, tpo, role, w):
    return [c for c in pool if c["gender"] == gender and c["tpo"] == tpo and c["role"] == role and fits(c, w)]


def count_table(pool):
    rows = []
    for g, t in itertools.product(GENDERS, TPOS):
        for band, temp in BANDS:
            w = {"temp": temp}
            nb = len({c["composition"] for c in options(pool, g, t, "basic", w)})
            nt = len({c["composition"] for c in options(pool, g, t, "trendy", w)})
            rows.append(dict(gender=g, tpo=t, band=band, basic=nb, trendy=nt,
                             status=("role_gap" if not nb or not nt else
                                     "both_rotate" if nb > 1 and nt > 1 else
                                     "one_rotates" if nb > 1 or nt > 1 else "single")))
    return rows


def summarise_counts(rows):
    by_band = defaultdict(Counter)
    for r in rows:
        by_band[r["band"]][r["status"]] += 1
        by_band[r["band"]]["empty_role_slots"] += (r["basic"] == 0) + (r["trendy"] == 0)
    total = Counter()
    for c in by_band.values():
        total.update(c)
    return {"cells_per_band": len(GENDERS) * len(TPOS), "role_slots_per_band": 2 * len(GENDERS) * len(TPOS),
            "by_band": {b: dict(c) for b, c in by_band.items()}, "all_18_cells": dict(total)}


# ---------------------------------------------------------------- selector
def seed(*parts):
    return int(hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:12], 16)


def role_penalty(mode, c, role, history, n):
    """Lower is better. history = previous recommendation days (newest last), this user/TPO.
    n = distinct compositions available for this role today; window = min(2, n-1)."""
    if mode == "none":
        return (0, 0, 0)
    window = min(2, n - 1)
    recent = [d[role]["composition"] for d in history[-window:] if d.get(role)] if window > 0 else []
    composition = int(c["composition"] in recent)
    if mode == "composition":
        return (composition, 0, 0)
    # editorial_formula is unassigned for all candidates, so no formula layer is applied here.
    outer = int(bool(history) and bool(history[-1].get(role)) and history[-1][role]["outer"] == c["outer"])
    last_seen = next((i for i, d in enumerate(reversed(history))
                      if d.get(role) and d[role]["composition"] == c["composition"]), len(history))
    return (composition, outer, -last_seen)   # least recently shown composition wins ties


ROLES = ("basic", "trendy")


def choose(pool, user, tpo, w, day, history, mode, keep=None):
    """keep = {role: candidate} that must stay (only the violated role is re-chosen).

    A kept role is never dropped: if no partner with a different composition exists,
    the kept role is returned alone and the other role is reported missing."""
    g = user["gender"]
    keep = keep or {}
    opts = {r: ([keep[r]] if r in keep else options(pool, g, tpo, r, w)) for r in ROLES}
    n = {r: len({c["composition"] for c in opts[r]}) for r in ROLES}
    notes = [f"no_alternative_{r}" for r in ROLES if n[r] == 1 and r not in keep]
    pairs = [(b, t) for b in opts["basic"] for t in opts["trendy"] if b["composition"] != t["composition"]]
    if pairs:
        def score(p):
            pb = role_penalty(mode, p[0], "basic", history, n["basic"])
            pt = role_penalty(mode, p[1], "trendy", history, n["trendy"])
            return (tuple(a + b for a, b in zip(pb, pt)), seed(user["id"], day, tpo, p[0]["id"], p[1]["id"]))
        best = min(pairs, key=score)
        relaxed = [k for k, v in zip(("composition", "outer"), score(best)[0][:2]) if v and mode == "hierarchical"]
        return dict(basic=best[0], trendy=best[1], shortage=None, relaxed=relaxed, notes=notes)
    if keep:
        kept = next(iter(keep))
        missing = "trendy" if kept == "basic" else "basic"
        return dict(**{kept: keep[kept], missing: None}, shortage=f"{missing}_missing", relaxed=[], notes=notes)
    for r in ROLES:
        if opts[r]:
            pick = min(opts[r], key=lambda c: (role_penalty(mode, c, r, history, n[r]), seed(user["id"], day, tpo, c["id"])))
            missing = "trendy" if r == "basic" else "basic"
            return dict(**{r: pick, missing: None}, shortage=f"{missing}_missing", relaxed=[], notes=notes)
    return dict(basic=None, trendy=None, shortage="no_candidate", relaxed=[], notes=notes)


def run(pool, visits, mode):
    users = [dict(id=f"{g}-{a}", gender=g, age=a) for g in GENDERS for a in AGES]
    out = []
    for user, tpo in itertools.product(users, TPOS):
        store, history = {}, []
        for v in visits:
            key = (v["date"], v.get("region", "A"))
            w = v["weather"]
            stored = store.get(key)
            changed = False
            if stored is None:
                res = choose(pool, user, tpo, w, v["date"], history, mode)
            else:
                bad = [r for r in ("basic", "trendy") if stored[r] and not fits(stored[r], w)]
                if not bad:
                    res = stored
                else:
                    keep = {r: stored[r] for r in ("basic", "trendy") if stored[r] and r not in bad}
                    res = choose(pool, user, tpo, w, v["date"], history, mode, keep=keep)
                    changed = True
            store[key] = res
            if history and history[-1]["date"] == v["date"]:
                history[-1].update(basic=res["basic"], trendy=res["trendy"])
            else:
                history.append(dict(date=v["date"], basic=res["basic"], trendy=res["trendy"]))
            out.append(dict(user=user["id"], tpo=tpo, date=v["date"], label=v.get("label", ""), changed=changed,
                            **{r: res[r] and res[r]["id"] for r in ("basic", "trendy")},
                            **{r + "_outer": res[r] and res[r]["outer"] for r in ("basic", "trendy")},
                            **{r + "_composition": res[r] and res[r]["composition"] for r in ("basic", "trendy")},
                            shortage=res["shortage"], relaxed=res["relaxed"], notes=res["notes"],
                            violation=any(res[r] and not fits(res[r], w) for r in ("basic", "trendy"))))
    return out


def metrics(rows):
    final = {}
    for r in rows:  # last state of each user/TPO/date
        final[(r["user"], r["tpo"], r["date"])] = r
    seqs = defaultdict(list)
    for (u, t, d), r in sorted(final.items()):
        seqs[(u, t)].append(r)
    m = Counter(pair_requests=len(final))
    streaks = []
    for seq in seqs.values():
        for role in ("basic", "trendy"):
            run_len, prev = 0, None
            for i, r in enumerate(seq):
                if not r[role]:
                    run_len, prev = 0, None
                    continue
                m["role_slots"] += 1
                if i > 0 and seq[i - 1][role]:
                    m["slots_with_previous_day"] += 1
                    m["same_composition_as_previous_day"] += r[role + "_composition"] == seq[i - 1][role + "_composition"]
                    m["same_outer_as_previous_day"] += r[role + "_outer"] == seq[i - 1][role + "_outer"]
                run_len = run_len + 1 if r[role + "_composition"] == prev else 1
                prev = r[role + "_composition"]
                streaks.append(run_len)
    for r in final.values():
        m["violations"] += r["violation"]
        m["same_composition_pair"] += bool(r["basic"] and r["trendy"] and r["basic_composition"] == r["trendy_composition"])
        m["basic_missing"] += r["shortage"] == "basic_missing"
        m["trendy_missing"] += r["shortage"] == "trendy_missing"
        m["one_role_missing"] += r["shortage"] in ("basic_missing", "trendy_missing")
        m["no_candidate"] += r["shortage"] == "no_candidate"
        m["no_alternative_notes"] += len(r["notes"])
        for k in r["relaxed"]:
            m["relaxed_" + k] += 1
    m["revisit_changed"] = sum(r["changed"] for r in rows)
    out = dict(m)
    out["longest_same_composition_streak_days"] = max(streaks) if streaks else 0
    swp = m["slots_with_previous_day"]
    out["same_composition_rate_excl_first_day"] = round(m["same_composition_as_previous_day"] / swp, 3) if swp else None
    out["same_composition_rate_incl_first_day"] = round(m["same_composition_as_previous_day"] / m["role_slots"], 3) if m["role_slots"] else None
    out["same_outer_rate_excl_first_day"] = round(m["same_outer_as_previous_day"] / swp, 3) if swp else None
    return out


def days(temps, **flags):
    return [dict(date=f"2026-12-{i + 1:02d}", weather={"temp": t, **{k: True for k, v in flags.items() if i in v}})
            for i, t in enumerate(temps)]


SCENARIOS = {
    "same_3C_7d": days([3.0] * 7),
    "same_8C_7d": days([8.0] * 7),
    "flip_4.9_5.1": days([4.9, 5.1] * 3 + [4.9]),
    "flip_-0.1_0.1": days([-0.1, 0.1] * 3 + [-0.1]),
    "rain2_snow2": days([3.0] * 7, rain={2, 3}, snow={4, 5}),
    "revisit_same_day": [
        dict(date="2026-12-01", weather={"temp": 3.0}, label="first"),
        dict(date="2026-12-01", weather={"temp": 3.6}, label="minor forecast update"),
        dict(date="2026-12-01", weather={"temp": 6.0}, label="update breaks a hard rule"),
        dict(date="2026-12-02", weather={"temp": 3.0}, label="next day")],
    "kst_rollover": [dict(date="2026-12-01", weather={"temp": 3.0}, label="23:59"),
                     dict(date="2026-12-02", weather={"temp": 3.0}, label="00:00")],
    "region_change": [dict(date="2026-12-01", weather={"temp": 8.0}, label="region A"),
                      dict(date="2026-12-01", weather={"temp": -2.0}, region="B", label="region B")],
    "synthetic_30d": days([round(3 + 7 * math.sin(i / 4.0), 1) for i in range(30)]),
}
MODES = ("none", "composition", "hierarchical")


def build():
    result = {"about": ("SYNTHETIC weather; non-current pools are HYPOTHETICAL; windows for coat/shearling/"
                        "trench/tweed and the 11°C cap on fleece/quilted are ASSUMPTIONS. Denominators: "
                        "pair_requests = users(6) x TPO(3) x days; role_slots = filled basic+trendy slots. "
                        "Repeats, avoidance windows and distinct counts all use the colour-free `composition` "
                        "key (a proxy for unbuilt art-NNN); candidate id and editorial_formula are kept separate. "
                        "NOT tested here: rain suitability (the rain flag is not used by the filter), real "
                        "UTC->KST conversion (dates are given as KST strings), storage atomicity."),
              "users": [f"{g}-{a}" for g in GENDERS for a in AGES], "tpos": list(TPOS),
              "counts": {}, "runs": {}}
    for name, pool in POOLS.items():
        rows = count_table(pool)
        result["counts"][name] = {"cells": rows, "summary": summarise_counts(rows)}
        for mode, (sname, visits) in itertools.product(MODES, SCENARIOS.items()):
            result["runs"][f"{name}|{mode}|{sname}"] = metrics(run(pool, visits, mode))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    text = json.dumps(build(), ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    if parser.parse_args().check:
        same = OUT.exists() and OUT.read_text() == text
        print("rotation study unchanged" if same else "rotation study output differs")
        return 0 if same else 1
    OUT.write_text(text)
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
