"""Editorial daily topic selection over core evidence, not a new saju verdict.

Timing candidates never prove events. Context layers support a daily topic but
are not counted as independent votes. No random topic rotation or sentence cap.
"""

from app.engine.services.daily_evidence import daily_relationship_evidence
from app.engine.services.daily_scenarios import select_daily_scenario
from app.engine.synthesis.operation_scope import usable_operations

_AUTO_SCENARIO = object()

_GODS = {
    'peer': 'self', 'rob_wealth': 'relationships', 'eating_god': 'enjoyment',
    'hurting_officer': 'expression', 'direct_wealth': 'money',
    'indirect_wealth': 'opportunity', 'direct_officer': 'responsibility',
    'seven_killings': 'pace', 'direct_resource': 'learning',
    'indirect_resource': 'reflection',
}
# Heading, body, morning preparation, afternoon practice, evening reflection.
_COPY = {
    'self': ('내 기준을 분명히 하는 날', '오늘의 초점은 자신의 선택입니다. 남의 기대에 맞추는 것과 내가 원하는 것을 구분하는 태도가 중요합니다.', '오늘 꼭 지키고 싶은 것을 하나 정하세요.', '부탁을 받으면 가능한 범위부터 알리세요.', '마음에 걸린 선택은 혼자 정리할 시간을 가져도 좋습니다.'),
    'relationships': ('가까울수록 필요한 배려', '오늘은 사람 사이의 거리와 몫을 돌아볼 주제입니다. 친한 사이라도 시간과 기대까지 같지는 않습니다.', '함께 잡은 약속의 시간과 장소를 챙기세요.', '의견이 다르면 상대가 원하는 것부터 들으세요.', '고마운 마음은 짧은 연락으로 전해도 충분합니다.'),
    'enjoyment': ('작은 즐거움으로 하루를 채우는 날', '오늘의 중심은 일상의 만족입니다. 잘 먹고 취미를 즐기는 시간도 하루를 채우는 소중한 부분입니다.', '식사를 급하게 넘기지 말고 한 끼를 챙기세요.', '손으로 만들거나 몸을 움직이는 활동에 잠깐 몰입해도 좋습니다.', '남은 시간을 모두 채울 필요는 없습니다. 편안한 여백을 남기세요.'),
    'expression': ('할 말은 분명하게 전하는 날', '오늘의 중심은 표현입니다. 생각을 꺼내는 것만큼 상대가 어떻게 받아들이는지도 중요합니다.', '전할 말이 있다면 핵심부터 정리하세요.', '대화에서는 설명을 덧붙이기 전에 상대의 반응을 들으세요.', '마음에 남은 말은 감정이 가라앉은 뒤 다시 꺼내도 됩니다.'),
    'money': ('작은 실속을 챙기는 날', '오늘은 돈의 규모보다 관리 방식에 초점을 둡니다. 반복되는 작은 소비와 약속의 조건이 점검할 부분입니다.', '예정된 결제나 자동이체 내역을 챙기세요.', '구매할 때는 할인율보다 최종 금액을 비교하세요.', '만족스러웠던 소비와 아쉬웠던 소비를 구분하면 다음 선택에 도움이 됩니다.'),
    'opportunity': ('가능성은 열어두고 선택은 신중하게', '오늘의 주제는 새로운 선택지입니다. 흥미로운 제안이라도 얻는 것과 감당할 부담은 따로 볼 필요가 있습니다.', '관심 가는 제안이 있다면 내용을 먼저 읽으세요.', '바로 답할 필요는 없습니다. 빠진 정보부터 물어보세요.', '당장의 매력보다 내 생활에 맞는 선택인지 생각할 시간을 두세요.'),
    'responsibility': ('작은 약속이 신뢰를 만드는 날', '오늘은 책임과 신뢰가 중심 주제입니다. 많은 약속보다 지킬 수 있는 약속이 중요합니다.', '오늘 예정된 약속을 확인하세요.', '감당하기 어려운 부탁에는 범위를 분명히 말하세요.', '답을 기다리는 사람이 있다면 짧게라도 소식을 전하세요.'),
    'pace': ('급할수록 내 속도를 지키는 날', '오늘은 압박 속에서 선택의 순서를 잡는 주제입니다. 모든 요구에 즉시 답하는 것이 책임감은 아닙니다.', '급한 것과 기다려도 되는 것을 나누세요.', '마음이 급하면 답하기 전에 잠깐 멈추세요.', '마무리 뒤에는 알림을 줄이고 쉴 시간을 확보하세요.'),
    'learning': ('배우는 시간과 쉬는 시간', '오늘은 배움과 보충에 초점을 둡니다. 모르는 것을 묻는 태도와 받아들인 내용을 소화할 여유가 중요합니다.', '알고 싶은 질문 하나를 적으세요.', '혼자 막힌 부분은 자료나 다른 사람의 도움을 받아도 좋습니다.', '정보를 더 쌓기보다 오늘 배운 것을 정리하고 쉬세요.'),
    'reflection': ('생각과 사실을 구분하는 날', '오늘은 익숙한 것을 다른 관점에서 바라보는 주제입니다. 떠오른 생각과 확인된 사실을 나누는 태도가 필요합니다.', '마음에 남은 생각을 짧게 기록하세요.', '혼자 내린 결론에 빠진 정보가 없는지 짚으세요.', '답을 내지 못한 생각은 잠시 내려놓아도 됩니다.'),
    'balance': ('익숙한 일상에서 균형 찾기', '지금은 한 방향을 강하게 권할 근거가 충분하지 않습니다. 큰 변화보다 현재 생활에서 편안하게 유지할 부분에 초점을 둡니다.', '오늘 감당할 범위를 정하세요.', '부담이 늘면 일정을 조정해도 됩니다.', '쉬는 시간까지 성과로 채울 필요는 없습니다.'),
}

