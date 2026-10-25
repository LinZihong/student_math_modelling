"""Extract an anonymized tunnel network from a mining plan (DWG -> JSON via libredwg).

Usage:
    dwgread -O JSON -o raw/plan.json raw/plan.dwg
    python scripts/extract_network.py raw/plan.json data/

Outputs (in data/), anonymized (rotated, mirrored, shifted; elevations relative to a hidden level):
    mine_network.xlsx    same layout as the CUMCM attachments: sheet 端点 (node id, x, y, z),
                         sheet 巷道 (tunnel id, node 1, node 2)
    mine_features.json   shafts, water-accumulation outlines, tunnel width
"""
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from shapely.geometry import LineString, MultiLineString, Point
from shapely.ops import nearest_points, unary_union
from shapely.strtree import STRtree

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from model.network import save_workbook  # noqa: E402

SNAP_TOL = 8.0          # m: bridge gaps up to this size between centerline ends and other lines
ELEV_RADIUS = 300.0     # m: survey labels used for interpolating a node's elevation
ROOF_RE = re.compile(r'[（(]\s*顶\s*(\d+(?:\.\d+)?)(?![\d.])')  # malformed labels such as "709..513" are skipped


def load_objects(path):
    txt = Path(path).read_bytes().decode('utf-8', errors='replace')
    # libredwg writes some malformed numbers ("123." and nan); patch them so the JSON parses
    txt = re.sub(r'(\d)\.(\s*[\],}])', r'\1.0\2', txt)
    txt = re.sub(r'\b(nan|-?inf)\b', 'null', txt)
    return json.loads(txt)['OBJECTS']


def collect_layers(objs):
    """Model-space geometry grouped by layer name."""
    layer = {o['handle'][-1]: o.get('name') for o in objs if o.get('object') == 'LAYER'}
    blocks = {o['handle'][-1]: o.get('name') for o in objs if o.get('object') == 'BLOCK_HEADER'}
    geo = defaultdict(lambda: {'lines': [], 'texts': [], 'inserts': []})
    for o in objs:
        t = o.get('entity')
        if not t or 'layer' not in o:
            continue
        if blocks.get(o.get('ownerhandle', [0])[-1]) not in ('*Model_Space', None):
            continue
        g = geo[layer.get(o['layer'][-1], '')]
        if t == 'LWPOLYLINE' and isinstance(o.get('points'), list):
            pts = [tuple(p[:2]) for p in o['points']]
            if o.get('flag', 0) & 512:
                pts.append(pts[0])
            g['lines'].append(pts)
        elif t == 'LINE':
            g['lines'].append([tuple(o['start'][:2]), tuple(o['end'][:2])])
        elif t in ('TEXT', 'MTEXT'):
            g['texts'].append((tuple(o['ins_pt'][:2]), o.get('text_value') or o.get('text', '')))
        elif t == 'INSERT':
            g['inserts'].append((tuple(o['ins_pt'][:2]), blocks.get(o['block_header'][-1])))
    return geo


def build_graph(centerlines):
    lines = []
    for pts in centerlines:
        pts = [p for i, p in enumerate(pts) if i == 0 or math.dist(p, pts[i - 1]) > 1e-6]
        if len(pts) >= 2 and LineString(pts).length > 1.0:
            lines.append(LineString(pts))
    # Bridge small gaps: join each dangling end to the nearest point of another line within SNAP_TOL
    tree = STRtree(lines)
    connectors = []
    for i, l in enumerate(lines):
        for end in (Point(l.coords[0]), Point(l.coords[-1])):
            best, bd = None, SNAP_TOL
            for j in tree.query(end.buffer(SNAP_TOL)):
                d = lines[j].distance(end)
                if j != i and d < bd:
                    best, bd = j, d
            if best is not None and bd > 1e-6:
                connectors.append(LineString([end, nearest_points(end, lines[best])[1]]))
    # unary_union splits every line at every intersection
    net = unary_union(lines + connectors)
    G = nx.Graph()
    key = lambda c: (round(c[0], 1), round(c[1], 1))
    for s in (net.geoms if isinstance(net, MultiLineString) else [net]):
        c = list(s.coords)
        for a, b in zip(c[:-1], c[1:]):
            if key(a) != key(b):
                G.add_edge(key(a), key(b))
    main = max(nx.connected_components(G), key=len)
    return G.subgraph(main).copy(), len(lines), len(connectors)


def survey_elevations(geo):
    pts, z = [], []
    for L in ('控制点注记', '控制点'):
        for p, t in geo.get(L, {}).get('texts', []):
            m = ROOF_RE.search(t)
            if m and 500 < float(m.group(1)) < 900:
                pts.append(p)
                z.append(float(m.group(1)))
    return np.array(pts), np.array(z)


def interpolate(nodes, spts, sz):
    tree = cKDTree(spts)
    out = []
    for n in nodes:
        idx = tree.query_ball_point(n, ELEV_RADIUS)
        if not idx:
            d, i = tree.query(n)
            out.append(sz[i])
            continue
        d = np.maximum(np.hypot(*(spts[idx] - n).T), 1.0)
        w = 1.0 / d**2
        out.append(float(np.sum(w * sz[idx]) / np.sum(w)))
    return np.array(out)


