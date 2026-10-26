"""Sensitivity of already-fixed 30-minute routes; no scenario-specific reselection."""
import json,math
from study import OUT,Arc,latest_departure
from prepare import setup,Flood,arcs

def evaluate(lookup,paths):
 return {s:latest_departure([lookup[a,b] for a,b in zip(p,p[1:])]) for s,p in paths.items()}

def main():
 rows=[r for r in json.loads((OUT/'target_guarantees.json').read_text()) if r['target_s']==1800 and r['status']=='solved'];paths={r['node']:r['path'] for r in rows}
 mins={k:{s:math.inf for s in paths} for k in ['Q0.25','Q0.5','Q1.0','reverse_ties']};G,_,exits,W,*_=setup('competition')
 files=sorted((OUT/'dense_SE').glob('*.json'));details=[]
 for i,file in enumerate(files):
  data=json.loads(file.read_text());src=data['source']
  for label,factor in [('Q0.25',.5),('Q0.5',1.),('Q1.0',2.)]:
   look={(a,b):Arc(a,b,L,w/factor,bk/factor,True,(1.3,.7 if vw==2 else .5,1)) for a,b,L,w,bk,vd,vw in data['arcs']}
   vals=evaluate(look,paths)
   for s,v in vals.items():mins[label][s]=min(mins[label][s],v)
  f=Flood(G,[(src,0.,.5)],W=W,reverse_ties=True);f.run();aa=arcs(f)
  look={(a.a,a.b):Arc(a.a,a.b,a.L,a.wet,a.block,True,(1.3,.7 if a.speed[1]==2 else .5,1)) for seq in aa.values() for a in seq}
  vals=evaluate(look,paths)
  for s,v in vals.items():mins['reverse_ties'][s]=min(mins['reverse_ties'][s],v)
  details.append({'source':src,'reverse_tie_mass_residual':f.max_residual})
  if i%25==0:print('fixed-route sensitivity',i+1,'/',len(files),flush=True)
  (OUT/'paper_sensitivity.json').write_text(json.dumps({'sources_processed':i+1,'route_count':len(paths),'min_deadlines':mins,'source_audit':details},indent=2))
 print({k:sum(v>=1800-1e-7 for v in d.values()) for k,d in mins.items()},flush=True)
if __name__=='__main__':main()
