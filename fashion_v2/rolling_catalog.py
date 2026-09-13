"""Fixed complete-look candidates for rolling fashion-board review.

This catalog is not the live board map. Approved candidates receive static
artwork before they can be exposed to users; no user request mixes garments.
"""

from datetime import date, timedelta


GENDERS = ("male", "female")
AGE_PROFILES = {
    "young": {"label": "19~34세", "min": 19, "max": 34},
    "adult": {"label": "35~49세", "min": 35, "max": 49},
    "mature": {"label": "50세 이상", "min": 50, "max": None},
}
WEATHER_FAMILIES = {
    "warm_transition": {"label": "더운 낮·선선한 저녁", "bands": ("very_hot", "hot", "warm")},
    "mild": {"label": "얇은 긴팔이 알맞은 날", "bands": ("mild",)},
    "cool_chilly": {"label": "얇은 재킷·니트가 필요한 날", "bands": ("cool", "chilly")},
}
TPOS = ("casual", "business_casual", "business_formal")
ROLES = ("daily", "trend")


def age_profile(age):
    """Return a visual preference, never an eligibility restriction."""
    if age is None:
        return "adult"
    if int(age) < 35:
        return "young"
    return "adult" if int(age) < 50 else "mature"


def weather_family(thermal_band):
    for key, profile in WEATHER_FAMILIES.items():
        if thermal_band in profile["bands"]:
            return key
    return "cool_chilly"


CASUAL = {
    "male": {
        "young": (("스트레이트 워시드 데님", "레트로 스니커즈"), ("세미와이드 블랙 데님", "가죽 스니커즈")),
        "adult": (("단정한 스트레이트 데님", "미니멀 가죽 스니커즈"), ("릴랙스드 그레이 데님", "레트로 가죽 스니커즈")),
        "mature": (("편안한 진청 스트레이트 데님", "쿠션 스니커즈"), ("편안한 차콜 캐주얼 팬츠", "가죽 스니커즈")),
    },
    "female": {
        "young": (("와이드 스트레이트 데님", "레트로 스니커즈"), ("플레어 미디 스커트", "메리제인 플랫")),
        "adult": (("그레이 워시 스트레이트 데님", "레트로 스니커즈"), ("A라인 미디 스커트", "슬링백 플랫")),
        "mature": (("편안한 스트레이트 데님", "쿠션 스니커즈"), ("차분한 플레어 미디 스커트", "소프트 로퍼")),
    },
}


def _item(category, label, material, wear_mode="worn"):
    return {"category": category, "label": label, "material": material, "wear_mode": wear_mode}


def _casual(gender, age_key, weather_key, role):
    variant = 0 if role == "daily" else 1
    bottom, shoes = CASUAL[gender][age_key][variant]
    female = gender == "female"
    choices = {
        "warm_transition": (
            (("반팔 코튼 티셔츠", "반팔 파인 니트") if female else ("반팔 니트 폴로", "반팔 파인 니트")),
            (("여성용 경량 셔츠 재킷", "칼라리스 가디건") if female else ("경량 필드 재킷", "코튼 오버셔츠")),
            "light_cotton", "carry"),
        "mild": (
            (("얇은 긴팔 티셔츠", "파인 니트") if female else ("얇은 긴팔 폴로", "크루넥 스웨트셔츠")),
            (("여성용 경량 필드 재킷", "소프트 가디건") if female else ("경량 해링턴 재킷", "텍스처 오버셔츠")),
            "light_cotton", "worn"),
        "cool_chilly": (
            (("니트 맨투맨", "크루넥 니트") if female else ("니트 폴로", "크루넥 니트")),
            (("여성용 캐주얼 재킷", "울 블렌드 가디건") if female else ("캐주얼 필드 재킷", "울 블렌드 블루종")),
            "wool_blend", "worn"),
    }
    tops, outers, outer_material, wear_mode = choices[weather_key]
    return [_item("outer", outers[variant], outer_material, wear_mode),
            _item("top", tops[variant], "cotton_knit"),
            _item("bottom", bottom, "denim" if "데님" in bottom else "woven"),
            _item("shoes", shoes, "leather_mesh")]


