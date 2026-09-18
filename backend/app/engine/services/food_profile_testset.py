"""Small food-semantics test set for validating DALHA food matching.

This is deliberately not the production menu catalog. The purpose is to test
whether a small, explainable food profile can be matched against Applied
Myeongri State before migrating the full menu pool.

Classical foundation signals used here are limited to explicit Huangdi Neijing
Five Flavors correspondences:
- rice -> sweet -> Earth
- wheat -> bitter -> Fire
- soybean -> salty -> Water
- beef -> sweet -> Earth
- pork -> salty -> Water
- chicken -> pungent -> Metal

Unlisted foundations (seafood, buckwheat, oats, eggs, etc.) are left
unclassified rather than forced into an element.
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
    five_flavors: FrozenSet[str]
    cooking_modifiers: Tuple[str, ...]
    serving_temperature: str
    thermal_nature: str = "undetermined"
    thermal_confidence: str = "low"


FOOD_TESTSET = (
    FoodProfile("비빔밥", ("rice",), ("gochujang",), ("mixed_vegetables", "egg"),
                frozenset({"sweet", "pungent", "salty"}), ("mix",), "warm"),
    FoodProfile("육회비빔밥", ("rice", "beef"), ("gochujang",), ("raw_beef", "mixed_vegetables"),
                frozenset({"sweet", "pungent", "salty"}), ("mix", "raw"), "cool"),
    FoodProfile("김치볶음밥", ("rice",), ("kimchi",), ("egg", "scallion"),
                frozenset({"sour", "pungent", "salty"}), ("stir_fry",), "hot"),
    FoodProfile("된장찌개", ("soybean",), ("doenjang",), ("tofu", "zucchini", "onion"),
                frozenset({"salty", "sweet"}), ("simmer",), "hot"),
    FoodProfile("김치찌개", ("pork",), ("kimchi",), ("tofu", "scallion"),
                frozenset({"sour", "pungent", "salty"}), ("simmer",), "hot"),
    FoodProfile("제육볶음", ("pork",), ("gochujang",), ("onion", "garlic", "scallion"),
                frozenset({"pungent", "sweet", "salty"}), ("stir_fry",), "hot"),
    FoodProfile("삼겹살구이", ("pork",), ("salt_garlic",), ("scallion",),
                frozenset({"salty", "pungent"}), ("grill",), "hot"),
    FoodProfile("소고기불고기", ("beef",), ("soy_sauce_marinade",), ("onion", "scallion"),
                frozenset({"sweet", "salty"}), ("grill_or_pan",), "hot"),
    FoodProfile("삼계탕", ("chicken", "rice"), ("chicken_broth",), ("garlic", "jujube", "ginseng"),
                frozenset({"sweet", "pungent"}), ("long_simmer",), "hot", "warm", "medium"),
    FoodProfile("해물칼국수", ("wheat",), ("seafood_broth",), ("seafood", "scallion"),
                frozenset({"salty", "sweet"}), ("boil",), "hot"),
    FoodProfile("물냉면", ("buckwheat_noodle",), ("cold_broth",), ("vinegar", "mustard", "cucumber"),
                frozenset({"sour", "salty", "pungent"}), ("boil_then_chill",), "cold"),
    FoodProfile("비빔냉면", ("buckwheat_noodle",), ("gochujang_vinegar_sauce",), ("cucumber", "egg"),
                frozenset({"sour", "pungent", "sweet", "salty"}), ("boil_then_chill", "mix"), "cold"),
    FoodProfile("짜장면", ("wheat",), ("chunjang",), ("pork", "onion", "cabbage"),
                frozenset({"salty", "sweet"}), ("boil", "stir_fry_sauce"), "hot"),
    FoodProfile("짬뽕", ("wheat",), ("spicy_seafood_broth",), ("seafood", "cabbage", "scallion"),
                frozenset({"pungent", "salty"}), ("boil", "stir_fry_then_simmer"), "hot"),
    FoodProfile("탕수육", ("pork",), ("sweet_sour_sauce",), ("starch_or_wheat_coating", "vegetables"),
                frozenset({"sour", "sweet"}), ("deep_fry",), "hot"),
    FoodProfile("어향가지", ("eggplant",), ("spicy_sour_savory_sauce",), ("garlic", "scallion"),
                frozenset({"sour", "pungent", "sweet", "salty"}), ("stir_fry",), "hot"),
    FoodProfile("경양식 돈가스", ("pork",), ("brown_sauce",), ("wheat_breadcrumb_coating", "cabbage"),
                frozenset({"sweet", "salty", "sour"}), ("deep_fry",), "hot"),
    FoodProfile("후라이드치킨", ("chicken",), ("fried_coating",), ("wheat_coating",),
                frozenset({"salty"}), ("deep_fry",), "hot"),
    FoodProfile("모둠초밥", ("rice",), ("vinegared_rice",), ("raw_fish", "seafood"),
                frozenset({"sour", "sweet", "salty"}), ("season_rice", "raw"), "cool"),
    FoodProfile("회덮밥", ("rice",), ("gochujang_vinegar_sauce",), ("raw_fish", "vegetables"),
                frozenset({"sour", "pungent", "sweet", "salty"}), ("mix", "raw"), "cool"),
    FoodProfile("알리오 올리오", ("wheat",), ("garlic_olive_oil",), ("garlic", "chili"),
                frozenset({"pungent", "salty"}), ("boil", "saute"), "hot"),
    FoodProfile("포케", ("rice",), ("soy_based_dressing",), ("raw_fish", "vegetables"),
                frozenset({"salty", "sweet"}), ("assemble", "raw"), "cool"),
    FoodProfile("햄에그 토스트", ("wheat",), ("toast_egg_ham",), ("pork_ham", "egg"),
                frozenset({"sweet", "salty"}), ("toast", "pan_cook"), "warm"),
    FoodProfile("오트밀", ("oats",), ("oat_porridge",), ("milk_or_water", "fruit_optional"),
                frozenset({"sweet"}), ("simmer",), "warm"),
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
            "basis": "five_flavor",
            "flavor": item,
        }
        for item in sorted(profile.five_flavors)
        if item in FIVE_FLAVOR_ELEMENT
    ]
    return {"foundation": foundation, "flavor": flavor}
