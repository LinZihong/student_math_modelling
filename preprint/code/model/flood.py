"""Volume-conserving, event-driven flood model on a tunnel graph. Units: m, s.

Rules (paper, Section 3):
  1. Spreading. A wet node passes all the water that reaches it to its outlets, split equally.
     Outlets are the level and downhill tunnels that are not full (problem statement); only if
     there are none, the uphill ones. A dry outlet starts to be covered at depth h0 ("cover"),
     or, if it goes uphill, to fill from its low end ("pond").
  2. A covered tunnel whose far end was still dry passes its water on ("through"); one whose far
     end was already wet (a loop, or two fronts meeting) stores it ("fill").
  3. Backing up. If a node has water but no outlet, the tunnel that brought the water stops
     passing it on and stores it. A full tunnel takes no more water, so the water backs up
     from dead ends toward the source.
  4. An uphill tunnel that fills up delivers its water to its upper node if that node is dry
     ("conduit").
Every tunnel's stored volume only grows, the total stored volume equals the volume that has
entered, and the depth used for walking is the stored volume divided by W*L.
"""
import heapq
import math

FULL, COVER, THROUGH, FILL, POND, CONDUIT, DRY = 'full', 'cover', 'through', 'fill', 'pond', 'conduit', 'dry'


class Edge:
    __slots__ = ('u', 'v', 'L', 'mode', 'vol', 'rate', 'src', 'child', 'feed',
                 't_in', 't_cov', 't_block', 't_full')

    def __init__(self, u, v, L):
        self.u, self.v, self.L = u, v, L
        self.mode, self.vol, self.rate = DRY, 0.0, 0.0
        self.src = self.child = None
        self.feed = {}
        self.t_in = self.t_cov = self.t_block = self.t_full = math.inf

    def other(self, n):
        return self.v if n == self.u else self.u


