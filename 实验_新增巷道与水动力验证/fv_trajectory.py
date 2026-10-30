"""Interpolate FV cell-center and junction depths along all simple routes."""
import json
import numpy as np
from network_fv import OUT

def analyse(stem,speed=1.):
    meta=json.loads(stem.with_suffix('.json').read_text());data=np.load(stem.with_suffix('.npz'))
    times=data['times'];nodes=list(data['nodes']);adj={};profiles={}
    for i,(a,b,L) in enumerate(meta['corridors']):
        if b=='O':continue # outlet drain is not a second human exit
        x=np.r_[0.,data[f'x{i}'],L]
        h=np.column_stack([data['node_depth'][:,nodes.index(a)],data[f'h{i}'],data['node_depth'][:,nodes.index(b)]])
        profiles[i]=(x,h)
        adj.setdefault(a,[]).append((b,i,False));adj.setdefault(b,[]).append((a,i,True))
    paths=[]
    def dfs(a,names,parts):
        if a=='E':paths.append((names,parts));return
        for b,i,reverse in adj[a]:
            if b not in names:dfs(b,names+[b],parts+[(i,reverse)])
    dfs('B',['B'],[])
    departures=np.arange(0,2600.01,2.);rows=[]
    for names,parts in paths:
        worst=np.zeros(len(departures));offset=0.
        for i,reverse in parts:
            x,h=profiles[i];L=x[-1];duration=L/speed
            for elapsed in np.linspace(0,duration,int(np.ceil(duration))+1):
                location=L-elapsed*speed if reverse else elapsed*speed
                j=min(max(int(np.searchsorted(x,location)-1),0),len(x)-2)
                f=(location-x[j])/(x[j+1]-x[j])
                series=(1-f)*h[:,j]+f*h[:,j+1]
                worst=np.maximum(worst,np.interp(departures+offset+elapsed,times,series))
            offset+=duration
        valid=departures+offset<=times[-1]
        row=dict(path=names,travel_s=offset,latest={})
        row['peak_depth_at_departure']={str(int(d)):float(worst[j]) for j,d in enumerate(departures)
                                        if d in [0,60,180,300,600,900,1200] and valid[j]}
        for threshold in [.2,.3,.4]:
            ok=valid & (worst<threshold)
            row['latest'][str(threshold)]=float(departures[ok][-1]) if np.any(ok) else None
        rows.append(row)
    return dict(stem=stem.name,q=meta['q'],dx=meta['dx'],area=meta['area'],added=meta['added'],speed=speed,
                paths=rows,minimum_peak_depth={str(d):min([r['peak_depth_at_departure'][str(d)] for r in rows if str(d) in r['peak_depth_at_departure']],default=None) for d in [0,60,180,300,600,900,1200]},
                best={str(h):max([r['latest'][str(h)] for r in rows if r['latest'][str(h)] is not None],default=None) for h in [.2,.3,.4]})

if __name__=='__main__':
    stems=sorted(OUT.glob('*_end3600p0.json'))
    rows=[analyse(s.with_suffix('')) for s in stems]
    (OUT/'trajectory-summary.json').write_text(json.dumps(rows,indent=2))
    for r in rows:print({k:v for k,v in r.items() if k!='paths'})
