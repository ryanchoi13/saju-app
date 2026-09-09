"""Translate core judgments into short advice; never recompute the core verdict.

Wording is an editorial interpretation, not another diagnostic engine. Preserve
core operation order and do not promote timing candidates into confirmed events.
"""

_TARGETS = {
    'peer': '내가 맡은 일', 'rob_wealth': '공동 일정이나 비용',
    'eating_god': '진행 중인 작업', 'hurting_officer': '전달할 제안',
    'direct_wealth': '지출이나 마감', 'indirect_wealth': '새로 들어온 제안',
    'direct_officer': '약속과 책임 범위', 'seven_killings': '급하게 처리할 일',
    'direct_resource': '확인할 자료', 'indirect_resource': '떠오른 아이디어',
}
# One attitude and one action, preserving the existing two display slots.
_COPY = {
    'protect': ('새로운 일을 늘리기보다 중요한 기준부터 지키기', '{target}에서 지켜야 할 기준 한 가지를 적어두기'),
    'resolve_conflict': ('엇갈린 의견은 결론보다 기준부터 맞추기', '{target}에서 서로 다르게 이해한 조건 한 가지를 확인하기'),
    'release_binding': ('막힌 일은 한꺼번에 풀기보다 작은 단계로 나누기', '{target}에서 막힌 단계 하나를 찾아 해결 방법을 정리하기'),
    'drain': ('생각과 의욕을 감당할 수 있는 결과로 옮기기', '{target}에서 오늘 끝낼 수 있는 부분 하나를 마무리하기'),
    'mediate': ('어느 한쪽을 밀어붙이기보다 연결점을 찾기', '{target}에서 함께 동의할 수 있는 조건 한 가지를 확인하기'),
    'warm': ('출발을 서두르지 말고 작은 준비로 흐름 만들기', '{target}에 필요한 준비 한 가지를 먼저 갖추기'),
    'cool': ('흥분한 상태에서 결정을 서두르지 않기', '{target}에 대한 결정을 잠시 미루고 조건을 다시 읽어보기'),
    'moisten': ('여유를 남겨두고 지속할 수 있는 속도 지키기', '{target}의 일정에 짧은 여유 시간을 확보하기'),
    'dry': ('흩어진 생각을 정리하고 우선순위를 분명히 하기', '{target}에서 불필요한 단계 하나를 정리하기'),
    'support': ('혼자 감당하려 하지 말고 필요한 준비와 도움 챙기기', '{target}에 필요한 자료나 도움 한 가지를 확보하기'),
    'stabilize': ('속도보다 순서를 지키며 흐름을 정돈하기', '{target}의 진행 순서를 짧게 적어보기'),
    'preserve_balance': ('한쪽으로 무리하지 말고 감당할 범위 지키기', '{target}에서 오늘 감당할 범위 한 가지를 정하기'),
    'preserve_special_structure': ('잘 작동하는 방식을 성급하게 바꾸지 않기', '{target}에서 유지할 방식 한 가지를 확인하기'),
}
_CHECKS = {
    'protect': '지켜야 할 기준', 'resolve_conflict': '서로 다르게 이해한 조건',
    'release_binding': '진행을 막고 있는 단계', 'drain': '마무리할 수 있는 부분',
    'mediate': '함께 동의할 수 있는 조건', 'warm': '시작에 필요한 준비',
    'cool': '서두르지 않고 다시 살펴볼 조건', 'moisten': '여유를 확보할 수 있는 부분',
    'dry': '정리할 수 있는 불필요한 단계', 'support': '보충할 자료나 도움',
    'stabilize': '먼저 정리할 순서', 'preserve_balance': '무리 없이 감당할 범위',
    'preserve_special_structure': '유지할 만한 기존 방식',
}
_NEUTRAL = ('확신을 서두르지 말고 확인된 것부터 판단하기', '{target}에서 아직 확인하지 못한 조건 한 가지를 확인하기')
_TENSION = {'stem_control', 'branch_clash', 'branch_punishment', 'branch_harm', 'branch_break'}


def build_daily_guidance(query: dict, daily_god: str, relations: list[dict]) -> dict:
    synthesis = query.get('synthesis') or {}
    semantic = query.get('semantic_state') or {}
    operations = synthesis.get('favorable_operations') or []
    primary = operations[0] if operations else {}
    operation = primary.get('operation')
    cautions = synthesis.get('caution_operations') or []
    conflicts = synthesis.get('diagnostic_conflicts') or []
    confidence = semantic.get('confidence', synthesis.get('confidence', 'undetermined'))
    unresolved = any(c.get('resolution') == 'preserve_as_unresolved' for c in conflicts)
    blocked = any(c.get('operation') == operation for c in cautions) if operation else False
    fallback = (confidence not in {'low', 'medium', 'high'} or unresolved or blocked or operation not in _COPY)
    mindset, template = _NEUTRAL if fallback else _COPY[operation]
    target = _TARGETS.get(daily_god, '오늘 처리할 일')
    # Only today's relationships, including their unresolved status, affect pace.
    daily_tensions = [r for r in relations if r.get('type') in _TENSION and any(
        m.get('pillar') == 'timing:daily' for m in r.get('members', []))]
    mode = 'verify' if fallback else 'core_operation'
    if confidence == 'low' and not fallback:
        mode = 'cautious_core_operation'
        template = '{target}에서 ' + _CHECKS[operation] + ' 한 가지를 확인하기'
    if daily_tensions and not fallback and confidence != 'low':
        mode = 'core_operation_with_daily_check'
        template = '관련 조건을 확인한 뒤 ' + template
    action = template.format(target=target)
    evidence_ids = list(dict.fromkeys(
        list(query.get('evidence_ids') or []) + list(primary.get('evidence_ids') or [])
        + [eid for c in cautions + conflicts for eid in c.get('evidence_ids', [])]
    ))
    return {
        'mindset': mindset, 'action': action,
        'evidence': {
            'version': 'daily-guidance-v1', 'mode': mode,
            'primary_operation': operation, 'priority_reason': primary.get('priority_reason'),
            'confidence': confidence, 'unresolved_conflict': unresolved,
            'blocked_by_caution': blocked, 'daily_ten_god': daily_god,
            'daily_relationship_ids': [r.get('relationship_id') for r in daily_tensions if r.get('relationship_id')],
            'timing_candidates_are_not_verdicts': True, 'evidence_ids': evidence_ids,
        },
    }
