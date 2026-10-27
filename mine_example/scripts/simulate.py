"""Worked example: the 论文_02_洪水传播与动态逃生_Claude稿's flood model and escape routing on an anonymized real mine plan.

Usage (from the project root):  python -m mine_example.scripts.simulate
Writes mine_example/results/summary.json and the figures in mine_example/figures/.

Scenario: water breaks in from the water-accumulation zone closest (by tunnel distance) to the
shafts; Q = 30 m^3/min and the other parameters of the competition problem; tunnel width
measured from the drawing; four miners at working faces; the four shaft bottoms are the exits.
"""
import json
import math
import statistics
from pathlib import Path

import networkx as nx
from shapely.geometry import LineString, Polygon
from shapely.ops import nearest_points

from model.flood import Flood
from model.legacy import legacy_flood
from model.network import insert_point, load_workbook
from model.routing import arcs, fastest, latest_departure, walk

ROOT = Path(__file__).resolve().parents[1]
Q = 30 / 60
ALERT = 60.0
# working faces nearest the inrush (0.3, 0.8 and 1.9 km away) and one on the far side of the mine
MINERS = {'M1': 'P0901', 'M2': 'P1146', 'M3': 'P1434', 'M4': 'P0176'}


def setup():
    G = load_workbook(ROOT / 'data' / 'mine_network.xlsx')
    feats = json.loads((ROOT / 'data' / 'mine_features.json').read_text())
    exits = {s['node'] for s in feats['shafts']}
    rings = [Polygon(p).buffer(0) for p in feats['water_outlines']]
    inner = [p for p in rings if not any(q is not p and q.area < p.area and p.contains(q.representative_point())
                                         for q in rings)]
    dist = nx.multi_source_dijkstra_path_length(G, exits, weight='length')
    seg = lambda u, v: LineString([G.nodes[u]['xyz'][:2], G.nodes[v]['xyz'][:2]])

    def zone_entry(ring):
        u, v = min(G.edges(), key=lambda e: seg(*e).distance(ring))
        return seg(u, v).distance(ring), u, v

    # the zone that is closest to the shafts by tunnel distance, among zones a roadway touches
    cands = [(min(dist[u], dist[v]), ring) for ring in inner for d, u, v in [zone_entry(ring)] if d < 1.0]
    _, ring = min(cands, key=lambda c: c[0])
    _, u, v = zone_entry(ring)
    p = nearest_points(seg(u, v), ring)[0]
    a, b = G.nodes[u]['xyz'], G.nodes[v]['xyz']
    s = LineString([a[:2], b[:2]]).project(p, normalized=True)
    A, _ = insert_point(G, tuple(a[i] + s * (b[i] - a[i]) for i in range(3)), 'A')
    return G, feats, exits, ring, A


def run(G, feats, exits, A, q=Q):
    f = Flood(G, [(A, 0.0, q)], W=feats['tunnel_width_m'])
    f.run()
    return f


def routes(G, f, exits, t0):
    adj = arcs(f)
    out, paths = {}, {}
    for name, start in MINERS.items():
        t, path = fastest(adj, start, exits, t0)
        dry_nodes = nx.multi_source_dijkstra(G, exits, target=start, weight='length')[1][::-1]
        dry = [next(a for a in adj[x] if a.b == y) for x, y in zip(dry_nodes, dry_nodes[1:])]
        td, stuck = walk(dry, t0)
        out[name] = dict(escape_min=t / 60, exit=path[-1].b if path else None, km=sum(a.L for a in path) / 1000,
                         latest_dep_min=latest_departure(path) / 60 if path else None,
                         dry_min=td / 60, dry_cut_at=stuck, dry_km=sum(a.L for a in dry) / 1000,
                         same_route=[a.b for a in path] == dry_nodes[1:])
        paths[name] = dict(aware=[path[0].a] + [a.b for a in path] if path else [], dry=dry_nodes, cut=stuck)
    return out, paths


def latest_alert(adj, start, exits, hi=1e7):
    """Latest start time from which some route still reaches an exit. Escaping is monotone in the
    start time (Lemma 1: an earlier start reaches every node no later), so bisection applies."""
    lo = 0.0
    if fastest(adj, start, exits, lo)[0] == math.inf:
        return None
    if fastest(adj, start, exits, hi)[0] < math.inf:
        return math.inf
    while hi - lo > 0.01:
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if fastest(adj, start, exits, mid)[0] < math.inf else (lo, mid)
    return lo


def main():
    G, feats, exits, ring, A = setup()
    f = run(G, feats, exits, A)
    W = feats['tunnel_width_m']
    z = {n: G.nodes[n]['xyz'][2] for n in G}
    summary = dict(inrush=dict(node=A, z=z[A]), shafts_z=sorted(z[n] for n in exits),
                   miners_z={k: z[v] for k, v in MINERS.items()})
    wet_t = [f.wet[n] for n in G if n.startswith('P')]
    total = sum(W * f.H * e.L for e in f.E.values())
    summary['flood'] = dict(
        median_node_days=statistics.median(wet_t) / 86400, max_node_days=max(wet_t) / 86400,
        last_full_days=max(e.t_full for e in f.E.values()) / 86400, bound_days=total / Q / 86400,
        residual=f.max_residual,
        extent={m: dict(wet_km=sum(e.L for e in f.E.values() if e.t_in <= 60 * m) / 1000,
                        impassable_km=sum(e.L for e in f.E.values() if e.t_block <= 60 * m) / 1000)
                for m in (10, 30, 60, 180, 1440)})
    node_t, _, _ = legacy_flood(G, A, Q, W=W)
    lt = [node_t[n] for n in G if n.startswith('P') and math.isfinite(node_t[n])]
    summary['legacy'] = dict(median_node_days=statistics.median(lt) / 86400, max_node_days=max(lt) / 86400,
                             reached=len(lt))
    f2 = run(G, feats, exits, A, 1.1 * Q)
    ratios = [getattr(f2.E[k], a) / getattr(e, a) for k, e in f.E.items()
              for a in ('t_in', 't_block', 't_full') if math.isfinite(getattr(e, a)) and getattr(e, a) > 0]
    summary['prop1'] = dict(n=len(ratios), min=min(ratios), max=max(ratios))

    summary['routes'], paths = routes(G, f, exits, ALERT)
    adj = arcs(f)
    for name, start in MINERS.items():
        la = latest_alert(adj, start, exits)
        summary['routes'][name]['latest_alert_min'] = la / 60 if la is not None else None
        summary['routes'][name]['dist_to_inrush_km'] = nx.shortest_path_length(G, A, start, weight='length') / 1000
    sweep = []
    for delay in (1, 3, 5, 10, 15, 20, 30):
        r, _ = routes(G, f, exits, 60.0 * delay)
        for name, x in r.items():
            sweep.append(dict(alert_min=delay, miner=name, aware_min=x['escape_min'],
                              aware_ok=math.isfinite(x['escape_min']),
                              dry_min=x['dry_min'] if math.isfinite(x['dry_min']) else 'cut off'))
    summary['alert_sweep'] = sweep
    (ROOT / 'results').mkdir(exist_ok=True)
    (ROOT / 'results' / 'summary.json').write_text(json.dumps(summary, indent=1, default=str))
    print(json.dumps({k: v for k, v in summary.items() if k != 'alert_sweep'}, indent=1, default=str))
    for row in sweep:
        print(row)
    return G, f, exits, ring, A, paths, summary


if __name__ == '__main__':
    main()
