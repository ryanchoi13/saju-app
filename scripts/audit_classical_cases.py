"""Compare sourced natal examples with actual fact/resolver outputs.

No fabricated birthdays, no natal pillars relabelled as daily pillars, and no
claim that a conservative hold reproduces a positive source interpretation.
"""
import json
from pathlib import Path
from app.engine.facts.hidden_stems import calculate_hidden_stems
from app.engine.facts.rooting import calculate_roots, calculate_exposed_stems
from app.engine.facts.relationship_candidates import calculate_relationship_candidates
from app.engine.relationships import resolve_relationships
from app.engine.timing.engine import _pillar

FIXTURE=Path(__file__).resolve().parents[1]/'backend/tests/fixtures/classical_combination_cases.json'


def run_cases():
    fixture=json.loads(FIXTURE.read_text())
    rows=[]
    for case in fixture['cases']:
        pillars={k:_pillar(v) for k,v in zip(fixture['source']['pillar_order'],case['pillars'])}
        hidden=calculate_hidden_stems(pillars)
        roots=calculate_roots(pillars,hidden)
        exposed=calculate_exposed_stems(pillars,hidden)
        candidates=calculate_relationship_candidates(pillars)
        resolved,evidence=resolve_relationships(candidates,pillars,roots,exposed)
        targets=[r for r in resolved if r.type==case['relationship']['type'] and
            {m['pillar'] for m in r.members}==set(case['relationship']['pillars'])]
        target=targets[0] if len(targets)==1 else None
        connections={k:[r.model_dump(mode='json') for r in roots.items if r.stem_pillar==k]
            for k in case['relationship']['pillars']}
        transformation=target.transformation.status.value if target and target.transformation else None
        transformation_check=('not_scored' if not case.get('expected_transformation') else
            'contradiction' if transformation=='established' else
            'matched' if transformation=='not_established' else 'unresolved')
        checks=[]
        for expected in case['expected_functions']:
            assessment=next((a for a in (target.member_function_assessments if target else [])
                if a['pillar']==expected['pillar'] and a['stem']==expected['stem']),None)
            actual=assessment.get('function_state') if assessment else None
            checks.append(dict(expected=expected,actual=actual,status=(
                'unsupported' if actual is None else 'unresolved' if actual=='undetermined'
                else 'matched' if actual==expected['state'] else 'contradiction')))
        function_status=next((s for s in ['contradiction','unsupported','unresolved']
            if any(c['status']==s for c in checks)), 'matched')
        rows.append(dict(id=case['id'],pillars=case['pillars'],
            expected_functions=case['expected_functions'],source_interpretation=case['source_interpretation'],
            relationship_found=target is not None,
            actual_relationship=target.model_dump(mode='json') if target else None,
            root_connections=connections,
            function_verdict=dict(status=function_status,checks=checks),
            expected_transformation=case.get('expected_transformation'),
            transformation_verdict=transformation_check,
            source_result_reproduced=(function_status=='matched' and
                transformation_check in {'matched','not_scored'}),
            evidence_complete=bool(target and set(target.evidence_ids)<={e.id for e in evidence})))
    return dict(source=fixture['source'],summary=dict(cases=len(rows),
        relationships_found=sum(r['relationship_found'] for r in rows),
        source_results_reproduced=sum(r['source_result_reproduced'] for r in rows),
        unsupported_function_cases=sum(r['function_verdict']['status']=='unsupported' for r in rows),
        unresolved_function_cases=sum(r['function_verdict']['status']=='unresolved' for r in rows)),cases=rows)


if __name__=='__main__':
    print(json.dumps(run_cases(),ensure_ascii=False,indent=2))
