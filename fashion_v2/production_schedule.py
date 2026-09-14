"""Actionable production schedule for owner-reviewed fashion boards."""

from dataclasses import dataclass
from calendar import monthrange
from datetime import date, timedelta

from fashion_v2.age_tpo_policy import next_generation_scopes
from fashion_v2.rolling_catalog import rolling_review_batches


SEASON_BY_REVIEW_MONTH = {1: "spring", 4: "summer", 7: "autumn", 10: "winter"}
SEASON_LABEL = {"spring": "봄", "summer": "여름", "autumn": "가을", "winter": "겨울"}
MONTHLY_OBSERVATION_TARGET = 8


@dataclass(frozen=True)
class ProductionPlan:
    event: str
    cycle_id: str
    title: str
    body: str
    standard_scope_count: int
    conditional_scope_count: int

    def as_dict(self):
        return {
            "event": self.event,
            "cycle_id": self.cycle_id,
            "title": self.title,
            "body": self.body,
            "standard_scope_count": self.standard_scope_count,
            "conditional_scope_count": self.conditional_scope_count,
        }


def _scope_counts():
    standard = next_generation_scopes(False)
    all_scopes = next_generation_scopes(True)
    return len(standard), len(all_scopes) - len(standard)


def _next_month(day):
    return date(day.year + (day.month == 12), 1 if day.month == 12 else day.month + 1, 1)


def _cycle_month(today, event):
    # Research and first Trend selection happen during the preceding month.
    return _next_month(today) if event in {"research", "trend_selection"} else today.replace(day=1)


def _monthly_window_plan(event, today):
    cycle = _cycle_month(today, event)
    cycle_id = cycle.strftime("%Y-%m")
    standard, conditional = _scope_counts()
    windows = {
        "research": ("자료 수집", "20~27일", "핵심 편집 출처와 국내 채택 자료를 모아 후보 8개의 반복 신호를 기록합니다."),
        "trend_selection": ("Trend 1차 확정", "28일", "근거를 통과한 후보만 다음 달 화보 후보로 확정합니다."),
        "correction": ("착장 보정", "1~7일", "연령·TPO·현실성·Daily/Trendy 차이를 보정합니다."),
        "final_correction": ("최종 보정", "8일", "제작 직전 착장표와 화보 프롬프트를 동결합니다."),
        "production": ("1~2개월 선행 화보 제작", "9~18일", "초기 4주를 우선하고 이후 1~2개월 온도 구간별 정적 화보를 제작합니다."),
        "release": ("엔진·화보 연결 검사와 배포", "19~20일", "승인된 화보만 엔진과 함께 연결하고 운영 화면을 검사합니다."),
    }
    label, period, purpose = windows[event]
    body = f"""<!-- fashion-board-schedule:{event}:{cycle_id} -->
## {cycle_id} {label}

작업 기간: **{period}**

{purpose}

### 작업 체크
- [ ] 남녀·연령대·TPO별 Daily/Trendy 쌍 확인
- [ ] 경주 기온 구간과 향후 4주 누락 범위 확인
- [ ] Trend 근거와 국내 현실성 확인
- [ ] 여성 30대 이상 가방, 50대 이상 편한 신발 확인
- [ ] 남성 포멀 바지 연결, 30대/50대 넥타이 차이 확인
- [ ] 40대 남성 Business Casual Daily 신발은 단정하게, 운동화는 Trend로 배치
- [ ] 완성 착장 하나만 표시하고 오른쪽 개별 아이템 레일 없음
- [ ] 정오님 승인 전 운영 공개 금지

### 제작 범위
- 표준 {standard}개, 20대 포멀 조건부 {conditional}개
- 엔진 변경과 승인 화보는 함께 배포
"""
    return ProductionPlan(event, f"{event}:{cycle_id}", f"[패션 화보] {cycle_id} {label}", body, standard, conditional)


def _weekly_audit(today):
    standard, conditional = _scope_counts()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    cycle = monday.isoformat()
    body = f"""<!-- fashion-board-schedule:weekly_audit:{cycle} -->
## {monday}~{sunday} 경주 날씨·화보 누락 점검

- [ ] 향후 16일 경주 체감온도·비·강풍 확인
- [ ] 현재 온도 구간의 남녀·연령·TPO별 Daily/Trendy 누락 확인
- [ ] 이미지와 추천 아이템·색상·소재 일치 확인
- [ ] 갑작스러운 날씨 변화가 있으면 중간 보정 이슈 생성
- [ ] 정오님 승인 없는 화보는 공개하지 않음
"""
    return ProductionPlan("weekly_audit", f"weekly_audit:{cycle}",
                          f"[패션 화보] {cycle} 주간 날씨·누락 점검", body,
                          standard, conditional)


