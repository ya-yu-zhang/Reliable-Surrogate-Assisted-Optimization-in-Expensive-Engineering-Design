"""New v2 finite-menu rollout solver and a fresh certificate reader."""
from fractions import Fraction
import heapq
import math
import time
from .rollout_v2_intervals import I, SQRT2PI, cdf, density, probability, exp_times_cdf, fraction_interval
from .filtered_exact_action_sets import prepare_bands, integer_envelope_from_bands


def domain_json(domain):
    return None if domain is None else [str(domain[0]),None if domain[1] is None else str(domain[1])]


def domain_read(domain):
    return None if domain is None else (Fraction(domain[0]),None if domain[1] is None else Fraction(domain[1]))


def dominance(bands,j):
    arrays,_,_ = prepare_bands(*bands,0.)
    la,lb,ua,ub = arrays
    low,high = Fraction(0),None
    for i in range(len(la)):
        if i == j:
            continue
        m,c = ua[j]-la[i],lb[i]-ub[j]
        if m == 0:
            if c < 0 or (c == 0 and i < j):
                return None
        elif m > 0:
            point = Fraction(c,m)
            high = point if high is None else min(high,point)
        else:
            low = max(low,Fraction(c,m))
    return None if high is not None and high <= low else (low,high)


def check_dominance(bands,j,domain):
    """Separate rational endpoint scan; reject positive-measure flat ties."""
    if domain is None:
        return True
    low,high = domain
    if low < 0 or (high is not None and high <= low):
        return False
    la,lb,ua,ub = [[Fraction(float(x)) for x in a] for a in bands]
    for i in range(len(la)):
        if i == j:
            continue
        m,c = ua[j]-la[i],lb[i]-ub[j]
        if i < j and m == c == 0:
            return False
        if m*low > c:
            return False
        if high is None:
            if m > 0:
                return False
        elif m*high > c:
            return False
    return True


def transformed(bound,model):
    if bound is None:
        return I(math.inf)
    if bound <= 0:
        return I(-math.inf)
    return (fraction_interval(bound).log()-I(model["first_mean"]))/I(model["first_sd"])


def event_radius(model,domain):
    if domain is None:
        return float(model["initial"])
    low,high = domain
    mass = probability(transformed(low,model),transformed(high,model))
    return (I(model["initial"])*(1-mass)).hi


def conditional_reward(model,index,x):
    m0 = float(model["initial"])
    first = I(model["first_mean"])+I(model["first_sd"])*x
    logh = first.minimum(I(m0).log())
    p = model["next"][str(index)]
    mu = I(p["mean"])+I(p["gamma"])*x
    sd = I(p["sd"])
    if sd.lo <= 0:
        raise ArithmeticError("Uncertified conditional variance")
    k = (logh-mu)/sd
    return (I(m0)-exp_times_cdf(logh,-k)
            -exp_times_cdf(mu+sd.square()/2,k-sd)).clipped(0.,m0)


