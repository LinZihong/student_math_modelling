"""Figures 2-5 and all tables of the v9 paper, generated from 实验_09 records (Figure 1: fig_geometry.py)."""
import json,math,sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
ROOT=Path(__file__).resolve().parents[1];P=Path(__file__).resolve().parent;E9=ROOT/'实验_09_水源位置未知时的固定逃生路线'
sys.path.insert(0,str(E9))
import core
from core import SOURCES,XYZ,EDGES,EXITS,PATHS,DIST,GRAPH
F=P/'figures';T=P/'tables';F.mkdir(exist_ok=True);T.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9.5,'axes.titlesize':10.5,'axes.labelsize':9.5,'legend.fontsize':8.5,'pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
S=json.loads((E9/'summary.json').read_text());PART=json.loads((E9/'partitions.json').read_text())['partitions']
REG=['NW','SW','SE','NE'];C=dict(shortest='#8a8f94',avoid='#d08c2d',robust='#1f6f9f',exact='#2b2b2b',ok='#4f9a8a',fixed='#e07b24',bad='#b5303c',zone='#d9cfe6',shaft='#a51c1c')
def save(fig,name):fig.savefig(F/(name+'.pdf'),bbox_inches='tight');fig.savefig(F/(name+'.png'),dpi=180,bbox_inches='tight');plt.close(fig)
def fmt(n):return f'{n:,}'
def counts(tau=30):return S['delay'][str(tau)]['counts']
def load(exp,part,zone,factor=1.):return np.load(E9/'results'/exp/f'{part}_z{zone}_q{factor}.npz')
SEG=[[XYZ[a][:2]/1000,XYZ[b][:2]/1000] for a,b,L in EDGES if a<b]
def network(ax,lw=.45,c='#d3d7da'):
 ax.add_collection(LineCollection(SEG,colors=c,linewidths=lw));ax.set_aspect('equal');ax.autoscale()
 ex=np.array([XYZ[e][:2]/1000 for e in EXITS]);ax.scatter(ex[:,0],ex[:,1],marker='s',s=16,c=C['shaft'],zorder=6)

FIELDS=core.Fields()
def cut_point(zone,path,depart=1800.):
 from model.routing import walk
 d=core.zone_dataset(FIELDS,zone);k=int(np.argmin(d.path_deadlines(path)));_,look=d.lookup(k)
 return walk([look[a,b] for a,b in zip(path,path[1:])],depart)[1]

def fig_failures():
 """Where the shortest routes fail for a northwest alarm, and why, per region."""
 fig=plt.figure(figsize=(9.6,4.3));ax=fig.add_axes([0,.02,.52,.92]);bx=fig.add_axes([.62,.17,.37,.68])
 network(ax);zone=set(PART['quadrant'][0]);r=load('E1_delay','quadrant',0);i=list(r['taus']).index(30)
 z=np.array([XYZ[s][:2]/1000 for s in zone]);ax.scatter(z[:,0],z[:,1],s=5,c='#b9a7d1',lw=0,zorder=2)
 out=~r['inside'];base=r['baseline']>=1800;solved=r['status'][i]==0
 for mask,col,size,lab in [(out&base,C['ok'],3,'shortest route works'),(out&~base&solved,C['fixed'],9,'needs a different route'),(out&~solved,C['bad'],11,'no fixed route works')]:
  q=np.array([XYZ[SOURCES[j]][:2]/1000 for j in np.where(mask)[0]]);ax.scatter(q[:,0],q[:,1],s=size,c=col,lw=0,zorder=4,label=lab)
 cuts=[cut_point(zone,PATHS[SOURCES[j]][::-1]) for j in np.where(out&~base)[0]];cuts=np.array([XYZ[c][:2]/1000 for c in cuts if c])
 ax.scatter(cuts[:,0],cuts[:,1],marker='x',s=22,c='k',lw=.8,zorder=7,alpha=.6)
 ax.legend(handles=[Line2D([],[],ls='',marker='o',ms=5,c='#b9a7d1',label='possible sources (NW zone)')]+[Line2D([],[],ls='',marker='x',ms=5,c='k',label='where shortest routes are cut')]+
  [Line2D([],[],ls='',marker='o',ms=4,c=c,label=l) for c,l in [(C['ok'],'shortest route works'),(C['fixed'],'needs a different route'),(C['bad'],'no fixed route works')]]+[Line2D([],[],ls='',marker='s',ms=5,c=C['shaft'],label='shaft')],loc='upper left',fontsize=8,frameon=False)
 ax.set_title('(a) Northwest alarm, 30-minute target: starting points outside the zone',loc='left');ax.set_xticks([]);ax.set_yticks([])
 for s in ['left','bottom']:ax.spines[s].set_visible(False)
 rows=counts();y=np.arange(4)
 ok=np.array([r['outside']['shortest'] for r in rows]);on=np.array([r['outside']['shortest_fail_at_onset'] for r in rows]);dl=np.array([r['outside']['shortest_fail_by_delay'] for r in rows]);n=ok+on+dl
 bx.barh(y,ok/n*100,color=C['ok'],label='works');bx.barh(y,on/n*100,left=ok/n*100,color=C['bad'],label='fails even leaving at once')
 bx.barh(y,dl/n*100,left=(ok+on)/n*100,color='#f2b134',label='fails only because of the delay')
 for k in range(4):bx.text(101,k,f'{on[k]+dl[k]} fail',va='center',fontsize=8.5)
 bx.set_yticks(y,REG);bx.invert_yaxis();bx.set_xlim(0,100);bx.set_xlabel('Starting points outside the zone (%)')
 bx.set_title('(b) Shortest routes, 30-minute target',loc='left');bx.legend(loc='upper center',bbox_to_anchor=(.45,-.2),ncol=1,frameon=False,fontsize=8)
 save(fig,'failures')

