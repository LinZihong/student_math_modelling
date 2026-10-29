"""Shared data and solvers for the v9 study: fixed escape routes when the alarm reports only a zone.

Flood schedules (fields/) and single-source latest-departure maps (upper/) are reused from
实验_07; this module only slices them by zone and adds the zone-avoiding rule.
"""
import sys,json,math,heapq
from pathlib import Path
import numpy as np
import networkx as nx
ROOT=Path(__file__).resolve().parents[1];E7=ROOT/'实验_07_分区预警与固定路线_全分区分析'
sys.path.insert(0,str(E7))
import engine
OUT=Path(__file__).resolve().parent
DESIGN=json.loads((E7/'design.json').read_text())
NODES=sorted(DESIGN['nodes']);NIDX={n:i for i,n in enumerate(NODES)}
SOURCES=sorted(set().union(*map(set,DESIGN['regions'].values())));SIDX={s:i for i,s in enumerate(SOURCES)}
EDGES=[tuple(x) for x in DESIGN['arcs']];EXITS=set(DESIGN['exits'])
XYZ={k:np.array(v) for k,v in DESIGN['nodes'].items()}

class Fields:
 """All 1,587 single-source flood schedules held once in memory, for one inflow factor."""
 def __init__(self,factor=1.):
  data=[np.load(E7/'fields'/f'{s}.npz') for s in SOURCES]
  self.wet=np.array([d['wet'] for d in data])/factor;self.block=np.array([d['block'] for d in data])/factor
  self.vwet=np.array([np.where(d['along'],.7,.5) for d in data])
  for d in data:d.close()
  self.U=np.array([np.load(E7/'upper'/f'{s}_q{factor}.npy') for s in SOURCES]);self.factor=factor

def zone_dataset(fields,zone):
 """An engine.Dataset restricted to the sources of one alarm zone, without re-reading files."""
 d=object.__new__(engine.Dataset);k=[SIDX[s] for s in sorted(zone)]
 d.directory=E7;d.design=DESIGN;d.sources=sorted(zone);d.nodes=NODES;d.nidx=NIDX;d.edges=EDGES
 d.aidx={(a,b):i for i,(a,b,L) in enumerate(EDGES)};d.exits=EXITS;d.cache=engine.OrderedDict()
 d.G=GRAPH;d.dist,d.paths=DIST,PATHS
 d.wet=fields.wet[k];d.block=fields.block[k];d.vwet=fields.vwet[k];d.vdry=1.3;d.U=fields.U[k]
 d.baseline=np.full_like(d.U,math.inf)
 for n in BASE_ORDER:
  parent=PATHS[n][-2];d.baseline[:,NIDX[n]]=d.arc_latest(d.aidx[n,parent],d.baseline[:,NIDX[parent]])
 return d

GRAPH=nx.Graph();GRAPH.add_weighted_edges_from(EDGES)
DIST,PATHS=nx.multi_source_dijkstra(GRAPH,sorted(EXITS))
BASE_ORDER=[n for n in sorted(NODES,key=lambda n:DIST[n]) if n not in EXITS]

def avoid_route(origin,zone):
 """Planner's rule: among routes to a shaft, take the shortest of those with the least length inside the zone.

 A tunnel counts as inside the zone if either end is a zone junction (the origin itself is exempt)."""
 inside=set(zone)-{origin};BIG=1e4
 def w(a,b,e):return e['weight']*(1+BIG*((a in inside) or (b in inside)))
 dist,path=nx.single_source_dijkstra(GRAPH,origin,weight=w)
 best=min((dist[x],x) for x in EXITS if x in dist)[1];return path[best]

def evaluate(d,path,target):
 """Latest safe departure of a fixed path over the zone's sources, and whether it meets the target."""
 dl=d.path_deadlines(path);m=float(dl.min());L=sum(GRAPH[a][b]['weight'] for a,b in zip(path,path[1:]))
 return m,L
