"""Post-process saved SWMM outputs; no new hydraulic simulations.

Enumerate every simple B-E path on the synthetic macro graph. Interpolate
node water depth linearly in space/time along walking trajectories. Depth
may recede; do not impose permanent closure. No waiting en route. This is
a discretization audit, not a certified continuous PDE trajectory bound.
"""
import json
from pathlib import Path
import numpy as np
from swmm.toolkit import output
from swmm.toolkit.shared_enum import ElementType, NodeAttribute, Time
from shortcut_screen import OUT

def load(stem):
    meta=json.loads(stem.with_suffix('.json').read_text())
    h=output.init();output.open(h,str(stem.with_suffix('.out')))
    N=output.get_times(h,Time.NUM_PERIODS);step=output.get_times(h,Time.REPORT_STEP)
    times=np.arange(N+1)*step
    depths={}
    for i in range(output.get_proj_size(h)[1]):
        name=output.get_elem_name(h,ElementType.NODE,i)
        depths[name]=np.r_[0.,output.get_node_series(h,i,NodeAttribute.INVERT_DEPTH,0,N-1)]
    output.close(h)
    return meta,times,depths

def macro_paths(meta):
    groups={}
    for r in meta['records']:groups.setdefault(r['corridor'],[]).append(r)
    adj={}
    for k,edges in groups.items():
        a,b=edges[0]['a'],edges[-1]['b']
        adj.setdefault(a,[]).append((b,edges))
        rev=[{**r,'a':r['b'],'b':r['a']} for r in edges[::-1]]
        adj.setdefault(b,[]).append((a,rev))
    paths=[]
    def visit(node,seen,edges):
        if node=='E':paths.append((seen,edges));return
        for dest,seg in adj.get(node,[]):
            if dest not in seen:visit(dest,seen+[dest],edges+seg)
    visit('B',['B'],[])
    return paths

def analyse(stem,speed=1.,sample_step=1.):
    meta,times,depths=load(stem)
    departures=np.arange(0.,2600.01,2.)
    rows=[]
    for names,edges in macro_paths(meta):
        worst=np.zeros(len(departures));offset=0.
        for r in edges:
            duration=r['length']/speed
            # Include endpoints and at most one second between samples.
            fractions=np.linspace(0.,1.,max(2,int(np.ceil(duration/sample_step))+1))
            for fraction in fractions:
                at=departures+offset+fraction*duration
                depth=(1-fraction)*np.interp(at,times,depths[r['a']])+fraction*np.interp(at,times,depths[r['b']])
                worst=np.maximum(worst,depth)
            offset+=duration
        valid=departures+offset<=times[-1]
        row={'route':names,'travel_s':offset,'depth_thresholds':{}}
        row['peak_depth_at_departure']={str(int(d)):float(worst[j]) for j,d in enumerate(departures)
                                        if d in [0,60,180,300,600,900,1200] and valid[j]}
        for threshold in [.2,.3,.4]:
            ok=valid & (worst<threshold)
            row['depth_thresholds'][str(threshold)]={
                'latest_grid_s':float(departures[ok][-1]) if np.any(ok) else None,
                'feasible_departure_count':int(ok.sum()),
                'feasibility_reopens':int(np.sum(np.diff(ok.astype(int))==1)),
                'initial_peak_depth':float(worst[0])}
        rows.append(row)
    origin=depths['B']
    first=np.flatnonzero(origin>=.3)
    return dict(stem=stem.name,speed=speed,sample_step=sample_step,
                origin_first_depth03_s=float(times[first[0]]) if len(first) else None,
                origin_recrossings_below03=int(np.sum(np.diff((origin>=.3).astype(int))==-1)),
                minimum_peak_depth={str(d):min([r['peak_depth_at_departure'][str(d)] for r in rows if str(d) in r['peak_depth_at_departure']],default=None) for d in [0,60,180,300,600,900,1200]},paths=rows)

if __name__=='__main__':
    rows=[]
    for dx,dt in [(25.,.25),(12.5,.25),(6.25,.125),(3.125,.0625),(1.5625,.03125)]:
        for added in [False,True]:
            name=f'q1.4_added{int(added)}_dx{dx}_dt{dt}_n0.025_bz0.5'.replace('.','p')
            rows.append(analyse(OUT/name))
            print(rows[-1],flush=True)
    (OUT/'trajectory-audit.json').write_text(json.dumps(rows,indent=2))
