"""Checks on the v9 results; writes verification.json.

1. The quadrant runs reproduce 实验_07 exactly at 10, 20 and 30 minutes.
2. Logical consistency of every record: the robust route is the shortest protected route, so it must
   exist whenever the shortest or zone-avoiding route is protected, and be no longer than either;
   it can exist only if the exact-source bound allows it.
3. Nested zones: a route protected for a zone is protected for each half of it, so finer
   bisection levels can never protect fewer starting points.
4. Independent forward walks of sampled robust and zone-avoiding routes against every zone source.
"""
import json,math,random
import numpy as np
import core
from core import OUT,SOURCES,E7
from run_experiments import tasks
from model.routing import walk

TOL=1e-6

def load(t):
 return np.load(OUT/'results'/t['exp']/(t['id']+'.npz'))

def main():
 todo,P=tasks();report={}
 # 1. Regression against 实验_07.
 mism=0;compared=0
 for zi,name in enumerate(['NW','SW','SE','NE']):
  t=next(t for t in todo if t['exp']=='E1_delay' and t['zone']==zi);r=load(t);taus=list(r['taus'])
  old=[json.loads(l) for l in (E7/f'full_{name}.jsonl').read_text().splitlines()]
  for o in old:
   i=taus.index(o['target_s']//60);j=SOURCES.index(o['node']);compared+=1
   st={'solved':0,'no_common_route':1,'impossible_even_with_source_known':2}[o['status']]
   if r['status'][i,j]!=st or (st==0 and abs(r['length'][i,j]-o['length_m'])>TOL) or abs(r['baseline'][j]-o['baseline_s'])>1e-6:mism+=1
 report['regression_vs_experiment_07']=dict(compared=compared,mismatches=mism)
 # 2. Consistency of every record.
 bad=dict(missing_robust=0,robust_longer=0,exceeds_exact=0,deadline_below_target=0,timeouts=0);records=0
 for t in todo:
  r=load(t)
  for i,tau in enumerate(r['taus']):
   T=tau*60.;st=r['status'][i];records+=len(st);bad['timeouts']+=int((st==3).sum())
   solved=st==0;base=r['baseline']>=T-1e-7;avoid=r['avoid_deadline']>=T-1e-7
   bad['missing_robust']+=int(((base|avoid)&~solved).sum())
   L=r['length'][i]
   bad['robust_longer']+=int((solved&base&(L>r['shortest']+TOL)).sum()+(solved&avoid&(L>r['avoid_length']+TOL)).sum())
   bad['exceeds_exact']+=int((solved&(r['exact']<T-1e-7)).sum())
   bad['deadline_below_target']+=int((solved&(r['deadline'][i]<T-1e-7)).sum())
 report['record_consistency']=dict(records=records,**bad)
 # 3. Nested bisection levels.
 viol=0;pairs=0
 for v in [0,1,2]:
  for k in [2,4,8,16,32,64]:
   for zi in range(k):
    parent=f'zones_k{k}_v{v}';child=f'zones_k{2*k}_v{v}'
    tp=next(t for t in todo if t['exp']=='E2_resolution' and t['part']==parent and t['zone']==zi)
    rp=load(tp);i=list(rp['taus']).index(30);ok=rp['status'][i]==0
    for c in [2*zi,2*zi+1]:
     if not P[child][c]:continue
     assert set(P[child][c])<=set(P[parent][zi])
     tc=next(t for t in todo if t['exp']=='E2_resolution' and t['part']==child and t['zone']==c);rc=load(tc)
     viol+=int((ok&(rc['status'][list(rc['taus']).index(30)]!=0)).sum());pairs+=1
 report['nested_zones']=dict(parent_child_pairs=pairs,violations=viol)
 # 4. Independent forward walks.
 F=core.Fields();rng=random.Random(20261028);checks=0;fails=0
 for t in [t for t in todo if t['exp']=='E1_delay']:
  zone=P[t['part']][t['zone']];d=core.zone_dataset(F,zone);paths=json.loads((OUT/'results'/t['exp']/(t['id']+'_paths.json')).read_text());r=load(t);i=list(r['taus']).index(30)
  for kind in ['robust','avoid']:
   names=sorted(paths[kind]);sample=rng.sample(names,8)
   for o in sample:
    # Leaving just before the computed deadline must work for every source; leaving one second
    # after it must fail for at least one source.
    p=paths[kind][o];j=SOURCES.index(o);dl=r['deadline'][i,j] if kind=='robust' else r['avoid_deadline'][j]
    if not 0<=dl<1e7:continue
    late=[]
    for k in range(len(zone)):
     _,look=d.lookup(k);arcs=[look[a,b] for a,b in zip(p,p[1:])]
     fails+=int(not math.isfinite(walk(arcs,dl-1e-6)[0]));late.append(math.isfinite(walk(arcs,dl+1.)[0]));checks+=1
    fails+=int(all(late))
 report['forward_walks']=dict(checks=checks,failures=fails)
 report['passed']=mism==0 and all(v==0 for k,v in bad.items() if k!='timeouts') and viol==0 and fails==0
 report['note']='Timed-out queries are unresolved, counted as unprotected in every summary, and not treated as failures of the checks.'
 (OUT/'verification.json').write_text(json.dumps(report,indent=1));print(json.dumps(report,indent=1))

if __name__=='__main__':main()
