"""Reproduce the preprint experiments without changing the source project.

Run from any directory: python preprint/code/run.py
Internal pickle caches are LOCAL trusted outputs, not distributable input formats.
"""
import csv
import hashlib
import importlib.util
import json
import math
import pickle
import random
import sys
import time
from pathlib import Path
import networkx as nx
from model.network import load_workbook,insert_point
from model.flood import Flood
from model.routing import Arc,arcs,fastest,walk,latest_departure
from robust import latest_network,constrained,budget_deadline

PAPER=Path(__file__).resolve().parents[1]
ROOT=PAPER.parent
OUT=PAPER/'results'
T0=60.
MINER_XYZ=[(4395.15,4614.53,6.59),(3398.34,5965.56,1.31),(3879.44,4125.47,6.22)]


def setup(case):
    if case=='competition':
        G=load_workbook(PAPER/'data/competition_network.xlsx')
        n0,e0=G.number_of_nodes(),G.number_of_edges()
        source,_=insert_point(G,(4143.12,4376.28,6.33),'A')
        exits=set()
        for p in [(6336.99,6073.22,36.15),(6416.05,6579.88,8.69)]:
            x=min(G,key=lambda n:math.dist(G.nodes[n]['xyz'],p))
            assert math.dist(G.nodes[x]['xyz'],p)<.05
            exits.add(x)
        return G,source,exits,4.,{},n0,e0
    spec=importlib.util.spec_from_file_location('cad_setup',PAPER/'audit/cad_scenario_source.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.ROOT=PAPER/'data/cad'
    G,feats,exits,ring,source=module.setup()
    return G,source,exits,feats['tunnel_width_m'],module.MINERS,G.number_of_nodes()-1,G.number_of_edges()-1


def dataset(case):
    cache=OUT/f'{case}_cache.pkl'
    if cache.exists():
        with cache.open('rb') as f:return pickle.load(f)
    G,source,exits,W,miners,n0,e0=setup(case)
    start=time.perf_counter()
    f=Flood(G,[(source,0.,.5)],W=W)
    f.run()
    elapsed=time.perf_counter()-start
    assert f.max_residual<1e-9
    assert all(math.isfinite(e.t_full) for e in f.E.values())
    # Split worker locations only in the routing graph, not the water simulation.
    H=G.copy()
    for u,v,d in H.edges(data=True):d['parent']=d['id']
    if case=='competition':
        miners={}
        for i,p in enumerate(MINER_XYZ,1):
            n,error=insert_point(H,p,f'M{i}')
            assert error<.05
            miners[f'M{i}']=n
    by_id={G.edges[e.u,e.v]['id']:e for e in f.E.values()}
    adj={}
    for u,v,data in H.edges(data=True):
        e=by_id[data['parent']]
        src=G.nodes[e.src]['xyz'];dst=G.nodes[e.other(e.src)]['xyz']
        for a,b in [(u,v),(v,u)]:
            x,y=H.nodes[a]['xyz'],H.nodes[b]['xyz']
            with_flow=sum((dst[k]-src[k])*(y[k]-x[k]) for k in range(3))>0
            adj.setdefault(a,[]).append(Arc(a,b,data['length'],e.t_in,e.t_block,with_flow))
    meta={'case':case,'nodes_original':n0,'edges_original':e0,'routing_nodes':len(H),
          'routing_edges':H.number_of_edges(),'width_m':W,'length_km':sum(d['length'] for _,_,d in G.edges(data=True))/1000,
          'max_volume_residual':f.max_residual,'flood_seconds':elapsed,
          'last_full_min':max(e.t_full for e in f.E.values())/60,'source':source}
    result=(H,adj,exits,miners,meta)
    with cache.open('wb') as out:pickle.dump(result,out)
    # Portable routing inputs; null means an infinite event time.
    (OUT/f'{case}_routing_input.json').write_text(json.dumps({
        'exits':sorted(exits),'miners':miners,'nodes':{n:H.nodes[n]['xyz'] for n in H},
        'arcs':[[a.a,a.b,a.L,a.wet if math.isfinite(a.wet) else None,
                 a.block if math.isfinite(a.block) else None,*a.speed] for aa in adj.values() for a in aa]},indent=2))
    print('prepared',meta,flush=True)
    return result


def finite(x):return x if math.isfinite(x) else None


def analyse(case):
    H,adj,exits,miners,meta=dataset(case)
    D=latest_network(adj,exits)
    rows=[];curves=[];paths=[];label_stats=[]
    # Named illustrative positions plus an outcome-independent uniform node sample.
    pool=sorted(n for n in H if n not in exits and n not in miners.values() and n!='A')
    sample=random.Random(20261025).sample(pool,40)
    origins=list(miners.items())+[(f'S{i+1:02}',n) for i,n in enumerate(sample)]
    for name,s in origins:
        base,path=fastest(adj,s,exits,T0)
        if not math.isfinite(base):
            rows.append({'case':case,'origin':name,'node':s,'feasible':False})
            continue
        deadline=latest_departure(path)
        row={'case':case,'origin':name,'node':s,'feasible':True,'nominal_arrival_min':base/60,
             'travel_min':(base-T0)/60,'fastest_deadline_min':deadline/60,'network_deadline_min':D[s]/60}
        for eps in [0.,.01,.05,.1]:
            cap=T0+(1+eps)*(base-T0)
            before=time.perf_counter()
            lo,hi,p,queries=budget_deadline(adj,s,exits,T0,cap,D)
            row[f'budget{eps}_deadline_min']=lo/60
            row[f'budget{eps}_upper_min']=hi/60
            row[f'budget{eps}_arrival_min']=walk(p,T0)[0]/60
            row[f'budget{eps}_seconds']=time.perf_counter()-before
            if name.startswith('M'):
                paths.append({'case':case,'origin':name,'eps':eps,'departure_lower_s':lo,
                              'departure_upper_s':hi,'nodes':[s]+[a.b for a in p],
                              'arrival_s':walk(p,T0)[0],'path_deadline_s':latest_departure(p)})
        rows.append(row)
        if name.startswith('M'):
            # Fixed, evenly spaced 0..60 min delay grid, plus model-defined endpoints.
            ds=sorted(set([T0+k*120 for k in range(31)]+[deadline,D[s]-1e-5]))
            for d in ds:
                if d<T0 or d>D[s]+1e-8:continue
                before=time.perf_counter()
                c,p,st=constrained(adj,s,exits,T0,d,D)
                if not math.isfinite(c):continue
                # A one-clock replan-at-d baseline, evaluated at nominal t0.
                _,q=fastest(adj,s,exits,d)
                curves.append({'case':case,'origin':name,'departure_min':d/60,
                    'optimal_nominal_min':c/60,'replan_nominal_min':walk(q,T0)[0]/60,
                    'runtime_s':time.perf_counter()-before,**st})
                label_stats.append(st)
        print(case,name,'done',flush=True)
    return rows,curves,paths,meta


def save_csv(name,rows):
    fields=list(dict.fromkeys(k for row in rows for k in row))
    with (OUT/name).open('w') as f:
        w=csv.DictWriter(f,fields);w.writeheader();w.writerows(rows)


def main():
    OUT.mkdir(exist_ok=True)
    rr=[];cc=[];pp=[];mm=[]
    for case in ['competition','cad']:
        r,c,p,m=analyse(case);rr+=r;cc+=c;pp+=p;mm.append(m)
        save_csv('origins.csv',rr);save_csv('curves.csv',cc)
        (OUT/'selected_paths.json').write_text(json.dumps(pp,indent=2))
        (OUT/'metadata.json').write_text(json.dumps(mm,indent=2))
    tracked=list((PAPER/'code').rglob('*.py'))+list((PAPER/'data').rglob('*.xlsx'))+list((PAPER/'data').rglob('*.json'))
    manifest={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in tracked}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))


if __name__=='__main__':main()
