from pathlib import Path
import json,shutil
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
P=Path(__file__).resolve().parent;R=P.parent/'实验_06_分区预警与固定路线_初期分析'
rows=json.loads((R/'longer_summary.json').read_text())
fig,ax=plt.subplots(figsize=(8,3.5),layout='constrained')
for r,color in zip(rows,['#168a78','#2572ad','#b85a31']):
 y=[r['baseline_success']]+[r['success_by_budget'][str(e)] for e in [.05,.1,.2,.5,1]]+[r['unlimited_success']]
 ax.plot(range(7),y,'o-',color=color,label=f"{int(r['target_min'])}-minute delay")
ax.set_xticks(range(7),['Baseline','+5%','+10%','+20%','+50%','+100%','Unlimited']);ax.set_ylabel('Origins meeting target (out of 548)');ax.set_xlabel('Distance allowance over dry shortest route');ax.set_ylim(240,560);ax.grid(axis='y',alpha=.2);ax.legend(frameon=False);fig.savefig(P/'figures/target_counts.png',dpi=220)
shutil.copy2(R/'regional_result.png',P/'figures/source_coverage.png')
import sys
sys.path.insert(0,str(R))
from study import Arc,latest_departure
sources=json.loads((R/'dense_results.json').read_text());opt=next(x for x in json.loads((R/'dense_optimum.json').read_text()) if x['eps']==.05 and x['speeds'][0]==4)
full=[]
for row in sources:
 data=json.loads((R/'dense_SE'/f"{row['source']}.json").read_text());lookup={(a,b):Arc(a,b,L,w,bk,True,(vd,vw,vw)) for a,b,L,w,bk,vd,vw in data['arcs']}
 full.append(latest_departure([lookup[u,v] for u,v in zip(opt['path'],opt['path'][1:])])/60)
fig,ax=plt.subplots(figsize=(7.5,3.7),layout='constrained')
for vals,c,label in [([x['baseline_path']/60 for x in sources],'#c74c3c','Dry shortest route'),([x['path']/60 for x in sources],'#d59516','Route designed on 8 sources'),(full,'#007d96','Route designed on all 113 nodes')]:
 ax.plot(range(1,114),[max(0,min(60,v)) for v in vals],'.',ms=4,color=c,label=label)
ax.axhline(opt['actual_deadline_s']/60,color='#007d96',ls='--',lw=1)
ax.set_xlabel('Southeast source node (sorted identifier)');ax.set_ylabel('Latest departure after inrush (min)');ax.set_ylim(-2,64);ax.legend(fontsize=9,loc='lower right');ax.grid(axis='y',alpha=.15)
fig.savefig(P/'figures/source_coverage.png',dpi=220)
