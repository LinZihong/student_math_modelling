"""Tests for the flood and routing models.  Run: python -m unittest model.test_model -v"""
import itertools
import math
import random
import unittest

import networkx as nx

from model.flood import Flood
from model.routing import Arc, fastest, latest_departure, walk

W, H, H0, Q = 4.0, 3.0, 0.1, 0.5


def graph(nodes, edges):
    G = nx.Graph()
    for n, xyz in nodes.items():
        G.add_node(n, xyz=xyz)
    for k, (a, b) in enumerate(edges):
        G.add_edge(a, b, id=f'H{k}', length=math.dist(nodes[a], nodes[b]))
    return G


def run(G, sources):
    f = Flood(G, sources, W=W, H=H, h0=H0)
    f.run()
    return f


class FloodTests(unittest.TestCase):
    def test_single_dead_end(self):
        f = run(graph({'s': (0, 0, 0), 'a': (100, 0, 0)}, [('s', 'a')]), [('s', 0.0, Q)])
        e = f.tunnel('s', 'a')
        self.assertAlmostEqual(e.t_cov, W * H0 * 100 / Q)
        self.assertAlmostEqual(e.t_block, W * 0.3 * 100 / Q)
        self.assertAlmostEqual(e.t_full, W * H * 100 / Q)
        self.assertAlmostEqual(f.wet['a'], e.t_cov)

    def test_series_backs_up_from_the_dead_end(self):
        f = run(graph({'s': (0, 0, 0), 'a': (100, 0, 0), 'b': (300, 0, 0)}, [('s', 'a'), ('a', 'b')]),
                [('s', 0.0, Q)])
        e1, e2 = f.tunnel('s', 'a'), f.tunnel('a', 'b')
        self.assertAlmostEqual(f.wet['b'], W * H0 * 300 / Q)
        self.assertAlmostEqual(e2.t_full, W * H0 * 100 / Q + W * H * 200 / Q)   # e1 passes water on until e2 is full
        self.assertAlmostEqual(e1.t_full, W * H * 300 / Q)
        self.assertLess(e2.t_full, e1.t_full)

    def test_equal_split_at_a_junction(self):
        nodes = {'s': (0, 0, 0), 'j': (50, 0, 0), 'a': (150, 0, 0), 'b': (50, 100, 0)}
        f = run(graph(nodes, [('s', 'j'), ('j', 'a'), ('j', 'b')]), [('s', 0.0, Q)])
        self.assertAlmostEqual(f.wet['a'], f.wet['b'])
        self.assertAlmostEqual(f.wet['a'] - f.wet['j'], W * H0 * 100 / (Q / 2))

    def test_loop_conserves_volume_and_fills_by_total_volume(self):
        nodes = {'s': (0, 0, 0), 'a': (100, 0, 0), 'b': (0, 120, 0), 'c': (90, 140, 0)}
        G = graph(nodes, [('s', 'a'), ('s', 'b'), ('a', 'c'), ('b', 'c'), ('a', 'b')])
        f = run(G, [('s', 0.0, Q)])
        total = sum(W * H * d['length'] for _, _, d in G.edges(data=True))
        self.assertLess(f.max_residual, 1e-9)
        self.assertAlmostEqual(max(e.t_full for e in f.E.values()), total / Q, places=6)

    def test_water_goes_downhill_first_and_rises_into_uphill_tunnels_later(self):
        nodes = {'s': (0, 0, 5), 'j': (50, 0, 5), 'lo': (150, 0, 0), 'hi': (50, 100, 8), 'top': (50, 200, 8)}
        G = graph(nodes, [('s', 'j'), ('j', 'lo'), ('j', 'hi'), ('hi', 'top')])
        f = run(G, [('s', 0.0, Q)])
        down, up = f.tunnel('j', 'lo'), f.tunnel('j', 'hi')
        self.assertGreaterEqual(up.t_in, down.t_full)       # uphill only after the downhill branch is full
        self.assertAlmostEqual(f.wet['hi'], up.t_full)       # the uphill tunnel fills from the bottom
        self.assertLess(f.wet['top'], math.inf)              # and then delivers water beyond it
        self.assertLess(f.max_residual, 1e-9)

    def test_two_sources_and_conservation(self):
        rng = random.Random(3)
        G = nx.random_geometric_graph(40, 0.3, seed=5)
        G = G.subgraph(max(nx.connected_components(G), key=len)).copy()
        for n in G:
            x, y = G.nodes[n]['pos']
            G.nodes[n]['xyz'] = (1000 * x, 1000 * y, rng.choice([0.0, 0.0, 1.0, 2.0]))
        for u, v in G.edges():
            G.edges[u, v]['length'] = math.dist(G.nodes[u]['xyz'], G.nodes[v]['xyz'])
        a, b = list(G)[:2]
        f = run(G, [(a, 0.0, Q), (b, 300.0, Q)])
        self.assertLess(f.max_residual, 1e-9)
        total = sum(W * H * d['length'] for _, _, d in G.edges(data=True))
        self.assertLessEqual(max(e.t_full for e in f.E.values()), (total + 300 * Q) / (2 * Q) + 1e-6)

    def test_proposition_1_scaling(self):
        rng = random.Random(7)
        G = nx.random_geometric_graph(60, 0.22, seed=11)
        G = G.subgraph(max(nx.connected_components(G), key=len)).copy()
        for n in G:
            x, y = G.nodes[n]['pos']
            G.nodes[n]['xyz'] = (1000 * x, 1000 * y, rng.choice([0.0, 1.0, 3.0]))
        for u, v in G.edges():
            G.edges[u, v]['length'] = math.dist(G.nodes[u]['xyz'], G.nodes[v]['xyz'])
        s = next(iter(G))
        f1, f2 = run(G, [(s, 0.0, Q)]), run(G, [(s, 0.0, 1.1 * Q)])
        for k, e in f1.E.items():
            for attr in ('t_in', 't_cov', 't_block', 't_full'):
                x, y = getattr(e, attr), getattr(f2.E[k], attr)
                if math.isfinite(x) and x > 0:
                    self.assertAlmostEqual(y / x, 1 / 1.1, places=9)


