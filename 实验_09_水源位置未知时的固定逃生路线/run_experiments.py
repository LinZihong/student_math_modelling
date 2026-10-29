"""Run all v9 experiments. Each task is one alarm zone at one inflow and a list of delay targets;
its results go to results/<experiment>/<task>.npz, so an interrupted run resumes where it stopped."""
import json,sys,time
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np
import core
from core import OUT,SOURCES,NIDX

STATUS={'solved':0,'no_common_route':1,'impossible_even_with_source_known':2,'timeout':3}
FIELDS={}

def tasks():
 P=json.loads((OUT/'partitions.json').read_text())['partitions'];out=[]
 def add(exp,part,factor,taus,paths=False):
  for i,z in enumerate(P[part]):
   if z:out.append(dict(exp=exp,part=part,zone=i,factor=factor,taus=taus,paths=paths,id=f'{part}_z{i}_q{factor}'))
 add('E1_delay','quadrant',1.,[0,5,10,15,20,30,45,60,90,120],paths=True)
 for part in P:
  if part.startswith('zones_'):add('E2_resolution',part,1.,[10,30,60] if part.endswith('_v0') else [30])
 add('E2_resolution','quadrant',1.,[10,30,60])
 for part in ['shaftcut_k2','shaftcut_k4']:add('E2_resolution',part,1.,[10,30,60])
 for b in [50,100,200,500,1000]:add('E3_breadth',f'quadrant_near{b}',1.,[30])
 add('E4_inflow','quadrant',2.,[10,30,60])
 for part in P:
  if part.startswith('zones_') and part.endswith('_v0'):add('E4_inflow',part,2.,[30])
 return out,P

def run(task,zone):
 F=FIELDS.setdefault(task['factor'],core.Fields(task['factor']))
 d=core.zone_dataset(F,zone);members=set(zone);n=len(SOURCES);T=len(task['taus'])
 res=dict(status=np.full((T,n),-1,np.int8),length=np.full((T,n),np.nan),deadline=np.full((T,n),np.nan),
  shortest=np.array([core.DIST[o] for o in SOURCES]),baseline=np.empty(n),exact=np.empty(n),avoid_deadline=np.empty(n),avoid_length=np.empty(n),
  inside=np.array([o in members for o in SOURCES]),active=np.zeros((T,n),np.int16))
 paths={}
 for j,o in enumerate(SOURCES):
  idx=NIDX[o];res['baseline'][j]=d.baseline[:,idx].min();res['exact'][j]=d.U[:,idx].min()
  ap=core.avoid_route(o,zone);res['avoid_deadline'][j],res['avoid_length'][j]=core.evaluate(d,ap,0)
  if task['paths']:paths.setdefault('avoid',{})[o]=ap
  for i,tau in enumerate(task['taus']):
   r=d.solve(o,tau*60.);res['status'][i,j]=STATUS[r['status']];res['active'][i,j]=r.get('active_sources',0)
   if r['status']=='solved':
    res['length'][i,j]=r['length_m'];res['deadline'][i,j]=r['deadline_s']
    if task['paths'] and tau==30:paths.setdefault('robust',{})[o]=r['path']
 return res,paths

def worker(task,zone):
 t=time.monotonic();res,paths=run(task,zone);folder=OUT/'results'/task['exp'];folder.mkdir(parents=True,exist_ok=True)
 np.savez_compressed(folder/(task['id']+'.tmp.npz'),taus=np.array(task['taus']),**res);(folder/(task['id']+'.tmp.npz')).replace(folder/(task['id']+'.npz'))
 if paths:(folder/(task['id']+'_paths.json')).write_text(json.dumps(paths))
 return task['id'],time.monotonic()-t,int((res['status']==3).sum())

def main():
 todo,P=tasks();only=sys.argv[1:]
 todo=[t for t in todo if (not only or t['exp'] in only) and not (OUT/'results'/t['exp']/(t['id']+'.npz')).exists()]
 todo.sort(key=lambda t:-len(P[t['part']][t['zone']]))
 print('tasks to run',len(todo),flush=True);start=time.monotonic();timeouts=0
 with ProcessPoolExecutor(max_workers=9) as pool:
  futures=[pool.submit(worker,t,P[t['part']][t['zone']]) for t in todo]
  for k,f in enumerate(as_completed(futures),1):
   tid,el,to=f.result();timeouts+=to
   if k%25==0 or k==len(todo):print(f'{k}/{len(todo)} done, last {tid} {el:.1f}s, timeouts {timeouts}, elapsed {time.monotonic()-start:.0f}s',flush=True)
 print('ALL TASKS COMPLETE; timeouts',timeouts,flush=True)

if __name__=='__main__':main()
