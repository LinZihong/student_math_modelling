"""Reproduce all numerical results, figures, tests, and provenance.

python code/reproduce.py --fresh     # recompute all flood schedules
python code/reproduce.py            # reuse local trusted caches when present
"""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import platform

HERE=Path(__file__).resolve().parent
PAPER=HERE.parent


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--fresh',action='store_true')
    args=parser.parse_args()
    if args.fresh:
        for name in ['competition_cache.pkl','cad_cache.pkl','competition_menu_schedules.pkl','cad_menu_schedules.pkl']:
            (PAPER/'results'/name).unlink(missing_ok=True)
    commands=[('tests',[sys.executable,'-m','unittest','discover','-s',str(HERE),'-p','test*.py','-v'])]
    commands += [(x,[sys.executable,str(HERE/f'{x}.py')]) for x in ['run','diagnostics','menus','figures','validate']]
    for name,command in commands:
        print('Running',name,flush=True)
        with (PAPER/'results'/f'{name}.log').open('w') as log:
            subprocess.run(command,cwd=PAPER,stdout=log,stderr=subprocess.STDOUT,check=True)
    env={'python':sys.version,'platform':platform.platform(),
         'packages':{p:importlib.metadata.version(p) for p in ['networkx','numpy','pandas','openpyxl','scipy','shapely','matplotlib']}}
    (PAPER/'results/environment.json').write_text(json.dumps(env,indent=2))
    tracked=list((PAPER/'code').rglob('*.py'))+list((PAPER/'data').rglob('*.xlsx'))+list((PAPER/'data').rglob('*.json'))+list((PAPER/'audit').glob('*.py'))
    manifest={str(p.relative_to(PAPER)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(tracked)}
    (PAPER/'results/manifest.json').write_text(json.dumps(manifest,indent=2))


if __name__=='__main__':main()
