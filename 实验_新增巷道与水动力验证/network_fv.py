"""Finite-volume channels coupled through finite-area, well-mixed junctions.

Junctions store mass with common water level and zero resolved momentum.
This is a specified reservoir coupling, NOT a validated arbitrary junction
law. Boundary flux is shared exactly by channel and junction balances.
"""
import json
from pathlib import Path
import numpy as np
from shallow_water import G,flux

OUT=Path(__file__).resolve().parent/'results'/'network_fv'
OUT.mkdir(parents=True,exist_ok=True)

class Network:
    def __init__(self,z,corridors,dx=12.5,area=16.,width=4.,roughness=.025,outfall='O'):
        self.z=dict(z);self.area=area;self.width=width;self.n=roughness;self.outfall=outfall
        self.depth={a:0. for a in z if a!=outfall};self.channels=[]
        for a,b,L in corridors:
            N=int(np.ceil(L/dx));d=L/N;x=(np.arange(N)+.5)*d
            bed=z[a]+(z[b]-z[a])*x/L
            self.channels.append(dict(a=a,b=b,L=L,dx=d,x=x,z=bed,h=np.zeros(N),q=np.zeros(N)))
        self.t=0.;self.balance=0.;self.max_residual=0.;self.initial_volume=self.volume()

    def volume(self):
        return self.area*sum(self.depth.values())+sum(float(c['h'].sum())*c['dx']*self.width for c in self.channels)

    def advance(self,target,sources):
        while self.t<target-1e-9:
            dt=min(1.,target-self.t);bundles=[];rates={n:sources.get(n,0.) for n in self.depth};out=0.
            for c in self.channels:
                a,b,h,q,z=c['a'],c['b'],c['h'],c['q'],c['z']
                u=np.divide(q,h,out=np.zeros_like(q),where=h>1e-10)
                waves=np.abs(u)+np.sqrt(G*h)
                dt=min(dt,.35*c['dx']/max(float(waves.max()),1e-6))
                # A mixed chamber imposes its hydrostatic head, zero velocity.
                hl=self.depth[a];ql=0.;zl=self.z[a]
                if b==self.outfall:hr=h[-1];qr=q[-1];zr=z[-1]
                else:hr=self.depth[b];qr=0.;zr=self.z[b]
                hh=np.r_[hl,h,hr];qq=np.r_[ql,q,qr];zz=np.r_[zl,z,zr]
                f,fl,fr=flux(hh[:-1],qq[:-1],zz[:-1],hh[1:],qq[1:],zz[1:])
                rates[a]-=self.width*f[0]
                if b!=self.outfall:rates[b]+=self.width*f[-1]
                else:out+=self.width*f[-1]
                bundles.append((c,f,fl,fr))
            # Limit draining both junctions and channel cells, preserving positivity.
            for n,rate in rates.items():
                if rate<0:dt=min(dt,.8*self.depth[n]*self.area/(-rate))
            for c,f,_,_ in bundles:
                loss=np.maximum(f[1:]-f[:-1],0.)
                mask=loss>1e-14
                if np.any(mask):dt=min(dt,float(np.min(.8*c['h'][mask]*c['dx']/loss[mask])))
            if dt<1e-12:raise ArithmeticError('zero positivity time step')
            for c,f,fl,fr in bundles:
                h=c['h']-dt/c['dx']*(f[1:]-f[:-1])
                q=c['q']-dt/c['dx']*(fl[1:]-fr[:-1])
                if h.min()<-1e-10:raise ArithmeticError('negative channel depth')
                h=np.maximum(h,0.)
                radius=self.width*h/(self.width+2*h)
                q/=1+dt*G*self.n**2*np.abs(q)/np.maximum(h*radius**(4/3),1e-15)
                c['h']=h;c['q']=np.where(h>1e-9,q,0.)
            for n,rate in rates.items():self.depth[n]+=dt*rate/self.area
            self.balance+=dt*(sum(sources.values())-out);self.t+=dt
            self.max_residual=max(self.max_residual,abs(self.volume()-self.initial_volume-self.balance))

def geometry(added,bz=.5,extra_length=100.):
    z={'A':2.,'B':bz,'C':1.,'E':0.,'O':-.2}
    paths=[('A','E',500.),('A','C',600.),('B','C',500.),('C','E',500.),('E','O',100.)]
    if added:paths.append(('A','B',extra_length))
    return z,paths

def experiment(added,dx=12.5,area=16.,end=3600.,q=1.4,bz=.5,roughness=.025,extra_length=100.,tag=''):
    z,paths=geometry(added,bz,extra_length);net=Network(z,paths,dx=dx,area=area,roughness=roughness)
    times=np.arange(0,end+1,2.);nodes=list(net.depth);nodehistory=[];history=[[] for _ in paths]
    for t in times:
        net.advance(t,{'A':q});nodehistory.append([net.depth[n] for n in nodes])
        for hist,c in zip(history,net.channels):hist.append(c['h'].copy())
    name=f'added{int(added)}_dx{dx}_area{area}_q{q}_end{end}'.replace('.','p')
    if tag:name=tag+'_'+name
    np.savez_compressed(OUT/f'{name}.npz',times=times,nodes=np.array(nodes),node_depth=np.array(nodehistory),
                        **{f'h{i}':np.array(h) for i,h in enumerate(history)},
                        **{f'x{i}':c['x'] for i,c in enumerate(net.channels)})
    summary=dict(stem=str(OUT/name),added=added,dx=dx,area=area,q=q,end=end,bz=bz,roughness=roughness,extra_length=extra_length,corridors=paths,z=z,nodes=nodes,
                 max_mass_residual_m3=net.max_residual,final_volume_m3=net.volume(),
                 max_depth=max(float(np.max(h)) for h in history),
                 origin_crossing03=next((float(t) for t,d in zip(times,nodehistory) if d[nodes.index('B')]>=.3),None))
    (OUT/f'{name}.json').write_text(json.dumps(summary,indent=2));print(summary,flush=True)
    return summary

def verification():
    # Symmetric dry-start fork: exact symmetry and total mass accounting.
    net=Network({'A':1.,'B':0.,'C':0.},[('A','B',100.),('A','C',100.)],outfall=None)
    net.advance(100.,{'A':.5})
    symmetry=float(np.max(np.abs(net.channels[0]['h']-net.channels[1]['h'])))
    # Closed nonflat graph at common stage must remain at rest.
    lake=Network({'A':.5,'B':0.,'C':.2},[('A','B',100.),('A','C',100.),('B','C',100.)],outfall=None)
    for n in lake.depth:lake.depth[n]=1-lake.z[n]
    for c in lake.channels:c['h']=1-c['z']
    lake.initial_volume=lake.volume();lake.advance(100.,{})
    depth_error=max(float(np.max(np.abs(c['h']+c['z']-1))) for c in lake.channels)
    result=dict(symmetry_error=symmetry,fork_mass_residual=net.max_residual,
                lake_stage_error=depth_error,lake_mass_residual=lake.max_residual)
    assert symmetry<1e-12 and net.max_residual<1e-8 and depth_error<1e-10
    (OUT/'verification.json').write_text(json.dumps(result,indent=2));print(result)

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true');p.add_argument('--dx',type=float,default=12.5)
    p.add_argument('--area',type=float,default=16.);args=p.parse_args()
    if args.verify:verification()
    else:
        for added in [False,True]:experiment(added,args.dx,args.area)
