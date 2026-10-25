"""Problems 1-4 of CUMCM 2025 Problem D with the revised model, plus sensitivity and checks.

Usage (from the project root):  python -m competition.run
Writes competition/results/*.json, *.xlsx and the figures in competition/figures/.
"""
import json
import math
import statistics
from pathlib import Path

import networkx as nx
import pandas as pd

from model.flood import Flood
from model.legacy import legacy_flood
from model.network import insert_point, load_workbook
from model.routing import V_AGAINST, V_DRY, V_WITH, Arc, arcs, fastest, latest_departure, walk, where

ROOT = Path(__file__).resolve().parent
DATA = ROOT.parent / 'original_question'
Q = 30 / 60
ALERT = 60.0

NETWORKS = {
    1: dict(file='附件1.xlsx', A=(5349.03, 4931.90, 10.00), B=(3760.40, 3808.33, 10.00), tB=240.0,
            exits=[(3252.16, 3326.63, 10.00), (3173.10, 2819.97, 10.00)],
            miners=[(5808.18, 5367.75, 10.00), (5194.00, 4785.31, 10.00), (6190.81, 3434.29, 10.00)]),
    2: dict(file='附件2.xlsx', A=(4143.12, 4376.28, 6.33), B=(5883.14, 5643.35, 40.37), tB=300.0,
            exits=[(6336.99, 6073.22, 36.15), (6416.05, 6579.88, 8.69)],
            miners=[(4395.15, 4614.53, 6.59), (3398.34, 5965.56, 1.31), (3879.44, 4125.47, 6.22)]),
}


def build(cfg):
    G = load_workbook(DATA / cfg['file'])
    n_nodes, n_edges = G.number_of_nodes(), G.number_of_edges()
    snap = {}
    for name, xyz in [('A', cfg['A']), ('B', cfg['B'])] + \
            [(f'E{k + 1}', p) for k, p in enumerate(cfg['exits'])] + \
            [(f'M{k + 1}', p) for k, p in enumerate(cfg['miners'])]:
        node, d = insert_point(G, xyz, name)
        snap[name] = (node, d)
    return G, snap, n_nodes, n_edges


def tunnel_table(G, f):
    """Times per original tunnel (split parts merged): water enters, covered, impassable, full."""
    rows = {}
    for e in f.E.values():
        d = G.edges[e.u, e.v]
        key = d.get('parent', d['id'])
        r = rows.setdefault(key, dict(t_in=math.inf, t_block=math.inf, t_full=-math.inf, L=0.0))
        r['t_in'] = min(r['t_in'], e.t_in)
        r['t_block'] = min(r['t_block'], e.t_block)
        r['t_full'] = max(r['t_full'], e.t_full)
        r['L'] += e.L
    return rows


def flood_stats(G, f, n_orig_nodes):
    orig = [n for n in G if n.startswith('P')]
    wet = [f.wet[n] for n in orig]
    tt = tunnel_table(G, f)
    full = [r['t_full'] for r in tt.values()]
    total = sum(f.W * f.H * e.L for e in f.E.values())
    return dict(nodes_reached=sum(map(math.isfinite, wet)), nodes=len(orig),
                median_node_min=statistics.median(wet) / 60, max_node_min=max(wet) / 60,
                tunnels_full=sum(map(math.isfinite, full)), tunnels=len(tt),
                last_full_h=max(full) / 3600, bound_h=total / Q / 3600,
                residual=f.max_residual, lost_m3=f.overflow)


def route_record(adj, start, exits, t0, G):
    t, path = fastest(adj, start, exits, t0)
    rec = dict(start=start, escape_min=t / 60, exit=path[-1].b if path else None,
               length_km=sum(a.L for a in path) / 1000,
               latest_dep_min=latest_departure(path) / 60 if path else None,
               nodes=[path[0].a] + [a.b for a in path] if path else [])
    # baseline: the shortest route in a dry mine, walked through the actual flood
    lengths, paths = nx.multi_source_dijkstra(G.reverse() if G.is_directed() else G, exits, target=start, weight='length')
    dry_nodes = paths[::-1]
    dry = [next(a for a in adj[x] if a.b == y) for x, y in zip(dry_nodes, dry_nodes[1:])]
    td, stuck = walk(dry, t0)
    rec.update(dry_min=td / 60, dry_cut_at=stuck, dry_km=lengths / 1000, same_route=rec['nodes'] == dry_nodes)
    return rec, path


def expand(G, seq):
    """Node sequence -> path in G, filling in nodes added by later splits."""
    out = [seq[0]]
    for x, y in zip(seq, seq[1:]):
        out += nx.shortest_path(G, x, y, weight='length')[1:] if not G.has_edge(x, y) else [y]
    return out