class Integrator:
    def __init__(self,model,domains,fixed=None):
        self.model,self.domains,self.fixed = model,domains,fixed
        self.m0 = float(model["initial"])
        self.cross = (I(self.m0).log()-I(model["first_mean"]))/I(model["first_sd"])
        self.mapped = {i:(transformed(lo,model),transformed(hi,model))
                       for i,(lo,hi) in domains.items()}
        cuts = {-8.,-4.,0.,4.,8.}
        cuts.update(x for x in (self.cross.lo,self.cross.hi) if -8 < x < 8)
        if fixed is None:
            cuts.update(x for low,high in self.mapped.values()
                        for x in (low.lo,low.hi,high.lo,high.hi) if -8 < x < 8)
        cuts = sorted(cuts)
        self.cache,self.heap,self.roots = {},[],[]
        self.serial,self.refinements = 0,0
        for a,b in zip(cuts[:-1],cuts[1:]):
            self.roots.append(self.node(a,b))
        self.tail = I(0,(I(self.m0)*2*cdf(-8)).hi)

    def assignment(self,a,b):
        phase = "below" if b <= self.cross.lo else "above" if a >= self.cross.hi else "uncertain"
        active = ([self.fixed] if self.fixed is not None else
                  sorted(i for i,(low,high) in self.mapped.items()
                         if b > low.lo and a < high.hi))
        if not active:
            raise ArithmeticError("Uncovered integration cell")
        return phase,active

    def value_at(self,i,x):
        key = i,x
        if key not in self.cache:
            self.cache[key] = conditional_reward(self.model,i,x)
        return self.cache[key]

    def leaf(self,a,b):
        phase,active = self.assignment(a,b)
        p = probability(a,b)
        cap = (self.m0*p).hi
        if phase == "uncertain" or len(active) != 1:
            return I(0,cap),0.,phase,active
        i = active[0]
        q0,q1 = self.value_at(i,a),self.value_at(i,b)
        n = self.model["next"][str(i)]
        beta = I(self.model["first_sd"]) if phase == "below" else I(0)
        d,sd = I(n["gamma"]),I(n["sd"])
        hmax = min(self.m0,(I(self.model["first_mean"])
                           +I(self.model["first_sd"])*I(a,b)).exp().hi)
        curvature = hmax*(beta.square()+d.square()+(beta-d).square()/(sd*SQRT2PI))
        width = I(b)-a
        error = (curvature*width.square()*p/8).hi
        wr = ((b*p-density(a)+density(b))/width).clipped(0,p.hi)
        wt = ((density(a)-density(b)-a*p)/width).clipped(0,p.hi)
        value = (wr*q0+wt*q1+I(-error,error)).clipped(0,cap)
        return value,error,phase,active

    def node(self,a,b,parent=None):
        value,error,phase,active = self.leaf(a,b)
        self.serial += 1
        node = dict(a=a,b=b,value=value,error=error,phase=phase,active=active,
                    parent=parent,children=None,serial=self.serial)
        if error > 0:
            heapq.heappush(self.heap,(-error,self.serial,node))
        return node

    def refine(self):
        if not self.heap:
            return False
        _,_,node = heapq.heappop(self.heap)
        a,b = node["a"],node["b"]
        mid = a/2+b/2
        if not a < mid < b:
            return False
        left,right = self.node(a,mid,node),self.node(mid,b,node)
        node["children"] = [left,right]
        while node is not None:
            node["value"] = node["children"][0]["value"]+node["children"][1]["value"]
            node = node["parent"]
        self.refinements += 1
        return True

    def value(self):
        return (sum((n["value"] for n in self.roots),I(0))+self.tail).clipped(0,self.m0)

    def curvature_error(self):
        return sum(-x[0] for x in self.heap)

    def certificate(self):
        leaves = []
        def walk(node):
            if node["children"] is None:
                leaves.append(dict(low=node["a"],high=node["b"],
                    interval=node["value"].pair(),phase=node["phase"],active=node["active"]))
            else:
                for child in node["children"]:
                    walk(child)
        for node in self.roots:
            walk(node)
        return dict(fixed=self.fixed,leaves=leaves,tail=self.tail.pair(),
                    value=self.value().pair(),endpoints=len(self.cache),refinements=self.refinements)


def exact_domains(bands,legacy):
    result = integer_envelope_from_bands(*bands,response_lower=0.)
    domains = result["exact_intervals"]
    if domains != legacy:
        raise ArithmeticError("New projection differs from frozen verified domains")
    return domains


def rank_key(branch):
    return int(str(branch).lstrip("b"))


