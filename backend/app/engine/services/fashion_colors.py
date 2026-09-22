"""Translate common daily state into a color input for the styling engine.

The fallback is a daily symbolic palette, never a personal favorable-element
verdict. Clothing shape, TPO, weather and wearable colors remain fashion rules.
"""
from app.engine.semantic.applied import build_applied_state, recommended_directions


def build_fashion_color_basis(core) -> dict:
    state = build_applied_state(core, 'natal+luck_cycle+annual+monthly+daily')
    eligible = recommended_directions(state)
    elements = list(dict.fromkeys(e for d in eligible for e in d.get('elements', [])
                                if e in {'木', '火', '土', '金', '水'}))
    reference = core.timing.daily.get('pillar', {}).get('stem_element')
    return dict(state_version=state['version'], scope=state['scope'],
                primary_element=elements[0] if elements else reference,
                reference_element=reference,
                source='confirmed_natal_direction' if elements else 'daily_symbolic_reference',
                confirmed_elements=elements,
                evidence_ids=list(dict.fromkeys(e for d in eligible for e in d.get('evidence_ids', []))),
                timing_effect_confirmed=False)
