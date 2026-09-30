"""Budget-blind PEM-SAEA prototype. No objective or diagnostic labels here."""
from dataclasses import dataclass, asdict
import numpy as np
from scipy.linalg import cho_factor, cho_solve
from scipy.spatial.distance import cdist
from scipy.stats import qmc


@dataclass(frozen=True)
class Settings:
    kernel_scale: float = 0.25
    ridge: float = 1e-6
    max_train: int = 256
    elite_train: int = 128
    parents: int = 64
    candidates: int = 256
    F: float = 0.5
    CR: float = 0.9
    pbest: float = 0.2
    residual_window: int = 100
    half_life: float = 25.0
    spatial_k: int = 20
    min_support: float = 20.0
    monitor_window: int = 30
    level: float = 0.9
    duplicate_tol: float = 1e-10
    tau_factor: float = 1e-6


def seed_stream(seed, tag, *parts):
    return np.random.default_rng(np.random.SeedSequence([int(seed), int(tag), *map(int, parts)]))


def init_design(d, seed):
    # Depends on D and seed, never on budget or method.
    return qmc.LatinHypercube(d, seed=seed_stream(seed, 11)).random(2*d+20)


def distances(x, y):
    return cdist(np.atleast_2d(x), np.atleast_2d(y)) / np.sqrt(np.shape(y)[1])


def subset_indices(x, y, cap=256, elite=128):
    n = len(y)
    if n <= cap:
        return np.arange(n)
    chosen = list(np.argsort(y, kind='stable')[:min(elite, cap)])
    mind = distances(x, x[chosen]).min(axis=1)
    mind[chosen] = -np.inf
    while len(chosen) < cap:
        j = int(np.argmax(mind))
        chosen.append(j)
        mind = np.minimum(mind, distances(x, x[j:j+1]).ravel())
        mind[chosen] = -np.inf
    return np.array(chosen)


class GaussianRBF:
    def __init__(self, settings=Settings()):
        self.settings = settings

    def fit(self, x, y):
        cfg = self.settings
        ix = subset_indices(x, y, cfg.max_train, cfg.elite_train)
        self.indices, self.x = ix, x[ix]
        self.mean = float(np.mean(y[ix]))
        self.scale = float(np.std(y[ix])) or 1.0
        k = np.exp(-distances(self.x, self.x)**2 / (2*cfg.kernel_scale**2))
        k.flat[::len(k)+1] += cfg.ridge
        self.coef = cho_solve(cho_factor(k, lower=True, check_finite=False),
                              (y[ix]-self.mean)/self.scale, check_finite=False)
        return self

    def predict(self, x):
        k = np.exp(-distances(x, self.x)**2 / (2*self.settings.kernel_scale**2))
        return self.mean + self.scale*(k @ self.coef)


def reflect(x):
    v = np.mod(x, 2.0)
    return np.where(v <= 1, v, 2-v)


