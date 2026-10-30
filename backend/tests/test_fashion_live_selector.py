from datetime import datetime, timedelta, timezone

import pytest

from fashion_v2 import live_selector
from fashion_v2.outfit_day_store import DurableOutfitDayStore, OutfitDayStore
from fashion_v2.svg_recommendation import PALETTE, build_svg_catalog_contexts
from fashion_v2.weather_outfit import PROFILE_RULES, thermal_band

UTC = timezone.utc
COLORS = (PALETTE["navy"], PALETTE["beige"])


def profile(apparent=8.0, *, rain=False, snow=False):
    band = thermal_band(apparent)
    return {
        "location": "경주",
        "location_mode": "fixed_gyeongju",
        "thermal_band": band["key"],
        "thermal_label": band["label"],
        "daytime_apparent_high": apparent,
        "evening_apparent_low": apparent - 5,
        "carry_light_outer": False,
        "rainy": rain,
        "snowy": snow,
        "guidance": PROFILE_RULES[band["key"]][3],
        "base_layer": band["base_layer"],
        "outerwear": band["outerwear"],
        "catalog_season_hint": band["catalog_season_hint"],
        "avoid_suede": rain,
    }


def legacy(gender="female", apparent=8.0, *, rain=False, snow=False):
    weather = profile(apparent, rain=rain, snow=snow)
    return build_svg_catalog_contexts(
        gender, "winter", *COLORS, weather_profile=weather, age=40,
    ), weather


def connect(store, now, *, gender="female", apparent=8.0, rain=False, snow=False,
            user_id="user_live_selector"):
    contexts, weather = legacy(gender, apparent, rain=rain, snow=snow)
    selected, diagnostics = live_selector.connect_selector(
        contexts, user_id=user_id, gender=gender, age=40, calendar_season="winter",
        colors=COLORS, weather_profile=weather, now_utc=now, store=store,
    )
    return contexts, selected, diagnostics, weather


def test_rollout_modes_are_server_controlled_and_stable(monkeypatch):
    monkeypatch.delenv(live_selector.ROLLOUT_ENV, raising=False)
    assert live_selector.rollout_enabled("user_a") is False

    monkeypatch.setenv(live_selector.ROLLOUT_ENV, "allowlist")
    monkeypatch.setenv(live_selector.ALLOWLIST_ENV, "user_a, user_b")
    assert live_selector.rollout_enabled("user_a") is True
    assert live_selector.rollout_enabled("user_c") is False

    monkeypatch.setenv(live_selector.ROLLOUT_ENV, "limited")
    monkeypatch.setenv(live_selector.PERCENT_ENV, "100")
    assert live_selector.rollout_enabled("user_c") is True
    monkeypatch.setenv(live_selector.PERCENT_ENV, "0")
    assert live_selector.rollout_enabled("user_c") is False
    assert live_selector.rollout_enabled("user_a") is True

    monkeypatch.setenv(live_selector.ROLLOUT_ENV, "all")
    assert live_selector.rollout_enabled("user_any") is True


def test_rollout_off_returns_the_exact_legacy_object(monkeypatch, tmp_path):
    monkeypatch.setenv(live_selector.ROLLOUT_ENV, "off")
    contexts, weather = legacy()
    selected, diagnostics = live_selector.connect_selector(
        contexts, user_id="user_off", gender="female", age=40, calendar_season="winter",
        colors=COLORS, weather_profile=weather,
        store=OutfitDayStore(str(tmp_path / "off.sqlite")),
    )
    assert selected is contexts
    assert diagnostics == {"status": "off", "mode": "off"}


def test_live_bridge_returns_two_renderable_looks_and_freezes_same_day(monkeypatch, tmp_path):
    monkeypatch.setenv(live_selector.ROLLOUT_ENV, "all")
    store = OutfitDayStore(str(tmp_path / "days.sqlite"))
    now = datetime(2026, 12, 1, 1, tzinfo=UTC)
    _, first, diagnostics, _ = connect(store, now)
    _, again, diagnostics_again, _ = connect(store, now + timedelta(hours=5))

    assert diagnostics["status"] == diagnostics_again["status"] == "applied"
    for tpo, context in first.items():
        assert len(context["looks"]) == 2
        assert all(look["garment_spec"] for look in context["looks"])
        if tpo in diagnostics["applied_tpos"]:
            assert context["status"] == "selector_live"
            assert all(look["candidate_id"] for look in context["looks"])
            assert [look["candidate_id"] for look in context["looks"]] == [
                look["candidate_id"] for look in again[tpo]["looks"]
            ]
        else:
            assert context["status"] == "svg_integration_review"


def test_fleece_rotates_in_within_two_days_and_obeys_review_boundaries(monkeypatch, tmp_path):
    monkeypatch.setenv(live_selector.ROLLOUT_ENV, "all")
    store = OutfitDayStore(str(tmp_path / "rotation.sqlite"))
    start = datetime(2026, 12, 1, 1, tzinfo=UTC)
    basics = []
    for offset in range(2):
        _, selected, diagnostics, _ = connect(store, start + timedelta(days=offset))
        assert diagnostics["status"] == "applied"
        basics.append(selected["casual"]["looks"][0]["candidate_id"])
    assert set(basics) & live_selector.FLEECE_CANDIDATES

    for index, apparent in enumerate((6.9, 11.0), start=3):
        _, selected, diagnostics, _ = connect(
            store, start + timedelta(days=index), apparent=apparent,
            user_id=f"user_boundary_{index}",
        )
        assert diagnostics["status"] == "applied"
        assert selected["casual"]["looks"][0].get("candidate_id") not in live_selector.FLEECE_CANDIDATES


