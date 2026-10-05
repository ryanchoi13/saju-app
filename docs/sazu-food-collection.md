# SAZU 음식 데이터 수집안 (2026-10-05)

현재 상태: 구현·로컬 테스트만 완료. 실제 수집/운영 배포 전. 키와 개인 결과는 저장소에 포함하지 않는다.

## 확인한 범위

- 공식 OpenAPI의 공개 경로 25개를 확인했다. 음식 전체 카탈로그를 내려주는 공개 경로는 없었다.
- 공식 `@sazuapp/client` 0.10.0과 `@sazuapp/mcp-server` 0.5.0 배포 코드를 직접 읽었다. HTTP 호출 도구이며 음식 원본 DB나 고정 기운 사전은 포함하지 않는다.
- `/v2/sazu/food`에 `foodPlan: monthly`를 주면 기간 식단과 장보기 목록을 받는다. 기존 달하 호출에는 이 옵션이 없다.
- `date`, 다른 출생 입력, `foodRotation`, `foodAvoid`를 바꾸는 공식 입력은 존재한다. 전체 수집이 보장되는 것은 아니다.
- `foodAvoid`는 재료군과 관련 음식을 제외하며 `avoidRequest.names`를 돌려준다. 추가 목록을 발견할 수 있지만 음식별 고정 오행·한열의 근거가 되는 것은 아니다.
- 현재 서비스는 Render Free이므로 Shell/SSH와 one-off job이 없다. 키를 꺼내지 않고 기존 서버에서 돌리려면 실행 코드 반영이 필요하다.

## 단계별 실행

1. 기존 테스트 계정과 공식 샘플 입력 5개로 같은 기준일부터 월간 응답을 받는다. 첫 실행은 음식 호출 최대 6건. 테스트 계정이 여러 개면 그 계정들이 우선되어 샘플 일부가 다음 실행으로 밀린다.
2. 실제 월간 `plan.days` 구조와 날짜 수, 음식 ID·이름·설명·주의·신규 항목 수를 확인한다. 샌드박스이면 범위 추정에 사용하지 않는다.
3. 결과 확인 후 명시 날짜 목록에 계절별 날짜를 추가한다. 예: 2026-01-15, 2026-04-15, 2026-07-15, 2026-10-15. 한 실행 음식 호출 상한은 30건.
4. 여러 샘플이라도 용신/부족 오행이 같을 수 있다. 실제 boost/reduce가 얼마나 다른지 검사한 뒤 필요한 조건만 보충한다.
5. 관측한 신규 ID 수가 줄어드는 것은 수집 포화의 징후이며 전체 확보 증거가 아니다. 전체 개수·원본 분류값이 필요하면 제공자의 공식 데이터 내보내기 범위를 확인해야 한다.

## 구현

- `sazu_food_research`: 요청 해시, 날짜, 요청 입력, 처리 상태, foodBalance 원문, 수신 시각.
- `sazu_food_observations`: 음식 ID, 이름, 원문 항목, 응답 내 위치, 원본 요청 연결.
- 이름/계정 ID는 SAZU에 보내지 않는다. 연구용 요청 입력은 접근 제한된 기존 DB에만 저장한다.
- `foodBalance`만 저장한다. 다른 사주 모듈이나 키를 브라우저·로그·저장소에 기록하지 않는다.
- 원문에 없는 오행/한열 값을 boost/reduce나 추천 이유로부터 추정해 음식 속성에 채우지 않는다.
- 기존 추천 화면/당일 캐시/사용 기록은 변경하지 않는다. 별도 공개 실행 API도 만들지 않는다.
- 명시한 요청마다 DB에서 먼저 처리권을 확보한다. 완료·실패·중단된 동일 요청은 자동 재호출하지 않는다. 중단 상태는 사람이 확인한다.
- `/v2/me`로 포함량 잔여를 확인하고 50회 여유를 남긴다. 한도 불명·무료 키·오류·월간 식단 누락이면 중단한다. 초기 잔여 확인 외에 각 음식 호출 전 재확인한다. 메타데이터 조회도 rate limit을 준수한다.
- 첫 실행 6건 상한은 음식 요청 수이며 상태/샘플 조회는 별도다. 실제 SAZU의 포함량/청구는 계정 응답으로 확인한다.

## 활성화 (승인 후)

기존 `SAZU_API_KEY`, `DATABASE_URL`, `DALHA_TEST_USER_IDS`를 그대로 사용한다.

- `SAZU_FOOD_COLLECT_ENABLED=1`
- `SAZU_FOOD_COLLECT_DATES=2026-10-05`
- `SAZU_FOOD_COLLECT_LIMIT=6`
- 선택: `SAZU_FOOD_COLLECT_USERS`로 정확한 테스트 계정을 지정. 미설정 시 기존 테스트 계정 사용.

비활성 기본값이며 시작 스레드는 즉시 반환한다. 재배포/시작 때 명시 작업을 처리한다. 완료 후 ENABLED를 0으로 돌릴 수 있다. 연구 행은 보존한다.

검증 SQL:

```sql
SELECT state, count(*) FROM sazu_food_research GROUP BY state;
SELECT count(DISTINCT food_id) FROM sazu_food_observations;
SELECT food_id, min(food_name), count(DISTINCT request_key)
FROM sazu_food_observations GROUP BY food_id ORDER BY count(DISTINCT request_key) DESC;
```

월간 식단 중복 분석은 월간 API 결과에 대한 분석이다. 하루치 API를 30번 호출한 결과나 아직 구현되지 않은 완성 메뉴 3개 추천의 중복률과 같다고 보고하지 않는다.

## 검증

`PYTHONPATH=. python3 -m unittest discover -s backend/tests -p 'test_sazu_food*.py' -v`

13개 통과: 기존 7개 + 수집기 6개. 출처/원문 유지, 이름·ID 제거, 요청 상한, 재실행 중복 방지, 오류 원문 비노출, 무료/불명 한도 중단, 기본 비활성 확인. 실제 API는 아직 호출하지 않았다.

## 원출처

- https://www.sazu.app/manse-api/openapi.json
- https://www.sazu.app/manse-api/docs
- https://www.sazu.app/manse-api/blog/saju-api-food-topic-guide
- https://registry.npmjs.org/@sazuapp/client/0.10.0
- https://registry.npmjs.org/@sazuapp/mcp-server/0.5.0
- https://render.com/docs/free