def make_candidates(x, y, seed, evaluation, cfg=Settings()):
    rng = seed_stream(seed, 21, evaluation)
    ni = min(len(y), cfg.parents)
    ix = subset_indices(x, y, ni, ni//2)
    pool, py = x[ix], y[ix]
    rank = np.argsort(py, kind='stable')
    trials = []
    for _ in range(cfg.candidates//2):
        i = int(rng.integers(ni))
        pb = int(rng.choice(rank[:max(2, int(np.ceil(cfg.pbest*ni)))]))
        available = np.array([j for j in range(ni) if j not in {i, pb}])
        r1, r2 = rng.choice(available, 2, replace=False)
        mutant = pool[i] + cfg.F*(pool[pb]-pool[i]) + cfg.F*(pool[r1]-pool[r2])
        mask = rng.random(x.shape[1]) < cfg.CR
        mask[rng.integers(x.shape[1])] = True
        trials.append(reflect(np.where(mask, mutant, pool[i])))
    sobol = qmc.Sobol(x.shape[1], scramble=True, seed=seed_stream(seed, 22, evaluation))
    trials = list(np.array(trials)) + list(sobol.random_base2(7))
    accepted = []
    for point in trials:
        if distances(point, x).min() <= cfg.duplicate_tol:
            continue
        if accepted and distances(point, np.array(accepted)).min() <= cfg.duplicate_tol:
            continue
        accepted.append(point)
    # Refill with a separate Sobol stream; avoid warnings from unbalanced batches.
    refill = qmc.Sobol(x.shape[1], scramble=True, seed=seed_stream(seed, 23, evaluation))
    while len(accepted) < cfg.candidates:
        for point in refill.random_base2(8) if not refill.num_generated else refill.random(256):
            if distances(point, x).min() > cfg.duplicate_tol and distances(point, np.array(accepted)).min() > cfg.duplicate_tol:
                accepted.append(point)
                if len(accepted) == cfg.candidates:
                    break
    return np.array(accepted[:cfg.candidates])


def weighted_quantile(r, w, level=0.9):
    r, w = np.asarray(r), np.asarray(w)
    order = np.argsort(r, kind='stable')
    cw = np.cumsum(w[order], axis=-1)
    j = np.searchsorted(cw, level*cw[-1], side='left')
    return float(r[order[min(j, len(r)-1)]])


def bounds(mu, scale, points, residuals, evaluation, variant='T', cfg=Settings()):
    """Residual tuples: (evaluation, x, prequential residual). Returns empirical bounds."""
    m = len(points)
    if not residuals:
        return dict(H=mu.copy(), q=np.zeros(m), neff=np.zeros(m), used=np.full(m, 'G'),
                    support=np.zeros(m, dtype=bool), weighted_distance=np.full(m, np.nan))
    history = residuals[-cfg.residual_window:]
    times = np.array([h[0] for h in history])
    xr = np.array([h[1] for h in history])
    r = np.array([h[2] for h in history])
    ds = distances(points, xr)
    tw = np.exp2(-(evaluation-times)/cfg.half_life)
    tw /= tw.max()
    tq = max(0.0, weighted_quantile(r, tw, cfg.level))
    gq = max(0.0, weighted_quantile(r, np.ones(len(r)), cfg.level))
    tn = tw.sum()**2 / np.dot(tw, tw)
    sw = None
    if len(r) >= cfg.spatial_k:
        h = np.partition(ds, cfg.spatial_k-1, axis=1)[:, cfg.spatial_k-1]
        sw = np.exp(-ds**2/(2*np.maximum(h[:, None], 1e-15)**2))
    qs, ns, used, wd = [], [], [], []
    for j in range(m):
        name = variant
        if name in {'S', 'ST'} and sw is None:
            name = 'T' if name == 'ST' else 'G'
        w = {'G': np.ones(len(r)), 'T': tw}.get(name)
        if w is None:
            w = sw[j] * (tw if name == 'ST' else 1)
        n = w.sum()**2 / np.dot(w, w)
        if n < cfg.min_support-1e-10:
            name = 'T' if name == 'ST' else 'G'
            if name == 'T' and tn < cfg.min_support-1e-10:
                name = 'G'
            w = tw if name == 'T' else np.ones(len(r))
            n = w.sum()**2 / np.dot(w, w)
        q = tq if name == 'T' else (gq if name == 'G' else max(0.0, weighted_quantile(r, w, cfg.level)))
        qs.append(q); ns.append(n); used.append(name)
        wd.append(float(np.dot(w, ds[j])/w.sum()))
    q = np.array(qs)
    return dict(H=mu+scale*q, q=q, neff=np.array(ns), used=np.array(used),
                support=np.array(ns) >= cfg.min_support-1e-10, weighted_distance=np.array(wd))


def management(monitors, stagnation, mode='full', fixed=0.3, cfg=Settings()):
    window = monitors[-cfg.monitor_window:]
    e = float(np.mean([v[0] for v in window])) if window else 0.0
    v = float(np.mean([v[1] for v in window])) if window else 0.0
    a = max(float(np.clip((e-0.1)/0.2, 0, 1)), float(np.clip((v-1)/2, 0, 1)))
    z = min(stagnation/20.0, 1.0)
    if mode == 'error':
        a = float(np.clip((e-0.1)/0.2, 0, 1)); z = 0.0
    elif mode == 'stagnation':
        a = 0.0
    p = float(np.clip(0.1+0.4*a+0.3*z, 0.1, 0.8))
    if len(monitors) < cfg.min_support:
        p = 0.5
    if mode == 'fixed':
        p = fixed
    elif mode == 'greedy':
        p = 0.0
    elif mode == 'random':
        p = 1.0
    return dict(p=p, a=a, z=z, mean_failure=e, mean_margin=v, monitoring_ready=len(monitors) >= cfg.min_support)


def choose(points, x, mu, bound, best, scale, state, seed, evaluation, use_upper=True, cfg=Settings()):
    rng = seed_stream(seed, 31, evaluation)
    u = float(rng.random())
    if state.get('random_candidate', False):
        k = int(rng.integers(len(points))); mode = 'pool_random'
    elif u < state['p']:
        k = int(np.argmax(distances(points, x).min(axis=1)))
        mode = 'explore'
    elif use_upper and state['monitoring_ready'] and state['a'] < 0.5 and np.any(bound['support'] & (bound['H'] < best-cfg.tau_factor*scale)):
        eligible = np.where(bound['support'], bound['H'], np.inf)
        k = int(np.argmin(eligible)); mode = 'upper'
    else:
        k = int(np.argmin(mu)); mode = 'mean'
    return k, mode, u, rng.bit_generator.state


METHODS = {
    'greedy': ('T','greedy',False,0.0),
    **{f'fixed{int(p*10):02}': ('T','fixed',False,p) for p in [0.1,0.3,0.5,0.8]},
    'T_fixed': ('T','fixed',True,0.3),
    'PEM_T': ('T','full',True,0.3),
    'PEM_G': ('G','full',True,0.3),
    'PEM_S': ('S','full',True,0.3),
    'PEM_ST': ('ST','full',True,0.3),
    'no_upper': ('T','full',False,0.3),
    'error_only': ('T','error',True,0.3),
    'stagnation_only': ('T','stagnation',False,0.3),
    'explore_only': ('T','random',False,1.0),
    'pool_random': ('T','greedy',False,0.0),
}
