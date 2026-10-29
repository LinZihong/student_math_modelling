"""Re-solve the queries that hit the 3 s / 30 s limits of the main run, with up to an hour per query,
and write the outcomes back into the result files; writes timeouts_rerun.json.

Same exact search as engine.Dataset.solve; only the time limits differ."""
import json,math,time
from concurrent.futures import ProcessPoolExecutor
import numpy as np
import core,engine
from core import OUT,SOURCES
from run_experiments import tasks,STATUS

LIMIT=3600.

def solve_long(d,origin,target):
 start=time.monotonic();idx=d.nidx[origin];active=[int(np.argmin(d.baseline[:,idx]))]
 while True:
  left=LIMIT-(time.monotonic()-start)
  if left<=0:return dict(status='timeout',active=len(active))
  try:p,_=engine.feasible(origin,d.exits,[d.scenario(k) for k in active],d.dist,math.inf,target,timeout=left)
  except TimeoutError:return dict(status='timeout',active=len(active))
  if p is None:return dict(status='no_common_route',active=len(active))
  dl=d.path_deadlines(p);worst=int(np.argmin(dl))
  if dl[worst]>=target-1e-7:
   return dict(status='solved',length=sum(d.G[a][b]['weight'] for a,b in zip(p,p[1:])),deadline=float(dl[worst]),active=len(active),path=p)
  active.append(worst)

def one(job):
 t,zone,i,j,tau=job;F=core.Fields(t['factor']);d=core.zone_dataset(F,zone);s=time.monotonic()
 r=solve_long(d,SOURCES[j],tau*60.);r.update(task=t['id'],exp=t['exp'],origin=SOURCES[j],tau=int(tau),seconds=round(time.monotonic()-s,1),i=i,j=j);return r

def main():
 todo,P=tasks();jobs=[]
 for t in todo:
  r=np.load(OUT/'results'/t['exp']/(t['id']+'.npz'))
  for i,tau in enumerate(r['taus']):
   for j in np.where(r['status'][i]==3)[0]:jobs.append((t,P[t['part']][t['zone']],i,int(j),tau))
 print('re-solving',len(jobs),'queries',flush=True)
 with ProcessPoolExecutor(max_workers=len(jobs) or 1) as pool:out=list(pool.map(one,jobs))
 for r in out:
  f=OUT/'results'/r['exp']/(r['task']+'.npz');a=dict(np.load(f));i,j=r['i'],r['j']
  a['status'][i,j]=STATUS[r['status']];a['active'][i,j]=r['active']
  if r['status']=='solved':a['length'][i,j]=r['length'];a['deadline'][i,j]=r['deadline']
  np.savez_compressed(f,**a)
  print(r['task'],r['origin'],r['status'],r['seconds'],'s',flush=True)
 (OUT/'timeouts_rerun.json').write_text(json.dumps([{k:v for k,v in r.items() if k!='path'} for r in out],indent=1))

if __name__=='__main__':main()
