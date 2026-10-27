"""The competition team's flood algorithm (Appendices A/B of the competition paper), kept only
for comparison. It is not volume-conserving: a tunnel that has just been covered fills at its
full inflow while passing the same inflow on downstream. `strict_uphill=True` reproduces the
Network 2 code, in which water never enters a tunnel leading to a higher node."""
import heapq
import math


def legacy_flood(G, source, Q, W=4.0, H=3.0, h0=0.1, strict_uphill=False):
    z = {n: G.nodes[n]['xyz'][2] for n in G}
    E = lambda a, b: frozenset((a, b))
    t_arr = {E(u, v): math.inf for u, v in G.edges()}
    t_full = dict(t_arr)
    node_t = {n: math.inf for n in G}
    reached, full, pq, seq = set(), set(), [], 0

    def push(t, kind, a, b, q):
        nonlocal seq
        heapq.heappush(pq, (t, seq, kind, a, b, q))
        seq += 1

    def send(t, n, came, q):
        outs = [m for m in G[n] if m != came and E(n, m) not in full
                and (not strict_uphill or z[m] <= z[n])]
        for m in outs:
            qq, L = q / len(outs), G.edges[n, m]['length']
            if E(n, m) not in reached:
                push(t + W * h0 * L / qq, 'reach', n, m, qq)
            else:
                push(t + W * (H - h0) * L / qq, 'full', n, m, qq)

    node_t[source] = 0.0
    send(0.0, source, None, Q)
    while pq:
        t, _, kind, a, b, q = heapq.heappop(pq)
        e = E(a, b)
        if kind == 'reach':
            if e in reached:
                continue
            reached.add(e)
            t_arr[e] = t
            node_t[b] = min(node_t[b], t)
            send(t, b, a, q)
            push(t + W * (H - h0) * G.edges[a, b]['length'] / q, 'full', a, b, q)
        elif e not in full:
            full.add(e)
            t_full[e] = t
            down = b if node_t[b] >= node_t[a] else a
            send(t, down, a if down == b else b, q)
    return node_t, t_arr, t_full
