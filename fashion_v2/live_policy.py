"""Age-aware production policy for fashion-v2 complete looks.

The catalogue remains a set of whole outfits.  This module only adds the
age-dependent finishing pieces approved during editorial review; it never
randomly mixes garments from different templates.
"""

from copy import deepcopy

from fashion_v2.age_tpo_policy import age_band


FEMALE_BAGS = {
    "casual": {
        "daily": ("가벼운 숄더백", "beige", "lightweight_leather"),
        "trend": ("모던 숄더백", "burgundy", "lightweight_leather"),
    },
    "business_casual": {
        "daily": ("가벼운 토트백", "brown", "lightweight_leather"),
        "trend": ("구조적 숄더백", "burgundy", "lightweight_leather"),
    },
    "business_formal": {
        "daily": ("구조적 핸드백", "black", "lightweight_leather"),
        "trend": ("구조적 핸드백", "burgundy", "lightweight_leather"),
    },
}

COMFORT_SHOES = {
    ("male", "casual", "daily"): ("쿠션 워킹 스니커즈", "cushioned_supportive"),
    ("male", "casual", "trend"): ("쿠션 레트로 스니커즈", "cushioned_supportive"),
    ("male", "business_casual", "daily"): ("고무창 컴포트 로퍼", "cushioned_rubber_sole"),
    ("male", "business_casual", "trend"): ("쿠션 가죽 스니커즈", "cushioned_supportive"),
    ("male", "business_formal", "daily"): ("쿠션 고무창 옥스퍼드", "cushioned_rubber_sole"),
    ("male", "business_formal", "trend"): ("고무창 더비 구두", "cushioned_rubber_sole"),
    ("female", "casual", "daily"): ("쿠션 워킹 스니커즈", "cushioned_supportive"),
    ("female", "casual", "trend"): ("쿠션 레트로 스니커즈", "cushioned_supportive"),
    ("female", "business_casual", "daily"): ("쿠션 컴포트 로퍼", "roomy_cushioned"),
    ("female", "business_casual", "trend"): ("소프트 스퀘어토 컴포트화", "roomy_cushioned"),
    ("female", "business_formal", "daily"): ("낮은 블록힐 컴포트 펌프스", "low_broad_heel_cushioned"),
    ("female", "business_formal", "trend"): ("낮은 블록힐 컴포트 펌프스", "low_broad_heel_cushioned"),
}


def apply_live_age_policy(look, age):
    """Return a production look decorated with approved age requirements."""
    result = deepcopy(look)
    band = age_band(age)
    result["age_band"] = band
    result["age_policy"] = "live_age_personalized"

    if result.get("gender") == "female" and band in {"thirties", "forties", "fifty_plus"}:
        if not any(item.get("category") == "bag" for item in result.get("items", ())):
            role = result.get("look_role", "daily")
            label, color, material = FEMALE_BAGS[result["tpo"]][role]
            result["items"].append({
                "category": "bag",
                "label": label,
                "color": color,
                "material": material,
                "age_required": True,
            })

    if band == "fifty_plus":
        shoe = next((item for item in result.get("items", ()) if item.get("category") == "shoes"), None)
        if shoe:
            label, comfort = COMFORT_SHOES[(result["gender"], result["tpo"], result["look_role"])]
            shoe.update(
                label=label,
                comfort_profile=comfort,
                comfort_gate_passed=True,
            )
    return result