def solve(models,bands,legacy,reference,method,max_seconds=30.,max_refinements=32768):
    start = time.perf_counter()
    integrators,domains,radii = {},{},{}
    projections = 0
    for b,model in models.items():
        if method == "direct":
            domains[b] = exact_domains(bands[b],legacy[b]); projections += 1
            integrators[b] = Integrator(model,domains[b])
            radii[b] = 0.
        else:
            domains[b] = dominance(bands[b],reference[b])
            if not check_dominance(bands[b],reference[b],domains[b]):
                domains[b] = exact_domains(bands[b],legacy[b]);projections += 1
                integrators[b] = Integrator(model,domains[b]);radii[b] = 0.
            else:
                integrators[b] = Integrator(model,legacy[b],reference[b])
                radii[b] = event_radius(model,domains[b])
    refinements = 0
    status,selected = "unresolved",None
    while True:
        intervals = {b:(q.value()+I(-radii[b],radii[b])).clipped(0,models[b]["initial"])
                     for b,q in integrators.items()}
        best = min(models,key=lambda b:(-intervals[b].lo,rank_key(b)))
        rivals = [b for b in models if b != best]
        rival = max(rivals,key=lambda b:intervals[b].hi) if rivals else None
        gap = 0. if rival is None else max(0.,(I(intervals[rival].hi)-intervals[best].lo).hi)
        delta = (I(models[best]["initial"])/1000000).lo
        if gap <= delta:
            status,selected = "accepted",best
            break
        if time.perf_counter()-start >= max_seconds or refinements >= max_refinements:
            break
        choices = [b for b in [best,rival] if b is not None
                   and (integrators[b].fixed is not None or integrators[b].heap)]
        if not choices:
            break
        b = max(choices,key=lambda k:intervals[k].width())
        q = integrators[b]
        if q.fixed is not None and radii[b] >= q.curvature_error():
            domains[b] = exact_domains(bands[b],legacy[b]);projections += 1
            integrators[b] = Integrator(models[b],domains[b]);radii[b] = 0.
        elif q.refine():
            refinements += 1
        elif q.fixed is not None:
            domains[b] = exact_domains(bands[b],legacy[b]);projections += 1
            integrators[b] = Integrator(models[b],domains[b]);radii[b] = 0.
        else:
            break
    certificates = {b:q.certificate() for b,q in integrators.items()}
    record = dict(method=method,status=status,selected=selected,
        intervals={b:v.pair() for b,v in intervals.items()},regret_upper=gap,
        delta_lower=delta,full_projections=projections,refinements=refinements,
        endpoint_evaluations=sum(len(q.cache) for q in integrators.values()),
        local_domains={b:domain_json(domains[b]) for b,q in integrators.items() if q.fixed is not None},
        event_radii=radii,certificates=certificates,
        solve_seconds=time.perf_counter()-start)
    return record


def check(record,models,bands,legacy,reference):
    """Fresh leaf evaluation/coverage/sums; shared arithmetic layer is explicit."""
    start = time.perf_counter()
    if set(record["certificates"]) != set(models) or set(record["intervals"]) != set(models):
        raise ArithmeticError("Incomplete first-action menu")
    intervals = {}
    for b,cert in record["certificates"].items():
        fixed = cert["fixed"]
        radius = 0.
        if fixed is not None:
            if fixed != reference[b]:
                raise ArithmeticError("Reference action mismatch")
            domain = domain_read(record["local_domains"][b])
            if not check_dominance(bands[b],fixed,domain):
                raise ArithmeticError("Invalid local dominance")
            radius = event_radius(models[b],domain)
        q = Integrator(models[b],legacy[b],fixed)
        leaves = sorted(cert["leaves"],key=lambda x:x["low"])
        if not leaves or leaves[0]["low"] != -8 or leaves[-1]["high"] != 8:
            raise ArithmeticError("Invalid window cover")
        total,last = I(0),-8.
        for leaf in leaves:
            a,z = leaf["low"],leaf["high"]
            if a != last or not a < z:
                raise ArithmeticError("Invalid leaf coverage")
            value,_,phase,active = q.leaf(a,z)
            if phase != leaf["phase"] or active != leaf["active"]:
                raise ArithmeticError("Invalid cell assignment")
            stored = I(leaf["interval"])
            if stored.lo > value.lo or stored.hi < value.hi:
                raise ArithmeticError("Invalid leaf enclosure")
            total += value
            last = z
        value = (total+q.tail+I(-radius,radius)).clipped(0,models[b]["initial"])
        stored = I(record["intervals"][b])
        # Different summation trees can add a few ulps. Use the reader's fresh
        # value as the accepted interval rather than trusting producer totals.
        intervals[b] = value.hull(stored)
    chosen = record["selected"]
    accepted = False
    regret = None
    if chosen is not None:
        regret = max([0.]+[(I(v.hi)-intervals[chosen].lo).hi
                          for b,v in intervals.items() if b != chosen])
        delta = (I(models[chosen]["initial"])/1000000).lo
        accepted = regret <= delta
    return dict(accepted=accepted,regret_upper=regret,
        intervals={b:v.pair() for b,v in intervals.items()},
        checker_seconds=time.perf_counter()-start,
        leaf_cells=sum(len(c["leaves"]) for c in record["certificates"].values()),
        shared_interval_and_curvature_layer=True)
