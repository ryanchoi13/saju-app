import json
import os
import sys
from datetime import date, time, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

from fastapi import FastAPI, Query
from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.semantic.applied import build_applied_state
from app.engine.services.food_match_preview import match_testset

app = FastAPI(title="DALHA Applied State Preview")


def _birth(y: int, m: int, d: int, gender: str, hour: int, minute: int) -> BirthInput:
    return BirthInput(
        name="preview",
        gender=gender,
        birth_date=date(y, m, d),
        calendar_type="solar",
        is_leap_month=False,
        birth_time=time(hour, minute),
        time_unknown=False,
    )


def _week_payload(start: date, days: int, birth: BirthInput) -> dict:
    rows = []
    for offset in range(days):
        target = start + timedelta(days=offset)
        core = calculate_myeongri_core(birth, target_date=target)
        state = build_applied_state(core, "natal+luck_cycle+annual+monthly+daily")
        food = match_testset(state)
        rows.append({
            "date": target.isoformat(),
            "day_ganji": core.timing.daily.get("pillar", {}).get("ganji"),
            "day_element": core.timing.daily.get("pillar", {}).get("stem_element"),
            "synthesis_confidence": core.synthesis.confidence.value,
            "strength": core.synthesis.strength_state,
            "climate": core.synthesis.climate_state,
            "favorable_operations": core.synthesis.favorable_operations,
            "pending_operations": core.synthesis.pending_operations,
            "diagnostic_conflicts": core.synthesis.diagnostic_conflicts,
            "applied_state": state,
            "food_match": food,
        })
    return {"rows": rows}


def _summary(payload: dict) -> list[dict]:
    result = []
    for row in payload["rows"]:
        state = row["applied_state"]
        direction_timings = {
            item["operation"]: {
                "status": item.get("status"),
                "elements": item.get("elements", []),
                "timing_relation": item.get("timing_assessment", {}).get("relation"),
                "has_unresolved_context": item.get("timing_assessment", {}).get("has_unresolved_context"),
                "supporting_elements": item.get("timing_assessment", {}).get("supporting_elements", []),
                "opposing_elements": item.get("timing_assessment", {}).get("opposing_elements", []),
                "mixed_elements": item.get("timing_assessment", {}).get("mixed_elements", []),
            }
            for item in state["directions"]
            if item.get("status") in {"confirmed", "conditional"}
        }
        food = row["food_match"]
        result.append({
            "date": row["date"],
            "day_ganji": row["day_ganji"],
            "day_element": row["day_element"],
            "overall_status": state["overall_status"],
            "confirmed_elements": state["confirmed_elements"],
            "conditional_elements": state["conditional_elements"],
            "directions": direction_timings,
            "strength_shift": state["timing"]["strength_shift"],
            "food": {
                "foundation_matches": food["foundation_matches"],
                "flavor_matches": food["flavor_matches"],
                "held_signal": food["held_signal"],
                "neutral": food["neutral"],
            },
        })
    return result


def _synthetic_supported_state(element: str) -> dict:
    return {
        "directions": [{
            "operation": "element_preview",
            "elements": [element],
            "status": "conditional",
            "timing_assessment": {"relation": "supports"},
        }]
    }


def _food_element_matrix() -> dict:
    result = {}
    for element in "木火土金水":
        matched = match_testset(_synthetic_supported_state(element))
        result[element] = {
            "foundation_matches": matched["foundation_matches"],
            "flavor_matches": matched["flavor_matches"],
        }
    return result


@app.on_event("startup")
def log_default_preview():
    birth = _birth(1978, 3, 13, "male", 10, 30)
    payload = _week_payload(date(2026, 9, 11), 7, birth)
    print("FOOD_ELEMENT_MATRIX=" + json.dumps(_food_element_matrix(), ensure_ascii=False, separators=(",", ":")), flush=True)
    print(
        "APPLIED_FOOD_WEEK_SUMMARY="
        + json.dumps(_summary(payload), ensure_ascii=False, separators=(",", ":")),
        flush=True,
    )


@app.get("/food-matrix")
def food_matrix():
    matrix = _food_element_matrix()
    return {
        "matrix": matrix,
        "counts": {
            element: {
                "foundation": len(data["foundation_matches"]),
                "flavor": len(data["flavor_matches"]),
                "total_unique": len(set(data["foundation_matches"]) | set(data["flavor_matches"])),
            }
            for element, data in matrix.items()
        },
    }


@app.get("/week")
def week(
    start: date = Query(date(2026, 9, 11)),
    days: int = Query(7, ge=1, le=31),
    y: int = 1978,
    m: int = 3,
    d: int = 13,
    gender: str = "male",
    hour: int = 10,
    minute: int = 30,
):
    birth = _birth(y, m, d, gender, hour, minute)
    payload = _week_payload(start, days, birth)
    return {
        "profile": {"y": y, "m": m, "d": d, "gender": gender, "hour": hour, "minute": minute},
        "summary": _summary(payload),
        **payload,
    }
