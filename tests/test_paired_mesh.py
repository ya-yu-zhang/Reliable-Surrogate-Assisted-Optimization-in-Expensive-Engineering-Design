import unittest
import numpy as np
from src.engineering_optimization_paired_mesh import overlap_weights,transfer,normalized_geometry

class PairedMeshTests(unittest.TestCase):
    def test_conservative_transfer_preserves_mean_and_range(self):
        base=np.random.default_rng(11).uniform(.01,.99,(50,100))
        for shape in [(75,150),(100,200)]:
            refined=transfer(base,shape)
            self.assertAlmostEqual(float(refined.mean()),float(base.mean()),12)
            self.assertGreaterEqual(float(refined.min()),float(base.min())-1e-12)
            self.assertLessEqual(float(refined.max()),float(base.max())+1e-12)
    def test_coarse_transfer_exact_and_double_resolution_replication(self):
        a=np.arange(12,dtype=float).reshape(3,4)/12
        self.assertTrue(np.array_equal(transfer(a,a.shape),a))
        self.assertTrue(np.allclose(transfer(a,(6,8)),np.repeat(np.repeat(a,2,0),2,1),rtol=0,atol=1e-14))
    def test_overlap_weight_rows_and_global_integral(self):
        for n,m in [(75,50),(150,100),(100,50)]:
            w=overlap_weights(n,m)
            self.assertTrue(np.allclose(w.sum(1),1.,rtol=0,atol=1e-13))
            self.assertTrue(np.allclose(w.sum(0)/n,1/m,rtol=0,atol=1e-13))
    def test_dimensionless_load_support_and_aspect_invariant(self):
        for nx,ny in [(100,50),(150,75),(200,100)]:
            g=normalized_geometry(nx,ny)
            self.assertEqual(g['aspect_ratio'],2.)
            self.assertEqual(g['force_position'],[0.,0.])
            self.assertEqual(g['vertical_support_position'],[1.,1.])
            self.assertEqual(g['total_vertical_force'],-1.)
if __name__=='__main__':unittest.main()
