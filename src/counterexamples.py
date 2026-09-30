"""Deterministic illustrations; these are NOT benchmark runs or a new theorem."""
from pathlib import Path
import json
import numpy as np


def main():
    # 9 unclaimed bounds succeed; the ONLY improvement claim fails.
    best=0.;tau=.01
    H=np.array([1.]*9+[-1.]);y=np.array([.5]*9+[.5])
    claim=H<best-tau;failed=y>H;false=claim & (y>=best-tau)
    assert np.all(~false|failed)
    report=dict(illustration='Overall 90% upper coverage with 100% FDP on the claimed subset',
        H=H.tolist(),y=y.tolist(),best=best,tau=tau,overall_failure=float(failed.mean()),
        claims=int(claim.sum()),false_claims=int(false.sum()),fdp=float(false.sum()/claim.sum()),
        conclusion='Overall coverage does not bound failure rate on an improvement-claim subset.')
    # Candidate-independent corrections leave the greedy minimizer unchanged.
    mu=np.array([-.8,-.2,.1]);upper=mu+.4
    report['constant_correction']=dict(mu=mu.tolist(),H=upper.tolist(),argmin_mu=int(mu.argmin()),argmin_H=int(upper.argmin()))
    out=Path(__file__).resolve().parents[1]/'results/counterexamples'
    out.mkdir(parents=True,exist_ok=True)
    (out/'examples.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
