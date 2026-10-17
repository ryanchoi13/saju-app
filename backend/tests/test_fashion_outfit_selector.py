"""PR-3 (#188): non-production selector, review gate, drawing resolver and day store."""
import ast
import os
import shutil
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from fashion_v2 import candidate_reviews as cr
from fashion_v2 import outfit_day_store as store_mod
from fashion_v2 import outfit_selector as sel
from fashion_v2.illustration_resolver import drawing_attributes, select_illustration
from fashion_v2.svg_recommendation import PALETTE
from fashion_v2.weather_outfit import thermal_band

ROOT = Path(__file__).resolve().parents[2]
UTC = timezone.utc
USER = {"id": "user_pr3test", "gender": "male", "age": 40}


def col(key):
    return {"hex": PALETTE[key]["hex"], "name": key, "name_ko": PALETTE[key]["name"]}


COLORS = (col("navy"), col("beige"))


def weather(t, rain=False, snow=False):
    band = thermal_band(t)
    profile = dict(thermal_band=band["key"], thermal_label=band["label"], daytime_apparent_high=t,
                   evening_apparent_low=t - 4, carry_light_outer=False, rainy=bool(rain), guidance="",
                   base_layer=band["base_layer"], catalog_season_hint=band["catalog_season_hint"], avoid_suede=bool(rain))
    return {"apparent_c": t, "basis": "test_fixed", "rain": rain, "snow": snow, "legacy_profile": profile}


def review(candidate_id, drawing_id, *, low=None, high=None, rain="unknown", snow="unknown", version=None):
    return {"candidate_id": candidate_id, "drawing_id": drawing_id,
            "drawing_version": version or cr.drawing_version(drawing_id),
            "temp_range": {"min": low, "max_exclusive": high}, "rain": rain, "snow": snow,
            "steps": list(cr.REQUIRED_STEPS), "date": "2026-10-17"}


def pick(tpo="casual", t=3.0, mode="study", reviews=(), user=USER, colors=COLORS, **w):
    return sel.select(user, tpo, "2026-12-01", colors, weather(t, **w), calendar_season="winter",
                      mode=mode, reviews=list(reviews))


# ---------------- resolver ----------------

def test_python_resolver_agrees_with_catalog_js_on_every_manifest_look():
    if shutil.which("node") is None:
        if os.environ.get("CI"):
            pytest.fail("node is missing in CI: resolver parity must not be skipped")
        pytest.skip("node is required (installed in CI)")
    from fashion_v2.live_match_check import rows_and_hits
    rows, hits = rows_and_hits()
    assert len(rows) == len(hits) > 0
    mismatches = [(i, h) for i, (r, h) in enumerate(zip(rows, hits, strict=True)) if select_illustration(r["look"]) != h]
    assert mismatches == []


def test_resolver_rejects_what_the_client_rejects():
    look = sel.render(sel._scope("male", "casual", weather(3.0), "winter")["male-winter-casual-daily"],
                      "basic", USER, COLORS, weather(3.0), "winter")
    assert select_illustration(look) == "all-018"
    assert select_illustration({**look, "renderer": "old"}) is None
    assert select_illustration({**look, "garment_spec": {**look["garment_spec"], "top": "없는 옷"}}) is None
    spec = look["garment_spec"]
    not_hex = {k: "navy" for k in spec if k.endswith("Color")}
    assert select_illustration({**look, "garment_spec": {**spec, **not_hex}}) is None
    extra_parts = {**look, "items": look["items"] + [{"label": "머플러", "color_parts": {"a": 1}}]}
    assert select_illustration(extra_parts) is None


def test_branch_that_draws_a_puffer_is_judged_by_the_drawing():
    # teen-winter-blue-pink turns the trendy coat into a puffer (all-055); base attributes say coat.
    teen = {"id": "user_teen", "gender": "female", "age": 15}
    result = pick("casual", t=8.0, user=teen, colors=(col("cobalt"), col("pink")))
    assert result["trendy"] is None or result["trendy"]["drawing_id"] != "all-055"
    assert result["filtered"]["trendy"].get("temperature_blocked") == 1
    assert drawing_attributes("all-055")["outer_type"]["value"] == "puffer"


# ---------------- review gate ----------------

def test_review_file_starts_empty_and_strict_mode_offers_nothing():
    assert cr.load_reviews() == []
    for tpo in ("casual", "business_casual", "business_formal"):
        result = pick(tpo, mode="strict")
        assert result["shortage"] == "no_candidate"
        assert set(result["filtered"]["basic"]) | set(result["filtered"]["trendy"]) <= {"unreviewed", "temperature_blocked"}


