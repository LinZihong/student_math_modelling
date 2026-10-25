"""Hydraulic bookkeeping checks and time-horizon / input sensitivity diagnostics."""
import json
import math
import time
import pandas as pd
import networkx as nx
from run import OUT,setup,dataset,save_csv,T0
from model.flood import Flood
from model.routing import Arc,fastest,latest_departure,walk
from robust import latest_network,budget_deadline,constrained


def transformed(adj,factor=1.,wet_speed=None):
    return {n:[Arc(a.a,a.b,a.L,a.wet/factor,a.block/factor,a.speed[1]==2.,
        (4.,2.,1.) if wet_speed is None else (4.,wet_speed,wet_speed)) for a in aa] for n,aa in adj.items()}


def main():
    audits=[];sens=[];detail=[]
    origins=pd.read_csv(OUT/'origins.csv')
    for case in ['competition','cad']:
        G,source,exits,W,miners,n0,e0=setup(case)
        f=Flood(G,[(source,0.,.5)],W=W);f.run()
        fq=Flood(G,[(source,0.,.75)],W=W);fq.run()
        ratios=[]
        for k,e in f.E.items():
            for name in ['t_in','t_cov','t_block','t_full']:
                a,b=getattr(e,name),getattr(fq.E[k],name)
                if math.isfinite(a) and a>0:ratios.append(abs(b/a-1/1.5))
        R=nx.Graph()
        R.add_nodes_from(reversed(list(G.nodes(data=True))))
        R.add_edges_from(reversed(list(G.edges(data=True))))
        fr=Flood(R,[(source,0.,.5)],W=W);fr.run()
        diff=[abs(e.t_block-fr.E[k].t_block) for k,e in f.E.items()]
        ft=Flood(G,[(source,0.,.5)],W=W,reverse_ties=True);ft.run()
        tiediff=[abs(e.t_block-ft.E[k].t_block) for k,e in f.E.items()]
        audits.append({'case':case,'scaling_comparisons':len(ratios),'scaling_max_error':max(ratios),
            'reverse_order_max_block_difference_s':max(diff),
            'reverse_tie_rule_max_block_difference_s':max(tiediff),
            'reversed_volume_residual':fr.max_residual,'scaled_volume_residual':fq.max_residual})
        H,adj,exits,miners,meta=dataset(case)
        alternate={}
        by_id={G.edges[e.u,e.v]['id']:e for e in ft.E.values()}
        for u,v,data in H.edges(data=True):
            e=by_id[data['parent']]
            src,dst=G.nodes[e.src]['xyz'],G.nodes[e.other(e.src)]['xyz']
            for a,b in [(u,v),(v,u)]:
                x,y=H.nodes[a]['xyz'],H.nodes[b]['xyz']
                along=sum((dst[k]-src[k])*(y[k]-x[k]) for k in range(3))>0
                alternate.setdefault(a,[]).append(Arc(a,b,data['length'],e.t_in,e.t_block,along))
        for factor,wet_speed,rule in [(2/3,None,'base'),(1.5,None,'base'),(2.,None,'base'),(1.,1.,'base'),(1.,None,'reverse_ties')]:
            aa=alternate if rule=='reverse_ties' else transformed(adj,factor,wet_speed)
            D=latest_network(aa,exits)
            for row in origins[origins['case']==case].itertuples():
                s=row.node
                base,p=fastest(aa,s,exits,T0)
                if not math.isfinite(base):
                    sens.append({'case':case,'origin':row.origin,'Q_factor':factor,'wet_speed':wet_speed,'tie_rule':rule,'feasible':False})
                    continue
                lo,hi,path,_=budget_deadline(aa,s,exits,T0,T0+1.05*(base-T0),D)
                sens.append({'case':case,'origin':row.origin,'Q_factor':factor,'wet_speed':wet_speed,
                    'tie_rule':rule,
                    'feasible':True,'baseline_deadline_min':latest_departure(p)/60,
                    'budget5_deadline_min':lo/60,'network_deadline_min':D[s]/60})
            print(case,'sensitivity',factor,wet_speed,flush=True)
        # Observe complete model-relative range, not just the first hour.
        D=latest_network(adj,exits)
        selected=list(miners.items())
        if case=='competition':selected.append(('S31',origins[(origins['case']==case)&(origins.origin=='S31')].iloc[0].node))
        for name,s in selected:
            base,p=fastest(adj,s,exits,T0)
            b=latest_departure(p)
            ds=sorted(set([T0+(D[s]-T0)*k/30 for k in range(31)]+[b,b+.1]))
            for d in ds:
                if d>D[s]:continue
                c,p,st=constrained(adj,s,exits,T0,d,D)
                _,q=fastest(adj,s,exits,d)
                if math.isfinite(c):
                    detail.append({'case':case,'origin':name,'departure_min':d/60,
                        'optimal_nominal_min':c/60,'replan_nominal_min':walk(q,T0)[0]/60,
                        'extra_percent':100*(c-base)/(base-T0),**st})
    (OUT/'hydraulic_audit.json').write_text(json.dumps(audits,indent=2))
    save_csv('sensitivity.csv',sens);save_csv('extended_curves.csv',detail)


if __name__=='__main__':main()
