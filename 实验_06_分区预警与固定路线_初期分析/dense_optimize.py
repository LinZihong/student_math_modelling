import json,math
import networkx as nx
from study import OUT,Arc,latest_network,deadline,optimize

def main():
 d=json.loads((OUT/'competition/design.json').read_text());G=nx.Graph();G.add_weighted_edges_from(sorted(d['edges']));exits=set(d['exits']);dist,paths=nx.multi_source_dijkstra(G,sorted(exits));s='P0104';base=paths[s][::-1]
 results=[]
 for speeds in [(4.,2.,1.),(1.3,.7,.5)]:
  ss=[]
  for file in sorted((OUT/'dense_SE').glob('*.json')):
   data=json.loads(file.read_text());adj={};look={}
   for a,b,L,wet,block,vd,vw in data['arcs']:
    arc=Arc(a,b,L,wet,block,True,(speeds[0],speeds[1] if vw==2 else speeds[2],1));adj.setdefault(a,[]).append(arc);look[a,b]=arc
   ss.append((adj,look,latest_network(adj,exits)))
  for eps in [0.,.05,.1,.2]:
   r=optimize(s,exits,ss,dist,dist[s]*(1+eps));r.update(speeds=speeds,eps=eps,sources=len(ss),baseline_deadline_s=deadline(base,ss),baseline_length_m=dist[s],exact_source_upper_s=min(x[2][s] for x in ss))
   if r['status']=='solved':r.update(actual_deadline_s=deadline(r['path'],ss),length_m=sum(G[u][v]['weight'] for u,v in zip(r['path'],r['path'][1:])))
   results.append(r);(OUT/'dense_optimum.json').write_text(json.dumps(results,indent=2));print({k:v for k,v in r.items() if k!='path'},flush=True)
if __name__=='__main__':main()
