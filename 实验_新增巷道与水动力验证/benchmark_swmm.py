"""First gate: steady uniform rectangular-channel flow, not mine validation.

Run with swmm-toolkit 0.17.0; preserves all inputs, reports, and binary outputs.
"""
from pathlib import Path
import json
from swmm.toolkit import solver, output
from swmm.toolkit.shared_enum import LinkAttribute, Time

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'results' / 'benchmark'
OUT.mkdir(parents=True, exist_ok=True)

def normal_depth(q, width, slope, roughness):
    lo, hi = 0., 3.
    for _ in range(100):
        h = (lo+hi)/2
        flow = width*h*(width*h/(width+2*h))**(2/3)*slope**.5/roughness
        if flow < q: lo = h
        else: hi = h
    return (lo+hi)/2

def run(q=.5, slope=.005, roughness=.025, segments=10, step=.5):
    stem=OUT/f'q{q}_s{slope}_n{roughness}_m{segments}_dt{step}'.replace('.', 'p')
    length=500.; dx=length/segments; h=normal_depth(q,4.,slope,roughness)
    lines=['[TITLE]','Uniform rectangular channel verification','[OPTIONS]',
           'FLOW_UNITS CMS','FLOW_ROUTING DYNWAVE','START_DATE 01/01/2026',
           'START_TIME 00:00:00','REPORT_START_DATE 01/01/2026',
           'REPORT_START_TIME 00:00:00','END_DATE 01/01/2026','END_TIME 02:00:00',
           'REPORT_STEP 00:01:00',f'ROUTING_STEP {step}','VARIABLE_STEP 0',
           'NORMAL_FLOW_LIMITED BOTH','[JUNCTIONS]']
    lines += [f'J{i} {slope*(length-i*dx)} 3 {h} 0 0' for i in range(segments)]
    lines += ['[OUTFALLS]',f'J{segments} 0 FIXED {h} NO','[CONDUITS]']
    lines += [f'C{i} J{i} J{i+1} {dx} {roughness} 0 0 {q} 0' for i in range(segments)]
    lines += ['[XSECTIONS]']+[f'C{i} RECT_OPEN 3 4 0 0 1' for i in range(segments)]
    lines += ['[INFLOWS]',f'J0 FLOW "" FLOW 1 1 {q}','[REPORT]','NODES ALL','LINKS ALL']
    stem.with_suffix('.inp').write_text('\n'.join(lines)+'\n')
    solver.swmm_run(str(stem.with_suffix('.inp')),str(stem.with_suffix('.rpt')),str(stem.with_suffix('.out')))
    handle=output.init(); output.open(handle,str(stem.with_suffix('.out')))
    periods=output.get_times(handle,Time.NUM_PERIODS)
    values=output.get_link_series(handle,segments//2,LinkAttribute.FLOW_DEPTH,periods-1,periods-1)
    output.close(handle)
    actual=float(values[-1])
    return dict(q=q,slope=slope,roughness=roughness,segments=segments,step=step,
                analytical_depth=h,simulated_depth=actual,relative_error=abs(actual/h-1))

if __name__=='__main__':
    results=[run(q=q,slope=s) for q in [.5,2.] for s in [.001,.005,.02]]
    (OUT/'summary.json').write_text(json.dumps({'engine':solver.swmm_get_version(),'cases':results},indent=2))
    print(json.dumps(results,indent=2))
