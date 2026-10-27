import json,csv,collections
from pathlib import Path
import numpy as np
OUT=Path(__file__).resolve().parent

def main():
 rows=[];examples=[]
 for p in sorted(OUT.glob('*_*.jsonl')):
  data=[json.loads(line) for line in p.read_text().splitlines()]
  if len(data)!=4761:raise ValueError(f'Incomplete {p}: {len(data)}')
  assert len({(r['node'],r['target_s']) for r in data})==4761
  for t in [600,1200,1800]:
   for group in ['all','outside','inside']:
    a=[r for r in data if r['target_s']==t and (group=='all' or r['inside_region']==(group=='inside'))]
    solved=[r for r in a if r['status']=='solved'];rescued=[r for r in solved if r['baseline_s']<t-1e-7]
    row=dict(source_set=a[0]['source_set'],region=a[0]['region'],source_count=a[0]['source_count'],target_min=t//60,group=group,n=len(a),baseline=sum(r['baseline_s']>=t for r in a),unlimited=len(solved),rescued=len(rescued))
    for cap in [.05,.1,.2,.5,1.]:row[f'cap_{int(cap*100)}']=sum(r['extra_fraction']<=cap+1e-8 for r in solved)
    for status in ['impossible_even_with_source_known','no_common_route','timeout']:row[status]=sum(r['status']==status for r in a)
    row['median_rescue_extra_pct']=float(np.median([r['extra_fraction']*100 for r in rescued])) if rescued else None
    row['max_rescue_length_m']=max((r['length_m'] for r in rescued),default=None)
    rows.append(row)
   if t==1800:
    candidates=[r for r in data if r['target_s']==t and r['status']=='solved' and r['baseline_s']<t and not r['inside_region']]
    candidates.sort(key=lambda r:(r['extra_fraction']>.5,-(min(t,r['deadline_s'])-max(0,r['baseline_s'])),r['extra_fraction']))
    if candidates:examples.append(candidates[0])
 (OUT/'summary.json').write_text(json.dumps(rows,indent=2));(OUT/'examples.json').write_text(json.dumps(examples,indent=2))
 with (OUT/'summary.csv').open('w') as f:
  w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 for r in rows:
  if r['group']=='outside':print(r)

if __name__=='__main__':main()