def _business_casual(gender, age_key, weather_key, role):
    trend = role == "trend"
    fit = {"young": "세미와이드", "adult": "스트레이트", "mature": "편안한 스트레이트"}[age_key]
    if gender == "female" and trend:
        bottom = {"young": "모던 미디 스커트", "adult": "A라인 미디 스커트", "mature": "차분한 미디 스커트"}[age_key]
        shoes = "슬링백 플랫" if age_key != "mature" else "소프트 로퍼"
    else:
        bottom = f"{fit} 서머 슬랙스" if weather_key == "warm_transition" else f"{fit} 슬랙스"
        shoes = "미니멀 가죽 스니커즈" if trend and age_key != "mature" else "로퍼"
    if gender == "female":
        top = "반팔 블라우스" if weather_key == "warm_transition" else ("얇은 셔츠" if weather_key == "mild" else "파인 니트")
        outer = "칼라리스 재킷" if not trend else "셔츠 재킷"
    else:
        top = "반팔 클래식 셔츠" if weather_key == "warm_transition" else ("옥스퍼드 셔츠" if weather_key == "mild" else "파인 니트")
        outer = "경량 해링턴 재킷" if not trend else "언스트럭처드 재킷"
    wear_mode = "carry" if weather_key == "warm_transition" else "worn"
    return [_item("outer", outer, "summer_wool" if weather_key == "warm_transition" else "wool_blend", wear_mode),
            _item("top", top, "cotton"),
            _item("bottom", bottom, "summer_wool" if weather_key == "warm_transition" else "wool_blend"),
            _item("shoes", shoes, "leather")]


def _business_formal(gender, age_key, weather_key, role):
    material = "summer_wool" if weather_key == "warm_transition" else ("spring_wool" if weather_key == "mild" else "autumn_wool")
    if gender == "female" and role == "trend":
        dress = {"young": "모던 정장 원피스", "adult": "반팔 정장 원피스" if weather_key == "warm_transition" else "정장 원피스", "mature": "클래식 정장 원피스"}[age_key]
        return [_item("outer", "경량 정장 재킷" if weather_key != "cool_chilly" else "정장 재킷", material),
                _item("dress", dress, material), _item("shoes", "닫힌 플랫", "leather")]
    bottom = {"young": "모던 스트레이트 수트 바지", "adult": "스트레이트 수트 바지", "mature": "편안한 클래식 수트 바지"}[age_key]
    items = [_item("outer", "수트 재킷", material),
             _item("top", "블라우스" if gender == "female" else "드레스 셔츠", "cotton_silk" if gender == "female" else "cotton"),
             _item("bottom", bottom, material)]
    if gender == "male":
        items.append(_item("tie", "레지멘탈 타이" if role == "trend" else "솔리드 타이", "silk"))
    items.append(_item("shoes", "펌프스" if gender == "female" else ("더비 구두" if role == "trend" else "옥스퍼드 구두"), "leather"))
    return items


def candidate(gender, age_key, weather_key, tpo, role):
    if gender not in GENDERS or age_key not in AGE_PROFILES or weather_key not in WEATHER_FAMILIES or tpo not in TPOS or role not in ROLES:
        raise ValueError("unknown editorial scope")
    builder = {"casual": _casual, "business_casual": _business_casual, "business_formal": _business_formal}[tpo]
    return {"id": f"{gender}-{age_key}-{weather_key}-{tpo}-{role}", "gender": gender,
            "age_profile": age_key, "age_policy": "soft_preference_no_exclusion",
            "weather_family": weather_key, "tpo": tpo, "look_role": role,
            "status": "owner_review_pending", "items": builder(gender, age_key, weather_key, role)}


REVIEW_CATALOG = tuple(candidate(g, a, w, t, r) for g in GENDERS for a in AGE_PROFILES
                       for w in WEATHER_FAMILIES for t in TPOS for r in ROLES)


def rolling_review_batches(start: date, horizon_days=35):
    end = start + timedelta(days=horizon_days)
    return (
        {"weather_family": "warm_transition", "review_on": start, "coverage_start": start, "coverage_end": min(end, start + timedelta(days=13))},
        {"weather_family": "mild", "review_on": start + timedelta(days=7), "coverage_start": start + timedelta(days=10), "coverage_end": min(end, start + timedelta(days=27))},
        {"weather_family": "cool_chilly", "review_on": start + timedelta(days=18), "coverage_start": start + timedelta(days=24), "coverage_end": end},
    )


def validate_review_catalog():
    expected = len(GENDERS) * len(AGE_PROFILES) * len(WEATHER_FAMILIES) * len(TPOS) * len(ROLES)
    if len(REVIEW_CATALOG) != expected or len({look["id"] for look in REVIEW_CATALOG}) != expected:
        raise ValueError("every review scope needs one fixed candidate")
    for look in REVIEW_CATALOG:
        items = look["items"]
        if sum(item["category"] == "shoes" for item in items) != 1:
            raise ValueError(f"{look['id']}: exactly one footwear item")
        carried = [item for item in items if item["wear_mode"] == "carry"]
        if look["weather_family"] == "warm_transition" and look["tpo"] != "business_formal":
            if len(carried) != 1 or carried[0]["category"] != "outer":
                raise ValueError(f"{look['id']}: one separate evening layer")
        elif carried:
            raise ValueError(f"{look['id']}: unexpected carried item")
        if look["tpo"] == "business_formal" and any("데님" in item["label"] for item in items):
            raise ValueError(f"{look['id']}: denim is not formal")
    return True


validate_review_catalog()
