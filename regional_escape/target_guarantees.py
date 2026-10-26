import json,math
from longer_detours import graph
from study import OUT,Arc,latest_network,feasible,deadline

def main():
 d,G,exits,dist,paths=graph('competition');ss=[];sources=[]
 for file in sorted((OUT/'dense_SE').glob('*.json')):
  data=json.loads(file.read_text());sources.append(data['source']);adj={};look={}
  for a,b,L,w,bk,vd,vw in data['arcs']:
   arc=Arc(a,b,L,w,bk,True,(1.3,.7 if vw==2 else .5,1));adj.setdefault(a,[]).append(arc);look[a,b]=arc
  ss.append((adj,look,latest_network(adj,exits)))
 origins=sorted(set(G)-set(sources)-exits-{'A'});rows=[]
 for i,s in enumerate(origins):
  base=deadline(paths[s][::-1],ss);upper=min(x[2][s] for x in ss)
  for t in [600,1200,1800]:
   r={'node':s,'target_s':t,'baseline_deadline_s':base,'shortest_length_m':dist[s],'source_known_upper_s':upper}
   try:
    p,_=feasible(s,exits,ss,dist,math.inf,t)
    if p is None:r['status']='impossible_even_with_source_known' if upper<t-1e-8 else 'no_common_route'
    else:
     length=sum(G[u][v]['weight'] for u,v in zip(p,p[1:]));actual=deadline(p,ss);assert actual>=t-1e-6
     r.update(status='solved',length_m=length,extra_fraction=length/dist[s]-1,deadline_s=actual,path=p)
   except TimeoutError:r['status']='timeout'
   rows.append(r)
  if i%50==0:print('all-origin target check',i+1,'/',len(origins),flush=True)
  if i%50==0 or i==len(origins)-1:(OUT/'target_guarantees.json').write_text(json.dumps(rows,indent=2))
 print('all-origin targets completed',len(rows),flush=True)
if __name__=='__main__':main()
