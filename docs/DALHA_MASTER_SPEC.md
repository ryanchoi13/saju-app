# DALHA MASTER SPEC
## 프로젝트 기준서 / Single Source of Truth
업데이트: 2026-09-06

> 목적: DALHA 개발에서 확정된 설계, 잠정 기준, 미정 사항, 현재 구현 상태를 한 곳에 보존한다.
> 새 채팅에서는 이 문서를 먼저 읽고 기존 결정을 임의로 바꾸지 않는다.
>
> 상태: [확정] 합의됨 / [잠정] 검증 후 조정 가능 / [미정] 미결정 / [구현] 코드 반영 / [미구현] 설계만 됨

# 1. DALHA의 정체성 [확정]
DALHA는 **생활밀착형 운세 서비스**다.

기본 흐름:
**현재 나의 흐름 → 어떻게 행동할지 → 무엇을 입을지 → 어떤 색을 활용할지 → 무엇을 지닐지 → 무엇을 먹을지 → 기타 생활 선택**

핵심 원칙:
**제대로 된 명리 분석 → 현실 생활로 번역**

재미를 위해 명리 판단을 임의 생성하지 않는다. 사용자가 “맞는다”고 느낄 수 있는 분석 품질이 재방문의 핵심이다.

# 2. 엔진 체계 [확정]
DALHA의 기본/root 언어는 **사주명리학**이다.

명리 코어 적용: 오늘운세, 정통사주/원국, 직업·사업, 재물, 연애·관계, 시험·학업, 월운·연운, 궁합 등.

별도 완결 체계는 독립 엔진으로 둔다: 자미두수, 토정비결, 타로, 성명학.
서로 다른 체계를 한 결과 안에서 출처를 숨긴 채 섞지 않는다.

# 3. DALHA 명리 코어의 역할 [확정]
오늘운세 전용이 아니라 **DALHA 전체 사주 기반 서비스가 공유하는 중앙 명리 코어 엔진**이다.

기능마다 별도 운세 공식을 만드는 대신:
**사주 계산 → 명리 진단 → 종합 판단 → 현재 활성 상태 → Semantic State → 서비스별 번역**

가장 중요한 원칙: **기능부터 운세 문구를 만들지 않는다.**

# 4. 전체 처리 파이프라인 [확정]
1. Birth/Input Layer
2. Natal Fact Calculation
3. Relationship Candidate Detection
4. Relationship Action Resolver
5. Independent Diagnostic Modules
6. Diagnostic Synthesis
7. Timing Overlay
8. Current Activated State
9. Shensha Supporting Layer
10. Semantic Intermediate State
11. Reality-Domain Translation
12. Lifestyle Translation
13. Expression Engine
14. Presentation Layer

각 단계의 원자료·판단 근거를 가능한 한 보존한다.

# 5. 입력 계층
기본 입력 [확정]: 이름, 성별, 생년월일, 양력/음력, 윤달 여부, 출생시간, 생시 미상 여부.

## 생시 미상 [확정]
분석을 중단하지 않는다.
1. 가능한 12개 시주 시나리오 계산
2. 모두에서 유지되는 결론 → 높은 신뢰
3. 일부에서 달라짐 → 조건부/중간 신뢰
4. 크게 뒤집힘 → 단정하지 않고 가능성/낮은 신뢰

즉 **생시 미상 = 분석 거부가 아니라 불확실성 계산**.

출생지/진태양시 convention [미정]: 절입·시간 경계에서 필요한 보정 규칙은 추후 확정.

# 6. 원국 사실 계산층 [확정]
해석과 계산을 분리하고 먼저 객관적 재료를 계산한다.

대상: 년주·월주·일주·시주, 천간·지지, 지장간, 월령/계절, 일간, 오행, 십성, 통근, 투간, 12운성, 합충형파해 관계 후보, 채택 신살의 성립 여부.

절기 기준을 정확히 사용한다. 지장간의 단순 존재와 실제 힘을 구분한다.

# 7. 관계 작용 엔진 [확정]
**관계가 존재한다 ≠ 관계가 실제로 작용한다.**

