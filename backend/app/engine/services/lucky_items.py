"""오늘의 행운 아이템 (2026-11-12 정오님 결정).

결정 문서: 프로젝트 claude/decisions-2026-11-12-lucky-item.md

- 오행 = 행운 색 1칸과 같은 오행(element_balance.luck_card_element). 피함 오행은 나오지 않는다.
- 쓰임 = 그날 일진 십성 10칸. 십성 뜻(비겁=나, 식상=표현·먹고 즐김, 재성=돈·살림, 관성=규칙·책임,
  인성=배움·쉼)은 명리 일반론이고, 그 뜻을 물건으로 잇는 것은 달하의 번역이다(고전 규칙 아님).
- 오행 → 재질·색은 현대 개운법 관례(木 나무·초록 / 火 붉은 / 土 베이지·흙 / 金 메탈·흰 / 水 남색·검정).
  향으로 오행을 나누는 것은 근거가 약해 쓰지 않는다.
- 신살은 쓰지 않는다. 시안에서는 후보를 보탰는데, 신살이 거의 매일 걸려(사람마다 하루 1~3개) 같은 아이템이
  일주일 안에 다시 나온 날이 11%였다. 신살 단독으로 정하지 않는다는 daily.py 원칙과도 맞춘다.
- 계절은 달력 월. 성별 태그는 예전 남성 대체 관행(파우치·헤어집게 여성, 넥타이·머니클립 남성)만 이어 간다.
- 십성 칸끼리 아이템이 겹치지 않으므로, 같은 십성이 돌아오는 10일마다 후보를 하나씩 넘기면
  기록 없이도 같은 종류가 7일 안에 다시 나오지 않는다(10일 안에 한 번씩만 나온다).
"""
from __future__ import annotations

from datetime import date
import hashlib

ITEMS_VERSION = "lucky-items-v2-20261112"

_W, _F, _E, _M, _S = "木", "火", "土", "金", "水"


def _v(wood, fire, earth, metal, water):
    return {k: v for k, v in zip((_W, _F, _E, _M, _S), (wood, fire, earth, metal, water)) if v}


