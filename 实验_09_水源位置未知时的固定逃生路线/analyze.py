"""Summaries of the v9 results; writes summary.json, which the paper's tables and figures read.

Whole-mine metric: every (starting point, source) pair counts once, with all 1,587 sources equally
likely. A pair is protected by a plan if the route the plan assigns for the source's alarm zone is
guaranteed for every source in that zone. Pairs that are not protected split into
"no way out" (even the exact source would not help) and "information-limited" (the exact source
would help, but no single route works for the whole zone).
"""
import json,math,statistics
import numpy as np
import core
from core import OUT,SOURCES,NIDX,E7,DIST,PATHS,EXITS
from run_experiments import tasks
from model.routing import walk

N=len(SOURCES);REG=['NW','SW','SE','NE']

def load(t):return np.load(OUT/'results'/t['exp']/(t['id']+'.npz'))

def single_source(factor):
 """Per-pair matrices (source x origin): exact-source latest departure and shortest-route latest departure."""
 F=core.Fields(factor);d=core.zone_dataset(F,SOURCES);cols=[NIDX[o] for o in SOURCES]
 return d.U[:,cols],d.baseline[:,cols]

def zone_results(todo,exp,part,factor):
 ts=sorted([t for t in todo if t['exp']==exp and t['part']==part and t['factor']==factor],key=lambda t:t['zone'])
 return [(t['zone'],load(t)) for t in ts]

def pair_share(P,part,results,tau,U):
 """Shares of all (origin, source) pairs protected by each plan for a partition at one delay."""
 T=tau*60.;w=np.zeros(N);prot={'shortest':0.,'avoid':0.,'robust':0.};info=0.
 for zi,r in results:
  zone=P[part][zi];i=list(r['taus']).index(tau);m=len(zone)
  prot['shortest']+=m*(r['baseline']>=T-1e-7).sum();prot['avoid']+=m*(r['avoid_deadline']>=T-1e-7).sum();prot['robust']+=m*(r['status'][i]==0).sum()
  rows=[SOURCES.index(s) for s in zone];ok=U[rows]>=T-1e-7
  info+=(ok.sum()-(ok[:, r['status'][i]==0]).sum())
 total=sum(len(z) for z in P[part])*N
 out={k:v/total for k,v in prot.items()};out['information_limited']=info/total
 return out

def quadrant_counts(P,results,tau,part='quadrant'):
 rows=[]
 for zi,r in results:
  T=tau*60.;i=list(r['taus']).index(tau);out=~r['inside'];st=r['status'][i];solved=st==0
  ext=r['length'][i]/r['shortest']-1;base=r['baseline']>=T-1e-7;avoid=r['avoid_deadline']>=T-1e-7
  def c(mask):return int(mask.sum())
  row=dict(region=REG[zi] if part.startswith('quadrant') else zi,sources=len(P[part][zi]),tau=tau)
  for g,m in [('outside',out),('inside',~out)]:
   row[g]=dict(n=c(m),shortest=c(m&base),avoid=c(m&avoid),robust=c(m&solved),no_way_out=c(m&(st==2)),no_common_route=c(m&(st==1)),
    **{f'cap{k}':c(m&solved&(ext<=k/100+1e-8)) for k in [10,20,50,100]},
    shortest_fail_at_onset=c(m&(r['baseline']<0)),shortest_fail_by_delay=c(m&(r['baseline']>=0)&~base),
    newly_protected_onset=c(m&solved&~base&(r['baseline']<0)),
    median_extra_newly=float(np.median(ext[m&solved&~base])) if c(m&solved&~base) else None,
    avoid_median_extra=float(np.median(r['avoid_length'][m]/r['shortest'][m]-1)),
    avoid_newly=c(m&avoid&~base),
    avoid_newly_median_extra=float(np.median((r['avoid_length']/r['shortest']-1)[m&avoid&~base])) if c(m&avoid&~base) else None,
    robust_on_avoid_newly_median_extra=float(np.median(ext[m&avoid&~base])) if c(m&avoid&~base) else None,
    robust_only=c(m&solved&~avoid&~base),
    robust_deadline_median_min=float(np.median(r['deadline'][i][m&solved&~base]))/60 if c(m&solved&~base) else None)
  rows.append(row)
 return rows