class Flood:
    def __init__(self, G, sources, W=4.0, H=3.0, h0=0.1, block=0.3, level_eps=0.005, reverse_ties=False):
        """sources: list of (node, start time s, inflow m^3/s)."""
        self.G, self.W, self.H, self.h0, self.block, self.eps = G, W, H, h0, block, level_eps
        # The parent-tree surrogate has sequential semantics at simultaneous events.
        # Make that convention explicit and independent of workbook insertion order.
        nodes=sorted(G,key=str)
        edges=sorted((tuple(sorted((u,v),key=str)) for u,v in G.edges()),
                     key=lambda uv:(str(uv[0]),str(uv[1])),reverse=reverse_ties)
        self.z = {n: G.nodes[n]['xyz'][2] for n in nodes}
        self.E = {frozenset((u, v)): Edge(u, v, G.edges[u,v]['length']) for u,v in edges}
        self.inc = {n: [self.E[frozenset((n, m))] for m in sorted(G[n],key=str)] for n in nodes}
        self.sources = sorted(sources, key=lambda s: (s[1],str(s[0])))
        self.src_rate = {n: 0.0 for n in G}
        self.wet = {n: math.inf for n in G}
        self.parent = {}
        self.order = []
        self.t = 0.0
        self.overflow = 0.0
        self.max_residual = 0.0
        self.saturated_at = math.inf

    # ---- flow distribution at the current instant ----
    def outlets(self, n):
        p = self.parent.get(n)
        feeding = p if p is not None and p.mode in (THROUGH, CONDUIT) else None   # it delivers to n
        cand = [e for e in self.inc[n] if e is not feeding and e.mode != FULL]
        down = [e for e in cand if self.z[e.other(n)] <= self.z[n] + self.eps]
        return down if down else cand

    def distribute(self):
        """Set every tunnel's inflow rate for the current state (rules 1-4)."""
        while True:
            for e in self.E.values():
                e.rate, e.feed = 0.0, {}
            inflow = dict(self.src_rate)
            self.lost = 0.0
            changed = False
            for n in self.order:                        # parents before children
                f = inflow.get(n, 0.0)
                if f <= 0:
                    continue
                outs = self.outlets(n)
                if not outs:
                    p = self.parent.get(n)
                    if p is not None and p.mode in (THROUGH, CONDUIT):
                        p.mode = FILL if p.mode == THROUGH else FULL   # rule 3: back up
                        changed = True
                        break
                    m = self.pool_edge(n) if self.src_rate[n] > 0 else None
                    if m is not None:                    # the inflow runs through the full tunnels
                        self.src_rate[m] += self.src_rate[n]   # to the nearest place with room
                        self.src_rate[n] = 0.0
                        changed = True
                        break
                    self.lost += f                       # everything reachable is full
                    continue
                share = f / len(outs)
                for e in outs:
                    if e.mode == DRY:
                        e.mode = COVER if self.z[e.other(n)] <= self.z[n] + self.eps else POND
                        e.src, e.t_in = n, self.t
                    if e.mode in (THROUGH, CONDUIT):     # a child tunnel passes the water on
                        inflow[e.child] = inflow.get(e.child, 0.0) + share
                    else:
                        e.rate += share
                        e.feed[n] = e.feed.get(n, 0.0) + share
            if not changed:
                return

    def pool_edge(self, n):
        """Nearest node, through full tunnels only, where water can still go."""
        seen, queue = {n: 0.0}, [(0.0, n)]
        while queue:
            d, x = heapq.heappop(queue)
            if d > seen[x]:
                continue
            if x != n and (self.outlets(x) or (self.parent.get(x) is not None
                                               and self.parent[x].mode in (THROUGH, CONDUIT))):
                return x
            for e in self.inc[x]:
                if e.mode == FULL:
                    y, d2 = e.other(x), d + e.L
                    if d2 < seen.get(y, math.inf):
                        seen[y] = d2
                        heapq.heappush(queue, (d2, y))
        return None

    # ---- events ----
    def targets(self, e):
        WL = self.W * e.L
        if e.mode == COVER:
            return [WL * self.h0]
        if e.mode in (FILL, POND):
            t = [WL * self.H]
            if e.t_block == math.inf:
                t.insert(0, WL * self.block)
            return t
        return []

    def run(self, t_end=math.inf):
        pending = list(self.sources)
        while True:
            while pending and pending[0][1] <= self.t + 1e-9:
                n, ts, q = pending.pop(0)
                self.src_rate[n] += q
                if self.wet[n] == math.inf:
                    self.wet[n] = ts
                    self.order.append(n)
            self.distribute()
            if self.lost > 0 and self.saturated_at == math.inf:
                self.saturated_at = self.t
            dt = math.inf
            for e in self.E.values():
                if e.rate > 0:
                    for target in self.targets(e):
                        if target > e.vol + 1e-12:
                            dt = min(dt, (target - e.vol) / e.rate)
                            break
            if pending:
                dt = min(dt, pending[0][1] - self.t)
            if dt == math.inf or self.t + dt > t_end:
                break
            self.t += dt
            for e in self.E.values():
                if e.rate > 0:
                    e.vol += e.rate * dt
            self.overflow += self.lost * dt
            self.check_volume()
            for e in self.E.values():
                if e.rate > 0:
                    self.event(e)

    def event(self, e):
        WL, tol = self.W * e.L, 1e-9 * max(1.0, self.W * e.L)
        if e.mode == COVER and e.vol >= WL * self.h0 - tol:
            e.vol, e.t_cov = WL * self.h0, self.t
            far = e.other(e.src)
            if len(e.feed) == 1 and self.wet[far] == math.inf:
                e.mode, e.child = THROUGH, far                   # rule 2
                self.wet[far], self.parent[far] = self.t, e
                self.order.append(far)
            else:
                e.mode = FILL
        if e.mode in (FILL, POND):
            if e.t_block == math.inf and e.vol >= WL * self.block - tol:
                e.t_block = self.t
            if e.vol >= WL * self.H - tol:
                e.vol, e.t_full = WL * self.H, self.t
                far = e.other(e.src)
                if e.mode == POND and self.wet[far] == math.inf:
                    e.mode, e.child = CONDUIT, far                # rule 4
                    self.wet[far], self.parent[far] = self.t, e
                    self.order.append(far)
                else:
                    e.mode = FULL
                if e.t_cov == math.inf:
                    e.t_cov = self.t

    def check_volume(self):
        entered = sum(q * max(0.0, self.t - ts) for n, ts, q in self.sources)
        stored = sum(e.vol for e in self.E.values()) + self.overflow
        self.max_residual = max(self.max_residual, abs(stored - entered) / max(entered, 1.0))

    # ---- results ----
    def tunnel(self, u, v):
        return self.E[frozenset((u, v))]

    def depth(self, e):
        return e.vol / (self.W * e.L)
