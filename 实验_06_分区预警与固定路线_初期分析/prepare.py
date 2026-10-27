import sys,json,random,statistics,hashlib,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'论文_04_绕行与延迟容忍_路线菜单探索/code'))
from run import setup
from model.flood import Flood
from model.routing import arcs
OUT=Path(__file__).resolve().parent

def main():
 for case in ['competition','cad']:
  G,_,exits,W,*_=setup(case)
  mx=statistics.median(G.nodes[n]['xyz'][0] for n in G);my=statistics.median(G.nodes[n]['xyz'][1] for n in G)
  regions={k:[] for k in ['SW','NW','SE','NE']}
  for n in sorted(G):
   if n in exits or n=='A':continue
   x,y,_=G.nodes[n]['xyz'];regions[('N' if y>=my else 'S')+('E' if x>=mx else 'W')].append(n)
  rng=random.Random(20261027);design={k:rng.sample(v,16) for k,v in regions.items()}
  dest=OUT/case;dest.mkdir(exist_ok=True)
  record={'case':case,'median_xy':[mx,my],'exits':sorted(exits),'nodes':{n:G.nodes[n]['xyz'] for n in sorted(G)},'edges':[[u,v,d['length']] for u,v,d in G.edges(data=True)],'regions':design,'protocol_sha256':hashlib.sha256((OUT/'protocol.json').read_bytes()).hexdigest()}
  (dest/'design.json').write_text(json.dumps(record,indent=2))
  for region,sources in design.items():
   for i,s in enumerate(sources):
    fpath=dest/f'{region}_{i:02}.json'
    if fpath.exists():continue
    f=Flood(G,[(s,0.,.5)],W=W);f.run();adj=arcs(f)
    assert f.max_residual<1e-9
    import math
    assert all(math.isfinite(a.block) for aa in adj.values() for a in aa)
    fpath.write_text(json.dumps({'source':s,'split':'design' if i<8 else 'heldout','max_volume_residual':f.max_residual,'arcs':[[a.a,a.b,a.L,a.wet,a.block,*a.speed] for aa in adj.values() for a in aa]}))
   print(case,region,'16 source fields ready',flush=True)
if __name__=='__main__':main()