def solve(net, cfg, speeds=(V_DRY, V_WITH, V_AGAINST), q=Q, h0=0.1, alert=ALERT, full=True):
    G, snap, n0, e0 = build(cfg)
    A, exits = snap['A'][0], {snap[f'E{k}'][0] for k in (1, 2)}
    miners = [snap[f'M{k}'][0] for k in (1, 2, 3)]
    f1 = Flood(G, [(A, 0.0, q)], h0=h0)
    f1.run()
    adj1 = arcs(f1, speeds)
    p2, paths = [], []
    for m in miners:
        rec, path = route_record(adj1, m, exits, alert, G)
        p2.append(rec)
        paths.append(path)
    out = dict(G=G, snap=snap, f1=f1, p2=p2, paths=paths, exits=exits, miners=miners, A=A)
    if not full:
        return out
    out['legacy'] = legacy_flood(G, A, q, h0=h0, strict_uphill=(net == 2))

    # Problem 3/4: the second inrush at B; re-plan 1 minute later from where each miner is.
    # The flood runs on the same graph; a miner inside a tunnel can go on or turn back.
    tB, t_switch = cfg['tB'], cfg['tB'] + 60.0
    B = snap['B'][0]
    f2 = Flood(G, [(A, 0.0, q), (B, tB, q)], h0=h0)
    f2.run()
    adj2 = arcs(f2, speeds)
    p4 = []
    for k, (rec, path) in enumerate(zip(p2, paths)):
        w = where(path, alert, t_switch)
        if w[0] == 'exit':
            p4.append(dict(miner=f'M{k + 1}', status='already out', escape_min=rec['escape_min']))
            continue
        arc, s = w[1], w[2]
        fwd = next(a for a in adj2[arc.a] if a.b == arc.b)
        back = next(a for a in adj2[arc.b] if a.b == arc.a)
        R = f'R{k + 1}'
        adj = dict(adj2)
        adj[R] = [Arc(R, arc.b, arc.L - s, fwd.wet, fwd.block, fwd.speed[1] == speeds[1], speeds),
                  Arc(R, arc.a, s, back.wet, back.block, back.speed[1] == speeds[1], speeds)]
        t_new, new = fastest(adj, R, exits, t_switch)
        rest = rec['nodes'][rec['nodes'].index(arc.b):]
        old_path = [adj[R][0]] + [next(a for a in adj2[x] if a.b == y) for x, y in zip(rest, rest[1:])]
        t_old, stuck = walk(old_path, t_switch)
        a_xyz, b_xyz = G.nodes[arc.a]['xyz'], G.nodes[arc.b]['xyz']
        p4.append(dict(miner=f'M{k + 1}', status='re-planned', on=(arc.a, arc.b), along_m=s,
                       xy=tuple(a_xyz[i] + s / arc.L * (b_xyz[i] - a_xyz[i]) for i in range(2)),
                       escape_min=t_new / 60, exit=new[-1].b if new else None,
                       length_km=sum(a.L for a in new) / 1000,
                       latest_dep_min=latest_departure(new) / 60 if new else None,
                       old_min=t_old / 60, old_cut_at=stuck, turned_back=new[0].b == arc.a,
                       same_as_old=[a.b for a in new] == rest,
                       nodes=[R] + [a.b for a in new]))
    # how much the inserted points (exits, miners, B) change the Problem 1 flood times
    G0 = load_workbook(DATA / cfg['file'])
    insert_point(G0, cfg['A'], 'A')
    f0 = Flood(G0, [('A', 0.0, q)], h0=h0)
    f0.run()
    diffs = [abs(f0.wet[n] - f1.wet[n]) / 60 for n in G0 if n.startswith('P') and math.isfinite(f0.wet[n])]
    out.update(f2=f2, p4=p4, t_switch=t_switch, B=B, adj2=adj2,
               subdivision=dict(median_min=statistics.median(diffs), max_min=max(diffs),
                                median_rel=statistics.median(d / (f0.wet[n] / 60) for d, n in
                                                             zip(diffs, [n for n in G0 if n.startswith('P') and math.isfinite(f0.wet[n])])
                                                             if f0.wet[n] > 0)))
    return out


