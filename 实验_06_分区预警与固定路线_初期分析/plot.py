import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from pathlib import Path
from study import OUT,Arc,latest_departure
D=json.loads((OUT/'competition/design.json').read_text());xy=D['nodes'];r=next(x for x in json.loads((OUT/'results.json').read_text()) if x['case']=='competition' and x['region']=='SE' and x['node']=='P0104' and x['eps']==.05);o=next(x for x in json.loads((OUT/'dense_optimum.json').read_text()) if x['eps']==.05 and x['speeds'][0]==4)
fig,axes=plt.subplots(1,2,figsize=(12,4.7),layout='constrained');ax=axes[0]
ax.add_collection(LineCollection([[(xy[u][0],xy[u][1]),(xy[v][0],xy[v][1])] for u,v,_ in D['edges']],colors='#d0d4d8',linewidths=.5))
for p,c,l in [(r['baseline_path'],'#c74c3c','Shortest route: 2,701 m'),(o['path'],'#007d96','Regional route: 2,769 m')]:ax.plot([xy[n][0] for n in p],[xy[n][1] for n in p],color=c,lw=2,label=l)
ax.scatter(*xy['P0104'][:2],color='black',s=30,zorder=5);ax.annotate('Worker P0104',xy['P0104'][:2],xytext=(-75,-20),textcoords='offset points',fontsize=9)
ax.autoscale();ax.set_aspect('equal');route_nodes=set(r['baseline_path']+o['path']);xmin=min(xy[n][0] for n in route_nodes)-200;xmax=max(xy[n][0] for n in route_nodes)+200;ymin=min(xy[n][1] for n in route_nodes)-200;ymax=max(xy[n][1] for n in route_nodes)+200;mx,my=D['median_xy'];ax.fill_between([mx,xmax],ymin,my,color='#edc66c',alpha=.25,label='Illustrative SE alarm region');ax.set_xlim(xmin,xmax);ax.set_ylim(ymin,ymax);ax.set_xlabel('Map x (m)');ax.set_ylabel('Map y (m)');ax.legend(fontsize=8,loc='upper left');ax.set_title('One fixed route for an uncertain source')
rows=json.loads((OUT/'dense_results.json').read_text());pooled=[]
for row in rows:
 data=json.loads((OUT/'dense_SE'/f"{row['source']}.json").read_text());lookup={(a,b):Arc(a,b,L,w,bk,True,(vd,vw,vw)) for a,b,L,w,bk,vd,vw in data['arcs']};pooled.append(latest_departure([lookup[u,v] for u,v in zip(o['path'],o['path'][1:])])/60)
ax=axes[1]
for vals,c,label in [([x['baseline_path']/60 for x in rows],'#c74c3c','Shortest'),([x['path']/60 for x in rows],'#d59516','Designed on 8 sources'),(pooled,'#007d96','Designed on all 113 nodes')]:
 ax.plot(range(1,len(rows)+1),[max(0,min(60,v)) for v in vals],'.',ms=3,color=c,label=label)
ax.axhline(o['actual_deadline_s']/60,color='#007d96',lw=1,ls='--');ax.set_xlabel('SE source node (sorted ID)');ax.set_ylabel('Latest departure after inrush (min)');ax.set_title('Every source checked against the same route\nValues clipped to 0–60 min for display',fontsize=10);ax.set_ylim(-2,63);ax.legend(fontsize=8,loc='lower right');fig.suptitle('Exploratory volume-transfer model; not a field safety guarantee',fontsize=11)
fig.savefig(OUT/'regional_result.png',dpi=180)
