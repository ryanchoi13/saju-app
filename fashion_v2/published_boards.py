"""Owner-approved age/TPO boards that may be shown in production.

Each entry contains the garments represented by its static image. A complete
Daily/Trendy pair is required before a scope is returned.
"""

from copy import deepcopy

from fashion_v2.age_tpo_policy import age_band


def _item(category, label, color_name=""):
    item = {
        "category": category,
        "label": label,
        "wear_mode": "carry" if category == "carry_outer" else "worn",
    }
    if color_name:
        item["color_name"] = color_name
    return item


def _look(key, gender, tpo, role, image, items):
    return {
        "id": f"published-{key}-{role}", "gender": gender,
        "season": "editorial_weather_matched", "tpo": tpo, "look_role": role,
        "status": "owner_approved_live", "selection_mode": "whole_template_only",
        "board_image": f"/assets/fashion-v2-boards/{image}",
        "board_palette_mode": "approved_complete_look", "items": items,
    }


PUBLISHED_PAIRS = {
    ("female", "teen", "casual", "warm"): (
        _look("female-teen-warm-casual", "female", "casual", "daily", "sample-v4-female-teen-warm-casual-daily.webp", [
            _item("top", "그래픽 반팔 티셔츠", "화이트"), _item("bottom", "와이드 데님", "블루"), _item("shoes", "쿠션 스니커즈", "화이트"), _item("carry_outer", "집업 후디", "그레이")]),
        _look("female-teen-warm-casual", "female", "casual", "trend", "sample-v5-female-teen-warm-casual-trend.webp", [
            _item("top", "체리 폴로", "레드"), _item("bottom", "미니 스코트", "네이비"), _item("shoes", "실버 러너", "실버"), _item("carry_outer", "얇은 트랙 재킷", "네이비")]),
    ),
    ("male", "teen", "casual", "warm"): (
        _look("male-teen-warm-casual", "male", "casual", "daily", "sample-v4-male-teen-warm-casual-daily.webp", [
            _item("top", "워시드 반팔 티셔츠", "블랙"), _item("bottom", "와이드 데님", "블랙"), _item("shoes", "쿠션 스니커즈", "그레이"), _item("carry_outer", "후디", "그레이")]),
        _look("male-teen-warm-casual", "male", "casual", "trend", "sample-v8-male-teen-warm-casual-trend.webp", [
            _item("top", "파이핑 풋볼 저지", "네이비"), _item("bottom", "벌룬 카펜터 데님", "블루"), _item("shoes", "실버 테크 러너", "실버"), _item("carry_outer", "얇은 바람막이", "그레이")]),
    ),
    ("female", "thirties", "casual", "warm"): (
        _look("female-thirties-warm-casual", "female", "casual", "daily", "sample-v5-female-thirties-warm-casual-daily.webp", [
            _item("top", "면 티셔츠", "아이보리"), _item("bottom", "릴랙스 데님", "블루"), _item("shoes", "레트로 스니커즈", "오프화이트"), _item("carry_outer", "얇은 셔츠", "블루"), _item("bag", "가벼운 숄더백", "브라운")]),
        _look("female-thirties-warm-casual", "female", "casual", "trend", "sample-v10-female-thirties-warm-casual-trend.webp", [
            _item("top", "코튼 티셔츠", "체리 레드"), _item("bottom", "배럴 데님", "다크 인디고"), _item("shoes", "실버 러너", "실버"), _item("carry_outer", "얇은 블루종", "네이비"), _item("bag", "모던 숄더백", "브라운")]),
    ),
    ("male", "thirties", "casual", "warm"): (
        _look("male-thirties-warm-casual", "male", "casual", "daily", "sample-v5-male-thirties-warm-casual-daily.webp", [
            _item("top", "워시드 면 티셔츠", "네이비"), _item("bottom", "릴랙스 데님", "블루"), _item("shoes", "쿠션 러너", "그레이"), _item("carry_outer", "얇은 셔츠", "오프화이트")]),
        _look("male-thirties-warm-casual", "male", "casual", "trend", "sample-v9-male-thirties-warm-casual-trend.webp", [
            _item("top", "조직감 니트 폴로", "버건디"), _item("bottom", "볼륨 슬랙스", "차콜"), _item("shoes", "대비 스웨이드 스니커즈", "브라운"), _item("carry_outer", "얇은 블루종", "네이비")]),
    ),
    ("female", "fifty_plus", "casual", "warm"): (
        _look("female-fifty-warm-casual", "female", "casual", "daily", "sample-v10-female-fifty-warm-casual-daily.webp", [
            _item("top", "면 티셔츠", "더스티 블루"), _item("bottom", "풀온 팬츠", "베이지"), _item("shoes", "쿠션 워킹화", "오프화이트"), _item("carry_outer", "얇은 카디건", "네이비"), _item("bag", "가벼운 숄더백", "브라운")]),
        _look("female-fifty-warm-casual", "female", "casual", "trend", "sample-v10-female-fifty-warm-casual-trend.webp", [
            _item("top", "니트 폴로", "딥 틸"), _item("bottom", "릴랙스 데님", "다크 인디고"), _item("shoes", "쿠션 레트로 러너", "오프화이트"), _item("carry_outer", "얇은 카디건", "베이지"), _item("bag", "모던 숄더백", "브라운")]),
    ),
    ("male", "fifty_plus", "casual", "warm"): (
        _look("male-fifty-warm-casual", "male", "casual", "daily", "sample-v6-male-fifty-warm-casual-daily.webp", [
            _item("top", "반팔 폴로", "라이트 블루"), _item("bottom", "면 치노", "카키"), _item("shoes", "쿠션 워킹화", "브라운"), _item("carry_outer", "얇은 바람막이", "네이비")]),
        _look("male-fifty-warm-casual", "male", "casual", "trend", "sample-v10-male-fifty-warm-casual-trend.webp", [
            _item("top", "조직감 니트 폴로", "버건디"), _item("bottom", "면 팬츠", "아이보리"), _item("shoes", "쿠션 스웨이드 스니커즈", "브라운"), _item("carry_outer", "오버셔츠", "네이비")]),
    ),
    ("male", "forties", "business_casual", "mild"): (
        _look("male-forties-mild-business-casual", "male", "business_casual", "daily", "sample-v7-male-forties-mild-business-casual-daily.webp", [
            _item("outer", "재킷", "네이비"), _item("top", "니트 폴로", "아이보리"), _item("bottom", "슬랙스", "그레이"), _item("shoes", "스웨이드 로퍼", "다크 브라운")]),
        _look("male-forties-mild-business-casual", "male", "business_casual", "trend", "sample-v7-male-forties-mild-business-casual-trend.webp", [
            _item("outer", "워크 재킷", "올리브"), _item("top", "스트라이프 셔츠", "블루"), _item("bottom", "볼륨 슬랙스", "차콜"), _item("shoes", "대비 가죽 스니커즈", "오프화이트")]),
    ),
    ("male", "thirties", "business_formal", "cool"): (
        _look("male-thirties-cool-business-formal", "male", "business_formal", "daily", "sample-v9-male-thirties-cool-business-formal-daily.webp", [
            _item("outer", "울 수트 재킷", "네이비"), _item("top", "드레스 셔츠", "화이트"), _item("bottom", "울 수트 바지", "네이비"), _item("tie", "레지멘탈 타이", "블루·버건디"), _item("shoes", "옥스퍼드 구두", "블랙")]),
        _look("male-thirties-cool-business-formal", "male", "business_formal", "trend", "male-autumn-business-formal-trend-red-offwhite-v1.webp", [
            _item("outer", "울 수트 재킷", "차콜"), _item("top", "드레스 셔츠", "오프화이트"), _item("bottom", "울 수트 바지", "차콜"), _item("tie", "솔리드 타이", "버건디"), _item("shoes", "더비 구두", "다크 브라운")]),
    ),
    ("male", "fifty_plus", "business_formal", "cool"): (
        _look("male-fifty-cool-business-formal", "male", "business_formal", "daily", "sample-v11-male-fifty-cool-business-formal-daily.webp", [
            _item("outer", "울 수트 재킷", "차콜"), _item("top", "드레스 셔츠", "라이트 블루"), _item("bottom", "재킷 아래로 연결된 울 수트 바지", "차콜"), _item("tie", "소패턴 타이", "딥 버건디"), _item("shoes", "쿠션 고무창 옥스퍼드", "다크 브라운")]),
        _look("male-fifty-cool-business-formal", "male", "business_formal", "trend", "male-autumn-business-formal-trend-red-offwhite-v1.webp", [
            _item("outer", "울 수트 재킷", "차콜"), _item("top", "드레스 셔츠", "오프화이트"), _item("bottom", "재킷 아래로 연결된 울 수트 바지", "차콜"), _item("tie", "솔리드 타이", "버건디"), _item("shoes", "고무창 더비 구두", "다크 브라운")]),
    ),
}


def _weather_family(tpo, profile, season):
    if profile:
        high = float(profile.get("daytime_apparent_high", 20))
        if tpo == "casual" and high >= 22:
            return "warm"
        if tpo == "business_casual" and 17 <= high <= 24:
            return "mild"
        if tpo == "business_formal" and 9 <= high <= 18:
            return "cool"
        return None
    if tpo == "casual" and season == "summer":
        return "warm"
    if tpo == "business_casual" and season in {"spring", "autumn"}:
        return "mild"
    if tpo == "business_formal" and season in {"autumn", "winter"}:
        return "cool"
    return None


def published_looks_for(gender, age, tpo, profile=None, season=None):
    if age is None or not profile:
        return ()
    pair = PUBLISHED_PAIRS.get((gender, age_band(age), tpo, _weather_family(tpo, profile, season)))
    return tuple(deepcopy(pair)) if pair else ()
