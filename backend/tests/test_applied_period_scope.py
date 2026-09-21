"""Period contracts: shorter periods must not change longer-period judgments."""
from datetime import date, time
import json

import pytest

from app.engine.core.models import BirthInput
from app.engine.orchestrator import calculate_myeongri_core
from app.engine.semantic.applied import build_applied_state
from app.engine.semantic.queries import build_service_query
from app.engine.timing.scope import core_for_timing_scope


@pytest.fixture(scope='module')
def cores():
    birth = BirthInput(name='Scope regression', gender='female',
                       birth_date=date(1998, 5, 19), birth_time=time(10))
    return {day: calculate_myeongri_core(birth, target_date=date(2026, 9, day))
            for day in (1, 7, 10, 11, 20, 30)}


def test_annual_state_is_invariant_across_month_boundary_and_daily_roles(cores):
    # The old PR returned supportive on Sep 10 and mixed on Sep 11.
    states = [build_applied_state(c, 'natal+luck_cycle+annual') for c in cores.values()]
    assert all(s == states[0] for s in states)
    assert states[0]['timing']['strength_shift'] == 'supportive'
    assert states[0]['timing']['effect_assessment_complete'] is False


def test_monthly_state_ignores_days_but_changes_at_solar_term(cores):
    states = {d: build_applied_state(c, 'natal+luck_cycle+annual+monthly') for d,c in cores.items()}
    assert states[10] == states[11] == states[20] == states[30]
    assert states[1]['timing']['observations'] != states[10]['timing']['observations']


def test_daily_observations_continue_to_change(cores):
    a,b = [build_applied_state(cores[d], 'natal+luck_cycle+annual+monthly+daily') for d in (10,11)]
    assert a['timing']['observations'] != b['timing']['observations']
    assert a['confirmed_elements'] == b['confirmed_elements']


def test_query_activation_and_evidence_respect_annual_scope(cores):
    a,b = [build_service_query(cores[d], 'annual_overall') for d in (10,11)]
    assert a['activated_state'] == b['activated_state']
    assert a['applied_state'] == b['applied_state']
    assert a['semantic_state'] == b['semantic_state']
    assert a['shensha_support'] == b['shensha_support']
    records = a['applied_state']['evidence_records']
    assert records
    payload = json.dumps({'activation':a['activated_state'], 'evidence':records})
    assert 'timing:daily' not in payload
    assert 'timing:monthly' not in payload
    assert all(r['id'] in a['applied_state']['evidence_ids'] for r in records)


def test_projection_does_not_mutate_core_and_lifetime_has_no_current_activation(cores):
    core = cores[10]
    before = core.model_dump(mode='json')
    build_service_query(core, 'annual_overall')
    state = build_applied_state(core, 'natal+all_luck_cycles')
    query = build_service_query(core, 'lifetime_overall')
    assert state['timing']['observations'] == []
    assert state['timing']['relations'] == []
    assert state['timing']['strength_shift'] is None
    assert not query['activated_state']['temporal_conditions']
    assert core.model_dump(mode='json') == before


def test_invalid_scope_is_rejected(cores):
    with pytest.raises(ValueError):
        core_for_timing_scope(cores[10], 'natal+annual_typo')