# key: (계절, 성별, 오행별 이름). 계절 all/winter/summer/mild, 성별 None/'female'/'male'
CATALOG: dict[str, tuple[str, str | None, dict[str, str]]] = {
    # 비견 — 내 속도
    "socks": ("all", None, _v("올리브 양말", "버건디 양말", "카멜 양말", "그레이 양말", "네이비 양말")),
    "cap": ("all", None, _v("올리브 캡 모자", "버건디 캡 모자", "베이지 캡 모자", "그레이 캡 모자", "네이비 캡 모자")),
    "keyring": ("all", None, _v("나무 키링", "붉은색 키링", "베이지 가죽 키링", "메탈 키링", "남색 키링")),
    "hairclip": ("all", "female", _v("올리브 헤어집게", "코럴 헤어끈", "베이지 헤어집게", "실버 헤어핀", "블랙 헤어집게")),
    # 겁재 — 앞서 나가는 힘을 다듬기
    "ring": ("all", None, _v("나무 반지", "로즈골드 반지", "세라믹 반지", "실버 반지", "블랙 반지")),
    "bracelet": ("all", None, _v("우드 비즈 팔찌", "붉은 실 팔찌", "브라운 가죽 팔찌", "실버 체인 팔찌", "블랙 비즈 팔찌")),
    "handcream": ("all", None, _v("올리브 튜브 핸드크림", "코럴 튜브 핸드크림", "베이지 튜브 핸드크림",
                                  "실버 튜브 핸드크림", "네이비 튜브 핸드크림")),
    # 식신 — 먹고 쉬며 즐김
    "tumbler": ("all", None, _v("나무 뚜껑 텀블러", "붉은 머그", "도자기 머그", "스테인리스 텀블러", "유리 물병")),
    "lunchbag": ("all", None, _v("리넨 도시락 가방", "붉은 도시락 가방", "베이지 도시락 가방",
                                 "실버 보냉 도시락 가방", "남색 도시락 가방")),
    "handkerchief": ("all", None, _v("리넨 손수건", "붉은 체크 손수건", "베이지 면 손수건", "흰 면 손수건", "남색 손수건")),
    "fan": ("summer", None, _v("대나무 부채", "붉은 부채", "한지 부채", "흰 부채", "남색 부채")),
    # 상관 — 말과 재치
    "pen": ("all", None, _v("나무 볼펜", "붉은색 포인트 펜", "베이지 볼펜", "메탈 소재 펜", "남색 만년필")),
    "lipbalm": ("all", None, _v("올리브 케이스 립밤", "레드 틴트 립밤", "베이지 케이스 립밤",
                                "실버 케이스 립밤", "네이비 케이스 립밤")),
    "tape": ("all", None, _v("잎 무늬 마스킹테이프", "붉은 체크 마스킹테이프", "크라프트 마스킹테이프",
                             "은박 마스킹테이프", "물결 무늬 마스킹테이프")),
    # 정재 — 실속
    "cardwallet": ("all", None, _v("나무 소재 카드 케이스", "버건디 카드지갑", "카멜 카드지갑", "메탈 카드 케이스", "남색 카드지갑")),
    "coinpurse": ("all", None, _v("리넨 동전지갑", "붉은 동전지갑", "브라운 가죽 동전지갑", "실버 동전지갑", "남색 동전지갑")),
    "pouch": ("all", "female", _v("초록 파우치", "붉은색 포인트 파우치", "베이지 지퍼 파우치", "실버 파우치", "남색 파우치")),
    "moneyclip": ("all", "male", _v(None, None, "브라운 가죽 머니클립", "메탈 머니클립", "블랙 머니클립")),
    # 편재 — 돈과 발이 바깥으로
    "ecobag": ("all", None, _v("리넨 에코백", "버건디 에코백", "베이지 캔버스 에코백", "흰 에코백", "남색 에코백")),
    "bag": ("all", None, _v("올리브 캔버스 백팩", "버건디 크로스백", "베이지 크로스백", "그레이 슬링백", "블랙 백팩")),
    "keycase": ("all", None, _v("나무 열쇠고리", "붉은 가죽 키 케이스", "베이지 키 케이스", "메탈 열쇠고리", "남색 키 케이스")),
    "sunglasses": ("summer", None, _v("우드 프레임 선글라스", "버건디 테 선글라스", "브라운 렌즈 선글라스",
                                      "메탈 프레임 선글라스", "블랙 선글라스")),
    # 정관 — 약속과 시간
    "watch": ("all", None, _v("나무 줄 손목시계", "버건디 가죽 줄 시계", "브라운 가죽 줄 시계", "메탈 손목시계", "남색 다이얼 시계")),
    "planner": ("all", None, _v("초록 표지 다이어리", "붉은 표지 플래너", "크라프트 표지 다이어리", "흰 표지 플래너", "남색 다이어리")),
    "cardcase": ("all", None, _v("나무 명함 케이스", "버건디 명함지갑", "카멜 명함지갑", "메탈 명함 케이스", "남색 명함지갑")),
    "tie": ("all", "male", _v("올리브 넥타이", "버건디 넥타이", "카멜 넥타이", "실버 넥타이핀", "네이비 넥타이")),
    # 편관 — 긴장과 대비
    "belt": ("all", None, _v("올리브 캔버스 벨트", "버건디 가죽 벨트", "브라운 가죽 벨트", "실버 버클 벨트", "블랙 가죽 벨트")),
    "badge": ("all", None, _v("나뭇잎 핀 배지", "붉은 에나멜 배지", "도자기 핀 배지", "실버 핀 배지", "남색 에나멜 배지")),
    "umbrella": ("all", None, _v("올리브 접이식 우산", "버건디 접이식 우산", "베이지 접이식 우산",
                                 "실버 접이식 우산", "네이비 접이식 우산")),
    "gloves": ("winter", None, _v("올리브 니트 장갑", "버건디 장갑", "브라운 가죽 장갑", "그레이 장갑", "블랙 가죽 장갑")),
    # 정인 — 배우고 정리
    "notebook": ("all", None, _v("초록 표지 메모장", "붉은 표지 노트", "베이지 메모패드", "흰 표지 노트", "남색 노트")),
    "bookmark": ("all", None, _v("나무 책갈피", "붉은 리본 책갈피", "가죽 책갈피", "메탈 책갈피", "남색 리본 책갈피")),
    "pencil": ("all", None, _v("원목 연필", "붉은 색연필", "크라프트 연필", "메탈 샤프", "남색 연필")),
    # 편인 — 혼자 쉬며 채움
    "earphone": ("all", None, _v("올리브 이어폰 케이스", "코럴 이어폰 케이스", "베이지 이어폰 케이스",
                                 "화이트 무선 이어폰", "블랙 무선 이어폰")),
    "eyemask": ("all", None, _v("리넨 안대", "버건디 안대", "베이지 안대", "아이보리 실크 안대", "네이비 안대")),
    "scarf": ("mild", None, _v("올리브 스카프", "버건디 스카프", "카멜 스카프", "아이보리 스카프", "네이비 스카프")),
    "muffler": ("winter", None, _v("올리브 목도리", "버건디 목도리", "카멜 목도리", "그레이 목도리", "네이비 목도리")),
    "blanket": ("winter", None, _v("초록 체크 무릎담요", "붉은 체크 무릎담요", "베이지 무릎담요",
                                   "아이보리 무릎담요", "네이비 무릎담요")),
    "mirror": ("all", None, _v("나무 손거울", "붉은 손거울", "베이지 손거울", "실버 손거울", "블랙 손거울")),
    "battery": ("all", None, _v("올리브 보조배터리", "코럴 보조배터리", "베이지 보조배터리", "메탈 보조배터리", "네이비 보조배터리")),
}

