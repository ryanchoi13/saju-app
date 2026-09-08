"""Curated daily meal pool and deterministic lifestyle translation rules."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date


MENU_POOL_VERSION = "daily-menu-pool-v2"


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


_INGREDIENT_RULES = (
    ("beef", ("소고기", "차돌", "불고기", "설렁탕", "곰탕", "스테이크")),
    ("pork", ("돼지", "제육", "삼겹살", "보쌈", "수육", "돈가스", "감자탕", "뼈해장국", "순대국밥")),
    ("chicken", ("닭", "치킨", "삼계탕")),
    ("seafood", ("해물", "해산물", "해초", "새우", "오징어", "주꾸미", "낙지", "조개", "홍합", "바지락", "굴", "꼬막", "문어", "아귀", "대구", "복국", "생선", "연어", "참치", "고등어", "갈치", "꽁치", "장어", "매생이", "재첩", "톳")),
    ("tofu_bean", ("두부", "콩", "된장", "청국장", "비지", "두유")),
    ("egg_dairy", ("계란", "달걀", "에그", "치즈", "요거트", "우유", "크림")),
    ("noodle_wheat", ("라면", "짜파게티", "비빔면", "국수", "파스타", "우동", "칼국수", "수제비", "베이글", "빵", "토스트", "샌드위치", "피자", "라자냐", "크루아상", "팬케이크")),
    ("rice_grain", ("밥", "죽", "솥밥", "김밥", "떡", "오트밀", "그래놀라")),
    ("root", ("감자", "고구마", "단호박", "연근", "우엉", "토란")),
    ("vegetable", ("채소", "나물", "샐러드", "아보카도", "시금치", "청경채", "가지", "오이", "배추", "무생채")),
    ("mushroom", ("버섯",)),
    ("fruit", ("과일", "사과", "키위", "배숙", "유자", "자몽")),
)

_LOW_FAMILIARITY = {
    "아라비아타 파스타", "해산물 빠에야", "스키야키", "오뎅나베",
    "돈코츠라멘", "감자뇨키", "똠얌꿍", "참치타다키",
}

_HIGH_FAMILIARITY = {
    "라면", "짜파게티", "비빔면", "후라이드치킨", "양념치킨", "간장치킨",
    "치킨버거", "햄버거", "불고기버거", "치즈버거", "새우버거",
    "제육볶음", "된장찌개", "김치찌개", "감자탕", "뼈해장국", "돼지국밥",
    "순대국밥", "돈가스", "불고기", "오징어뭇국", "해물찜", "조개구이",
}

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
    for ingredient, keywords in _INGREDIENT_RULES:
        if any(keyword in name for keyword in keywords):
            return ingredient
    return "mixed"


def _cuisine_for(name: str, group: str) -> str:
    if any(word in name for word in ("파스타", "피자", "리조또", "샐러드", "스테이크", "버거")):
        return "western"
    if any(word in name for word in ("라멘", "우동", "오차즈케", "타다키", "스키야키", "나베")):
        return "japanese"
    if any(word in name for word in ("쌀국수", "팟타이", "똠얌꿍", "월남쌈")):
        return "southeast_asian"
    if any(word in name for word in ("짬뽕", "유산슬", "중화")):
        return "chinese"
    return "korean"


def _group(
    element: str,
    group: str,
    seasons: str,
    periods: str,
    tags: str,
    names: str,
) -> list[MenuCandidate]:
    return [
        MenuCandidate(
            name=name.strip(),
            element=element,
            group=group,
            seasons=frozenset(seasons.split()),
            periods=frozenset(periods.split()),
            tags=frozenset(tags.split()),
            ingredient=_ingredient_for(name.strip()),
            cuisine=_cuisine_for(name.strip(), group),
            familiarity=(
                4 if name.strip() in _HIGH_FAMILIARITY
                else 2 if name.strip() in _LOW_FAMILIARITY
                else 3
            ),
        )
        for name in names.split("|")
        if name.strip()
    ]


MENU_POOL = tuple(
    _group(
        "木", "wood_fresh", "spring summer", "lunch dinner", "fresh light cool",
        "봄나물 비빔밥|새싹채소 비빔밥|닭가슴살 그린샐러드|연두부 채소샐러드|아보카도 샐러드|시저샐러드|그릭샐러드|카프레제 샐러드|월남쌈|연어 포케",
    )
    + _group(
        "木", "wood_noodle", "spring summer autumn", "lunch dinner", "fresh light create",
        "바질페스토 파스타|들기름 막국수|메밀 비빔국수|채소 쌀국수|잔치국수|부추 칼국수|비빔면|루꼴라 파스타|미나리 국수|짜파게티",
    )
    + _group(
        "木", "wood_warm", "autumn winter spring", "lunch dinner", "balanced warm organize",
        "채소카레|버섯덮밥|가지덮밥|청경채볶음|채소볶음밥|두부채소볶음|버섯리조또|시금치오믈렛|채소라자냐|잡채",
    )
    + _group(
        "木", "wood_breakfast", "spring summer", "breakfast snack", "fresh light record",
        "그린 스무디|사과 셀러리 주스|키위 요거트|말차 오트밀|아보카도 토스트|허브 치즈 샌드위치|에그 샐러드 샌드위치|과일 그래놀라 볼|쑥떡과 차|바질 토마토 파니니",
    )
    + _group(
        "木", "wood_tangy", "summer autumn", "lunch dinner", "fresh cool mediate",
        "열무비빔밥|김치말이국수|묵은지 두부김치|오이냉국 정식|초계국수|유부초밥|매실소스 닭구이|불고기|불고기버거|치킨버거",
    )
    + _group(
        "火", "fire_spicy_soup", "autumn winter", "lunch dinner", "warm hearty support",
        "육개장|순두부찌개|김치찌개|부대찌개|해물짬뽕|마라탕|매운 닭개장|고추장찌개|알탕|매운 어묵탕",
    )
    + _group(
        "火", "fire_grill", "spring summer autumn winter", "lunch dinner", "warm create move",
        "닭갈비|제육볶음|주꾸미볶음|오징어볶음|고추장삼겹살|탄두리치킨|후라이드치킨|화덕피자|그릴드 스테이크|양념치킨",
    )
    + _group(
        "火", "fire_red_meal", "spring summer autumn winter", "lunch dinner", "warm create organize",
        "토마토파스타|아라비아타 파스타|로제파스타|김치볶음밥|낙지볶음밥|매콤한 치킨카레|간장치킨|페퍼로니피자|해산물 빠에야|매운 소고기 쌀국수",
    )
    + _group(
        "火", "fire_snack", "autumn winter spring", "breakfast snack", "warm move record",
        "토마토 에그스크램블|햄치즈 핫샌드위치|시나몬토스트|구운 파프리카 샌드위치|떡볶이|닭꼬치|매운 핫도그|생강차와 구운 떡|계피차와 호두빵|자몽차와 에그타르트",
    )
    + _group(
        "火", "fire_gentle_warmth", "autumn winter", "lunch dinner", "warm balanced mediate",
        "닭한마리|삼계탕|소고기 샤브샤브|스키야키|버섯전골|오뎅나베|돈코츠라멘|유부우동|치킨수프|라면",
    )
    + _group(
        "土", "earth_rice", "spring summer autumn winter", "lunch dinner", "balanced hearty organize",
        "영양솥밥|버섯솥밥|곤드레밥|전복솥밥|오곡밥 정식|현미밥 정식|콩나물밥|시래기밥|밤밥|연근밥",
    )
    + _group(
        "土", "earth_root", "autumn winter", "lunch dinner", "warm hearty support",
        "감자옹심이|감자수제비|고구마그라탱|단호박죽|팥죽|뿌리채소카레|우엉잡채|연근조림 정식|토란국|햄버거",
    )
    + _group(
        "土", "earth_comfort", "spring autumn winter", "lunch dinner", "balanced warm stabilize",
        "된장찌개|청국장|보리밥 정식|강된장비빔밥|들깨수제비|닭칼국수|닭죽|소고기죽|야채죽|콩비지찌개",
    )
    + _group(
        "土", "earth_breakfast", "spring summer autumn winter", "breakfast snack", "balanced support pace",
        "오트밀죽|고구마토스트|감자샌드위치|단호박샌드위치|통밀베이글|버터 크루아상|바나나 팬케이크|프렌치토스트|그래놀라 요거트|콘수프와 모닝빵",
    )
    + _group(
        "土", "earth_global", "autumn winter spring", "lunch dinner", "hearty create stabilize",
        "감자뇨키|버섯크림리조또|고구마피자|감자탕|뼈해장국|카레라이스|오므라이스|돼지국밥|순대국밥|돈가스",
    )
    + _group(
        "金", "metal_clear_soup", "autumn winter spring", "breakfast lunch dinner", "warm clear support",
        "설렁탕|소고기곰탕|닭곰탕|떡국|만둣국|콩나물국밥|북엇국|황태해장국|오징어뭇국|맑은 순두부국",
    )
    + _group(
        "金", "metal_crisp", "spring summer autumn", "lunch dinner", "fresh light organize",
        "무밥|소고기무국|무생채비빔밥|도토리묵밥|메밀묵밥|배추전|양배추롤|콜슬로 샌드위치|조개구이|백김치국수",
    )
    + _group(
        "金", "metal_simple_protein", "spring summer autumn winter", "lunch dinner", "clear balanced protect",
        "돼지고기수육|보쌈 정식|편백찜|닭가슴살구이|흰살생선구이|두부스테이크|계란찜 정식|새우소금구이|소고기편채|오리훈제샐러드",
    )
    + _group(
        "金", "metal_clean_meal", "spring summer autumn winter", "lunch dinner", "clear create mediate",
        "소금라멘|봉골레파스타|버섯크림파스타|치킨크림리조또|새우필라프|유산슬덮밥|중화잡채밥|닭고기쌀국수|하얀짬뽕|차돌숙주볶음밥",
    )
    + _group(
        "金", "metal_breakfast", "spring summer autumn winter", "breakfast snack", "light clear record",
        "배도라지차와 쌀과자|유자차와 백설기|흰콩두유|플레인요거트|치즈버거|치즈샌드위치|달걀샌드위치|소금빵|배숙|새우버거",
    )
    + _group(
        "水", "water_sea_soup", "autumn winter spring", "breakfast lunch dinner", "broth warm moisten",
        "소고기미역국|해물탕|매생이국|굴국밥|대구탕|복국|재첩국|홍합탕|바지락칼국수|해물순두부찌개",
    )
    + _group(
        "水", "water_fish_meal", "spring summer autumn winter", "lunch dinner", "balanced protect support",
        "연어덮밥|참치회덮밥|장어덮밥|고등어구이정식|갈치조림|꽁치김치조림|아귀찜|꼬막비빔밥|해초비빔밥|문어숙회정식",
    )
    + _group(
        "水", "water_black_food", "autumn winter spring", "breakfast lunch dinner", "balanced moisten record",
        "검은콩밥|흑미밥|검은깨죽|들깨미역국|김밥 정식|온메밀소바|메밀전병|김국|톳밥|검은콩국수",
    )
    + _group(
        "水", "water_cool_light", "spring summer", "lunch dinner snack", "cool light moisten",
        "물냉면|서리태콩국수|냉우동|연어 오차즈케|연두부국|도토리묵사발|해파리냉채|과일화채|나박김치국수|냉모밀",
    )
    + _group(
        "水", "water_global", "spring summer autumn winter", "lunch dinner", "broth create move",
        "해산물파스타|해산물리조또|생선가스|연어스테이크|참치타다키|새우팟타이|해물볶음우동|똠얌꿍|해물찜|조개찜",
    )
)


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


def recommend_daily_menus(
    *,
    target_date: date,
    current_hour: int | None,
    day_master: str,
    daily_ganji: str,
    lucky_element: str,
    primary_operation: str,
    count: int = 2,
) -> dict:
    """Choose diverse real dishes; the element is guidance, not a health claim."""

    if count < 1:
        raise ValueError("추천 메뉴 수는 1개 이상이어야 합니다.")
    season = season_for(target_date.month)
    period = meal_period_for(current_hour)
    operation_tag = _OPERATION_TAG.get(primary_operation, "balanced")
    seed = (
        f"{target_date.isoformat()}|{current_hour}|{day_master}|{daily_ganji}|"
        f"{lucky_element}|{primary_operation}"
    )

    def context_score(candidate: MenuCandidate) -> int:
        score = 0
        # The Myeongri result is the primary axis. Season, time and action only
        # rank candidates inside that direction; they must not overturn it.
        score += 20 if candidate.element == lucky_element else 0
        score += 4 if season in candidate.seasons else 0
        score += 8 if period in candidate.periods else 0
        score += 3 if operation_tag in candidate.tags else 0
        score += candidate.familiarity - 2
        return score

    ingredient_scores: dict[str, int] = {}
    for candidate in MENU_POOL:
        if candidate.element != lucky_element or candidate.ingredient == "mixed":
            continue
        ingredient_scores[candidate.ingredient] = max(
            ingredient_scores.get(candidate.ingredient, 0),
            context_score(candidate),
        )
    ingredient_theme = min(
        ingredient_scores,
        key=lambda ingredient: (
            -ingredient_scores[ingredient],
            hashlib.sha256(f"{seed}|{ingredient}".encode("utf-8")).hexdigest(),
        ),
    )

    def rank(candidate: MenuCandidate) -> tuple[int, str]:
        score = context_score(candidate)
        score += 9 if candidate.ingredient == ingredient_theme else 0
        return (-score, _tie_breaker(seed, candidate))

    period_candidates = [item for item in MENU_POOL if period in item.periods]
    ranked = sorted(period_candidates or list(MENU_POOL), key=rank)
    selected: list[MenuCandidate] = []
    used_groups = set()
    while len(selected) < count:
        remaining = [candidate for candidate in ranked if candidate not in selected]
        if not remaining:
            break
        best_score = rank(remaining[0])[0]
        equally_suitable = [
            candidate for candidate in remaining if rank(candidate)[0] == best_score
        ]
        candidate = next(
            (
                item for item in equally_suitable
                if item.group not in used_groups
            ),
            equally_suitable[0],
        )
        selected.append(candidate)
        used_groups.add(candidate.group)

    return {
        "pool_version": MENU_POOL_VERSION,
        "pool_size": len(MENU_POOL),
        "menus": [item.name for item in selected],
        "ingredient_theme": ingredient_theme,
        "ingredient_theme_ko": _INGREDIENT_KO[ingredient_theme],
        "season": season,
        "meal_period": period,
        "reason": (
            f"오늘의 보완 방향에서 {_INGREDIENT_KO[ingredient_theme]} 재료군을 잡고, "
            f"{_SEASON_KO[season]}·{_PERIOD_KO[period]} 시간대와 필요한 행동을 함께 "
            "반영한 음식 추천입니다. 특정 음식의 효능을 뜻하지는 않습니다."
        ),
    }
