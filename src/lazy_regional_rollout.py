"""Lazy response discovery from affine bands, without a complete action set.

Queries only encountered bivariate posterior marginals. Unqueried responses
may be any positive conditional laws; no full-joint SPD claim is made.
"""
from fractions import Fraction
import math
import time

from .rollout_v2_intervals import I,cdf,probability
from .rollout_v2_solver import (Integrator,dominance,check_dominance,
    transformed,domain_json,domain_read,rank_key)
from .rollout_regional_enclosure import baseline


def initialize_cells(model):
    cross=(I(model['initial']).log()-I(model['first_mean']))/I(model['first_sd'])
    cuts=sorted({-8.,-4.,0.,4.,8.}|{v for v in [cross.lo,cross.hi] if -8<v<8})
    return [dict(low=a,high=b,action=None) for a,b in zip(cuts[:-1],cuts[1:])]


def unknown_value(model,low,high,method):
    upper=(model['initial']*probability(low,high)).hi
    lower=baseline(model,low,high).lo if method=='regional' else 0.
    return I(lower,upper)


def selection(intervals):
    best=min(intervals,key=lambda b:(-intervals[b].lo,rank_key(b)))
    rivals=[b for b in intervals if b!=best]
    rival=max(rivals,key=lambda b:(intervals[b].hi,-rank_key(b))) if rivals else None
    regret=0. if rival is None else max(0.,(I(intervals[rival].hi)-intervals[best].lo).hi)
    return best,rival,regret


def solve(models,bands,nominal,oracle,method,max_seconds=5.,max_operations=2048):
    began=time.perf_counter();cells={b:initialize_cells(m) for b,m in models.items()}
    discovered={b:{} for b in models};integrators={};scans=checks=operations=0
    def value(b,cell):
        if 'interval' in cell:return I(cell['interval'])
        if cell['action'] is None:
            return unknown_value(models[b],cell['low'],cell['high'],method)
        key=b,cell['action']
        if key not in integrators:
            j=cell['action'];models[b]['next'][str(j)]=oracle(b,j)
            integrators[key]=Integrator(models[b],{j:(Fraction(0),None)},j)
        return integrators[key].leaf(cell['low'],cell['high'])[0]
    status,selected='unresolved',None
    reason='resource_limit'
    while True:
        intervals={}
        for b in models:
            for cell in cells[b]:
                cell['interval']=value(b,cell).pair()
            tail=I(0,(I(models[b]['initial'])*2*cdf(-8)).hi)
            intervals[b]=(sum((I(c['interval']) for c in cells[b]),I(0))+tail).clipped(0,models[b]['initial'])
        best,rival,regret=selection(intervals)
        delta=(I(models[best]['initial'])/1000000).lo
        if regret<=delta:
            status,selected,reason='accepted',best,'selection_bound'
            break
        if operations>=max_operations or time.perf_counter()-began>=max_seconds:break
        choices=[(b,c) for b in [best,rival] if b is not None for c in cells[b]]
        b,cell=max(choices,key=lambda bc:(I(bc[1]['interval']).width(),-rank_key(bc[0]),-bc[1]['low']))
        lo,hi=cell['low'],cell['high'];mid=lo/2+hi/2
        if not lo<mid<hi:
            reason='binary_cell_floor';break
        operations+=1
        if cell['action'] is not None:
            replacement=[dict(low=lo,high=mid,action=cell['action']),dict(low=mid,high=hi,action=cell['action'])]
        else:
            found=None
            for j,dom in discovered[b].items():
                if dom is None:continue
                a=max(lo,transformed(dom[0],models[b]).hi)
                z=min(hi,transformed(dom[1],models[b]).lo)
                if a<z and a<=mid<=z:found=(j,dom,a,z);break
            if found is None:
                z=math.exp(I(models[b]['first_mean']).mid()+I(models[b]['first_sd']).mid()*mid)
                num,den=z.as_integer_ratio();slopes,intercepts=nominal[b]
                j=min(range(len(slopes)),key=lambda i:(slopes[i]*num+intercepts[i]*den,i))
                dom=dominance(bands[b],j);scans+=1
                if not check_dominance(bands[b],j,dom):raise ArithmeticError('Invalid discovered domain')
                checks+=1;discovered[b][j]=dom
                if dom is not None:
                    a=max(lo,transformed(dom[0],models[b]).hi)
                    z=min(hi,transformed(dom[1],models[b]).lo)
                    if a<z:found=(j,dom,a,z)
            if found is None:
                replacement=[dict(low=lo,high=mid,action=None),dict(low=mid,high=hi,action=None)]
            else:
                j,dom,a,z=found;replacement=[]
                if lo<a:replacement.append(dict(low=lo,high=a,action=None))
                replacement.append(dict(low=a,high=z,action=j))
                if z<hi:replacement.append(dict(low=z,high=hi,action=None))
        index=cells[b].index(cell);cells[b][index:index+1]=replacement
    return dict(method=method,status=status,selected=selected,reason=reason,
        regret_upper=regret,delta_lower=delta,intervals={b:v.pair() for b,v in intervals.items()},
        cells=cells,domains={b:{str(j):domain_json(d) for j,d in ds.items()} for b,ds in discovered.items()},
        counters=dict(cell_operations=operations,dominance_scans=scans,producer_dominance_checks=checks,
            conditional_reward_endpoint_evaluations=sum(len(q.cache) for q in integrators.values()),
            complete_projections=0),solve_seconds=time.perf_counter()-began)


