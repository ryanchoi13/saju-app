"""Reassess timing in the requested period before projecting service state.

Filtering relationship members alone is insufficient: excluded periods can
supply roots, seasonal context and overlapping relations to an allowed pair.
Calculations stay in the timing core; semantic state only projects the result.
"""
from app.engine.core.models import ActivatedState, TimingResult, PillarFact
from app.engine.timing.engine import _relationship_changes, summarize_strength_shift
from app.engine.timing.conditions import assess_temporal_conditions
from app.engine.timing.direction import compare_temporal_directions
from app.engine.timing.observations import observe_temporal_structure
from app.engine.shensha import calculate_shensha

AXES = ('luck_cycle', 'annual', 'monthly', 'daily')


def timing_axes_for_scope(scope: str) -> set[str]:
    parts = set(scope.split('+'))
    if not parts <= {'natal', 'all_luck_cycles', *AXES}:
        raise ValueError(f'Unknown timing scope: {scope}')
    if 'all_luck_cycles' in parts:
        if parts & set(AXES):
            raise ValueError('Lifetime cycles cannot be mixed with current timing')
        return set()
    return parts & set(AXES)


def core_for_timing_scope(core, scope: str):
    """Return a non-mutating view with newly assessed, period-local evidence."""
    allowed = timing_axes_for_scope(scope)
    if allowed == set(AXES):
        return core
    if not allowed:
        shensha, shensha_evidence = calculate_shensha(core.natal_facts.pillars)
        return core.model_copy(update={'timing': TimingResult(
            luck_cycle=core.timing.luck_cycle if 'all_luck_cycles' in scope.split('+') else {}
        ), 'activated_state': ActivatedState(), 'shensha': shensha,
            'evidence': list({e.id: e for e in core.evidence + shensha_evidence}.values())})
    overlays = {}
    for axis in AXES:
        if axis not in allowed:
            continue
        value = core.timing.luck_cycle.get('current') if axis == 'luck_cycle' else getattr(core.timing, axis)
        if value and value.get('pillar'):
            overlays[axis] = value
    pillars = {axis: PillarFact.model_validate(value['pillar']) for axis, value in overlays.items()}
    natal = core.natal_facts.pillars
    changes = _relationship_changes(natal, pillars)
    timing = TimingResult(
        luck_cycle={'current': overlays.get('luck_cycle')},
        annual=overlays.get('annual', {}), monthly=overlays.get('monthly', {}),
        daily=overlays.get('daily', {}), relationship_changes=changes,
    )
    conditions, condition_evidence = assess_temporal_conditions(natal, timing, core.synthesis)
    direction, direction_evidence = compare_temporal_directions(conditions, core.synthesis)
    gods = list(dict.fromkeys(v['ten_god'] for v in overlays.values() if v.get('ten_god')))
    activated = ActivatedState(
        temporal_observations=observe_temporal_structure(natal, pillars),
        temporal_conditions=conditions, temporal_direction=direction,
        activated_ten_gods=gods, strength_shift=summarize_strength_shift(gods),
        relationship_changes=changes,
        climate_shift={**{a + '_element': v['pillar']['stem_element'] for a, v in overlays.items()},
                       'requires_reassessment': True},
    )
    # The same relation ID can have different premises at different scopes.
    # Replace its evidence in this view, leaving the original core untouched.
    shensha, shensha_evidence = calculate_shensha(natal, timing)
    evidence = {e.id: e for e in core.evidence}
    evidence.update({e.id: e for e in condition_evidence + direction_evidence + shensha_evidence})
    return core.model_copy(update={'timing': timing, 'activated_state': activated,
                                   'shensha': shensha, 'evidence': list(evidence.values())})
