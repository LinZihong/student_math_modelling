"""Exact routing conditional on prescribed, permanent tunnel closures. Units: m, s.

Speed is 4 before wetting, w afterward, and zero after closure. Equality at
the closure time is permitted. This module makes no hydraulic predictions.
"""
from dataclasses import dataclass
import heapq
import math


@dataclass(frozen=True)
class Arc:
    u: str
    v: str
    length: float
    wet: float
    block: float
    speed: float = 1.0

    def arrival(self, t):
        if not math.isfinite(t) or t > self.block:
            return math.inf
        dry_distance = 4 * max(0.0, self.wet - t)
        if self.length <= dry_distance:
            end = t + self.length / 4
        else:
            end = max(t, self.wet) + (self.length - dry_distance) / self.speed
        return end if end <= self.block + 1e-8 else math.inf

    def latest(self, deadline):
        """Latest entry that exits by deadline; negative values are allowed."""
        end = min(deadline, self.block)
        if end == math.inf:
            return math.inf
        if end == -math.inf:
            return -math.inf
        wet_distance = self.speed * max(0.0, end - self.wet)
        if self.length <= wet_distance:
            return end - self.length / self.speed
        return min(end, self.wet) - (self.length - wet_distance) / 4


def earliest(arcs, start, exits, t0):
    adj = {}
    for a in arcs:
        adj.setdefault(a.u, []).append(a)
    best, prev, queue = {start: t0}, {}, [(t0, start)]
    while queue:
        t, u = heapq.heappop(queue)
        if t != best[u]:
            continue
        if u in exits:
            path = []
            while u != start:
                a = prev[u]
                path.append(a)
                u = a.u
            return t, path[::-1]
        for a in adj.get(u, []):
            t2 = a.arrival(t)
            if t2 < best.get(a.v, math.inf):
                best[a.v], prev[a.v] = t2, a
                heapq.heappush(queue, (t2, a.v))
    return math.inf, []


def latest_departures(arcs, exits):
    """Reverse label-setting algorithm; all exits have deadline infinity."""
    incoming = {}
    for a in arcs:
        incoming.setdefault(a.v, []).append(a)
    labels = {x: math.inf for x in exits}
    successor, done = {}, set()
    queue = [(-math.inf, x) for x in sorted(exits)]
    heapq.heapify(queue)
    while queue:
        negative, v = heapq.heappop(queue)
        if v in done or -negative != labels[v]:
            continue
        done.add(v)
        for a in incoming.get(v, []):
            if a.u in done:
                continue
            candidate = a.latest(labels[v])
            if candidate > labels.get(a.u, -math.inf):
                labels[a.u], successor[a.u] = candidate, a
                heapq.heappush(queue, (-candidate, a.u))
    return labels, successor


def path_deadline(path):
    deadline = math.inf
    for a in reversed(path):
        deadline = a.latest(deadline)
    return deadline


def walk(path, t):
    for a in path:
        t = a.arrival(t)
    return t


def deadline_path(successor, start, exits):
    path, seen = [], set()
    while start not in exits:
        if start in seen or start not in successor:
            return []
        seen.add(start)
        a = successor[start]
        path.append(a)
        start = a.v
    return path
