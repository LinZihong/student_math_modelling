"""Escape routing on the flooding network (paper, Section 4). Units: m, s.

A tunnel is dry before water first enters it (t_in), walkable in shallow water until its
depth exceeds 0.3 m (t_block), and impassable afterwards. Walking time is computed exactly:
the speed is 4 m/s before t_in and 2 m/s (with the flow) or 1 m/s (against it) afterwards.
"""
import heapq
import math

V_DRY, V_WITH, V_AGAINST = 4.0, 2.0, 1.0


class Arc:
    """Tunnel e walked from a to b."""
    __slots__ = ('a', 'b', 'L', 'wet', 'block', 'speed')

    def __init__(self, a, b, L, wet, block, with_flow, speeds=(V_DRY, V_WITH, V_AGAINST)):
        self.a, self.b, self.L, self.wet, self.block = a, b, L, wet, block
        self.speed = (speeds[0], speeds[1] if with_flow else speeds[2])

    def exit_time(self, t):
        """a_e(t): time of reaching b when entering at a at time t (inf if the tunnel blocks first)."""
        if t > self.block:
            return math.inf
        v_dry, v_wet = self.speed
        dry = v_dry * max(0.0, self.wet - t)
        end = t + self.L / v_dry if self.L <= dry else max(t, self.wet) + (self.L - dry) / v_wet
        return end if end <= self.block + 1e-9 else math.inf

    def latest_entry(self, deadline):
        """Latest entry time at a that still reaches b by `deadline` (and before the tunnel blocks)."""
        end = min(deadline, self.block)
        if end == math.inf:
            return math.inf
        v_dry, v_wet = self.speed
        wet_dist = v_wet * max(0.0, end - self.wet)
        if self.L <= wet_dist:
            return end - self.L / v_wet
        return min(end, self.wet) - (self.L - wet_dist) / v_dry

    def position(self, t_enter, t):
        """Distance from a reached at time t (t_enter <= t < exit_time)."""
        v_dry, v_wet = self.speed
        if t <= self.wet:
            return v_dry * (t - t_enter)
        return v_dry * max(0.0, self.wet - t_enter) + v_wet * (t - max(t_enter, self.wet))


def arcs(flood, speeds=(V_DRY, V_WITH, V_AGAINST)):
    """Directed arcs for every tunnel and both directions, from a finished Flood."""
    out = {}
    for e in flood.E.values():
        for a, b in ((e.u, e.v), (e.v, e.u)):
            out.setdefault(a, []).append(Arc(a, b, e.L, e.t_in, e.t_block, e.src == a, speeds))
    return out


def fastest(adj, start, exits, t0):
    """Earliest-arrival Dijkstra (Theorem 1). Returns (arrival time, [arcs])."""
    best, prev, queue = {start: t0}, {}, [(t0, start)]
    while queue:
        t, n = heapq.heappop(queue)
        if t > best[n]:
            continue
        if n in exits:
            path = []
            while n != start:
                path.append(prev[n])
                n = prev[n].a
            return t, path[::-1]
        for arc in adj.get(n, []):
            t2 = arc.exit_time(t)
            if t2 < best.get(arc.b, math.inf):
                best[arc.b], prev[arc.b] = t2, arc
                heapq.heappush(queue, (t2, arc.b))
    return math.inf, []


def walk(path, t0):
    """Arrival time along a fixed path, and the node where the miner gets stuck (or None)."""
    t = t0
    for arc in path:
        t2 = arc.exit_time(t)
        if t2 == math.inf:
            return math.inf, arc.a
        t = t2
    return t, None


def latest_departure(path):
    """Latest start time from which the fixed path still reaches its exit (Lemma 1 makes this well defined)."""
    d = math.inf
    for arc in reversed(path):
        d = arc.latest_entry(d)
    return d


def where(path, t0, t):
    """Miner's place at time t when walking `path` from t0: ('exit', node) or ('arc', arc, distance from arc.a)."""
    s = t0
    for arc in path:
        e = arc.exit_time(s)
        if t < e:
            return 'arc', arc, arc.position(s, t)
        s = e
    return 'exit', path[-1].b if path else None


def rebind(path, adj):
    """The same node sequence as `path`, with arcs taken from another flood's `adj`."""
    out = []
    for arc in path:
        out.append(next(x for x in adj[arc.a] if x.b == arc.b))
    return out
