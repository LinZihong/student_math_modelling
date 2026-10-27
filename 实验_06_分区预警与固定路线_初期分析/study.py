"""Exact finite-scenario length-constrained common-path search; bounded execution explicitly reported."""
import sys,json,math,heapq,random,time,csv
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'论文_04_绕行与延迟容忍_路线菜单探索/code'))
from model.routing import Arc,latest_departure,walk
from robust import latest_network
import networkx as nx
OUT=Path(__file__).resolve().parent

def fields(case,region):
 out=[]
 for i in range(16):
  d=json.loads((OUT/case/f'{region}_{i:02}.json').read_text());adj={};look={}
  for a,b,L,wet,block,vd,vw in d['arcs']:
   arc=Arc(a,b,L,wet,block,True,(vd,vw,vw));adj.setdefault(a,[]).append(arc);look[a,b]=arc
  out.append((adj,look,latest_network(adj,set(json.loads((OUT/case/'design.json').read_text())['exits']))))
 return out

def deadline(path,scenarios):
 return min(latest_departure([lookup[u,v] for u,v in zip(path,path[1:])]) for _,lookup,_ in scenarios)

def feasible(s,exits,scenarios,dist,cap,d,timeout=3.):
 """Shortest common feasible path; dominance by length and each scenario arrival."""
 start=time.monotonic();adj=scenarios[0][0];Ds=[x[2] for x in scenarios]
 if any(d>D.get(s,-math.inf)+1e-8 for D in Ds):return None,0
 labels=[(s,0.,(d,)*len(scenarios),-1)];live=[True];at={s:[0]};q=[(dist[s],0.,0)];expanded=0
 while q:
  if time.monotonic()-start>timeout:raise TimeoutError('search time limit; no infeasibility claim')
  _,cost,i=heapq.heappop(q)
  if not live[i]:continue
  node,_,times,parent=labels[i];expanded+=1
  if node in exits:
   path=[]
   while i>=0:path.append(labels[i][0]);i=labels[i][3]
   return path[::-1],expanded
  for a in adj[node]:
   n=a.b;l=cost+a.L
   if l+dist[n]>cap+1e-7:continue
   tt=tuple(scenarios[k][1][node,n].exit_time(t) for k,t in enumerate(times))
   if any(not math.isfinite(t) or t>Ds[k].get(n,-math.inf)+1e-8 for k,t in enumerate(tt)):continue
   ids=[j for j in at.get(n,[]) if live[j]]
   if any(labels[j][1]<=l and all(x<=y for x,y in zip(labels[j][2],tt)) for j in ids):continue
   for j in ids:
    if l<=labels[j][1] and all(x<=y for x,y in zip(tt,labels[j][2])):live[j]=False
   j=len(labels);labels.append((n,l,tt,i));live.append(True);at[n]=[v for v in ids if live[v]]+[j];heapq.heappush(q,(l+dist[n],l,j))
 return None,expanded

def optimize(s,exits,scenarios,dist,cap):
 hi=min(3600.,min(x[2].get(s,-math.inf) for x in scenarios));lo=0.;calls=0
 if hi<0:return {'status':'immediate_impossible_even_with_exact_source','upper':hi}
 try:
  p,_=feasible(s,exits,scenarios,dist,cap,0.);calls+=1
  if p is None:return {'status':'no_common_route_at_zero','upper':0.}
  best=p
  while hi-lo>.5:
   d=(hi+lo)/2;p,_=feasible(s,exits,scenarios,dist,cap,d);calls+=1
   if p is None:hi=d
   else:lo=d;best=p
  return {'status':'solved','lower':lo,'upper':hi,'path':best,'calls':calls}
 except TimeoutError:
  return {'status':'timeout','calls':calls}

def main():
 results=json.loads((OUT/'results.json').read_text()) if (OUT/'results.json').exists() else [];screens=json.loads((OUT/'screen.json').read_text()) if (OUT/'screen.json').exists() else []
 for case in ['competition','cad']:
  design=json.loads((OUT/case/'design.json').read_text());exits=set(design['exits']);G=nx.Graph()
  G.add_weighted_edges_from(sorted(design['edges']));dist,paths=nx.multi_source_dijkstra(G,sorted(exits))
  exclude=exits|{s for ss in design['regions'].values() for s in ss}|{'A'}
  for region in design['regions']:
   if any(x['case']==case and x['region']==region for x in screens):continue
   ss=fields(case,region);train=ss[:8];test=ss[8:];base={};buckets={'low':[],'immediate':[],'ceiling':[]}
   for s in sorted(set(G)-exclude):
    p=paths[s][::-1];b=deadline(p,train);base[s]=(p,b)
    category='immediate' if b<0 else 'low' if b<3600 else 'ceiling';buckets[category].append(s)
    screens.append({'case':case,'region':region,'node':s,'baseline_train_s':b,'exact_source_upper_s':min(x[2][s] for x in train),'category':category})
   rng=random.Random(20261028);selected=rng.sample(buckets['low'],min(12,len(buckets['low'])))+rng.sample(buckets['immediate'],min(4,len(buckets['immediate'])))
   print(case,region,{k:len(v) for k,v in buckets.items()},'selected',len(selected),flush=True)
   for s in selected:
    bp,b=base[s];bt=deadline(bp,test)
    for eps in [0.,.05,.1,.2]:
     r=optimize(s,exits,train,dist,dist[s]*(1+eps))
     r.update(case=case,region=region,node=s,eps=eps,baseline_length_m=dist[s],baseline_train_s=b,baseline_test_s=bt,baseline_path=bp,exact_source_upper_s=min(x[2][s] for x in train))
     if r['status']=='solved':
      p=r['path'];length=sum(G[u][v]['weight'] for u,v in zip(p,p[1:]));td=deadline(p,train);hd=deadline(p,test)
      assert length<=dist[s]*(1+eps)+1e-6 and td>=r['lower']-1e-6
      assert all(math.isfinite(walk([look[u,v] for u,v in zip(p,p[1:])],max(0,r['lower']-.01))[0]) for _,look,_ in train)
      r.update(length_m=length,train_actual_s=td,test_actual_s=hd,train_capped_gain_s=min(3600,td)-max(0,min(3600,b)),test_capped_gain_s=max(0,min(3600,hd))-max(0,min(3600,bt)),heldout_sources_meeting_design_guarantee=sum(deadline(p,[field])>=r['lower'] for field in test))
     results.append(r)
    (OUT/'results.json').write_text(json.dumps(results,indent=2))
   (OUT/'screen.json').write_text(json.dumps(screens,indent=2))
   print(case,region,'optimization complete',flush=True)
if __name__=='__main__':main()
