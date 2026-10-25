"""Train fixed route menus on eight source nodes; test on eight different nodes.

Equal scenario counts are descriptive design weights, not accident probabilities.
Coverage requires a feasible fixed route whose travel time is <=1.1 times oracle.
Exact enumeration optimizes menus of size 1,2,3 WITHIN training-derived candidates.
"""
import itertools
import json
import math
import pickle
import random
from pathlib import Path
import pandas as pd
from run import OUT,setup,dataset,save_csv,T0
from model.flood import Flood
from model.routing import Arc,fastest,walk

DELAYS=[1.,15.,60.,180.]


def schedule(case):
    cache=OUT/f'{case}_menu_schedules.pkl'
    if cache.exists():
        with cache.open('rb') as f:return pickle.load(f)
    G,source,exits,W,miners,n0,e0=setup(case)
    H,baseline,exits,miners,meta=dataset(case)
    others=random.Random(20261026).sample(sorted(n for n in G if n!=source and n not in exits),15)
    sources=[source]+others
    rows=[]
    for i,s in enumerate(sources):
        f=Flood(G,[(s,0.,.5)],W=W);f.run()
        assert f.max_residual<1e-9
        by_id={G.edges[e.u,e.v]['id']:e for e in f.E.values()}
        adj={}
        for u,v,data in H.edges(data=True):
            e=by_id[data['parent']]
            src,dst=G.nodes[e.src]['xyz'],G.nodes[e.other(e.src)]['xyz']
            for a,b in [(u,v),(v,u)]:
                x,y=H.nodes[a]['xyz'],H.nodes[b]['xyz']
                along=sum((dst[k]-src[k])*(y[k]-x[k]) for k in range(3))>0
                adj.setdefault(a,[]).append(Arc(a,b,data['length'],e.t_in,e.t_block,along))
        rows.append({'source':s,'adj':adj,'split':'train' if i<8 else 'test','residual':f.max_residual})
        print(case,'menu source',i+1,flush=True)
    with cache.open('wb') as out:pickle.dump(rows,out)
    # Explicit scenario identities, independent of outcome.
    (OUT/f'{case}_menu_design.json').write_text(json.dumps({
        'source_seed':20261026,'delay_min':DELAYS,'quality_factor':1.1,
        'sources':[{'node':r['source'],'split':r['split'],'residual':r['residual']} for r in rows]},indent=2))
    return rows


def path_key(p):return tuple((a.a,a.b) for a in p)


def best_menu(masks,k):
    """Exact maximum coverage, deterministic lexicographic tie-breaking."""
    if not masks:return (),0
    k=min(k,len(masks))
    best=();score=-1
    for choice in itertools.combinations(range(len(masks)),k):
        union=0
        for j in choice:union|=masks[j]
        value=union.bit_count()
        if value>score:best,score=choice,value
    return best,score


def main():
    origins=pd.read_csv(OUT/'origins.csv')
    results=[];saved=[];details=[]
    for case in ['competition','cad']:
        scenarios=schedule(case)
        H,baseline,exits,miners,meta=dataset(case)
        cells=[]
        for r in scenarios:
            lookup={(a.a,a.b):a for aa in r['adj'].values() for a in aa}
            for t in DELAYS:cells.append({**r,'time':t*60,'lookup':lookup})
        for row in origins[origins['case']==case].itertuples():
            s=row.node
            oracle=[];pool=set()
            for c in cells:
                arrival,p=fastest(c['adj'],s,exits,c['time'])
                oracle.append(arrival)
                if c['split']=='train' and p:pool.add(path_key(p))
            candidates=sorted(pool)
            masks=[];testmasks=[];feasmasks=[]
            train_possible=sum(math.isfinite(a) for a,c in zip(oracle,cells) if c['split']=='train')
            test_possible=sum(math.isfinite(a) for a,c in zip(oracle,cells) if c['split']=='test')
            for p in candidates:
                train=test=feas=0
                for i,(a,c) in enumerate(zip(oracle,cells)):
                    if not math.isfinite(a):continue
                    actual=walk([c['lookup'][uv] for uv in p],c['time'])[0]
                    if c['split']=='test' and math.isfinite(actual):feas|=1<<i
                    if math.isfinite(actual) and actual-c['time']<=1.1*(a-c['time'])+1e-7:
                        if c['split']=='train':train|=1<<i
                        else:test|=1<<i
                masks.append(train);testmasks.append(test);feasmasks.append(feas)
            _,base=fastest(baseline,s,exits,T0)
            base_test=0
            if base:
                for i,(a,c) in enumerate(zip(oracle,cells)):
                    if c['split']=='test' and math.isfinite(a):
                        actual=walk([c['lookup'][uv] for uv in path_key(base)],c['time'])[0]
                        base_test+=int(math.isfinite(actual) and actual-c['time']<=1.1*(a-c['time'])+1e-7)
            for k in [1,2,3]:
                choice,score=best_menu(masks,k)
                test=feas=0
                for j in choice:test|=testmasks[j];feas|=feasmasks[j]
                results.append({'case':case,'origin':row.origin,'node':s,'k':k,'candidates':len(candidates),
                    'train_possible':train_possible,'train_covered':score,'test_possible':test_possible,
                    'test_covered':test.bit_count(),'test_feasible':feas.bit_count(),'nominal_route_test_covered':base_test})
                saved.append({'case':case,'origin':row.origin,'k':k,'routes':[[s]+[v for u,v in candidates[j]] for j in choice]})
                for i,(a,c) in enumerate(zip(oracle,cells)):
                    if c['split']=='test':
                        details.append({'case':case,'origin':row.origin,'source':c['source'],'delay_min':c['time']/60,
                            'k':k,'oracle_feasible':math.isfinite(a),'covered':bool(test&(1<<i)),
                            'route_exists':bool(feas&(1<<i))})
            print(case,'menu origin',row.origin,flush=True)
        save_csv('menus.csv',results);save_csv('menu_test_cells.csv',details)
        (OUT/'menus_paths.json').write_text(json.dumps(saved,indent=2))


if __name__=='__main__':main()
