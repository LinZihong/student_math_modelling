import math
import random
import unittest
import networkx as nx
from model.routing import Arc,walk,latest_departure,fastest
from robust import constrained,latest_network,budget_deadline
from menus import best_menu


class RobustTests(unittest.TestCase):
    def test_menu_no_universal_small_cover(self):
        choice,score=best_menu([1<<i for i in range(5)],3)
        self.assertEqual(score,3)
        self.assertEqual(len(choice),3)

    def test_menu_exact_coverage(self):
        choice,score=best_menu([0b1100,0b0011,0b1010],2)
        self.assertEqual(score,4)
        self.assertEqual(choice,(0,1))
    def test_speed_switch(self):
        self.assertAlmostEqual(Arc('a','b',20,4.1,100,True).exit_time(0),5.9)

    def test_brute_force(self):
        rng=random.Random(20261025)
        self.queries=0
        for case in range(200):
            G=nx.gnp_random_graph(6,.45,seed=case,directed=True)
            adj={}; lookup={}
            for u,v in G.edges():
                wet=rng.uniform(0,60)
                a=Arc(str(u),str(v),rng.uniform(1,80),wet,wet+rng.uniform(5,200),rng.random()<.5)
                adj.setdefault(a.a,[]).append(a);lookup[a.a,a.b]=a
            paths=[]
            for target in [4,5]:
                for p in nx.all_simple_paths(G,0,target):
                    if any(v in [4,5] for v in p[1:-1]): continue
                    paths.append([lookup[str(u),str(v)] for u,v in zip(p,p[1:])])
            D=latest_network(adj,{'4','5'})
            true_D=max((latest_departure(p) for p in paths),default=-math.inf)
            self.assertAlmostEqual(D.get('0',-math.inf),true_D)
            for d in [1,5,15,30,60,120]:
                cost,p,_=constrained(adj,'0',{'4','5'},1,d,D)
                truth=min((walk(q,1)[0] for q in paths if math.isfinite(walk(q,d)[0])),default=math.inf)
                self.assertAlmostEqual(cost,truth)
                if p:
                    self.assertTrue(math.isfinite(walk(p,d)[0]))
                    self.assertAlmostEqual(walk(p,1)[0],cost)
            # Full finite-path optimum, independently enumerated, for a 10% budget.
            base=min((walk(p,1)[0] for p in paths),default=math.inf)
            if math.isfinite(base):
                cap=1+1.1*(base-1)
                truth=max(latest_departure(p) for p in paths if walk(p,1)[0]<=cap)
                lo,hi,p,_=budget_deadline(adj,'0',{'4','5'},1,cap,D)
                self.assertLessEqual(lo,truth+1e-6)
                self.assertGreaterEqual(hi,truth-1e-6)
                self.assertLessEqual(hi-lo,.010001)

    def test_two_clocks_needed(self):
        # A direct fast prefix wins at t0 but loses after wetting; keep both labels.
        aa=[Arc('s','v',30,5,200,False), Arc('s','u',36,100,200,True),
            Arc('u','v',36,100,200,True),Arc('v','t',20,36,36,True)]
        adj={}
        for a in aa:adj.setdefault(a.a,[]).append(a)
        # Prefix labels at v: (15,40) and (18,28) for t0=0,d=10.
        cost,path,stats=constrained(adj,'s',{'t'},0,10)
        self.assertEqual(cost,23)
        self.assertEqual(path[0].b,'u')
        for d in (0,5,10,20):
            cost,path,_=constrained(adj,'s',{'t'},0,d)
            ps=[[aa[0],aa[3]],[aa[1],aa[2],aa[3]]]
            best=min((walk(p,0)[0] for p in ps if math.isfinite(walk(p,d)[0])),default=math.inf)
            self.assertEqual(cost,best)


if __name__=='__main__': unittest.main()
