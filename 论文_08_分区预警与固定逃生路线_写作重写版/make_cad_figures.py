"""Publication figures and tables from frozen CAD audit records."""
import json
from pathlib import Path
import numpy as np
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from mpl_toolkits.mplot3d.art3d import Line3DCollection
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
ROOT=Path(__file__).resolve().parents[1];P=Path(__file__).resolve().parent;D=ROOT/'实验_07_分区预警与固定路线_全分区分析';F=P/'figures';T=P/'tables'
F.mkdir(exist_ok=True);T.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.titlesize':11,'axes.labelsize':9,'legend.fontsize':8,'pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
d=json.loads((D/'design.json').read_text());xyz={k:np.array(v) for k,v in d['nodes'].items()};G=nx.Graph();G.add_weighted_edges_from(d['arcs']);edges=list(G.edges);rows=json.loads((D/'summary.json').read_text());colors={'NW':'#20639b','SW':'#d16925','SE':'#17817c','NE':'#8d5c9f'}
def save(fig,name):
 fig.savefig(F/(name+'.pdf'),bbox_inches='tight');fig.savefig(F/(name+'.png'),dpi=190,bbox_inches='tight');plt.close(fig)
def lookup(region,target=30,source='full',group='outside'):
 return next(r for r in rows if r['region']==region and r['target_min']==target and r['source_set']==source and r['group']==group)
# Geometry: elevation is measured data supplied to the model, not a flood surface.
fig=plt.figure(figsize=(10.5,4.7));ax=fig.add_axes([-.02,.04,.65,.92],projection='3d');z=np.array([v[2] for v in xyz.values()]);norm=Normalize(z.min(),z.max());segments=[np.array([xyz[a],xyz[b]])/np.array([1000,1000,1]) for a,b in edges]
coll=Line3DCollection(segments,cmap='viridis',norm=norm,linewidths=.65,alpha=.92);coll.set_array(np.array([(xyz[a][2]+xyz[b][2])/2 for a,b in edges]));ax.add_collection3d(coll)
pts=np.array(list(xyz.values()));ax.set_xlim(pts[:,0].min()/1000,pts[:,0].max()/1000);ax.set_ylim(pts[:,1].min()/1000,pts[:,1].max()/1000);ax.set_zlim(z.min(),z.max());span=np.ptp(pts,axis=0);ax.set_box_aspect([span[0],span[1],span[2]*35]);ax.view_init(elev=24,azim=-58);ax.set_xlabel('x (km)',labelpad=1);ax.set_ylabel('y (km)',labelpad=1);ax.set_zlabel('Elevation proxy (m)',labelpad=4);ax.tick_params(labelsize=7,pad=0)
for axis in [ax.xaxis,ax.yaxis,ax.zaxis]:axis.pane.fill=False
ex=np.array([xyz[n] for n in d['exits']]);ax.scatter(ex[:,0]/1000,ex[:,1]/1000,ex[:,2],c='#bd3b36',marker='*',s=55,depthshade=False)
ax.set_title('(a) Tunnel network in three dimensions',y=.98);ax.text2D(.04,.03,'Vertical scale exaggerated 35×',transform=ax.transAxes,fontsize=8)
ax2=fig.add_axes([.66,.19,.30,.65]);ax2.add_collection(LineCollection([[xyz[a][:2]/1000,xyz[b][:2]/1000] for a,b in edges],colors='#d1d5d8',linewidths=.45))
for region in ['NW','SW','SE','NE']:
 q=np.array([xyz[n][:2]/1000 for n in d['regions'][region]]);ax2.scatter(q[:,0],q[:,1],s=3,c=colors[region],alpha=.8)
