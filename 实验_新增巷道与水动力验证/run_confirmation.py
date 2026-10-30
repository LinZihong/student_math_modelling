"""Execute the frozen factorial without selecting successes."""
import hashlib,itertools,json
from pathlib import Path
from shortcut_screen import simulate
from network_fv import experiment
from trajectory_audit import analyse as swmm_read
from fv_trajectory import analyse as fv_read

ROOT=Path(__file__).resolve().parent
protocol=ROOT/'confirmation_protocol.json'
raw=protocol.read_bytes();plan=json.loads(raw);keys=list(plan['factorial'])
out=ROOT/'results'/'confirmation_v1';out.mkdir(parents=True,exist_ok=True)
manifest={'protocol_sha256':hashlib.sha256(raw).hexdigest(),'protocol':plan}
(out/'protocol_snapshot.json').write_text(json.dumps(manifest,indent=2))
results=[]
for index,values in enumerate(itertools.product(*(plan['factorial'][k] for k in keys))):
    pars=dict(zip(keys,values));tag=f'confirm{index:02}'
    row={'index':index,'parameters':pars,'models':{}}
    for name,run,read in [('fv',experiment,fv_read),('swmm',simulate,swmm_read)]:
        pair=[]
        for added in [False,True]:
            kwargs=dict(pars,added=added,dx=plan['dx'],tag=tag)
            if name=='fv':kwargs['area']=plan['fv_chamber_area']
            else:kwargs['dt']=plan['swmm_dt']
            metadata=run(**kwargs);analysis=read(Path(metadata['stem']))
            pair.append({'metadata':metadata,'analysis':analysis})
        differences={str(t):pair[1]['analysis']['minimum_peak_depth'][str(t)]-pair[0]['analysis']['minimum_peak_depth'][str(t)] for t in [0,600]}
        row['models'][name]={'runs':pair,'difference_m':differences,
            'predicted_reversal':differences['0']<=-.02 and differences['600']>=.02}
    row['both_models_reversal']=all(r['predicted_reversal'] for r in row['models'].values())
    results.append(row)
    (out/f'case_{index:02}.json').write_text(json.dumps(row,indent=2))
    (out/'results.json').write_text(json.dumps(results,indent=2))
    print('COMPLETED',index,pars,{n:r['difference_m'] for n,r in row['models'].items()},flush=True)
