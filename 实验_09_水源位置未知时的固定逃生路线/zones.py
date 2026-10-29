"""Alarm-zone partitions and source sets used by the v9 study; writes partitions.json.

Alarm zones of increasing resolution are made by recursive bisection: the mine is cut in two along
a straight line so that both halves hold the same tunnel length, then each half is cut again along
the perpendicular direction, and so on, giving 2, 4, 8, ... zones of equal tunnel length. Each
junction carries half the length of the tunnels that meet it. Variants rotate the first cutting
direction by 0, 60 and 120 degrees. The four median quadrants are kept as a separate partition, and two partitions are cut
deliberately through the shaft cluster.
"""
import json,math,statistics
import numpy as np
from shapely.geometry import Point,Polygon
from core import ROOT,OUT,DESIGN,SOURCES,GRAPH,XYZ

KS=[1,2,4,8,16,32,64,128];ANGLES={0:0.,1:60.,2:120.};BUFFERS=[50,100,200,500,1000]
WEIGHT={s:sum(GRAPH[s][n]['weight'] for n in GRAPH[s])/2 for s in SOURCES}

def bisect(nodes,levels,angle):
 if levels==0:return [sorted(nodes)]
 u=np.array([math.cos(math.radians(angle)),math.sin(math.radians(angle))])
 order=sorted(nodes,key=lambda s:(float(XYZ[s][:2]@u),s));total=sum(WEIGHT[s] for s in order);acc=0.;cut=len(order)
 for i,s in enumerate(order):
  acc+=WEIGHT[s]
  if acc>=total/2:cut=i+1;break
 return bisect(order[:cut],levels-1,angle+90)+bisect(order[cut:],levels-1,angle+90)

def main():
 parts={'quadrant':[sorted(DESIGN['regions'][r]) for r in ['NW','SW','SE','NE']]}
 for v,angle in ANGLES.items():
  for k in KS:
   if k==1 and v>0:continue
   parts[f'zones_k{k}_v{v}']=bisect(SOURCES,int(math.log2(k)),angle)
 # Zones cut on purpose through the shaft cluster: straight lines through the shafts' centroid, across
 # the main roadway (135 deg) for two zones, and both across and along it (45 deg) for four.
 c=np.mean([XYZ[e][:2] for e in DESIGN['exits']],axis=0);dirs={a:np.array([math.cos(math.radians(a)),math.sin(math.radians(a))]) for a in [45,135]}
 side=lambda s,a:float((XYZ[s][:2]-c)@dirs[a])>=0
 parts['shaftcut_k2']=[sorted(s for s in SOURCES if side(s,45)==b) for b in [False,True]]
 parts['shaftcut_k4']=[sorted(s for s in SOURCES if (side(s,45),side(s,135))==k) for k in [(False,False),(False,True),(True,False),(True,True)]]
 features=json.loads((ROOT/'论文_04_绕行与延迟容忍_路线菜单探索/data/cad/data/mine_features.json').read_text())
 polys=[Polygon(p).buffer(0) for p in features['water_outlines']]
 near={s:min(Point(XYZ[s][:2]).distance(p) for p in polys) for s in SOURCES}
 for b in BUFFERS:
  parts[f'quadrant_near{b}']=[[s for s in z if near[s]<=b] for z in parts['quadrant']]
 for name,zs in parts.items():
  flat=[s for z in zs for s in z]
  assert len(flat)==len(set(flat))
  if 'near' not in name:assert sorted(flat)==SOURCES,name
 out={'partitions':parts,'angles_deg':ANGLES,'water_distance_m':near,'median_xy':DESIGN['median_xy'],'junction_weight_m':WEIGHT}
 (OUT/'partitions.json').write_text(json.dumps(out,indent=1))
 for name,zs in parts.items():
  km=[sum(WEIGHT[s] for s in z)/1000 for z in zs]
  print(name,len(zs),'zones; sources',sum(map(len,zs)),'| junctions min/max',min(map(len,zs)),max(map(len,zs)),'| km min/max %.1f/%.1f'%(min(km),max(km)))

if __name__=='__main__':main()
