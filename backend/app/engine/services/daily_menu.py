"""Curated daily meal pool and deterministic lifestyle translation rules."""

from __future__ import annotations

import hashlib
import math
from collections import Counter
from dataclasses import dataclass
from datetime import date
from app.engine.services.menu_categories import PROFILES, menu_category, cooking_style
from app.engine.services.meal_nutrition import serving_suggestion, meal_estimate, macro_summary
from app.engine.services.menu_frequency import frequency_evidence, frequency_bonus
from app.engine.services.menu_demographics import demographic_evidence
from app.engine.services.meal_feedback import preference_bonus
from app.engine.services.menu_frequency_review import REVIEWED_POPULARITY


MENU_POOL_VERSION = "daily-menu-pool-v3"
DIET_MENU_POOL_VERSION = "diet-menu-pool-v1"


@dataclass(frozen=True)
class MenuCandidate:
    name: str
    element: str
    group: str
    seasons: frozenset[str]
    periods: frozenset[str]
    tags: frozenset[str]
    ingredient: str
    cuisine: str
    familiarity: int
    estimated_kcal: int
    macro_profile: str
    has_protein: bool
    has_vegetables: bool
    carb_heavy: bool
    fat_heavy: bool
    popularity: int
    accessibility: int
    age_groups: frozenset[str]
    nutrition_estimate: dict | None = None


_INGREDIENT_RULES = (
    ("beef", ("소고기", "양지", "차돌", "불고기", "설렁탕", "곰탕", "스테이크")),
    ("pork", ("돼지", "제육", "삼겹살", "보쌈", "수육", "돈가스", "돈카츠", "감자탕", "뼈해장국", "순대국밥")),
    ("chicken", ("닭", "치킨", "삼계탕")),
    ("seafood", ("해물", "해산물", "해초", "새우", "오징어", "주꾸미", "낙지", "조개", "홍합", "바지락", "굴", "꼬막", "문어", "아귀", "대구", "복국", "생선", "연어", "참치", "광어", "초밥", "회", "고등어", "갈치", "꽁치", "장어", "매생이", "재첩", "톳")),
    ("tofu_bean", ("두부", "콩", "된장", "청국장", "비지", "두유")),
    ("egg_dairy", ("계란", "달걀", "에그", "치즈", "요거트", "우유", "크림")),
    ("noodle_wheat", ("라면", "짜파게티", "국수", "분짜", "파스타", "우동", "칼국수", "수제비", "베이글", "빵", "토스트", "샌드위치", "피자", "라자냐", "크루아상", "팬케이크")),
    ("rice_grain", ("밥", "죽", "솥밥", "김밥", "떡", "오트밀", "그래놀라")),
    ("root", ("감자", "고구마", "단호박", "연근", "우엉", "토란")),
    ("vegetable", ("채소", "나물", "샐러드", "아보카도", "시금치", "청경채", "가지", "오이", "배추", "무생채")),
    ("mushroom", ("버섯",)),
    ("fruit", ("과일", "사과", "키위", "유자", "자몽")),
)

_LOW_FAMILIARITY = {
    "해산물 빠에야", "스키야키", "오뎅나베", "돈코츠라멘",
    "감자뇨키", "똠얌꿍", "참치타다키",
}

_HIGH_FAMILIARITY = {
    "라면", "짜파게티", "비빔국수", "후라이드치킨", "양념치킨", "간장치킨",
    "치킨버거", "햄버거", "불고기버거", "치즈버거", "새우버거",
    "제육볶음", "된장찌개", "김치찌개", "감자탕", "뼈해장국", "돼지국밥",
    "순대국밥", "경양식 돈가스", "소고기불고기", "오징어뭇국", "해물찜", "조개구이",
}

_YOUTH_WORDS = ("버거", "치킨", "돈가스", "돈카츠", "카레", "떡볶이", "파스타", "피자", "토스트", "샌드위치")
_MATURE_WORDS = ("국", "찌개", "탕", "밥", "나물", "생선", "두부", "콩", "죽", "수육", "보쌈")
_COMMON_WORDS = (
    "김치찌개", "된장찌개", "비빔밥", "불고기", "제육", "돈가스", "치킨",
    "카레", "짜장", "짬뽕", "국수", "칼국수", "라면", "파스타", "버거",
    "김밥", "국밥", "냉면", "초밥", "샌드위치", "토스트",
)


def age_group_for(age: int | None) -> str | None:
    if age is None:
        return None
    if age <= 12:
        return "child"
    if age <= 19:
        return "teen"
    if age <= 34:
        return "young_adult"
    if age <= 54:
        return "middle_adult"
    return "mature_adult"


_CONSUMER_OVERRIDES = {
    "짜장면": (5,5), "마라탕": (2,3), "탕수육": (4,5),
    "소고기불고기": (5,5), "순대국밥": (4,5), "돼지국밥": (4,5),
    "해물칼국수": (4,5), "잔치국수": (4,5), "소고기무국": (4,5),
    "콩나물국": (4, 5), "된장국": (4, 5), "시래기국": (3, 4), "김치국": (3, 4), "동태국": (3, 4),
    "김치볶음밥": (4, 5), "새우볶음밥": (4, 5), "계란볶음밥": (4, 5), "해물볶음밥": (3, 4), "햄볶음밥": (3, 4),
    "닭죽": (3, 4), "소고기죽": (3, 4), "야채죽": (3, 4),
    "양송이스프": (3, 4), "감자수프": (3, 4), "야채수프": (3, 4),
    "간장계란밥": (4, 5),
    "된장국과 밥·달걀말이": (5, 5), "콩나물국과 밥·두부구이": (4, 5),
    "누룽지·달걀찜·김": (3, 4), "찐만두·달걀국": (3, 4),
    "삼겹살구이": (4, 5),
    # Editorial tiers, not measured population percentages. Specific dishes must
    # override broad words such as chicken, rice bowl or toast.
    "탄두리치킨": (1, 2), "굴국밥": (1, 2), "꼬막비빔밥": (2, 2),
    "해초비빔밥": (1, 2), "무생채비빔밥": (2, 3),
    "새싹채소 비빔밥": (2, 3), "봄나물 비빔밥": (3, 3),
    "강된장비빔밥": (3, 3), "야채비빔밥": (5, 5),
    "돌솥비빔밥": (5, 5), "육회비빔밥": (3, 3),
    "참치회덮밥": (3, 4), "장어덮밥": (2, 3),
    "햄치즈 토스트": (5, 5), "햄에그 토스트": (5, 5),
    "햄치즈양배추 토스트": (5, 5), "길거리 토스트": (5, 5),
    "아보카도 토스트": (3, 3), "콜슬로 샌드위치": (2, 3),
    "루꼴라 샌드위치": (3, 3), "치킨수프": (2, 3),
    "치킨크림리조또": (3, 3), "나박김치국수": (1, 2),
    "백김치국수": (2, 2), "재첩국과 따뜻한 쌀밥": (2, 2),
    "매생이국": (2, 2), "토란국": (2, 2), "검은깨죽": (2, 3),
}


