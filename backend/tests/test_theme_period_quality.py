"""Ensure personal interpretation survives shorter copy and honest period labels."""
from copy import deepcopy
from datetime import date, time

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.semantic.queries import build_service_query
from app.engine.services.theme_editorial import build_theme_content, CHAPTERS, personal_comparison
from app.engine.services.reading_editorial import theme_lens, cycle_paragraphs
from .test_theme_present_reader import VisibleText


def test_three_synthetic_profiles_keep_calculated_reading_for_five_themes():
    profiles = [(1984, 2, 17, 'male'), (1992, 5, 16, 'female'), (2001, 11, 3, 'male')]
    observed = {kind: set() for kind in ('wealth', 'career', 'love', 'health', 'study')}
    for year, month, day, gender in profiles:
        core = calculate_myeongri_core(
            BirthInput(name='합성 검증', gender=gender, birth_date=date(year, month, day), birth_time=time(8)),
            target_date=date(2026, 10, 4))
        for kind, service, domain in [('wealth', 'lifetime_wealth', 'money'),
                                      ('career', 'career', 'work'), ('love', 'love', 'love'),
                                      ('health', 'health', 'wellbeing'), ('study', 'study', 'learning')]:
            query = build_service_query(core, service)
            current = query['timing']['luck_cycles']['current']
            content = build_theme_content(query, '합성 검증', kind, '<p>검증 근거</p>')
            view = VisibleText(content)
            text = ''.join(view.text)
            # The actual calculated cycle passage, not just the user's name,
            # must remain visible; the age range identifies its long scope.
            cycle = cycle_paragraphs(current['ten_god'], domain)[0]
            assert cycle in text
            assert f"{current['start_age']}~{current['end_age']}세" in text
            observed[kind].add(cycle)
            assert view.sections == ['current', 'nature', 'practice']
            assert all(view.paragraphs)
            assert sum(p in text for _, ps in CHAPTERS[kind] for p in ps) == 1
            assert all(p in content for _, ps in CHAPTERS[kind] for p in ps)
            if kind != 'health':
                lens = theme_lens(query, kind).replace('관계에서는 눈여겨볼 부분은', '관계에서 눈여겨볼 부분은').replace('일에서는 눈여겨볼 부분은', '일에서 눈여겨볼 부분은')
                lens = lens.replace('재성이 적다고 돈을 벌지 못한다는 뜻은 아닙니다.', '이 설명만으로 재산의 규모를 판단하지는 않습니다.')
                assert lens in text
            without_current = deepcopy(query)
            without_current['timing']['luck_cycles']['current'] = None
            fallback = ''.join(VisibleText(build_theme_content(without_current, '합성 검증', kind, '')).text)
            assert '현재 대운 구간을 확인하지 못했습니다' in fallback
            assert '약 10년의 흐름' not in fallback
    assert all(len(variants) > 1 for variants in observed.values())


def test_comparison_follows_actual_role_pair_not_name_or_rotation():
    same = ' '.join(personal_comparison({}, 'direct_wealth', {'ten_god': 'direct_wealth'}, 'money', 'wealth'))
    different = ' '.join(personal_comparison({}, 'direct_wealth', {'ten_god': 'indirect_wealth'}, 'money', 'wealth'))
    assert '기본 구조와 현재 대운에서 모두' in same
    assert '기본 구조에서는' in different and '현재 대운에서는' in different
    assert same != different
    assert personal_comparison({}, None, None, 'money', 'wealth') == []
