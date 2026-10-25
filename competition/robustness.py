"""Additional experiments for the article: run times and sensitivity of the flood times to
subdividing tunnels.  Usage (from the project root):  python -m competition.robustness"""
import json
import math
import random
import statistics
import time
from pathlib import Path

from competition.run import NETWORKS, Q, build
from model.flood import Flood
from model.network import insert_point
from model.routing import arcs, fastest

ROOT = Path(__file__).resolve().parent


def subdivision_test(cfg, trials=20, points=10, seed=0):
    """Insert `points` extra degree-2 nodes at random positions and compare junction arrival times."""
    rng = random.Random(seed)
    G, snap, _, _ = build(cfg)
    base = Flood(G, [(snap['A'][0], 0.0, Q)])
    base.run()
    orig = [n for n in G if n.startswith('P')]
    rel = []
    for _ in range(trials):
        H = G.copy()
        edges = list(H.edges())
        for k in range(points):
            u, v = rng.choice(edges)
            a, b = H.nodes[u]['xyz'], H.nodes[v]['xyz']
            s = rng.uniform(0.2, 0.8)
            insert_point(H, tuple(a[i] + s * (b[i] - a[i]) for i in range(3)), f'X{k}')
            edges = list(H.edges())
        f = Flood(H, [(snap['A'][0], 0.0, Q)])
        f.run()
        rel += [abs(f.wet[n] - base.wet[n]) / base.wet[n] for n in orig if base.wet[n] > 0]
    rel.sort()
    return dict(trials=trials, points=points, samples=len(rel),
                unchanged_share=sum(r < 1e-9 for r in rel) / len(rel),
                p95=rel[int(0.95 * len(rel))], p99=rel[int(0.99 * len(rel))], max=rel[-1])


def runtimes(cfg):
    G, snap, _, _ = build(cfg)
    t = time.perf_counter()
    f = Flood(G, [(snap['A'][0], 0.0, Q)])
    f.run()
    t_flood = time.perf_counter() - t
    adj = arcs(f)
    exits = {snap['E1'][0], snap['E2'][0]}
    t = time.perf_counter()
    for k in (1, 2, 3):
        fastest(adj, snap[f'M{k}'][0], exits, 60.0)
    t_route = (time.perf_counter() - t) / 3
    return dict(flood_s=t_flood, route_ms=1000 * t_route, nodes=G.number_of_nodes(), edges=G.number_of_edges())


def main():
    out = {}
    for net, cfg in NETWORKS.items():
        out[net] = dict(runtime=runtimes(cfg), subdivision=subdivision_test(cfg))
        print(net, out[net])
    (ROOT / 'results' / 'robustness.json').write_text(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
