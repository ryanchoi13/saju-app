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
    "accessory_rule": "only_when_context_or_outfit_balance_requires",
    "formal_trouser_pose": "stack_both_legs_then_fold_lower_section_sideways",
    "forbidden": (
        "invisible_mannequin",
        "detached_item_rail",
        "duplicate_garment",
        "brand_logo",
        "embedded_text",
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
        raise ValueError("supporting accessories must remain optional and sparse")
    return True


validate_layout_spec()