def _consumer_metadata(name: str, cuisine: str, familiarity: int) -> tuple[int, int, frozenset[str]]:
    """Editorial base priors; separately sourced survey anchors add a small bonus."""

    # Unknown variants start below their category, irrespective of nationality.
    base_popularity, accessibility = PROFILES[menu_category(name)]
    popularity = max(1, base_popularity - 1)
    if name in _HIGH_FAMILIARITY:
        popularity = base_popularity
    if name in _LOW_FAMILIARITY:
        popularity, accessibility = 1, 2
    popularity, accessibility = _CONSUMER_OVERRIDES.get(name, (popularity, accessibility))
    popularity = REVIEWED_POPULARITY.get(name, popularity)
    groups = {"young_adult", "middle_adult"}
    if any(word in name for word in _YOUTH_WORDS):
        groups.update({"child", "teen"})
    if any(word in name for word in _MATURE_WORDS) and cuisine == "korean":
        groups.add("mature_adult")
    if popularity >= 5:
        groups.update({"teen", "mature_adult"})
    return popularity, accessibility, frozenset(groups)

_CUISINE_OVERRIDES = {
    "분짜": "southeast_asian", "어향가지": "chinese", "짜장면": "chinese",
    "탕수육": "chinese", "깐풍기": "chinese", "오코노미야키": "japanese",
    "모둠초밥": "japanese", "연어초밥": "japanese", "광어회": "japanese",
    "유부초밥": "japanese", "일본식 돈카츠": "japanese",
    "경양식 돈가스": "western", "알리오 올리오": "western",
}
_INGREDIENT_OVERRIDES = {
    "육회비빔밥": "beef", "야채비빔밥": "vegetable",
    "두부스테이크": "tofu_bean", "연어스테이크": "seafood",
    "짜장면": "noodle_wheat", "탕수육": "pork", "깐풍기": "chicken",
    "어향가지": "vegetable", "오코노미야키": "noodle_wheat",
}

# Group defaults express the dish's energy direction. Meal-time suitability is
# intentionally overridden per dish so breakfast and snack never blur together.
_PERIOD_OVERRIDES = {
    "닭죽": "breakfast lunch", "소고기죽": "breakfast lunch", "야채죽": "breakfast lunch",
    "단호박죽": "breakfast snack", "감자수프": "breakfast lunch",
    "간장계란밥": "breakfast lunch", "채소 듬뿍 아귀찜": "dinner",
    "된장국과 밥·달걀말이": "breakfast lunch dinner",
    "콩나물국과 밥·두부구이": "breakfast lunch dinner",
    "누룽지·달걀찜·김": "breakfast",
    "찐만두·달걀국": "lunch dinner",
    "삼겹살구이": "dinner",
    "고추장삼겹살": "dinner",
    "그린 스무디": "breakfast snack", "사과 셀러리 주스": "breakfast snack",
    "키위 요거트": "breakfast snack", "말차 오트밀": "breakfast",
    "아보카도 토스트": "breakfast", "BLT 샌드위치": "breakfast lunch",
    "루꼴라 샌드위치": "breakfast lunch", "햄에그 샌드위치": "breakfast lunch",
    "에그 샐러드 샌드위치": "breakfast lunch", "과일 그래놀라 볼": "breakfast snack",
    "쑥떡과 차": "snack", "바질 토마토 파니니": "breakfast lunch",
    "토마토 에그스크램블": "breakfast", "햄치즈 토스트": "breakfast snack",
    "햄치즈양배추 토스트": "breakfast snack", "길거리 토스트": "breakfast snack",
    "떡볶이": "snack", "닭꼬치": "snack", "핫도그": "snack",
    "생강차와 구운 떡": "snack", "계피차와 호두빵": "snack",
    "자몽차와 에그타르트": "snack", "오트밀죽": "breakfast",
    "딸기잼 토스트": "breakfast snack", "감자샐러드 샌드위치": "breakfast lunch",
    "단호박샌드위치": "breakfast lunch", "통밀베이글": "breakfast snack",
    "버터 크루아상": "breakfast snack", "바나나 팬케이크": "breakfast snack",
    "프렌치토스트": "breakfast snack", "그래놀라 요거트": "breakfast snack",
    "콘수프와 모닝빵": "breakfast", "배도라지차와 쌀과자": "snack",
    "유자차와 백설기": "snack", "흰콩두유": "breakfast snack",
    "플레인요거트": "breakfast snack", "치즈버거": "lunch dinner",
    "치즈샌드위치": "breakfast lunch", "달걀샌드위치": "breakfast lunch",
    "소금빵": "breakfast snack", "양송이스프": "breakfast lunch",
    "야채수프": "breakfast lunch",
    "새우버거": "lunch dinner", "검은콩밥": "lunch dinner",
    "흑미밥": "lunch dinner", "검은깨죽": "breakfast",
    "들깨미역국": "breakfast lunch dinner",
    "온메밀소바": "lunch dinner", "메밀전병": "snack",
    "김국과 따뜻한 쌀밥": "breakfast lunch dinner", "톳밥": "lunch dinner",
    "검은콩국수": "lunch dinner", "과일화채": "snack",
    "김밥": "lunch dinner snack", "문어숙회정식": "dinner",
    "삶은 계란과 토스트": "breakfast", "계란프라이와 토스트": "breakfast",
    "햄에그 토스트": "breakfast", "간장계란밥": "breakfast",
    "콩나물국밥": "breakfast lunch dinner", "북엇국": "breakfast lunch dinner",
    "황태해장국": "breakfast lunch dinner", "오징어뭇국": "breakfast lunch dinner",
    "맑은 순두부국": "breakfast lunch dinner", "소고기미역국": "breakfast lunch dinner",
    "매생이국": "lunch dinner", "굴국밥": "lunch dinner",
    "재첩국과 따뜻한 쌀밥": "breakfast lunch dinner",
}

def _periods_for(name: str, default_periods: str) -> frozenset[str]:
    return frozenset(_PERIOD_OVERRIDES.get(name, default_periods).split())

_INGREDIENT_KO = {
    "beef": "소고기",
    "pork": "돼지고기",
    "chicken": "닭고기",
    "seafood": "생선·해산물",
    "tofu_bean": "두부·콩",
    "egg_dairy": "달걀·유제품",
    "noodle_wheat": "면·밀가루",
    "rice_grain": "쌀·곡물",
    "root": "뿌리채소",
    "vegetable": "채소·나물",
    "mushroom": "버섯",
    "fruit": "과일",
    "mixed": "균형 재료",
}


def _ingredient_for(name: str) -> str:
    if name in _INGREDIENT_OVERRIDES:
        return _INGREDIENT_OVERRIDES[name]
    for ingredient, keywords in _INGREDIENT_RULES:
        if any(keyword in name for keyword in keywords):
            return ingredient
    return "mixed"


def _cuisine_for(name: str, group: str) -> str:
    if name in _CUISINE_OVERRIDES:
        return _CUISINE_OVERRIDES[name]
    if any(word in name for word in (
        "파스타", "피자", "리조또", "샐러드", "스테이크", "버거",
        "토스트", "샌드위치", "베이글", "크루아상", "팬케이크",
        "오트밀", "요거트", "그래놀라", "콘수프", "양송이스프",
    )):
        return "western"
    if any(word in name for word in ("라멘", "우동", "오차즈케", "타다키", "스키야키", "나베", "초밥")):
        return "japanese"
    if any(word in name for word in ("쌀국수", "팟타이", "똠얌꿍", "월남쌈")):
        return "southeast_asian"
    if any(word in name for word in ("짬뽕", "유산슬", "중화", "짜장", "어향", "탕수육", "깐풍기")):
        return "chinese"
    return "korean"


