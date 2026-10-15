"""Necessary correctness tests; synthetic fixtures, no engineering evaluations."""
import copy
import math
import unittest
from fractions import Fraction as F
import numpy as np
from scipy.integrate import quad
from scipy.special import ndtr
from src.rollout_v2_intervals import I,cdf,fraction_interval
from src.rollout_v2_posterior import enclose,inverse_bounds
from src.rollout_v2_solver import (conditional_reward,Integrator,dominance,
    check_dominance,solve,check)


class RolloutV2(unittest.TestCase):
    def test_directed_arithmetic(self):
        for a,b in [(1.,3.),(-7.,3.),(1e-120,1e120),(.1,-.3)]:
            for got,want in [(I(a)+b,F(a)+F(b)),(I(a)*b,F(a)*F(b)),(I(a)/b,F(a)/F(b))]:
                self.assertLessEqual(F(got.lo),want)
                self.assertGreaterEqual(F(got.hi),want)
        for f in [F(1,3),-F(2**250+7,2**199+3)]:
            r=fraction_interval(f)
            self.assertLessEqual(F(r.lo),f);self.assertGreaterEqual(F(r.hi),f)

    def test_normal_identity(self):
        for x in [-5.,-1.,0.,1.,5.]:
            v=cdf(x)+cdf(-x)
            self.assertLessEqual(v.lo,1);self.assertGreaterEqual(v.hi,1)
        self.assertEqual(cdf(0).pair(),[.5,.5])

    def model(self,second=math.log(3)):
        return dict(initial=10.,first_mean=I(math.log(5)).pair(),first_sd=I(.15).pair(),
                    next={"0":dict(mean=I(second).pair(),gamma=I(.03).pair(),sd=I(.2).pair())})

    def test_conditional_against_independent_integral(self):
        m=self.model()
        for x in [-3.,0.,3.]:
            h=min(10,math.exp(m["first_mean"][0]+.15*x))
            mu=m["next"]["0"]["mean"][0]+.03*x
            val,err=quad(lambda w:(10-min(h,math.exp(mu+.2*w)))*math.exp(-w*w/2)/math.sqrt(2*math.pi),
                         -12,12,epsabs=1e-11,points=[(math.log(h)-mu)/.2])
            v=conditional_reward(m,0,x)
            self.assertLessEqual(v.lo,val+max(err,1e-10))
            self.assertGreaterEqual(v.hi,val-max(err,1e-10))

    def test_integration_cover_contains_quadrature(self):
        m=self.model();q=Integrator(m,{0:(F(0),None)},0)
        for _ in range(100):q.refine()
        def f(x):
            h=min(10,math.exp(m["first_mean"][0]+.15*x))
            mu=m["next"]["0"]["mean"][0]+.03*x
            k=(math.log(h)-mu)/.2
            return (10-h*ndtr(-k)-math.exp(mu+.02)*ndtr(k-.2))*math.exp(-x*x/2)/math.sqrt(2*math.pi)
        expected,error=quad(f,-8,8,epsabs=1e-10)
        value=q.value()
        self.assertLessEqual(value.lo,expected+error)
        self.assertGreaterEqual(value.hi,expected-error)
        self.assertEqual(q.certificate()["leaves"][0]["low"],-8.)

    def test_tie_and_exact_domain(self):
        flat=([0.,0.],[1.,1.],[0.,0.],[1.,1.])
        self.assertIsNone(dominance(flat,1))
        self.assertFalse(check_dominance(flat,1,(F(0),None)))
        crossing=([0.,1.],[1.,0.],[0.,1.],[1.,0.])
        self.assertEqual(dominance(crossing,1),(F(0),F(1)))
        self.assertTrue(check_dominance(crossing,1,(F(0),F(1))))
        self.assertFalse(check_dominance(crossing,1,(F(0),F(2))))

    def test_selection_and_corrupt_record_rejection(self):
        models={"0":self.model(math.log(2)),"1":self.model(math.log(6))}
        band=([0.,0.],[0.,1.],[0.,0.],[0.,1.])
        bands={b:band for b in models};legacy={b:{0:(F(0),None)} for b in models};reference={b:0 for b in models}
        for method in ["direct","local"]:
            r=solve(models,bands,legacy,reference,method)
            self.assertEqual(r["status"],"accepted")
            self.assertEqual(r["selected"],"0")
            self.assertTrue(check(r,models,bands,legacy,reference)["accepted"])
            bad=copy.deepcopy(r);bad["certificates"].pop("1")
            with self.assertRaises(ArithmeticError):check(bad,models,bands,legacy,reference)
            bad=copy.deepcopy(r);bad["certificates"]["0"]["leaves"][0]["low"]=-7.
            with self.assertRaises(ArithmeticError):check(bad,models,bands,legacy,reference)
            bad=copy.deepcopy(r);bad["certificates"]["0"]["leaves"][0]["interval"]=[0.,0.]
            with self.assertRaises(ArithmeticError):check(bad,models,bands,legacy,reference)
        no=solve(models,bands,legacy,reference,"direct",max_refinements=0)
        self.assertIn(no["status"],["accepted","unresolved"])

    def test_posterior_against_exact_two_by_two(self):
        A=np.array([[2.,.25],[.25,1.]])
        B=np.array([[.3,.2],[.1,.7]]);K=np.array([[2.,.1],[.1,2.]])
        y=np.array([2.,3.]);means,cov,record=enclose(A,B,K,y)
        det=F(2)-F(.25)**2
        inv=[[F(1)/det,-F(.25)/det],[-F(.25)/det,F(2)/det]]
        s=F(record["scale"])**2;c=record["center"]
        for i in range(2):
            exact_weights=[sum(F(float(B[i,k]))*inv[k][j] for k in range(2)) for j in range(2)]
            oracle=I(c)+sum((fraction_interval(w)*(I(float(z)).log()-c)
                            for w,z in zip(exact_weights,y)),I(0))
            self.assertLessEqual(means[i].lo,oracle.lo)
            self.assertGreaterEqual(means[i].hi,oracle.hi)
            for j in range(2):
                exact=s*(F(float(K[i,j]))-sum(exact_weights[k]*F(float(B[j,k])) for k in range(2)))
                self.assertLessEqual(F(cov[i][j].lo),exact)
                self.assertGreaterEqual(F(cov[i][j].hi),exact)
        with self.assertRaises(ArithmeticError):inverse_bounds(A,np.zeros_like(A))
        with self.assertRaises(np.linalg.LinAlgError):enclose(np.array([[1.,2.],[2.,1.]]),B,K,y)


if __name__=="__main__":
    unittest.main()
