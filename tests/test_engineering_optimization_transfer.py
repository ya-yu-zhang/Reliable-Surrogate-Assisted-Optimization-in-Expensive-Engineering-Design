"""Cheap checks of scientific boundaries; no new FE labels."""
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np
from src.engineering_optimization_transfer import Ledger, policy_choice, select_policy, seed


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.cfg = json.loads(Path("configs/engineering_optimization_transfer.json").read_text())

    def test_paid_budget_equations(self):
        c=self.cfg
        audit=c["initial"]+len(c["policies"])*c["pilot_steps"]+c["budget"]-c["initial"]
        portfolio=c["initial"]+len(c["policies"])*(c["budget"]-c["initial"])
        self.assertEqual((audit,portfolio),(280,626))
        self.assertEqual((audit+portfolio)*c["repeats"]*len(c["forcedist"]),c["global_call_cap"])

    def test_pre_before_call_and_failure_is_paid(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)
            def objective(x):
                rows=[json.loads(l) for l in (path/"events.jsonl").read_text().splitlines()]
                self.assertEqual(rows[-1]["event"],"pre")
                raise FloatingPointError("synthetic failure")
            ledger=Ledger(path,1,objective)
            with self.assertRaises(FloatingPointError):
                ledger.evaluate(np.zeros(19),"audited","initial",None,1)
            self.assertEqual(ledger.calls,1)
            with self.assertRaises(RuntimeError):
                ledger.evaluate(np.zeros(19),"audited","initial",None,2)
            ledger.journal.close()
            rows=[json.loads(l) for l in (path/"events.jsonl").read_text().splitlines()]
            self.assertEqual([r["event"] for r in rows],["pre","failure"])

    def test_seed_namespaces_and_exact_ties(self):
        self.assertNotEqual(seed(self.cfg,0,0,55),seed(self.cfg,0,0,56))
        self.assertNotEqual(seed(self.cfg,0,0,11),seed(self.cfg,1,0,11))
        self.assertEqual(select_policy({p:1. for p in self.cfg["policies"]},self.cfg["tie_priority"]),"pi")
        for p in self.cfg["policies"]:
            self.assertEqual(policy_choice(np.ones(3),np.ones(3),1.,1.,p,self.cfg),0)


if __name__ == "__main__": unittest.main()
