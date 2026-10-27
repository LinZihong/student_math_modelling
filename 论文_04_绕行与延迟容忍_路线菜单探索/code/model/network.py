"""Tunnel networks: reading the competition workbooks and inserting points into tunnels."""
import math

import networkx as nx
import pandas as pd


def load_workbook(path):
    """Read a workbook with sheets 端点 (id, x, y, z) and 巷道 (id, node 1, node 2), one header row."""
    nodes = pd.read_excel(path, sheet_name='端点', header=None, skiprows=1)
    edges = pd.read_excel(path, sheet_name='巷道', header=None, skiprows=1)
    G = nx.Graph()
    for nid, x, y, z in nodes.itertuples(index=False):
        G.add_node(str(nid), xyz=(float(x), float(y), float(z)))
    for eid, a, b in edges.itertuples(index=False):
        a, b = str(a), str(b)
        G.add_edge(a, b, id=str(eid), length=math.dist(G.nodes[a]['xyz'], G.nodes[b]['xyz']))
    return G


def save_workbook(G, path, title_x='x (m)', title_y='y (m)', title_z='z (m)'):
    """Write G in the competition layout (one header row)."""
    nodes = sorted(G.nodes())
    with pd.ExcelWriter(path) as xw:
        pd.DataFrame([[n, *[round(c, 3) for c in G.nodes[n]['xyz']]] for n in nodes],
                     columns=['端点编号', title_x, title_y, title_z]).to_excel(xw, sheet_name='端点', index=False)
        pd.DataFrame([[d['id'], u, v] for u, v, d in sorted(G.edges(data=True), key=lambda e: e[2]['id'])],
                     columns=['巷道编号', '巷道端点1', '巷道端点2']).to_excel(xw, sheet_name='巷道', index=False)


def insert_point(G, xyz, name, tol=0.05):
    """Add `name` at xyz. If xyz is (within tol) an existing node, return that node instead;
    otherwise split the nearest tunnel at the projection of xyz and return `name`.
    Returns (node, distance from xyz to the network)."""
    best = None
    for u, v, d in G.edges(data=True):
        a, b = G.nodes[u]['xyz'], G.nodes[v]['xyz']
        ab = [b[k] - a[k] for k in range(3)]
        L2 = sum(c * c for c in ab)
        s = 0.0 if L2 == 0 else max(0.0, min(1.0, sum((xyz[k] - a[k]) * ab[k] for k in range(3)) / L2))
        p = [a[k] + s * ab[k] for k in range(3)]
        dist = math.dist(p, xyz)
        if best is None or dist < best[0]:
            best = (dist, u, v, s, p)
    dist, u, v, s, p = best
    L = G.edges[u, v]['length']
    if s * L <= tol:
        return u, dist
    if (1 - s) * L <= tol:
        return v, dist
    eid = G.edges[u, v]['id']
    orig = G.edges[u, v].get('parent', eid)
    G.remove_edge(u, v)
    G.add_node(name, xyz=tuple(p))
    G.add_edge(u, name, id=f'{eid}/{name}a', length=s * L, parent=orig)
    G.add_edge(name, v, id=f'{eid}/{name}b', length=(1 - s) * L, parent=orig)
    return name, dist