def fig_plans():
 """Share of outside starting points protected by each plan, per quadrant zone, at 30 minutes."""
 rows=counts();fig,ax=plt.subplots(figsize=(7.4,2.9));y=np.arange(4)[::-1]
 keys=[('shortest','shortest route',C['shortest'],'o'),('avoid','avoid-the-zone rule',C['avoid'],'D'),('cap20','robust, ≤20% longer',C['robust'],'v'),('robust','robust, any length',C['robust'],'o'),('exact','exact source known',C['exact'],'|')]
 for k,(row,yy) in enumerate(zip(rows,y)):
  o=row['outside'];n=o['n'];exact=n-o['no_way_out']
  vals={'shortest':o['shortest'],'avoid':o['avoid'],'cap20':o['cap20'],'robust':o['robust'],'exact':exact}
  ax.plot([vals['shortest']/n*100,exact/n*100],[yy,yy],c='#e3e3e3',lw=6,zorder=1,solid_capstyle='round')
  for key,lab,col,m in keys:ax.scatter(vals[key]/n*100,yy,c=col,marker=m,s=70 if m!='|' else 160,zorder=3,label=lab if k==0 else None,**({'facecolors':'white' if key=='cap20' else col,'edgecolors':col,'linewidths':1.6} if m!='|' else {'linewidths':2.2}))
 ax.set_yticks(y,[f"{r['region']} alarm" for r in rows]);ax.set_xlabel('Starting points outside the alarm zone that are protected (%)');ax.set_xlim(45,101)
 ax.legend(loc='upper center',bbox_to_anchor=(.5,-.25),ncol=5,frameon=False,fontsize=8,handletextpad=.2,columnspacing=1)
 save(fig,'plans')

