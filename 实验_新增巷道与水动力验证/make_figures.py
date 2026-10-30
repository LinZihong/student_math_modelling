"""Scientific figures from retained data; no new simulated outcomes."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from continuous_certificate import profiles,witness_peak

ROOT=Path(__file__).resolve().parent;OUT=ROOT/'figures';OUT.mkdir(exist_ok=True)
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':160})

def confirmation():
    rows=json.loads((ROOT/'results/confirmation_v1/results.json').read_text())
    fig,axes=plt.subplots(1,2,figsize=(9,3.7),sharey=True)
    for ax,t,title in zip(axes,['0','600'],['Immediate departure','Departure after 10 min']):
        for model,color,offset in [('fv','#2369a0',-.12),('swmm','#c26725',.12)]:
            y=[r['models'][model]['difference_m'][t] for r in rows]
            ax.scatter(np.arange(16)+offset,y,color=color,s=24,label='Finite volume' if model=='fv' else 'SWMM')
        ax.axhline(0,color='black',lw=.7);ax.axhline(-.02 if t=='0' else .02,color='gray',ls='--',lw=.8)
        ax.set(title=title,xlabel='Frozen factorial case',xticks=range(0,16,3))
    axes[0].set_ylabel('Added minus original peak depth (m)')
    axes[1].legend(frameon=False,fontsize=9)
    fig.tight_layout();fig.savefig(OUT/'confirmation.png');plt.close(fig)

def delay_curve():
    paths0=[['B','C','E'],['B','C','A','E']]
    paths1=paths0+[['B','A','E'],['B','A','C','E']]
    fig,axes=plt.subplots(1,2,figsize=(9,3.7),sharey=True)
    output=[]
    for ax,model in zip(axes,['fv','swmm']):
        for added,color in [(False,'#2369a0'),(True,'#c26725')]:
            if model=='fv':stem=ROOT/'results/network_fv'/f'added{int(added)}_dx6p25_area16p0_q0p5_end3600p0'
            else:stem=ROOT/'results/shortcut_screen'/f'q0p5_added{int(added)}_dx6p25_dt0p125_n0p025_bz0p5'
            times,fields,origin=profiles(stem,model);deps=np.arange(0,1201,30)
            peaks=[min(witness_peak(times,fields,p,float(d)) for p in (paths1 if added else paths0)) for d in deps]
            ax.plot(deps/60,peaks,color=color,label='Added connection' if added else 'Original layout')
            if added:ax.plot(deps/60,np.interp(deps,times,origin),color=color,ls=':',lw=1,label='Origin-depth lower bound')
            output.append(dict(model=model,added=added,departure_s=deps.tolist(),minimum_peak=peaks))
        ax.set(xlabel='Departure delay (min)',title='Finite-volume model' if model=='fv' else 'SWMM model')
    axes[0].set_ylabel('Minimum peak depth on a simple route (m)');axes[1].legend(frameon=False,fontsize=8)
    fig.tight_layout();fig.savefig(OUT/'delay_curve.png');plt.close(fig)
    (ROOT/'results/delay_curve.json').write_text(json.dumps(output,indent=2))

def geometry():
    fig,axes=plt.subplots(1,2,figsize=(9,3.2),gridspec_kw={'width_ratios':[1.3,1]})
    ax=axes[0];pos={'A':(0,1),'B':(0,0),'C':(1.5,0),'E':(1.5,1),'O':(2.1,1)}
    edges=[('A','E','500 m'),('A','C','600 m'),('B','C','500 m'),('C','E','500 m'),('E','O','100 m')]
    for a,b,label in edges:
        x,y=pos[a],pos[b];ax.plot([x[0],y[0]],[x[1],y[1]],color='#2369a0',lw=2)
        offset=.08 if a!='A' or b!='C' else -.1
        ax.text((x[0]+y[0])/2,(x[1]+y[1])/2+offset,label,fontsize=8,ha='center',backgroundcolor='white')
    ax.plot([0,0],[0,1],ls='--',lw=2,color='#c26725');ax.text(-.12,.5,'Added\n80–120 m',ha='right',va='center',fontsize=8,color='#c26725')
    for n,(x,y) in pos.items():ax.scatter(x,y,s=80,color='white',edgecolor='black',zorder=3);ax.text(x+.06,y-.08,n,fontsize=10)
    ax.text(0,1.2,'A: inrush',fontsize=9);ax.text(0,-.25,'B: worker',fontsize=9);ax.text(1.4,1.2,'E: escape endpoint',fontsize=9)
    ax.text(2.,.75,'O: drain',fontsize=8);ax.set(xlim=(-.6,2.45),ylim=(-.35,1.45));ax.axis('off')
    ax=axes[1];ax.plot([0,100,600],[2,.5,1],marker='o',color='#c26725')
    ax.plot([100,600],[.5,1],color='#2369a0',lw=2)
    ax.set(xlabel='Schematic distance along A–B–C (m)',ylabel='Bed elevation (m)',ylim=(0,2.3))
    for x,z,n in [(0,2,'A'),(100,.5,'B'),(600,1,'C')]:ax.annotate(n,(x,z),xytext=(5,8),textcoords='offset points')
    fig.tight_layout();fig.savefig(OUT/'geometry.png');plt.close(fig)

if __name__=='__main__':confirmation();delay_curve();geometry()
