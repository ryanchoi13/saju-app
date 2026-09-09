from copy import deepcopy
from unittest import TestCase
from app.engine.services.daily_topics import select_daily_topics


class DailyTopicsTests(TestCase):
    def query(self, god='eating_god'):
        return {'timing': {k: {'ten_god': v} for k,v in dict(daily=god, monthly='hurting_officer', annual='direct_wealth', luck_cycle='seven_killings').items()},
                'synthesis': {'confidence': 'medium', 'favorable_operations': [], 'caution_operations': []}}

    def relation(self, kind='branch_clash'):
        return {'relationship_id': 'r1', 'type': kind, 'status': 'candidate', 'members': [{'pillar': 'timing:daily', 'symbol': '子'}, {'pillar': 'day', 'symbol': '午'}]}

    def test_supporting_star_cannot_select_title_and_duplicate_signal_not_counted(self):
        q=self.query()
        a=select_daily_topics(q,[self.relation()],[])
        b=select_daily_topics(q,[self.relation(),self.relation('stem_control')],['peach_blossom','peach_blossom'])
        self.assertEqual(a['title'],b['title'])
        self.assertEqual(b['evidence']['independent_daily_tension_groups'],0)
        self.assertEqual(len([n for n in b['evidence']['notes'] if n['origin']=='shensha:peach_blossom']),1)
        self.assertNotIn('연애운',b['advice'])

    def test_secondary_notes_retained_without_sentence_cap(self):
        q=self.query()
        q['timing']['annual']['ten_god']='direct_wealth'
        q['timing']['monthly']['ten_god']='direct_wealth'
        q['synthesis']['favorable_operations']=[{'operation':'support','evidence_ids':['support:1']}]
        r=select_daily_topics(q,[self.relation()],['flower_canopy','travel_horse','literary_star','peach_blossom'])
        topics={n['topic'] for n in r['evidence']['notes']}
        self.assertTrue({'reflection','movement','learning','relationships'} <= topics)
        self.assertNotIn('money',topics)
        self.assertNotIn('rest',topics)
        self.assertGreaterEqual(r['advice'].count('.'),5)
        self.assertFalse(r['evidence']['hourly_prediction'])

    def test_core_priority_can_refine_title_with_daily_context(self):
        q=self.query('hurting_officer')
        a=select_daily_topics(q,[],[])
        q['synthesis']['favorable_operations']=[{'operation':'mediate','urgency':'high'}]
        b=select_daily_topics(q,[],[])
        self.assertEqual(a['title'],b['title'])
        self.assertEqual(a['advice'],b['advice'])
        q['synthesis']['caution_operations']=[{'operation':'mediate'}]
        c=select_daily_topics(q,[],[])
        self.assertEqual(a['title'],c['title'])

    def test_unknown_context_does_not_invent_event_and_input_unchanged(self):
        q=self.query('indirect_wealth');before=deepcopy(q)
        r=select_daily_topics(q,[],[])
        self.assertEqual(q,before)
        self.assertNotIn('당첨',r['advice'])
        q['synthesis']['confidence']='undetermined'
        r=select_daily_topics(q,[],[])
        self.assertEqual(r['evidence']['primary_topic'],'balance')

    def test_assessed_daily_signal_requires_status_and_provenance(self):
        from app.engine.services.daily_evidence import daily_relationship_evidence
        q=self.query()
        relation=self.relation()
        q['activated_state']={'relationship_changes':[relation,dict(relation)]}
        self.assertEqual(daily_relationship_evidence(q)['candidate_group_count'],1)
        before=select_daily_topics(q,[],[])
        relation.update(status='active',requires_reassessment=False,evidence_ids=['assessment:1'])
        q['activated_state']['relationship_changes']=[relation]
        # Active merely says a relationship was recognized. A matching effect
        # assessment with valence is required to change the warning copy.
        self.assertEqual(select_daily_topics(q,[],[])['time_flow'],before['time_flow'])
        effect = dict(relation, checklist_evaluated=True, eligibility='conditional',
                      effect_status='established',valence='adverse')
        q['activated_state']['temporal_conditions']={'records':[effect]}
        after=select_daily_topics(q,[],[])
        self.assertNotEqual(before['time_flow']['afternoon'],after['time_flow']['afternoon'])
        effect['requires_reassessment']=True
        self.assertEqual(select_daily_topics(q,[],[])['advice'],before['advice'])

    def test_beneficial_clash_is_not_a_warning_and_adverse_combination_is(self):
        for kind, valence, caution in [('branch_clash','beneficial',False), ('stem_combination','adverse',True)]:
            q=self.query()
            baseline=select_daily_topics(q,[],[])
            relation=self.relation(kind)
            q['activated_state']={'relationship_changes':[relation], 'temporal_conditions':{'records':[
                dict(relation, checklist_evaluated=True,eligibility='conditional',effect_status='established',
                     valence=valence,requires_reassessment=False,evidence_ids=['effect:1'])]}}
            after=select_daily_topics(q,[],[])
            self.assertEqual(after['time_flow']['afternoon'] != baseline['time_flow']['afternoon'],caution)

    def test_effect_for_different_members_cannot_change_copy(self):
        q=self.query();baseline=select_daily_topics(q,[],[])
        relation=self.relation()
        effect=dict(relation,checklist_evaluated=True,eligibility='conditional',effect_status='established',
                    valence='adverse',requires_reassessment=False,evidence_ids=['effect:1'])
        effect['members']=[{'pillar':'timing:daily','symbol':'卯'},{'pillar':'day','symbol':'酉'}]
        q['activated_state']={'relationship_changes':[relation],'temporal_conditions':{'records':[effect]}}
        self.assertEqual(select_daily_topics(q,[],[])['advice'],baseline['advice'])

    def test_unrelated_conflict_keeps_supported_rest_note(self):
        q=self.query('seven_killings')
        q['synthesis']['favorable_operations']=[{'operation':'support','evidence_ids':['strength:1']}]
        q['synthesis']['diagnostic_conflicts']=[{'operations':['warm','cool'],'resolution':'preserve_as_unresolved'}]
        result=select_daily_topics(q,[],[])
        self.assertTrue(any(n['topic']=='rest' for n in result['evidence']['notes']))
        q['synthesis']['diagnostic_conflicts'][0]['operations']=['support','drain']
        self.assertFalse(any(n['topic']=='rest' for n in select_daily_topics(q,[],[])['evidence']['notes']))

    def test_background_cannot_create_daily_relationship_warning(self):
        q=self.query()
        q['synthesis']['favorable_operations']=[{'operation':'resolve_conflict','urgency':'high'}]
        result=select_daily_topics(q,[],[])
        self.assertFalse(any(n['topic']=='relationships' for n in result['evidence']['notes']))