def main():
    (ROOT / 'results').mkdir(exist_ok=True)
    summary, keep = {}, {}
    for net, cfg in NETWORKS.items():
        r = solve(net, cfg)
        keep[net] = r
        G, f1, f2 = r['G'], r['f1'], r['f2']
        node_t, t_arr, t_full = r['legacy']
        leg = [node_t[n] for n in G if n.startswith('P')]
        leg_reached = [x for x in leg if math.isfinite(x)]
        s = dict(snap={k: [v[0], round(v[1], 4)] for k, v in r['snap'].items()},
                 problem1=flood_stats(G, f1, 0), problem3=flood_stats(G, f2, 0),
                 legacy=dict(nodes_reached=len(leg_reached), median_node_min=statistics.median(leg_reached) / 60,
                             max_node_min=max(leg_reached) / 60),
                 problem2=[{k: v for k, v in p.items() if k != 'nodes'} for p in r['p2']],
                 problem4=[{k: v for k, v in p.items() if k != 'nodes'} for p in r['p4']],
                 subdivision=r['subdivision'])
        # Proposition 1 on the real network
        G1, snap1, _, _ = build(cfg)
        fq = Flood(G1, [(snap1['A'][0], 0.0, 1.1 * Q)])
        fq.run()
        ratios = [getattr(fq.E[k], a) / getattr(e, a) for k, e in f1.E.items()
                  for a in ('t_in', 't_cov', 't_block', 't_full') if math.isfinite(getattr(e, a)) and getattr(e, a) > 0]
        s['prop1'] = dict(n=len(ratios), min=min(ratios), max=max(ratios))
        summary[net] = s
        # result workbooks (times in minutes, 2 decimals)
        for tag, GG, ff in (('1', G, f1), ('3', G, f2)):
            nodes = pd.DataFrame([[n, round(ff.wet[n] / 60, 2) if math.isfinite(ff.wet[n]) else None]
                                  for n in sorted(GG) if n.startswith('P')], columns=['端点编号', '水流到达时刻(min)'])
            tt = tunnel_table(GG, ff)
            tun = pd.DataFrame([[k, round(v['t_in'] / 60, 2), round(v['t_block'] / 60, 2), round(v['t_full'] / 60, 2)]
                                for k, v in sorted(tt.items())],
                               columns=['巷道编号', '水流进入时刻(min)', '水深超过0.3m时刻(min)', '充满水时刻(min)'])
            with pd.ExcelWriter(ROOT / 'results' / f'result{tag}-{net}.xlsx') as xw:
                nodes.to_excel(xw, sheet_name='端点', index=False)
                tun.to_excel(xw, sheet_name='巷道', index=False)
        for tag, recs in (('2', r['p2']), ('4', r['p4'])):
            pd.DataFrame([{'矿工': f'M{k + 1}', '逃生用时(min, 从突水起)': round(p['escape_min'], 2),
                           '出口': p.get('exit'), '路径': ' -> '.join(p.get('nodes', []))}
                          for k, p in enumerate(recs)]).to_excel(ROOT / 'results' / f'result{tag}-{net}.xlsx', index=False)

    # Sensitivity (Problem 2 setting): one parameter at a time
    base = {net: solve(net, cfg, full=False)['p2'] for net, cfg in NETWORKS.items()}
    cases = [('Q', +0.1), ('Q', -0.1), ('h0', +0.1), ('h0', -0.1), ('v_with', +0.1), ('v_with', -0.1),
             ('v_against', +0.1), ('v_against', -0.1)] + [('alert', a) for a in (0, 2, 5, 10, 15, 20)]
    sens = []
    for par, x in cases:
        changes, route_changes, cut, dry_changes = [], 0, 0, []
        for net, cfg in NETWORKS.items():
            kw = dict(full=False)
            if par == 'Q':
                kw['q'] = Q * (1 + x)
            elif par == 'h0':
                kw['h0'] = 0.1 * (1 + x)
            elif par == 'v_with':
                kw['speeds'] = (V_DRY, V_WITH * (1 + x), V_AGAINST)
            elif par == 'v_against':
                kw['speeds'] = (V_DRY, V_WITH, V_AGAINST * (1 + x))
            else:
                kw['alert'] = 60.0 * x
            res = solve(net, cfg, **kw)['p2']
            for b, p in zip(base[net], res):
                t0b, t0p = ALERT, kw.get('alert', ALERT)
                changes.append(((p['escape_min'] - t0p / 60) - (b['escape_min'] - t0b / 60)) / (b['escape_min'] - t0b / 60))
                route_changes += p['nodes'] != b['nodes']
                cut += not math.isfinite(p['dry_min'])
                if math.isfinite(p['dry_min']) and math.isfinite(b['dry_min']):
                    dry_changes.append(((p['dry_min'] - t0p / 60) - (b['dry_min'] - t0b / 60)) / (b['dry_min'] - t0b / 60))
        sens.append(dict(parameter=par, change=x, mean_travel_change_pct=100 * statistics.mean(changes),
                         max_abs_travel_change_pct=100 * max(map(abs, changes)),
                         routes_changed=route_changes, dry_routes_cut=cut,
                         mean_dry_change_pct=100 * statistics.mean(dry_changes) if dry_changes else None))
    summary['sensitivity'] = sens
    (ROOT / 'results' / 'summary.json').write_text(json.dumps(summary, indent=1, ensure_ascii=False, default=str))
    print(json.dumps(summary, indent=1, ensure_ascii=False, default=str))
    return keep


if __name__ == '__main__':
    main()
