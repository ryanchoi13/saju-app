from datetime import date, time
from unittest.mock import patch

import pytest

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.semantic.applied import build_applied_state, recommended_directions
from app.engine.semantic.overall import select_overall_domains
from app.engine.services.applied_guidance import direction_advice
from app.engine.services.fashion_colors import build_fashion_color_basis
from app.engine.services import (
    build_lifetime_wealth_report, build_lifetime_career_report,
    build_lifetime_study_report, build_lifetime_love_report,
    build_lifetime_health_report, build_lifetime_overall_report,
    build_annual_overall_report, build_compatibility_report,
)


@pytest.fixture
def core():
    c = calculate_myeongri_core(BirthInput(name='Adapter test', gender='female',
        birth_date=date(1998,5,19), birth_time=time(10)), target_date=date(2026,9,10))
    c.synthesis.favorable_operations = [dict(operation='support', elements=['木'],
        assessment_status='completed', evidence_ids=['evidence:strength:ordered-diagnosis'])]
    c.synthesis.pending_operations = []
    c.synthesis.caution_operations = []
    c.synthesis.diagnostic_conflicts = []
    return c


@pytest.mark.parametrize('block', ['conditional','caution','conflict'])
def test_unusable_directions_cannot_reach_advice_or_fashion(core, block):
    if block == 'conditional':
        core.synthesis.favorable_operations[0]['unresolved_requirements'] = ['personal_need']
    elif block == 'caution':
        core.synthesis.caution_operations = [dict(operation='support')]
    else:
        core.synthesis.diagnostic_conflicts = [dict(operations=['support'],resolution='preserve_as_unresolved')]
    state = build_applied_state(core, 'natal')
    assert recommended_directions(state) == []
    assert direction_advice(state, 'wealth', 'fallback') == 'fallback'
    colors = build_fashion_color_basis(core)
    assert colors['confirmed_elements'] == []
    assert colors['source'] == 'daily_symbolic_reference'


@pytest.mark.parametrize('builder,args,topic', [
    (build_lifetime_wealth_report,(), 'wealth'),
    (build_lifetime_career_report,('직장',), 'career'),
    (build_lifetime_study_report,(), 'study'),
    (build_lifetime_love_report,('솔로',), 'love'),
])
def test_theme_report_actually_consumes_state(core, builder, args, topic):
    state = build_applied_state(core, 'natal+all_luck_cycles')
    phrase = direction_advice(state, topic, 'fallback')
    report = builder(core, '테스트', *args)
    assert phrase != 'fallback' and phrase in report['content']
    assert report['analysis_basis']['recommended_operations'] == ['support']
    core.synthesis.favorable_operations[0]['unresolved_requirements'] = ['force']
    blocked = builder(core, '테스트', *args)
    assert phrase not in blocked['content']
    assert blocked['analysis_basis']['recommended_operations'] == []


def test_health_and_lifetime_use_applied_eligibility(core):
    for builder in (build_lifetime_health_report, build_lifetime_overall_report):
        confirmed = builder(core, '테스트')
        changed = core.model_copy(deep=True)
        changed.synthesis.favorable_operations[0]['unresolved_requirements'] = ['force']
        blocked = builder(changed, '테스트')
        assert confirmed['content'] != blocked['content']
        assert blocked['analysis_basis']['recommended_operations'] == []


def test_overall_selection_reads_state_instead_of_raw_synthesis(core):
    state = build_applied_state(core, 'natal')
    assert 'wellbeing' in select_overall_domains(core,'natal')['primary_domains']
    state['directions'] = []
    with patch('app.engine.semantic.overall.build_applied_state', return_value=state):
        assert 'wellbeing' not in select_overall_domains(core,'natal')['primary_domains']


def test_annual_and_monthly_use_requested_period_not_core_target(core):
    report = build_annual_overall_report(core, '테스트', 2027)
    summaries = report['evidence_summary']
    assert summaries['annual']['scope'] == 'annual'
    assert summaries['annual']['applied_state_version']
    assert all(m['interpretation']['scope']=='monthly' for m in summaries['months'])
    assert all(m['representative_date'].startswith('2027-') for m in summaries['months'])


def test_fashion_ignores_stale_semantic_elements_and_keeps_unknown_unconfirmed(core):
    core.semantic_state.favorable_elements = ['金']
    colors = build_fashion_color_basis(core)
    assert colors['primary_element'] == '木'
    assert colors['source'] == 'confirmed_natal_direction'
    core.synthesis.favorable_operations = []
    core.synthesis.pending_operations = [dict(operation='warm',element='火')]
    colors = build_fashion_color_basis(core)
    assert colors['primary_element'] == core.timing.daily['pillar']['stem_element']
    assert colors['source'] == 'daily_symbolic_reference'


def test_compatibility_uses_shared_eligibility(core):
    core.semantic_state.favorable_elements = ['金']
    confirmed = build_compatibility_report(core, core, 'A', 'B', '친구 / 지인')
    core.synthesis.favorable_operations = []
    unresolved = build_compatibility_report(core, core, 'A', 'B', '친구 / 지인')
    assert confirmed['content'] != unresolved['content']
    assert '특정 유리 오행을 확정하지 않아' in unresolved['content']


def test_real_fashion_pipeline_passes_common_state_color_to_palette():
    import main
    basis = dict(primary_element='水', reference_element='木', source='confirmed_natal_direction',
                 state_version='test-state', scope='natal+luck_cycle+annual+monthly+daily')
    with patch.object(main,'build_fashion_color_basis',return_value=basis), \
         patch.object(main,'select_wada_duo_for_targets',wraps=main.select_wada_duo_for_targets) as selector:
        result = main.get_saju_pillars_and_analysis('검토', 'female', 1998,5,19,'solar',5)
    assert selector.call_args.args[0] == '水'
    assert result['daily_fortune']['fashion_color_basis'] == basis
    assert result['daily_fortune']['fashion_v2']
