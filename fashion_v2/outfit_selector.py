"""Daily two-look selector (#188 PR-3/PR-4B).

Picks one basic and one trendy look for a user / TPO / day from the existing
candidates. The legacy builder remains the fallback; the guarded live bridge may
replace its two looks after durable selection succeeds.

Order of checks for every candidate (each failure is recorded with a reason):
  1. scope        - the candidate is what the legacy weather catalogue would offer for
                    this weather (reuses weather_templates_for / templates_for, so no new
                    temperature windows are invented for coats etc.).
  2. render       - the real pipeline renders it (select_template -> review preferences ->
                    apply_colors) and the server resolver finds the drawing; else no_drawing.
  3. temperature  - owner-policy rule on the DRAWN outer (resolver attributes). Blocked
                    stays blocked in every mode.
  4. weather      - rain/snow True needs an explicit "suitable" review; None (forecast
                    unavailable) blocks with weather_unknown. Applies in every mode.
  5. review gate  - a current record's reviewed range always applies (including study).
                    strict also requires a record; study may use an unreviewed legacy
                    candidate and tags it unreviewed. Study bypasses ONLY record presence.
Then basic + trendy are chosen as a pair with different compositions (drawing
geometry), repeats are avoided over the last min(2, n-1) days, then the outer type of
yesterday, then least-recently-shown; ties break on a date seed. If no valid pair
exists the kept role (if any) is returned alone and the other role is reported missing.
Conditions are never relaxed to fill two looks.
"""
from __future__ import annotations

import hashlib
from collections import Counter
from copy import deepcopy

from fashion_v2.candidate_constraints import BLOCKED, temperature_verdict
from fashion_v2.candidate_registry import SELECTOR_SOURCE, active_candidates
from fashion_v2.candidate_reviews import find_review, in_reviewed_range
from fashion_v2.candidate_templates import templates_for_selector
from fashion_v2.illustration_resolver import composition_key, drawing_attributes, select_illustration
from fashion_v2.realwear_rules import styling_for
from fashion_v2.review_preferences import apply_review_preferences
from fashion_v2.svg_recommendation import apply_colors, select_template, tone
from fashion_v2.template_catalog import templates_for
from fashion_v2.weather_catalog import weather_templates_for

ROLES = ("basic", "trendy")
ROLE_NUMBER = {"basic": 1, "trendy": 2}
MODES = ("strict", "study")
_ACTIVE = active_candidates()
_ROLE_OF = {c["candidate_id"]: c["role"] for c in _ACTIVE}
_REVIEW_REQUIRED = {c["candidate_id"] for c in _ACTIVE if c["source"] == SELECTOR_SOURCE}


def seed(*parts) -> int:
    return int(hashlib.sha256("|".join(map(str, parts)).encode()).hexdigest()[:12], 16)


def _scope(gender, tpo, weather, calendar_season):
    profile = weather.get("legacy_profile")
    source = (weather_templates_for(gender, tpo, profile, calendar_season=calendar_season) if profile
              else templates_for(gender, calendar_season, tpo))
    result = {t["id"]: t for t in source}
    for template in templates_for_selector(gender, tpo, weather, calendar_season):
        if template["id"] in result:
            raise ValueError(f"duplicate selector template id: {template['id']}")
        result[template["id"]] = template
    return result


def render(template, role, user, colors, weather, calendar_season):
    """Same per-look steps as build_svg_catalog_contexts, without the cross-look `previous`."""
    a, b = colors
    look = apply_review_preferences(
        select_template(deepcopy(template), user.get("age"), ROLE_NUMBER[role], weather.get("legacy_profile")), a, b)
    look["calendar_season"] = calendar_season
    look["styling"] = styling_for(look)
    for i, item in enumerate(look["items"]):
        c = tone(item["base_color"])
        item.update(key=f"item-{i}", color_name=c["name"], hex=c["hex"], color_relation="base")
    return apply_colors(look, a, b, None)


