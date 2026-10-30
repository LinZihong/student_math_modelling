"""Matched exploratory comparison; retaining disagreements is mandatory."""
import json
from pathlib import Path
from fv_trajectory import analyse as fv,OUT as FOUT
from trajectory_audit import analyse as swmm,OUT as SOUT

if __name__=='__main__':
    rows=[]
    for q in [.5,.8,1.,1.2,1.4,1.6,2.]:
        for added in [False,True]:
            f=FOUT/f'added{int(added)}_dx6.25_area16.0_q{q}_end3600.0'.replace('.','p')
            s=SOUT/f'q{q}_added{int(added)}_dx6.25_dt0.125_n0.025_bz0.5'.replace('.','p')
            fr=fv(f);sr=swmm(s)
            best={h:max([p['depth_thresholds'][h]['latest_grid_s'] for p in sr['paths'] if p['depth_thresholds'][h]['latest_grid_s'] is not None],default=None) for h in ['0.2','0.3','0.4']}
            rows.append(dict(q=q,added=added,finite_volume=fr['best'],swmm=best,
                             fv_minimum_peak=fr['minimum_peak_depth'],swmm_minimum_peak=sr['minimum_peak_depth']))
    (FOUT.parent/'matched-hydraulics.json').write_text(json.dumps(rows,indent=2))
    for row in rows:print(row)
