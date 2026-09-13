"""Select complete fashion-v2 looks by forecast-derived clothing weight.

Calendar season still controls colour mood elsewhere.  This module selects
what is actually comfortable to wear.  A warm day with a cool evening uses a
curated daytime outfit plus a separate carry layer; it never renders the
carry layer as though it were worn all day.
"""

from copy import deepcopy

from fashion_v2.template_catalog import templates_for


TPOS = ("casual", "business_casual", "business_formal")
ROLES = ("daily", "trend")

# Only switch the live payload when both Daily and Trend boards for that exact
# colour result have passed visual review. Other users retain existing boards.
REVIEWED_WEATHER_BOARD_PAIRS = {
    ("male", "#ebd3a2", "#a2b0ad"),
}


def reviewed_weather_board_available(gender, color_a, color_b):
    return (
        gender,
        str(color_a.get("hex", "")).lower(),
        str(color_b.get("hex", "")).lower(),
    ) in REVIEWED_WEATHER_BOARD_PAIRS


def _item(category, label, color, material, wear_mode="worn"):
    return {
        "category": category,
        "label": label,
        "color": color,
        "material": material,
        "wear_mode": wear_mode,
    }


def _look(gender, tpo, role, form, items):
    return {
        "id": f"{gender}-warm-transition-{tpo}-{role}",
        "gender": gender,
        "season": "weather_transition",
        "tpo": tpo,
        "look_role": role,
        "form": form,
        "formal_variant": None,
        "status": "owner_review_pending",
        "selection_mode": "whole_template_only",
        "age_policy": "soft_preference_no_exclusion",
        "items": items,
    }


# These are complete, reviewed-as-a-set candidates for a short-sleeve daytime
# forecast that needs one light layer after sunset.  Daily and Trend deliberately
# differ in top, silhouette, footwear, and carry layer.
WARM_TRANSITION_LOOKS = (
    _look("male", "casual", "daily", "pants", [
        _item("top", "반팔 폴로", "navy", "cotton_pique"),
        _item("bottom", "경량 스트레이트 팬츠", "light_gray", "light_cotton"),
        _item("shoes", "가죽 운동화", "dark_brown", "leather"),
        _item("carry_outer", "얇은 바람막이", "navy", "light_nylon", "carry"),
    ]),
    _look("male", "casual", "trend", "pants", [
        _item("top", "반팔 니트", "camel", "cotton_knit"),
        _item("bottom", "세미와이드 경량 팬츠", "charcoal", "light_cotton"),
        _item("shoes", "레트로 가죽 운동화", "black", "leather"),
        _item("carry_outer", "얇은 오버셔츠", "charcoal", "light_cotton", "carry"),
    ]),
    _look("male", "business_casual", "daily", "pants", [
        _item("top", "반팔 클래식 셔츠", "light_blue", "cotton"),
        _item("bottom", "서머 슬랙스", "navy", "summer_wool"),
        _item("shoes", "로퍼", "dark_brown", "leather"),
        _item("carry_outer", "경량 해링턴 재킷", "beige", "light_cotton", "carry"),
    ]),
    _look("male", "business_casual", "trend", "pants", [
        _item("top", "니트 폴로", "ivory", "cotton_knit"),
        _item("bottom", "원턱 서머 슬랙스", "gray", "summer_wool"),
        _item("shoes", "미니멀 가죽 운동화", "black", "leather"),
        _item("carry_outer", "얇은 언스트럭처드 재킷", "navy", "summer_wool", "carry"),
    ]),
    _look("female", "casual", "daily", "pants", [
        _item("top", "반팔 티셔츠", "ivory", "cotton"),
        _item("bottom", "경량 스트레이트 팬츠", "denim_blue", "light_denim"),
        _item("shoes", "가죽 운동화", "gray", "leather"),
        _item("carry_outer", "얇은 바람막이", "beige", "light_nylon", "carry"),
    ]),
    _look("female", "casual", "trend", "skirt", [
        _item("top", "반팔 파인 니트", "soft_pink", "cotton_knit"),
        _item("bottom", "라이트 플리츠 스커트", "navy", "light_woven"),
        _item("shoes", "메리제인 플랫", "black", "leather"),
        _item("carry_outer", "얇은 크롭 셔츠", "ivory", "light_cotton", "carry"),
    ]),
    _look("female", "business_casual", "daily", "pants", [
        _item("top", "반팔 니트", "ivory", "cotton_knit"),
        _item("bottom", "서머 슬랙스", "navy", "summer_wool"),
        _item("shoes", "로퍼", "dark_brown", "leather"),
        _item("carry_outer", "얇은 칼라리스 재킷", "beige", "summer_wool", "carry"),
    ]),
    _look("female", "business_casual", "trend", "skirt", [
        _item("top", "반팔 블라우스", "light_blue", "cotton"),
        _item("bottom", "라이트 미디 스커트", "charcoal", "light_woven"),
        _item("shoes", "슬링백 플랫", "black", "leather"),
        _item("carry_outer", "얇은 셔츠 재킷", "dusty_blue", "light_cotton", "carry"),
    ]),
)


