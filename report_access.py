"""리포트 열람 권한 판단. 순수 함수만 둔다 (DB·FastAPI 없이 테스트하기 위해 main.py 에서 분리).

핵심 규칙
- is_unlocked 는 반드시 서버가 '결제(복채 차감) 기록'에서 계산한다. 요청 본문·쿼리·헤더의 값은 쓰지 않는다.
- 기록의 출처는 wallet_store 가 돌려준 reports 목록이며, main.hydrate_account() 가 DB 기준으로 다시 채운 값이다.
- 4단 구조 리포트(business·venture·love·health·wealth·study)만 is_unlocked 를 받는다. 나머지 빌더는 인자를 받지 않는다.
"""
from __future__ import annotations

# 1·2단 무료 + 3·4단 구매 후 공개 (career/love/health/wealth/study 빌더). 'daewoon' 은 lifetime.py 에 is_unlocked 가 아직 없다.
TIERED_REPORTS = frozenset({"business", "venture", "love", "health", "wealth", "study"})

# 무료 공개 리포트. 현재 대운·타고난 성향은 무료이고 미래 대운은 빌더가 잠금 티저로만 만든다(본문 없음).
FREE_REPORTS = frozenset({"daewoon"})
PREVIEW_REPORTS = TIERED_REPORTS | FREE_REPORTS

# 보관함에 저장된 풀이가 최신인지 비교할 때 쓰는 키별 문구 버전. main.py 가 빌더 상수로 채운다.
REPORT_PRICES = {
    "daewoon": 450, "sinnian": 300, "gunghap": 250,
    "wealth": 220, "business": 220, "venture": 220, "love": 220, "health": 220, "study": 220,
}


def owns_report(reports, report_key: str) -> bool:
    """보관함에 report_key 풀이가 있는가. 항상 bool 을 돌려준다."""
    return any(isinstance(r, dict) and r.get("report_key") == report_key for r in (reports or ()))


def builder_kwargs(report_key: str, unlocked) -> dict:
    """빌더에 넘길 추가 키워드. 4단 구조 리포트만 is_unlocked 를 받고, 값은 `is True` 일 때만 True."""
    if report_key in TIERED_REPORTS:
        return {"is_unlocked": unlocked is True}
    return {}


# 공개 범위(10/15 결정): 이 풀이들은 아직 팔지 않는다 — 화면은 '곧 열려요'로 보여 준다(index.html DALHA_SOON_REPORTS 와 같은 목록).
# 화면만 막으면 결제 창구에 직접 요청해 살 수 있으므로 서버에서도 막는다(11/23 점검). 등록된 테스트 계정은 살 수 있다.
# 11/25 정오님: 테마운을 다 만들었으니 '곧 열려요'는 없었던 일로 — 모든 풀이를 복채로 바로 산다.
# 다시 막을 풀이가 생기면 여기와 index.html DALHA_SOON_REPORTS 에 같이 넣는다.
SOON_REPORTS = frozenset()


def on_sale(report_key, is_tester=False):
    return is_tester or report_key not in SOON_REPORTS
