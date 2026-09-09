"""Conditional life advice from observed structure; NOT a strongest-fortune verdict.

Ordering below is DALHA editorial policy, not classical probabilities. Only
natal-connected observations nominate a subject. Background can break a subject
tie but cannot introduce one. No date hash, random choice, or repetition penalty.
"""
from app.engine.services.daily_scene_context import JOIN_CONTEXT, CHANGE_CONTEXT

FAMILIES = {
    'peer': 'self', 'rob_wealth': 'social',
    'eating_god': 'expression', 'hurting_officer': 'expression',
    'direct_wealth': 'money', 'indirect_wealth': 'money',
    'direct_officer': 'pace', 'seven_killings': 'pace',
    'direct_resource': 'learning', 'indirect_resource': 'learning',
}
JOIN = {'stem_combination', 'branch_six_combination', 'branch_three_combination', 'branch_directional_combination'}
CHANGE = {'branch_clash'}
# Title, body, morning, afternoon, evening, one concrete action.
COPY = {
('social', 'join'): ('함께할 일은 먼저 뜻을 맞추세요', '사람과 함께하는 계획이 있다면 서로 바라는 것부터 나누세요. 친하다는 이유로 말하지 않은 기대까지 같다고 생각할 필요는 없습니다.', '만날 사람에게 전하고 싶은 내용을 정하세요.', '같이 정할 일은 상대의 의견을 먼저 들으세요.', '오늘 고마웠던 사람에게 짧게 마음을 전해도 좋습니다.', '함께 잡은 약속 하나의 시간과 장소를 확정하세요.'),
('social', 'change'): ('다른 의견 앞에서 서두르지 않기', '의견이 갈린다면 바로 설득하려 하기보다 무엇이 다른지부터 짚으세요. 한 번의 반응으로 사람 전체를 판단하지 않는 편이 좋습니다.', '민감한 이야기는 급한 시간대를 피하세요.', '불편한 점은 상대의 성격보다 구체적인 행동을 말하세요.', '답장이 늦어도 이유를 미리 단정하지 마세요.', '의견이 다른 사람에게 이유를 한 번 더 물어보세요.'),
('social', 'mixed'): ('가까운 사이에도 여유가 필요합니다', '함께하고 싶은 마음과 혼자 있고 싶은 마음이 동시에 들 수 있습니다. 약속을 무리하게 늘리기보다 서로 편안한 거리를 이야기하세요.', '오늘 만남에 쓸 수 있는 시간을 가늠하세요.', '부탁을 받으면 가능한 부분과 어려운 부분을 나눠 말하세요.', '대화가 길어지면 다음에 이어가도 괜찮습니다.', '부담되는 약속 하나의 시간이나 범위를 조율하세요.'),
('money', 'join'): ('함께 쓰는 돈일수록 기준을 분명하게', '공동 구매나 비용을 나눌 일이 있다면 금액과 부담할 몫부터 맞추세요. 좋은 뜻으로 시작해도 계산을 생략할 필요는 없습니다.', '함께 결제할 내역이 있는지 살펴보세요.', '가격뿐 아니라 취소와 환불 조건도 읽으세요.', '정산할 일이 남았다면 기록을 한곳에 모으세요.', '나눠 낼 비용 하나의 금액과 정산일을 정하세요.'),
('money', 'change'): ('마음이 바뀌면 구매도 멈춰도 됩니다', '사려고 했다는 이유만으로 결제할 필요는 없습니다. 조건이 달라졌다면 예산과 필요를 다시 따져보세요.', '구매 목록에서 지금 필요한 것만 남기세요.', '예상보다 비싸다면 다른 선택과 비교하세요.', '쓰지 않는 물건을 살펴보면 다음 소비의 기준이 보입니다.', '급하지 않은 구매 하나는 결제를 미루세요.'),
('money', 'mixed'): ('좋아 보여도 부담할 몫은 따로 보세요', '끌리는 제안이 있다면 혜택과 의무를 함께 읽으세요. 시작할 때의 비용뿐 아니라 유지하거나 그만둘 때의 조건도 중요합니다.', '관심 있는 상품의 전체 비용을 확인하세요.', '설명이 빠진 조건은 결제 전에 물어보세요.', '사고 싶은 마음과 실제 사용할 계획을 구분하세요.', '검토 중인 선택 하나의 추가 비용을 확인하세요.'),
('expression', 'join'): ('좋아하는 것을 함께 나누기', '취미나 관심사를 나눌 자리가 있다면 완벽하게 준비할 때까지 기다릴 필요는 없습니다. 상대가 함께 즐길 수 있도록 설명은 쉽고 짧게 시작하세요.', '나누고 싶은 사진이나 이야기를 하나 골라두세요.', '내 이야기 뒤에는 상대의 취향도 물어보세요.', '함께 즐긴 것 중 다시 하고 싶은 것을 기억해 두세요.', '좋아하는 음악이나 사진 하나를 가까운 사람과 나눠보세요.'),
('expression', 'change'): ('익숙한 방식에서 한 걸음 벗어나기', '하던 방식이 답답하다면 작은 부분부터 바꿔보세요. 취미든 표현이든 처음 시도한 결과를 곧바로 잘하고 못함으로 나눌 필요는 없습니다.', '바꿔보고 싶은 방법을 하나 정하세요.', '평소와 다른 순서나 도구로 가볍게 시도하세요.', '결과보다 어떤 과정이 즐거웠는지 돌아보세요.', '익숙한 취미를 평소와 다른 방법으로 잠깐 즐겨보세요.'),
('expression', 'mixed'): ('솔직한 표현에도 전할 순서가 있습니다', '하고 싶은 말이 많다면 가장 전하고 싶은 뜻부터 고르세요. 솔직하게 말하는 것과 한 번에 모두 쏟아내는 것은 다릅니다.', '전할 내용 중 핵심과 부연 설명을 나누세요.', '상대가 이해했는지 듣고 다음 말을 이어가세요.', '감정이 섞인 메시지는 보내기 전에 다시 읽으세요.', '길게 쓴 메시지에서 가장 중요한 문장 하나를 앞에 두세요.'),
('learning', 'join'): ('혼자 막힌 질문은 함께 풀어보세요', '이해가 멈춘 부분은 다른 설명을 듣는 것도 방법입니다. 도움을 구할 때는 어디까지 이해했고 무엇이 막혔는지 구체적으로 말하세요.', '알고 싶은 질문을 하나 적으세요.', '질문과 관련된 자료나 경험 있는 사람을 찾아보세요.', '들은 내용을 내 말로 정리하면 빈틈을 발견하기 쉽습니다.', '혼자 풀리지 않던 질문 하나를 구체적으로 물어보세요.'),
('learning', 'change'): ('익숙한 생각도 다시 확인할 수 있습니다', '새로운 정보가 기존 생각과 다르다면 어느 쪽이 맞는지 서둘러 정하지 마세요. 출처와 전제가 같은지 확인하는 과정이 먼저입니다.', '확실히 아는 것과 추측하는 것을 나누세요.', '다른 설명을 발견하면 근거가 되는 원문을 읽으세요.', '생각을 고치는 일을 실패로 받아들일 필요는 없습니다.', '당연하게 여겼던 정보 하나의 출처를 확인하세요.'),
('learning', 'mixed'): ('많이 읽기보다 제대로 이해하기', '서로 다른 설명을 한꺼번에 받아들이면 오히려 판단이 흐려질 수 있습니다. 지금 풀려는 질문에 필요한 정보부터 남기세요.', '오늘 알아볼 범위를 좁히세요.', '자료마다 같게 말하는 부분과 다르게 말하는 부분을 나누세요.', '답이 없는 부분은 미정으로 두고 쉬어도 됩니다.', '찾아본 내용을 확실한 것과 더 확인할 것으로 나눠 적으세요.'),
('pace', 'join'): ('함께 맡을 일은 역할부터 나누세요', '함께 준비하거나 책임질 일이 있다면 서로 맡을 범위를 먼저 정하세요. 내가 빠르게 할 수 있다는 이유로 모두 떠안을 필요는 없습니다.', '오늘 약속 중 함께 준비할 부분을 확인하세요.', '도움이 필요하면 내용과 시간을 구체적으로 요청하세요.', '끝난 일은 공유하고 남은 일의 담당을 맞추세요.', '함께 맡은 일 하나에서 내 역할과 상대의 역할을 정하세요.'),
('pace', 'change'): ('계획이 바뀌면 순서도 바꾸세요', '예정과 달라진 일이 있다면 원래 계획을 모두 지키려 애쓰지 마세요. 꼭 필요한 것과 나중에 해도 되는 것을 다시 나누면 됩니다.', '움직일 시간과 약속 사이에 여유를 남기세요.', '새로운 요청을 받으면 기존 일정부터 확인하세요.', '하지 못한 것보다 남겨도 되는 것을 정리하세요.', '빡빡한 일정 하나를 옮기거나 범위를 줄이세요.'),
('pace', 'mixed'): ('약속을 지키려면 한계도 알려야 합니다', '협조하고 싶어도 시간과 여력이 충분한지는 별개입니다. 무조건 수락한 뒤 버티기보다 가능한 범위를 먼저 알려주세요.', '이미 잡힌 약속을 확인하세요.', '추가 요청에는 바로 답하기보다 필요한 시간을 가늠하세요.', '내일을 위해 마무리할 시각을 정해도 좋습니다.', '부담되는 요청 하나에 가능한 범위나 다른 시간을 제안하세요.'),
('self', 'join'): ('내 취향을 지키면서 함께 즐기기', '같이 시간을 보내더라도 모든 취향을 맞출 필요는 없습니다. 내가 좋아하는 것과 상대가 원하는 것을 하나씩 나누면 선택이 쉬워집니다.', '오늘 하고 싶은 것을 하나 떠올리세요.', '함께 고를 때는 내 의견도 짧게 보태세요.', '다르게 즐긴 경험도 좋은 대화거리가 될 수 있습니다.', '함께할 활동을 고를 때 내 취향을 하나 제안하세요.'),
('self', 'change'): ('내게 맞지 않는 선택은 바꿔도 됩니다', '이미 정했다는 이유로 불편한 선택을 계속 유지할 필요는 없습니다. 남의 기대보다 지금 내가 감당할 수 있는지부터 돌아보세요.', '마음에 걸리는 선택을 하나 짚으세요.', '원치 않는 부탁에는 짧고 분명하게 의사를 전하세요.', '혼자 편안하게 보낼 시간을 남기세요.', '내키지 않는 부탁 하나에는 가능한 선을 분명하게 말하세요.'),
('self', 'mixed'): ('양보할 것과 지킬 것을 나누세요', '함께 맞춰갈 부분과 내 기준을 지킬 부분을 구분하세요. 모두 양보하거나 모두 거절하는 방식만 있는 것은 아닙니다.', '오늘 꼭 지키고 싶은 기준을 하나 정하세요.', '의견을 조율할 때 대안을 함께 말하세요.', '선택 뒤에도 불편함이 남으면 무엇 때문인지 돌아보세요.', '조율할 일이 있다면 양보할 부분과 지킬 부분을 하나씩 말하세요.'),
}