mx,my=np.array(d['median_xy'])/1000;ax2.axvline(mx,c='#666',ls='--',lw=.65);ax2.axhline(my,c='#666',ls='--',lw=.65)
for region,x,y in [('NW',1.1,8.5),('NE',7.6,8.5),('SW',1.1,1),('SE',7.6,1)]:ax2.text(x,y,f'{region}\n{len(d["regions"][region])} sources',fontsize=8,color=colors[region],bbox=dict(fc='white',ec='none',alpha=.85,pad=2))
ax2.scatter(ex[:,0]/1000,ex[:,1]/1000,c='#222',marker='*',s=32);ax2.autoscale();ax2.set_aspect('equal');ax2.set_xlabel('x (km)');ax2.set_ylabel('y (km)');ax2.set_title('(b) Four alarm regions');save(fig,'cad_geometry_3d')
# The step from shortest baseline to a small positive allowance includes tie choices.
fig,axes=plt.subplots(1,2,figsize=(10,3.55))
for region in ['NW','SW','SE','NE']:
 r=lookup(region);vals=[r[k]/r['n']*100 for k in ['baseline','cap_5','cap_10','cap_20','cap_50','cap_100','unlimited']];axes[0].plot(range(7),vals,marker='o',ms=4,lw=1.8,c=colors[region],label=region)
axes[0].set_xticks(range(7),['Shortest\nroute','5','10','20','50','100','No\nlimit']);axes[0].set_xlabel('Detour allowance (% extra distance)');axes[0].set_ylabel('Starting points protected at 30 min (%)');axes[0].set_ylim(48,102);axes[0].legend(ncol=2,loc='lower right');axes[0].set_title('(a) Longer detours protect more starting points');axes[0].grid(axis='y',alpha=.2)
for i,region in enumerate(['NW','SW','SE','NE']):
 vals=[lookup(region,t)['rescued'] for t in [10,20,30]];axes[1].plot([10,20,30],vals,marker='o',ms=4,lw=1.8,c=colors[region]);axes[1].annotate(f'{region}: {vals[-1]}',(30,vals[-1]),xytext=(5,0 if region!='NE' else -9),textcoords='offset points',fontsize=8,c=colors[region])
axes[1].set_xlim(8,35);axes[1].set_ylim(0,530);axes[1].set_xticks([10,20,30]);axes[1].set_xlabel('Delay target (min)');axes[1].set_ylabel('Extra starting points protected');axes[1].set_title('(b) Gain from rerouting, no detour limit');axes[1].grid(axis='y',alpha=.2);fig.tight_layout(w_pad=2);save(fig,'cad_detours')
# A simple example, selected to explain the mechanism, not as a prevalence estimate.
a=[json.loads(s) for s in (D/'full_SE.jsonl').read_text().splitlines()];r=next(r for r in a if r['node']=='P0036' and r['target_s']==1800);_,paths=nx.multi_source_dijkstra(G,sorted(d['exits']));baseline=paths[r['node']][::-1]
fig,ax=plt.subplots(figsize=(7.2,4.9));ax.add_collection(LineCollection([[xyz[a][:2]/1000,xyz[b][:2]/1000] for a,b in edges],colors='#d8dcde',linewidths=.5));
for path,color,label in [(baseline,'#c3473e','Shortest route: 6.195 km'),(r['path'],'#087f8c','Rerouted: 6.449 km (+4.1%)')]:
 q=np.array([xyz[n][:2]/1000 for n in path]);ax.plot(q[:,0],q[:,1],color=color,lw=2,label=label)
point=xyz[r['node']][:2]/1000;ax.scatter(*point,c='black',s=25,zorder=5);ax.annotate('Start: P0036',point,xytext=(8,8),textcoords='offset points',fontsize=9)
for node,offset in [(baseline[-1],(-85,-18)),(r['path'][-1],(-90,18))]:
 point=xyz[node][:2]/1000;ax.scatter(*point,c='black',marker='*',s=60,zorder=5);ax.annotate('Shaft '+node,point,xytext=offset,textcoords='offset points',arrowprops=dict(arrowstyle='-',color='#777',lw=.6),fontsize=8)
