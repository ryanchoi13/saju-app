"""Translate core judgments into short advice; never recompute the core verdict.

Wording is an editorial interpretation, not another diagnostic engine. Preserve
core operation order and do not promote timing candidates into confirmed events.
"""

from app.engine.services.daily_evidence import daily_relationship_evidence
from app.engine.services.daily_scenarios import select_daily_scenario
from app.engine.synthesis.operation_scope import usable_operations, operation_block_reason

_AUTO_SCENARIO = object()

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


_UNIFIED = {
    'protect': '주변에 휩쓸리지 말고 오늘 지키고 싶은 기준 하나를 정해보세요.',
    'resolve_conflict': '결론을 서두르지 말고 서로 다르게 이해한 점을 확인해 보세요.',
    'release_binding': '조급한 마음을 내려놓고 막힌 일의 첫 단계부터 풀어보세요.',
    'drain': '조급한 마음을 버리고 미뤄둔 일 하나를 오늘 마무리해 보세요.',
    'mediate': '내 생각을 잠시 내려놓고 상대의 이야기를 끝까지 들어보세요.',
    'warm': '완벽하게 준비하려는 부담을 덜고 작은 것부터 시작해 보세요.',
    'cool': '들뜬 마음을 가라앉히고 결정할 조건을 다시 읽어보세요.',
    'moisten': '빽빽한 일정에 여유를 두고 잠시 쉬는 시간을 가져보세요.',
    'dry': '복잡하게 생각하기보다 불필요한 단계 하나를 줄여보세요.',
    'support': '혼자 감당하려는 부담을 내려놓고 필요한 도움 하나를 구해보세요.',
    'stabilize': '속도를 재촉하지 말고 편안하게 이어갈 순서를 정해보세요.',
    'preserve_balance': '욕심을 조금 덜고 오늘 감당할 수 있는 범위를 정해보세요.',
    'preserve_special_structure': '변화를 서두르지 말고 잘 맞았던 방식을 먼저 살펴보세요.',
}

def build_daily_guidance(query: dict, daily_god: str, relations: list[dict], *, scenario=_AUTO_SCENARIO) -> dict:
    synthesis = query.get('synthesis') or {}
    semantic = query.get('semantic_state') or {}
    operations = usable_operations(synthesis)
    primary = operations[0] if operations else {}
    operation = primary.get('operation')
    cautions = synthesis.get('caution_operations') or []
    conflicts = synthesis.get('diagnostic_conflicts') or []
    confidence = semantic.get('confidence', synthesis.get('confidence', 'undetermined'))
    unresolved = any(c.get('resolution') == 'preserve_as_unresolved' and
                     (not c.get('operations') or operation in c['operations']) for c in conflicts)
    blocked = any(c.get('operation') == operation for c in cautions) if operation else False
    fallback = (confidence not in {'low', 'medium', 'high'} or unresolved or blocked or operation not in _COPY)
    mindset, template = _NEUTRAL if fallback else _COPY[operation]
    target = _TARGETS.get(daily_god, '오늘 처리할 일')
    # Only today's relationships, including their unresolved status, affect pace.
    daily_tensions = daily_relationship_evidence(query)['cautions']
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
    # The natal direction is context, not a fresh daily event. Use today's
    # subject for the action without cycling unrelated topics or synonym lists.
    daily_actions = {
        'peer': '원치 않는 부탁에는 짧고 분명하게 의사를 전하세요.',
        'rob_wealth': '함께 쓰는 비용이나 역할 중 애매한 부분 하나를 정하세요.',
        'eating_god': '미뤄둔 취미에 오늘 20분만 써보세요.',
        'hurting_officer': '돌려 말하지 말고 원하는 것을 한 문장으로 전하세요.',
        'direct_wealth': '쓰지 않는 정기결제 하나가 있는지 확인하세요.',
        'indirect_wealth': '마음이 끌리는 선택의 장점과 부담을 하나씩 적으세요.',
        'direct_officer': '미뤄둔 답장 하나를 오늘 보내세요.',
        'seven_killings': '오늘 하지 않아도 되는 일정 하나를 덜어내세요.',
        'direct_resource': '배운 내용 하나를 내 말로 짧게 설명해 보세요.',
        'indirect_resource': '걱정 하나를 적고 사실인지 추측인지 구분하세요.',
    }
    unified = ('성급하게 결론 내리지 말고 확인하지 못한 조건 하나를 살펴보세요.'
               if fallback else daily_actions.get(daily_god, _UNIFIED[operation]))
    # A compatible assessed direction can add specificity; never force it on
    # unrelated topics. Protect/balance provide restraint already present above.
    if not fallback and operation in {'mediate', 'resolve_conflict'} and daily_god in {'peer', 'rob_wealth', 'hurting_officer', 'direct_officer'}:
        unified = _UNIFIED[operation]
    elif not fallback and operation in {'support', 'moisten', 'cool'} and daily_god in {'seven_killings', 'direct_resource', 'indirect_resource'}:
        unified = _UNIFIED[operation]
    if scenario is _AUTO_SCENARIO:
        scenario = select_daily_scenario(query)
    if scenario:
        unified = scenario['unified_advice']
    if daily_tensions and not fallback:
        unified = '서로 다르게 이해한 점이 없는지 중요한 이야기를 차분히 확인해 보세요.'
    return {
        'unified_advice': unified,
        'mindset': mindset, 'action': action,
        'evidence': {
            'scenario': scenario['evidence'] if scenario else None,
            'version': 'daily-guidance-v5-function-scope', 'copy_version': 'daily-guidance-copy-v2', 'natal_operation_is_background': True, 'mode': mode,
            'held_operations': [{'operation': o.get('operation'), 'reason': operation_block_reason(o, synthesis)}
                                for o in synthesis.get('favorable_operations', []) if operation_block_reason(o, synthesis)],
            'primary_operation': operation, 'priority_reason': primary.get('priority_reason'),
            'confidence': confidence, 'unresolved_conflict': unresolved,
            'blocked_by_caution': blocked, 'daily_ten_god': daily_god,
            'daily_relationship_ids': [r.get('relationship_id') for r in daily_tensions if r.get('relationship_id')],
            'timing_candidates_are_not_verdicts': True, 'evidence_ids': evidence_ids,
        },
    }