def test_study_mode_only_skips_the_review_gate():
    result = pick("casual", t=3.0, mode="study")
    assert result["basic"] and result["trendy"]
    assert "unreviewed" in result["basic"]["flags"] and "unreviewed" in result["trendy"]["flags"]
    warm = pick("casual", t=8.0, mode="study")     # policy still blocks the short puffer
    assert warm["basic"] is None and warm["filtered"]["basic"] == {"temperature_blocked": 1}


def test_strict_passes_only_a_current_reviewed_drawing():
    trendy = pick("casual", t=3.0, mode="study")["trendy"]
    ok = review(trendy["candidate_id"], trendy["drawing_id"], high=11)
    result = pick("casual", t=3.0, mode="strict", reviews=[ok])
    assert result["trendy"]["drawing_id"] == trendy["drawing_id"] and result["basic"] is None
    assert result["shortage"] == "basic_missing"
    stale = review(trendy["candidate_id"], trendy["drawing_id"], high=11, version="0" * 16)
    assert pick("casual", t=3.0, mode="strict", reviews=[stale])["shortage"] == "no_candidate"


def test_review_can_narrow_but_never_widen_the_policy():
    basic = pick("casual", t=3.0, mode="study")["basic"]       # short puffer
    wide = review(basic["candidate_id"], basic["drawing_id"], low=-20, high=20)
    assert pick("casual", t=8.0, mode="strict", reviews=[wide])["filtered"]["basic"] == {"temperature_blocked": 1}
    narrow = review(basic["candidate_id"], basic["drawing_id"], low=-20, high=2)
    assert pick("casual", t=3.0, mode="strict", reviews=[narrow])["filtered"]["basic"] == {"outside_reviewed_range": 1}


def test_coat_without_policy_rule_needs_a_reviewed_range_in_strict():
    trendy = pick("casual", t=3.0, mode="study")["trendy"]
    assert drawing_attributes(trendy["drawing_id"])["temperature_rule"] is None
    assert "temperature_unreviewed" in trendy["flags"]
    assert pick("casual", t=3.0, mode="strict")["filtered"]["trendy"] == {"unreviewed": 1}


@pytest.mark.parametrize("mode", ["strict", "study"])
def test_rain_and_snow_unknown_block_in_every_mode(mode):
    rainy = pick("casual", t=3.0, mode=mode, rain=True)
    assert rainy["shortage"] == "no_candidate"
    assert set(rainy["filtered"]["basic"]) == {"rain_unknown"}
    snowy = pick("casual", t=3.0, mode=mode, snow=True)
    assert set(snowy["filtered"]["trendy"]) == {"snow_unknown"}
    failed = pick("casual", t=3.0, mode=mode, rain=None)
    assert set(failed["filtered"]["basic"]) == {"weather_unknown"}


def test_explicit_rain_review_lets_a_look_through():
    trendy = pick("casual", t=3.0, mode="study")["trendy"]
    wet = review(trendy["candidate_id"], trendy["drawing_id"], high=11, rain="suitable")
    result = pick("casual", t=3.0, mode="study", rain=True, reviews=[wet])
    assert result["trendy"]["candidate_id"] == trendy["candidate_id"]


def test_record_validation():
    assert cr.validate_record({"candidate_id": "x"})
    bad_steps = {**review("x", "all-018"), "steps": ["owner_final"]}
    assert "all three review steps are required" in cr.validate_record(bad_steps)
    assert cr.validate_record(review("x", "all-018", low=5, high=5))


# ---------------- selection ----------------

def test_pair_never_shares_a_composition_and_is_deterministic():
    for tpo in ("casual", "business_casual", "business_formal"):
        a, b = pick(tpo), pick(tpo)
        assert a == b
        if a["basic"] and a["trendy"]:
            assert a["basic"]["composition"] != a["trendy"]["composition"]


def test_penalty_uses_composition_window_and_outer():
    opt = {"composition": "C1", "outer_type": "coat"}
    hist = [{"basic": {"composition": "C1", "outer_type": "coat"}}]
    assert sel._penalty(opt, "basic", hist, n=2)[:2] == (1, 1)
    assert sel._penalty(opt, "basic", hist, n=1)[0] == 0      # no alternative -> no penalty


def test_kept_role_is_never_dropped():
    first = pick("casual", t=3.0)
    result = sel.select(USER, "casual", "2026-12-01", COLORS, weather(8.0), calendar_season="winter",
                        mode="study", keep={"trendy": first["trendy"]})
    assert result["trendy"] == first["trendy"] and result["basic"] is None
    assert result["shortage"] == "basic_missing"


# ---------------- store ----------------

@pytest.fixture
def store(tmp_path):
    return store_mod.OutfitDayStore(str(tmp_path / "outfits.sqlite3"))


