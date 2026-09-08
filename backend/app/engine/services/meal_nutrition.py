"""Internal whole-meal estimates; not measured recipes or dietary prescriptions.

All gram templates below are editorial estimates. Components represent assumed
servings, not user-selected quantities. Replace with verified recipe records later.
"""
from functools import lru_cache
from app.engine.services.menu_categories import menu_category

def serving_suggestion(name: str) -> str:
    """Concrete meal accompaniment; not a verified portion/calorie prescription."""
    additions = {
        "토마토 에그스크램블": "토마토 에그스크램블·통밀빵",
        "시금치오믈렛": "시금치오믈렛·통밀빵",
        "콩나물밥": "콩나물밥·두부구이·김",
        "시래기밥": "시래기밥·달걀찜·김",
        "연근밥": "연근밥·두부구이·채소 반찬",
        "야채비빔밥": "야채비빔밥·달걀프라이",
        "돌솥비빔밥": "돌솥비빔밥·달걀프라이",
        "플레인요거트": "플레인요거트·오트밀·바나나·견과류",
        "시나몬토스트": "시나몬토스트·삶은 달걀·우유",
        "딸기잼 토스트": "딸기잼 토스트·삶은 달걀·우유",
        "통밀베이글": "통밀베이글·달걀·토마토",
        "배추전": "배추전·두부구이·밥",
        "토란국": "토란국·밥·달걀찜",
        "우엉잡채": "우엉잡채·두부구이·밥",
        "어향가지": "어향가지·달걀볶음·밥",
        "검은콩밥": "검은콩밥·달걀찜·채소 반찬",
    }
    if name in additions:
        return additions[name]
    if name in {"양송이스프", "감자수프", "야채수프"}:
        return f"{name}·통밀빵·삶은 달걀"
    if name == "야채죽":
        return f"{name}·달걀찜"
    if name in {"콩나물국", "김치국", "된장국", "시래기국"}:
        return f"{name}·밥·두부구이"
    if name.endswith("국"):
        return f"{name}·밥·반찬"
    if name.endswith(("찌개", "청국장", "구이", "볶음", "스테이크")):
        return f"{name}·밥·채소 반찬"
    if name.endswith("회"):
        return f"{name}·밥·채소 곁들임"
    if "샐러드" in name and not any(w in name for w in ("빵", "밥", "샌드위치", "파스타", "면", "감자", "고구마")):
        return f"{name}·통밀빵"
    if menu_category(name) in {"fish_meal", "seafood_meal", "meat_grill", "tofu_meal"} and not any(w in name for w in ("밥", "정식", "빵")):
        return f"{name}·밥"
    return name


# Carbohydrate, protein, fat grams per assumed accompanying portion.
SIDES = {
    "밥": (65, 6, 1), "통밀빵": (30, 6, 3),
    "두부구이": (4, 12, 8), "김": (1, 1, 1),
    "채소 반찬": (8, 2, 3), "채소 곁들임": (6, 2, 1),
    "반찬": (8, 3, 3), "달걀찜": (2, 12, 10),
    "달걀프라이": (1, 6, 7), "달걀볶음": (2, 12, 12),
    "삶은 달걀": (1, 6, 5), "달걀": (1, 6, 5),
    "우유": (10, 7, 7), "오트밀": (23, 5, 3),
    "바나나": (23, 1, 0), "견과류": (3, 3, 8), "토마토": (6, 1, 0),
}
PROTEIN_WORDS = ("고기", "양지", "닭", "치킨", "제육", "불고기", "돼지", "수육", "보쌈",
                 "달걀", "계란", "에그", "오믈렛", "두부", "콩", "치즈", "우유", "요거트",
                 "연어", "참치", "생선", "고등어", "삼치", "북어", "황태", "동태", "새우", "해물", "굴", "조개")
VEGETABLE_WORDS = ("채소", "야채", "나물", "샐러드", "양배추", "시금치", "토마토", "가지", "버섯", "김치", "미역", "청경채", "비빔밥")


def energy(grams):
    return round(4 * grams[0] + 4 * grams[1] + 9 * grams[2], 1)


