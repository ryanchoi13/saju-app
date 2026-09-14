"""Actionable production schedule for owner-reviewed fashion boards."""

from dataclasses import dataclass
from datetime import date

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
    if event == "monthly":
        return _monthly_plan(today)
    if event == "seasonal":
        return _seasonal_plan(today)
    raise ValueError("event must be monthly or seasonal")

