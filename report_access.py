"""리포트 열람 권한 판단. 순수 함수만 둔다 (DB·FastAPI 없이 테스트하기 위해 main.py 에서 분리).

핵심 규칙
- is_unlocked 는 반드시 서버가 '결제(복채 차감) 기록'에서 계산한다. 요청 본문·쿼리·헤더의 값은 쓰지 않는다.
- 기록의 출처는 wallet_store 가 돌려준 reports 목록이며, main.hydrate_account() 가 DB 기준으로 다시 채운 값이다.
- 4단 구조 리포트(business·love·health)만 is_unlocked 를 받는다. 나머지 빌더는 인자를 받지 않는다.
"""
from __future__ import annotations

# 1·2단 무료 + 3·4단 구매 후 공개 (career/love/health 빌더). 'daewoon' 은 lifetime.py 에 is_unlocked 가 아직 없다.
TIERED_REPORTS = frozenset({"business", "love", "health"})

# 보관함에 저장된 풀이가 최신인지 비교할 때 쓰는 키별 문구 버전. main.py 가 빌더 상수로 채운다.
REPORT_PRICES = {
    "daewoon": 450, "sinnian": 300, "gunghap": 350,
    "wealth": 220, "business": 220, "love": 220, "health": 220, "study": 220,
}


def owns_report(reports, report_key: str) -> bool:
    """보관함에 report_key 풀이가 있는가. 항상 bool 을 돌려준다."""
    return any(isinstance(r, dict) and r.get("report_key") == report_key for r in (reports or ()))


def builder_kwargs(report_key: str, unlocked) -> dict:
    """빌더에 넘길 추가 키워드. 4단 구조 리포트만 is_unlocked 를 받고, 값은 `is True` 일 때만 True."""
    if report_key in TIERED_REPORTS:
        return {"is_unlocked": unlocked is True}
    return {}
