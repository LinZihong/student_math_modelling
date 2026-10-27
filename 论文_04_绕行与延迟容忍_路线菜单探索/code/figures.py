"""Tables and publication figures generated only from completed experiment outputs."""
import json
import math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from run import OUT,PAPER,dataset

FIG=PAPER/'figures'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.spines.top':False,
 'axes.spines.right':False,'savefig.dpi':220,'axes.labelsize':9,'legend.fontsize':8})
COLORS=['#1f5787','#d07825','#367b65','#885a9d']


def save(fig,name):
    fig.savefig(FIG/f'{name}.png',bbox_inches='tight',facecolor='white')
    plt.close(fig)


def main():
    FIG.mkdir(exist_ok=True)
    origins=pd.read_csv(OUT/'origins.csv')
    menus=pd.read_csv(OUT/'menus.csv')
    curves=pd.read_csv(OUT/'extended_curves.csv')
    sens=pd.read_csv(OUT/'sensitivity.csv')
    stats={};tex=[]
    # Network geometry; identify the base inrush and supplied illustrative positions.
    fig,axs=plt.subplots(1,2,figsize=(7.1,3.4))
    for ax,case,title in zip(axs,['competition','cad'],['Competition network 2','CAD-derived network']):
        G,adj,exits,miners,meta=dataset(case)
        pos={n:np.array(G.nodes[n]['xyz'][:2])/1000 for n in G}
        ax.add_collection(LineCollection([[pos[u],pos[v]] for u,v in G.edges()],colors='#b7c1ca',linewidths=.5))
        for n in exits:ax.scatter(*pos[n],marker='^',s=35,c=COLORS[2],zorder=3)
        ax.scatter(*pos['A'],marker='*',s=95,c='#b43b35',zorder=4)
        for name,n in miners.items():
            ax.scatter(*pos[n],s=15,c='#172d42',zorder=3)
            ax.annotate(name,pos[n],xytext=(3,4),textcoords='offset points',fontsize=7)
        ax.autoscale();ax.set_aspect('equal');ax.set_title(title);ax.set_xlabel('x (km)');ax.set_ylabel('y (km)')
    fig.tight_layout();save(fig,'networks')
    # Cost of protecting a later departure, normalized only for display.
    fig,axs=plt.subplots(2,2,figsize=(7.1,4.5))
    for ax,(case,name) in zip(axs.ravel(),[('competition','S31'),('competition','M1'),('cad','M2'),('cad','M3')]):
        c=curves[(curves['case']==case)&(curves.origin==name)].sort_values('departure_min')
        r=origins[(origins['case']==case)&(origins.origin==name)].iloc[0]
        x=(c.departure_min-1)/(r.network_deadline_min-1)
        oracle_cost=100*(c.replan_nominal_min-r.nominal_arrival_min)/r.travel_min
        ax.plot(x,c.extra_percent,'o-',ms=2.4,lw=1,color=COLORS[0],label='Two-departure optimum')
        ax.plot(x,oracle_cost,'x--',ms=3,lw=.7,color=COLORS[1],label='Replan-at-delay baseline')
        ax.axhline(5,color='#a3a3a3',lw=.7,ls=':')
        ax.set_title(f'{case.capitalize()} / {name}');ax.set_xlabel('Required delay / maximum feasible delay');ax.set_ylabel('Extra nominal travel (%)')
        ax.grid(alpha=.15)
    axs[0,0].legend(loc='upper left');fig.tight_layout();save(fig,'cost_curves')
    # Horizon-capped apparent gains.
    fig,ax=plt.subplots(figsize=(6.6,2.9))
    for j,(case,label) in enumerate([('competition','Competition'),('cad','CAD')]):
        g=origins[(origins['case']==case)&origins.origin.str.startswith('S')]
        b=g.fastest_deadline_min;d=g['budget0.05_deadline_min']
        vals=[int(sum(d-b>1/60)),int(sum(np.minimum(d,180)-np.minimum(b,180)>1/60)),int(sum(np.minimum(d,60)-np.minimum(b,60)>1/60))]
        stats[case]={'sample_size':len(g),'horizon_counts':vals}
        ax.bar(np.arange(3)+(j-.5)*.32,vals,width=.32,label=label,color=COLORS[j])
        for k,v in enumerate(vals):ax.text(k+(j-.5)*.32,v+.5,str(v),ha='center',fontsize=8)
    ax.set_xticks(range(3),['No horizon','180-minute horizon','60-minute horizon']);ax.set_ylabel('Origins gaining > 1 s (out of 40)');ax.set_ylim(0,40);ax.legend();fig.tight_layout();save(fig,'horizons')
    # Held-out source menu coverage; separate quality from mere feasibility in tables.
    fig,axs=plt.subplots(1,2,figsize=(7.1,2.9),sharey=True)
    menurows=[]
    for ax,case in zip(axs,['competition','cad']):
        g=menus[(menus['case']==case)&menus.origin.str.startswith('S')]
        base=g[g.k==1];den=int(base.test_possible.sum())
        vals=[100*base.nominal_route_test_covered.sum()/den]
        for k in [1,2,3]:
            z=g[g.k==k]
            vals.append(100*z.test_covered.sum()/den)
            menurows.append((case,k,int(z.train_covered.sum()),int(z.train_possible.sum()),int(z.test_covered.sum()),den,int(z.test_feasible.sum())))
        stats[case]['menu_denominator']=den;stats[case]['menu_coverage_pct']=vals
        ax.bar(range(4),vals,color=['#9aa4ad',*COLORS[:3]])
        for i,v in enumerate(vals):ax.text(i,v+.4,f'{v:.1f}',ha='center',fontsize=8)
        ax.set_xticks(range(4),['Nominal','Best 1','Best 2','Best 3']);ax.set_title(case.capitalize());ax.set_ylim(70,103)
    axs[0].set_ylabel('Held-out timely coverage (%)');fig.tight_layout();save(fig,'menus')
    # All manuscript tables use the same precision and results files.
    tex.append(r'\begin{tabular}{llrrrr}\toprule Network & Origin & Travel (min) & $D(P_0)$ (h) & $D_{.05}$ (h) & $D^*$ (h)\\\midrule')
    for r in origins[origins.origin.str.startswith('M')].to_dict('records'):
        tex.append(f"{r['case'].capitalize()} & {r['origin']} & {r['travel_min']:.2f} & {r['fastest_deadline_min']/60:.2f} & {r['budget0.05_deadline_min']/60:.2f} & {r['network_deadline_min']/60:.2f} \\")
        tex[-1]+='\\'
    tex.append(r'\bottomrule\end{tabular}')
    (OUT/'named_table.tex').write_text('\n'.join(tex))
    tex=[r'\begin{tabular}{lrrrrr}\toprule Network & $K$ & Train & Test & Test (\%) & Feasible (\%)\\\midrule']
    for case,k,tr,trden,te,teden,fe in menurows:
        tex.append(f'{case.capitalize()} & {k} & {tr}/{trden} & {te}/{teden} & {100*te/teden:.2f} & {100*fe/teden:.2f} '+r'\\')
    tex.append(r'\bottomrule\end{tabular}')
    (OUT/'menu_table.tex').write_text('\n'.join(tex))
    agg=[]
    for (case,factor,wet,rule),g in sens[sens.origin.str.startswith('S')].groupby(['case','Q_factor','wet_speed','tie_rule'],dropna=False):
        b=g.baseline_deadline_min;d=g.budget5_deadline_min
        agg.append({'case':case,'Q_factor':factor,'wet_speed':None if math.isnan(wet) else wet,'tie_rule':rule,
            'raw_count':int(sum(d-b>1/60)),'h60_count':int(sum(np.minimum(d,60)-np.minimum(b,60)>1/60)),
            'h180_count':int(sum(np.minimum(d,180)-np.minimum(b,180)>1/60))})
    stats['sensitivity']=agg
    stats['queries_extended']=len(curves);stats['max_labels']=int(curves.max_labels_at_node.max())
    stats['max_replan_gap_min']=float((curves.replan_nominal_min-curves.optimal_nominal_min).max())
    (OUT/'paper_stats.json').write_text(json.dumps(stats,indent=2))


if __name__=='__main__':main()
