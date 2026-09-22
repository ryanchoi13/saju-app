"""Service wording reads assessed common state; it never adjudicates Myeongri."""
from app.engine.semantic.applied import recommended_directions


_GUIDANCE = {
    'wealth': {
        'support': '재정 결정을 혼자 서두르기보다 필요한 정보와 도움을 확보하는 데 먼저 힘을 쓰세요.',
        'drain': '준비한 역량을 작은 실행으로 옮기고, 실제 수입과 지출 기록을 보며 조정하세요.',
        'mediate': '수입·지출·공동 책임 사이의 연결을 정리하고 합의 내용을 분명하게 남겨 보세요.',
        'stabilize': '새 계획을 늘리기 전에 기존 지출과 약속을 감당할 수 있는지 확인하세요.',
    },
    'career': {
        'support': '업무량을 늘리기 전에 필요한 자원과 협업 상대를 확보하는 데 집중해 보세요.',
        'drain': '쌓아 둔 생각과 경험을 작은 결과물로 만들어 피드백을 받아 보세요.',
        'mediate': '역할과 기대가 어긋나는 지점을 찾아 담당 범위와 협업 방식을 조율해 보세요.',
        'stabilize': '동시에 벌이는 일을 줄이고 맡은 일을 끝내는 순서를 분명하게 정해 보세요.',
    },
    'study': {
        'support': '학습량을 늘리기보다 이해를 돕는 자료와 질문할 상대를 먼저 확보해 보세요.',
        'drain': '읽고 이해한 내용을 직접 설명하거나 문제로 풀어 보는 시간을 확보하세요.',
        'mediate': '이해·복습·문제풀이가 끊기는 지점을 찾아 공부 순서를 연결해 보세요.',
        'stabilize': '새 교재를 늘리기보다 정해 둔 복습과 실전 연습을 꾸준히 이어가 보세요.',
    },
    'love': {
        'support': '관계를 혼자 감당하려 하기보다 필요한 도움과 바라는 점을 구체적으로 전해 보세요.',
        'drain': '생각만 쌓아 두기보다 작은 표현과 대화로 마음을 전달해 보세요.',
        'mediate': '서로 다른 기대를 확인하고 두 사람이 지킬 수 있는 약속으로 조율해 보세요.',
        'stabilize': '큰 결론을 서두르기보다 일상에서 지킬 수 있는 약속부터 이어가 보세요.',
    },
}


def direction_advice(state: dict, topic: str, fallback: str) -> str:
    """Translate only eligible confirmed directions, preserving existing fallback."""
    mapping = _GUIDANCE.get(topic, {})
    phrases = list(dict.fromkeys(mapping[d['operation']] for d in recommended_directions(state)
                               if d.get('operation') in mapping))
    return ' '.join(phrases[:2]) if phrases else fallback


def state_basis(state: dict) -> dict:
    return dict(version=state['version'], scope=state['scope'],
                overall_status=state['overall_status'],
                recommended_operations=list(dict.fromkeys(d['operation'] for d in recommended_directions(state))),
                evidence_ids=state['evidence_ids'])
