"""Exploratory coupled-water/pedestrian shortcut screen; not field validation.

Synthetic loop: A-C-E and B-C-E, optional A-B. Water enters A, miner at B.
First crossing of segment-mean depth 0.3 m closes segment permanently.
Walking is constant 1 m/s. All reported deadlines conditional on these rules.
"""
from pathlib import Path
import heapq, json, math, re
from swmm.toolkit import solver, output
from swmm.toolkit.shared_enum import LinkAttribute, Time

OUT=Path(__file__).resolve().parent/'results'/'shortcut_screen'
OUT.mkdir(parents=True,exist_ok=True)

def simulate(q, added, dx=25., dt=.5, roughness=.025, bz=1.5,extra_length=100.,tag=''):
    name=f'q{q}_added{int(added)}_dx{dx}_dt{dt}_n{roughness}_bz{bz}'.replace('.','p')
    if tag:name=tag+'_'+name
    stem=OUT/name
    z={'A':2.,'B':bz,'C':1.,'E':0.,'O':-.2}
    # A-E is short but cannot be used from B without the added cross passage.
    corridors=[('A','E',500.),('A','C',600.),('B','C',500.),('C','E',500.),('E','O',100.)]
    if added: corridors.append(('A','B',extra_length))
    links=[]
    for k,(a,b,length) in enumerate(corridors):
        count=math.ceil(length/dx); last=a
        for j in range(count):
            nxt=b if j==count-1 else f'X{k}_{j}'
            if nxt!=b:z[nxt]=z[a]+(z[b]-z[a])*(j+1)/count
            links.append((f'L{len(links)}',last,nxt,length/count,k));last=nxt
    lines=['[TITLE]','Exploratory synthetic mine shortcut','[OPTIONS]',
           'FLOW_UNITS CMS','FLOW_ROUTING DYNWAVE','START_DATE 01/01/2026',
           'START_TIME 00:00:00','REPORT_START_DATE 01/01/2026',
           'REPORT_START_TIME 00:00:00','END_DATE 01/01/2026','END_TIME 01:00:00',
           'REPORT_STEP 00:00:02',f'ROUTING_STEP {dt}','VARIABLE_STEP 0',
           'NORMAL_FLOW_LIMITED BOTH','[JUNCTIONS]']
    lines += [f'{n} {h} 3 0 0 0' for n,h in z.items() if n!='O']
    lines += ['[OUTFALLS]','O -0.2 FREE NO','[CONDUITS]']
    lines += [f'{i} {a} {b} {length} {roughness} 0 0 0 0' for i,a,b,length,k in links]
    lines += ['[XSECTIONS]']+[f'{i} RECT_CLOSED 3 4 0 0 1' for i,*_ in links]
    lines += ['[INFLOWS]',f'A FLOW "" FLOW 1 1 {q}','[REPORT]','NODES ALL','LINKS ALL']
    stem.with_suffix('.inp').write_text('\n'.join(lines)+'\n')
    solver.swmm_run(str(stem.with_suffix('.inp')),str(stem.with_suffix('.rpt')),str(stem.with_suffix('.out')))
    handle=output.init();output.open(handle,str(stem.with_suffix('.out')))
    periods=output.get_times(handle,Time.NUM_PERIODS)
    step=output.get_times(handle,Time.REPORT_STEP)
    records=[]
    for index,(ident,a,b,length,k) in enumerate(links):
        depths=output.get_link_series(handle,index,LinkAttribute.FLOW_DEPTH,0,periods-1)
        crossing=next((step*(j+1) for j,h in enumerate(depths) if h>=.3),None)
        records.append(dict(id=ident,a=a,b=b,length=length,corridor=k,block=crossing,max_depth=max(depths)))
    output.close(handle)
    report=stem.with_suffix('.rpt').read_text()
    error=float(re.search(r'Continuity Error \(%\)\s*\.+\s*([-\d.]+)',report).group(1))
    result=dict(stem=str(stem),q=q,added=added,dx=dx,dt=dt,roughness=roughness,bz=bz,extra_length=extra_length,continuity_error_pct=error,
                records=records,latest=latest(records),dry_distance=distance(records),
                warnings=[line.strip() for line in report.splitlines() if 'WARNING' in line or 'ERROR' in line])
    stem.with_suffix('.json').write_text(json.dumps(result,indent=2))
    return result

def latest(records):
    # Require arrival by observed horizon; unblocked beyond it is unknown.
    adj={}
    for r in records:
        for a,b in [(r['a'],r['b']),(r['b'],r['a'])]:adj.setdefault(a,[]).append((b,r))
    D={'E':3600.};heap=[(-3600.,'E')]
    while heap:
        val,b=heapq.heappop(heap);val=-val
        if val<D[b]:continue
        for a,r in adj[b]:
            # Lower endpoint of report bracket to avoid optimistic rounding.
            closure=r['block']-2 if r['block'] is not None else 3600.
            candidate=min(val,closure)-r['length']
            if candidate>D.get(a,-math.inf):
                D[a]=candidate;heapq.heappush(heap,(-candidate,a))
    return D['B']

def distance(records):
    return 3600-latest([{**r,'block':None} for r in records])

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--mode',choices=['base','expanded','refinement','fine'],default='base')
    mode=parser.parse_args().mode
    summary=[]
    if mode=='base':settings=[dict(q=q) for q in [.5,1.,2.,4.,8.]]
    elif mode=='expanded':settings=[dict(q=q,bz=bz) for bz in [.5,1.,1.5,2.,3.] for q in [1.2,1.4,1.6]]
    elif mode=='refinement':settings=[dict(q=1.4,bz=.5,dx=dx,dt=dt) for dx,dt in [(25.,.25),(12.5,.25),(6.25,.125)]]
    else:settings=[dict(q=1.4,bz=.5,dx=dx,dt=dt) for dx,dt in [(3.125,.0625),(1.5625,.03125)]]
    for setting in settings:
        for added in [False,True]:
            r=simulate(added=added,**setting)
            summary.append({k:v for k,v in r.items() if k!='records'})
            print(summary[-1],flush=True)
            (OUT/f'{mode}-records.json').write_text(json.dumps(summary,indent=2))
