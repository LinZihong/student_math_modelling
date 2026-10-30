"""Exact trajectory peak for bilinear space/time reconstructed depth fields.

Exactness is for the saved reconstruction, not the underlying PDE solution.
Within each crossed space-time cell, depth along a constant-speed trajectory
is quadratic. Evaluate endpoints and any interior concave quadratic vertex.
"""
import json
from pathlib import Path
import numpy as np
from trajectory_audit import load

ROOT=Path(__file__).resolve().parent

def peak(times,x,field,depart,speed=1.,reverse=False):
    if reverse:x=x[-1]-x[::-1];field=field[:,::-1]
    end=depart+x[-1]/speed
    assert depart>=times[0] and end<=times[-1]+1e-8
    breaks=np.unique(np.r_[depart+x/speed,times[(times>depart)&(times<end)]])
    def values(t):
        pos=(t-depart)*speed
        j=np.clip(np.searchsorted(x,pos,side='right')-1,0,len(x)-2)
        k=np.clip(np.searchsorted(times,t,side='right')-1,0,len(times)-2)
        a=(pos-x[j])/(x[j+1]-x[j]);b=(t-times[k])/(times[k+1]-times[k])
        return (1-a)*((1-b)*field[k,j]+b*field[k+1,j])+a*((1-b)*field[k,j+1]+b*field[k+1,j+1])
    l=breaks[:-1];r=breaks[1:];m=(l+r)/2
    y0=values(l);ym=values(m);y1=values(r)
    aa=2*(y1+y0-2*ym);bb=y1-y0-aa
    vertex=np.divide(-bb,2*aa,out=np.zeros_like(aa),where=np.abs(aa)>1e-14)
    use=(aa<0)&(vertex>0)&(vertex<1)
    maximum=max(float(y0.max()),float(y1.max()))
    if np.any(use):maximum=max(maximum,float(np.max(aa[use]*vertex[use]**2+bb[use]*vertex[use]+y0[use])))
    return maximum

def profiles(stem,model):
    if model=='swmm':
        meta,times,depth=load(stem);groups={}
        for r in meta['records']:groups.setdefault(r['corridor'],[]).append(r)
        result={}
        for group in groups.values():
            a,b=group[0]['a'],group[-1]['b'];nodes=[a]+[r['b'] for r in group]
            x=np.r_[0.,np.cumsum([r['length'] for r in group])]
            result[(a,b)]=(x,np.column_stack([depth[n] for n in nodes]))
        origin=depth['B']
    else:
        meta=json.loads(stem.with_suffix('.json').read_text());d=np.load(stem.with_suffix('.npz'))
        times=d['times'];nodes=list(d['nodes']);result={}
        for i,(a,b,L) in enumerate(meta['corridors']):
            if b=='O':continue
            x=np.r_[0.,d[f'x{i}'],L]
            h=np.column_stack([d['node_depth'][:,nodes.index(a)],d[f'h{i}'],d['node_depth'][:,nodes.index(b)]])
            result[(a,b)]=(x,h)
        origin=d['node_depth'][:,nodes.index('B')]
    return times,result,origin

def witness_peak(times,fields,path,depart,speed=1.):
    answer=0.;time=depart
    for a,b in zip(path,path[1:]):
        reverse=(a,b) not in fields
        x,h=fields[(b,a) if reverse else (a,b)]
        answer=max(answer,peak(times,x,h,time,speed,reverse));time+=x[-1]/speed
    return answer

def verification():
    # h(x,t)=x(1-t), x=t gives t(1-t) with interior maximum .25.
    times=np.array([0.,1.]);x=np.array([0.,1.]);h=np.array([[0.,1.],[0.,0.]])
    assert abs(peak(times,x,h,0.)-.25)<1e-12
    # Reverse path x=1-t gives (1-t)^2, maximum1 at departure.
    assert abs(peak(times,x,h,0.,reverse=True)-1.)<1e-12

if __name__=='__main__':
    verification();out=ROOT/'results'/'confirmation_v1'
    rows=json.loads((out/'results.json').read_text());records=[]
    for case in rows:
        for model,pair in case['models'].items():
            old=profiles(Path(pair['runs'][0]['metadata']['stem']),model)
            new=profiles(Path(pair['runs'][1]['metadata']['stem']),model)
            for speed in [.7,1.,1.3]:
                upper=witness_peak(old[0],old[1],['B','C','E'],600.,speed)
                lower=float(np.interp(600.,new[0],new[2]))
                records.append(dict(index=case['index'],model=model,speed=speed,old_witness_peak=upper,
                                     new_origin_depth=lower,certified_margin=lower-upper))
    report=dict(records=len(records),positive=sum(r['certified_margin']>0 for r in records),
                above_2cm=sum(r['certified_margin']>=.02 for r in records),
                minimum_margin=min(r['certified_margin'] for r in records),details=records)
    (out/'continuous_certificate.json').write_text(json.dumps(report,indent=2))
    print({k:v for k,v in report.items() if k!='details'})
