"""Reproduce legacy event schedules and test NEW routing questions conditionally.

Legacy flood physics is NOT repaired or validated. No output here is a real
mine safety estimate. Original code executes only through its simulation,
before any exports. Instrumentation records the winning front event.
"""
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import numpy as np
from routing import Arc, earliest, latest_departures, path_deadline, walk, deadline_path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / 'results'
CASES = {
    1: {'exits': [(3252.16,3326.63,10),(3173.10,2819.97,10)],
        'workers': [(5808.18,5367.75,10),(5194,4785.31,10),(6190.81,3434.29,10)]},
    2: {'exits': [(6336.99,6073.22,36.15),(6416.05,6579.88,8.69)],
        'workers': [(4395.15,4614.53,6.59),(3398.34,5965.56,1.31),(3879.44,4125.47,6.22)]}}


def legacy(case):
    file = ROOT / '论文_01_中文原文的英文翻译/code' / ('appA.txt' if case == 1 else 'appB.txt')
    source = file.read_text().split('results_edges = []')[0]
    source = re.sub(r'excel_file = .*', 'excel_file = '+repr(str(ROOT/'原始材料_竞赛题目与附件'/f'附件{case}.xlsx')),source)
    # These actual workbooks have ONE header row; header=1 drops P0000/H0000.
    source = source.replace('header=1', 'header=0')
    source = source.replace('pq = []', 'audit_front = {}\npq = []')
    source = source.replace('edge_reach_time[edge_id] = current_time',
        'edge_reach_time[edge_id] = current_time\n        audit_front[edge_id] = (flow_rate, node_id)')
    ns = {}
    exec(compile(source,str(file),'exec'),ns)
    return ns, hashlib.sha256(file.read_bytes()).hexdigest()


def make_arcs(ns, factor=1.):
    arcs = []
    for edge, (u,v,length) in ns['edge_info'].items():
        if edge in ns['audit_front']:
            q, downstream = ns['audit_front'][edge]
            reach, full = ns['edge_reach_time'][edge], ns['edge_fill_time'][edge]
            # Diagnostic reconstruction from WINNING reach event; not a claim
            # that earlier losing fronts were absent. Preserve this limitation.
            wet = max(0., reach - .4*length/q)
            block = min(full, reach + .8*length/q)
            wet, block = wet/factor, block/factor
        else:
            downstream, wet, block = None, math.inf, math.inf
        for a,b in [(u,v),(v,u)]:
            arcs.append(Arc(a,b,length,wet,block,2. if b == downstream else 1.))
    return arcs


def snap(ns, xyz):
    # Requested locations in the competition datasets should be existing nodes.
    candidates = [(float(np.linalg.norm(np.array(xyz)-np.array([ns['X'][i],ns['Y'][i],ns['Z'][i]]))),n)
                  for n,i in ns['node_map'].items()]
    distance, node = min(candidates)
    if distance > .1: raise ValueError((xyz,node,distance))
    return node, distance


def insert_worker(ns, arcs, xyz, name):
    p = np.array(xyz)
    def coord(n):
        i=ns['node_map'][n]
        return np.array([ns['X'][i],ns['Y'][i],ns['Z'][i]])
    candidates=[]
    for a in arcs:
        x,y=coord(a.u),coord(a.v)
        fraction=float(np.clip(np.dot(p-x,y-x)/np.dot(y-x,y-x),0,1))
        candidates.append((float(np.linalg.norm(p-(x+fraction*(y-x)))),a.u,a.v,fraction))
    error,u,v,f=min(candidates)
    if error > .05: raise ValueError(('worker off network',xyz,error))
    if f < 1e-9: return arcs,u,error
    if f > 1-1e-9: return arcs,v,error
    split=[]
    for a in arcs:
        if {a.u,a.v} == {u,v}:
            fraction=f if a.u==u else 1-f
            split.extend([Arc(a.u,name,a.length*fraction,a.wet,a.block,a.speed),
                          Arc(name,a.v,a.length*(1-fraction),a.wet,a.block,a.speed)])
        else: split.append(a)
    return split,name,error


