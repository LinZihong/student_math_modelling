"""Reconcile manuscript tables and headline claims with individual stored outcomes."""
import json,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent;D=P.parent/'cad_regional_audit';summary=json.loads((D/'summary.json').read_text());checks=[];total=0
for source in ['full','near']:
 for region in ['NW','SW','SE','NE']:
  a=[json.loads(s) for s in (D/f'{source}_{region}.jsonl').read_text().splitlines()];assert len(a)==4761;assert len({(r['node'],r['target_s']) for r in a})==4761;assert all(r['status']!='timeout' for r in a);total+=len(a)
  for group in ['all','inside','outside']:
   for t in [600,1200,1800]:
    b=[r for r in a if r['target_s']==t and (group=='all' or r['inside_region']==(group=='inside'))];s=next(r for r in summary if r['source_set']==source and r['region']==region and r['group']==group and r['target_min']==t/60)
    assert len(b)==s['n'];assert sum(r['baseline_s']>=t for r in b)==s['baseline'];assert sum(r['status']=='solved' for r in b)==s['unlimited']
    for cap in [5,10,20,50,100]:assert sum(r['status']=='solved' and r['extra_fraction']<=cap/100+1e-8 for r in b)==s[f'cap_{cap}']
    checks.append((source,region,group,t))
for region in ['NW','SW','SE','NE']:
 a=[json.loads(s) for s in (D/'high_flow'/f'{region}.jsonl').read_text().splitlines()];assert len(a)==1587 and len({r['node'] for r in a})==1587;assert all(r['status']!='timeout' for r in a);total+=len(a)
assert total==44436
s=next(r for r in summary if r['source_set']=='full' and r['region']=='NW' and r['group']=='outside' and r['target_min']==30);assert [s[k] for k in ['n','baseline','cap_20','cap_50','cap_100','unlimited']]==[1243,720,812,961,1162,1200]
assert json.loads((D/'stress.json').read_text())['forward_checks']==7935
# Verify stored analysis hashes before relying on them.
audit=json.loads((D/'audit.json').read_text());assert all(hashlib.sha256((D/k).read_bytes()).hexdigest()==v for k,v in audit['file_sha256'].items())
out=P/'audit/revision-2026-10-26';out.mkdir(parents=True,exist_ok=True);(out/'claims-check.json').write_text(json.dumps(dict(queries=total,summary_cells_checked=len(checks),all_terminal=True,analysis_hashes_verified=True,headline_checked=True),indent=2));print('Verified',total,'queries and',len(checks),'summary cells; frozen analysis hashes match')
