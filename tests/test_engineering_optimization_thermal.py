import unittest
import numpy as np
from scipy.sparse.linalg import spsolve
from src.engineering_thermal_adapter import densities, matrix
from src.engineering_optimization_thermal import choose_gate

class ThermalChecks(unittest.TestCase):
    def test_volume_and_bounds(self):
        for x in [np.zeros(12),np.ones(12),np.linspace(0,1,12)]:
            rho=densities(x)
            self.assertAlmostEqual(float(rho.mean()),.35,places=14)
            self.assertTrue(np.all((rho>0)&(rho<1)))

    def test_manufactured_solution_second_order(self):
        errors=[]
        for n in [12,24,48]:
            z=(np.arange(n)+.5)/n
            exact=np.outer(np.sin(np.pi*z),np.sin(np.pi*z))
            rhs=(2*np.pi**2*exact/n**2).ravel()
            A=matrix(np.ones((n,n)))
            computed=spsolve(A,rhs)
            errors.append(float(np.linalg.norm(computed-exact.ravel())/np.linalg.norm(exact)))
            self.assertLess(float(np.linalg.norm(A@computed-rhs)/np.linalg.norm(rhs)),1e-11)
        self.assertGreater(errors[0]/errors[1],3.9)
        self.assertGreater(errors[1]/errors[2],3.9)
        self.assertLess(errors[-1],.0004)

    def test_symmetry_positive_energy_and_heat_conservation(self):
        k=1+np.arange(144).reshape(12,12)/144
        A=matrix(k)
        self.assertEqual((A-A.T).nnz,0)
        self.assertGreater(float(np.linalg.eigvalsh(A.toarray()).min()),0)
        q=np.full(144,1/144); T=spsolve(A,q).reshape(12,12)
        flux=2*(np.sum(k[0]*T[0])+np.sum(k[-1]*T[-1])+
                np.sum(k[:,0]*T[:,0])+np.sum(k[:,-1]*T[:,-1]))
        self.assertAlmostEqual(float(flux),1,places=12)

    def test_gate_rejects_late_only_advantage(self):
        cfg={'policies':['mean','ei','lcb'],'gate_checkpoints':[4,6,8],'promotion_margin':.02}
        mean=[10.]*9; ei=[10.]*8+[8.]; lcb=[11.]*9
        selected,best,_=choose_gate({'mean':mean,'ei':ei,'lcb':lcb},cfg)
        self.assertEqual((selected,best),('mean','ei'))
        ei=[9.]*9
        selected,best,_=choose_gate({'mean':mean,'ei':ei,'lcb':lcb},cfg)
        self.assertEqual((selected,best),('ei','ei'))

if __name__=='__main__': unittest.main()
