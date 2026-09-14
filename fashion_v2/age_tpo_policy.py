"""Age-aware TPO coverage for the next reviewed fashion-board batch.

This policy controls which editorial boards are prepared and surfaced by
default. It does not ban garments by age and it does not change the current
live recommendation map until the new static boards pass owner review.
"""


GENDERS = ("male", "female")
ROLES = ("daily", "trend")
WEATHER_FAMILIES = ("warm_transition", "mild", "cool_chilly")
TPOS = ("casual", "business_casual", "business_formal")

AGE_BANDS = {
    "teen": {"label": "10대", "min": 10, "max": 19},
    "twenties": {"label": "20대", "min": 20, "max": 29},
    "thirties": {"label": "30대", "min": 30, "max": 39},
    "forties": {"label": "40대", "min": 40, "max": 49},
    "fifty_plus": {"label": "50대+", "min": 50, "max": None},
}

# Standard boards are part of every rolling batch. Conditional boards are
# prepared in a smaller set and shown only for an explicit need. Teen
# interviews and ceremonies will be a separate occasion rather than being
# mislabeled as business wear.
TPO_COVERAGE = {
    "teen": {"standard": ("casual",), "conditional": ()},
    "twenties": {
        "standard": ("casual", "business_casual"),
        "conditional": ("business_formal",),
    },
    "thirties": {"standard": TPOS, "conditional": ()},
    "forties": {"standard": TPOS, "conditional": ()},
    "fifty_plus": {"standard": TPOS, "conditional": ()},
}

TWENTIES_FORMAL_DIRECTION = {
    "male": {"default": "modern_suit_no_tie", "strict_context": "tie_allowed"},
    "female": {
        "default": "modern_tailored_set_or_dress",
        "strict_context": "conservative_tailoring",
    },
}

# Editorial starting weights for future female Casual board batches. These are
# review defaults, not market statistics. Re-estimate them from Dalha selection
# and feedback data once each age/role cell has a useful sample size.
FEMALE_CASUAL_FORM_WEIGHTS = {
    "thirties": {
        "daily": {"pants": 65, "skirt": 20, "dress": 15},
        "trend": {"pants": 50, "skirt": 30, "dress": 20},
    },
    "fifty_plus": {
        "daily": {"pants": 75, "skirt": 15, "dress": 10},
        "trend": {"pants": 45, "skirt": 35, "dress": 20},
    },
}

FIFTY_PLUS_MALE_CASUAL_POLICY = {
    "daily": {
        "bottom_priority": ("cotton_chinos", "denim", "easy_pants"),
        "headwear": "omit_by_default",
        "shoe": "understated_low_profile_walking_sneaker",
    },
    "trend": {
        "bottom_priority": ("ecru_cotton", "dark_denim", "relaxed_pleated"),
        "headwear": "omit_by_default",
        "shoe": "understated_low_profile_sneaker",
    },
}

# A bag completes everyday dress for women from their thirties onward.  The
# category is intentionally broader than a rigid top-handle "handbag": the TPO
# chooses a shoulder, crossbody, tote, or satchel shape.  Sport and beach
# boards may opt out when carrying a bag would be unnatural.
FEMALE_BAG_POLICY = {
    "teen": {"required": False, "direction": "optional_youth_bag"},
    "twenties": {"required": False, "direction": "optional_function_or_trend_bag"},
    "thirties": {"required": True, "direction": "practical_shoulder_crossbody_or_tote"},
    "forties": {"required": True, "direction": "refined_shoulder_crossbody_or_tote"},
    "fifty_plus": {"required": True, "direction": "lightweight_medium_shoulder_crossbody_or_satchel"},
}

FEMALE_BAG_ROLE_DIRECTION = {
    "daily": "practical_lightweight_neutral_and_easy_to_carry",
    "trend": "comfortable_carry_with_current_shape_material_or_color",
}

# Comfort is a gate, not an anti-fashion style.  Fifty-plus boards choose a
# current-looking option only from shoes that remain stable and wearable.
FIFTY_PLUS_COMFORT_SHOE_POLICY = {
    "required_features": (
        "roomy_soft_or_square_toe",
        "cushioned_supportive_sole",
        "low_broad_heel",
        "stable_heel_hold",
        "slip_resistant_not_heavy",
    ),
    "daily": {
        "female": ("cushioned_walking_sneaker", "comfort_loafer", "supportive_slip_on"),
        "male": ("cushioned_walking_sneaker", "rubber_sole_loafer", "supportive_slip_on"),
    },
    "trend": {
        "female": ("refined_comfort_sneaker", "soft_square_toe_mary_jane", "cushioned_loafer"),
        "male": ("retro_comfort_runner", "refined_leather_sneaker", "rubber_sole_derby"),
    },
    "forbidden": (
        "pointed_narrow_toe",
        "stiletto_or_high_heel",
        "thin_unsupported_flat",
        "loose_flip_flop_or_mule",
        "heavy_exaggerated_platform",
    ),
}

# Review directions for the next workwear comparison boards. Age changes the
# priority of details; it never prohibits a color or garment.
MALE_FORMAL_AGE_DIRECTION = {
    "thirties": {
        "tie_priority": ("blue_burgundy_regimental", "clear_navy", "small_geometric"),
        "impression": "younger_modern",
    },
    "fifty_plus": {
        "tie_priority": ("deep_burgundy", "dark_navy_foulard", "forest_micro_pattern"),
        "impression": "restrained_mature",
    },
}

FORTIES_MALE_BUSINESS_CASUAL_SHOES = {
    "daily": ("dark_brown_suede_loafer", "minimal_dark_leather_sneaker"),
    "trend": ("premium_low_profile_contrast_sneaker", "modern_derby"),
}


def age_band(age):
    """Return the editorial age band; age remains a soft garment preference."""
    if age is None:
        return "thirties"
    value = int(age)
    if value < 20:
        return "teen"
    if value < 30:
        return "twenties"
    if value < 40:
        return "thirties"
    if value < 50:
        return "forties"
    return "fifty_plus"


def tpos_for(age_key, include_conditional=False):
    if age_key not in AGE_BANDS:
        raise ValueError("unknown age band")
    coverage = TPO_COVERAGE[age_key]
    if include_conditional:
        return coverage["standard"] + coverage["conditional"]
    return coverage["standard"]


def next_generation_scopes(include_conditional=False):
    """Return fixed board scopes to prepare before the next publishing gate."""
    return tuple(
        {
            "gender": gender,
            "age_band": age_key,
            "weather_family": weather,
            "tpo": tpo,
            "look_role": role,
            "coverage": (
                "conditional"
                if tpo in TPO_COVERAGE[age_key]["conditional"]
                else "standard"
            ),
        }
        for gender in GENDERS
        for age_key in AGE_BANDS
        for weather in WEATHER_FAMILIES
        for tpo in tpos_for(age_key, include_conditional)
        for role in ROLES
    )