_CARB_KEYWORDS = (
    "밥", "죽", "면", "국수", "라멘", "우동", "칼국수", "수제비",
    "파스타", "피자", "리조또", "빵", "토스트", "샌드위치", "베이글",
    "라자냐", "팬케이크", "그래놀라", "오트밀", "떡", "초밥", "덮밥",
)
_CARB_DENSE_KEYWORDS = (
    "라면", "짜파게티", "면", "국수", "라멘", "우동", "칼국수", "수제비",
    "파스타", "피자", "빵", "토스트", "샌드위치", "베이글", "라자냐", "팬케이크",
)
_PROTEIN_KEYWORDS = (
    "육회",
    "소고기", "양지", "차돌", "불고기", "스테이크", "돼지고기", "제육",
    "삼겹살", "수육", "보쌈", "돈가스", "돈카츠", "닭", "치킨", "오리",
    "생선", "연어", "참치", "광어", "고등어", "갈치", "꽁치", "장어",
    "해물", "해산물", "새우", "오징어", "주꾸미", "낙지", "조개", "굴",
    "꼬막", "문어", "아귀", "대구", "동태", "두부", "콩", "된장", "청국장",
    "계란", "달걀", "에그", "요거트", "우유", "치즈", "햄", "BLT",
)
_VEGETABLE_KEYWORDS = (
    "채소", "나물", "샐러드", "비빔밥", "숙주", "양배추", "버섯", "시금치",
    "가지", "청경채", "오이", "배추", "무생채", "아보카도", "케일", "당근",
    "연근", "우엉", "단호박", "고구마", "감자", "쌈",
)
_FAT_DENSE_KEYWORDS = (
    "후라이드", "양념치킨", "간장치킨", "피자", "크림", "그라탱",
    "돈가스", "돈카츠", "탕수육", "깐풍기", "삼겹살", "족발", "햄버거",
    "버거", "크루아상",
)

_KCAL_OVERRIDES = {
    "후라이드치킨": 900, "양념치킨": 950, "간장치킨": 900,
    "화덕피자": 850, "페퍼로니피자": 900, "고구마피자": 900,
    "햄버거": 650, "치즈버거": 700, "불고기버거": 650,
    "치킨버거": 700, "새우버거": 650, "떡볶이": 550,
    "라면": 500, "짜파게티": 600, "비빔국수": 520,
    "계란후라이와 통밀토스트": 400, "간장계란밥": 480,
}


def _nutrition_for(name: str, group: str, periods: frozenset[str]) -> tuple[int, str, bool, bool, bool, bool, dict]:
    """Return conservative representative-meal metadata, not a serving prescription."""

    has_carb = any(keyword in name for keyword in _CARB_KEYWORDS)
    has_protein = any(keyword in name for keyword in _PROTEIN_KEYWORDS)
    has_vegetables = any(keyword in name for keyword in _VEGETABLE_KEYWORDS)
    carb_heavy = any(keyword in name for keyword in _CARB_DENSE_KEYWORDS)
    fat_heavy = any(keyword in name for keyword in _FAT_DENSE_KEYWORDS)

    if has_protein and (has_carb or has_vegetables):
        macro_profile = "balanced"
    elif has_protein:
        macro_profile = "protein_forward"
    elif has_carb:
        macro_profile = "carb_forward"
    else:
        macro_profile = "light_mixed"

    if name in _KCAL_OVERRIDES:
        kcal = _KCAL_OVERRIDES[name]
    elif any(word in name for word in ("피자", "그라탱", "크림", "돈가스", "돈카츠", "탕수육", "깐풍기")):
        kcal = 750
    elif any(word in name for word in ("파스타", "리조또", "볶음밥", "덮밥", "국밥", "짜장면", "짬뽕")):
        kcal = 650
    elif any(word in name for word in ("국수", "라멘", "우동", "칼국수", "수제비", "막국수", "냉면", "쌀국수")):
        kcal = 550
    elif any(word in name for word in ("비빔밥", "정식", "솥밥", "카레", "오므라이스", "초밥")):
        kcal = 600
    elif any(word in name for word in ("샌드위치", "토스트", "베이글", "팬케이크", "오차즈케")):
        kcal = 420
    elif any(word in name for word in ("샐러드", "포케", "월남쌈", "샤브샤브", "편백찜")):
        kcal = 500
    elif any(word in name for word in ("구이", "볶음", "스테이크", "수육", "보쌈", "찜")):
        kcal = 550
    elif any(word in name for word in ("찌개", "탕", "국")):
        kcal = 500
    elif "breakfast" in periods:
        kcal = 350
    else:
        kcal = 500
    estimate = meal_estimate(name, kcal, has_protein, has_vegetables, fat_heavy)
    return round(estimate["estimated_kcal"]), macro_profile, estimate["protein_g"] >= 15, estimate["has_vegetables"], carb_heavy, fat_heavy, estimate


def _group(
    element: str,
    group: str,
    seasons: str,
    periods: str,
    tags: str,
    names: str,
) -> list[MenuCandidate]:
    candidates = []
    for name in (item.strip() for item in names.split("|") if item.strip()):
        candidate_periods = _periods_for(name, periods)
        nutrition = _nutrition_for(name, group, candidate_periods)
        cuisine = _cuisine_for(name, group)
        familiarity = 4 if name in _HIGH_FAMILIARITY else 2 if name in _LOW_FAMILIARITY else 3
        consumer = _consumer_metadata(name, cuisine, familiarity)
        candidates.append(MenuCandidate(
            name=name.strip(),
            element=element,
            group=group,
            seasons=(frozenset({"winter", "spring"}) if name in {"꼬막비빔밥", "굴국밥"}
                     else frozenset({"spring", "summer", "autumn", "winter"})
                     if name in {"야채비빔밥", "돌솥비빔밥", "육회비빔밥"}
                     else frozenset(seasons.split())),
            periods=candidate_periods,
            tags=frozenset(tags.split()),
            ingredient=_ingredient_for(name.strip()),
            cuisine=cuisine,
            familiarity=familiarity,
            nutrition_estimate=nutrition[6],
            estimated_kcal=nutrition[0],
            macro_profile=nutrition[1],
            has_protein=nutrition[2],
            has_vegetables=nutrition[3],
            carb_heavy=nutrition[4],
            fat_heavy=nutrition[5],
            popularity=consumer[0],
            accessibility=consumer[1],
            age_groups=consumer[2],
        ))
    return candidates