CTX = {"region": "gyeongju_fixed", "note": "test context only"}


def rec(store, now, w, ctx=CTX, tpo="casual"):
    return store_mod.recommend_for_day(store, USER, tpo, now, ctx, COLORS, w, calendar_season="winter", mode="study")


def test_kst_day_from_utc():
    assert str(store_mod.today_kst(datetime(2026, 12, 1, 14, 59, 59, tzinfo=UTC))) == "2026-12-01"
    assert str(store_mod.today_kst(datetime(2026, 12, 1, 15, 0, 0, tzinfo=UTC))) == "2026-12-02"
    with pytest.raises(ValueError):
        store_mod.today_kst(datetime(2026, 12, 1, 15, 0, 0))


def test_same_day_revisit_and_minor_forecast_keep_the_stored_pair(store):
    now = datetime(2026, 12, 1, 0, 0, tzinfo=UTC)
    first = rec(store, now, weather(3.0))
    assert first["source"] == "created" and first["revision"] == 0
    again = rec(store, now + timedelta(hours=3), weather(3.6))
    assert again["source"] == "stored"
    assert (again["basic"], again["trendy"]) == (first["basic"], first["trendy"])


def test_rule_breaking_forecast_replaces_only_that_role(store):
    now = datetime(2026, 12, 1, 0, 0, tzinfo=UTC)
    first = rec(store, now, weather(3.0))
    changed = rec(store, now + timedelta(hours=5), weather(6.0))
    assert changed["source"] == "revised" and changed["revision"] == 1
    assert changed["trendy"] == first["trendy"]                 # still valid, kept
    assert changed["basic"] is None and changed["shortage"] == "basic_missing"
    assert store.count() == 1


def test_context_change_is_a_separate_row_but_the_same_history_day(store):
    now = datetime(2026, 12, 1, 0, 0, tzinfo=UTC)
    rec(store, now, weather(3.0))
    rec(store, now, weather(3.0), ctx={**CTX, "settings": "changed"})
    assert store.count() == 2
    owner = store_mod.owner_key(USER["id"])
    assert len(store.history(owner, "casual", store_mod.today_kst(now) + timedelta(days=1))) == 1


def test_history_is_previous_seven_days_only(store):
    start = datetime(2026, 12, 1, 0, 0, tzinfo=UTC)
    for i in range(10):
        rec(store, start + timedelta(days=i), weather(3.0))
    owner = store_mod.owner_key(USER["id"])
    day10 = store_mod.today_kst(start + timedelta(days=9))
    days = [h["day"] for h in store.history(owner, "casual", day10)]
    assert days == [str(day10 - timedelta(days=k)) for k in range(7, 0, -1)]


def test_rows_older_than_thirty_days_are_deleted(store):
    old = datetime(2026, 10, 1, 0, 0, tzinfo=UTC)
    rec(store, old, weather(3.0))
    rec(store, old + timedelta(days=35), weather(3.0))
    assert store.count() == 1


def test_concurrent_first_writes_leave_one_row(store):
    owner, now = store_mod.owner_key(USER["id"]), datetime(2026, 12, 1, 0, 0, tzinfo=UTC)
    day = store_mod.today_kst(now)
    barrier, results = threading.Barrier(2), []

    def write(tag):
        barrier.wait()
        results.append(store.insert_if_absent(owner, day, "casual", "ctx", {"writer": tag}, now))

    threads = [threading.Thread(target=write, args=(t,)) for t in ("a", "b")]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert store.count() == 1
    assert results[0][1] == results[1][1]
    assert sorted(r[2] for r in results) == [False, True]


def test_store_requires_a_member_account():
    with pytest.raises(ValueError):
        store_mod.owner_key("guest")


# ---------------- isolation ----------------

def test_new_modules_are_not_reachable_from_the_live_path():
    new = {"fashion_v2.outfit_selector", "fashion_v2.outfit_day_store", "fashion_v2.candidate_reviews",
           "fashion_v2.illustration_resolver"}
    for path in [ROOT / "main.py"] + [ROOT / "fashion_v2" / n for n in (
            "svg_recommendation.py", "template_catalog.py", "weather_catalog.py", "weather_outfit.py",
            "weather_service.py", "review_preferences.py", "wearable_options.py", "realwear_rules.py")]:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imported = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        imported |= {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        assert not imported & new, path.name
    for name in ("outfit_selector.py", "outfit_day_store.py", "candidate_reviews.py", "illustration_resolver.py"):
        source = (ROOT / "fashion_v2" / name).read_text(encoding="utf-8")
        assert "import main" not in source and "from main" not in source
        assert "wardrobe_store" not in source and "_connection" not in source
