"""Two-departure exact label search. No hydraulic assumptions beyond FIFO arcs.

The optimization minimizes arrival at t0 among fixed routes also feasible at d.
All comparisons use full float precision; there is no label cap or epsilon pruning.
"""
import heapq
import math
from dataclasses import dataclass


def latest_network(adj, exits):
    incoming = {}
    for aa in adj.values():
        for a in aa:
            incoming.setdefault(a.b, []).append(a)
    D = {x: math.inf for x in exits}
    queue = [(-math.inf, x) for x in sorted(exits)]
    done = set()
    heapq.heapify(queue)
    while queue:
        nd,v=heapq.heappop(queue)
        if v in done or -nd != D[v]: continue
        done.add(v)
        for a in incoming.get(v,[]):
            if a.a in done: continue
            z=a.latest_entry(D[v])
            if z>D.get(a.a,-math.inf):
                D[a.a]=z
                heapq.heappush(queue,(-z,a.a))
    return D


@dataclass
class Label:
    node: str
    nominal: float
    delayed: float
    parent: int
    arc: object
    active: bool = True


def constrained(adj, start, exits, t0, d, D=None):
    if d < t0: raise ValueError('d must be at least t0')
    if D is None: D=latest_network(adj,exits)
    stats={'generated':1,'expanded':0,'max_labels_at_node':1}
    if d>D.get(start,-math.inf)+1e-8: return math.inf,[],stats
    labels=[Label(start,t0,d,-1,None)]
    at={start:[0]}
    queue=[(t0,d,0)]
    while queue:
        x,y,i=heapq.heappop(queue)
        label=labels[i]
        if not label.active: continue
        stats['expanded']+=1
        if label.node in exits:
            path=[]
            while labels[i].parent>=0:
                path.append(labels[i].arc)
                i=labels[i].parent
            return x,path[::-1],stats
        for a in adj.get(label.node,[]):
            yy=a.exit_time(y)
            if not math.isfinite(yy) or yy>D.get(a.b,-math.inf)+1e-8: continue
            xx=a.exit_time(x)
            if not math.isfinite(xx): continue
            live=[j for j in at.get(a.b,[]) if labels[j].active]
            if any(labels[j].nominal<=xx and labels[j].delayed<=yy for j in live): continue
            for j in live:
                if xx<=labels[j].nominal and yy<=labels[j].delayed:
                    labels[j].active=False
            k=len(labels)
            labels.append(Label(a.b,xx,yy,i,a))
            at[a.b]=[j for j in live if labels[j].active]+[k]
            stats['max_labels_at_node']=max(stats['max_labels_at_node'],len(at[a.b]))
            stats['generated']+=1
            heapq.heappush(queue,(xx,yy,k))
    return math.inf,[],stats


def budget_deadline(adj,start,exits,t0,budget,D=None,tolerance=.01):
    """Bracket max feasible departure for arrival <= budget, within tolerance seconds."""
    if D is None: D=latest_network(adj,exits)
    lo,hi=t0,D.get(start,-math.inf)
    if not math.isfinite(hi): raise ValueError('This experiment requires a finite deadline')
    cost,path,_=constrained(adj,start,exits,t0,lo,D)
    if cost>budget: return None
    best=path
    queries=1
    while hi-lo>tolerance:
        d=(hi+lo)/2
        cost,path,_=constrained(adj,start,exits,t0,d,D)
        queries+=1
        if cost<=budget+1e-8: lo,best=d,path
        else: hi=d
    return lo,hi,best,queries