천간합, 육합, 육충, 삼합, 반합, 형, 파, 해 등은 후보 탐지 후 실제 작용을 별도 판정한다.

판정 요소: 월령, 위치, 통근, 투간, 세력, 관계 완성도, 주변 간지, 다른 합충과의 경쟁, 시간축에서 들어오는 힘.

`삼합100 > 육합80 > 충70` 같은 고정 서열 점수는 사용하지 않는다.
형·파·해는 보존하되 초기에는 주요 합/충보다 낮은 보조 신호로 다룬다.

가능하면 각 관계에 candidate, active/inactive/conditional, strength, reason, source/evidence를 보존한다.

# 8. 독립 진단 모듈 [확정]
최소 다음을 독립 분석 후 종합한다.
1. 격국/구조
2. 억부/세력
3. 조후/환경
4. 병약
5. 통관
6. 특수격/전왕/종격/화격 가능성

# 9. 격국/구조 [확정]
월령은 핵심이지만 월지만 보고 격국 이름을 붙이지 않는다.
월령, 지장간, 투간, 통근, 합화/충 등의 구조 변화, 성격/파격/구응을 함께 본다.
격국 이름보다 **그 구조가 실제 작동하는가**가 중요하다.
격국·억부·조후를 배타적 하나의 정답으로 만들지 않는다.

# 10. 신강·신약 / 억부 [확정]
단순 오행 개수나 덧셈 점수로 결정하지 않는다.

순차 판단:
1. 계절력/득령
2. 뿌리·지장간/득지·통근
3. 주변 생조·극·설·耗
4. 합충 등으로 실제 힘 변화
5. 전체 기세

결과는 극약 → 신약 → 중화권 → 신강 → 극왕 + 특수격 가능성처럼 단계형으로 보존한다.
내부 수치화는 도구로 가능하지만 최종 판단을 단순 임계점 하나로 결정하지 않는다. 근거를 함께 보존한다.

# 11. 조후 [확정]
조후는 “일간이 강한가?”가 아니라 **환경이 지나치게 차갑거나 뜨겁거나 건조하거나 습해 정상 작동이 어려운가**를 보는 독립 진단이다.

`겨울=火`, `여름=水`로 단순화하지 않는다.
월령, 일간, 전체 원국, 기존 火/水/土 상태, 해당 오행의 사용 가능성·뿌리·세력, 한난조습의 극단성을 함께 본다.
조후가 항상 억부보다 우선하거나 항상 부차적인 것이 아니다. 환경 문제가 심각할수록 긴급도가 올라간다.

# 12. 병약 [확정]
질병 예측이 아니다.
**사주의 핵심 병목/문제가 무엇이며 어떤 작용이 그것을 풀어주는가**를 본다.
단순히 없는 오행을 채우는 방식이 아니다.

# 13. 통관 [확정]
강한 두 세력이 충돌할 때 한쪽을 무조건 억제하지 않고 흐름을 연결할 매개 작용을 찾는다. 예: 金→水→木.
단, 매개 오행 자체가 이미 과다/문제인지 확인한다.

# 14. 특수 구조 [확정]
종격·전왕·화격 등은 일반 신강신약 공식으로 억지 처리하지 않는다.
별도 탐지 모듈에서 후보와 성립/파괴 조건을 검토한다. 불확실하면 가능성과 근거를 보존한다.

# 15. 용신/유리한 작용 [확정]
처음부터 `용신=火` 하나로 압축하지 않는다.

각 진단 렌즈를 보존한다:
- 격국상 필요한 작용
- 억부상 필요한 작용
- 조후상 긴급한 작용
- 병약상 해결 작용
- 통관상 매개 작용
- 특수격 유지/파괴 조건

**사주 → 다각도 진단 → 종합 판단 → 이유 보존**.
`격국40+억부30+조후20` 같은 고정 가중치는 현재 채택하지 않는다. 시뮬레이션 후 조정한다.

# 16. 십성 / 12운성 [확정]
십성은 핵심 엔진이다. `재성=돈`, `관성=직장`, `인성=공부`처럼 하나의 십성을 하나의 사건으로 바로 번역하지 않는다.

