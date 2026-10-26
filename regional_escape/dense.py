"""Post-screen exhaustive SE-node stress test, competition network, fixed P0104 routes."""
import json,sys,math
from pathlib import Path
from prepare import setup,Flood,arcs,OUT
from model.routing import latest_departure

def main():
 case='competition';region='SE';G,_,exits,W,*_=setup(case);design=json.loads((OUT/case/'design.json').read_text());mx,my=design['median_xy']
 sources=[n for n in sorted(G) if n not in exits and n!='A' and G.nodes[n]['xyz'][0]>=mx and G.nodes[n]['xyz'][1]<my]
 dest=OUT/'dense_SE';dest.mkdir(exist_ok=True)
 r=next(x for x in json.loads((OUT/'results.json').read_text()) if x['case']==case and x['region']==region and x['node']=='P0104' and x['eps']==.05)
 results=[]
 for i,s in enumerate(sources):
  p=dest/f'{s}.json'
  if p.exists():data=json.loads(p.read_text())
  else:
   f=Flood(G,[(s,0.,.5)],W=W);f.run();adj=arcs(f)
   data={'source':s,'max_volume_residual':f.max_residual,'arcs':[[a.a,a.b,a.L,a.wet,a.block,*a.speed] for aa in adj.values() for a in aa]}
   p.write_text(json.dumps(data))
  from model.routing import Arc
  lookup={(a,b):Arc(a,b,L,wet,block,True,(vd,vw,vw)) for a,b,L,wet,block,vd,vw in data['arcs']}
  values={k:latest_departure([lookup[u,v] for u,v in zip(r[k],r[k][1:])]) for k in ['baseline_path','path']}
  results.append({'source':s,**values,'original_design':s in design['regions'][region][:8],'original_heldout':s in design['regions'][region][8:]})
  if i%25==0:print('dense',i+1,'/',len(sources),flush=True)
  (OUT/'dense_results.json').write_text(json.dumps(results,indent=2))
 print('dense done',len(results),'worst',min(x['baseline_path'] for x in results),min(x['path'] for x in results),flush=True)
if __name__=='__main__':main()