def number(x, positive_infinity='blocked'):
    return round(x/60,6) if math.isfinite(x) else (positive_infinity if x > 0 else 'unreachable')


def main():
    OUT.mkdir(exist_ok=True)
    rows, audits, route_records, frontier_rows = [], [], [], []
    for case, cfg in CASES.items():
        ns, digest = legacy(case)
        original_arcs = make_arcs(ns)
        exits = {snap(ns,p)[0] for p in cfg['exits']}
        audits.append({'case':case,'original_code_sha256':digest,'nodes':len(ns['node_map']),
                       'edges':len(ns['edge_info']),'wet_edges':len(ns['audit_front']),
                       'status':'legacy nonconservative flood; conditional routing only'})
        for miner,p in enumerate(cfg['workers'],1):
            arcs,start,error = insert_worker(ns,original_arcs,p,f'WORKER{miner}')
            labels, successors = latest_departures(arcs,exits)
            latest_path = deadline_path(successors,start,exits)
            dry_arcs = [Arc(a.u,a.v,a.length,math.inf,math.inf) for a in arcs]
            _, dry_path = earliest(dry_arcs,start,exits,0.)
            lookup = {(a.u,a.v):a for a in arcs}
            dry_path = [lookup[(a.u,a.v)] for a in dry_path]
            # Candidate trade-off curve, NOT a claimed complete Pareto frontier:
            # optimize at 61 departure times, evaluate all fixed paths at 1 min.
            candidates={}
            for delay in range(61):
                _,path=earliest(arcs,start,exits,delay*60.)
                if path: candidates[tuple((a.u,a.v) for a in path)] = path
            pairs=[(walk(p,60.),path_deadline(p),p) for p in candidates.values()]
            for arrival,limit,path in pairs:
                if not math.isfinite(arrival): continue
                dominated=any(a<=arrival and d>=limit and (a<arrival or d>limit) for a,d,_ in pairs)
                if not dominated:
                    frontier_rows.append({'case':case,'miner':miner,
                        'arrival_from_1min_start_min':number(arrival),
                        'route_latest_departure_min':number(limit,'unbounded'),
                        'path':';'.join([path[0].u]+[a.v for a in path])})
            for alert in (0,1,2,5,10,20,30,60):
                arrival,path = earliest(arcs,start,exits,alert*60.)
                base = {'case':case,'miner':miner,'alert_min':alert,'snap_error_m':error,
                        'earliest_arrival_min':number(arrival),
                        'travel_duration_min':number(arrival-alert*60),
                        'dry_route_arrival_min':number(walk(dry_path,alert*60)),
                        'latest_departure_min':number(labels.get(start,-math.inf),'unbounded'),
                        'fastest_route_departure_limit_min':number(path_deadline(path),'unbounded') if path else 'no_route',
                        'max_delay_route_arrival_min':number(walk(latest_path,alert*60)) if latest_path else 'no_route'}
                # Evaluate fixed nominal route under earlier flooding, without
                # choosing a new path after seeing each evaluated scenario.
                for factor in (1.1,1.25,1.5,2.):
                    changed = {(a.u,a.v):Arc(a.u,a.v,a.length,a.wet/factor,a.block/factor,a.speed) for a in arcs}
                    stressed = [changed[(a.u,a.v)] for a in path]
                    base[f'fixed_route_Qx{factor}_arrival_min'] = number(walk(stressed,alert*60)) if path else 'no_route'
                rows.append(base)
                route_records.append({'case':case,'miner':miner,'alert_min':alert,
                                      'fastest_path':[(a.u,a.v) for a in path],
                                      'latest_path':[(a.u,a.v) for a in latest_path]})
        print('Finished network',case,flush=True)
    with (OUT/'conditional_routes.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0])); writer.writeheader();writer.writerows(rows)
    (OUT/'audit.json').write_text(json.dumps(audits,indent=2))
    (OUT/'paths.json').write_text(json.dumps(route_records,indent=2))
    with (OUT/'candidate_tradeoffs.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(frontier_rows[0]));writer.writeheader();writer.writerows(frontier_rows)
    for row in rows:
        if row['alert_min']==1: print(row)


if __name__ == '__main__': main()