# Explicit editorial ingredient estimates, not measured recipe claims.
BREAKFAST_RECIPES = {
    "블루베리 두유 견과 스무디": [("블루베리", (14, 1, 0)), ("무가당 두유", (6, 9, 5)), ("견과류", (3, 3, 8)), ("오트밀", (12, 2, 1))],
    "케일 바나나 사과 요거트 스무디": [("케일", (3, 1, 0)), ("바나나", (18, 1, 0)), ("사과", (12, 0, 0)), ("플레인 요거트", (10, 8, 5)), ("견과류", (3, 3, 8))],
    "케일 바나나 두유 스무디": [("케일", (3, 1, 0)), ("바나나", (23, 1, 0)), ("무가당 두유", (6, 9, 5)), ("견과류", (3, 3, 8))],
    "땅콩버터 통밀토스트": [("통밀토스트", (40, 8, 4)), ("땅콩버터", (3, 5, 10))],
}


@lru_cache(maxsize=1024)
def meal_estimate(name, base_kcal, has_protein, has_vegetables, fat_heavy):
    """Replace the implicit meal template when explicit sides exist; never add
    rice to a calorie estimate that already assumes a rice-based whole meal.
    Unchanged composite names are ONE whole-meal template, not split twice.
    """
    serving = serving_suggestion(name)
    sides = serving[len(name):].strip("·").split("·") if serving != name else []
    has_starch = any(side in {"밥", "통밀빵"} for side in sides)
    category = menu_category(name)
    if name in BREAKFAST_RECIPES:
        components = [{"name": label, "grams": grams} for label, grams in BREAKFAST_RECIPES[name]]
    elif sides:
        # Dish-only assumptions. Explicit sides replace old whole-meal kcal.
        if category == "western_soup":
            main = (23, 5, 9)
        elif category == "porridge":
            main = (50, 6, 4)
        elif category in {"soup", "stew"} and has_starch:
            main = (12, 14 if has_protein else 5, 10)
        elif category in {"salad", "fish_meal", "seafood_meal", "meat_grill", "meat_stirfry", "tofu_meal", "egg_meal", "vegetable_meal", "raw_fish"} and has_starch:
            main = (12, 25 if has_protein else 6, 16 if fat_heavy else 12)
        elif name == "플레인요거트":
            main = (9, 8, 5)
        else:
            main = (65, 10, 10) if "밥" in name else (45, 10, 10)
        components = [{"name": name, "grams": main}]
        components += [{"name": side, "grams": SIDES[side]} for side in sides]
    else:
        # Existing composite/whole meals retain their representative energy.
        # These ratios are editorial defaults, NOT a measured nutrient database.
        p = .22 if has_protein else .10
        f = .40 if fat_heavy else .27
        components = [{"name": name, "grams": ((1-p-f)*base_kcal/4, p*base_kcal/4, f*base_kcal/9)}]
    grams = tuple(round(sum(item["grams"][i] for item in components), 2) for i in range(3))
    return {"source_kind": "editorial_estimate", "verified_recipe": False,
            "model_version": "whole-meal-estimate-v1", "estimated_kcal": energy(grams),
            "carbohydrate_g": grams[0], "protein_g": grams[1], "fat_g": grams[2],
            "has_vegetables": has_vegetables or any(w in serving for w in VEGETABLE_WORDS),
            "components": [{"name": item["name"], "carbohydrate_g": round(item["grams"][0],2),
                            "protein_g": round(item["grams"][1],2), "fat_g": round(item["grams"][2],2)} for item in components]}


def macro_summary(totals):
    kcal = energy(totals)
    ratios = [round(g * factor / kcal * 100, 1) if kcal else 0 for g, factor in zip(totals, (4, 4, 9))]
    # Broad product review bands, not age-specific clinical requirements.
    limits = ((45, 65), (15, 30), (20, 35))
    deviation = sum(max(low-ratio, 0, ratio-high) for ratio, (low, high) in zip(ratios, limits))
    return {"carbohydrate_g": round(totals[0],2), "protein_g": round(totals[1],2),
            "fat_g": round(totals[2],2), "energy_percent": dict(zip(("carbohydrate", "protein", "fat"),ratios)),
            "within_editorial_review_band": deviation == 0, "deviation": round(deviation,1),
            "source_kind": "editorial_estimate", "not_personal_requirement": True}