def _weather_fit(profile, source):
    return {
        "thermal_band": profile["thermal_band"],
        "thermal_label": profile["thermal_label"],
        "daytime_apparent_high": profile["daytime_apparent_high"],
        "evening_apparent_low": profile["evening_apparent_low"],
        "carry_light_outer": profile["carry_light_outer"],
        "rainy": profile["rainy"],
        "guidance": profile["guidance"],
        "template_source": source,
    }


def _rain_safe(look):
    for item in look["items"]:
        if "suede" not in item["material"]:
            continue
        item.update(
            label="생활방수 가죽 운동화",
            material="water_resistant_leather",
            rain_adjusted=True,
        )


def weather_templates_for(gender, tpo, profile):
    """Return one Daily and one Trend whole outfit for the weather profile."""
    if gender not in {"male", "female"} or tpo not in TPOS:
        return ()

    use_transition = (
        profile["carry_light_outer"]
        and profile["base_layer"] in {"short_sleeve", "short_or_thin_long"}
        and tpo != "business_formal"
    )
    if use_transition:
        selected = [
            look for look in WARM_TRANSITION_LOOKS
            if look["gender"] == gender and look["tpo"] == tpo
        ]
        source = "warm_day_cool_evening"
    else:
        selected = list(templates_for(gender, profile["catalog_season_hint"], tpo))
        source = f"thermal_{profile['catalog_season_hint']}"

    result = []
    for original in selected:
        look = deepcopy(original)
        for item in look["items"]:
            item.setdefault("wear_mode", "worn")
        if profile["avoid_suede"]:
            _rain_safe(look)
        look["weather_fit"] = _weather_fit(profile, source)
        result.append(look)
    return tuple(result)


def validate_weather_catalog():
    errors = []
    expected = {(g, t, r) for g in ("male", "female") for t in TPOS[:-1] for r in ROLES}
    actual = {(x["gender"], x["tpo"], x["look_role"]) for x in WARM_TRANSITION_LOOKS}
    if actual != expected or len(WARM_TRANSITION_LOOKS) != len(expected):
        errors.append("warm transition needs one Daily and one Trend per non-formal scope")
    for look in WARM_TRANSITION_LOOKS:
        worn = [x for x in look["items"] if x["wear_mode"] == "worn"]
        carried = [x for x in look["items"] if x["wear_mode"] == "carry"]
        if len(carried) != 1 or carried[0]["category"] != "carry_outer":
            errors.append(f"{look['id']}: exactly one carry layer is required")
        if not any(x["category"] in {"top", "dress"} for x in worn):
            errors.append(f"{look['id']}: a worn daytime top is required")
        if not any(x["category"] == "shoes" for x in worn):
            errors.append(f"{look['id']}: worn shoes are required")
        if look["gender"] == "male":
            bottom = next(x for x in worn if x["category"] == "bottom")
            if bottom["color"] not in {"navy", "gray", "charcoal", "light_gray"}:
                errors.append(f"{look['id']}: impractical male bottom")
    if errors:
        raise ValueError("; ".join(errors))
    return True


validate_weather_catalog()