class RoutingTests(unittest.TestCase):
    def test_exact_traversal_counterexample(self):
        self.assertAlmostEqual(Arc('a', 'b', 20, 4.1, math.inf, True).exit_time(0), 5.9)   # 20 segments give 5.75
        self.assertEqual(Arc('a', 'b', 20, 4.1, 5.77, True).exit_time(0), math.inf)

    def test_first_in_first_out_and_latest_entry(self):
        rng = random.Random(1)
        for _ in range(2000):
            wet = rng.uniform(0, 100)
            arc = Arc('a', 'b', rng.uniform(1, 300), wet, wet + rng.uniform(0, 200), rng.random() < 0.5)
            t1, t2 = sorted(rng.uniform(0, 300) for _ in range(2))
            self.assertLessEqual(arc.exit_time(t1), arc.exit_time(t2))
            d = rng.uniform(0, 400)
            le = arc.latest_entry(d)
            if le > -math.inf and math.isfinite(le):
                self.assertLessEqual(arc.exit_time(le), d + 1e-6)
                self.assertTrue(arc.exit_time(le + 1e-3) > d or arc.exit_time(le + 1e-3) == math.inf)

    def test_dijkstra_matches_brute_force(self):
        rng = random.Random(2)
        for trial in range(150):
            G = nx.gnp_random_graph(7, 0.45, seed=trial)
            adj, arcs = {}, {}
            for u, v in G.edges():
                L, wet = rng.uniform(10, 200), rng.uniform(0, 60)
                block = wet + rng.uniform(0, 80) if rng.random() < 0.6 else math.inf
                src = rng.choice([u, v])
                for a, b in ((u, v), (v, u)):
                    arc = Arc(a, b, L, wet, block, src == a)
                    adj.setdefault(a, []).append(arc)
                    arcs[a, b] = arc
            exits = {5, 6}
            t, path = fastest(adj, 0, exits, 10.0)
            best = math.inf
            for x in exits:
                if 0 in G and x in G and nx.has_path(G, 0, x):
                    for p in nx.all_simple_paths(G, 0, x):
                        best = min(best, walk([arcs[a, b] for a, b in zip(p, p[1:])], 10.0)[0])
            self.assertAlmostEqual(t, best) if math.isfinite(best) else self.assertEqual(t, math.inf)
            if path:
                self.assertAlmostEqual(walk(path, 10.0)[0], t)
                self.assertGreaterEqual(latest_departure(path), 10.0 - 1e-9)


if __name__ == '__main__':
    unittest.main()
