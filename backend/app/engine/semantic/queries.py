"""Define which core layers each DALHA fortune service is allowed to read."""

from __future__ import annotations

from typing import Literal

from app.engine.core.models import MyeongriCoreResult


QUERY_PROFILE_VERSION = "service-query-profile-v1"
ServiceQuery = Literal[
    "lifetime_overall",
    "annual_overall",
    "monthly_overall",
    "daily_overall",
    "lifetime_wealth",
    "annual_wealth",
    "health",
    "love",
    "business",
    "study",
    "career",
]

_PROFILES = {
    "lifetime_overall": {
        "scope": "natal+all_luck_cycles",
        "diagnostics": ["structure", "strength", "climate", "pathology", "mediation", "special_structure"],
        "ten_gods": [],
    },
    "annual_overall": {
        "scope": "natal+luck_cycle+annual",
        "diagnostics": ["structure", "strength", "climate", "pathology", "mediation", "special_structure"],
        "ten_gods": [],
    },
    "monthly_overall": {
        "scope": "natal+luck_cycle+annual+monthly",
        "diagnostics": ["structure", "strength", "climate", "pathology", "mediation"],
        "ten_gods": [],
    },
    "daily_overall": {
        "scope": "natal+luck_cycle+annual+monthly+daily",
        "diagnostics": ["strength", "climate", "pathology", "mediation"],
        "ten_gods": [],
    },
    "lifetime_wealth": {
        "scope": "natal+all_luck_cycles",
        "diagnostics": ["structure", "strength", "pathology", "mediation", "special_structure"],
        "ten_gods": ["direct_wealth", "indirect_wealth", "eating_god", "hurting_officer"],
    },
    "annual_wealth": {
        "scope": "natal+luck_cycle+annual",
        "diagnostics": ["structure", "strength", "pathology", "mediation", "special_structure"],
        "ten_gods": ["direct_wealth", "indirect_wealth", "eating_god", "hurting_officer"],
    },
    "health": {
        "scope": "natal+all_luck_cycles",
        "diagnostics": ["strength", "climate", "pathology", "mediation"],
        "ten_gods": [],
        "medical_claim_allowed": False,
    },
    "love": {
        "scope": "natal+all_luck_cycles",
        "diagnostics": ["structure", "strength", "mediation"],
        "ten_gods": ["direct_wealth", "indirect_wealth", "direct_officer", "seven_killings", "peer", "rob_wealth"],
    },
    "business": {
        "scope": "natal+all_luck_cycles",
        "diagnostics": ["structure", "strength", "pathology", "mediation"],
        "ten_gods": ["direct_wealth", "indirect_wealth", "eating_god", "hurting_officer", "peer", "rob_wealth"],
    },
    "study": {
        "scope": "natal+all_luck_cycles",
        "diagnostics": ["structure", "strength", "climate"],
        "ten_gods": [
            "direct_resource", "indirect_resource", "eating_god", "hurting_officer",
            "direct_officer", "seven_killings",
        ],
    },
    "career": {
        "scope": "natal+all_luck_cycles",
        "diagnostics": ["structure", "strength", "pathology", "mediation"],
        "ten_gods": ["direct_officer", "seven_killings", "direct_wealth", "indirect_wealth", "eating_god", "hurting_officer"],
    },
}


def _timing_for_scope(core: MyeongriCoreResult, scope: str) -> dict:
    timing = {}
    if "all_luck_cycles" in scope:
        timing["luck_cycles"] = core.timing.luck_cycle
    elif "luck_cycle" in scope:
        timing["luck_cycle"] = core.timing.luck_cycle.get("current")
    if "annual" in scope:
        timing["annual"] = core.timing.annual
    if "monthly" in scope:
        timing["monthly"] = core.timing.monthly
    if "daily" in scope:
        timing["daily"] = core.timing.daily
    if scope.endswith("selected_timing"):
        timing = {
            "luck_cycle": core.timing.luck_cycle.get("current"),
            "annual": core.timing.annual,
            "monthly": core.timing.monthly,
            "daily": core.timing.daily,
        }
    return timing


def build_service_query(core: MyeongriCoreResult, query: ServiceQuery) -> dict:
    """Project only the evidence layers relevant to one product surface."""

    profile = _PROFILES[query]
    diagnostics = {
        name: core.diagnostics[name].model_dump(mode="json")
        for name in profile["diagnostics"]
        if name in core.diagnostics
    }
    target_gods = set(profile["ten_gods"])
    focused_ten_gods = [
        item.model_dump(mode="json")
        for item in core.natal_facts.ten_gods.visible + core.natal_facts.ten_gods.hidden
        if not target_gods or item.ten_god.value in target_gods
    ]
    return {
        "profile_version": QUERY_PROFILE_VERSION,
        "query": query,
        "scope": profile["scope"],
        "natal": {
            "day_master": core.natal_facts.day_master.model_dump(mode="json") if core.natal_facts.day_master else None,
            "focused_ten_gods": focused_ten_gods,
            "relationships": [item.model_dump(mode="json") for item in core.relationships],
        },
        "diagnostics": diagnostics,
        "synthesis": core.synthesis.model_dump(mode="json"),
        "timing": _timing_for_scope(core, profile["scope"]),
        "activated_state": (
            core.activated_state.model_dump(mode="json")
            if profile["scope"] != "natal" else None
        ),
        "shensha_support": [item.model_dump(mode="json") for item in core.shensha],
        "semantic_state": core.semantic_state.model_dump(mode="json"),
        "constraints": {
            "shensha_standalone_verdict": False,
            "fixed_score_verdict": False,
            "medical_claim_allowed": profile.get("medical_claim_allowed"),
        },
        "evidence_ids": list(dict.fromkeys(
            core.synthesis.evidence_ids + core.semantic_state.evidence_ids
        )),
    }