def fig_information():
 """(a) Whole-mine protection against the number of alarm zones; (b) against the warning delay."""
 fig,(ax,bx)=plt.subplots(1,2,figsize=(9.6,3.7));ks=[1,2,4,8,16,32,64,128];x=np.log2(ks)
 res=S['resolution'];pp=S['resolution_per_pair']['30']
 for key,lab in [('shortest','shortest route'),('avoid','avoid-the-zone rule'),('robust','robust fixed route')]:
  vals=np.array([[res[f'zones_k{k}_v{v}']['30'][key] for v in [0,1,2] if f'zones_k{k}_v{v}' in res] for k in ks],dtype=object)
  lo=np.array([min(v) for v in vals])*100;hi=np.array([max(v) for v in vals])*100;mid=np.array([np.mean(v) for v in vals])*100
  ax.fill_between(x,lo,hi,color=C[key],alpha=.18,lw=0);ax.plot(x,mid,marker='o',ms=3.5,c=C[key],label=lab)
 ax.scatter([8.6],[pp['shortest']*100],c=C['shortest'],s=25);ax.annotate('shortest route,\nexact source',(8.6,pp['shortest']*100),xytext=(0,-30),textcoords='offset points',fontsize=7,ha='center',color=C['shortest']);ax.scatter([8.6],[pp['exact']*100],c=C['exact'],marker='_',s=200,lw=2)
 ax.axhline(pp['exact']*100,c=C['exact'],ls='--',lw=1,label='exact source known (ceiling)')
 q=res['quadrant']['30'];ax.scatter([2],[q['robust']*100],marker='*',s=110,c=C['robust'],edgecolors='white',zorder=5,label='robust, quadrants')
 ax.scatter([1,2],[res['shaftcut_k2']['30']['robust']*100,res['shaftcut_k4']['30']['robust']*100],marker='D',s=30,c='white',edgecolors=C['robust'],linewidths=1.4,zorder=5,label='robust, zones divided at the shafts')
 ax.set_xticks(list(x)+[8.6],[str(k) for k in ks]+['exact']);ax.set_xlabel('Number of alarm zones');ax.set_ylabel('Protected (worker, flood) pairs (%)')
 ax.set_title('(a) Finer alarm zones, 30-minute target',loc='left');ax.legend(fontsize=7.8,frameon=False,loc='lower right')
 taus=sorted(int(t) for t in S['delay']);d=S['delay']
 for key,lab,col in [('shortest','shortest route',C['shortest']),('avoid','avoid-the-zone rule',C['avoid']),('robust','robust fixed route',C['robust'])]:bx.plot(taus,[d[str(t)]['pairs'][key]*100 for t in taus],marker='o',ms=3.5,c=col,label=lab+', quadrant zones')
 bx.plot(taus,[d[str(t)]['per_pair']['exact']*100 for t in taus],c=C['exact'],ls='--',label='exact source known')
 bx.set_xlabel('Warning delay target (min)');bx.set_ylabel('Protected (worker, flood) pairs (%)');bx.set_title('(b) Later warnings, four quadrant zones',loc='left');bx.legend(fontsize=7.8,frameon=False,loc='lower left')
 lo=min(ax.get_ylim()[0],bx.get_ylim()[0]);ax.set_ylim(lo,100);bx.set_ylim(lo,100)
 fig.tight_layout(w_pad=2.5);save(fig,'information')