12운성은 보조 엔진이다. `제왕=무조건 강`, `묘=무조건 약`으로 신강신약을 결정하지 않는다. 음간 순행/역행 및 적용법 차이도 고려한다.

# 17. 시간축 엔진 [확정]
기본: 대운 → 세운 → 월운 → 일진.

서비스에 필요한 범위만 적용:
- 오늘운세: 원국 + 대운 + 세운 + 월운 + 일진
- 연간 재물운: 원국 + 대운 + 세운, 필요 시 월운
- 10년 직업 흐름: 원국 + 대운
- 궁합: A 원국 + B 원국 + 상호작용, 필요한 기간운 추가

고정 가중합 `대운40/세운30/월운20/일진10` 금지.
시간축이 들어올 때마다 관계 네트워크, 강약, 구조, 조후, 십성 활성, 합충 등의 실제 작용을 다시 평가한다.
큰 시간축은 배경, 작은 시간축은 현재 활성 신호.

대운 방향/시작 [잠정]: 양남음녀 순행, 음남양녀 역행; 년간 음양+전통적 성별 기준; 순행 다음 절기/역행 이전 절기; 3일=1년; 가능하면 분수 보존; 월주에서 육십갑자 순서. 정확한 절입 시각 사용. 세부 convention은 구현 전 최종 검증.

# 18. Current Activated State [확정 방향]
시간축 후 현재 상태를 별도 데이터로 만든다.
후보: activated_ten_gods, strength_shift, relationship_changes, climate_shift, structure_changes, favorable_operations, caution_operations, opportunity_signals, pressure_signals.

# 19. Semantic Intermediate State [확정]
명리 계산과 사용자 문구 사이에 의미 계층을 둔다.

예시 필드: overall_flow, energy_direction, favorable_elements, caution_elements, activated_ten_gods, strongest_interactions, opportunity_topics, caution_topics, action_tendencies, emotional_tendencies, expansion, execution, spending_pressure, relationship_tension, mobility, decision_stability.

실제 schema는 구현 명세에서 확정.
목적: 같은 명리 상태에서 오늘운세·재물·직업·컬러·음식·행동 조언이 서로 모순되지 않게 한다.

# 20. 현실 영역 번역 [확정]
영역: 재물, 직업/사업, 연애/관계, 학업/시험, 이동/변화, 대인관계.

하나의 십성을 하나의 현실 사건으로 직결하지 않는다. 여러 십성, 강약, 구조, 유불리, 합충, 시간축을 함께 본다.

# 21. 신살 엔진
## 기본 위치 [확정]
신살은 **명리 코어를 지배하지 않는 보조 시스템**이다. 격국·강약·핵심 판단을 뒤집지 않는다. 코어와 같은 방향이면 해석 근거를 강화할 수 있다.

## 활성 3단계 [확정]
- 관찰: 신살 성립, 독립 코어 근거 약함 → 별도 신살 메뉴
- 활성: 신살 + 같은 현실 테마의 독립 코어 신호 → 해당 영역 보조 근거
- 강한 활성: 신살 + 독립 코어 신호 + 실제 작용력 + 시간축 추가 근거 → 주요 테마 후보

강한 활성이어도 사건 발생을 단정하지 않는다.

## 승격 절차 [확정]
1. 신살 자체가 정확한 규칙으로 성립하는가?
2. 신살과 **독립적으로 계산된** 코어가 같은 현실 테마를 가리키는가?
3. 그 코어 신호가 실제 작용력을 갖는가?
4. 대운/세운/월운/일진에서 추가 근거가 중첩되는가?

같은 글자 하나 때문에 신살과 충이 동시에 파생되면 독립 증거 2개처럼 중복 계산하지 않는다.

## 교차검증 예 [확정]
- 역마 → 이동/변화, 환경전환, 합충, 활동영역 변화
- 도화/함지 → 관계, 노출, 표현, 대인접촉
- 화개 → 몰입, 전문성, 내향적 집중
- 문창 → 인성/식상, 학습, 표현, 문서
- 천을귀인 → 지원/도움과 관련된 유리한 구조
- 겁살/재살 등 → 실제 충돌·압력·손실 신호와 교차검증

