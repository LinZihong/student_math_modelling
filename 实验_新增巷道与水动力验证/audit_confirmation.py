"""Audit numerical gates and a route-independent origin-depth certificate.

Post-hoc mechanism analysis; not part of the frozen primary prediction.
"""
import hashlib,json,re
from pathlib import Path
import numpy as np
from trajectory_audit import load

ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results'/'confirmation_v1'

def number(pattern,text):
    m=re.search(pattern,text)
    if not m:raise ValueError(pattern)
    return float(m.group(1))

def audit():
    rows=json.loads((OUT/'results.json').read_text())
    frozen=json.loads((OUT/'protocol_snapshot.json').read_text())
    assert hashlib.sha256((ROOT/'confirmation_protocol.json').read_bytes()).hexdigest()==frozen['protocol_sha256']
    result=[]
    for case in rows:
        models={}
        for name,pair in case['models'].items():
            gates=[]
            for run in pair['runs']:
                m=run['metadata'];stem=Path(m['stem'])
                if name=='fv':
                    gates.append(dict(mass_error_m3=m['max_mass_residual_m3'],max_depth=m['max_depth'],
                                      passed=m['max_mass_residual_m3']<1e-6 and m['max_depth']<3))
                else:
                    text=stem.with_suffix('.rpt').read_text()
                    nonconv=number(r'% of Steps Not Converging\s*:\s*([\d.]+)',text)
                    flooding=number(r'Flooding Loss\s*\.+\s*([\d.]+)',text)
                    maximum=max(r['max_depth'] for r in m['records'])
                    passed=abs(m['continuity_error_pct'])<1 and nonconv==0 and flooding==0 and maximum<3
                    gates.append(dict(continuity_error_pct=m['continuity_error_pct'],nonconverging_pct=nonconv,
                                      flooding_report_units=flooding,max_depth=maximum,passed=passed))
            new=Path(pair['runs'][1]['metadata']['stem'])
            if name=='fv':
                data=np.load(new.with_suffix('.npz'));idx=list(data['nodes']).index('B')
                origin=float(np.interp(600,data['times'],data['node_depth'][:,idx]))
                oldpaths=pair['runs'][0]['analysis']['paths']
                witness=next(p for p in oldpaths if p['path']==['B','C','E'])
            else:
                _,times,depths=load(new);origin=float(np.interp(600,times,depths['B']))
                oldpaths=pair['runs'][0]['analysis']['paths']
                witness=next(p for p in oldpaths if p['route']==['B','C','E'])
            oldcost=witness['peak_depth_at_departure']['600']
            models[name]=dict(numerical_gates=gates,origin_depth_new=origin,old_witness_peak=oldcost,
                              certificate_margin_m=origin-oldcost,certificate_above_2cm=origin-oldcost>=.02)
        result.append(dict(index=case['index'],models=models,
                           both_certified=all(m['certificate_above_2cm'] for m in models.values()),
                           all_numerical_gates=all(g['passed'] for m in models.values() for g in m['numerical_gates'])))
    report=dict(cases=len(rows),expected_cases=16,primary_both_reversal=sum(c['both_models_reversal'] for c in rows),
                all_gates_cases=sum(r['all_numerical_gates'] for r in result),both_certified_cases=sum(r['both_certified'] for r in result),details=result)
    (OUT/'audit.json').write_text(json.dumps(report,indent=2))
    print({k:v for k,v in report.items() if k!='details'})

if __name__=='__main__':audit()