@pytest.mark.parametrize("hazard", ["rain", "snow"])
def test_fleece_is_never_shown_in_rain_or_snow(monkeypatch, tmp_path, hazard):
    monkeypatch.setenv(live_selector.ROLLOUT_ENV, "all")
    store = OutfitDayStore(str(tmp_path / f"{hazard}.sqlite"))
    _, selected, diagnostics, _ = connect(
        store, datetime(2026, 12, 1, 1, tzinfo=UTC),
        rain=hazard == "rain", snow=hazard == "snow",
    )
    for context in selected.values():
        assert all(look.get("candidate_id") not in live_selector.FLEECE_CANDIDATES
                   for look in context["looks"])
    assert diagnostics["status"] in {"applied", "fallback"}


def test_selector_error_and_shortage_keep_legacy_two_look_contract(monkeypatch):
    monkeypatch.setenv(live_selector.ROLLOUT_ENV, "all")
    contexts, weather = legacy()

    class BrokenStore:
        def get(self, *args, **kwargs):
            raise RuntimeError("not exposed")

    selected, diagnostics = live_selector.connect_selector(
        contexts, user_id="user_broken", gender="female", age=40, calendar_season="winter",
        colors=COLORS, weather_profile=weather, store=BrokenStore(),
    )
    assert selected is contexts
    assert diagnostics == {"status": "fallback", "reason": "selector_error"}

    monkeypatch.setattr(live_selector, "recommend_for_day", lambda *args, **kwargs: {
        "basic": None, "trendy": None, "shortage": "no_candidate",
    })
    selected, diagnostics = live_selector.connect_selector(
        contexts, user_id="user_shortage", gender="female", age=40, calendar_season="winter",
        colors=COLORS, weather_profile=weather, store=object(),
    )
    assert selected == contexts
    assert diagnostics["status"] == "fallback"
    assert {entry["tpo"] for entry in diagnostics["fallback_tpos"]} == set(contexts)


def test_missing_snow_field_is_unknown_and_keeps_legacy(monkeypatch, tmp_path):
    monkeypatch.setenv(live_selector.ROLLOUT_ENV, "all")
    contexts, weather = legacy()
    weather.pop("snowy")
    selected, diagnostics = live_selector.connect_selector(
        contexts, user_id="user_old_weather", gender="female", age=40,
        calendar_season="winter", colors=COLORS, weather_profile=weather,
        store=OutfitDayStore(str(tmp_path / "old-weather.sqlite")),
    )
    assert selected == contexts
    assert diagnostics["status"] == "fallback"
    assert {entry["tpo"] for entry in diagnostics["fallback_tpos"]} == set(contexts)


def test_fleece_guidance_replaces_only_the_mismatched_cold_sentence():
    contexts, weather = legacy()
    contexts["casual"]["looks"][0]["candidate_id"] = "pending-female-winter-casual-fleece"
    weather["guidance"] += " 추가 안내."
    guidance = live_selector.selected_guidance(weather, contexts)
    assert "도톰한 니트와 코트" not in guidance
    assert "플리스와 긴팔 한 겹" in guidance
    assert "추가 안내" in guidance


def test_durable_adapter_uses_application_local_database(monkeypatch, tmp_path):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("RENDER_SERVICE_ID", raising=False)
    monkeypatch.setenv("DALHA_WARDROBE_DB", str(tmp_path / "application.sqlite"))
    store = DurableOutfitDayStore()
    store.initialize()
    now = datetime(2026, 12, 1, 1, tzinfo=UTC)
    owner = "a" * 64
    day = now.date()
    revision, payload, created = store.insert_if_absent(
        owner, day, "casual", "ctx", {"basic": None}, now, "study",
    )
    assert (revision, payload, created) == (0, {"basic": None}, True)
    assert store.get(owner, day, "casual", "ctx") == (0, {"basic": None})
    assert store.health() == "local_sqlite"


def test_actual_daily_fortune_response_uses_the_guarded_bridge(monkeypatch, tmp_path):
    from main import get_saju_pillars_and_analysis

    monkeypatch.setenv(live_selector.ROLLOUT_ENV, "all")
    monkeypatch.setattr(
        live_selector, "production_store", OutfitDayStore(str(tmp_path / "main-response.sqlite")),
    )
    daily = get_saju_pillars_and_analysis(
        "운영연결", "female", 1990, 5, 15, "solar", 5,
        menu_account_id="user_live_main", weather_profile=profile(8),
    )["daily_fortune"]
    assert daily["fashion_selector"]["status"] == "applied"
    assert daily["weather_outfit"]["selector_applied"] is True
    assert any(context["status"] == "selector_live" for context in daily["fashion_v2"].values())
    assert all(len(context["looks"]) == 2 for context in daily["fashion_v2"].values())
