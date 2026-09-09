"""Benchmark integrity tests, NOT tests claiming classical outcomes reproduced."""
from pathlib import Path
import importlib.util
import json
from unittest import TestCase
from unittest.mock import patch
from app.engine.core.models import TransformationStatus

PATH=Path(__file__).resolve().parents[2]/'scripts/audit_classical_cases.py'
spec=importlib.util.spec_from_file_location('classical_audit',PATH)
audit=importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class ClassicalBenchmarkIntegrityTests(TestCase):
    def test_inputs_remain_natal_and_have_provenance(self):
        fixture=json.loads(audit.FIXTURE.read_text())
        self.assertEqual(fixture['scope'],'natal_only')
        self.assertEqual(fixture['source']['pillar_order'],['year','month','day','hour'])
        self.assertTrue(fixture['source']['url'].startswith('https://'))
        for c in fixture['cases']:
            self.assertEqual(len(c['pillars']),4)
            self.assertTrue(c['locator'])
            for expected in c['expected_functions']:
                i=fixture['source']['pillar_order'].index(expected['pillar'])
                self.assertEqual(c['pillars'][i][0],expected['stem'])

    def test_actual_candidate_detection_and_evidence_reproduce(self):
        result=audit.run_cases()
        self.assertEqual(result['summary']['relationships_found'],4)
        self.assertTrue(all(c['evidence_complete'] for c in result['cases']))
        self.assertTrue(all(not m['pillar'].startswith('timing:')
            for c in result['cases'] for m in c['actual_relationship']['members']))

    def test_partial_function_match_is_not_scored_as_full_source_reproduction(self):
        result=audit.run_cases()
        self.assertEqual(result['summary']['source_results_reproduced'],4)
        self.assertEqual(result['summary']['unsupported_function_cases'],0)
        self.assertEqual(result['summary']['unresolved_function_cases'],0)
        target=next(c for c in result['cases'] if c['expected_transformation'])
        self.assertEqual(target['function_verdict']['status'],'matched')
        self.assertEqual(target['transformation_verdict'],'matched')
        resolve = audit.resolve_relationships
        def omit_conversion_judgment(*args, **kwargs):
            relations, evidence = resolve(*args, **kwargs)
            for relation in relations:
                if relation.transformation and relation.transformation.status is TransformationStatus.NOT_ESTABLISHED:
                    relation.transformation.status = TransformationStatus.CONDITIONAL
            return relations, evidence
        with patch.object(audit, 'resolve_relationships', side_effect=omit_conversion_judgment):
            partial = audit.run_cases()
        self.assertEqual(partial['summary']['source_results_reproduced'],3)
        target = next(c for c in partial['cases'] if c['expected_transformation'])
        self.assertEqual(target['function_verdict']['status'],'matched')
        self.assertEqual(target['transformation_verdict'],'unresolved')
        self.assertFalse(target['source_result_reproduced'])

    def test_root_presence_alone_does_not_separate_source_outcomes(self):
        result=audit.run_cases()
        retained=[c for c in result['cases'] if all(x['state']=='retained' for x in c['expected_functions'])]
        reduced=[c for c in result['cases'] if all(x['state']=='reduced' for x in c['expected_functions'])]
        self.assertEqual(len(retained),2);self.assertEqual(len(reduced),2)
        self.assertTrue(any(all(c['root_connections'].values()) for c in retained))
        self.assertTrue(any(all(c['root_connections'].values()) for c in reduced))
        self.assertEqual(result,audit.run_cases())