def mechanism(P,todo,F):
 """Where the shortest route of an unprotected outside starting point is cut, for quadrant zones at 30 min,
 and whether the robust route ends at a different shaft."""
 out={}
 for zi,name in enumerate(REG):
  t=next(t for t in todo if t['exp']=='E1_delay' and t['zone']==zi);r=load(t);zone=P['quadrant'][zi];d=core.zone_dataset(F,zone)
  paths=json.loads((OUT/'results'/t['exp']/(t['id']+'_paths.json')).read_text())['robust'];i=list(r['taus']).index(30)
  cut=[];other_shaft=0;newly=0;cut_in_zone=0
  for j,o in enumerate(SOURCES):
   if r['inside'][j] or r['baseline'][j]>=1800:continue
   p=PATHS[o][::-1];dl=d.path_deadlines(p);k=int(np.argmin(dl));_,look=d.lookup(k)
   t0=1800.;arr,stuck=walk([look[a,b] for a,b in zip(p,p[1:])],t0)
   if stuck is not None:cut.append(DIST[stuck]);cut_in_zone+=stuck in set(zone)
   if r['status'][i,j]==0:
    newly+=1;other_shaft+=paths[o][-1]!=p[-1]
  out[name]=dict(cut_points=len(cut),cut_median_km_from_shaft=statistics.median(cut)/1000 if cut else None,
   cut_within_1km_of_shaft=sum(c<=1000 for c in cut),cut_inside_zone=cut_in_zone,newly_protected=newly,newly_to_other_shaft=other_shaft)
 return out

def shaft_area(P,todo,radius=300.):
 """How each partition treats the junctions within `radius` m (along the tunnels) of a shaft, and how
 well the robust plan protects the mine when the zone holding most of them raises the alarm (30 min)."""
 area={s for s in SOURCES if DIST[s]<=radius};out={'radius_m':radius,'junctions':len(area),'partitions':{}}
 for part in P:
  if not (part.startswith('zones_') or part.startswith('shaftcut') or part=='quadrant'):continue
  hits=sorted(((len(area&set(z)),i) for i,z in enumerate(P[part]) if area&set(z)),reverse=True);big=hits[0][1]
  t=next(t for t in todo if t['exp']=='E2_resolution' and t['part']==part and t['zone']==big);r=load(t);i=list(r['taus']).index(30)
  out['partitions'][part]=dict(zones_touching=len(hits),largest_share=hits[0][0]/len(area),worst_zone_size=len(P[part][big]),worst_zone_protected=float((r['status'][i]==0).mean()))
 return out

def main():
 todo,P=tasks();S={}
 U1,B1=single_source(1.);U2,B2=single_source(2.)
 def per_pair(U,B,tau):return dict(exact=float((U>=tau*60-1e-7).mean()),shortest=float((B>=tau*60-1e-7).mean()))
 # Delay sweep on quadrants.
 q=zone_results(todo,'E1_delay','quadrant',1.);taus=list(q[0][1]['taus'])
 S['delay']={str(t):dict(counts=quadrant_counts(P,q,t),pairs=pair_share(P,'quadrant',q,t,U1),per_pair=per_pair(U1,B1,t)) for t in taus}
 # Zone resolution.
 S['resolution']={}
 for part in P:
  if not (part.startswith('zones_') or part.startswith('shaftcut') or part=='quadrant'):continue
  res=zone_results(todo,'E2_resolution',part,1.)
  S['resolution'][part]={str(t):pair_share(P,part,res,t,U1) for t in res[0][1]['taus']}
 S['resolution_per_pair']={str(t):per_pair(U1,B1,t) for t in [10,30,60]}
 S['quadrant_vs_bisection4']={p:S['resolution'][p]['30'] for p in ['quadrant','zones_k4_v0','zones_k4_v1','zones_k4_v2']}
 # Source breadth.
 S['breadth']={}
 for b in [50,100,200,500,1000]:
  part=f'quadrant_near{b}';res=zone_results(todo,'E3_breadth',part,1.)
  rows=[SOURCES.index(x) for z in P[part] for x in z]
  S['breadth'][str(b)]=dict(sources=len(rows),counts=quadrant_counts(P,res,30,part),pairs=pair_share(P,part,res,30,U1),
   per_pair=dict(exact=float((U1[rows]>=1800-1e-7).mean()),shortest=float((B1[rows]>=1800-1e-7).mean())))
 # Inflow doubled.
 qf=zone_results(todo,'E4_inflow','quadrant',2.)
 S['inflow']={'quadrant':{str(t):dict(counts=quadrant_counts(P,qf,t),pairs=pair_share(P,'quadrant',qf,t,U2),per_pair=per_pair(U2,B2,t)) for t in [10,30,60]},
  'resolution':{p:pair_share(P,p,zone_results(todo,'E4_inflow',p,2.),30,U2) for p in P if p.startswith('zones_') and p.endswith('_v0')}}
 S['mechanism']=mechanism(P,todo,core.Fields())
 S['shaft_area']=shaft_area(P,todo)
 S['timeouts']=[dict(task=t['id'],tau=int(tau),count=int((r['status'][i]==3).sum())) for t in todo for r in [load(t)] for i,tau in enumerate(r['taus']) if (r['status'][i]==3).any()]
 S['queries']=int(sum(load(t)['status'].size for t in todo))
 (OUT/'summary.json').write_text(json.dumps(S,indent=1,default=lambda o:o.item()));print('summary written')

if __name__=='__main__':main()
