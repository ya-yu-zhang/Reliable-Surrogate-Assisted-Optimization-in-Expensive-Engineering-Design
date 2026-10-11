"""Authored, dimensionless finite-volume conduction model; not an EngiBench case.

Unit square, zero-temperature boundary on all four sides, total heat input one.
Twelve equal-area material zones, mean density 0.35, k = 1 + 19*rho**3.
Face conductance uses the harmonic mean; boundary half-cell distances are exact.
Objective is thermal compliance q.T @ T, not peak temperature or a safety metric.
"""
from __future__ import annotations
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve


def densities(x):
    logits = 6 * np.asarray(x, dtype=float) - 3
    if logits.shape != (12,) or np.any((x < 0) | (x > 1)):
        raise ValueError('Expected twelve unit-box parameters')
    low, high = -20., 20.
    for _ in range(70):
        offset = (low + high) / 2
        rho = 1 / (1 + np.exp(-(logits + offset)))
        if rho.mean() < .35: low = offset
        else: high = offset
    return 1 / (1 + np.exp(-(logits + (low + high) / 2)))


def matrix(k):
    n = len(k)
    if k.shape != (n,n) or np.any(k <= 0): raise ValueError('Positive square field required')
    ids = np.arange(n*n).reshape(n,n)
    diagonal = np.zeros((n,n)); rows=[]; cols=[]; values=[]
    for a,b,ka,kb in [(ids[:-1],ids[1:],k[:-1],k[1:]),
                       (ids[:,:-1],ids[:,1:],k[:,:-1],k[:,1:])]:
        g = 2*ka*kb/(ka+kb)
        np.add.at(diagonal.ravel(),a.ravel(),g.ravel())
        np.add.at(diagonal.ravel(),b.ravel(),g.ravel())
        rows.extend([a.ravel(),b.ravel()]); cols.extend([b.ravel(),a.ravel()])
        values.extend([-g.ravel(),-g.ravel()])
    diagonal[0] += 2*k[0]; diagonal[-1] += 2*k[-1]
    diagonal[:,0] += 2*k[:,0]; diagonal[:,-1] += 2*k[:,-1]
    rows.append(ids.ravel()); cols.append(ids.ravel()); values.append(diagonal.ravel())
    return coo_matrix((np.concatenate(values),(np.concatenate(rows),np.concatenate(cols))),
                      shape=(n*n,n*n)).tocsr()


class ThermalDesign:
    def __init__(self, n=24, condition='central_source'):
        if n % 12: raise ValueError('Mesh must divide the 3-by-4 zone boundaries')
        self.n, self.condition = n, condition
        yy,xx = np.meshgrid((np.arange(n)+.5)/n,(np.arange(n)+.5)/n,indexing='ij')
        centers={'central_source':(.5,.5), 'offset_source':(.75,.25)}
        cx,cy=centers[condition]
        q=np.exp(-((xx-cx)**2+(yy-cy)**2)/(2*.08**2))
        self.q=(q/q.sum()).ravel()
    def field(self,x):
        rho=densities(np.asarray(x)).reshape(3,4)
        return 1+19*np.repeat(np.repeat(rho,self.n//3,axis=0),self.n//4,axis=1)**3
    def solve(self,x):
        k=self.field(x); A=matrix(k); T=spsolve(A,self.q)
        residual=float(np.linalg.norm(A@T-self.q)/np.linalg.norm(self.q))
        temp=T.reshape(self.n,self.n)
        flux=float(2*(np.sum(k[0]*temp[0])+np.sum(k[-1]*temp[-1])+
                      np.sum(k[:,0]*temp[:,0])+np.sum(k[:,-1]*temp[:,-1])))
        value=float(self.q@T)
        if not np.isfinite(value) or value <= 0 or residual > 1e-9 or abs(flux-1)>1e-9:
            raise FloatingPointError('Invalid conduction solve')
        return value, {'relative_residual':residual,'boundary_heat_flux':flux,
                       'mean_density':float(densities(np.asarray(x)).mean()),
                       'minimum_temperature':float(T.min())}
    def __call__(self,x): return self.solve(x)[0]