def check(record,models,bands,posterior):
    began=time.perf_counter();intervals={};endpoints=0;domain_checks=0
    if set(record['cells'])!=set(models):raise ArithmeticError('Missing menu branch')
    for b,model in models.items():
        ds={int(j):domain_read(d) for j,d in record['domains'][b].items()}
        for j,dom in ds.items():
            if not check_dominance(bands[b],j,dom):raise ArithmeticError('Bad local proof')
            domain_checks+=1
        qs={};total=I(0);last=-8.
        for cell in record['cells'][b]:
            lo,hi,j=cell['low'],cell['high'],cell['action']
            if lo!=last or not lo<hi:raise ArithmeticError('Bad cover')
            last=hi
            if j is None:v=unknown_value(model,lo,hi,record['method'])
            else:
                if j not in ds or ds[j] is None:raise ArithmeticError('Missing action proof')
                d=ds[j]
                if lo<transformed(d[0],model).hi or hi>transformed(d[1],model).lo:raise ArithmeticError('Action outside stable region')
                if j not in qs:
                    model['next'][str(j)]=posterior[b,str(j)]['conditional']
                    qs[j]=Integrator(model,{j:(Fraction(0),None)},j)
                v=qs[j].leaf(lo,hi)[0]
            stored=I(cell['interval'])
            if stored.lo>v.lo or stored.hi<v.hi:raise ArithmeticError('Unsound cell')
            total+=v
        if last!=8.:raise ArithmeticError('Missing tail boundary')
        tail=I(0,(I(model['initial'])*2*cdf(-8)).hi)
        intervals[b]=(total+tail).clipped(0,model['initial'])
        endpoints+=sum(len(q.cache) for q in qs.values())
    selected=record['selected'];regret=None;accepted=False
    if selected is not None:
        regret=max([0.]+[(I(v.hi)-intervals[selected].lo).hi for b,v in intervals.items() if b!=selected])
        accepted=regret<=record['delta_lower']
    return dict(accepted=accepted,regret_upper=regret,
        intervals={b:v.pair() for b,v in intervals.items()},
        conditional_reward_endpoint_evaluations=endpoints,dominance_checks=domain_checks,
        checker_seconds=time.perf_counter()-began,shared_arithmetic_and_curvature_layer=True)