## v1 적용 [확정]
v1은 역마, 도화/함지, 화개, 문창, 천을귀인 5개를 먼저 정확히 구현한다. 코어 교차검증, 시간축 활성, 실제 사례 테스트 후 나머지 신살의 추가 여부를 연구·결정한다.
B급 조건부: 장성, 반안, 지살, 겁살, 재살, 망신, 육해, 천살, 월살, 천덕, 월덕 등.
C급 메인 판단 제외 후보: 백호, 탕화, 낙정관, 고신, 과숙 등 공포·사건예측으로 오용되기 쉬운 신살.

## 별도 메뉴 [확정 방향]
가칭 **내 사주에 들어온 살**.
원국/대운/연/월/일 신살, 현재 활성 정도, 전통 의미, 왜 지금 의미 있는지, 활용, 주의를 보여준다.
“활용/주의”는 DALHA의 현대 생활 번역임을 내부적으로 구분한다.

# 22. 표현 엔진 [확정]
명리 사실 → Semantic State → 중요도 선택 → 현실 해석 → 행동 제안 → 자연스러운 한국어.
권장 문장: **판단 → 이유 → 실제 활용**.

AI를 쓰더라도 생년월일만 주고 운세를 창작시키지 않는다. DALHA 엔진이 먼저 판단하고 AI는 구조화된 판단을 설명한다. 근거 chain을 보존해 향후 “왜 이렇게 나왔나요?” 기능을 지원한다.

# 23. 점수 [미정]
사용자 점수 표시는 배제하지 않았으나 미확정.
내부 명리 판단과 presentation score를 분리한다. 83점을 보여줘도 “명리학적으로 객관적인 83점”으로 취급하지 않는다.

# 24. 오늘운세 [확정 목표]
최종적으로 **원국 + 대운 + 세운 + 월운 + 일진**을 명리 코어에서 분석한 Semantic State를 사용한다.
현재 일간 오행 × 오늘 천간 오행 5관계는 임시 버전.

오늘 조언: ① 오늘의 큰 흐름 + ② 실제 행동/개운 방향. 5개 preset 하나로 끝내지 않는다.

# 25. 컬러/패션 엔진
## A+B [확정]
**원국 전체 오행 구조 + 계절/월령 + 오늘 일진 천간·지지와 상호작용 → 오늘 활용/보완/완화할 기운 → A/B 색상 방향 → 적합하면 Wada Duo**.
같은 木이라고 항상 같은 초록을 추천하지 않는다.

## Wada 위치 [확정]
**명리가 주인, Wada는 내부 배색 DB/우선 참고자료**.
1. 명리에서 A 결정
2. A 후보
3. A 포함 Wada Duo 탐색
4. B가 2차 명리 필요와 맞는지 평가
5. 충분하면 원래 pair
6. 아니면 Wada를 버리고 B 직접 선택

우선순위: **명리 적합성 > 배색 조화 > 다양성**.

B 적합도 [잠정]: 80+ Wada B 우선, 60–79 비교, <60 Wada 포기. 코어 후 시뮬레이션 조정.

Wada Duo→Trio로 C를 찾는 방식 폐기 [확정]. 120 Duo 중 Trio에 동일 두 색이 그대로 들어간 경우 3개(2.5%)뿐. 4-color도 사용하지 않는다.

C [확정 방향/미구현]: 명리에서 추가 보완/완화 필요가 강할 때 독립 선택. A+B가 기본, C는 보조.

UI [확정]: Wada/Wada Duo 번호/provenance를 사용자에게 표시하지 않는다. 가칭 **오늘의 추천 컬러 조합**. 영문 색명/HEX는 필요 시 가능.

# 26. 패션 TPO [확정]
사용자 선택: casual / business_casual / business_formal. 기본 casual. 선택을 기억·복원하되 변경 가능. 저장은 미구현.

**TPO = 현실의 절대 경계 / 오늘의 명리 mood = 그 안에서 오늘 에너지를 표현하는 방식**.

