"""Re-evaluate frozen 30-minute routes; no re-optimization at changed inflow."""
import json,time
import numpy as np
from engine import Dataset,OUT,walk

def main():
 design=json.loads((OUT/'design.json').read_text());summary=[];checks=0
 for region in ['SE','NE','NW','SW']:
  p=OUT/f'full_{region}.jsonl'
  while not p.exists() or len(p.read_text().splitlines())!=4761:time.sleep(5)
  rows=[json.loads(line) for line in p.read_text().splitlines()];rows=[r for r in rows if r['target_s']==1800 and r['status']=='solved']
  d=Dataset(design['regions'][region]);wet=d.wet.copy();block=d.block.copy()
  rescued=[r for r in rows if r['baseline_s']<1800]
  # Independent forward scalar evaluation of a deterministic sample, all sources.
  for r in sorted(rescued,key=lambda r:r['node'])[::max(1,len(rescued)//5)][:5]:
   length=sum(d.G[a][b]['weight'] for a,b in zip(r['path'],r['path'][1:]));assert abs(length-r['length_m'])<1e-6
   for k in range(len(d.sources)):
    _,lookup=d.lookup(k);arrival=walk([lookup[a,b] for a,b in zip(r['path'],r['path'][1:])],1800)[0]
    assert np.isfinite(arrival);checks+=1
  for factor in [.5,1.,2.]:
   d.wet=wet/factor;d.block=block/factor
   values={r['node']:float(d.path_deadlines(r['path']).min()) for r in rows}
   for group in ['all','outside','inside']:
    group_rows=[r for r in rows if group=='all' or r['inside_region']==(group=='inside')]
    summary.append(dict(region=region,group=group,flow_m3_s=.5*factor,nominal_routes=len(group_rows),retained=sum(values[r['node']]>=1800-1e-7 for r in group_rows),nominal_rescued=sum(r['baseline_s']<1800 for r in group_rows),rescued_retained=sum(values[r['node']]>=1800-1e-7 and r['baseline_s']<1800 for r in group_rows)))
  (OUT/'stress.json').write_text(json.dumps({'rows':summary,'forward_checks':checks},indent=2));print(region,'stress complete, checks',checks,flush=True)

if __name__=='__main__':main()
