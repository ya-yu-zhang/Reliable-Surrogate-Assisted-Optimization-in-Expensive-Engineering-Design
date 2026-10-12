import json,tempfile,unittest
from pathlib import Path
import numpy as np
from src.engineering_optimization_common_continuation import Ledger,decision_classes,effect_label

class CommonContinuationChecks(unittest.TestCase):
    def test_exact_action_classes_and_neutral_control(self):
        result=decision_classes({'mean':2,'ei':3,'pi':3,'lcb':5,'mean_common_shift':2})
        self.assertEqual(result,{2:['mean','mean_common_shift'],3:['ei','pi'],5:['lcb']})
    def test_signed_effect_boundaries(self):
        self.assertEqual(effect_label(1.01e-6,1e-6),'better')
        self.assertEqual(effect_label(-1.01e-6,1e-6),'worse')
        self.assertEqual(effect_label(1e-6,1e-6),'tie')
    def test_failure_is_paid_and_prediction_precedes_solver(self):
        with tempfile.TemporaryDirectory() as d:
            def objective(x):
                first=json.loads((Path(d)/'events.jsonl').read_text().splitlines()[0])
                self.assertEqual(first['event'],'pre')
                raise RuntimeError('fake failure')
            ledger=Ledger(Path(d),1,objective,{})
            with self.assertRaises(RuntimeError): ledger.evaluate(np.zeros(19),'state','branch',1,{'mu':0.,'sd':1.})
            self.assertEqual(ledger.calls,1); ledger.journal.close()
    def test_cached_labels_do_not_consume_new_solver_budget(self):
        with tempfile.TemporaryDirectory() as d:
            x=np.ones(19); key=x.astype('<f8').tobytes().hex()
            ledger=Ledger(Path(d),1,lambda x: (_ for _ in ()).throw(AssertionError('Should not solve')),{key:2.})
            self.assertEqual(ledger.evaluate(x,'state','branch',0,{}),2.)
            self.assertEqual((ledger.calls,ledger.reused),(0,1)); ledger.journal.close()
if __name__=='__main__': unittest.main()