def tunnel_width(geo, G, samples=400):
    """Median wall-to-wall distance, estimated as twice the centerline-to-nearest-wall distance."""
    walls = [LineString(p) for p in geo['巷道']['lines'] if len(p) >= 2 and LineString(p).length > 0]
    tree = STRtree(walls)
    rng = np.random.default_rng(0)
    edges = list(G.edges())
    d = []
    for k in rng.choice(len(edges), size=min(samples, len(edges)), replace=False):
        u, v = edges[k]
        p = Point((u[0] + v[0]) / 2, (u[1] + v[1]) / 2)
        j = tree.nearest(p)
        dist = walls[j].distance(p)
        if 0.5 < dist < 5:
            d.append(2 * dist)
    return float(np.median(d)), len(d)


class Anonymizer:
    """Random rotation + mirror + shift of the plan, and a random reference level for elevations.
    The key is stored next to the raw drawing (raw/, never published), so outputs are reproducible
    but cannot be mapped back to real coordinates without it."""

    def __init__(self, key_path, pts, z):
        if key_path.exists():
            k = json.loads(key_path.read_text())
        else:
            rng = np.random.default_rng()
            k = {'theta': float(rng.uniform(0, 2 * np.pi)), 'zref': float(np.floor(min(z)) - rng.uniform(5, 40))}
            P = np.array(pts)
            c, s_ = np.cos(k['theta']), np.sin(k['theta'])
            R = np.c_[-(c * P[:, 0] - s_ * P[:, 1]), s_ * P[:, 0] + c * P[:, 1]]
            k['x0'], k['y0'] = float(R[:, 0].min() - 500), float(R[:, 1].min() - 500)
            key_path.write_text(json.dumps(k))
        self.k = k

    def xy(self, p):
        c, s_ = np.cos(self.k['theta']), np.sin(self.k['theta'])
        x, y = -(c * p[0] - s_ * p[1]), s_ * p[0] + c * p[1]
        return [round(float(x - self.k['x0']), 2), round(float(y - self.k['y0']), 2)]

    def z(self, v):
        return round(float(v - self.k['zref']), 3)


def main(json_path, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    geo = collect_layers(load_objects(json_path))

    G, n_lines, n_conn = build_graph(geo['中心线']['lines'])
    shafts = [p for p, b in geo['井筒']['inserts']]
    # Shafts are drawn beside the roadways: join each to the nearest node by a shaft-bottom connector
    nodes = list(G.nodes())
    ntree = cKDTree(nodes)
    shaft_nodes = []
    for p in shafts:
        d, i = ntree.query(p)
        sp = (round(p[0], 1), round(p[1], 1))
        G.add_edge(sp, nodes[i])
        shaft_nodes.append((sp, round(float(d), 1)))

    spts, sz = survey_elevations(geo)
    order = sorted(G.nodes())
    z = interpolate(np.array(order), spts, sz)
    width, n_w = tunnel_width(geo, G)

    ids = {n: f'P{k + 1:04d}' for k, n in enumerate(order)}
    zmap = dict(zip(order, z))
    lengths = [math.dist(u, v) for u, v in G.edges()]
    slopes = [abs(zmap[u] - zmap[v]) / max(math.dist(u, v), 1e-9) for u, v in G.edges()]

    # Anonymize: rotate, mirror and shift the plan, and give elevations relative to a hidden level.
    T = Anonymizer(Path(json_path).parent / 'anon_key.json', order, z)
    A = nx.Graph()
    for n in order:
        A.add_node(ids[n], xyz=(*T.xy(n), T.z(zmap[n])))
    edges = sorted((min(ids[u], ids[v]), max(ids[u], ids[v])) for u, v in G.edges())
    for k, (a, b) in enumerate(edges):
        A.add_edge(a, b, id=f'H{k + 1:04d}', length=math.dist(A.nodes[a]['xyz'], A.nodes[b]['xyz']))
    save_workbook(A, out / 'mine_network.xlsx')

    water = [[T.xy(p) for p in ring] for ring in geo['积水线']['lines'] if len(ring) > 10]
    feats = {
        'source': 'mining plan of a working longwall coal mine (anonymized)',
        'shafts': [{'node': ids[n], 'xy': T.xy(n), 'connector_m': d} for n, d in shaft_nodes],
        'water_outlines': water,
        'survey_points': len(sz),
        'tunnel_width_m': round(width, 2), 'width_samples': n_w,
    }
    (out / 'mine_features.json').write_text(json.dumps(feats, ensure_ascii=False))

    deg = Counter(d for _, d in G.degree())
    print(f'centerline pieces {n_lines}, gap connectors {n_conn}')
    print(f'nodes {G.number_of_nodes()}, tunnels {G.number_of_edges()}, total length {sum(lengths) / 1000:.1f} km')
    print('degree distribution', sorted(deg.items()))
    print(f'survey elevations {len(sz)}: {sz.min():.1f}-{sz.max():.1f} m; node Z {z.min():.1f}-{z.max():.1f} m')
    print(f'slope: median {np.median(slopes):.4f}, 99th pct {np.percentile(slopes, 99):.3f}, max {max(slopes):.3f}')
    print(f'tunnel width (median of {n_w}) {width:.2f} m')
    print('shafts', feats['shafts'])
    print('water outlines', len(water))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
