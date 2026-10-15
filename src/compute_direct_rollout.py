"""Direct two-step values on frozen development inputs; no future labels.

Ordinary floating quadrature, not a certified optimizer.  The declared selector
is the exact lower envelope of the saved binary nominal affine coefficients.
Coefficient-band ambiguity is reported separately, never counted as disjoint
action probabilities.  No physical objective, bound evaluator or GP fit is used.
"""
from pathlib import Path
from fractions import Fraction
import csv
import hashlib
import importlib.metadata
import json
import math
import time
import warnings

import numpy as np
from scipy.integrate import quad, IntegrationWarning
from scipy.linalg import cho_solve
from scipy.special import ndtr
from sklearn.gaussian_process.kernels import ConstantKernel, Matern

from .verify_and_benchmark_gp_envelope import locate, future_pool
from .certified_affine_envelope import coefficient_bands
from .filtered_exact_action_sets import integer_envelope_from_bands

BASELINE = '58f539c2d0738b20c7d0d4889fe8d808a03a3019'
PARENT = 'd43ae048287da985addf324b0e83f1cea7b14daf'
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'results/direct_rollout_reference_20261015'
SQRT2PI = math.sqrt(2*math.pi)
GL16 = np.polynomial.legendre.leggauss(16)
GL32 = np.polynomial.legendre.leggauss(32)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name, obj):
    (OUT/name).write_text(json.dumps(obj, indent=2, allow_nan=False)+'\n')


def phi(x):
    return math.exp(-x*x/2)/SQRT2PI if math.isfinite(x) else 0.


def mass(lo, hi):
    return max(0., float(ndtr(-lo)-ndtr(-hi) if lo >= 0 else ndtr(hi)-ndtr(lo)))


def ei(t, mu, sd):
    if sd == 0:
        return max(0., t-mu)
    d = t-mu
    return max(0., d*float(ndtr(d/sd))+sd*phi(d/sd))


def whole_line(arrays):
    """Closed exact rational band intervals on both half-lines."""
    la, lb, ua, ub = arrays
    result = []
    for flip, args in ((False, arrays), (True, ([-x for x in ua], lb, [-x for x in la], ub))):
        found = integer_envelope_from_bands(*args, response_lower=0.)
        for i in found['indices']:
            lo, hi = found['exact_intervals'][i]
            result.append((i, None if hi is None else -hi, -lo) if flip else (i, lo, hi))
    return result


def cells(intervals, extra=()):
    """Disjoint open cells; endpoints have zero Gaussian probability."""
    ends = sorted({v for _, lo, hi in intervals for v in (lo, hi) if v is not None}
                  | {v for v in extra if v is not None})
    for lo, hi in zip([None]+ends, ends+[None]):
        if lo is not None and hi is not None and lo == hi:
            continue
        point = (hi-1 if lo is None else lo+1 if hi is None else (lo+hi)/2)
        active = sorted({i for i, a, b in intervals
                         if (a is None or a < point) and (b is None or point < b)})
        if not active:
            raise AssertionError('Response domain not covered')
        yield lo, hi, active


def abs_affine(a, b, lo, hi):
    cuts = [lo, hi]
    if b and lo < -a/b < hi:
        cuts.insert(1, -a/b)
    return sum(abs(a*mass(l, u)+b*(phi(l)-phi(u)))
               for l, u in zip(cuts[:-1], cuts[1:]))


