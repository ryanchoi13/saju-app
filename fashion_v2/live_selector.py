"""Guarded production bridge for the reviewed outfit selector (#188 PR-4B).

The existing two-look response is the fallback contract. Rollout is controlled only
by server environment variables, so disabling it needs no client or database change:

- ``DALHA_FASHION_SELECTOR_ROLLOUT=off`` (default)
- ``allowlist`` with comma-separated ``DALHA_FASHION_SELECTOR_ACCOUNTS``
- ``limited`` with a stable ``DALHA_FASHION_SELECTOR_PERCENT`` bucket (allowlist wins)
- ``all``

The bridge uses study mode for legacy candidates because they predate owner-review
records. Selector-only candidates still require their current review in every mode.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import logging
import os

from fashion_v2.candidate_reviews import load_reviews
from fashion_v2.outfit_day_store import production_store, recommend_for_day
from fashion_v2.weather_outfit import PROFILE_RULES

LOGGER = logging.getLogger(__name__)
ROLLOUT_ENV = "DALHA_FASHION_SELECTOR_ROLLOUT"
ALLOWLIST_ENV = "DALHA_FASHION_SELECTOR_ACCOUNTS"
PERCENT_ENV = "DALHA_FASHION_SELECTOR_PERCENT"
SELECTOR_VERSION = "outfit-selector-v1"
MODE = "study"
FLEECE_CANDIDATES = {
    "pending-female-winter-casual-fleece",
    "pending-male-winter-casual-fleece",
}


def initialize_storage():
    production_store.initialize()


def storage_health() -> str:
    return production_store.health()


def _allowlist() -> set[str]:
    return {value.strip() for value in os.getenv(ALLOWLIST_ENV, "").split(",") if value.strip()}


def rollout_mode() -> str:
    value = os.getenv(ROLLOUT_ENV, "off").strip().lower()
    return value if value in {"off", "allowlist", "limited", "all"} else "off"


def rollout_enabled(user_id: str | None) -> bool:
    if not user_id:
        return False
    mode = rollout_mode()
    if mode == "off":
        return False
    if mode == "all":
        return True
    if user_id in _allowlist():
        return True
    if mode == "allowlist":
        return False
    try:
        percent = max(0, min(100, int(os.getenv(PERCENT_ENV, "0"))))
    except ValueError:
        percent = 0
    bucket = int(hashlib.sha256(user_id.encode()).hexdigest()[:8], 16) % 100
    return bucket < percent


def selector_weather(profile: dict) -> dict:
    """Translate the live forecast into the selector's explicit hard-rule inputs."""
    return {
        "apparent_c": profile.get("daytime_apparent_high"),
        "basis": "daytime_apparent_high",
        # Preserve missing hazard fields as unknown. The selector rejects unknown
        # weather instead of silently treating an older/incomplete forecast as dry.
        "rain": profile.get("rainy"),
        "snow": profile.get("snowy"),
        "fetched_at": profile.get("fetched_at"),
        "legacy_profile": profile,
    }


def _context(gender, age, calendar_season, colors, profile) -> dict:
    return {
        "selector": SELECTOR_VERSION,
        "region": profile.get("location_mode", "fixed_gyeongju"),
        "gender": gender,
        "age": age,
        "calendar_season": calendar_season,
        "colors": [color.get("hex") for color in colors],
    }


def connect_selector(legacy_contexts: dict, *, user_id: str | None, gender: str, age: int | None,
                     calendar_season: str, colors, weather_profile: dict | None,
                     now_utc: datetime | None = None, store=None) -> tuple[dict, dict]:
    """Return (contexts, diagnostics). Every TPO keeps the legacy two-look fallback."""
    if not rollout_enabled(user_id):
        return legacy_contexts, {"status": "off", "mode": rollout_mode()}
    if not weather_profile or weather_profile.get("daytime_apparent_high") is None:
        return legacy_contexts, {"status": "fallback", "reason": "weather_unavailable"}

    selected = deepcopy(legacy_contexts)
    weather = selector_weather(weather_profile)
    user = {"id": user_id, "gender": gender, "age": age}
    now_utc = now_utc or datetime.now(timezone.utc)
    store = store or production_store
    reviews = load_reviews()
    applied = []
    fallback = []
    try:
        for tpo, legacy in legacy_contexts.items():
            result = recommend_for_day(
                store, user, tpo, now_utc,
                _context(gender, age, calendar_season, colors, weather_profile),
                colors, weather, calendar_season=calendar_season, mode=MODE, reviews=reviews,
            )
            options = [result.get("basic"), result.get("trendy")]
            if result.get("shortage") or any(not option or not option.get("look") for option in options):
                fallback.append({"tpo": tpo, "reason": result.get("shortage") or "invalid_look"})
                continue
            context = deepcopy(legacy)
            context.update(
                status="selector_live",
                looks=[deepcopy(options[0]["look"]), deepcopy(options[1]["look"])],
                selection_source=SELECTOR_VERSION,
                selection_revision=result.get("revision", 0),
            )
            selected[tpo] = context
            applied.append(tpo)
    except Exception as exc:  # The established two-look result is the production safety net.
        LOGGER.warning("Fashion selector fallback (%s)", type(exc).__name__)
        return legacy_contexts, {"status": "fallback", "reason": "selector_error"}
    return selected, {
        "status": "applied" if applied else "fallback",
        "mode": rollout_mode(),
        "applied_tpos": applied,
        "fallback_tpos": fallback,
    }


def selected_guidance(profile: dict | None, contexts: dict) -> str | None:
    """Align the cold-weather sentence only when the shown basic look is fleece."""
    if not profile:
        return None
    guidance = profile.get("guidance")
    try:
        candidate = contexts["casual"]["looks"][0].get("candidate_id")
    except (KeyError, IndexError, TypeError, AttributeError):
        return guidance
    if candidate not in FLEECE_CANDIDATES:
        return guidance
    sentence = "오늘 추천은 플리스와 긴팔 한 겹을 기준으로 골랐어요. 오래 밖에 있거나 추위를 많이 타면 더 따뜻한 겉옷을 준비하세요."
    cold = PROFILE_RULES["cold"][3]
    if isinstance(guidance, str) and cold in guidance:
        return guidance.replace(cold, sentence, 1)
    return " ".join(part for part in (sentence, guidance) if part)
