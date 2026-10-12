import unittest
from src.budgeted_decision_audit import Observation,audit

class BudgetAuditTests(unittest.TestCase):
    def run_audit(self,curves,budget=18,mode='adaptive'):
        trace=[]
        def observe(b,h):
            self.assertEqual(h,sum(x[0]==b for x in trace))
            trace.append((b,h))
            return Observation(curves[b][h],f'{b}:{h}')
        result=audit({b:[b] for b in curves},'mean',observe,100.,
                     {b:1. for b in curves},budget=budget,mode=mode)
        self.assertLessEqual(len(trace),budget)
        return result
    def test_immediate_tie_cannot_be_certified_as_future_tie(self):
        c={'mean':[100]*6,'ei':[100,100,100,100,100,80]}
        a=self.run_audit(c,4)
        self.assertEqual(a['labels']['ei'],'abstain')
        b=self.run_audit(c,12)
        self.assertEqual(b['labels']['ei'],'better')
    def test_immediate_winner_can_be_delayed_loser(self):
        c={'mean':[100,100,90,90,70,70],'ei':[90]*6}
        self.assertEqual(self.run_audit(c,12,'immediate')['labels']['ei'],'better')
        self.assertEqual(self.run_audit(c,12)['labels']['ei'],'worse')
    def test_unqueried_future_cannot_change_trace_or_outputs(self):
        a=self.run_audit({'mean':[100]*6,'ei':[100]*6},4)
        b=self.run_audit({'mean':[100]*6,'ei':[100,100,99,98,90,70]},4)
        self.assertEqual(a,b)
    def test_exact_equivalence_shares_branch_and_classification(self):
        calls=[]
        def oracle(b,h): calls.append((b,h));return Observation(100.,f'{b}:{h}')
        r=audit({'a':['mean','pi'],'b':['ei','lcb']},'a',oracle,100.,
                {'a':1.,'b':1.},budget=12)
        self.assertEqual(len(calls),12)
        self.assertEqual(r['labels']['mean'],r['labels']['pi'])
        self.assertEqual(r['labels']['ei'],r['labels']['lcb'])
    def test_four_distinct_actions_charge_screening_and_abstentions(self):
        r=self.run_audit({b:[100]*6 for b in ['mean','ei','pi','lcb']},18)
        self.assertEqual(r['requests'],18)
        self.assertEqual(list(r['labels'].values()).count('abstain'),2)
    def test_distinct_actions_with_equal_utility_are_not_merged(self):
        r=self.run_audit({'mean':[100]*6,'ei':[100]*6},12)
        self.assertEqual(r['distinct_points'],12)
        self.assertEqual(r['reasons']['ei'],'measured_target_horizon')

if __name__=='__main__':unittest.main()
