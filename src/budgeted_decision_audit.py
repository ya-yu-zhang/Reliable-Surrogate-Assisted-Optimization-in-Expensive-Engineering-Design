"""Budgeted conditional first-action audit; no statistical early certificate.

Only identical actions in the SAME state and continuation share trajectories.
All measured classifications require both branches to reach the target horizon.
Incomplete comparisons abstain; h0 ties never certify a later tie.
"""
from __future__ import annotations
import math
from dataclasses import dataclass


def classify(delta, margin):
    if not math.isfinite(delta) or not math.isfinite(margin) or margin < 0:
        raise ValueError("Invalid effect/margin")
    return "better" if delta > margin else "worse" if delta < -margin else "tie"


@dataclass(frozen=True)
class Observation:
    incumbent: float
    point_key: str


def audit(classes, baseline, observe, initial, root_sd, *, horizon=5,
          budget=18, margin=0.001, mode="adaptive", stages=(0, 1, 3, 5)):
    """observe(branch, step) reveals only that next prefix observation.

    The budget conservatively counts requested branch-step labels. Report exact
    distinct points separately, including paid initial-history cache reuse.
    Priority uses observed h1 impact and root uncertainty, never future labels.
    It is an allocation heuristic, not an uncertainty confidence bound.
    """
    if baseline not in classes or initial <= 0 or budget < 0:
        raise ValueError("Invalid audit design")
    if mode not in {"adaptive", "fixed_depth", "fixed_breadth", "immediate", "full"}:
        raise ValueError("Unknown audit mode")
    if tuple(stages) != (0, 1, 3, horizon) or horizon != 5:
        raise ValueError("This frozen version requires horizon five")
    branches=list(classes); others=[b for b in branches if b != baseline]
    depth={b:-1 for b in branches}; latest={}; seen=set(); trace=[]
    spent=0
    if not others:
        names=classes[baseline]
        return {"labels":{n:"tie" for n in names},
                "reasons":{n:"exact_same_action_and_continuation" for n in names},
                "effects":{n:0. for n in names},"depth":depth,
                "requests":0,"distinct_points":0,"trace":[]}

    def advance(branch, target):
        nonlocal spent
        while depth[branch] < target and spent < budget:
            step=depth[branch]+1
            obs=observe(branch, step)
            if not math.isfinite(obs.incumbent) or obs.incumbent <= 0:
                raise ValueError("Invalid oracle label")
            if branch in latest and obs.incumbent > latest[branch]:
                raise ValueError("Incumbent cannot worsen")
            spent+=1; depth[branch]=step; latest[branch]=obs.incumbent
            seen.add(obs.point_key)
            trace.append({"branch":branch,"step":step,"incumbent":obs.incumbent,
                          "point_key":obs.point_key,"requests_so_far":spent})

    if mode == "immediate":
        for branch in branches: advance(branch,0)
    elif mode in {"fixed_depth","full"}:
        for branch in [baseline]+others: advance(branch,horizon)
    elif mode == "fixed_breadth":
        for step in range(horizon+1):
            for branch in [baseline]+others: advance(branch,step)
    else:
        # Stage 0/1 is read for all classes, including immediate ties. This
        # exploration overhead is explicit and may reduce classified coverage.
        for step in [0,1]:
            for branch in [baseline]+others: advance(branch,step)
        advance(baseline,horizon)
        reference=next((t['incumbent'] for t in reversed(trace)
                        if t['branch']==baseline and t['step']==1), initial)
        priority=sorted(others,key=lambda b:(
            -(abs(reference-latest.get(b,initial))/initial + root_sd[b]/initial),
            branches.index(b)))
        # Complete higher-priority trajectories rather than treating a partial
        # curve as an endpoint certificate. Leftover labels remain disclosed.
        for branch in priority:
            for target in stages[2:]: advance(branch,target)

    labels={}; reasons={}; effects={}
    for branch,names in classes.items():
        if branch==baseline:
            label="tie"; reason="exact_same_action_and_continuation"; effect=0.
        elif mode=="immediate" and depth[baseline]>=0 and depth[branch]>=0:
            effect=(latest[baseline]-latest[branch])/initial
            label=classify(effect,margin); reason="h0_proxy_for_h5_not_certificate"
        elif depth[baseline]==horizon and depth[branch]==horizon:
            effect=(latest[baseline]-latest[branch])/initial
            label=classify(effect,margin); reason="measured_target_horizon"
        else:
            label="abstain"; reason="budget_insufficient_for_target_horizon"; effect=None
        for name in names:
            labels[name]=label; reasons[name]=reason; effects[name]=effect
    return {"labels":labels,"reasons":reasons,"effects":effects,"depth":depth,
            "requests":spent,"distinct_points":len(seen),"trace":trace}


def calibration_rule(classes, baseline, predictions, nrmse, coverage, cfg):
    """Constructed baseline, NOT a published diagnostic algorithm.

    Calibrated root expected improvement is a proxy for conditional h5 benefit.
    The gate has no finite-horizon coverage or frequentist guarantee.
    """
    labels={}; base=predictions[baseline]
    reliable=(nrmse<=cfg['calibration_max_nrmse'] and
              coverage>=cfg['calibration_min_coverage'])
    for branch,names in classes.items():
        if branch==baseline: label='tie'
        elif not reliable: label='abstain'
        else: label=classify(predictions[branch]-base,cfg['relative_margin'])
        labels.update({name:label for name in names})
    return labels
