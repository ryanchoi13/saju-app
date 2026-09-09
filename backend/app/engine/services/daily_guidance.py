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
    'protect': ('중요한 기준에 마음두기', '{target}에서 지킬 기준 하나 적기'),
    'resolve_conflict': ('의견이 달라도 차분하게 듣기', '{target}에서 엇갈린 조건 하나 확인하기'),
    'release_binding': ('막힌 일에도 조급해하지 않기', '{target}에서 막힌 단계 하나 정리하기'),
    'drain': ('조급함보다 차근차근 완성하는 데 마음두기', '{target} 중 오늘 끝낼 부분 하나 정하기'),
    'mediate': ('내 입장만큼 상대 입장도 헤아리기', '{target}에서 합의할 조건 하나 정하기'),
    'warm': ('작은 시작을 편안하게 받아들이기', '{target}에 필요한 준비 하나 갖추기'),
    'cool': ('들뜬 마음에 휩쓸리지 않기', '{target}의 조건을 결정 전에 다시 읽기'),
    'moisten': ('무리하지 않고 여유 갖기', '{target}의 일정에 여유 시간 넣기'),
    'dry': ('복잡한 생각보다 중요한 것에 집중하기', '{target}에서 불필요한 단계 하나 줄이기'),
    'support': ('혼자 감당하려는 부담 내려놓기', '{target}에 필요한 자료나 도움 구하기'),
    'stabilize': ('속도보다 차분함에 마음두기', '{target}의 순서 적기'),
    'preserve_balance': ('지나친 욕심보다 균형에 마음두기', '{target} 중 오늘 할 범위 정하기'),
    'preserve_special_structure': ('익숙한 방식의 장점도 존중하기', '{target}에서 유지할 방식 하나 정하기'),
}
_CHECKS = {
    'protect': '지킬 기준', 'resolve_conflict': '엇갈린 조건',
    'release_binding': '막힌 단계', 'drain': '마무리할 부분',
    'mediate': '합의할 조건', 'warm': '시작에 필요한 준비',
    'cool': '다시 살펴볼 조건', 'moisten': '여유를 둘 부분',
    'dry': '불필요한 단계', 'support': '보충할 자료나 도움',
    'stabilize': '먼저 정리할 순서', 'preserve_balance': '감당할 범위',
    'preserve_special_structure': '유지할 방식',
}
_NEUTRAL = ('성급한 확신보다 열린 마음 갖기', '{target}의 미확인 조건 하나 확인하기')
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
        template = '{target}에서 ' + _CHECKS[operation] + ' 하나 확인하기'
    if daily_tensions and not fallback and confidence != 'low':
        mode = 'core_operation_with_daily_check'
        template = '조건 확인 후 ' + template
    action = template.format(target=target)
    evidence_ids = list(dict.fromkeys(
        list(query.get('evidence_ids') or []) + list(primary.get('evidence_ids') or [])
        + [eid for c in cautions + conflicts for eid in c.get('evidence_ids', [])]
    ))
    return {
        'mindset': mindset, 'action': action,
        'evidence': {
            'version': 'daily-guidance-v2-concise', 'mode': mode,
            'primary_operation': operation, 'priority_reason': primary.get('priority_reason'),
            'confidence': confidence, 'unresolved_conflict': unresolved,
            'blocked_by_caution': blocked, 'daily_ten_god': daily_god,
            'daily_relationship_ids': [r.get('relationship_id') for r in daily_tensions if r.get('relationship_id')],
            'timing_candidates_are_not_verdicts': True, 'evidence_ids': evidence_ids,
        },
    }
