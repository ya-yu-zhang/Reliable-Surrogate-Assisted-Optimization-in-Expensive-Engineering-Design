"""Enclose the explicit fixed-binary log-GP; no fitting or objective calls."""
import math
import numpy as np
from scipy.linalg import cho_solve, solve_triangular
from .rollout_v2_intervals import I


def up(x):
    return np.nextafter(x, np.inf)


def gamma(n):
    return math.nextafter(n/(2**53-n), math.inf)


def dot(a, b):
    """Binary dot plus an outward absolute error bound, including underflow."""
    n = a.shape[-1]
    g = gamma(4*n+32)
    denominator = math.nextafter(1-g, -math.inf)
    value = a @ b
    absolute = up((np.abs(a) @ np.abs(b))/denominator + 1e-300)
    error = up(up(g*absolute)+1e-300)
    if not np.isfinite(value).all() or not np.isfinite(error).all():
        raise ArithmeticError("Nonfinite reduction")
    return value, error


def norm_bound(a, axis=1):
    n = a.shape[axis]
    return float(np.max(up(np.sum(np.abs(a), axis=axis)/
                           math.nextafter(1-gamma(4*n+32), -math.inf)+1e-300)))


def inverse_bounds(a, approximate=None):
    n = len(a)
    if approximate is None:
        approximate = np.linalg.inv(a)
    value, error = dot(a, approximate)
    residual = up(np.abs(np.eye(n)-value)+error+
                  up(gamma(4*n+32)*(np.eye(n)+np.abs(value)))+1e-300)
    ri, r1 = norm_bound(residual), norm_bound(residual, 0)
    if max(ri, r1) >= .5:
        raise ArithmeticError("Inverse residual gate failed")
    ni = (I(norm_bound(approximate))/(1-I(ri))).hi
    n1 = (I(norm_bound(approximate, 0))/(1-I(r1))).hi
    return ni, n1, max(ri, r1)


def spd_bound(center, radii=None):
    if not np.array_equal(center, center.T):
        raise ValueError("Nonsymmetric matrix")
    L = np.linalg.cholesky(center)
    Linv = solve_triangular(L, np.eye(len(L)), lower=True)
    ni, n1, _ = inverse_bounds(L, Linv)
    product, error = dot(L, L.T)
    absolute = up(np.abs(center-product)+error+
                  up(gamma(4*len(L)+32)*(np.abs(center)+np.abs(product)))+1e-300)
    if radii is not None:
        absolute = up(absolute+radii)
    perturbation = (I(ni)*n1*norm_bound(absolute)).hi
    if perturbation >= 1:
        raise ArithmeticError("SPD perturbation gate failed")
    return perturbation


def enclose(A, B, K, y):
    A, B, K, y = map(lambda x:np.asarray(x,dtype=float), (A,B,K,y))
    if not np.isfinite(y).all() or np.any(y <= 0) or not np.array_equal(A,A.T):
        raise ValueError("Invalid fixed model input")
    logs = np.log(y)
    c0, s0 = float(logs.mean()), float(logs.std())
    if not s0 > 0:
        raise ArithmeticError("Zero target scale")
    targets = [I(float(z)).log()-c0 for z in y]
    mid = np.array([r.mid() for r in targets])
    radius = np.array([max((I(x)-r).hi,(r-I(x)).hi)
                       for x,r in zip(mid,targets)])
    L = np.linalg.cholesky(A)
    P = cho_solve((L,True),np.eye(len(A)))
    invnorm, _, residual = inverse_bounds(A,P)
    train_spd = spd_bound(A)
    W = cho_solve((L,True),B.T).T
    prod, perr = dot(A,W.T)
    rabs = up(np.abs(B.T-prod)+perr+
              up(gamma(4*len(A)+32)*(np.abs(B.T)+np.abs(prod)))+1e-300)
    weight_errors = up(invnorm*np.max(rabs,axis=0))
    meanprod, meanround = dot(W,mid[:,None])
    means = []
    total_target = sum((I(max(abs(r.lo),abs(r.hi))) for r in targets),I(0))
    for i in range(len(B)):
        radius_part = sum((I(abs(w))*float(r) for w,r in zip(W[i],radius)),I(0))
        error = I(float(weight_errors[i]))*total_target+radius_part+float(meanround[i,0])
        means.append(I(c0)+I(float(meanprod[i,0]))+I(-error.hi,error.hi))
    q, qerr = dot(W,B.T)
    bnorm = [sum((I(abs(float(v))) for v in row),I(0)) for row in B]
    covariance = [[None for _ in B] for _ in B]
    for i in range(len(B)):
        for j in range(len(B)):
            error = I(float(weight_errors[i]))*bnorm[j]+float(qerr[i,j])
            covariance[i][j] = (I(float(K[i,j]))-I(float(q[i,j]))
                                +I(-error.hi,error.hi))*I(s0).square()
    for i in range(len(B)):
        for j in range(i):
            covariance[i][j] = covariance[j][i] = covariance[i][j].intersect(covariance[j][i])
    center = np.array([[z.mid() for z in row] for row in covariance])
    radii = np.array([[max((I(center[i,j])-z).hi,(z-I(center[i,j])).hi)
                       for j,z in enumerate(row)] for i,row in enumerate(covariance)])
    posterior_spd = spd_bound(center,radii)
    return means,covariance,dict(center=c0,scale=s0,
        inverse_residual_upper=residual, training_SPD_perturbation=train_spd,
        posterior_SPD_perturbation=posterior_spd,
        maximum_mean_width=max(z.width() for z in means),
        maximum_covariance_width=max(z.width() for row in covariance for z in row))