def select_daily_scenario(query):
    observed = (query.get('activated_state') or {}).get('temporal_observations') or {}
    if observed.get('version') != 'temporal-observations-v1' or (query.get('synthesis') or {}).get('confidence') == 'undetermined':
        return None
    records = [r for r in observed.get('daily_observations', [])
        if r.get('structure_status') == 'observed' and r.get('newly_introduced')
        and r.get('type') in JOIN | CHANGE
        and any(m.get('pillar') == 'timing:daily' for m in r.get('members', []))]
    conditions = (query.get('activated_state') or {}).get('temporal_conditions') or {}
    condition_records = {r['relationship_id']: r for r in conditions.get('records', [])}
    if conditions:
        # A missing/rejected/unsupported condition record cannot nominate a scene.
        records = [r for r in records if condition_records.get(r.get('relationship_id'), {}).get('eligibility') == 'conditional']
    by_family = {}
    for r in records:
        function_targets = condition_records.get(r.get('relationship_id'), {}).get('checks', {}).get('function_targets', [])
        anchors = list(r.get('anchors', [])) + [
            dict(natal=True, ten_god=t['role_to_day_master']) for t in function_targets
            if t.get('stem_pillar') in {'year', 'month', 'day', 'hour'}
            and t.get('function_kind') in {'root_support', 'visible_role'}
        ]
        for a in anchors:
            family = 'self' if a.get('ten_god') == 'day_master' else FAMILIES.get(a.get('ten_god'))
            if a.get('natal') and family:
                by_family.setdefault(family, {})[r['id']] = r
    if not by_family:
        return None
    timing = query.get('timing') or {}
    # A tie stays unresolved if these contextual facts do not distinguish it.
    preferences = [('daily_branch', observed.get('daily_branch_ten_god'))] + [
        (axis, (timing.get(axis) or {}).get('ten_god')) for axis in ('daily', 'monthly', 'annual', 'luck_cycle')]
    family = next(iter(by_family)) if len(by_family) == 1 else None
    origin = 'unique_natal_connected_subject' if family else None
    if family is None:
        for axis, god in preferences:
            f = FAMILIES.get(god)
            if f in by_family:
                family, origin = f, axis
                break
    if family is None:
        return None
    supporting = list(by_family[family].values())
    direction = (query.get('activated_state') or {}).get('temporal_direction') or {}
    selected_ids = {r.get('relationship_id') for r in supporting}
    direction_records = [r for r in direction.get('records', []) if r['relationship_id'] in selected_ids]
    joins = any(r['type'] in JOIN for r in supporting)
    changes = any(r['type'] in CHANGE for r in supporting)
    mode = 'mixed' if joins and changes else 'join' if joins else 'change'
    daily_family = FAMILIES.get((timing.get('daily') or {}).get('ten_god'))
    context_key = (family, daily_family)
    context_table = JOIN_CONTEXT if mode == 'join' else CHANGE_CONTEXT if mode == 'change' else {}
    contextual = context_key in context_table
    title, body, morning, afternoon, evening, action = context_table[context_key] if contextual else COPY[family, mode]
    return dict(title=title, opening=body, time_flow=dict(morning=morning, afternoon=afternoon, evening=evening),
        unified_advice=action,
        evidence=dict(version='daily-conditional-scenes-v2-function-targets', family=family, mode=mode,
            selection_basis=origin, considered_subjects=sorted(by_family),
            daily_subject=daily_family, contextual_copy=contextual,
            content_key=f'{family}:{mode}:{daily_family}' if contextual else f'{family}:{mode}',
            observation_ids=sorted(r['id'] for r in supporting),
            rule_codes=sorted({r['rule_code'] for r in supporting}),
            condition_evidence_ids=sorted({eid for r in supporting for eid in condition_records.get(r.get('relationship_id'),{}).get('evidence_ids',[])}),
            condition_check_version=conditions.get('version'),
            function_target_ids=sorted({t['target_id'] for r in supporting
                for t in condition_records.get(r.get('relationship_id'), {}).get('checks', {}).get('function_targets', [])}),
            function_targets_are_conditional=True,
            direction_review=[dict(relationship_id=r['relationship_id'], comparison_summary=r['comparison_summary'],
                realized_valence=r['realized_valence'],evidence_ids=r['evidence_ids']) for r in direction_records],
            conditional_direction_changes_copy=False,
            interpretation_level='conditional_editorial_advice',
            ranking_is_editorial=True, strongest_fortune_domain_claim=False,
            effect_assessment_complete=False, valence='undetermined'))
