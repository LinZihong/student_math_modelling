"""All-origin audit of low delay tolerance on retained, uncalibrated hazard schedules."""
import sys,json,math,csv,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'论文_04_绕行与延迟容忍_路线菜单探索/code'))
from model.routing import Arc,fastest,latest_departure,walk
from robust import latest_network,budget_deadline
OUT=Path(__file__).resolve().parent

def load(case,factor):
 data=json.loads((ROOT/f'论文_04_绕行与延迟容忍_路线菜单探索/results/{case}_routing_input.json').read_text());adj={}
 for a,b,L,wet,block,vd,vw in data['arcs']:
  arc=Arc(a,b,L,math.inf if wet is None else wet/factor,math.inf if block is None else block/factor,True,(vd,vw,vw))
  adj.setdefault(a,[]).append(arc)
 return data,adj,set(data['exits'])

def main():
 rows=[];paths=[];counts=[]
 for factor in [1.,2.,5.]:
  for case in ['competition','cad']:
   data,adj,exits=load(case,factor);D=latest_network(adj,exits)
   stats={'case':case,'hazard_time_compression':factor,'origins':0,'infeasible_at_1min':0,'urgent':0,'min_baseline_tolerance_min':None}
   for s in sorted(data['nodes']):
    if s in exits or s=='A':continue
    stats['origins']+=1
    base,p=fastest(adj,s,exits,60.)
    if not math.isfinite(base):stats['infeasible_at_1min']+=1;continue
    b=latest_departure(p);tol=(b-60)/60
    old=stats['min_baseline_tolerance_min'];stats['min_baseline_tolerance_min']=tol if old is None else min(old,tol)
    row={'case':case,'factor':factor,'node':s,'travel_min':(base-60)/60,'baseline_tolerance_min':tol,'network_tolerance_min':(D[s]-60)/60,'unrestricted_gain_upper_min':(D[s]-b)/60,'urgent':tol<=60}
    if tol<=60:
     stats['urgent']+=1
     for eps in [0.,.05,.1,.2]:
      if D[s]-b<=.01:
       lo,hi,q=b,D[s],p
      else:
       lo,hi,q,_=budget_deadline(adj,s,exits,60.,60+(1+eps)*(base-60),D)
      actual=walk(q,60.)[0];deadline=latest_departure(q)
      assert actual<=60+(1+eps)*(base-60)+1e-6
      assert deadline>=lo-1e-6
      assert math.isfinite(walk(q,max(60.,lo-.02))[0])
      row[f'gain_{eps}_min']=max(0,(lo-b)/60)
      row[f'gain_{eps}_upper_min']=max(0,(hi-b)/60)
      row[f'extra_{eps}_min']=(actual-base)/60
      paths.append({'case':case,'factor':factor,'node':s,'eps':eps,'baseline_path':[s]+[a.b for a in p],'selected_path':[s]+[a.b for a in q],'deadline_lower_s':lo,'deadline_upper_s':hi,'baseline_deadline_s':b,'nominal_arrival_s':actual})
    rows.append(row)
   counts.append(stats)
   print(stats,flush=True)
   (OUT/'counts.json').write_text(json.dumps(counts,indent=2))
   (OUT/'paths.json').write_text(json.dumps(paths,indent=2))
   fields=list(dict.fromkeys(k for r in rows for k in r))
   with (OUT/'origins.csv').open('w') as f:
    w=csv.DictWriter(f,fields);w.writeheader();w.writerows(rows)
if __name__=='__main__':main()
