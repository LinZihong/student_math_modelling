"""How often each plan actually leads a worker into water, averaged over every (starting point, source)
pair, for the quadrant zones at a 30-minute delay; writes realized.json.

A guarantee covers every source in the zone; this complementary measure asks, for the actual source,
whether the assigned route still reaches a shaft. Where no robust route exists, the robust plan falls
back to the zone-avoiding route (or, as a variant, to the shortest route).
"""
import json
import numpy as np
import core
from core import OUT,SOURCES,PATHS
from run_experiments import tasks

def main():
 todo,P=tasks();F=core.Fields();T=1800.;n=len(SOURCES);trapped={k:0 for k in ['shortest','avoid','robust_then_avoid','robust_then_shortest']}
 for zi,zone in enumerate(P['quadrant']):
  d=core.zone_dataset(F,zone);paths=json.loads((OUT/f'results/E1_delay/quadrant_z{zi}_q1.0_paths.json').read_text())
  for o in SOURCES:
   fail={'shortest':d.path_deadlines(PATHS[o][::-1])<T-1e-7,'avoid':d.path_deadlines(paths['avoid'][o])<T-1e-7}
   rob=paths['robust'].get(o)
   for k in ['shortest','avoid']:trapped[k]+=int(fail[k].sum())
   trapped['robust_then_avoid']+=0 if rob else int(fail['avoid'].sum());trapped['robust_then_shortest']+=0 if rob else int(fail['shortest'].sum())
 out={k:v/(n*n) for k,v in trapped.items()};(OUT/'realized.json').write_text(json.dumps(out,indent=1));print(out)
if __name__=='__main__':main()
