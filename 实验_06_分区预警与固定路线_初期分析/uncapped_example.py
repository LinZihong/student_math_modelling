import json,math
from longer_detours import graph
from study import OUT,Arc,latest_network,feasible,deadline
_,G,exits,dist,_=graph('competition');ss=[]
for f in sorted((OUT/'dense_SE').glob('*.json')):
 d=json.loads(f.read_text());adj={};look={}
 for a,b,L,w,bk,vd,vw in d['arcs']:
  arc=Arc(a,b,L,w,bk,True,(1.3,.7 if vw==2 else .5,1));adj.setdefault(a,[]).append(arc);look[a,b]=arc
 ss.append((adj,look,latest_network(adj,exits)))
rows=[];s='P0104'
for eps in [.05,.2,.5,1.,None]:
 cap=math.inf if eps is None else dist[s]*(1+eps);lo=0.;hi=min(x[2][s] for x in ss);best=None
 while hi-lo>.5:
  d=(lo+hi)/2;p,_=feasible(s,exits,ss,dist,cap,d)
  if p is None:hi=d
  else:lo=d;best=p
 r={'node':s,'eps':eps,'lower_s':lo,'upper_s':hi,'length_m':sum(G[u][v]['weight'] for u,v in zip(best,best[1:])),'deadline_s':deadline(best,ss),'path':best};rows.append(r);print({k:v for k,v in r.items() if k!='path'},flush=True)
(OUT/'uncapped_example.json').write_text(json.dumps(rows,indent=2))