MENU_POOL = tuple(
    _group(
        "木", "wood_fresh", "spring summer", "lunch dinner", "fresh light cool",
        "야채비빔밥|돌솥비빔밥|육회비빔밥|봄나물 비빔밥|새싹채소 비빔밥|닭가슴살 그린샐러드|연두부 채소샐러드|아보카도 샐러드|시저샐러드|그릭샐러드|카프레제 샐러드|월남쌈|연어 포케",
    )
    + _group(
        "木", "wood_noodle", "spring summer autumn", "lunch dinner", "fresh light create",
        "바질페스토 파스타|들기름 막국수|메밀 비빔국수|양지 소고기 쌀국수|잔치국수|해물칼국수|비빔국수|루꼴라 파스타|분짜|짜파게티",
    )
    + _group(
        "木", "wood_warm", "autumn winter spring", "lunch dinner", "balanced warm organize",
        "소고기카레|버섯덮밥|가지덮밥|청경채볶음과 두부구이|채소볶음밥|두부채소볶음|버섯리조또|시금치오믈렛|시금치라자냐|잡채",
    )
    + _group(
        "木", "wood_breakfast", "spring summer", "breakfast snack", "fresh light record",
        "그린 스무디|사과 셀러리 주스|키위 요거트|말차 오트밀|아보카도 토스트|BLT 샌드위치|루꼴라 샌드위치|햄에그 샌드위치|에그 샐러드 샌드위치|과일 그래놀라 볼|쑥떡과 차|바질 토마토 파니니",
    )
    + _group(
        "木", "wood_tangy", "summer autumn", "lunch dinner", "fresh cool mediate",
        "열무비빔밥|김치말이국수|두부김치|오이냉국 정식|초계국수|유부초밥|닭다리살구이|소고기불고기|불고기버거|치킨버거",
    )
    + _group(
        "火", "fire_spicy_soup", "autumn winter", "lunch dinner", "warm hearty support",
        "육개장|순두부찌개|김치찌개|부대찌개|해물짬뽕|마라탕|매운 닭개장|고추장찌개|알탕|매운탕|매운 어묵탕",
    )
    + _group(
        "火", "fire_grill", "spring summer autumn winter", "lunch dinner", "warm create move",
        "닭갈비|제육볶음|주꾸미볶음|오징어볶음|오징어제육볶음|고추장삼겹살|탄두리치킨|후라이드치킨|화덕피자|그릴드 스테이크|양념치킨",
    )
    + _group(
        "火", "fire_red_meal", "spring summer autumn winter", "lunch dinner", "warm create organize",
        "토마토파스타|알리오 올리오|로제파스타|김치볶음밥|낙지볶음밥|매콤한 치킨카레|간장치킨|페퍼로니피자|해산물 빠에야|매운 소고기 쌀국수",
    )
    + _group(
        "火", "fire_snack", "autumn winter spring", "breakfast snack", "warm move record",
        "토마토 에그스크램블|햄치즈 토스트|햄에그 토스트|햄치즈양배추 토스트|길거리 토스트|삶은 계란과 토스트|계란프라이와 토스트|떡볶이|닭꼬치|핫도그|생강차와 구운 떡|계피차와 호두빵|자몽차와 에그타르트",
    )
    + _group(
        "火", "fire_gentle_warmth", "autumn winter", "lunch dinner", "warm balanced mediate",
        "닭한마리|삼계탕|소고기 샤브샤브|스키야키|버섯전골|오뎅나베|돈코츠라멘|유부우동|치킨수프|라면",
    )
    + _group(
        "土", "earth_rice", "spring summer autumn winter", "lunch dinner", "balanced hearty organize",
        "영양솥밥|버섯솥밥|곤드레밥|전복솥밥|오곡밥 정식|현미밥 정식|콩밥|콩나물밥|시래기밥|밤밥|연근밥|된장국과 밥·달걀말이|콩나물국과 밥·두부구이|누룽지·달걀찜·김|찐만두·달걀국",
    )
    + _group(
        "土", "earth_root", "autumn winter", "lunch dinner", "warm hearty support",
        "감자옹심이|감자수제비|고구마그라탱|단호박죽|팥죽|야채카레|우엉잡채|연근조림 정식|토란국|햄버거",
    )
    + _group(
        "土", "earth_comfort", "spring autumn winter", "lunch dinner", "balanced warm stabilize",
        "된장찌개|청국장|보리밥 정식|강된장비빔밥|들깨수제비|닭칼국수|닭죽|소고기죽|야채죽|콩비지찌개",
    )
    + _group(
        "土", "earth_breakfast", "spring summer autumn winter", "breakfast snack", "balanced support pace",
        "오트밀죽|딸기잼 토스트|감자샐러드 샌드위치|단호박샌드위치|통밀베이글|버터 크루아상|바나나 팬케이크|프렌치토스트|그래놀라 요거트|콘수프와 모닝빵",
    )
    + _group(
        "土", "earth_global", "autumn winter spring", "lunch dinner", "hearty create stabilize",
        "감자뇨키|버섯크림리조또|고구마피자|감자탕|뼈해장국|카레라이스|오므라이스|간장계란밥|돼지국밥|순대국밥|경양식 돈가스|일본식 돈카츠",
    )
    + _group(
        "金", "metal_clear_soup", "autumn winter spring", "lunch dinner", "warm clear support",
        "설렁탕|소고기곰탕|닭곰탕|떡국|만둣국|콩나물국밥|북엇국|황태해장국|오징어뭇국|맑은 순두부국|콩나물국|김치국|된장국|시래기국|동태국",
    )
    + _group(
        "金", "metal_crisp", "spring summer autumn", "lunch dinner", "fresh light organize",
        "무밥|소고기무국|무생채비빔밥|도토리묵밥|메밀묵밥|배추전|양배추롤|콜슬로 샌드위치|조개구이|백김치국수",
    )
    + _group(
        "金", "metal_simple_protein", "spring summer autumn winter", "lunch dinner", "clear balanced protect",
        "돼지고기수육|보쌈 정식|편백찜|닭가슴살구이|흰살생선구이|두부스테이크|계란찜과 밥·채소 반찬|새우소금구이|소고기편채|오리훈제샐러드|삼겹살구이",
    )
    + _group(
        "金", "metal_clean_meal", "spring summer autumn winter", "lunch dinner", "clear create mediate",
        "어향가지|짜장면|탕수육|깐풍기|봉골레파스타|버섯크림파스타|치킨크림리조또|새우필라프|유산슬덮밥|중화잡채밥|닭고기쌀국수|하얀짬뽕|차돌숙주볶음밥|새우볶음밥|계란볶음밥|해물볶음밥|햄볶음밥",
    )
    + _group(
        "金", "metal_breakfast", "spring summer autumn winter", "breakfast snack", "light clear record",
        "배도라지차와 쌀과자|유자차와 백설기|흰콩두유|플레인요거트|치즈버거|치즈샌드위치|달걀샌드위치|소금빵|양송이스프|야채수프|감자수프|새우버거",
    )
    + _group(
        "水", "water_sea_soup", "autumn winter spring", "lunch dinner", "broth warm moisten",
        "소고기미역국|해물탕|매생이국|굴국밥|대구탕|복국|재첩국과 따뜻한 쌀밥|홍합탕|바지락칼국수|해물순두부찌개",
    )
    + _group(
        "水", "water_fish_meal", "spring summer autumn winter", "lunch dinner", "balanced protect support",
        "연어덮밥|참치회덮밥|장어덮밥|고등어구이와 채소 반찬|갈치조림과 나물 반찬|꽁치김치조림|채소 듬뿍 아귀찜|꼬막비빔밥|해초비빔밥|문어숙회정식",
    )
    + _group(
        "水", "water_black_food", "autumn winter spring", "lunch dinner", "balanced moisten record",
        "검은콩밥|흑미밥|검은깨죽|들깨미역국|김밥|온메밀소바|메밀전병|김국과 따뜻한 쌀밥|톳밥|검은콩국수",
    )
    + _group(
        "水", "water_cool_light", "spring summer", "lunch dinner snack", "cool light moisten",
        "물냉면|서리태콩국수|냉우동|연어 오차즈케|연두부국|도토리묵사발|해파리냉채|과일화채|나박김치국수|냉모밀",
    )
    + _group(
        "水", "water_global", "spring summer autumn winter", "lunch dinner", "broth create move",
        "해산물파스타|해산물리조또|생선가스|연어스테이크|참치타다키|새우팟타이|해물볶음우동|똠얌꿍|해물찜|조개찜|모둠초밥|연어초밥|광어회|오코노미야키",
    )
)


from .menu_catalog_revision import apply_catalog_revision
MENU_POOL = apply_catalog_revision(MENU_POOL, _group)


