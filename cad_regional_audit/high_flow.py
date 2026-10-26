import json,time
from engine import Dataset,OUT

def main():
 design=json.loads((OUT/'design.json').read_text());folder=OUT/'high_flow';folder.mkdir(exist_ok=True)
 origins=sorted(set().union(*map(set,design['regions'].values())))
 for region in ['SE','NE','SW','NW']:
  sources=design['regions'][region]
  while not all((OUT/'fields'/f'{s}.npz').exists() for s in sources):time.sleep(5)
  d=Dataset(sources,factor=2.);p=folder/f'{region}.jsonl';done=set()
  if p.exists():done={json.loads(line)['node'] for line in p.read_text().splitlines()}
  with p.open('a') as f:
   for node in origins:
    if node in done:continue
    r=d.solve(node,1800);r.update(region=region,inside_region=node in sources,flow_m3_s=1.)
    f.write(json.dumps(r)+'\n');f.flush()
  print(region,'high-flow optimization complete',flush=True)

if __name__=='__main__':main()
