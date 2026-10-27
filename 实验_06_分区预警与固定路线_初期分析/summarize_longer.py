import json,hashlib
from pathlib import Path
OUT=Path(__file__).resolve().parent
rows=json.loads((OUT/'target_guarantees.json').read_text());summary=[]
assert len(rows)==1644 and len({(r['node'],r['target_s']) for r in rows})==1644
assert not any(r['status']=='timeout' for r in rows)
for t in [600,1200,1800]:
 a=[r for r in rows if r['target_s']==t];b=[r for r in a if r['status']=='solved']
 summary.append({'target_min':t/60,'origins':len(a),'baseline_success':sum(r['baseline_deadline_s']>=t for r in a),'success_by_budget':{str(e):sum(r['extra_fraction']<=e+1e-8 for r in b) for e in [.05,.1,.2,.5,1]},'unlimited_success':len(b),'fixed_route_impossible':sum(r['status']=='no_common_route' for r in a),'source_known_impossible':sum(r['status']=='impossible_even_with_source_known' for r in a)})
(OUT/'longer_summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2))
