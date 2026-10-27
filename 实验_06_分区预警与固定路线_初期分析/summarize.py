import json,hashlib,math
from pathlib import Path
OUT=Path(__file__).resolve().parent
r=json.loads((OUT/'results.json').read_text());screen=json.loads((OUT/'screen.json').read_text());summary=[]
for case in ['competition','cad']:
 for eps in [.05,.1,.2]:
  a=[x for x in r if x['case']==case and x['eps']==eps and x['baseline_train_s']>=0];b=[x for x in a if x['status']=='solved']
  summary.append({'case':case,'budget':eps,'selected_baseline_feasible_origins':len(a),'design_gain_at_least_1min':sum(x['train_capped_gain_s']>=60 for x in b),'heldout_gain_at_least_1min':sum(x['test_capped_gain_s']>=60 for x in b),'heldout_loss_at_least_1min':sum(x['test_capped_gain_s']<=-60 for x in b)})
assert len(r)==492 and len({(x['case'],x['region'],x['node'],x['eps']) for x in r})==492
assert not any(x['status']=='timeout' for x in r)
dense=json.loads((OUT/'dense_results.json').read_text());opts=json.loads((OUT/'dense_optimum.json').read_text())
assert len(dense)==113 and len(opts)==8
mid=json.loads((OUT/'midpoint_results.json').read_text())
ms=[]
for speeds in [[4.,2.,1.],[1.3,.7,.5]]:
 vals=[v for x in mid for v in x['values'] if v['speeds']==speeds]
 ms.append({'speeds':speeds,'sources':len(vals),'baseline_min_s':min(v['baseline'] for v in vals),'fixed_min_s':min(v['fixed'] for v in vals),'fixed_failed_immediate':sum(v['fixed']<0 for v in vals)})
report={'comparison':summary,'sampled_origin_region_pairs':123,'originally_infeasible_design_pairs':27,'dense_sources':113,'midpoint_checks':ms,'all_solver_calls_completed':True,'limitations':'Finite-scenario, volume-transfer-model result; no continuous-region guarantee or accident probabilities. Dense case selected after screening, not representative prevalence.'}
(OUT/'summary.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
