"""Small food-semantics test set for validating DALHA food matching.

Preview data only. Flavor matching uses only the food's *identity flavors*:
a flavor must be clearly perceived as part of the dish's character. Salt, soy
sauce, or seasoning merely being present is not enough to create a salty signal.

Composition such as vegetable-rich / meat-forward is preserved separately and
is not automatically converted into an element.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, Tuple


FIVE_FLAVOR_ELEMENT = {
    "sour": "木",
    "bitter": "火",
    "sweet": "土",
    "pungent": "金",
    "salty": "水",
}

# Limited classical foundation signals already accepted for this pilot.
CLASSICAL_FOUNDATION = {
    "rice": ("sweet", "土"),
    "wheat": ("bitter", "火"),
    "soybean": ("salty", "水"),
    "beef": ("sweet", "土"),
    "pork": ("salty", "水"),
    "chicken": ("pungent", "金"),
}


@dataclass(frozen=True)
class FoodProfile:
    name: str
    foundations: Tuple[str, ...]
    identity_ingredients: Tuple[str, ...]
    secondary_ingredients: Tuple[str, ...]
    identity_flavors: FrozenSet[str]
    taste_notes: Tuple[str, ...]
    composition_tags: FrozenSet[str]
    cooking_modifiers: Tuple[str, ...]
    serving_temperature: str
    thermal_nature: str = "undetermined"
    thermal_confidence: str = "low"


FOOD_TESTSET = (
    FoodProfile("비빔밥", ("rice",), ("gochujang", "mixed_vegetables"), ("egg",),
                frozenset({"pungent", "sweet"}), ("vegetal", "savory"),
                frozenset({"grain_based", "vegetable_rich"}), ("mix",), "warm"),
    FoodProfile("육회비빔밥", ("rice", "beef"), ("raw_beef", "gochujang"), ("mixed_vegetables",),
                frozenset({"pungent", "sweet"}), ("savory",),
                frozenset({"grain_based", "vegetable_rich", "raw_protein"}), ("mix", "raw"), "cool"),
    FoodProfile("김치볶음밥", ("rice",), ("kimchi",), ("egg", "scallion"),
                frozenset({"sour", "pungent"}), ("savory",),
                frozenset({"grain_based"}), ("stir_fry",), "hot"),
    FoodProfile("된장찌개", ("soybean",), ("doenjang",), ("tofu", "zucchini", "onion"),
                frozenset({"salty"}), ("fermented", "savory"),
                frozenset({"broth_based", "vegetable_present"}), ("simmer",), "hot"),
    FoodProfile("김치찌개", ("pork",), ("kimchi",), ("tofu", "scallion"),
                frozenset({"sour", "pungent", "salty"}), ("fermented", "savory"),
                frozenset({"broth_based", "meat_present"}), ("simmer",), "hot"),
    FoodProfile("제육볶음", ("pork",), ("gochujang",), ("onion", "garlic", "scallion"),
                frozenset({"pungent", "salty", "sweet"}), ("savory",),
                frozenset({"meat_forward", "vegetable_present"}), ("stir_fry",), "hot"),
    FoodProfile("삼겹살구이", ("pork",), ("grilled_pork",), ("garlic", "scallion"),
                frozenset(), ("fatty", "savory"),
                frozenset({"meat_forward"}), ("grill",), "hot"),
    FoodProfile("소고기불고기", ("beef",), ("soy_sugar_marinade",), ("onion", "scallion"),
                frozenset({"sweet"}), ("savory",),
                frozenset({"meat_forward", "vegetable_present"}), ("grill_or_pan",), "hot"),
    FoodProfile("삼계탕", ("chicken", "rice"), ("chicken_broth",), ("garlic", "jujube", "ginseng"),
                frozenset(), ("mild", "savory"),
                frozenset({"broth_based", "meat_forward", "grain_present"}), ("long_simmer",), "hot", "warm", "medium"),
    FoodProfile("해물칼국수", ("wheat",), ("seafood_broth",), ("seafood", "scallion"),
                frozenset(), ("seafood_umami", "savory"),
                frozenset({"noodle_based", "broth_based", "seafood_forward"}), ("boil",), "hot"),
    FoodProfile("물냉면", ("buckwheat_noodle",), ("cold_broth",), ("cucumber", "egg"),
                frozenset(), ("mild", "style_dependent_sour_sweet"),
                frozenset({"noodle_based", "cold_dish"}), ("boil_then_chill",), "cold"),
    FoodProfile("비빔냉면", ("buckwheat_noodle",), ("gochujang_vinegar_sauce",), ("cucumber", "egg"),
                frozenset({"sour", "pungent", "sweet"}), ("savory",),
                frozenset({"noodle_based", "cold_dish"}), ("boil_then_chill", "mix"), "cold"),
    FoodProfile("짜장면", ("wheat",), ("chunjang_sauce",), ("pork", "onion", "cabbage"),
                frozenset({"sweet"}), ("umami", "savory"),
                frozenset({"noodle_based", "vegetable_present"}), ("boil", "stir_fry_sauce"), "hot"),
    FoodProfile("짬뽕", ("wheat",), ("spicy_seafood_broth",), ("seafood", "cabbage", "scallion"),
                frozenset({"pungent", "salty"}), ("seafood_umami",),
                frozenset({"noodle_based", "broth_based", "seafood_forward", "vegetable_present"}), ("boil", "stir_fry_then_simmer"), "hot"),
    FoodProfile("탕수육", ("pork",), ("sweet_sour_sauce",), ("starch_or_wheat_coating", "vegetables"),
                frozenset({"sour", "sweet"}), ("savory",),
                frozenset({"meat_forward"}), ("deep_fry",), "hot"),
    FoodProfile("어향가지", ("eggplant",), ("spicy_sour_savory_sauce",), ("garlic", "scallion"),
                frozenset({"sour", "pungent", "sweet"}), ("umami", "savory"),
                frozenset({"vegetable_forward"}), ("stir_fry",), "hot"),
    FoodProfile("경양식 돈가스", ("pork",), ("fried_pork", "brown_sauce"), ("wheat_breadcrumb_coating", "cabbage"),
                frozenset({"sour", "sweet"}), ("savory",),
                frozenset({"meat_forward"}), ("deep_fry",), "hot"),
    FoodProfile("후라이드치킨", ("chicken",), ("fried_chicken",), ("wheat_coating",),
                frozenset(), ("savory", "seasoned"),
                frozenset({"meat_forward"}), ("deep_fry",), "hot"),
    FoodProfile("모둠초밥", ("rice",), ("vinegared_rice", "raw_fish"), ("seafood",),
                frozenset({"sour", "sweet"}), ("seafood_umami",),
                frozenset({"grain_based", "raw_protein", "seafood_forward"}), ("season_rice", "raw"), "cool"),
    FoodProfile("회덮밥", ("rice",), ("raw_fish", "gochujang_vinegar_sauce"), ("vegetables",),
                frozenset({"sour", "pungent", "sweet"}), ("seafood_umami",),
                frozenset({"grain_based", "vegetable_rich", "raw_protein", "seafood_forward"}), ("mix", "raw"), "cool"),
    FoodProfile("알리오 올리오", ("wheat",), ("garlic_olive_oil",), ("garlic", "chili"),
                frozenset({"pungent"}), ("savory",),
                frozenset({"noodle_based"}), ("boil", "saute"), "hot"),
    FoodProfile("포케", ("rice",), ("raw_fish", "vegetables"), ("soy_based_dressing",),
                frozenset(), ("fresh", "savory"),
                frozenset({"grain_based", "vegetable_rich", "raw_protein", "seafood_forward"}), ("assemble", "raw"), "cool"),
    FoodProfile("햄에그 토스트", ("wheat",), ("toast_egg_ham",), ("pork_ham", "egg"),
                frozenset({"sweet"}), ("savory",),
                frozenset({"bread_based", "protein_present"}), ("toast", "pan_cook"), "warm"),
    FoodProfile("오트밀", ("oats",), ("oat_porridge",), ("milk_or_water", "fruit_optional"),
                frozenset(), ("mild", "nutty"),
                frozenset({"grain_based"}), ("simmer",), "warm"),
)


def element_signals(profile: FoodProfile) -> dict:
    """Return explainable elemental signals without numeric weighting."""

    foundation = []
    for ingredient in profile.foundations:
        mapped = CLASSICAL_FOUNDATION.get(ingredient)
        if mapped:
            flavor, element = mapped
            foundation.append({
                "element": element,
                "basis": "classical_foundation",
                "ingredient": ingredient,
                "flavor": flavor,
            })

    flavor = [
        {
            "element": FIVE_FLAVOR_ELEMENT[item],
            "basis": "identity_flavor",
            "flavor": item,
        }
        for item in sorted(profile.identity_flavors)
        if item in FIVE_FLAVOR_ELEMENT
    ]
    return {"foundation": foundation, "flavor": flavor}