def integrate(partition, mz, sz, means, gammas, sigmas, incumbent, kind, tight):
    """Integrate scaled conditional EI, or a stable clipped-gain diagnostic."""
    scale = incumbent if kind == 'clipped' else max(incumbent, abs(mz), sz,
                float(np.max(np.abs(means))), float(np.max(sigmas)), 1.)
    epsabs, epsrel = ((1e-14, 2e-13) if tight else (1e-13, 2e-12))
    nodes, weights = GL32 if tight else GL16
    total = error = 0.
    evaluations = 0
    messages = []
    for zlo, zhi, i in partition:
        lo = max(-12., -math.inf if zlo is None else (float(zlo)-mz)/sz)
        hi = min(12., math.inf if zhi is None else (float(zhi)-mz)/sz)
        if lo >= hi:
            continue
        mu, gamma, sigma = means[i], gammas[i], sigmas[i]
        t = incumbent if kind == 'value' else 0.
        breaks = [-8., -4., -1., 0., 1., 4., 8., (t-mz)/sz, -mz/sz,
                  (incumbent-mz)/sz]
        if gamma:
            breaks.append((t-mu)/gamma)
        if sz != gamma:
            breaks.append((mu-mz)/(sz-gamma))
        cuts = sorted({lo, hi, *(x for x in breaks if lo < x < hi)})

        def f(x):
            z, conditional_mean = mz+sz*x, mu+gamma*x
            if kind == 'clipped':
                h = min(incumbent, max(0., z))
                if h == 0:
                    gain = incumbent
                elif sigma == 0:
                    gain = incumbent-min(h, max(0., conditional_mean))
                else:
                    # Integral_0^h P(Y<t)dt: avoids subtracting O(sd) EIs.
                    gain = incumbent-h+h/2*float(weights@ndtr(
                        ((nodes+1)*h/2-conditional_mean)/sigma))
                return gain/scale*phi(x)
            return ei(min(t, z), conditional_mean, sigma)/scale*phi(x)

        for a, b in zip(cuts[:-1], cuts[1:]):
            result = quad(f, a, b, epsabs=epsabs, epsrel=epsrel,
                          limit=200, full_output=1)
            value, err, info = result[:3]
            if len(result) > 3:
                messages.append(result[3])
            # QUADPACK diagnostics are evidence, never a rigorous enclosure.
            if info['last'] >= 200:
                raise ArithmeticError('Quadrature subdivision limit reached')
            total += value*scale
            error += err*scale
            evaluations += info['neval']
    if kind != 'clipped':
        total += ei(incumbent if kind == 'value' else 0., mz, sz)
    return total, error, evaluations, messages


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    assert not (OUT/'decisions_frozen.json').exists(), 'Do not overwrite a frozen decision record'
    design = dict(baseline=BASELINE, parent_commit=PARENT,
        status='ordinary numerical reference, no rigorous value/selection certificate',
        scope='all seen development inputs; not independent policy validation',
        target='E[m0-min(m0,Z,Y_pi(Z))] under fixed root joint Gaussian',
        selector='saved binary nominal affine lower envelope; lowest eligible index at ties',
        first_action_tie='lowest numeric branch identifier',
        band_overlap='separate disjoint overlay and floating coupling-error diagnostic',
        root_support='full Gaussian; no truncation or probability renormalization',
        numerical_window_standard_deviations=12, tail='linear growth bound reported separately',
        primary_quad=dict(epsabs_scaled=1e-13, epsrel=2e-12, limit=200),
        crosscheck_quad=dict(epsabs_scaled=1e-14, epsrel=2e-13, limit=200),
        clipped_diagnostic='direct stable bounded integral, 16 vs 32 Gauss-Legendre nodes',
        delta_over_initial=1e-6, metadata_states=60, nontrivial_states=43, branches=114,
        future_response_journals_read=False, new_physical_evaluations=0,
        new_bound_queries=0, new_hyperparameter_fits=0, new_independent_samples=0,
        source_sha256=digest(Path(__file__)))
    save('DESIGN.json', design)  # Frozen before any new root algebra or integration.
    inputs = {}

    def read(path):
        inputs[str(path.relative_to(ROOT))] = digest(path)
        return json.loads(path.read_text())

    gp = ROOT/'gp_attachment/results/engineering_optimization_gp_reachability_v1'
    plan, status = read(gp/'plan.json'), read(gp/'construction_status.json')
    assert status['baseline_commit'] == BASELINE and len(plan['mean_states']) == 60
    assert len(status['files_sha256']) == 43 and len(status['alias_only_exclusions']) == 17
    old = read(ROOT/'results/rollout_event_preflight_20261015/branches.json')
    shortcut = {(r['dataset'], r['state'], r['branch']): r for r in old}
    for name in ('filtered_exact_action_sets.py', 'certified_affine_envelope.py',
                 'verify_and_benchmark_gp_envelope.py', 'gp_action_reachability.py'):
        inputs['src/'+name] = digest(ROOT/'src'/name)
    initial_plans = {}
    for meta in plan['mean_states']:
        source = ('results/engineering_optimization_common_continuation_v1/plans/'+meta['state']+'.json'
                  if meta['dataset'] == 'archived_common_mean' else
                  f"results/engineering_optimization_budget_audit_v1/block_{meta['block']}/{meta['state']}_plan.json")
        initial = read(locate(ROOT, source))
        assert not {'trajectories', 'control_curves', 'branch_records', 'calibration'}.intersection(initial)
        initial_plans[meta['dataset'], meta['state']] = initial
    start = time.perf_counter()
    root_seconds = partition_seconds = integral_seconds = 0.
    rows, records, decisions = [], [], []
    for number, name in enumerate(sorted(status['files_sha256']), 1):
        path = gp/'construction'/name
        assert digest(path) == status['files_sha256'][name]
        item = read(path)
        meta = item['metadata']; initial = initial_plans[meta['dataset'], meta['state']]
        cfg = plan['pool_configs'][meta['dataset']]
        begin = time.perf_counter()
        X, y = np.array(initial['X']), np.array(initial['y'])
        center, scale_y = float(y.mean()), float(y.std())
        kernel = (ConstantKernel(1., (.05, 20))*Matern(np.full(19, .2), (.005, 2.), nu=2.5)).clone_with_theta(np.array(initial['theta']))
        A = kernel(X); A[np.diag_indices_from(A)] += cfg['alpha']
        L = np.linalg.cholesky(A)
        alpha = cho_solve((L, True), (y-center)/scale_y)
        pool, seed = future_pool(meta, cfg)
        assert seed == item['pool_seed'] and hashlib.sha256(pool.tobytes()).hexdigest() == item['raw_pool_sha256']
        root_seconds += time.perf_counter()-begin
        group = []
        for branch, rec in item['branches'].items():
            begin = time.perf_counter()
            c = rec['coefficients']; a, b = c['slope'], c['intercept']
            nominal = whole_line((a, b, a, b))
            bands = whole_line(coefficient_bands(a, b, c['slope_error'], c['intercept_error']))
            parts = [(lo, hi, min(active)) for lo, hi, active in cells(nominal)]
            ids = sorted({i for i, _, _ in bands})
            assert {i for _, _, i in parts}.issubset(ids)
            index = {i: j for j, i in enumerate(ids)}
            partition_seconds += time.perf_counter()-begin
            begin = time.perf_counter()
            candidates = pool[np.array(rec['eligible_pool_indices'])]
            test = np.vstack((np.array(initial['actions'][branch]), candidates[ids]))
            B = kernel(test, X)
            means = center+scale_y*(B@alpha)
            C = (kernel(test)-B@cho_solve((L, True), B.T))*scale_y**2
            C = (C+C.T)/2
            mz, sz = float(means[0]), math.sqrt(C[0, 0])
            gamma = C[1:, 0]/sz
            conditional_var = np.diag(C)[1:]-gamma**2
            assert np.all(conditional_var > 0)
            sigma = np.sqrt(conditional_var)
            means = means[1:]
            root_seconds += time.perf_counter()-begin
            local_parts = [(lo, hi, index[i]) for lo, hi, i in parts]
            begin = time.perf_counter()
            computed = {}
            for kind in ('value', 'negative', 'clipped'):
                primary = integrate(local_parts, mz, sz, means, gamma, sigma, meta['initial'], kind, False)
                check = integrate(local_parts, mz, sz, means, gamma, sigma, meta['initial'], kind, True)
                computed[kind] = dict(value=check[0], quad_error_estimate=check[1],
                    crosscheck_absolute_difference=abs(primary[0]-check[0]),
                    integrand_evaluations=primary[2]+check[2],
                    quad_messages=list(dict.fromkeys(primary[3]+check[3])))
            integral_seconds += time.perf_counter()-begin
            # Overlay with nominal boundaries; never sum overlapping R_i as probabilities.
            overlap_mass = coupling_error = 0.
            for lo, hi, active in cells(bands, [v for l, u, _ in parts for v in (l, u)]):
                if len(active) < 2:
                    continue
                point = hi-1 if lo is None else lo+1 if hi is None else (lo+hi)/2
                anchor = next(i for l, u, i in parts
                              if (l is None or l < point) and (u is None or point < u))
                assert anchor in active
                l = -math.inf if lo is None else (float(lo)-mz)/sz
                u = math.inf if hi is None else (float(hi)-mz)/sz
                probability = mass(l, u); overlap_mass += probability
                j = index[anchor]
                for i in active:
                    if i != anchor:
                        k = index[i]
                        coupling_error += abs_affine(means[k]-means[j], gamma[k]-gamma[j], l, u)
                        coupling_error += math.sqrt(2/math.pi)*abs(sigma[k]-sigma[j])*probability
            incumbent = meta['initial']
            tail = (incumbent+abs(mz)+float(np.max(np.abs(means)))+
                    math.sqrt(2/math.pi)*float(np.max(sigma)))*2*float(ndtr(-12.))
            tail += (sz+float(np.max(np.abs(gamma))))*2*phi(12.)
            V, N, P = (computed[k]['value'] for k in ('value', 'negative', 'clipped'))
            numerical_error = max(computed['value']['quad_error_estimate'],
                                  computed['value']['crosscheck_absolute_difference'])+tail
            identity_error = abs((V-N)-P)
            assert 0 <= P <= incumbent*(1+1e-10)
            assert identity_error < max(incumbent*1e-7, 1e-6), (name, branch, identity_error)
            prev = shortcut[meta['dataset'], meta['state'], branch]
            assert math.isclose(mz, prev['root_mean'], rel_tol=1e-12, abs_tol=1e-8)
            assert math.isclose(sz, prev['root_sd'], rel_tol=1e-12, abs_tol=1e-8)
            row = dict(dataset=meta['dataset'], state=meta['state'], branch=branch,
                baseline_branch=meta['baseline'], initial=incumbent,
                value=V, negative_value=N, clipped_gain_diagnostic=P,
                negative_fraction=N/V, identity_residual=identity_error,
                primary_crosscheck_abs=computed['value']['crosscheck_absolute_difference'],
                quad_error_estimate=computed['value']['quad_error_estimate'],
                tail_growth_bound_float=tail, numerical_error_diagnostic=numerical_error,
                overlap_probability_float=overlap_mass,
                band_selector_value_error_float=coupling_error,
                selector_value_lower_float=max(0., V-coupling_error-numerical_error),
                selector_value_upper_float=V+coupling_error+numerical_error,
                nominal_cells=len(parts), whole_line_retained=len(ids),
                root_mean=mz, root_sd=sz, root_negative_probability=float(ndtr(-mz/sz)),
                fixed_pair_value=prev['provisional_fixed_pair_value'],
                previous_eta=prev['provisional_eta'],
                direct_minus_fixed_pair=V-prev['provisional_fixed_pair_value'])
            rows.append(row); group.append(row)
            records.append(dict(dataset=meta['dataset'], state=meta['state'], branch=branch,
                metadata=meta, root_mean=mz, root_sd=sz, indices=ids,
                conditional_means=means.tolist(), conditional_standard_slopes=gamma.tolist(),
                conditional_standard_deviations=sigma.tolist(),
                nominal_cells=[dict(lower=None if l is None else str(l),
                    upper=None if u is None else str(u), index=i) for l, u, i in parts],
                computed=computed))
        rank = sorted(group, key=lambda r: (-r['value'], int(r['branch'].lstrip('b'))))
        clipped_rank = sorted(group, key=lambda r: (-r['clipped_gain_diagnostic'], int(r['branch'].lstrip('b'))))
        chosen = rank[0]
        gap = max(r['selector_value_upper_float'] for r in group)-chosen['selector_value_lower_float']
        rival_upper = max(r['selector_value_upper_float'] for r in group if r is not chosen)
        decisions.append(dict(dataset=meta['dataset'], state=meta['state'],
            baseline_branch=meta['baseline'], value_ranking=[r['branch'] for r in rank],
            chosen_branch=chosen['branch'], clipped_diagnostic_ranking=[r['branch'] for r in clipped_rank],
            ranking_changes_if_negative_component_removed=chosen['branch'] != clipped_rank[0]['branch'],
            selected_negative_fraction=chosen['negative_fraction'], initial=chosen['initial'],
            nominal_top_gap=chosen['value']-rank[1]['value'],
            numeric_and_band_gap_float=gap, delta=chosen['initial']*1e-6,
            floating_delta_condition_met=bool(gap <= chosen['initial']*1e-6),
            floating_unique_ranking_with_band_margin=bool(chosen['selector_value_lower_float'] > rival_upper)))
        print(json.dumps(dict(states_complete=number, branches_complete=len(rows))), flush=True)
    assert len(rows) == 114 and len(decisions) == 43
    save('branches.json', rows)
    save('conditional_models.json', records)
    save('state_decisions.json', decisions)
    with (OUT/'state_table.csv').open('w', newline='') as stream:
        fields = list(decisions[0]); writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader(); writer.writerows(decisions)
    summary = dict(baseline=BASELINE, parent_commit=PARENT, states=43, branches=114,
        metadata_states=60, aliases_retained=17,
        value_type='ordinary high-accuracy numerical reference for nominal frozen selector',
        numerical_or_selection_certificate=False,
        new_root_kernel_constructions=43, new_branch_conditional_systems=114,
        new_physical_evaluations=0, new_bound_queries=0, new_hyperparameter_fits=0,
        new_independent_samples=0, future_response_journals_read=False,
        root_and_covariance_seconds=root_seconds, partition_seconds=partition_seconds,
        quadrature_seconds=integral_seconds, elapsed_seconds=time.perf_counter()-start,
        source_sha256=digest(Path(__file__)), inputs_sha256=inputs,
        runtime_versions={n: importlib.metadata.version(n) for n in ('numpy','scipy','scikit-learn')},
        negative_fraction_min=min(r['negative_fraction'] for r in rows),
        negative_fraction_median=float(np.median([r['negative_fraction'] for r in rows])),
        negative_fraction_max=max(r['negative_fraction'] for r in rows),
        clipped_ranking_changed_states=sum(d['ranking_changes_if_negative_component_removed'] for d in decisions),
        floating_delta_condition_states=sum(d['floating_delta_condition_met'] for d in decisions),
        floating_unique_ranking_states=sum(d['floating_unique_ranking_with_band_margin'] for d in decisions),
        max_quadrature_crosscheck_difference=max(r['primary_crosscheck_abs'] for r in rows),
        max_identity_residual=max(r['identity_residual'] for r in rows),
        max_band_overlap_probability=max(r['overlap_probability_float'] for r in rows),
        max_band_selector_value_error_float=max(r['band_selector_value_error_float'] for r in rows),
        quadratures_with_messages=sum(bool(v['quad_messages']) for r in records for v in r['computed'].values()),
        integrand_evaluations=sum(v['integrand_evaluations'] for r in records for v in r['computed'].values()))
    save('analysis.json', summary)
    frozen = dict(status='decisions frozen before any future-response read by this work',
        source_sha256=digest(Path(__file__)), inputs_sha256=inputs,
        output_sha256={p.name:digest(p) for p in sorted(OUT.iterdir()) if p.is_file()},
        new_physical_evaluations=0, future_response_journals_read=False)
    save('decisions_frozen.json', frozen)
    print(json.dumps({k:v for k,v in summary.items() if k != 'inputs_sha256'}, indent=2))


if __name__ == '__main__':
    with warnings.catch_warnings():
        warnings.simplefilter('error', IntegrationWarning)
        run()