남성 business formal: 정장은 재킷/바지 동일 suit이므로 두 Wada 색을 상·하의로 강제 분할하지 않는다. 주요 suit색 navy, charcoal/dark gray, 일부 medium/light gray, black은 더 formal/ceremonial. 셔츠 white/light blue 중심, 일부 pale pastel. accent는 tie, 자연스러운 범위의 belt/shoes, watch 등. **Pocket square 제외.**

여성 business formal: 남성보다 허용 색 범위가 넓으며 light blue, cobalt, green, teal, burgundy/wine, pink, lavender 등도 실제 professional suiting 범위에서 가능. 무제한 허용은 아님.

최종 배치: A+B → TPO → 성별/TPO/item별 색 범위·빈도·우선순위 → 부자연스러우면 다른 item → 그래도 부자연스러우면 사용하지 않음 → mood가 표현 방식 조절.

# 27. 소재/아이템 축 [확정]
소재와 컬러는 독립 축. 색을 소재 추천에 강제로 붙이지 않는다.
style/context + material → 자연스러운 item; 없으면 추천하지 않는다. 구매 압박을 주지 않는다.

# 28. 오늘의 행운 아이템 [확정]
**오늘의 전체 명리 흐름 + 개운/행동 방향**을 기준으로 필요한 행동·상태를 실제 생활에서 돕는 물건 추천.
영역: 일상, 업무, 취미, 이동/여행 등. 패션 액세서리는 기본 우선순위 낮음. 오행 색/재질/형태는 보조 근거. 큰 후보 pool로 자연스럽게 반복 감소; 이력 기반 억지 anti-repeat 금지. 정확한 pool 규모 미정.

# 29. 오늘의 메뉴 [확정]
한국 현대 실제 식생활 + 한국에서 흔한 세계 음식. 후보 약 250~300 [잠정], 최종 2개, 내부 5~10 ranking [잠정].

속성: cuisine, 오행적 해석, warm/cool, season, time, light/hearty, flavor intensity, spicy, oily, broth, texture, 대략 영양 구성.
탄단지 균형 고려, 두 메뉴 모두 탄수화물 위주/유사 메뉴 피함. `火=매운 음식` 금지.

파이프라인: **원국+오늘 → 활용/보완/완화 → 맛/음식 성향 → 계절/시간 → 영양 균형 → pair 다양성 → 최종 2개**.
건강식만 추천하는 서비스가 되지 않는다.

# 30. 행운 숫자 [제외 후보 확정]
하도 오행 수(水1·6, 火2·7, 木3·8, 金4·9, 土5·10)는 있으나 매일 개인화 단일 숫자를 고르는 널리 인정된 명리 규칙이 부족하고 반복감이 큼. 현재 제외 후보 확정. UI/코드 삭제는 최종 구현 때 결정.

# 31. 행운 방향 [확정: 유지]
단순 `木=동쪽`만 사용하지 않는다.

전통 희신방 참고:
甲己→艮 NE / 乙庚→乾 NW / 丙辛→坤 SW / 丁壬→離 S / 戊癸→巽 SE.

24산 8방위: N 壬子癸 / NE 丑艮寅 / E 甲卯乙 / SE 辰巽巳 / S 丙午丁 / SW 未坤申 / W 庚酉辛 / NW 戌乾亥.

무조건 한 방향 승자를 만들지 않는다. 서로 다른 근거로 의미 있으면 최대 2개 정도, 각 방향의 용도/이유를 설명. 하나면 하나만. 다양성을 목표로 하지 않는다. 개인 사주+오늘의 표준화된 자평식 일일 8방위 공식이 확인되지 않았으므로 임의 공식 금지. 기문둔갑 등 별도 체계를 출처 없이 섞지 않는다.

# 32. 성명학 [확정]
**별도 메뉴 + 별도 성명학 엔진**. 명리 코어 내부에 이름을 사주팔자 구성요소처럼 섞지 않는다.
향후 **명리 코어 + 성명학 엔진 → 명리·성명 통합 분석** 가능.

