"""Full CAD source-node enumeration; four bounded local worker processes."""
import sys,json,math,time,hashlib,statistics,os
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'论文_04_绕行与延迟容忍_路线菜单探索/code'))
from run import setup
from model.flood import Flood
from model.routing import arcs
OUT=Path(__file__).resolve().parent
NET=None

def init():
 global NET
 NET=setup('cad')

def simulate(source):
 G,_,exits,W,*_=NET
 start=time.monotonic();f=Flood(G,[(source,0.,.5)],W=W);f.run();aa=arcs(f)
 seq=sorted((a for seq in aa.values() for a in seq),key=lambda a:(a.a,a.b))
 wet=np.array([a.wet for a in seq]);block=np.array([a.block for a in seq]);along=np.array([a.speed[1]==2 for a in seq])
 assert np.isfinite(wet).all() and np.isfinite(block).all() and f.max_residual<1e-9
 p=OUT/'fields'/f'{source}.npz';tmp=p.with_suffix('.tmp.npz');np.savez_compressed(tmp,wet=wet,block=block,along=along);tmp.replace(p)
 return {'source':source,'mass_residual':f.max_residual,'elapsed_s':time.monotonic()-start,'reused':False}

def main():
 OUT.joinpath('fields').mkdir(exist_ok=True)
 G,_,exits,W,*_=setup('cad');mx=statistics.median(G.nodes[n]['xyz'][0] for n in G);my=statistics.median(G.nodes[n]['xyz'][1] for n in G)
 sources=sorted(set(G)-exits-{'A'});regions={k:[] for k in ['SW','NW','SE','NE']}
 for n in sources:
  x,y,_=G.nodes[n]['xyz'];regions[('N' if y>=my else 'S')+('E' if x>=mx else 'W')].append(n)
 directed=sorted((a,b,G[a][b]['length']) for a in G for b in G[a]);nodes=sorted(G)
 from shapely.geometry import Point,Polygon
 features=json.loads((ROOT/'论文_04_绕行与延迟容忍_路线菜单探索/data/cad/data/mine_features.json').read_text());polys=[Polygon(p).buffer(0) for p in features['water_outlines']]
 near=[n for n in sources if min(Point(G.nodes[n]['xyz'][:2]).distance(p) for p in polys)<=50]
 design={'nodes':{n:G.nodes[n]['xyz'] for n in nodes},'arcs':directed,'exits':sorted(exits),'regions':regions,'width':W,'median_xy':[mx,my],'annotated_water_near50m':near,'inputs_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'论文_04_绕行与延迟容忍_路线菜单探索/code/model/flood.py',ROOT/'论文_04_绕行与延迟容忍_路线菜单探索/data/cad/data/mine_network.xlsx',ROOT/'论文_04_绕行与延迟容忍_路线菜单探索/data/cad/data/mine_features.json']}}
 (OUT/'design.json').write_text(json.dumps(design,indent=2));print('design',len(sources),{k:len(v) for k,v in regions.items()},'near water annotations',len(near),flush=True)
 results=[]
 if (OUT/'preparation.json').exists():results=json.loads((OUT/'preparation.json').read_text())
 done={x['source'] for x in results};missing=[]
 existing={}
 for p in (ROOT/'实验_06_分区预警与固定路线_初期分析/cad').glob('*_*.json'):
  d=json.loads(p.read_text())
  if 'arcs' in d and 'source' in d:existing[d['source']]=d
 for s in sources:
  if s in done and (OUT/'fields'/f'{s}.npz').exists():continue
  if s in existing:
   d=existing[s];seq=sorted(d['arcs'],key=lambda a:(a[0],a[1]));assert [(a[0],a[1],a[2]) for a in seq]==[tuple(x) for x in directed]
   np.savez_compressed(OUT/'fields'/f'{s}.npz',wet=[a[3] for a in seq],block=[a[4] for a in seq],along=[a[6]==2 for a in seq]);results.append({'source':s,'mass_residual':d['max_volume_residual'],'elapsed_s':0,'reused':True})
  else:missing.append(s)
 (OUT/'preparation.json').write_text(json.dumps(results,indent=2));print('existing',len(results),'new simulations',len(missing),flush=True)
 with ProcessPoolExecutor(max_workers=4,initializer=init) as pool:
  futures={pool.submit(simulate,s):s for s in missing}
  for future in as_completed(futures):
   r=future.result();results.append(r)
   if len(results)%25==0:print('completed',len(results),'/',len(sources),'latest elapsed',round(r['elapsed_s'],2),flush=True)
   (OUT/'preparation.json').write_text(json.dumps(results,indent=2))
 print('PREPARATION COMPLETE',len(results),flush=True)
if __name__=='__main__':main()
