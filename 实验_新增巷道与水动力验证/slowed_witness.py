"""Depth-responsive witness policies, deliberately not an empirical gait law.

Every spatial step sets v=v0/(1+k*h_current) and holds it until the next
step. Peak depth on that linear trajectory segment is computed exactly
for the saved bilinear hydraulic field. Re-evaluate speed at each step.
"""
from pathlib import Path
import json
import numpy as np
from continuous_certificate import profiles,peak

ROOT=Path(__file__).resolve().parent

def slowed(times,fields,depart=600.,v0=1.,k=4.,ds=1.):
    t=depart;maximum=0.
    for a,b in [('B','C'),('C','E')]:
        reverse=(a,b) not in fields
        x,h=fields[(b,a) if reverse else (a,b)]
        if reverse:x=x[-1]-x[::-1];h=h[:,::-1]
        pos=0.
        while pos<x[-1]-1e-8:
            j=min(int(np.searchsorted(x,pos+1e-8)-1),len(x)-2)
            nxt=min(pos+ds,x[j+1]);dist=nxt-pos
            f=(pos-x[j])/(x[j+1]-x[j]);g=(nxt-x[j])/(x[j+1]-x[j])
            left=(1-f)*h[:,j]+f*h[:,j+1];right=(1-g)*h[:,j]+g*h[:,j+1]
            depth=float(np.interp(t,times,left));v=v0/(1+k*depth)
            if t+dist/v>times[-1]:return dict(status='horizon_exceeded',arrival_lower=t)
            maximum=max(maximum,peak(times,np.array([0.,dist]),np.column_stack([left,right]),t,v))
            t+=dist/v;pos=nxt
    return dict(status='complete',arrival=t,peak_depth=maximum)

if __name__=='__main__':
    folder=ROOT/'results'/'confirmation_v1';cases=json.loads((folder/'results.json').read_text());rows=[]
    for case in cases:
        for model,pair in case['models'].items():
            old=profiles(Path(pair['runs'][0]['metadata']['stem']),model)
            new=profiles(Path(pair['runs'][1]['metadata']['stem']),model)
            lower=float(np.interp(600,new[0],new[2]))
            for k in [2.,4.]:
                answer=slowed(old[0],old[1],k=k)
                rows.append(dict(index=case['index'],model=model,k=k,**answer,
                                 margin=lower-answer['peak_depth'] if answer['status']=='complete' else None))
    report=dict(cases=len(rows),complete=sum(r['status']=='complete' for r in rows),
                positive=sum(r['margin'] is not None and r['margin']>0 for r in rows),
                minimum_margin=min(r['margin'] for r in rows if r['margin'] is not None),details=rows)
    (folder/'slowed_witness.json').write_text(json.dumps(report,indent=2))
    print({k:v for k,v in report.items() if k!='details'})