이름 오행을 실제 천간/지지와 동급 힘으로 계산하지 않는다. `사주 火 부족 + 이름 火 = 원국 火 증가` 금지. 대신 명리 코어가 필요로 하는 방향과 이름의 성명학적 특성이 얼마나 조응하는지 별도 관계로 본다.

향후 가칭 **내 이름과 사주**: 이름 자체 분석, 사주와 잘 맞는/충돌하는 부분, 현재 운에서 의미, 강점 활용, 작명/개명 후보 비교. 한자 이름이 필요한 분석과 한글만 가능한 분석을 구분. 세부 성명학 학파/계산법 미정.

# 33. 객관·판단·번역 경계 [확정]
Fact Layer: 사주팔자, 절기, 지장간, 일간, 십성, 오행, 12운성, 운 간지, 관계 후보, 신살 성립 여부.

Judgment Layer: 신강신약, 실제 관계 작용력, 격국 성립, 조후 긴급도, 특수격, 오행/작용의 유용성. **규칙 → 조건 → 예외 → 충돌 → 근거 → 판단**. 학파 차이를 보편적 진리처럼 숨기지 않는다.

Translation Layer: 행동, 컬러, 패션, 음식, 아이템, 현대 생활 영역, 점수(채택 시). 전통 판단과 DALHA 현대 번역을 내부적으로 구분.

# 34. 현재 코드/아키텍처 상태
현재 두 backend 구현이 존재한다.

Root `main.py`: 현재 웹 `index.html`이 실제 사용. 주요 API: `/api/auth/kakao`, `/api/user/register-saju`, wardrobe CRUD, `/api/reports/unlock`, `/api/zodiac-fortune`, `/api/daily-tarot`, `/api/user/charge-coin`, `/api/today-ganji`, `/api/test-saju-engine`.

`backend/app/main.py`: 별도 구조화 FastAPI. 모바일 `mobile/lib/api.dart`는 이 계열 API를 기대. 웹/모바일 API 구조가 갈라져 있음. 장기 통합 필요하지만 지금 전체 재작성 금지.

`backend/app/engine`: lunar-python, korean-lunar-calendar 사용; calendar.py, pillars.py, characters.py, constants.py 등. root의 옛 간이 계산보다 구조화됨.

DB도 root 메모리 dict와 backend/app optional Supabase 구조가 분리되어 있음.

# 35. root main.py 반영 상태
root `get_saju_pillars_and_analysis()`가 backend `calculate_saju()`로 년/월/일주를 가져오도록 변경 [구현]. 현재 call은 `birth_time=None`, `time_unknown=True`; 기존 root 시주 계산은 새 엔진과 아직 통합되지 않음.

KST UTC+9 오늘 날짜 + lunar-python `Solar.fromYmd()`로 오늘 일간/일지 계산 [구현]. `/api/today-ganji` 정상 동작. 2026-09-02 테스트 `己卯`. 이는 smoke test이지 독립 역법 검증 완료 의미는 아님.

# 36. 현재 Today Fortune 임시 로직 [구현/임시]
사용자 일간 오행 × 오늘 일간 오행으로 same/supported/output/wealth/pressure 5관계 생성. 이를 title, score, advice, mindset, action, morning/afternoon/evening에 사용.
**최종 명리 코어가 아니며 새 코어 완성 후 교체.**

# 37. 기존 오늘운세 진행 상태
1. 원국 년/월/일 backend engine 연결 — 완료
2. KST 오늘 간지 — 완료
3. 사용자 일간 오행 — 완료
4. 사용자/오늘 오행 관계 — 완료
5. title+score 동적화 — 완료
6. advice — 완료
7. mindset+action — 완료
8. time_flow — 완료
9. outfit/color/Wada A+B 기본 추천 및 상·하의 배치 — 완료/시각 검증
10. lucky item/number/direction/menu — 기존 hardcoded 부분 남음

1~9의 명리 판단은 최종 코어가 아니라 임시 동적 버전.

