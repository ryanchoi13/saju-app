"""Verified survey anchors, separate from editorial ranking transforms.

KHIDI 2023 national frequent-food table. Percent = survey-day consumption
respondent proportion, NOT meal share, restaurant market share or preference.
No summing of overlapping rates; no substring inheritance to unusual variants.
"""
SOURCE = "https://www.khidi.or.kr/kps/dhraStat/result15?menuId=MENU01669&year=2023"
# Curated explicit mappings: dish -> (survey food label, percent, matching status).
ANCHORS = {
    "라면": ("라면", 14.85, "exact"),
    "김치찌개": ("김치찌개", 9.63, "exact"),
    "된장찌개": ("된장찌개", 8.98, "exact"),
    "소고기미역국": ("미역국", 9.25, "broader_food_proxy"),
    "제육볶음": ("돼지고기볶음", 6.58, "broader_food_proxy"),
    "삼겹살구이": ("삼겹살구이", 6.39, "exact"),
    "소고기불고기": ("불고기", 4.60, "broader_food_proxy"),
    "야채비빔밥": ("비빔밥", 3.92, "broader_food_proxy"),
    "돌솥비빔밥": ("비빔밥", 3.92, "broader_food_proxy"),
    "된장국과 밥·달걀말이": ("된장국", 14.58, "main_dish_proxy"),
    "콩나물국과 밥·두부구이": ("콩나물국", 5.68, "main_dish_proxy"),
    "후라이드치킨": ("닭튀김/강정", 7.93, "broader_food_proxy"),
    "양념치킨": ("닭튀김/강정", 7.93, "broader_food_proxy"),
    "고등어구이": ("고등어구이", 3.15, "exact"),
}


def frequency_evidence(name):
    anchor = ANCHORS.get(name)
    if not anchor:
        return {"source_kind": "editorial_prior", "observed_percent": None}
    label, rate, match = anchor
    return {"source_kind": "survey_anchor", "survey_year": 2023,
            "survey_food": label, "observed_percent": rate, "match": match,
            "metric": "survey_day_consumption_proportion", "source_url": SOURCE,
            "score_transform": "editorial_0_to_2_bonus"}


def frequency_bonus(name):
    anchor = ANCHORS.get(name)
    if not anchor:
        return 0
    # Small corroboration bonus; raw respondent percentages aren't probabilities.
    return 2 if anchor[1] >= 6 else 1