_SOCIAL = {'relationships', 'expression', 'responsibility'}
_REST_OPS = {'support', 'moisten', 'cool', 'stabilize'}


def select_daily_topics(query, relations, shensha, *, scenario=_AUTO_SCENARIO):
    timing = query.get('timing') or {}
    synthesis = query.get('synthesis') or {}
    daily_god = (timing.get('daily') or {}).get('ten_god')
    main = _GODS.get(daily_god, 'balance')
    confidence = synthesis.get('confidence', 'undetermined')
    if confidence == 'undetermined':
        main = 'balance'
    context = {axis: _GODS.get((timing.get(axis) or {}).get('ten_god'))
               for axis in ('luck_cycle', 'annual', 'monthly')}
    primary_origin = 'timing:daily' if main != 'balance' else 'fallback:uncertain'
    if scenario is _AUTO_SCENARIO:
        scenario = select_daily_scenario(query)
    if scenario:
        main = {'social': 'relationships', 'pace': 'pace', 'expression': 'expression',
                'money': 'money', 'self': 'self', 'learning': 'learning'}[scenario['evidence']['family']]
        primary_origin = 'timing:observed-natal-connection'
    evidence_gate = daily_relationship_evidence(query)
    assessed = evidence_gate['assessed']
    notes = []
    def add(topic, text, origin, status='interpreted', evidence_ids=()):
        if not any(n['origin'] == origin or n['text'] == text for n in notes):
            notes.append(dict(topic=topic, text=text, origin=origin, status=status,
                              evidence_ids=list(evidence_ids)))

    operations = usable_operations(synthesis)
    for op in operations:
        name = op.get('operation')
        # Supplemental daily advice needs an assessed direction AND timing context.
        if main != 'relationships' and name in {'mediate', 'resolve_conflict'} and main in _SOCIAL and bool(assessed):
            add('relationships', '가까운 사람과 의견이 다를 때는 서로 원하는 것을 먼저 확인해 보세요.', 'core:relationship', evidence_ids=op.get('evidence_ids', []))
        if name in _REST_OPS and main in {'pace', 'learning', 'reflection'}:
            add('rest', '피로가 느껴진다면 일정 사이에 쉴 틈을 남기세요.', 'core:rest', evidence_ids=op.get('evidence_ids', []))
    seen = set()
    day_relations = []
    for r in evidence_gate['cautions']:
        members = r.get('members', [])
        if not any(m.get('pillar') == 'timing:daily' for m in members):
            continue
        key = tuple(sorted((m.get('pillar', ''), m.get('position', ''), m.get('symbol', '')) for m in members))
        if key not in seen:
            seen.add(key)
            day_relations.append(r)
    if day_relations:
        add('verification', '결정을 앞두고 있다면 빠뜨린 조건이 없는지 살펴보세요.', 'timing:daily-conditions', 'assessed',
            [r['relationship_id'] for r in day_relations if r.get('relationship_id')])
    # Supporting stars may add a practical note but never select the title.
    star_copy = {
        'flower_canopy': ('reflection', '혼자 생각을 정리하는 시간도 도움이 됩니다.'),
        'literary_star': ('learning', '읽거나 적으면서 생각을 정리해 보세요.'),
        'heavenly_noble': ('relationships', '혼자 막힌 부분은 필요한 도움을 구해보세요.'),
        'peach_blossom': ('relationships', '만남에서는 관심을 표현하되 상대의 반응도 존중해 보세요.'),
        'travel_horse': ('movement', '이동할 계획이 있다면 동선과 시간을 미리 확인해 보세요.'),
    }
    for star in dict.fromkeys(shensha):
        if star in star_copy:
            topic, text = star_copy[star]
            if topic != main and not any(n['topic'] == topic for n in notes):
                add(topic, text, 'shensha:' + star, 'supporting')
    heading, opening, morning, afternoon, evening = _COPY[main]
    if scenario:
        heading, opening = scenario['title'], scenario['opening']
        morning, afternoon, evening = (scenario['time_flow'][k] for k in ('morning', 'afternoon', 'evening'))
    # These are practical scheduling suggestions, not hourly fortune calculations.
    if day_relations:
        afternoon = '중요한 이야기는 서로 같은 뜻으로 이해했는지 확인해 보세요.'
    return dict(title=heading, advice=' '.join([opening] + [n['text'] for n in notes]),
                time_flow=dict(morning=morning, afternoon=afternoon, evening=evening),
                evidence=dict(version='daily-topics-conditional-v4-function-scope', scenario=scenario['evidence'] if scenario else None, primary_topic=main,
                    usable_core_operations=[o.get('operation') for o in operations],
                    primary_origin=primary_origin, context=context, notes=notes,
                    hourly_prediction=False, confidence=confidence,
                    independent_daily_tension_groups=len(seen),
                    candidate_groups_held_back=evidence_gate['candidate_group_count'],
                    timing_assessment_complete=evidence_gate['assessment_complete'],
                    topic_basis='conditional_observed_structure' if scenario else 'editorial_daily_ten_god_mapping',
                    background_only_context=True,
                    no_event_prediction=True))