# 38. Wada 파일 현황
- `wada_context_placement.py`: 120 Duo × gender × TPO × season × age = 8,640 placement; leaf `top`, `top_hex`, `bottom`, `bottom_hex`.
- `wada_color_rules.py`: 120 Duo / 115 unique HEX, 색상 속성, item heuristic, `score_color_for_item`, `ranked_items_for_color`, `evaluate_duo`.
- `wada_wuxing_selector.py`: day-master + today stem 기반 임시 selector; 최종 코어로 교체 예정.
- `wada_color_ko.py`: 사용자용 한국어 색명.

확정 번역 일부: Deep Indigo→짙은 남색 / Raw Sienna→밝은 갈색 / Madder Brown→붉은 갈색 / Sea Green→민트 청록.

# 39. Wada 연구 결과
Vol.1 일반 구성: 총 348 = 2색120 + 3색120 + 4색108. 일부 디지털 복원은 누락 12개 추가 360; 혼동 금지.

Duo→Trio exact overlap은 3/120=2.5%:
- Duo #23 Cinnamon Buff + Light Mauve → Trio #180 + Neutral Gray
- Duo #34 Eosine Pink + Neutral Gray → Trio #197 + Dark Soft Violet
- Duo #46 Orange + Black → Trio #144 + Rosolanc Purple

Coloriro는 Wada 348 조합의 착장 casebook/reference. Wada 조합과 Coloriro의 의복 배치·비율·계절 분류를 구분하며 현대 DALHA의 최종 권위로 사용하지 않는다.

# 40. 현재 색 selector 한계
`wada_wuxing_selector.py`는 day master element + today stem element + date seed만 사용. 원국 전체, 월령, 강약, 조후, 구조, 오늘 지지, 시간축 상호작용을 아직 사용하지 않는다.

기존 분석: candidate 전체에서 97/120 Duo, 105/115 unique colors 접근 가능하나 개인별 노출은 균형적이지 않음. 1978-03-13 양력(甲木) 예시의 2026-09는 23 unique Duo/37 unique colors. 초록 체감 편중이 있었음.

대응: **먼저 제대로 된 명리 코어를 만든다.** 이후에도 편중되면 패션 다양성 보정 검토. 처음부터 초록 비율을 인위적으로 줄이지 않는다.

# 41. Frontend 패션 현재 동작
`updateTodayWardrobeMatchPick()`가 `daily_fortune.wada_palette` 사용. `top.standard_color`, `bottom.standard_color`로 wardrobe substring match.

`style_mood`: casual→쿨 티셔츠/데님 팬츠, smart_casual→캐주얼 셔츠/치노 팬츠, 기타→드레스 셔츠/슬랙스. accessory logic은 smart_casual을 formal 쪽으로 처리하는 단순화 있음.

현재 배치는 여러 생년월일로 화면 검증했고 기본 결과는 만족. garment placement 로직을 불필요하게 변경하지 않는다.

# 42. UI 보류
- 사용자 UI의 `Wada Duo #...` 제거 [확정/미구현]
- TPO 선택 기억/복원 [확정/미구현]
- 한국어 조사/자연스러움은 나중에 일괄 정리. 현재 `with_wa_gwa()` 정도 존재.

# 43. 개발 작업 원칙 [확정]
- 전체 파일 재작성 금지
- 기존 기능 유지
- 필요한 파일만 수정
- 파일별 변경 내용 제공
- 최소 변경
- 한 단계씩 배포 확인

검증 workflow: **minimal change → GitHub edit/commit → Render deploy → hard refresh → 실제 기능 테스트**.

코드 안내는 파일/위치/삭제/붙여넣기/건드리지 않을 부분을 정확히 안내. snippet에 실제 leading indentation 포함. 한 번에 너무 많은 단계 금지.

현재는 **코딩보다 핵심 원칙을 먼저 확정하는 설계 단계**. 코어 구현 명세가 충분히 확정되기 전 실제 코드 수정 시작하지 않는다.

# 44. 알려진 이슈
- horse zodiac onclick 오류 수정 완료.
- 오늘운세 static 문제 일부 임시 동적화 완료.
- root와 backend/app API/engine 이중화.
- root 시주 계산/elements_weight 등에 옛 간이 방식이 남았을 가능성.
- 오래된 코드는 placeholder/간략 구현일 수 있으며 최근 수정 부분만 production에 가까울 수 있음.
- Gemini/AI에게 프로젝트 전체 clean/rewrite 금지.

