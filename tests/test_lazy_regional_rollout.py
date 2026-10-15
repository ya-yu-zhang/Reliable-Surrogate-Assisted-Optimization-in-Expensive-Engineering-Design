import copy,math,unittest
from src.lazy_regional_rollout import solve,check,unknown_value
from src.rollout_v2_intervals import I


class LazyRegionTests(unittest.TestCase):
    def fixture(self):
        models={b:dict(initial=10.,first_mean=[math.log(5)]*2,first_sd=[.15]*2,next={}) for b in ['0','1']}
        band=([0.,0.],[0.,1.],[0.,0.],[0.,1.])
        bands={b:band for b in models};nominal={b:([0,0],[0,1]) for b in models}
        cache={}
        def oracle(b,j):
            self.assertEqual(j,0)
            q=dict(mean=[math.log(2 if b=='0' else 6)]*2,gamma=[.02]*2,sd=[.2]*2)
            cache[b,str(j)]=dict(conditional=q)
            return q
        return models,bands,nominal,oracle,cache

    def test_both_routes_select_without_complete_projection(self):
        for method in ['uniform','regional']:
            m,b,n,o,p=self.fixture();r=solve(m,b,n,o,method)
            self.assertEqual(r['status'],'accepted');self.assertEqual(r['selected'],'0')
            self.assertEqual(r['counters']['complete_projections'],0)
            self.assertTrue(check(r,m,b,p)['accepted'])
            self.assertLessEqual(len(p),2)

    def test_positive_range_restricts_unknown_reward(self):
        m,*_=self.fixture()
        a=unknown_value(m['0'],-1,1,'regional');b=unknown_value(m['0'],-1,1,'uniform')
        self.assertGreater(a.lo,b.lo);self.assertEqual(a.hi,b.hi)

    def test_resource_exhaustion_remains_unresolved(self):
        m,b,n,o,p=self.fixture();r=solve(m,b,n,o,'regional',max_operations=0)
        self.assertEqual(r['status'],'unresolved');self.assertIsNone(r['selected'])
        self.assertEqual(len(p),0)

    def test_reader_rejects_changed_cell_and_missing_proof(self):
        m,b,n,o,p=self.fixture();r=solve(m,b,n,o,'regional')
        bad=copy.deepcopy(r);bad['cells']['0'][0]['low']=-7
        with self.assertRaises(ArithmeticError):check(bad,m,b,p)
        bad=copy.deepcopy(r)
        branch=next(k for k,v in bad['cells'].items() if any(c['action'] is not None for c in v))
        bad['domains'][branch]={}
        with self.assertRaises(ArithmeticError):check(bad,m,b,p)


if __name__=='__main__':unittest.main()
