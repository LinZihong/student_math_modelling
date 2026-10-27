"""Fresh interior-source stress check of the frozen dense-node route; no retraining."""
import json,random,math
from prepare import setup,Flood,arcs,OUT
from model.routing import latest_departure,Arc

def main():
 G,_,exits,W,*_=setup('competition');design=json.loads((OUT/'competition/design.json').read_text());mx,my=design['median_xy']
 eligible=[]
 for u,v in sorted(tuple(sorted(e)) for e in G.edges()):
  x,y,z=[(a+b)/2 for a,b in zip(G.nodes[u]['xyz'],G.nodes[v]['xyz'])]
  if x>=mx and y<my:eligible.append((u,v,(x,y,z)))
 chosen=random.Random(20261030).sample(eligible,min(24,len(eligible)))
 records=json.loads((OUT/'dense_optimum.json').read_text());paths={tuple(r['speeds']):r['path'] for r in records if r['eps']==.05 and r['status']=='solved'}
 import networkx as nx
 baseline=nx.multi_source_dijkstra(G,sorted(exits),target='P0104',weight='length')[1][::-1]
 (OUT/'midpoint_design.json').write_text(json.dumps({'eligible_edges':len(eligible),'seed':20261030,'sources':chosen,'routes':[{'speeds':k,'path':v} for k,v in paths.items()]},indent=2))
 results=[]
 for i,(u,v,xyz) in enumerate(chosen):
  H=G.copy();edge=dict(H.edges[u,v]);H.remove_edge(u,v);H.add_node('midpoint_source',xyz=xyz)
  for n in [u,v]:H.add_edge(n,'midpoint_source',id=edge['id']+'mid'+n,length=edge['length']/2)
  f=Flood(H,[('midpoint_source',0.,.5)],W=W);f.run();aa=arcs(f);lookup={(a.a,a.b):a for arcs0 in aa.values() for a in arcs0}
  def mapped(p):
   out=[p[0]]
   for a,b in zip(p,p[1:]):
    if {a,b}=={u,v}:out.append('midpoint_source')
    out.append(b)
   return out
  record={'edge':[u,v],'mass_residual':f.max_residual,'values':[]}
  for speeds,path in paths.items():
   ls={k:Arc(a.a,a.b,a.L,a.wet,a.block,True,(speeds[0],speeds[1] if a.speed[1]==2 else speeds[2],1.)) for k,a in lookup.items()}
   vals={}
   for label,p in [('baseline',baseline),('fixed',path)]:
    p=mapped(p);vals[label]=latest_departure([ls[a,b] for a,b in zip(p,p[1:])])
   record['values'].append({'speeds':speeds,**vals})
  results.append(record);(OUT/'midpoint_results.json').write_text(json.dumps(results,indent=2))
  if i%8==0:print('midpoints',i+1,flush=True)
 print('midpoints complete',len(results),flush=True)
if __name__=='__main__':main()