# 십성 → (그날 말, 후보). 칸끼리 겹치지 않는다(겹치면 10일 안 재등장이 생긴다 — 테스트로 막음).
BY_TEN_GOD: dict[str, tuple[str, tuple[str, ...]]] = {
    "peer": ("내 속도로 가는 날", ("socks", "cap", "keyring", "hairclip")),
    "rob_wealth": ("힘이 앞서 나가는 날", ("ring", "bracelet", "handcream")),
    "eating_god": ("먹고 쉬며 즐기는 날", ("tumbler", "lunchbag", "handkerchief", "fan")),
    "hurting_officer": ("말과 재치가 앞서는 날", ("pen", "lipbalm", "tape", "mirror")),
    "direct_wealth": ("실속을 챙기는 날", ("cardwallet", "coinpurse", "pouch", "moneyclip")),
    "indirect_wealth": ("돈과 발이 바깥으로 도는 날", ("ecobag", "bag", "keycase", "battery", "sunglasses")),
    "direct_officer": ("약속과 시간이 앞서는 날", ("watch", "planner", "cardcase", "tie")),
    "seven_killings": ("긴장하고 대비하는 날", ("belt", "badge", "umbrella", "gloves")),
    "direct_resource": ("배우고 정리하는 날", ("notebook", "bookmark", "pencil")),
    "indirect_resource": ("혼자 쉬며 채우는 날", ("earphone", "eyemask", "scarf", "muffler", "blanket")),
}

def season_fits(season: str, month: int) -> bool:
    if season == "all":
        return True
    if season == "winter":
        return month in (11, 12, 1, 2)
    if season == "summer":
        return month in (6, 7, 8)
    return month in (3, 4, 5, 9, 10, 11)   # mild


def candidates(ten_god: str, element: str, month: int, gender: str | None) -> list[str]:
    def fits(key: str) -> bool:
        season, sex, names = CATALOG[key]
        return element in names and season_fits(season, month) and (sex is None or sex == gender)

    base = BY_TEN_GOD.get(ten_god, BY_TEN_GOD["direct_resource"])[1]
    keys = [k for k in base if fits(k)]
    if not keys:   # 예: 여름 남성 + 후보 오행이 없는 칸. 정인 칸은 모든 오행·계절이 있다.
        keys = [k for k in BY_TEN_GOD["direct_resource"][1] if fits(k)]
    return keys


def pick(ten_god: str, element: str, target: date, gender: str | None, person_key: str) -> dict:
    keys = candidates(ten_god, element, target.month, gender)
    salt = int(hashlib.sha256(f"lucky-item|{person_key}".encode()).hexdigest()[:8], 16)
    key = keys[(target.toordinal() // 10 + salt) % len(keys)]
    day_phrase = BY_TEN_GOD.get(ten_god, BY_TEN_GOD["direct_resource"])[0]
    return dict(key=key, name=CATALOG[key][2][element], day_phrase=day_phrase, candidates=keys)
