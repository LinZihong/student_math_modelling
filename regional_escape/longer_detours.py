"""Larger length budgets on same frozen origin-region panel; dense-node replication."""
import json,math,random
import networkx as nx
from study import OUT,fields,deadline,optimize,Arc,latest_network

def graph(case):
 d=json.loads((OUT/case/'design.json').read_text());G=nx.Graph();G.add_weighted_edges_from(sorted(d['edges']));exits=set(d['exits']);dist,paths=nx.multi_source_dijkstra(G,sorted(exits));return d,G,exits,dist,paths

def solve(s,eps,ss,G,exits,dist):
 cap=math.inf if eps is None else dist[s]*(1+eps)
 r=optimize(s,exits,ss,dist,cap);r.update(node=s,eps=eps,shortest_length_m=dist[s])
 if r['status']=='solved':
  r['deadline_s']=deadline(r['path'],ss);r['length_m']=sum(G[u][v]['weight'] for u,v in zip(r['path'],r['path'][1:]));assert r['length_m']<=cap+1e-6 and r['deadline_s']>=r['lower']-1e-6
 return r

def screen():
 old=json.loads((OUT/'results.json').read_text());rows=[]
 for case in ['competition','cad']:
  d,G,exits,dist,paths=graph(case)
  for region in d['regions']:
   ss=fields(case,region)
   for base in [x for x in old if x['case']==case and x['region']==region and x['eps']==0]:
    s=base['node']
    for eps in [.5,1.,None]:
     r=solve(s,eps,ss[:8],G,exits,dist);r.update(case=case,region=region,baseline_train_s=base['baseline_train_s'],baseline_test_s=base['baseline_test_s'])
     if r['status']=='solved':r['heldout_deadline_s']=deadline(r['path'],ss[8:])
     rows.append(r)
   (OUT/'longer_screen.json').write_text(json.dumps(rows,indent=2));print('larger budgets',case,region,flush=True)

def dense():
 d,G,exits,dist,paths=graph('competition');ss=[];sources=[]
 for file in sorted((OUT/'dense_SE').glob('*.json')):
  data=json.loads(file.read_text());sources.append(data['source']);adj={};lookup={}
  for a,b,L,w,bk,vd,vw in data['arcs']:
   arc=Arc(a,b,L,w,bk,True,(1.3,.7 if vw==2 else .5,1));adj.setdefault(a,[]).append(arc);lookup[a,b]=arc
  ss.append((adj,lookup,latest_network(adj,exits)))
 buckets={'low':[],'immediate':[],'ceiling':[]};base={}
 for s in sorted(set(G)-set(sources)-exits-{'A'}):
  b=deadline(paths[s][::-1],ss);base[s]=b;buckets['immediate' if b<0 else 'low' if b<3600 else 'ceiling'].append(s)
 rng=random.Random(20261031);selected=rng.sample(buckets['low'],min(12,len(buckets['low'])))+rng.sample(buckets['immediate'],min(4,len(buckets['immediate'])))
 if 'P0104' not in selected:selected.append('P0104')
 (OUT/'longer_dense_design.json').write_text(json.dumps({'sources':sources,'speeds':[1.3,.7,.5],'counts':{k:len(v) for k,v in buckets.items()},'selected':selected,'seed':20261031,'note':'Selected on baseline only; P0104 retained separately as previous illustrative case; source region excluded from worker origins.'},indent=2))
 rows=[]
 for s in selected:
  for eps in [0.,.05,.2,.5,1.,None]:
   r=solve(s,eps,ss,G,exits,dist);r['baseline_s']=base[s];r['exact_source_upper_s']=min(x[2][s] for x in ss);rows.append(r)
  (OUT/'longer_dense.json').write_text(json.dumps(rows,indent=2));print('dense larger budgets',s,flush=True)
if __name__=='__main__':screen();dense()