# The diet pool is intentionally separate from the general pool.  These are
# complete, familiar meals rather than smaller portions of high-energy dishes.
# Calories and exact serving sizes are deliberately deferred until verified
# nutrition data is connected.
def _diet_group(
    element: str,
    group: str,
    periods: str,
    tags: str,
    ingredient: str,
    cuisine: str,
    names: str,
) -> list[MenuCandidate]:
    candidates = []
    for name in (item.strip() for item in names.split("|") if item.strip()):
        candidate_periods = frozenset(periods.split())
        nutrition = _nutrition_for(name, group, candidate_periods)
        consumer = _consumer_metadata(name, cuisine, 4)
        candidates.append(MenuCandidate(
            name=name,
            element=element,
            group=group,
            seasons=frozenset({"spring", "summer", "autumn", "winter"}),
            periods=candidate_periods,
            tags=frozenset(tags.split()),
            ingredient=(
                _ingredient_for(name)
                if _ingredient_for(name) != "mixed"
                else ingredient
            ),
            cuisine=cuisine,
            familiarity=4,
            nutrition_estimate=nutrition[6],
            estimated_kcal=nutrition[0],
            macro_profile=nutrition[1],
            has_protein=nutrition[2],
            has_vegetables=nutrition[3],
            carb_heavy=nutrition[4],
            fat_heavy=nutrition[5],
            popularity=consumer[0],
            accessibility=consumer[1],
            age_groups=consumer[2],
        ))
    return candidates


DIET_MENU_POOL = tuple(
    _diet_group(
        "木", "diet_breakfast_fresh", "breakfast", "fresh light balanced",
        "fruit", "western",
        "그릭요거트·저당 그래놀라·베리|그릭요거트·바나나·견과류|오트밀·사과·견과류",
    )
    + _diet_group(
        "火", "diet_breakfast_egg", "breakfast", "warm balanced hearty",
        "egg_dairy", "western",
        "계란후라이와 통밀토스트|토마토 에그스크램블·무가당 차|버섯 에그스크램블·통밀빵|닭가슴살 에그샌드위치|감자 에그샌드위치|햄치즈 통밀토스트·커피|땅콩버터 통밀토스트",
    )
    + _diet_group(
        "土", "diet_breakfast_korean", "breakfast", "warm balanced stabilize",
        "rice_grain", "korean",
        "간장계란밥|북엇국과 밥|단호박 달걀찜|고구마·삶은 달걀·우유",
    )
    + _diet_group(
        "水", "diet_breakfast_light", "breakfast", "fresh light moisten",
        "tofu_bean", "korean",
        "블루베리 두유 견과 스무디|케일 바나나 사과 요거트 스무디|블루베리 검은콩 스무디·삶은 달걀|케일 바나나 두유 스무디|당근 사과주스·달걀치즈 토스트|연어 오차즈케|달걀 오차즈케",
    )
    + _diet_group(
        "木", "diet_poke", "lunch", "fresh balanced hearty",
        "rice_grain", "western",
        "닭가슴살 포케|닭다리살 구이 포케|연어 포케|참치 포케|새우 포케|소고기 불고기 포케|두부버섯 포케",
    )
    + _diet_group(
        "土", "diet_rice", "lunch", "balanced hearty stabilize",
        "rice_grain", "korean",
        "닭고기 현미비빔밥|소고기 나물비빔밥|두부 나물비빔밥|보리밥 된장찌개|순두부찌개·잡곡밥",
    )
    + _diet_group(
        "火", "diet_lunch_warm", "lunch", "warm balanced hearty",
        "chicken", "korean",
        "닭고기 채소카레·잡곡밥|소고기 채소덮밥|오징어 채소볶음·잡곡밥|돼지고기 숙주볶음·밥",
    )
    + _diet_group(
        "木", "diet_noodle_wrap", "lunch", "fresh light balanced",
        "noodle_wheat", "southeast_asian",
        "닭고기 쌀국수|소고기 양지 쌀국수|닭고기 메밀국수|들기름 메밀국수·달걀|닭고기 월남쌈|새우 월남쌈|닭가슴살 샐러드 파스타|새우 토마토 파스타|통밀 치킨랩",
    )
    + _diet_group(
        "金", "diet_dinner_meat", "dinner", "warm balanced protect",
        "chicken", "korean",
        "훈제치킨 채소구이|닭다리살 소금구이·샐러드|닭고기 버섯볶음|닭고기 두부전골|닭고기 양배추쌈",
    )
    + _diet_group(
        "金", "diet_dinner_beef_pork", "dinner", "warm balanced hearty",
        "beef", "korean",
        "소고기 숙주볶음|소고기 버섯전골|돼지고기 양배추찜|돼지고기 두부김치|소고기 샤브샤브",
    )
    + _diet_group(
        "水", "diet_dinner_seafood", "dinner", "light balanced moisten",
        "seafood", "korean",
        "고등어구이·채소 반찬|연어구이·구운 채소|흰살생선구이·버섯|새우 두부찜|오징어 숙회·채소무침|해물 샤브샤브",
    )
    + _diet_group(
        "土", "diet_dinner_tofu", "dinner", "warm light stabilize",
        "tofu_bean", "korean",
        "두부버섯전골|순두부 달걀탕|두부스테이크·구운 채소|버섯 두부 샤브샤브",
    )
)


DIET_DEFAULT_EXCLUSIONS = frozenset({
    "해물짬뽕", "하얀짬뽕", "중화잡채밥", "채소 듬뿍 아귀찜",
    "삼겹살구이",
    "피자", "화덕피자", "페퍼로니피자", "고구마피자",
    "후라이드치킨", "양념치킨", "간장치킨",
    "햄버거", "치즈버거", "불고기버거", "치킨버거", "새우버거", "햄버거 세트",
    "김밥", "떡볶이", "라면", "짜파게티", "비빔국수",
    "경양식 돈가스", "일본식 돈카츠", "버터 크루아상",
    "로제파스타", "버섯크림파스타", "치킨크림리조또",
    "오코노미야키", "생선가스", "탕수육", "깐풍기",
    "새우팟타이", "해물볶음우동", "고구마그라탱",
    "시금치라자냐", "고추장삼겹살", "삼겹살",
    "감자탕", "뼈해장국", "돼지국밥", "순대국밥", "부대찌개",
    "짜장면", "오므라이스",
})

DIET_BREAKFAST_EXCLUSIONS = frozenset({
    "굴국밥", "매생이국", "검은깨죽",
})

DIET_CONDITIONAL_MENUS = frozenset({
    "제육볶음", "소고기불고기", "토마토파스타", "알리오 올리오",
    "두부김치", "카레라이스",
})


_OPERATION_TAG = {
    "protect": "protect",
    "resolve_conflict": "mediate",
    "release_binding": "organize",
    "drain": "light",
    "mediate": "mediate",
    "warm": "warm",
    "cool": "cool",
    "moisten": "moisten",
    "dry": "clear",
    "support": "support",
    "stabilize": "stabilize",
    "preserve_balance": "balanced",
    "preserve_special_structure": "protect",
}

_SEASON_KO = {"spring": "봄", "summer": "여름", "autumn": "가을", "winter": "겨울"}
_PERIOD_KO = {"breakfast": "아침", "lunch": "점심", "snack": "간식", "dinner": "저녁"}
_GAN_ELEMENT = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
}

def season_for(month: int) -> str:
    if month in {3, 4, 5}:
        return "spring"
    if month in {6, 7, 8}:
        return "summer"
    if month in {9, 10, 11}:
        return "autumn"
    return "winter"


def meal_period_for(hour: int | None) -> str:
    if hour is None:
        return "lunch"
    if 4 <= hour < 11:
        return "breakfast"
    if 11 <= hour < 15:
        return "lunch"
    if 15 <= hour < 18:
        return "snack"
    return "dinner"


