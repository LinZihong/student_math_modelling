import json,time,argparse
from engine import Dataset,OUT

def main():
 p=argparse.ArgumentParser();p.add_argument('region');p.add_argument('--near',action='store_true');args=p.parse_args()
 design=json.loads((OUT/'design.json').read_text());members=set(design['regions'][args.region]);sources=sorted(members)
 if args.near:sources=sorted(members.intersection(design['annotated_water_near50m']))
 name=('near_' if args.near else 'full_')+args.region
 if not sources:raise ValueError('Empty source set')
 while not all((OUT/'fields'/f'{s}.npz').exists() for s in sources):time.sleep(5)
 print(name,'loading',len(sources),'sources',flush=True);d=Dataset(sources)
 origins=sorted(set().union(*map(set,design['regions'].values())))
 output=OUT/f'{name}.jsonl';done=set()
 if output.exists():
  for line in output.read_text().splitlines():
   r=json.loads(line);done.add((r['node'],r['target_s']))
 count=len(done)
 with output.open('a') as f:
  for target in [600,1200,1800]:
   for node in origins:
    if (node,target) in done:continue
    r=d.solve(node,target);r.update(region=args.region,source_set='near' if args.near else 'full',source_count=len(sources),inside_region=node in members)
    f.write(json.dumps(r)+'\n');f.flush();count+=1
    if count%500==0:print(name,count,'/',len(origins)*3,flush=True)
 print(name,'complete',flush=True)

if __name__=='__main__':main()
