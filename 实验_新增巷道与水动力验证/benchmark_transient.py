"""Ritter dry-bed dam-break benchmark for SWMM's transient front accuracy.

Flat 2 km channel, initial depth 1 m left of x=0 and zero to the right.
Compare t=60,100 s before distant boundaries influence the comparison region.
Manning n=0.0001 approximates frictionless flow; not a mine parameter.
"""
import json
from pathlib import Path
import numpy as np
from swmm.toolkit import solver,output
from swmm.toolkit.shared_enum import NodeAttribute,Time

OUT=Path(__file__).resolve().parent/'results'/'transient'
OUT.mkdir(parents=True,exist_ok=True)

def ritter(x,t):
    c=np.sqrt(9.81)
    return np.where(x<=-c*t,1.,np.where(x>=2*c*t,0.,(2*c-x/t)**2/(9*9.81)))

def run(dx,damping='NONE'):
    stem=OUT/f'ritter_dx{dx}_{damping}'.replace('.','p')
    count=int(2000/dx);xs=np.linspace(-1000,1000,count+1)
    lines=['[TITLE]','Ritter benchmark','[OPTIONS]','FLOW_UNITS CMS','FLOW_ROUTING DYNWAVE',
           'START_DATE 01/01/2026','START_TIME 00:00:00','END_DATE 01/01/2026','END_TIME 00:02:00',
           'REPORT_START_DATE 01/01/2026','REPORT_START_TIME 00:00:00','REPORT_STEP 00:00:01',
           'ROUTING_STEP 0.05','VARIABLE_STEP 0',f'INERTIAL_DAMPING {damping}',
           'NORMAL_FLOW_LIMITED BOTH','LENGTHENING_STEP 0','MIN_SURFAREA 0.01',
           'HEAD_TOLERANCE 0.00001','MAX_TRIALS 40','[JUNCTIONS]']
    lines += [f'J{i} 0 3 {1 if x<0 else 0} 0 0' for i,x in enumerate(xs[:-1])]
    lines+=['[OUTFALLS]',f'J{count} 0 FREE NO','[CONDUITS]']
    lines += [f'C{i} J{i} J{i+1} {dx} 0.0001 0 0 0 0' for i in range(count)]
    lines+=['[XSECTIONS]']+[f'C{i} RECT_OPEN 3 4 0 0 1' for i in range(count)]
    lines+=['[REPORT]','NODES ALL','LINKS ALL']
    stem.with_suffix('.inp').write_text('\n'.join(lines)+'\n')
    solver.swmm_run(str(stem.with_suffix('.inp')),str(stem.with_suffix('.rpt')),str(stem.with_suffix('.out')))
    handle=output.init();output.open(handle,str(stem.with_suffix('.out')))
    rows=[];profiles=[]
    for t in [60,100]:
        h=np.array([output.get_node_series(handle,i,NodeAttribute.INVERT_DEPTH,t-1,t-1)[0] for i in range(count)])
        x=xs[:-1];exact=ritter(x,t);mask=np.abs(x)<=700
        rows.append(dict(t=t,mean_absolute_depth_error=float(np.mean(np.abs(h[mask]-exact[mask]))),
                         max_depth=float(h.max()),min_depth=float(h.min()),
                         front_numerical=float(x[h>.01][-1]),front_exact=float(2*np.sqrt(9.81)*t),
                         front_exact_same_depth01=float((2*np.sqrt(9.81)-3*np.sqrt(9.81*.01))*t)))
        profiles.append(dict(t=t,x=x.tolist(),h=h.tolist(),exact=exact.tolist()))
    output.close(handle)
    result=dict(dx=dx,damping=damping,errors=rows)
    stem.with_suffix('.json').write_text(json.dumps(dict(**result,profiles=profiles)))
    return result

if __name__=='__main__':
    rows=[run(dx) for dx in [25.,12.5,6.25]]
    (OUT/'summary.json').write_text(json.dumps(rows,indent=2))
    print(json.dumps(rows,indent=2))
