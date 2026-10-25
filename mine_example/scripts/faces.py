"""Escape statistics for every working face (dead end) of the mine network.
Usage (from the project root):  python -m mine_example.scripts.faces"""
import json
import math
import statistics

import networkx as nx

from mine_example.scripts.simulate import ROOT, latest_alert, run, setup
from model.routing import arcs, fastest, walk


def main():
    G, feats, exits, ring, A = setup()
    f = run(G, feats, exits, A)
    adj = arcs(f)
    dA = nx.single_source_dijkstra_path_length(G, A, weight='length')
    _, dry_paths = nx.multi_source_dijkstra(G, exits, weight='length')
    rows = []
    for n in G:
        if G.degree(n) != 1 or n in exits:
            continue
        t, path = fastest(adj, n, exits, 60.0)
        dry = dry_paths[n][::-1]
        td, _ = walk([next(a for a in adj[x] if a.b == y) for x, y in zip(dry, dry[1:])], 60.0)
        la = latest_alert(adj, n, exits, hi=4e6)
        rows.append(dict(face=n, dist_km=dA[n] / 1000, aware_min=t / 60, dry_min=td / 60,
                         latest_alert_min=None if la is None else la / 60))
    gains = [r['dry_min'] - r['aware_min'] for r in rows if math.isfinite(r['dry_min'])]
    la = [r['latest_alert_min'] if r['latest_alert_min'] is not None else 0.0 for r in rows]
    near = [r for r in rows if r['dist_km'] <= 2.0]
    summary = dict(
        faces=len(rows),
        dry_route_cut=sum(not math.isfinite(r['dry_min']) for r in rows),
        faces_with_gain=sum(g > 1 / 60 for g in gains), max_gain_min=max(gains),
        latest_alert_lt_10min=sum(x < 10 for x in la), latest_alert_lt_1h=sum(x < 60 for x in la),
        latest_alert_lt_1d=sum(x < 1440 for x in la),
        faces_within_2km=len(near),
        near_with_gain=sum(r['dry_min'] - r['aware_min'] > 1 / 60 for r in near if math.isfinite(r['dry_min'])),
        near_latest_alert_median_h=statistics.median(x['latest_alert_min'] or 0 for x in near) / 60,
        all_latest_alert_median_d=statistics.median(la) / 1440,
    )
    (ROOT / 'results' / 'faces.json').write_text(json.dumps(dict(summary=summary, faces=rows), indent=1))
    print(json.dumps(summary, indent=1))
    for r in sorted(rows, key=lambda r: r['latest_alert_min'] or 0)[:8]:
        print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()})


if __name__ == '__main__':
    main()