# 45. 아직 결정할 주요 사항
명리 코어 v1: 모듈/파일 구조, 데이터 schema, Relationship Resolver 상세 rule, 격국 v1 rule, 신강신약 sequential rule, 조후/병약/통관 rule, 특수격 범위, synthesis rule, uncertainty/confidence/evidence schema, Semantic State 실제 필드, service query interface.

시간: 출생지/진태양시 convention, 대운 시작 세부 convention 검증.

신살: v1 최종 목록, 정확한 성립 규칙, 신살별 core cross-check map, activation 세부 구현.

Presentation: 점수 여부/방식, 설명 길이, confidence 표시.

생활 번역: lucky item pool, menu 250~300 pool, direction synthesis, third color C, material/item rules.

별도 엔진: 성명학, 자미두수, 토정비결 등.

# 46. 다음 작업 순서
**다음 즉시 진행: DALHA 명리 코어 v1 구현 명세**

1. 코어 모듈/파일 경계 설계
2. 공통 데이터 모델 정의
3. Fact Calculation 출력 schema
4. Relationship Resolver 입력/출력 schema
5. 6개 Diagnostic Module 인터페이스
6. Synthesis Engine 인터페이스
7. Timing Overlay 구조
8. Shensha Layer 구조
9. Semantic State schema
10. Service Query/Translation interface
11. Evidence/Confidence 구조
12. v1/v2 범위 분리
13. 테스트 대표 사주 및 경계 사례
14. 시뮬레이션 후 규칙 보정
15. 그 다음 실제 코드 구현

# 47. 명리 코어 v1 구현 명세 확정 [확정]

2026-09-06 `DALHA_MYEONGRI_CORE_V1_SPEC.md`로 상세 구현 명세를 분리 확정했다.

확정 범위: 모듈 경계, 공통 schema, Fact Layer, Relationship Resolver, 격국·억부·조후·병약·통관·특수구조 독립 진단, Synthesis, 시간축, 신살 5개, Semantic State, Service Query, evidence/confidence/uncertainty, v1 범위, 테스트 기준.

모든 사주 기반 메뉴는 별도 운세 공식을 만들지 않고 같은 코어를 사용한다. 평생운세는 원국+대운, 올해운세는 원국+현재 대운+세운, 평생 재물운은 원국 재물 구조+전체 대운, 올해 재물운은 원국 재물 구조+대운+세운(필요 시 월운), 오늘운세는 원국+대운+세운+월운+일진을 사용한다.

건강 관련 결과는 질병·사고·수명 예측이 아니라 조후·소모·압박·생활 리듬을 생활관리 조언으로 번역한다.

첫 연결은 정통사주·원국 분석이며 검증 후 오늘운세에 연결한다. 기존 오늘운세와 Wada 착장 배치는 새 코어가 검증되기 전까지 유지한다.

다음 실제 작업: 최신 백엔드 구조와 테스트 현황을 확인한 뒤 공통 Schema부터 최소 변경으로 구현한다.

# 48. 새 채팅 시작 규칙
사용자가 **“DALHA_MASTER_SPEC 기준으로 계속하자. 명리 코어 v1 구현 명세부터.”**라고 하면:
1. 이 파일을 실제로 찾아 읽는다.
2. 기억만으로 진행하지 않는다.
3. [확정]을 임의 변경하지 않는다.
4. 변경 필요 시 이유를 먼저 설명하고 사용자와 결정한다.
5. [잠정]/[미정]을 검토·확정한다.
6. 최신 코드 작업은 이 문서가 아니라 최신 GitHub/업로드 파일을 코드 source of truth로 사용한다.
7. 중요한 새 결정은 MASTER SPEC에도 반영한다.

# 49. 한 문장 원칙 [확정]
**DALHA는 전통 명리의 계산과 판단 근거를 가능한 한 정직하게 보존하고, 그것을 현대 사용자가 실제 생활에서 이해하고 활용할 수 있는 형태로 번역하는 서비스다.**
