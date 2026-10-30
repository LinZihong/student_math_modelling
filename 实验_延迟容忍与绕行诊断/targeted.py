import json,csv,math,hashlib
from pathlib import Path
from investigate import load,OUT,ROOT
from model.routing import fastest,latest_departure,walk
from robust import latest_network,constrained
rows=list(csv.DictReader((OUT/'origins.csv').open())); checks=[]
old=list(csv.DictReader((ROOT/'论文_04_绕行与延迟容忍_路线菜单探索/results/origins.csv').open()))
for case in ['competition','cad']:
 data,adj,exits=load(case,1.);D=latest_network(adj,exits)
 for row in rows:
  if row['case']!=case or row['factor']!='1.0' or row['urgent']!='True':continue
  s=row['node'];base,p=fastest(adj,s,exits,60.);b=latest_departure(p)
  out={'case':case,'node':s,'in_original_40_sample':any(x['node']==s and x['case']==case and x['origin'].startswith('S') for x in old),'baseline_travel_min':(base-60)/60,'baseline_deadline_from_inrush_min':b/60,'baseline_tolerance_after_1min_min':(b-60)/60,'network_deadline_from_inrush_min':D[s]/60,'degree':len(adj[s]),'local_latest_exit_bound_min':max(a.latest_entry(math.inf) for a in adj[s])/60,'targets':[]}
  for gain in [1,10,30]:
   d=b+gain*60;c,q,st=constrained(adj,s,exits,60.,d,D)
   target={'additional_tolerance_min':gain,'departure_from_inrush_min':d/60,'feasible':math.isfinite(c)}
   if math.isfinite(c):
    arrival=walk(q,d)[0];best,_=fastest(adj,s,exits,d)
    assert math.isfinite(arrival) and not math.isfinite(walk(p,d)[0])
    target.update(extra_travel_min=(c-base)/60,extra_percent=100*(c-base)/(base-60),nominal_travel_min=(c-60)/60,delayed_travel_min=(arrival-d)/60,delayed_best_travel_min=(best-d)/60,route=[s]+[a.b for a in q])
   out['targets'].append(target)
  # Failure trace of the nominal route ten minutes past its deadline.
  t=b+600;trace=[]
  for a in p:
   end=a.exit_time(t)
   if not math.isfinite(end):
    out['failed_arc_at_plus10']={'from':a.a,'to':a.b,'entry_min':t/60,'block_min':a.block/60};break
   t=end
  checks.append(out)
summary=[]
for factor in ['1.0','2.0','5.0']:
 for case in ['competition','cad']:
  subset=[r for r in rows if r['factor']==factor and r['case']==case and r['urgent']=='True']
  summary.append({'case':case,'time_compression':float(factor),'urgent':len(subset),'gainers':{eps:sum(float(r[f'gain_{eps}_min'])>1/60 for r in subset) for eps in ['0.05','0.1','0.2']}})
report={'targeted_baseline':checks,'summary':summary,'input_sha256':{case:hashlib.sha256((ROOT/f'论文_04_绕行与延迟容忍_路线菜单探索/results/{case}_routing_input.json').read_bytes()).hexdigest() for case in ['competition','cad']}}
(OUT/'targeted.json').write_text(json.dumps(report,indent=2))
for x in checks:
 print({k:v for k,v in x.items() if k!='targets'})
 print([{k:v for k,v in t.items() if k!='route'} for t in x['targets']])
print(summary)
