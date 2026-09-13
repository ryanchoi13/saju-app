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
