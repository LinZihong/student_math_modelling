"""Exact finite-source constraint generation with vector full-set validation."""
import sys,json,math,time,heapq
from pathlib import Path
from collections import OrderedDict
import numpy as np
import networkx as nx
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'实验_06_分区预警与固定路线_初期分析'),str(ROOT/'论文_04_绕行与延迟容忍_路线菜单探索/code')]
from study import feasible
from model.routing import Arc,latest_departure,walk
from robust import latest_network
OUT=Path(__file__).resolve().parent

class Dataset:
 def __init__(self,sources,factor=1.,directory=OUT):
  self.directory=directory;self.design=json.loads((directory/'design.json').read_text());self.sources=list(sources);self.nodes=sorted(self.design['nodes']);self.nidx={n:i for i,n in enumerate(self.nodes)}
  self.edges=[tuple(x) for x in self.design['arcs']];self.aidx={(a,b):i for i,(a,b,L) in enumerate(self.edges)};self.exits=set(self.design['exits']);self.cache=OrderedDict()
  self.G=nx.Graph();self.G.add_weighted_edges_from(self.edges);self.dist,self.paths=nx.multi_source_dijkstra(self.G,sorted(self.exits))
  data=[np.load(directory/'fields'/f'{s}.npz') for s in sources]
  self.wet=np.array([d['wet'] for d in data])/factor;self.block=np.array([d['block'] for d in data])/factor;self.vwet=np.array([np.where(d['along'],.7,.5) for d in data]);self.vdry=1.3
  for d in data:d.close()
  self.U=np.empty((len(sources),len(self.nodes)))
  for i,s in enumerate(sources):
   p=directory/'upper'/f'{s}_q{factor}.npy'
   if p.exists():self.U[i]=np.load(p)
   else:
    adj,look=self.lookup(i);D=latest_network(adj,self.exits);self.U[i]=[D.get(n,-math.inf) for n in self.nodes];p.parent.mkdir(exist_ok=True);np.save(p,self.U[i])
  self.baseline=np.full_like(self.U,math.inf)
  for n in sorted(self.nodes,key=lambda n:self.dist[n]):
   if n not in self.exits:
    parent=self.paths[n][-2];self.baseline[:,self.nidx[n]]=self.arc_latest(self.aidx[n,parent],self.baseline[:,self.nidx[parent]])
 def lookup(self,k):
  if k in self.cache:
   self.cache.move_to_end(k);return self.cache[k]
  adj={};look={}
  for j,(a,b,L) in enumerate(self.edges):
   arc=Arc(a,b,L,float(self.wet[k,j]),float(self.block[k,j]),True,(self.vdry,float(self.vwet[k,j]),1));adj.setdefault(a,[]).append(arc);look[a,b]=arc
  self.cache[k]=(adj,look)
  if len(self.cache)>24:self.cache.popitem(last=False)
  return adj,look
 def scenario(self,k):
  adj,look=self.lookup(k);return adj,look,{n:float(self.U[k,i]) for i,n in enumerate(self.nodes)}
 def arc_latest(self,j,deadlines):
  end=np.minimum(deadlines,self.block[:,j]);wetdist=self.vwet[:,j]*np.maximum(0.,end-self.wet[:,j]);L=self.edges[j][2]
  return np.where(L<=wetdist,end-L/self.vwet[:,j],np.minimum(end,self.wet[:,j])-(L-wetdist)/self.vdry)
 def path_deadlines(self,path):
  d=np.full(len(self.sources),math.inf)
  for a,b in reversed(list(zip(path,path[1:]))):d=self.arc_latest(self.aidx[a,b],d)
  return d
 def solve(self,origin,target,limit=30.):
  start=time.monotonic();idx=self.nidx[origin];upper=float(self.U[:,idx].min());base=float(self.baseline[:,idx].min());worst=int(np.argmin(self.baseline[:,idx]));active=[worst]
  result={'node':origin,'target_s':target,'baseline_s':base,'shortest_length_m':self.dist[origin],'source_known_upper_s':upper}
  if upper<target-1e-8:return {**result,'status':'impossible_even_with_source_known','witness_source':self.sources[int(np.argmin(self.U[:,idx]))]}
  if base>=target:
   return {**result,'status':'solved','length_m':self.dist[origin],'extra_fraction':0.,'deadline_s':base,'path':self.paths[origin][::-1],'active_sources':0,'iterations':0}
  while True:
   if time.monotonic()-start>limit:return {**result,'status':'timeout','active_sources':len(active)}
   try:p,_=feasible(origin,self.exits,[self.scenario(k) for k in active],self.dist,math.inf,target,timeout=min(3.,max(.01,limit-(time.monotonic()-start))))
   except TimeoutError:return {**result,'status':'timeout','active_sources':len(active)}
   if p is None:return {**result,'status':'no_common_route','witness_sources':[self.sources[k] for k in active]}
   d=self.path_deadlines(p);worst=int(np.argmin(d));minimum=float(d[worst])
   if minimum>=target-1e-7:
    length=sum(self.G[a][b]['weight'] for a,b in zip(p,p[1:]));return {**result,'status':'solved','length_m':length,'extra_fraction':length/self.dist[origin]-1,'deadline_s':minimum,'path':p,'active_sources':len(active),'iterations':len(active),'binding_source':self.sources[worst]}
   if worst in active:raise ArithmeticError('Scalar and vector feasibility conflict')
   active.append(worst)