def _monthly_plan(today):
    standard, conditional = _scope_counts()
    cycle = today.strftime("%Y-%m")
    batches = rolling_review_batches(today)
    batch_lines = "\n".join(
        f"- [ ] {batch['weather_family']}: {batch['review_on']} 검토 → "
        f"{batch['coverage_start']}~{batch['coverage_end']} 사용 구간"
        for batch in batches
    )
    slots = "\n".join(f"- [ ] 후보 {index}/8 근거 기록" for index in range(1, 9))
    body = f"""<!-- fashion-board-schedule:monthly:{cycle} -->
## {cycle} 패션 후보 관찰

월 1회 관찰 작업입니다. 새로 보인 상품 한 개가 아니라, 같은 스타일 신호가 편집·국내 채택 자료에서 반복되는지 기록합니다.

### 후보 {MONTHLY_OBSERVATION_TARGET}개
{slots}

### 근거 게이트
- [ ] 핵심 편집 출처 2곳 이상에서 반복 확인
- [ ] 국내 채택 출처 1곳 이상 확인
- [ ] 실루엣·소재·색/패턴·신발 중 2가지 이상 변화 확인
- [ ] Daily와 Trendy의 완성 착장 차이가 모바일에서도 명확함
- [ ] 여성 30대 이상 가방, 50대 이상 편한 신발 기준 확인
- [ ] 오른쪽 개별 아이템 없이 완성 착장 하나만 구성

### 35일 선행 검토
{batch_lines}

### 운영 원칙
- 표준 제작 범위: {standard}개, 20대 포멀 조건부 범위: {conditional}개
- 자동 생성·자동 공개 금지
- 정오님이 출처·TPO·현실성·화면 일치를 승인한 보드만 운영 연결
"""
    return ProductionPlan("monthly", f"monthly:{cycle}", f"[패션 화보] {cycle} 월간 후보 관찰", body, standard, conditional)


def _seasonal_plan(today):
    if today.month not in SEASON_BY_REVIEW_MONTH:
        raise ValueError("seasonal review is only scheduled in January, April, July, or October")
    season = SEASON_BY_REVIEW_MONTH[today.month]
    label = SEASON_LABEL[season]
    standard, conditional = _scope_counts()
    cycle = f"{today.year}-{season}"
    body = f"""<!-- fashion-board-schedule:seasonal:{cycle} -->
## {today.year} {label} 정식 화보 제작·검토

분기별 시즌 전환 작업입니다. 월간 관찰에서 근거를 통과한 후보만 제작 대상으로 올립니다.

### 제작 매트릭스
- [ ] 표준 {standard}개: 남녀 × 5개 연령대별 TPO 범위 × 3개 날씨군 × Daily/Trendy
- [ ] 조건부 {conditional}개: 20대 Business Formal, 명시적 포멀 상황에만 사용
- [ ] 각 운영 범위에 Daily/Trendy 두 장이 모두 준비됨

### 화보 QA
- [ ] 완성 착장 하나만 표시하고 오른쪽 개별 아이템 레일 없음
- [ ] 이미지와 추천 아이템·색상·소재가 일치함
- [ ] 여성 30대 이상은 TPO에 맞는 가방 포함
- [ ] 50대 이상 남녀 신발은 편안함 게이트 통과
- [ ] 남성 포멀 바지는 재킷 아래에서 자연스럽게 연결되고 짧아 보이지 않음
- [ ] 모바일 전체 이미지·Daily/Trendy 전환·닫기 버튼 확인

### 승인·배포
- [ ] 정오님 1차 화보 검토
- [ ] 수정안 재검토
- [ ] 승인 보드만 published registry 등록
- [ ] 전체 회귀 테스트 통과
- [ ] PR 병합 후 dalha.kr 운영 확인

자동 공개하지 않습니다. 이 이슈의 승인 체크가 끝난 보드만 운영에 반영합니다.
"""
    return ProductionPlan("seasonal", f"seasonal:{cycle}", f"[패션 화보] {today.year} {label} 시즌 제작·검토", body, standard, conditional)


def production_plan(event, today=None):
    today = today or date.today()
    if event in {"research", "trend_selection", "correction", "final_correction", "production", "release"}:
        return _monthly_window_plan(event, today)
    if event == "weekly_audit":
        return _weekly_audit(today)
    if event == "monthly":
        return _monthly_plan(today)
    if event == "seasonal":
        return _seasonal_plan(today)
    raise ValueError("unknown production schedule event")
