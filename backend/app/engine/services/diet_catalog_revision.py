"""Reviewed dish-level metadata for diet ideas, not nutritional prescriptions.

Elements are DALHA's editorial symbolism: greens/freshness (木), red or roasted
preparations (火), grains/roots (土), white ingredients/light broth (金), and
seafood/dark ingredients (水). A dish gets an explicit dominant feature, not its
cuisine's or entire group's element. These are not measured health effects.
"""
from dataclasses import replace

# name | element | cuisine | principal ingredient | culinary family | rationale
_ROWS = """
그릭요거트·저당 그래놀라·베리|金|western|egg_dairy|yogurt|흰 요거트 중심
그릭요거트·바나나·견과류|金|western|egg_dairy|yogurt|흰 요거트 중심
오트밀·사과·견과류|土|western|rice_grain|grain_bowl|귀리 곡물 중심
계란후라이와 통밀토스트|火|western|egg_dairy|toast|달걀과 빵을 굽는 조리
토마토 에그스크램블·무가당 차|火|western|egg_dairy|egg|붉은 토마토를 익힌 조리
버섯 에그스크램블·통밀빵|火|western|egg_dairy|egg|달걀과 버섯을 볶는 조리
닭가슴살 에그샌드위치|金|western|chicken|sandwich|담백한 닭가슴살과 달걀
감자 에그샌드위치|土|western|root|sandwich|감자와 빵 중심
햄치즈 통밀토스트·커피|火|western|egg_dairy|toast|햄과 치즈를 구운 토스트
땅콩버터 통밀토스트|土|western|rice_grain|toast|통밀과 견과 중심
간장계란밥|土|korean|rice_grain|rice|밥 중심의 한 그릇
북엇국과 밥|水|korean|seafood|soup|북어 중심의 국
단호박 달걀찜|土|korean|root|steamed|노란 단호박 중심
고구마·삶은 달걀·우유|土|korean|root|root_plate|고구마 중심의 구성
블루베리 두유 견과 스무디|水|western|tofu_bean|smoothie|짙은 베리와 두유
케일 바나나 사과 요거트 스무디|木|western|vegetable|smoothie|푸른 케일 중심
블루베리 검은콩 스무디·삶은 달걀|水|western|tofu_bean|smoothie|검은콩과 짙은 베리
케일 바나나 두유 스무디|木|western|vegetable|smoothie|푸른 케일 중심
당근 사과주스·달걀치즈 토스트|土|western|root|toast|당근과 빵 중심
연어 오차즈케|水|japanese|seafood|rice|연어 중심의 찻물밥
달걀 오차즈케|土|japanese|rice_grain|rice|밥과 달걀 중심
닭가슴살 포케|金|western|chicken|poke|담백한 닭가슴살 중심
닭다리살 구이 포케|火|western|chicken|poke|구운 닭다리살 중심
연어 포케|水|western|seafood|poke|연어 중심
참치 포케|水|western|seafood|poke|참치 중심
새우 포케|水|western|seafood|poke|새우 중심
소고기 불고기 포케|火|western|beef|poke|볶은 불고기 중심
두부버섯 포케|金|western|tofu_bean|poke|흰 두부와 버섯 중심
닭고기 현미비빔밥|土|korean|rice_grain|rice|현미 곡물 중심
소고기 나물비빔밥|木|korean|vegetable|rice|나물 중심의 비빔 구성
두부 나물비빔밥|木|korean|vegetable|rice|나물 중심의 비빔 구성
보리밥 된장찌개|土|korean|rice_grain|soup|보리 곡물과 된장 중심
순두부찌개·잡곡밥|火|korean|tofu_bean|soup|붉은 양념의 찌개
닭고기 채소카레·잡곡밥|土|korean|rice_grain|rice|노란 카레와 잡곡밥
소고기 채소덮밥|火|korean|beef|rice|볶은 소고기 중심
오징어 채소볶음·잡곡밥|火|korean|seafood|stirfry|붉은 양념으로 볶는 조리
돼지고기 숙주볶음·밥|火|korean|pork|stirfry|돼지고기를 볶는 조리
닭고기 쌀국수|金|southeast_asian|chicken|noodles|담백한 닭 육수와 흰 쌀국수
소고기 양지 쌀국수|金|southeast_asian|beef|noodles|맑은 육수와 흰 쌀국수
닭고기 메밀국수|土|korean|noodle_wheat|noodles|메밀 곡물 중심
들기름 메밀국수·달걀|土|korean|noodle_wheat|noodles|메밀 곡물 중심
닭고기 월남쌈|木|southeast_asian|vegetable|wrap|생채소를 싸 먹는 구성
새우 월남쌈|水|southeast_asian|seafood|wrap|새우 중심의 쌈
닭가슴살 샐러드 파스타|木|western|vegetable|pasta|생채소 샐러드 중심
새우 토마토 파스타|火|western|seafood|pasta|붉은 토마토 소스 중심
통밀 치킨랩|土|western|noodle_wheat|wrap|통밀 곡물 중심
훈제치킨 채소구이|火|western|chicken|grill|훈연과 구이 조리
닭다리살 소금구이·샐러드|火|western|chicken|grill|닭다리살 구이 중심
닭고기 버섯볶음|金|korean|mushroom|stirfry|담백한 버섯과 닭고기 중심
닭고기 두부전골|金|korean|tofu_bean|soup|흰 두부와 맑은 전골
닭고기 양배추쌈|木|korean|vegetable|wrap|양배추 쌈 중심
소고기 숙주볶음|火|korean|beef|stirfry|소고기를 볶는 조리
소고기 버섯전골|金|korean|mushroom|soup|버섯과 맑은 전골
돼지고기 양배추찜|木|korean|vegetable|steamed|양배추 중심의 찜
돼지고기 두부김치|火|korean|pork|stirfry|붉은 김치를 볶는 조리
소고기 샤브샤브|金|japanese|beef|soup|맑은 육수의 데침
고등어구이·채소 반찬|水|korean|seafood|grill|고등어 중심
연어구이·구운 채소|水|western|seafood|grill|연어 중심
흰살생선구이·버섯|水|western|seafood|grill|생선 중심
새우 두부찜|水|korean|seafood|steamed|새우 중심의 찜
오징어 숙회·채소무침|水|korean|seafood|seafood_plate|오징어 중심
해물 샤브샤브|水|japanese|seafood|soup|해산물 중심의 국물
두부버섯전골|金|korean|tofu_bean|soup|흰 두부와 버섯 중심
순두부 달걀탕|金|korean|tofu_bean|soup|흰 순두부와 맑은 국물
두부스테이크·구운 채소|金|western|tofu_bean|grill|흰 두부 중심
버섯 두부 샤브샤브|金|japanese|tofu_bean|soup|흰 두부와 맑은 육수
닭가슴살 그린샐러드|木|western|vegetable|salad|푸른 잎채소 중심
새우 아보카도 샐러드|水|western|seafood|salad|새우 중심
참치 병아리콩 샐러드|水|western|seafood|salad|참치 중심
두부 버섯 샐러드|金|western|tofu_bean|salad|흰 두부와 버섯 중심
달걀 렌틸콩 샐러드|土|western|tofu_bean|salad|렌틸콩과 달걀의 곡물형 구성
단호박 리코타 샐러드|土|western|root|salad|노란 단호박 중심
병아리콩 채소 포케|木|western|vegetable|poke|다채로운 생채소 중심
아보카도 달걀 포케|木|western|vegetable|poke|푸른 아보카도 중심
렌틸콩 구운채소 볼|火|western|vegetable|grain_bowl|채소를 굽는 조리
퀴노아 단호박 볼|土|western|rice_grain|grain_bowl|퀴노아와 단호박 중심
새우 통밀 샌드위치|水|western|seafood|sandwich|새우 중심
닭가슴살 아보카도 통밀 샌드위치|金|western|chicken|sandwich|담백한 닭가슴살 중심
참치 오이 통밀 샌드위치|水|western|seafood|sandwich|참치 중심
달걀 채소 통밀 샌드위치|土|western|noodle_wheat|sandwich|통밀과 달걀 중심
훈제연어 통밀 샌드위치|水|western|seafood|sandwich|연어 중심
후무스 구운채소 통밀 샌드위치|火|western|vegetable|sandwich|구운 채소 중심
새우 채소 통밀랩|水|western|seafood|wrap|새우 중심
달걀 아보카도 통밀랩|木|western|vegetable|wrap|푸른 아보카도 중심
두부 채소 통밀랩|金|western|tofu_bean|wrap|흰 두부 중심
후무스 채소 통밀랩|土|western|tofu_bean|wrap|병아리콩과 통밀 중심
오이 달걀 김밥|木|korean|vegetable|gimbap|오이 중심의 채소 김밥
오이 참치 김밥|水|korean|seafood|gimbap|참치와 김 중심
닭가슴살 채소 김밥|金|korean|chicken|gimbap|담백한 닭가슴살 중심
두부 채소 김밥|金|korean|tofu_bean|gimbap|흰 두부 중심
"""

REVIEW = {row[0]: dict(zip(('element', 'cuisine', 'ingredient', 'family', 'reason'), row[1:]))
          for line in _ROWS.strip().splitlines() if (row := line.split('|'))}
NEW_NAMES = tuple(REVIEW)[66:]


def apply_diet_revision(pool, factory):
    by_name = {item.name: item for item in pool}
    if set(by_name) != set(REVIEW) - set(NEW_NAMES):
        raise ValueError('Review every diet dish before changing the catalog')
    for name in NEW_NAMES:
        meta = REVIEW[name]
        by_name[name] = factory(meta['element'], 'diet_' + meta['family'],
                                'breakfast lunch dinner', 'light balanced',
                                meta['ingredient'], meta['cuisine'], name)[0]
    return tuple(replace(by_name[name], element=meta['element'], cuisine=meta['cuisine'],
                         ingredient=meta['ingredient']) for name, meta in REVIEW.items())


def diet_family(name):
    return REVIEW[name]['family']