def fig_example():
 """One northwest-alarm example: the shortest route is cut near the shafts; the robust route avoids that."""
 r=load('E1_delay','quadrant',0);i=list(r['taus']).index(30);paths=json.loads((E9/'results/E1_delay/quadrant_z0_q1.0_paths.json').read_text())['robust']
 zone=set(PART['quadrant'][0]);cand=[]
 for j,o in enumerate(SOURCES):
  if r['inside'][j] or r['baseline'][j]>=1800 or r['status'][i,j]!=0:continue
  ext=r['length'][i,j]/r['shortest'][j]-1
  if paths[o][-1]!=PATHS[o][0] and .03<=ext<=.25 and 3000<=r['shortest'][j]<=7000:cand.append((ext,o))
 cand.sort();ext,o=cand[len(cand)//2];j=SOURCES.index(o)
 fig,ax=plt.subplots(figsize=(7,5.2));network(ax);z=np.array([XYZ[s][:2]/1000 for s in zone]);ax.scatter(z[:,0],z[:,1],s=5,c='#b9a7d1',lw=0,zorder=2)
 base=PATHS[o][::-1]
 for p,col,lab in [(base,C['bad'],f'shortest route: {r["shortest"][j]/1000:.2f} km'),(paths[o],C['robust'],f'robust route: {r["length"][i,j]/1000:.2f} km (+{ext*100:.0f}%)')]:
  q=np.array([XYZ[n][:2]/1000 for n in p]);ax.plot(q[:,0],q[:,1],c=col,lw=2.2,label=lab,zorder=5)
 c=cut_point(zone,base);cx,cy=XYZ[c][:2]/1000;ax.scatter([cx],[cy],marker='X',s=90,c='k',zorder=8);ax.annotate('cut by the flood',(cx,cy),xytext=(10,12),textcoords='offset points',fontsize=8.5)
 for sh in {base[-1],paths[o][-1]}:ax.annotate('shaft '+sh,XYZ[sh][:2]/1000,xytext=(-62,-14 if sh==paths[o][-1] else 4),textcoords='offset points',fontsize=8,color=C['shaft'])
 ax.scatter(*(XYZ[o][:2]/1000),c='k',s=30,zorder=7);ax.annotate(f'start {o}',XYZ[o][:2]/1000,xytext=(6,6),textcoords='offset points',fontsize=8.5)
 ax.legend(loc='upper right',fontsize=8.5,frameon=True,framealpha=.95);ax.set_xlabel('x (km)');ax.set_ylabel('y (km)')
 save(fig,'example');return dict(cut_node=c,cut_km_from_shaft=DIST[c]/1000,origin=o,shortest_km=r['shortest'][j]/1000,robust_km=r['length'][i,j]/1000,extra=ext,shortest_shaft=base[-1],robust_shaft=paths[o][-1],shortest_deadline_min=r['baseline'][j]/60,robust_deadline_min=r['deadline'][i,j]/60,candidates=len(cand))

def tables(example):
 rows=counts();lines=[]
 for r in rows:
  o=r['outside'];lines.append(f"{r['region']} & {fmt(r['sources'])} & {fmt(o['n'])} & {fmt(o['shortest'])} & {fmt(o['avoid'])} & {fmt(o['cap20'])} & {fmt(o['cap50'])} & {fmt(o['robust'])} & {fmt(o['n']-o['no_way_out'])}\\\\")
 (T/'plans_rows.tex').write_text('\n'.join(lines)+'\n\\bottomrule\n')
 res=S['resolution'];lines=[]
 for k in [1,2,4,8,16,32,64,128]:
  vs=[res[f'zones_k{k}_v{v}']['30'] for v in [0,1,2] if f'zones_k{k}_v{v}' in res]
  def rng(key):
   a=[x[key]*100 for x in vs];return f'{np.mean(a):.1f}' if len(a)==1 or max(a)-min(a)<.05 else f'{np.mean(a):.1f} ({min(a):.1f}--{max(a):.1f})'
  lines.append(f"{k} & {rng('shortest')} & {rng('avoid')} & {rng('robust')} & {rng('information_limited')}\\\\")
 pp=S['resolution_per_pair']['30'];lines.append(f"\\midrule Exact source & {pp['shortest']*100:.1f} & -- & {pp['exact']*100:.1f} & 0.0\\\\")
 (T/'resolution_rows.tex').write_text('\n'.join(lines)+'\n\\bottomrule\n')
 lines=[]
 def prow(label,n,pr,pp):return f"{label} & {fmt(n)} & {pr['shortest']*100:.1f} & {pr['avoid']*100:.1f} & {pr['robust']*100:.1f} & {pr['information_limited']*100:.1f} & {pp['exact']*100:.1f}\\\\"
 for b,v in S['breadth'].items():lines.append(prow(f'Within {b}\\,m',v['sources'],v['pairs'],v['per_pair']))
 d=S['delay']['30'];lines.append(prow('Whole zone',sum(len(z) for z in PART['quadrant']),d['pairs'],d['per_pair']))
 (T/'breadth_rows.tex').write_text('\n'.join(lines)+'\n\\bottomrule\n')
 lines=[];R=S['resolution'];I=S['inflow']['resolution']
 for k in [1,2,4,8,16,32,64,128]:
  p=f'zones_k{k}_v0';lines.append(f"{k} equal zone{'s' if k>1 else ''}{' (no location)' if k==1 else ''} & "+' & '.join(f"{R[p][t]['robust']*100:.1f}" for t in ['10','30','60'])+f" & {I[p]['robust']*100:.1f}\\\\")
 lines.append('\\midrule')
 for p,lab in [('quadrant','4 quadrants'),('shaftcut_k2','2 zones cut at the shafts'),('shaftcut_k4','4 zones cut at the shafts')]:
  lines.append(f"{lab} & "+' & '.join(f"{R[p][t]['robust']*100:.1f}" for t in ['10','30','60'])+(f" & {S['inflow']['quadrant']['30']['pairs']['robust']*100:.1f}" if p=='quadrant' else ' & --')+'\\\\')
 lines.append(f"Exact source & "+' & '.join(f"{S['resolution_per_pair'][t]['exact']*100:.1f}" for t in ['10','30','60'])+f" & {S['inflow']['quadrant']['30']['per_pair']['exact']*100:.1f}\\\\")
 (T/'extra_rows.tex').write_text('\n'.join(lines)+'\n\\bottomrule\n')
 lines=[]
 for r in counts():
  o=r['inside'];lines.append(f"{r['region']} & {fmt(o['n'])} & {fmt(o['shortest'])} & {fmt(o['avoid'])} & {fmt(o['robust'])} & {fmt(o['no_way_out'])} & {fmt(o['no_common_route'])}\\\\")
 (T/'inside_rows.tex').write_text('\n'.join(lines)+'\n\\bottomrule\n')
 (T/'example.json').write_text(json.dumps(example,indent=1))

if __name__=='__main__':
 fig_failures();fig_plans();fig_information();ex=fig_example();tables(ex);print('figures and tables written',ex)
