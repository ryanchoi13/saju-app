from datetime import date

from fashion_v2.rolling_catalog import (
    REVIEW_CATALOG, age_profile, candidate, rolling_review_batches,
    validate_review_catalog, weather_family,
)


def test_review_catalog_covers_gender_age_weather_tpo_and_role():
    assert validate_review_catalog() is True
    assert len(REVIEW_CATALOG) == 108
    assert len({look["id"] for look in REVIEW_CATALOG}) == 108


def test_age_is_a_soft_visual_preference_with_three_profiles():
    assert [age_profile(age) for age in (24, 42, 57, None)] == ["young", "adult", "mature", "adult"]
    looks = [candidate("female", band, "warm_transition", "casual", "daily") for band in ("young", "adult", "mature")]
    assert all(look["age_policy"] == "soft_preference_no_exclusion" for look in looks)
    bottoms = {next(i["label"] for i in look["items"] if i["category"] == "bottom") for look in looks}
    assert len(bottoms) == 3


def test_revised_adult_womens_casual_is_denim_and_not_a_bomber():
    look = candidate("female", "adult", "warm_transition", "casual", "daily")
    labels = [item["label"] for item in look["items"]]
    assert "그레이 워시 스트레이트 데님" in labels
    assert not any("봄버" in label for label in labels)
    assert next(i for i in look["items"] if i["category"] == "outer")["wear_mode"] == "carry"


def test_warm_nonformal_has_one_carry_layer_and_formal_does_not():
    casual = candidate("male", "adult", "warm_transition", "casual", "daily")
    formal = candidate("male", "adult", "warm_transition", "business_formal", "daily")
    assert [i["category"] for i in casual["items"] if i["wear_mode"] == "carry"] == ["outer"]
    assert not any(i["wear_mode"] == "carry" for i in formal["items"])


def test_daily_and_trend_are_complete_distinct_outfits_in_every_scope():
    for daily in (look for look in REVIEW_CATALOG if look["look_role"] == "daily"):
        trend_id = daily["id"].removesuffix("-daily") + "-trend"
        trend = next(look for look in REVIEW_CATALOG if look["id"] == trend_id)
        assert {i["label"] for i in daily["items"]} != {i["label"] for i in trend["items"]}


def test_weather_band_maps_to_prepared_monthly_families():
    assert weather_family("hot") == "warm_transition"
    assert weather_family("mild") == "mild"
    assert weather_family("cool") == "cool_chilly"
    assert weather_family("chilly") == "cool_chilly"


def test_rolling_review_batches_prepare_before_35_day_window_changes():
    batches = rolling_review_batches(date(2026, 9, 13))
    assert [batch["weather_family"] for batch in batches] == ["warm_transition", "mild", "cool_chilly"]
    assert batches[0]["review_on"] == date(2026, 9, 13)
    assert batches[-1]["coverage_end"] == date(2026, 10, 18)
    assert all(batch["review_on"] <= batch["coverage_start"] for batch in batches)


def test_owner_review_page_is_noindex_and_uses_four_new_single_look_boards():
    from main import serve_design_comparison

    response = serve_design_comparison("fashion-review")
    assert response.path.endswith("assets/fashion-review.html")
    assert response.headers["x-robots-tag"] == "noindex, nofollow"
    html = open(response.path, encoding="utf-8").read()
    assert html.count("review-") == 4
    assert "아직 운영 추천 화보에는 적용하지 않았습니다" in html