def _tie_breaker(seed: str, candidate: MenuCandidate) -> str:
    raw = f"{seed}|{candidate.name}|{candidate.group}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def history_context(target_date: date, history: tuple[dict, ...]) -> tuple[frozenset[str], Counter]:
    """Only preceding nine calendar days affect a recommendation."""
    counts = Counter()
    groups = Counter()
    yesterday = set()
    for plan in history:
        gap = (target_date - date.fromisoformat(plan["date"])).days
        if not 1 <= gap <= 9:
            continue
        names = {meal["menu"] for meal in plan["meals"]}
        counts.update(names)
        groups.update(menu_category(name) for name in names)
        if gap == 1:
            yesterday.update(names)
    return frozenset(yesterday | {name for name, n in counts.items() if n >= 2}), groups


def _grouped_selection(candidates, score, seed, count, used_menus, category_counts):
    """One entry per culinary category, then choose a suitable variant.

    A category's score uses its best eligible candidate (never a sum), and its
    deterministic variation uses the category ID, not the number of variants.
    """
    selected = []
    remaining = list(candidates)
    used_categories = {menu_category(name) for name in used_menus}
    while remaining and len(selected) < count:
        groups = {}
        for item in remaining:
            groups.setdefault(menu_category(item.name), []).append(item)
        def category_score(group):
            best = max(score(item) for item in groups[group])
            frequency = PROFILES[group][0]
            digest = hashlib.sha256(f"{seed}|category|{group}".encode()).hexdigest()
            uniform = (int(digest[:12], 16) + 1) / (16**12 + 1)
            variation = -math.log(-math.log(uniform)) * 2
            return (best + frequency * 2 + variation
                    - min(12, category_counts.get(group, 0) * 2)
                    - (6 if group in used_categories else 0))
        category = max(sorted(groups), key=category_score)
        # Rotate close variants AFTER category selection; extra variants never
        # increase that category's chance. Large suitability gaps still prevail.
        best_variant = max(score(item) for item in groups[category])
        shortlist = [item for item in groups[category] if score(item) >= best_variant - 4]
        def variant_score(item):
            digest = _tie_breaker(seed, item)
            return score(item) + int(digest[:12], 16) / 16**12 * 4
        choice = max(shortlist, key=lambda item: (variant_score(item), item.name))
        selected.append(choice)
        used_categories.add(category)
        remaining = [item for item in remaining if item != choice]
    return selected


def food_family(name: str) -> str:
    """Culinary repetition groups, not medical or biological equivalence."""
    for family, words in (
        ("pollock", ("동태", "황태", "북어", "북엇", "명태", "코다리")),
        ("oily_fish", ("고등어", "삼치", "참치", "꽁치")),
        ("salmon", ("연어",)),
        ("white_fish", ("흰살생선", "광어", "대구", "갈치", "복국")),
        ("shellfish", ("꼬막", "조개", "바지락", "홍합", "재첩", "굴")),
        ("cephalopod", ("오징어", "낙지", "주꾸미", "문어")),
    ):
        if any(word in name for word in words):
            return family
    return ""


def _family_available(name: str, used_menus: frozenset[str]) -> bool:
    family = food_family(name)
    return not family or all(food_family(used) != family for used in used_menus)




def _balanced_candidates(candidates, totals):
    balanced = [item for item in candidates if _macro_deviation(item, totals) == 0]
    # Never relax diet exclusions, timing or repetition just to fit rough macros.
    # Any unavoidable deviation remains visible in the internal daily report.
    return balanced or candidates


def _macro_deviation(candidate, totals):
    estimate = candidate.nutrition_estimate
    if estimate is None:
        return 0
    combined = [totals[i] + estimate[key] for i, key in enumerate(("carbohydrate_g", "protein_g", "fat_g"))]
    return macro_summary(combined)["deviation"]


def _macro_penalty(candidate, totals):
    if not any(totals):
        return 0  # A light breakfast is balanced by the rest of the day.
    return round(_macro_deviation(candidate, totals) * 2)


def recommend_daily_menus(
    *,
    target_date: date,
    current_hour: int | None,
    day_master: str,
    daily_ganji: str,
    lucky_element: str,
    primary_operation: str,
    count: int = 2,
    recent_menus: frozenset[str] = frozenset(),
    used_cuisines: frozenset[str] = frozenset(),
    used_menus: frozenset[str] = frozenset(),
    used_ingredients: frozenset[str] = frozenset(),
    excluded_ingredients: frozenset[str] = frozenset(),
    excluded_menus: frozenset[str] = frozenset(),
    require_protein: bool = False,
    require_vegetables: bool = False,
    exclude_carb_heavy: bool = False,
    exclude_fat_heavy: bool = False,
    target_kcal: int | None = None,
    age_group: str | None = None,
    demographic_age: int | None = None,
    gender: str | None = None,
    preferences: dict | None = None,
    timing_element_weights: dict[str, int] | None = None,
    macro_totals: tuple[float, float, float] = (0, 0, 0),
    climate_tags: frozenset[str] = frozenset(),
    finalize_macros: bool = False,
    blocked_menus: frozenset[str] = frozenset(),
    category_counts: dict[str, int] | None = None,
) -> dict:
    """Choose diverse real dishes; the element is guidance, not a health claim."""

    if count < 1:
        raise ValueError("추천 메뉴 수는 1개 이상이어야 합니다.")
    season = season_for(target_date.month)
    period = meal_period_for(current_hour)
    operation_tag = _OPERATION_TAG.get(primary_operation, "balanced")
    daily_element = _GAN_ELEMENT.get(daily_ganji[:1], lucky_element)
    seed = (
        f"{target_date.isoformat()}|{current_hour}|{day_master}|{daily_ganji}|"
        f"{lucky_element}|{primary_operation}"
    )

    def context_score(candidate: MenuCandidate) -> int:
        score = 0
        # The natal correction and changing daily stem share the main axis.
        score += 4 if timing_element_weights is None and candidate.element == lucky_element else 0
        score += 6 if timing_element_weights is None and candidate.element == daily_element else 0
        score += (timing_element_weights or {}).get(candidate.element, 0)
        score += 4 if season in candidate.seasons else 0
        score += 8 if period in candidate.periods else 0
        score += 3 if operation_tag in candidate.tags else 0
        score += min(2, len(climate_tags & candidate.tags))
        score += candidate.familiarity - 2
        score += candidate.popularity - 3
        score += frequency_bonus(candidate.name)
        score -= _macro_penalty(candidate, macro_totals)
        score += max(-1, candidate.accessibility - 3)
        score += demographic_evidence(candidate.name, demographic_age, gender)["bonus"]
        score += preference_bonus(candidate, preferences)
        # Cuisine balance and recent repetition are weak tie-breakers only.
        score -= 4 if candidate.cuisine in used_cuisines else 0
        score -= 10 if candidate.ingredient in used_ingredients else 0
        score -= 4 if candidate.name in recent_menus else 0
        # Keep the fortune signals dominant while rotating similarly scored dishes
        # across adjacent dates so one strong candidate does not crowd out its peers.
        if target_kcal is not None:
            score -= abs(candidate.estimated_kcal - target_kcal) // 100
        return score

    period_candidates = [
        item for item in MENU_POOL
        if (
            period in item.periods
            and item.name not in blocked_menus
            and item.name not in used_menus
            and _family_available(item.name, used_menus)
            and item.name not in excluded_menus
            and item.ingredient not in excluded_ingredients
            and (not require_protein or item.has_protein)
            and (not require_vegetables or item.has_vegetables)
            and (not exclude_carb_heavy or not item.carb_heavy)
            and (not exclude_fat_heavy or not item.fat_heavy)
        )
    ]
    eligible_candidates = _balanced_candidates(period_candidates, macro_totals) if finalize_macros else period_candidates


    def rank(candidate: MenuCandidate) -> tuple[int, str]:
        score = context_score(candidate)
        return (-score, _tie_breaker(seed, candidate))

    selected = _grouped_selection(eligible_candidates, lambda item: -rank(item)[0],
                                  seed, count, used_menus, category_counts or {})

    return {
        "pool_version": MENU_POOL_VERSION,
        "pool_size": len(MENU_POOL),
        "menus": [item.name for item in selected],
        "ingredient_theme": selected[0].ingredient if selected else "mixed",
        "ingredient_theme_ko": _INGREDIENT_KO[selected[0].ingredient] if selected else _INGREDIENT_KO["mixed"],
        "season": season,
        "meal_period": period,
        "daily_element": daily_element,
        "reason": (
            "오늘의 보완 방향과 식사 구성을 검토하고, "
            f"{_SEASON_KO[season]}·{_PERIOD_KO[period]} 시간대와 오늘의 변화 흐름을 함께 "
            "반영한 음식 추천입니다. 특정 음식의 효능을 뜻하지는 않습니다."
        ),
    }


