"""Independent first-order finite-volume shallow-water core (per unit width).

HLL flux and Audusse et al. (2004) hydrostatic reconstruction. Existing
numerical machinery, not a research contribution. No network junctions yet.
"""
import numpy as np

G=9.81

def flux(hL,qL,zL,hR,qR,zR):
    uL=np.divide(qL,hL,out=np.zeros_like(qL),where=hL>1e-10)
    uR=np.divide(qR,hR,out=np.zeros_like(qR),where=hR>1e-10)
    z=np.maximum(zL,zR)
    l=np.maximum(0.,hL+zL-z);r=np.maximum(0.,hR+zR-z)
    ql=l*uL;qr=r*uR
    cL=np.sqrt(G*l);cR=np.sqrt(G*r)
    sl=np.minimum(uL-cL,uR-cR);sr=np.maximum(uL+cL,uR+cR)
    # Dry-bed characteristic fan bounds (Ritter).
    sl=np.where(l<=1e-10,uR-2*cR,sl)
    sr=np.where(r<=1e-10,uL+2*cL,sr)
    sl=np.minimum(sl,0.);sr=np.maximum(sr,0.)
    den=np.maximum(sr-sl,1e-12)
    fh=(sr*ql-sl*qr+sl*sr*(r-l))/den
    fq=(sr*(ql*uL+.5*G*l*l)-sl*(qr*uR+.5*G*r*r)+sl*sr*(qr-ql))/den
    return fh,fq+.5*G*(hL*hL-l*l),fq+.5*G*(hR*hR-r*r)

def step(h,q,z,dx,dt,roughness=0.,width=4.):
    # Transmissive boundaries; benchmark observation region is out of reach.
    hh=np.pad(h,1,mode='edge');qq=np.pad(q,1,mode='edge');zz=np.pad(z,1,mode='edge')
    f,left,right=flux(hh[:-1],qq[:-1],zz[:-1],hh[1:],qq[1:],zz[1:])
    hn=h-dt/dx*(f[1:]-f[:-1]);qn=q-dt/dx*(left[1:]-right[:-1])
    if hn.min() < -1e-9:raise ArithmeticError(f'negative depth {hn.min()}')
    hn=np.maximum(hn,0.)
    if roughness:
        R=width*hn/(width+2*hn)
        qn/=1+dt*G*roughness**2*np.abs(qn)/np.maximum(hn*R**(4/3),1e-15)
    qn=np.where(hn>1e-9,qn,0.)
    return hn,qn,dt*(f[0]-f[-1])

def evolve(h,q,z,dx,end,roughness=0.):
    t=0.;boundary=0.;initial=float(h.sum()*dx)
    while t<end-1e-10:
        u=np.divide(q,h,out=np.zeros_like(q),where=h>1e-10)
        dt=min(end-t,.4*dx/max(float(np.max(np.abs(u)+np.sqrt(G*h))),1e-6))
        h,q,amount=step(h,q,z,dx,dt,roughness)
        boundary+=amount;t+=dt
    return h,q,float(h.sum()*dx-initial-boundary)

if __name__=='__main__':
    from pathlib import Path
    import json
    out=Path(__file__).resolve().parent/'results'/'finite_volume';out.mkdir(parents=True,exist_ok=True)
    rows=[]
    for dx in [25.,12.5,6.25,3.125]:
        x=np.arange(-1000+dx/2,1000,dx);z=np.zeros_like(x)
        h=(x<0).astype(float);q=np.zeros_like(h)
        h,q,res=evolve(h,q,z,dx,100.)
        c=np.sqrt(G);exact=np.where(x<=-100*c,1.,np.where(x>=200*c,0.,(2*c-x/100)**2/(9*G)))
        mask=np.abs(x)<700
        rows.append(dict(test='ritter',dx=dx,mean_absolute_error=float(np.abs(h[mask]-exact[mask]).mean()),
                         mass_residual_per_width=res,front_h001=float(x[h>.01][-1]),
                         exact_front_h001=float((2*c-3*np.sqrt(G*.01))*100)))
        np.savez(out/f'ritter_{dx}.npz',x=x,h=h,q=q,exact=exact)
    x=np.linspace(0,100,200);z=.4*np.sin(x/12);h=.8-z;q=np.zeros_like(h)
    hh,qq,res=evolve(h.copy(),q,z,x[1]-x[0],100.)
    rows.append(dict(test='lake_at_rest',max_depth_error=float(np.max(np.abs(hh-h))),max_discharge=float(np.max(np.abs(qq))),mass_residual_per_width=res))
    (out/'summary.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
