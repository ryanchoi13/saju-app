"""Visual rules for owner-reviewed fashion boards.

These rules describe artwork direction only. They never assemble or publish a
look at request time; approved boards remain static assets.
"""


LAYOUT_SPEC = {
    "style": "editorial_floor_flat_lay",
    "layer_order": ("outer", "top_or_dress", "bottom", "shoes"),
    "garment_rule": "natural_overlap_without_body_silhouette",
    "shoe_scale": {"min": 1.15, "max": 1.30},
    "optional_accessory_count": {"min": 0, "max": 1},
    "accessory_rule": "one_bag_required_for_women_thirties_plus_except_explicit_sport_or_beach",
    "formal_trouser_pose": "tuck_waist_under_jacket_stack_both_legs_then_fold_both_lower_sections_sideways_together",
    "forbidden": (
        "invisible_mannequin",
        "detached_item_rail",
        "duplicate_garment",
        "brand_logo",
        "embedded_text",
        "formal_trousers_with_only_one_leg_folded",
        "formal_trousers_detached_from_jacket_or_short_looking",
    ),
}


BACKGROUND_PRESETS = {
    "warm_neutral": {"label": "웜 아이보리", "hex": "#F2EEE6"},
    "cool_neutral": {"label": "라이트 블루그레이", "hex": "#E9EEF0"},
    "soft_gray": {"label": "소프트 웜그레이", "hex": "#ECEAE6"},
    "clean_white": {"label": "클린 오프화이트", "hex": "#F7F7F4"},
}


def select_background(outfit_tone):
    """Choose contrast for readability; never tint the board strongly."""
    mapping = {
        "brown_beige": "warm_neutral",
        "light_neutral": "cool_neutral",
        "dark_neutral": "warm_neutral",
        "mixed_color": "clean_white",
        "gray_dominant": "soft_gray",
    }
    try:
        return BACKGROUND_PRESETS[mapping[outfit_tone]]
    except KeyError as exc:
        raise ValueError("unknown outfit tone") from exc


def validate_layout_spec():
    scale = LAYOUT_SPEC["shoe_scale"]
    accessories = LAYOUT_SPEC["optional_accessory_count"]
    if not (1 < scale["min"] <= scale["max"] <= 1.3):
        raise ValueError("shoe emphasis must remain editorial, not distorted")
    if accessories != {"min": 0, "max": 1}:
        raise ValueError("supporting accessories must remain sparse")
    if "both_lower_sections" not in LAYOUT_SPEC["formal_trouser_pose"]:
        raise ValueError("formal trouser legs must be folded together")
    if "tuck_waist_under_jacket" not in LAYOUT_SPEC["formal_trouser_pose"]:
        raise ValueError("formal trousers must connect naturally under the jacket")
    return True


validate_layout_spec()