def evaluate(candidate_id, template, role, user, colors, weather, calendar_season, mode, reviews):
    """Return (option or None, reason)."""
    try:
        look = render(template, role, user, colors, weather, calendar_season)
    except ValueError:
        return None, "render_failed"
    drawing = select_illustration(look)
    if drawing is None:
        return None, "no_drawing"
    attrs = drawing_attributes(drawing)
    t = weather.get("apparent_c")
    if t is None:
        return None, "weather_unknown"
    policy = temperature_verdict(attrs, t)
    if policy == BLOCKED:
        return None, "temperature_blocked"
    record = find_review(reviews, candidate_id, drawing)
    for kind in ("rain", "snow"):
        flag = weather.get(kind)
        if flag is None:
            return None, "weather_unknown"
        if flag:
            verdict = record.get(kind) if record else "unknown"
            if verdict != "suitable":
                return None, f"{kind}_{verdict if verdict in ('unknown', 'unsuitable') else 'unknown'}"
    flags = []
    if record is not None and not in_reviewed_range(record, t):
        return None, "outside_reviewed_range"
    if record is None and (mode == "strict" or candidate_id in _REVIEW_REQUIRED):
        return None, "unreviewed"
    if record is None:
        flags.append("unreviewed")
    if policy != "allowed":
        flags.append("temperature_unreviewed")
    look["candidate_id"] = candidate_id
    look["drawing_id"] = drawing
    return {"candidate_id": candidate_id, "role": role, "drawing_id": drawing,
            "composition": composition_key(drawing), "outer_type": attrs["outer_type"]["value"],
            "flags": flags, "items": [{"label": i["label"], "hex": i["hex"]} for i in look["items"]],
            "look": look}, "ok"


def _penalty(option, role, history, n):
    window = min(2, n - 1)
    recent = [d[role]["composition"] for d in history[-window:] if d.get(role)] if window > 0 else []
    composition = int(option["composition"] in recent)
    outer = int(bool(history) and bool(history[-1].get(role)) and history[-1][role]["outer_type"] == option["outer_type"])
    last = next((i for i, d in enumerate(reversed(history))
                 if d.get(role) and d[role]["composition"] == option["composition"]), len(history))
    return (composition, outer, -last)


def select(user, tpo, day, colors, weather, *, calendar_season, history=(), mode="strict",
           reviews=(), keep=None):
    """history: previous days' results for this user/TPO, oldest first (same-day excluded)."""
    if mode not in MODES:
        raise ValueError("mode must be strict or study")
    keep = keep or {}
    history = list(history)
    scope = _scope(user["gender"], tpo, weather, calendar_season)
    options = {r: [] for r in ROLES}
    filtered = {r: Counter() for r in ROLES}
    for cid, template in scope.items():
        role = _ROLE_OF.get(cid)
        if role not in ROLES or role in keep:
            continue
        option, reason = evaluate(cid, template, role, user, colors, weather, calendar_season, mode, reviews)
        if option:
            options[role].append(option)
        else:
            filtered[role][reason] += 1
    for role, kept in keep.items():
        options[role] = [kept]
    n = {r: len({o["composition"] for o in options[r]}) for r in ROLES}
    notes = [f"no_alternative_{r}" for r in ROLES if n[r] == 1 and r not in keep]
    pairs = [(b, t) for b in options["basic"] for t in options["trendy"] if b["composition"] != t["composition"]]
    base = {"day": day, "tpo": tpo, "mode": mode, "notes": notes,
            "filtered": {r: dict(filtered[r]) for r in ROLES}}
    if pairs:
        def score(p):
            pb, pt = _penalty(p[0], "basic", history, n["basic"]), _penalty(p[1], "trendy", history, n["trendy"])
            return tuple(x + y for x, y in zip(pb, pt)), seed(user["id"], day, tpo, p[0]["candidate_id"], p[1]["candidate_id"])
        best = min(pairs, key=score)
        relaxed = [k for k, v in zip(("composition", "outer"), score(best)[0][:2]) if v]
        return {**base, "basic": best[0], "trendy": best[1], "shortage": None, "relaxed": relaxed}
    if keep:
        kept = next(iter(keep))
        missing = "trendy" if kept == "basic" else "basic"
        return {**base, kept: keep[kept], missing: None, "shortage": f"{missing}_missing", "relaxed": []}
    for role in ROLES:
        if options[role]:
            pick = min(options[role], key=lambda o: (_penalty(o, role, history, n[role]),
                                                      seed(user["id"], day, tpo, o["candidate_id"])))
            missing = "trendy" if role == "basic" else "basic"
            return {**base, role: pick, missing: None, "shortage": f"{missing}_missing", "relaxed": []}
    return {**base, "basic": None, "trendy": None, "shortage": "no_candidate", "relaxed": []}


def still_valid(option, weather, reviews, mode) -> bool:
    """Re-check a stored look against a newer forecast (drawing-based, no re-render)."""
    t = weather.get("apparent_c")
    if t is None or weather.get("rain") is None or weather.get("snow") is None:
        return False
    if temperature_verdict(drawing_attributes(option["drawing_id"]), t) == BLOCKED:
        return False
    for kind in ("rain", "snow"):
        if weather.get(kind):
            record = find_review(reviews, option["candidate_id"], option["drawing_id"])
            if not record or record[kind] != "suitable":
                return False
    record = find_review(reviews, option["candidate_id"], option["drawing_id"])
    if record is not None and not in_reviewed_range(record, t):
        return False
    if record is None and (mode == "strict" or option["candidate_id"] in _REVIEW_REQUIRED):
        return False
    return True