def recommend_diet_menus(
    *,
    target_date: date,
    current_hour: int | None,
    day_master: str,
    daily_ganji: str,
    lucky_element: str,
    primary_operation: str,
    count: int = 1,
    recent_menus: frozenset[str] = frozenset(),
    used_cuisines: frozenset[str] = frozenset(),
    used_menus: frozenset[str] = frozenset(),
    used_ingredients: frozenset[str] = frozenset(),
    excluded_ingredients: frozenset[str] = frozenset(),
    require_protein: bool = False,
    require_vegetables: bool = False,
    exclude_carb_heavy: bool = False,
    exclude_fat_heavy: bool = False,
    target_kcal: int | None = None,
    age_group: str | None = None,
    demographic_age: int | None = None,
    gender: str | None = None,
    preferences: dict | None = None,
    timing_element_weights: dict[str, int] | None = None,
    macro_totals: tuple[float, float, float] = (0, 0, 0),
    climate_tags: frozenset[str] = frozenset(),
    finalize_macros: bool = False,
    blocked_menus: frozenset[str] = frozenset(),
    category_counts: dict[str, int] | None = None,
) -> dict:
    """Select filling diet meals without attaching unverified calorie claims."""

    if count < 1:
        raise ValueError("추천 메뉴 수는 1개 이상이어야 합니다.")
    season = season_for(target_date.month)
    period = meal_period_for(current_hour)
    operation_tag = _OPERATION_TAG.get(primary_operation, "balanced")
    daily_element = _GAN_ELEMENT.get(daily_ganji[:1], lucky_element)
    seed = (
        f"diet|{target_date.isoformat()}|{current_hour}|{day_master}|{daily_ganji}|"
        f"{lucky_element}|{primary_operation}"
    )
    eligible = [
        item for item in DIET_MENU_POOL
        if (
            period in item.periods
            and item.name not in blocked_menus
            and item.name not in used_menus
            and _family_available(item.name, used_menus)
            and item.ingredient not in excluded_ingredients
            and (not require_protein or item.has_protein)
            and (not require_vegetables or item.has_vegetables)
            and (not exclude_carb_heavy or not item.carb_heavy)
            and (not exclude_fat_heavy or not item.fat_heavy)
        )
    ]

    def score(candidate: MenuCandidate) -> int:
        value = 0
        value += 4 if timing_element_weights is None and candidate.element == lucky_element else 0
        value += 6 if timing_element_weights is None and candidate.element == daily_element else 0
        value += (timing_element_weights or {}).get(candidate.element, 0)
        value += 4 if season in candidate.seasons else 0
        value += 8 if period in candidate.periods else 0
        value += 3 if operation_tag in candidate.tags else 0
        value += min(2, len(climate_tags & candidate.tags))
        value += candidate.popularity - 3
        value += frequency_bonus(candidate.name)
        value -= _macro_penalty(candidate, macro_totals)
        value += max(-1, candidate.accessibility - 3)
        value += demographic_evidence(candidate.name, demographic_age, gender)["bonus"]
        value += preference_bonus(candidate, preferences)
        value -= 4 if candidate.cuisine in used_cuisines else 0
        value -= 10 if candidate.ingredient in used_ingredients else 0
        value -= 4 if candidate.name in recent_menus else 0
        if target_kcal is not None:
            value -= abs(candidate.estimated_kcal - target_kcal) // 100
        return value

    if finalize_macros:
        eligible = _balanced_candidates(eligible, macro_totals)
    selected = _grouped_selection(eligible, score, seed, count, used_menus, category_counts or {})
    return {
        "pool_version": DIET_MENU_POOL_VERSION,
        "pool_size": len(DIET_MENU_POOL),
        "menus": [item.name for item in selected],
        "ingredient_theme": selected[0].ingredient if selected else "mixed",
        "ingredient_theme_ko": _INGREDIENT_KO[selected[0].ingredient] if selected else _INGREDIENT_KO["mixed"],
        "season": season,
        "meal_period": period,
        "daily_element": daily_element,
        "calorie_status": "estimated_internal",
    }


def recommend_daily_general_plan(
    *,
    target_date: date,
    day_master: str,
    daily_ganji: str,
    lucky_element: str,
    primary_operation: str,
    recent_menus: frozenset[str] = frozenset(),
    age_group: str | None = None,
    demographic_age: int | None = None,
    gender: str | None = None,
    preferences: dict | None = None,
    timing_element_weights: dict[str, int] | None = None,
    climate_tags: frozenset[str] = frozenset(),
    history: tuple[dict, ...] = (),
) -> dict:
    """Build a breakfast, lunch and dinner plan from the general menu pool."""

    hours = {"breakfast": 8, "lunch": 12, "dinner": 19}
    blocked_menus, category_counts = history_context(target_date, history)
    used_menus: set[str] = set()
    used_cuisines: set[str] = set()
    used_ingredients: set[str] = set()
    ingredient_counts: dict[str, int] = {}
    protein_meals = 0
    vegetable_meals = 0
    carb_heavy_meals = 0
    fat_heavy_meals = 0
    estimated_daily_kcal = 0
    day_macros = [0.0, 0.0, 0.0]
    meals: list[dict] = []

    meal_targets = {"breakfast": 450, "lunch": 650, "dinner": 650}
    for index, (period, hour) in enumerate(hours.items()):
        remaining_after = 2 - index
        selection = recommend_daily_menus(
            target_date=target_date,
            current_hour=hour,
            day_master=day_master,
            daily_ganji=daily_ganji,
            lucky_element=lucky_element,
            primary_operation=primary_operation,
            count=1,
            recent_menus=recent_menus,
            used_cuisines=frozenset(used_cuisines),
            used_menus=frozenset(used_menus),
            used_ingredients=frozenset(used_ingredients),
            excluded_ingredients=frozenset(
                ingredient for ingredient, count in ingredient_counts.items()
                if count >= 2
            ),
            require_protein=(protein_meals + remaining_after < 2),
            require_vegetables=(vegetable_meals == 0 and remaining_after == 0),
            exclude_carb_heavy=(carb_heavy_meals >= 1),
            exclude_fat_heavy=(fat_heavy_meals >= 1),
            target_kcal=(max(meal_targets[period] - 150, min(meal_targets[period] + 150,
                             sum(meal_targets.values()) - estimated_daily_kcal))
                         if remaining_after == 0 else meal_targets[period]),
            blocked_menus=blocked_menus,
            category_counts=category_counts,
            age_group=age_group,
            demographic_age=demographic_age, gender=gender, preferences=preferences,
            timing_element_weights=timing_element_weights,
            macro_totals=tuple(day_macros),
            climate_tags=climate_tags,
            finalize_macros=(remaining_after == 0),
        )
        name = selection["menus"][0]
        candidate = next(item for item in MENU_POOL if item.name == name)
        used_menus.add(name)
        used_cuisines.add(candidate.cuisine)
        used_ingredients.add(candidate.ingredient)
        ingredient_counts[candidate.ingredient] = ingredient_counts.get(candidate.ingredient, 0) + 1
        protein_meals += int(candidate.has_protein)
        vegetable_meals += int(candidate.has_vegetables)
        carb_heavy_meals += int(candidate.carb_heavy)
        fat_heavy_meals += int(candidate.fat_heavy)
        nutrition = candidate.nutrition_estimate
        estimated_daily_kcal += nutrition["estimated_kcal"]
        for i, key in enumerate(("carbohydrate_g", "protein_g", "fat_g")):
            day_macros[i] += nutrition[key]
        meals.append({"period": period, "menu": name,
                      "serving_suggestion": serving_suggestion(name),
                      "nutrition_estimate": nutrition,
                      "frequency_evidence": frequency_evidence(name),
                      "demographic_evidence": demographic_evidence(name, demographic_age, gender),
                      "ingredient": candidate.ingredient, "cuisine": candidate.cuisine,
                      "food_family": food_family(name),
                      "category": menu_category(name), "cooking_style": cooking_style(name)})

    return {
        "date": target_date.isoformat(),
        "mode": "general",
        "age_group": age_group,
        "timing_element_weights": timing_element_weights or {},
        "climate_tags": sorted(climate_tags),
        "meals": meals,
        "estimated_daily_kcal": round(estimated_daily_kcal, 1),
        "macro_estimate": macro_summary(day_macros),
        "nutrition_check": {
            "protein_meals": protein_meals,
            "vegetable_meals": vegetable_meals,
            "carb_heavy_meals": carb_heavy_meals,
            "fat_heavy_meals": fat_heavy_meals,
        },
    }


