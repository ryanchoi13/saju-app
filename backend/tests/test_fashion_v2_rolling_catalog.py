from datetime import date
from pathlib import Path

from fashion_v2.rolling_catalog import (
    REVIEW_CATALOG, age_profile, candidate, rolling_review_batches,
    validate_review_catalog, weather_family,
)
from fashion_v2.editorial_layout import LAYOUT_SPEC, select_background, validate_layout_spec
from fashion_v2.age_tpo_policy import (
    TWENTIES_FORMAL_DIRECTION, age_band, next_generation_scopes, tpos_for,
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


def test_owner_review_page_is_noindex_and_uses_thirty_six_flat_lay_boards():
    from main import serve_design_comparison

    response = serve_design_comparison("fashion-review")
    assert response.path.endswith("assets/fashion-review.html")
    assert response.headers["x-robots-tag"] == "noindex, nofollow"
    html = open(response.path, encoding="utf-8").read()
    boards = list(Path("assets/fashion-v2-boards").glob("review-*-warm-*-v3.webp"))
    assert len(boards) == 36
    assert all("layout-sample" not in path.name for path in boards)
    assert "editorial floor" not in html
    assert "편집형 플랫레이" in html
    assert all(age in html for age in ("19~34세", "35~49세", "50세 이상"))
    assert "아직 운영 추천 화보에는 적용하지 않았습니다" in html


def test_age_research_page_covers_both_genders_and_five_age_bands():
    from main import serve_design_comparison

    response = serve_design_comparison("fashion-age-research")
    assert response.path.endswith("assets/fashion-age-research.html")
    assert response.headers["x-robots-tag"] == "noindex, nofollow"
    html = open(response.path, encoding="utf-8").read()
    assert all(label in html for label in ("여성", "남성", "10대", "20대", "30대", "40대", "50대+"))
    assert all(tpo in html for tpo in ("캐주얼", "비즈니스 캐주얼", "비즈니스 포멀"))
    assert "항상 올블랙" in html
    assert "아래 TPO 범위는 다음 화보 제작 정책에 반영했으며" in html
    assert "비즈니스 캐주얼·포멀은 만들지 않습니다" in html
    assert "포멀 · 필요할 때" in html


def test_editorial_layout_is_floor_flat_lay_not_invisible_mannequin():
    assert validate_layout_spec() is True
    assert LAYOUT_SPEC["style"] == "editorial_floor_flat_lay"
    assert LAYOUT_SPEC["garment_rule"] == "natural_overlap_without_body_silhouette"
    assert "invisible_mannequin" in LAYOUT_SPEC["forbidden"]
    assert LAYOUT_SPEC["shoe_scale"] == {"min": 1.15, "max": 1.30}
    assert LAYOUT_SPEC["optional_accessory_count"] == {"min": 0, "max": 1}


def test_background_is_selected_for_contrast_not_fixed_to_one_color():
    assert select_background("brown_beige")["hex"] == "#F2EEE6"
    assert select_background("light_neutral")["hex"] == "#E9EEF0"
    assert select_background("mixed_color")["hex"] == "#F7F7F4"


def test_next_generation_tpo_coverage_follows_age_relevance():
    assert tpos_for("teen") == ("casual",)
    assert tpos_for("twenties") == ("casual", "business_casual")
    assert tpos_for("twenties", include_conditional=True) == (
        "casual", "business_casual", "business_formal",
    )
    for age_key in ("thirties", "forties", "fifty_plus"):
        assert tpos_for(age_key) == (
            "casual", "business_casual", "business_formal",
        )


def test_next_generation_has_five_age_bands_and_separates_optional_formal():
    assert [age_band(age) for age in (17, 24, 35, 47, 61, None)] == [
        "teen", "twenties", "thirties", "forties", "fifty_plus", "thirties",
    ]
    standard = next_generation_scopes()
    with_conditional = next_generation_scopes(include_conditional=True)
    assert len(standard) == 144
    assert len(with_conditional) == 156
    added = [scope for scope in with_conditional if scope not in standard]
    assert len(added) == 12
    assert all(scope["age_band"] == "twenties" for scope in added)
    assert all(scope["tpo"] == "business_formal" for scope in added)
    assert all(scope["coverage"] == "conditional" for scope in added)


def test_twenty_something_formal_is_modern_and_not_tie_first():
    assert TWENTIES_FORMAL_DIRECTION["male"]["default"] == "modern_suit_no_tie"
    assert TWENTIES_FORMAL_DIRECTION["male"]["strict_context"] == "tie_allowed"
    assert TWENTIES_FORMAL_DIRECTION["female"]["default"] == "modern_tailored_set_or_dress"
