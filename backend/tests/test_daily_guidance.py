from copy import deepcopy
from unittest import TestCase
from app.engine.services.daily_guidance import build_daily_guidance


class DailyGuidanceTests(TestCase):
    def query(self, operation='protect'):
        return {'semantic_state': {'confidence': 'medium'}, 'synthesis': {
            'favorable_operations': [{'operation': operation, 'priority_reason': 'urgent', 'evidence_ids': ['core:1']}],
            'caution_operations': [], 'diagnostic_conflicts': [],
        }, 'evidence_ids': ['timing:1']}

    def test_same_ten_god_uses_different_core_direction(self):
        a = build_daily_guidance(self.query(), 'indirect_wealth', [])
        b = build_daily_guidance(self.query('support'), 'indirect_wealth', [])
        self.assertNotEqual(a['mindset'], b['mindset'])
        self.assertNotEqual(a['action'], b['action'])
        self.assertIn('새로 들어온 제안', a['action'])
        self.assertEqual(a['evidence']['priority_reason'], 'urgent')
        self.assertEqual(a['evidence']['evidence_ids'], ['timing:1', 'core:1'])

    def test_caution_unknown_low_and_unresolved_use_verification(self):
        for case in ('caution', 'unknown', 'undetermined', 'unresolved'):
            q = self.query()
            if case == 'caution': q['synthesis']['caution_operations'] = [{'operation': 'protect'}]
            if case == 'unknown': q['synthesis']['favorable_operations'][0]['operation'] = 'new_operation'
            if case == 'undetermined': q['semantic_state']['confidence'] = 'undetermined'
            if case == 'unresolved': q['synthesis']['diagnostic_conflicts'] = [{'resolution': 'preserve_as_unresolved'}]
            with self.subTest(case=case):
                result = build_daily_guidance(q, 'peer', [])
                self.assertEqual(result['evidence']['mode'], 'verify')
                self.assertIn('확인', result['action'])

    def test_daily_candidate_only_adds_check_without_changing_core_direction(self):
        q = self.query('support')
        relation = {'type': 'branch_clash', 'status': 'candidate', 'relationship_id': 'daily:1', 'members': [{'pillar': 'timing:daily'}]}
        a = build_daily_guidance(q, 'direct_resource', [relation])
        self.assertEqual(a['evidence']['primary_operation'], 'support')
        self.assertIn('조건을 확인한 뒤', a['action'])
        relation['members'] = [{'pillar': 'timing:annual'}]
        b = build_daily_guidance(q, 'direct_resource', [relation])
        self.assertNotIn('조건을 확인한 뒤', b['action'])

    def test_priority_order_preserved_and_input_untouched(self):
        q = self.query('preserve_special_structure')
        q['synthesis']['favorable_operations'].append({'operation': 'drain'})
        before = deepcopy(q)
        a = build_daily_guidance(q, 'eating_god', [])
        self.assertEqual(a['evidence']['primary_operation'], 'preserve_special_structure')
        self.assertEqual(q, before)
        self.assertNotIn('\n', a['action'])
        self.assertNotIn('\n', a['mindset'])

    def test_low_confidence_checks_core_direction_without_discarding_it(self):
        q = self.query('support')
        q['semantic_state']['confidence'] = 'low'
        result = build_daily_guidance(q, 'peer', [])
        self.assertEqual(result['evidence']['mode'], 'cautious_core_operation')
        self.assertIn('보충할 자료나 도움', result['action'])
        self.assertIn('확인하기', result['action'])