def recommend_daily_diet_plan(
    *,
    target_date: date,
    day_master: str,
    daily_ganji: str,
    lucky_element: str,
    primary_operation: str,
    recent_menus: frozenset[str] = frozenset(),
    age_group: str | None = None,
    demographic_age: int | None = None,
    gender: str | None = None,
    preferences: dict | None = None,
    timing_element_weights: dict[str, int] | None = None,
    climate_tags: frozenset[str] = frozenset(),
    history: tuple[dict, ...] = (),
) -> dict:
    """Build three meals with one or two diet-pool substitutions."""

    patterns = (
        frozenset({"breakfast", "dinner"}),
        frozenset({"breakfast", "lunch"}),
        frozenset({"dinner"}),
    )
    digest = hashlib.sha256(target_date.isoformat().encode("utf-8")).hexdigest()
    diet_periods = patterns[int(digest[:2], 16) % len(patterns)]
    hours = {"breakfast": 8, "lunch": 12, "dinner": 19}
    blocked_menus, category_counts = history_context(target_date, history)
    used_menus: set[str] = set()
    used_cuisines: set[str] = set()
    used_ingredients: set[str] = set()
    ingredient_counts: dict[str, int] = {}
    protein_meals = 0
    vegetable_meals = 0
    carb_heavy_meals = 0
    fat_heavy_meals = 0
    estimated_daily_kcal = 0
    day_macros = [0.0, 0.0, 0.0]
    meals: list[dict] = []

    meal_targets = {"breakfast": 350, "lunch": 550, "dinner": 500}
    for index, (period, hour) in enumerate(hours.items()):
        remaining_after = 2 - index
        kwargs = dict(
            target_date=target_date,
            current_hour=hour,
            day_master=day_master,
            daily_ganji=daily_ganji,
            lucky_element=lucky_element,
            primary_operation=primary_operation,
            count=1,
            recent_menus=recent_menus,
            used_cuisines=frozenset(used_cuisines),
            used_menus=frozenset(used_menus),
            used_ingredients=frozenset(used_ingredients),
            excluded_ingredients=frozenset(
                ingredient for ingredient, count in ingredient_counts.items()
                if count >= 2
            ),
            require_protein=(protein_meals + remaining_after < 2),
            require_vegetables=(vegetable_meals == 0 and remaining_after == 0),
            exclude_carb_heavy=(carb_heavy_meals >= 1),
            exclude_fat_heavy=(fat_heavy_meals >= 1),
            target_kcal=(max(meal_targets[period] - 150, min(meal_targets[period] + 150,
                             sum(meal_targets.values()) - estimated_daily_kcal))
                         if remaining_after == 0 else meal_targets[period]),
            blocked_menus=blocked_menus,
            category_counts=category_counts,
            age_group=age_group,
            demographic_age=demographic_age, gender=gender, preferences=preferences,
            timing_element_weights=timing_element_weights,
            macro_totals=tuple(day_macros),
            climate_tags=climate_tags,
            finalize_macros=(remaining_after == 0),
        )
        is_diet = period in diet_periods
        selection = (
            recommend_diet_menus(**kwargs)
            if is_diet else
            recommend_daily_menus(
                **kwargs,
                excluded_menus=(
                    DIET_DEFAULT_EXCLUSIONS | DIET_BREAKFAST_EXCLUSIONS
                    if period == "breakfast" else
                    DIET_DEFAULT_EXCLUSIONS
                ),
            )
        )
        name = selection["menus"][0]
        pool = DIET_MENU_POOL if is_diet else MENU_POOL
        candidate = next(item for item in pool if item.name == name)
        used_menus.add(name)
        used_cuisines.add(candidate.cuisine)
        used_ingredients.add(candidate.ingredient)
        ingredient_counts[candidate.ingredient] = ingredient_counts.get(candidate.ingredient, 0) + 1
        protein_meals += int(candidate.has_protein)
        vegetable_meals += int(candidate.has_vegetables)
        carb_heavy_meals += int(candidate.carb_heavy)
        fat_heavy_meals += int(candidate.fat_heavy)
        nutrition = candidate.nutrition_estimate
        estimated_daily_kcal += nutrition["estimated_kcal"]
        for i, key in enumerate(("carbohydrate_g", "protein_g", "fat_g")):
            day_macros[i] += nutrition[key]
        meals.append({"period": period, "menu": name, "diet_menu": is_diet,
                      "serving_suggestion": serving_suggestion(name),
                      "nutrition_estimate": nutrition,
                      "frequency_evidence": frequency_evidence(name),
                      "demographic_evidence": demographic_evidence(name, demographic_age, gender),
                      "ingredient": candidate.ingredient, "cuisine": candidate.cuisine,
                      "food_family": food_family(name),
                      "category": menu_category(name), "cooking_style": cooking_style(name)})

    return {
        "date": target_date.isoformat(),
        "mode": "diet",
        "age_group": age_group,
        "timing_element_weights": timing_element_weights or {},
        "climate_tags": sorted(climate_tags),
        "diet_meal_count": len(diet_periods),
        "meals": meals,
        "estimated_daily_kcal": round(estimated_daily_kcal, 1),
        "macro_estimate": macro_summary(day_macros),
        "calorie_status": "estimated_internal",
        "nutrition_check": {
            "protein_meals": protein_meals,
            "vegetable_meals": vegetable_meals,
            "carb_heavy_meals": carb_heavy_meals,
            "fat_heavy_meals": fat_heavy_meals,
        },
    }
