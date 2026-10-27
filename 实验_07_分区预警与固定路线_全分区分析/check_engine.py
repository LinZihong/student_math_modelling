import json,random,math
from engine import Dataset,OUT,latest_departure,feasible

def main():
 design=json.loads((OUT/'design.json').read_text());sources=[s for region in design['regions'].values() for s in region if (OUT/'fields'/f'{s}.npz').exists()]
 sources=random.Random(20261101).sample(sorted(sources),min(12,len(sources)));ds=Dataset(sources);nodes=random.Random(20261102).sample(sorted(set(ds.nodes)-ds.exits-{'A'}),24)
 comparisons=0
 for n in nodes:
  p=ds.paths[n][::-1];v=ds.path_deadlines(p)
  for k in range(len(sources)):
   adj,look=ds.lookup(k);scalar=latest_departure([look[a,b] for a,b in zip(p,p[1:])]);assert abs(scalar-v[k])<1e-7
  for target in [600,1200,1800]:
   r=ds.solve(n,target);p,_=feasible(n,ds.exits,[ds.scenario(k) for k in range(len(sources))],ds.dist,math.inf,target)
   assert (p is not None)==(r['status']=='solved'),(n,target,r['status'])
   if p is not None:
    length=sum(ds.G[a][b]['weight'] for a,b in zip(p,p[1:]));assert abs(length-r['length_m'])<1e-6
   comparisons+=1
 result={'sources':sources,'origins':nodes,'full_solver_comparisons':comparisons,'scalar_vector_deadline_comparisons':len(nodes)*len(sources),'passed':True}
 (OUT/'engine_tests.json').write_text(json.dumps(result,indent=2));print(result)
if __name__=='__main__':main()
