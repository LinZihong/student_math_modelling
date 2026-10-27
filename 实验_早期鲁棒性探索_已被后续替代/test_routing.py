"""Independent small-graph enumeration, analytic crossing and counterexample tests."""
import math
import random
import unittest
from routing import Arc, earliest, latest_departures, path_deadline, walk


class RoutingTests(unittest.TestCase):
    def test_crosses_wetting_event(self):
        a = Arc('s', 't', 100, 10, 100, 1)
        self.assertEqual(a.arrival(0), 70)
        self.assertEqual(a.latest(70), 0)
        # Four dry seconds cover 16 m; the remaining 4 m take two seconds.
        a = Arc('s', 't', 20, 4, 100, 2)
        self.assertEqual(a.arrival(0), 6)

    def test_fastest_is_not_most_delay_tolerant(self):
        arcs = [Arc('s','t',40,0,30,2), Arc('s','a',30,0,200,1),
                Arc('a','t',30,0,200,1)]
        arrival, path = earliest(arcs,'s',{'t'},0)
        labels, _ = latest_departures(arcs,{'t'})
        self.assertEqual(arrival,20)
        self.assertEqual(path_deadline(path),10)
        self.assertEqual(labels['s'],140)

    def test_wetting_inside_last_segment(self):
        # Segment-start speed freezes 4 m/s across t=4.1 and returns 5.75;
        # exact integration gives 5.8. This error can flip closure feasibility.
        a = Arc('s','t',20,4.1,5.77,2)
        self.assertEqual(a.arrival(0),math.inf)

    def test_split_at_worker_preserves_traversal(self):
        a = Arc('s','t',100,10,100,1)
        parts=[Arc('s','m',37,10,100,1),Arc('m','t',63,10,100,1)]
        for t in [0,5,10,40,80]:
            self.assertEqual(a.arrival(t),walk(parts,t))

    def test_earlier_flood_is_never_better(self):
        for wet in [0,3,10,100]:
            a=Arc('s','t',20,wet,wet+30,2)
            worse=Arc('s','t',20,wet/1.5,(wet+30)/1.5,2)
            for t in range(100): self.assertGreaterEqual(worse.arrival(t),a.arrival(t))

    def test_random_graphs_against_enumeration(self):
        rng = random.Random(20261024)
        for _ in range(100):
            arcs = []
            for u in range(5):
                for v in range(5):
                    if u != v and rng.random() < .4:
                        wet = rng.uniform(0,40)
                        block = rng.choice([math.inf, wet+rng.uniform(1,100)])
                        arcs.append(Arc(str(u),str(v),rng.uniform(1,60),wet,block,rng.choice([1,2])))
            paths = []
            def visit(u, seen, path):
                if u == '4':
                    paths.append(path)
                    return
                for a in arcs:
                    if a.u == u and a.v not in seen:
                        visit(a.v,seen|{a.v},path+[a])
            visit('0',{'0'},[])
            # Independent bisection of forward feasibility, no reverse formula.
            for path in paths:
                if math.isinf(walk(path, -1000)):
                    continue
                lo, hi = -1000., 1000.
                if math.isfinite(walk(path, hi)):
                    self.assertEqual(path_deadline(path),math.inf)
                    continue
                for _ in range(70):
                    mid = (lo+hi)/2
                    if math.isfinite(walk(path,mid)): lo=mid
                    else: hi=mid
                self.assertAlmostEqual(lo,path_deadline(path),places=6)
            for t0 in (0,10,30,60):
                actual,_ = earliest(arcs,'0',{'4'},t0)
                expected = min((walk(p,t0) for p in paths),default=math.inf)
                self.assertEqual(actual,expected)
            labels,_ = latest_departures(arcs,{'4'})
            expected = max((path_deadline(p) for p in paths),default=-math.inf)
            self.assertAlmostEqual(labels.get('0',-math.inf),expected)


if __name__ == '__main__': unittest.main()
