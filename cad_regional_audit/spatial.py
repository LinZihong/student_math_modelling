import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import networkx as nx
import numpy as np
from engine import OUT

def main():
 d=json.loads((OUT/'design.json').read_text());xy={n:v[:2] for n,v in d['nodes'].items()};G=nx.Graph();G.add_weighted_edges_from(d['arcs']);edges=[(a,b) for a,b in G.edges]
 weights={n:sum(G[n][v]['weight']/2 for v in G[n]) for n in G};stats=[]
 fig,axes=plt.subplots(2,2,figsize=(12,12))
 for ax,region in zip(axes.flat,['SW','NW','SE','NE']):
  rows=[json.loads(s) for s in (OUT/f'full_{region}.jsonl').read_text().splitlines()];rows=[r for r in rows if r['target_s']==1800 and not r['inside_region']]
  rescued={r['node'] for r in rows if r['status']=='solved' and r['baseline_s']<1800}
  components=sorted((sorted(c) for c in nx.connected_components(G.subgraph(rescued))),key=len,reverse=True)
  total=sum(weights[r['node']] for r in rows)
  stats.append(dict(region=region,rescued_nodes=len(rescued),rescued_induced_component_sizes=list(map(len,components)),components=components,weighted_baseline_fraction=sum(weights[r['node']] for r in rows if r['baseline_s']>=1800)/total,weighted_optimized_fraction=sum(weights[r['node']] for r in rows if r['status']=='solved')/total))
  ax.add_collection(LineCollection([[xy[a],xy[b]] for a,b in edges],colors='#d6d6d6',linewidths=.5))
  sx=np.array([xy[n] for n in d['regions'][region]]);ax.scatter(sx[:,0],sx[:,1],s=3,c='#c5a1d7',alpha=.5,label='Candidate sources')
  for label,color,condition in [('Shortest route sufficient','#519c88',lambda r:r['baseline_s']>=1800),('Rescued by rerouting','#df7b20',lambda r:r['node'] in rescued),('No guarantee found (proved)','#b5303c',lambda r:r['status']!='solved')]:
   pts=np.array([xy[r['node']] for r in rows if condition(r)])
   if len(pts):ax.scatter(pts[:,0],pts[:,1],s=10 if color!='#519c88' else 3,c=color,label=label)
  ex=np.array([xy[n] for n in d['exits']]);ax.scatter(ex[:,0],ex[:,1],marker='*',s=65,c='black',label='Exits');ax.set_title(f'{region}: {len(rescued)} rescued outside-region nodes');ax.axis('equal');ax.set_xlabel('CAD x (m)');ax.set_ylabel('CAD y (m)')
 axes[0,0].legend(fontsize=7,loc='best');fig.suptitle('CAD network: fixed regional routes, 30-minute notification delay');fig.tight_layout();fig.savefig(OUT/'spatial_30min.png',dpi=170);plt.close(fig)
 (OUT/'spatial_summary.json').write_text(json.dumps(stats,indent=2))
 # Post-hoc illustrative origin; its route changes exit, not merely a tiny edge.
 rows=[json.loads(s) for s in (OUT/'full_SE.jsonl').read_text().splitlines()];r=next(r for r in rows if r['node']=='P0036' and r['target_s']==1800)
 _,paths=nx.multi_source_dijkstra(G,sorted(d['exits']));baseline=paths[r['node']][::-1]
 fig,ax=plt.subplots(figsize=(9,9));ax.add_collection(LineCollection([[xy[a],xy[b]] for a,b in edges],colors='#ddd',linewidths=.7))
 for path,color,label in [(baseline,'#bf3535','Dry shortest: 6.195 km'),(r['path'],'#087f8c','Fixed regional route: 6.449 km (+4.1%)')]:
  pts=np.array([xy[n] for n in path]);ax.plot(pts[:,0],pts[:,1],color=color,lw=2,label=label)
 origin=xy[r['node']];ax.scatter(*origin,s=60,c='black',zorder=5);ax.annotate('P0036',origin,xytext=(8,8),textcoords='offset points')
 for node in d['exits']:ax.scatter(*xy[node],marker='*',s=90,c='black')
 for node,offset in [(baseline[-1],(-48,-20)),(r['path'][-1],(12,12))]:ax.annotate(node,xy[node],xytext=offset,textcoords='offset points',fontsize=9)
 ax.axis('equal');ax.legend();ax.set_title('Two fixed routes from P0036 under an SE alarm');ax.set_xlabel('CAD x (m)');ax.set_ylabel('CAD y (m)');fig.tight_layout();fig.savefig(OUT/'case_P0036.png',dpi=170);plt.close(fig)

if __name__=='__main__':main()
