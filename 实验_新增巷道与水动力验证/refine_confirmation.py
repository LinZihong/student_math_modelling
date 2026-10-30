"""Post-confirmation numerical diagnostics, not new held-out confirmation.

Cases: first corner0, weak/missed early-benefit corner7, worst late margin15.
"""
import json
from pathlib import Path
import numpy as np
from network_fv import experiment
from shortcut_screen import simulate
from continuous_certificate import profiles,witness_peak

ROOT=Path(__file__).resolve().parent;OUT=ROOT/'results'/'confirmation_refinement'
OUT.mkdir(parents=True,exist_ok=True)
base=json.loads((ROOT/'results/confirmation_v1/results.json').read_text())
settings=[]
for index in [0,7,15]:
    settings.extend([(index,'fv',3.125,16.),(index,'fv',1.5625,16.),(index,'swmm',3.125,16.)])
settings.extend([(15,'fv',3.125,4.),(15,'fv',3.125,64.)])
results=[]
for index,model,dx,area in settings:
    pars=base[index]['parameters'];tag=f'refine{index:02}_{model}_a{int(area)}'
    pair=[]
    for added in [False,True]:
        if model=='fv':meta=experiment(added,dx=dx,area=area,tag=tag,**pars)
        else:meta=simulate(added=added,dx=dx,dt=.0625,tag=tag,**pars)
        pair.append(meta)
    old=profiles(Path(pair[0]['stem']),model);new=profiles(Path(pair[1]['stem']),model)
    origin=float(np.interp(600,new[0],new[2]))
    margins={}
    for speed in [.7,1.,1.3]:margins[str(speed)]=origin-witness_peak(old[0],old[1],['B','C','E'],600,speed)
    row=dict(index=index,model=model,dx=dx,area=area,new_origin_depth=origin,margins=margins,runs=pair)
    results.append(row)
    (OUT/'results.json').write_text(json.dumps(results,indent=2))
    print('COMPLETED',index,model,dx,area,margins,flush=True)