ax.set_xlim(2.8,9.65);ax.set_ylim(1.6,7.3);ax.set_aspect('equal');ax.set_xlabel('x (km)');ax.set_ylabel('y (km)');ax.legend(loc='upper left',framealpha=.95);save(fig,'cad_route_example')
# Spatial pattern of the gains.
fig,axes=plt.subplots(2,2,figsize=(8.4,8.0))
for ax,region in zip(axes.flat,['NW','SW','SE','NE']):
 a=[json.loads(s) for s in (D/f'full_{region}.jsonl').read_text().splitlines()];a=[r for r in a if r['target_s']==1800 and not r['inside_region']];ax.add_collection(LineCollection([[xyz[u][:2]/1000,xyz[v][:2]/1000] for u,v in edges],colors='#d3d7d9',linewidths=.4))
 src=np.array([xyz[n][:2]/1000 for n in d['regions'][region]]);ax.scatter(src[:,0],src[:,1],s=2,c='#a9a0b7',alpha=.6)
 for color,test,size in [('#368b7b',lambda r:r['baseline_s']>=1800,2),('#d87a22',lambda r:r['status']=='solved' and r['baseline_s']<1800,7),('#b5303c',lambda r:r['status']!='solved',7)]:
  q=np.array([xyz[r['node']][:2]/1000 for r in a if test(r)])
  if len(q):ax.scatter(q[:,0],q[:,1],s=size,c=color)
 ax.scatter(ex[:,0]/1000,ex[:,1]/1000,c='#111',marker='*',s=18);ax.autoscale();ax.set_aspect('equal');ax.set_title(f'{region}: {lookup(region)["rescued"]} starting points newly protected');ax.set_xlabel('x (km)');ax.set_ylabel('y (km)')
handles=[Line2D([],[],ls='',marker='o',ms=4,c=c,label=l) for c,l in [('#a9a0b7','Possible sources'),('#368b7b','Shortest route works'),('#d87a22','Protected only by rerouting'),('#b5303c','Not protected')]];fig.legend(handles=handles,loc='lower center',ncol=2,fontsize=8);fig.tight_layout(rect=[0,.06,1,1]);save(fig,'cad_spatial')
# Numerical tables are generated rather than retyped.
def write(name,lines): (T/name).write_text('\n'.join(line.rstrip(chr(92))+chr(92)*2 for line in lines)+'\n'+chr(92)+'bottomrule\n')
write('main_rows.tex',[f"{reg} & {lookup(reg)['source_count']:,} & {lookup(reg)['n']:,} & {lookup(reg)['baseline']:,} & {lookup(reg)['cap_20']:,} & {lookup(reg)['cap_50']:,} & {lookup(reg)['unlimited']:,} & {lookup(reg)['rescued']:,} \\\\" for reg in ['NW','SW','SE','NE']])
write('inside_rows.tex',[f"{reg} & {lookup(reg,group='inside')['n']} & {lookup(reg,group='inside')['baseline']} & {lookup(reg,group='inside')['unlimited']} & {lookup(reg,group='inside')['impossible_even_with_source_known']} & {lookup(reg,group='inside')['no_common_route']} \\\\" for reg in ['NW','SW','SE','NE']])
write('near_rows.tex',[f"{reg} & {lookup(reg,source='near')['source_count']} & {lookup(reg,source='near')['baseline']:,} & {lookup(reg,source='near')['unlimited']:,} & {lookup(reg,source='near')['rescued']} \\\\" for reg in ['NW','SW','SE','NE']])
lines=[]
for reg in ['NW','SW','SE','NE']:
 a=[json.loads(s) for s in (D/'high_flow'/f'{reg}.jsonl').read_text().splitlines()];a=[r for r in a if not r['inside_region']];st=next(r for r in json.loads((D/'stress.json').read_text())['rows'] if r['region']==reg and r['group']=='outside' and r['flow_m3_s']==1.)
 lines.append(f"{reg} & {lookup(reg)['unlimited']:,} & {st['retained']:,} & {sum(r['baseline_s']>=1800 for r in a):,} & {sum(r['status']=='solved' for r in a):,} \\\\")
write('flow_rows.tex',lines)
print('Generated four figures and four tables from stored records')
