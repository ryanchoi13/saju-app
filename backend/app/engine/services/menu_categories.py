"""Culinary categories and editorial frequency priors, not survey percentages.

Frequency applies once per category. Individual variants cannot acquire the
category's popularity just because their name contains a common food word.
"""

# Category priors: frequency and accessibility on a 1..5 editorial scale.
PROFILES = {
    "western_soup": (3, 4), "smoothie": (3, 4),
    "toast": (4, 5), "sandwich": (4, 5), "bread": (3, 4),
    "breakfast_bowl": (3, 4), "drink": (2, 4), "snack": (2, 4),
    "bibimbap": (4, 5), "rice_bowl": (3, 4), "rice_meal": (4, 5),
    "soup": (5, 5), "stew": (5, 5), "gukbap": (4, 5),
    "porridge": (3, 4), "hotpot": (3, 4), "curry": (4, 5),
    "noodles": (4, 5), "chinese_noodles": (4, 5), "pasta": (3, 4),
    "fried_rice": (4, 5), "sushi": (3, 4), "raw_fish": (2, 3),
    "fish_meal": (3, 4), "seafood_meal": (3, 3),
    "meat_stirfry": (4, 5), "meat_grill": (3, 4),
    "chicken": (4, 5), "burger": (3, 5), "pizza": (3, 4),
    "cutlet": (4, 5), "salad": (3, 4), "poke": (3, 3),
    "wrap": (3, 3), "egg_meal": (4, 5), "tofu_meal": (4, 4),
    "vegetable_meal": (3, 4), "other": (2, 3),
}


def menu_category(name: str) -> str:
    from .menu_catalog_revision import CATEGORIES
    if name in CATEGORIES:
        return CATEGORIES[name]
    overrides = {"육개장": "soup", "매운 닭개장": "soup", "감자옹심이": "noodles",
                 "고구마그라탱": "vegetable_meal", "연근조림 정식": "vegetable_meal",
                 "깐풍기": "chicken", "유자차와 백설기": "snack",
                 "메밀전병": "snack", "도토리묵사발": "vegetable_meal",
                 "해파리냉채": "seafood_meal", "똠얌꿍": "soup",
                 "오코노미야키": "snack"}
    if name in overrides:
        return overrides[name]
    for category, words in (
        ("western_soup", ("수프", "스프")),
        ("smoothie", ("스무디",)),
        ("toast", ("토스트",)), ("sandwich", ("샌드위치",)),
        ("poke", ("포케",)), ("wrap", ("월남쌈", "치킨랩", "양배추쌈")),
        ("pasta", ("파스타", "알리오 올리오", "라자냐", "뇨키", "리조또")),
        ("burger", ("버거",)), ("pizza", ("피자",)),
        ("cutlet", ("돈가스", "돈카츠", "생선가스")),
        ("raw_fish", ("광어회", "타다키")),
        ("sushi", ("초밥",)), ("rice_bowl", ("덮밥", "오차즈케")),
        ("bibimbap", ("비빔밥",)), ("gukbap", ("국밥", "설렁탕", "곰탕", "해장국")),
        ("chinese_noodles", ("짜장면", "짬뽕")),
        ("noodles", ("국수", "칼국수", "라면", "짜파게티", "우동", "라멘", "냉면", "모밀", "소바", "수제비", "팟타이", "분짜")),
        ("fried_rice", ("볶음밥", "오므라이스", "필라프", "잡채밥", "빠에야")),
        ("curry", ("카레",)), ("hotpot", ("전골", "샤브샤브", "편백찜", "나베", "스키야키", "닭한마리")),
        ("stew", ("찌개", "청국장")),
        ("soup", ("국", "탕", "수프", "스프")),
        ("porridge", ("죽", "누룽지")),
        ("chicken", ("후라이드치킨", "양념치킨", "간장치킨", "탄두리치킨")),
        ("meat_stirfry", ("제육", "불고기", "닭갈비", "숙주볶음", "닭고기 버섯볶음")),
        ("fish_meal", ("고등어", "삼치", "생선", "갈치", "꽁치", "연어", "코다리")),
        ("seafood_meal", ("오징어", "새우", "주꾸미", "낙지", "문어", "해물", "조개", "아귀")),
        ("salad", ("샐러드",)),
        ("meat_grill", ("삼겹살", "수육", "보쌈", "스테이크", "닭다리", "닭가슴살", "훈제", "소고기편채")),
        ("egg_meal", ("달걀", "계란", "에그", "오믈렛")),
        ("tofu_meal", ("두부",)),
        ("breakfast_bowl", ("요거트", "요구르트", "그래놀라", "오트밀")),
        ("bread", ("빵", "베이글", "팬케이크", "크루아상", "파니니")),
        ("drink", ("주스", "스무디", "두유")),
        ("rice_meal", ("밥",)),
        ("snack", ("떡", "과자", "타르트", "화채", "닭꼬치", "핫도그")),
        ("vegetable_meal", ("채소", "가지", "나물", "잡채", "배추전", "양배추")),
    ):
        if any(word in name for word in words):
            return category
    return "other"


def cooking_style(name: str) -> str:
    if any(w in name for w in ("회", "초밥", "타다키")):
        return "raw_or_sushi"
    for style, words in (("fried", ("후라이드", "양념치킨", "돈가스", "돈카츠", "튀김")),
                         ("grilled", ("구이", "스테이크", "삼겹살")),
                         ("braised", ("조림",)), ("steamed", ("찜", "수육", "보쌈")),
                         ("stirfried", ("볶음", "제육", "불고기")),
                         ("soup", ("국", "탕", "찌개", "전골"))):
        if any(word in name for word in words):
            return style
    return "mixed"
