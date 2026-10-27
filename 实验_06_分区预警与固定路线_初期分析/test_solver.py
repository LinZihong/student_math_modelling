import random,math,json
import networkx as nx
from study import feasible,deadline,optimize,OUT
from model.routing import Arc,walk
from robust import latest_network
rng=random.Random(20261029);tested=0
for trial in range(100):
 G=nx.Graph();G.add_nodes_from(range(6))
 for i in range(5):G.add_edge(i,i+1,weight=rng.uniform(1,10))
 for i in range(6):
  for j in range(i+2,6):
   if rng.random()<.4:G.add_edge(i,j,weight=rng.uniform(1,10))
 ss=[]
 for k in range(3):
  adj={};look={}
  for u,v,d in G.edges(data=True):
   wet=rng.uniform(0,20);block=wet+rng.uniform(1,25)
   for a,b in [(u,v),(v,u)]:
    arc=Arc(a,b,d['weight'],wet,block,True,(2.,.7,.7));adj.setdefault(a,[]).append(arc);look[a,b]=arc
  ss.append((adj,look,latest_network(adj,{5})))
 dist=nx.single_source_dijkstra_path_length(G,5);cap=dist[0]*1.5
 candidates=[p for p in nx.all_simple_paths(G,0,5) if sum(G[u][v]['weight'] for u,v in zip(p,p[1:]))<=cap+1e-7]
 for d in [0.,3.,10.,20.]:
  truth=[p for p in candidates if all(math.isfinite(walk([look[u,v] for u,v in zip(p,p[1:])],d)[0]) for _,look,_ in ss)]
  actual,_=feasible(0,{5},ss,dist,cap,d)
  assert bool(truth)==(actual is not None),(trial,d)
  if actual:
   cost=sum(G[u][v]['weight'] for u,v in zip(actual,actual[1:]));best=min(sum(G[u][v]['weight'] for u,v in zip(p,p[1:])) for p in truth)
   assert abs(cost-best)<1e-7
  tested+=1
 best=max(deadline(p,ss) for p in candidates)
 r=optimize(0,{5},ss,dist,cap)
 if best<0:assert r['status']!='solved'
 else:assert r['status']=='solved' and r['lower']<=best+1e-7 and r['upper']>=best-1e-7
(OUT/'solver_tests.json').write_text(json.dumps({'graphs':100,'scenarios_per_graph':3,'feasibility_and_minlength_comparisons':tested,'deadline_optima_bracketed':100,'passed':True},indent=2))
print('400 common-route feasibility/minlength comparisons and 100 deadline brackets passed')
