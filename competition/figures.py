"""Figures for Problems 1-4.  Usage (from the project root): python -m competition.figures"""
import math
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap, LogNorm
from matplotlib.lines import Line2D
import matplotlib.patheffects as pe

from competition.run import NETWORKS, solve
from model.routing import where

OUT = Path(__file__).resolve().parent / 'figures'
NAMES = {1: 'N1', 2: 'N2'}
INK, INK2 = '#0b0b0b', '#52514e'
DRY, WET, BLOCKED = '#c9c8c2', '#86b6ef', '#184f95'
AWARE, UNAWARE, CRITICAL = '#6250d6', '#eb6834', '#d03b3b'
ARRIVAL = LinearSegmentedColormap.from_list('arr', ['#0d366b', '#1c5cab', '#3987e5', '#86b6ef', '#cde2fb'])
HALO = [pe.withStroke(linewidth=2.5, foreground='white')]
plt.rcParams.update({'font.family': 'Arial', 'font.size': 8.5, 'axes.edgecolor': INK2,
                     'xtick.color': INK2, 'ytick.color': INK2, 'axes.labelcolor': INK2})


def frame(ax):
    ax.set_aspect('equal')
    ax.set_xlabel('x (km)')
    ax.set_ylabel('y (km)')
    ax.xaxis.set_major_formatter(lambda v, _: f'{v / 1000:g}')
    ax.yaxis.set_major_formatter(lambda v, _: f'{v / 1000:g}')
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)


def xy(G, n):
    return G.nodes[n]['xyz'][:2]


def mark_sources(ax, G, r, with_b=False):
    ax.plot(*xy(G, r['A']), marker='*', color=CRITICAL, ms=12, mec='white', mew=0.8, ls='none', zorder=6)
    ax.annotate('A', xy(G, r['A']), (-15, 6), textcoords='offset points', color=INK, weight='bold', path_effects=HALO, zorder=8)
    if with_b:
        ax.plot(*xy(G, r['B']), marker='D', color=CRITICAL, ms=7, mec='white', mew=0.8, ls='none', zorder=6)
        ax.annotate('B', xy(G, r['B']), (6, 4), textcoords='offset points', color=INK, weight='bold', path_effects=HALO, zorder=8)


def mark_exits(ax, G, r):
    for k, n in enumerate(sorted(r['exits'])):
        ax.plot(*xy(G, n), marker='^', color=INK, ms=8, mec='white', mew=0.8, ls='none', zorder=6)
        ax.annotate(f'E{k + 1}', xy(G, n), (-16, -3), textcoords='offset points', color=INK, weight='bold', path_effects=HALO, zorder=8)


def flood_state(ax, G, f, t):
    groups = {DRY: [], WET: [], BLOCKED: []}
    for e in f.E.values():
        c = BLOCKED if t >= e.t_block else WET if t >= e.t_in else DRY
        groups[c].append([xy(G, e.u), xy(G, e.v)])
    for c, lw in ((DRY, 0.8), (WET, 3.2), (BLOCKED, 3.2)):
        ax.add_collection(LineCollection(groups[c], colors=c, linewidths=lw, capstyle='round'))


def zoom(ax, G, nodes, pad=350):
    pts = [xy(G, n) for n in nodes if n in G]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    ax.set_xlim(min(xs) - pad, max(xs) + pad)
    ax.set_ylim(min(ys) - pad, max(ys) + pad)


def draw_path(ax, G, nodes, color, ls='-', lw=1.8, start_xy=None):
    pts = ([start_xy] if start_xy else []) + [xy(G, n) for n in nodes if n in G]
    ax.plot([p[0] for p in pts], [p[1] for p in pts], color=color, lw=lw, ls=ls, zorder=4, solid_capstyle='round')


def arrival_maps(res):
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 7.0))
    fig.subplots_adjust(right=0.84, hspace=0.3)
    norm = LogNorm(vmin=1, vmax=5e4)
    for col, net in enumerate((1, 2)):
        r = res[net]
        G = r['G']
        for row, (f, title, b) in enumerate(((r['f1'], 'single source', False),
                                             (r['f2'], 'delayed second source', True))):
            ax = axes[row, col]
            segs = [[xy(G, e.u), xy(G, e.v)] for e in f.E.values()]
            vals = [max(e.t_in / 60, 1) for e in f.E.values()]
            lc = LineCollection(segs, cmap=ARRIVAL, norm=norm, linewidths=1.0)
            lc.set_array(vals)
            ax.add_collection(lc)
            mark_sources(ax, G, r, b)
            ax.autoscale_view()
            frame(ax)
            ax.set_title(f'{NAMES[net]}: {title}', loc='left', fontsize=9, color=INK)
    cb = fig.colorbar(lc, cax=fig.add_axes([0.87, 0.3, 0.02, 0.4]))
    cb.set_label('time water first enters the tunnel (min, log scale)')
    cb.outline.set_visible(False)
    fig.savefig(OUT / 'arrival_maps.png', dpi=220, bbox_inches='tight')
    plt.close(fig)


def legend(fig, extra=(), extra_label='earliest-arriving route'):
    h = [Line2D([], [], color=DRY, lw=1.2, label='dry'),
         Line2D([], [], color=WET, lw=2.0, label='water ≤ 0.3 m'),
         Line2D([], [], color=BLOCKED, lw=2.0, label='impassable'),
         Line2D([], [], color=AWARE, lw=1.8, label=extra_label)] + list(extra)
    fig.legend(handles=h, loc='lower center', ncol=4, frameon=False, fontsize=7.5, bbox_to_anchor=(0.5, -0.06))


def routes(res, t_show=15 * 60):
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 4.2))
    for ax, net in zip(axes, (1, 2)):
        r = res[net]
        G = r['G']
        flood_state(ax, G, r['f1'], t_show)
        for k, p in enumerate(r['p2']):
            if not p['same_route']:
                import networkx as nx
                dry = nx.multi_source_dijkstra(G, r['exits'], target=p['start'], weight='length')[1]
                draw_path(ax, G, dry, UNAWARE, ls=(0, (3, 2)), lw=1.4)
            draw_path(ax, G, p['nodes'], AWARE)
            ax.plot(*xy(G, p['start']), 'o', color=INK, ms=6, mec='white', mew=0.8, zorder=7)
            ax.annotate(f'M{k + 1}', xy(G, p['start']), (6, -12), textcoords='offset points', weight='bold', color=INK, path_effects=HALO, zorder=8)
        mark_sources(ax, G, r)
        mark_exits(ax, G, r)
        frame(ax)
        zoom(ax, G, [n for p in r['p2'] for n in p['nodes']] + [r['A']])
        ax.set_title(f'{NAMES[net]}: water at t = {t_show // 60} min', loc='left', fontsize=9, color=INK)
    legend(fig, [Line2D([], [], color=UNAWARE, lw=1.4, ls=(0, (3, 2)), label='shortest route by length')])
    fig.tight_layout()
    fig.savefig(OUT / 'routes_single.png', dpi=220, bbox_inches='tight')
    plt.close(fig)


def replan(res):
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.9))
    for ax, net in zip(axes, (1, 2)):
        r = res[net]
        G, ts = r['G'], r['t_switch']
        t_show = ts + 10 * 60
        flood_state(ax, G, r['f2'], t_show)
        for k, (p2, p4, path) in enumerate(zip(r['p2'], r['p4'], r['paths'])):
            if p4['status'] != 're-planned':
                continue
            here = p4['xy']
            done = [n for n in p2['nodes'][:p2['nodes'].index(p4['on'][1])]]
            draw_path(ax, G, done, INK2, lw=1.0)
            rest = p2['nodes'][p2['nodes'].index(p4['on'][1]):]
            draw_path(ax, G, rest, UNAWARE, ls=(0, (3, 2)), lw=1.4, start_xy=here)
            draw_path(ax, G, p4['nodes'][1:], AWARE, start_xy=here)
            ax.plot(*here, 'o', color=INK, ms=6, mec='white', mew=0.8, zorder=7)
            ax.annotate(f'M{k + 1}', here, (5, 4), textcoords='offset points', weight='bold', color=INK, path_effects=HALO, zorder=8)
        mark_sources(ax, G, r, True)
        mark_exits(ax, G, r)
        frame(ax)
        zoom(ax, G, [n for p in r['p2'] for n in p['nodes']] + [n for p in r['p4'] for n in p.get('nodes', [])[1:]]
             + [r['A'], r['B']])
        ax.set_title(f'{NAMES[net]}: re-plan at {ts / 60:.0f} min, water at {t_show / 60:.0f} min',
                     loc='left', fontsize=9, color=INK)
    legend(fig, extra_label='revised route', extra=[Line2D([], [], color=INK2, lw=1.0, label='walked before re-planning'),
                     Line2D([], [], color=UNAWARE, lw=1.4, ls=(0, (3, 2)), label='remainder of original route')])
    fig.tight_layout()
    fig.savefig(OUT / 'routes_replan.png', dpi=220, bbox_inches='tight')
    plt.close(fig)


def setup(res):
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.9))
    elev = LinearSegmentedColormap.from_list('elev', ['#86b6ef', '#3987e5', '#1c5cab', '#0d366b'])
    for ax, net in zip(axes, (1, 2)):
        r = res[net]
        G = r['G']
        segs = [[xy(G, u), xy(G, v)] for u, v in G.edges()]
        if net == 1:
            ax.add_collection(LineCollection(segs, colors=INK2, linewidths=0.6))
        else:
            lc = LineCollection(segs, cmap=elev, linewidths=0.9)
            lc.set_array([(G.nodes[u]['xyz'][2] + G.nodes[v]['xyz'][2]) / 2 for u, v in G.edges()])
            ax.add_collection(lc)
        mark_sources(ax, G, r, True)
        mark_exits(ax, G, r)
        for m in r['miners']:
            ax.plot(*xy(G, m), 'o', color=INK, ms=4.5, mec='white', mew=0.8, zorder=7)
        ax.autoscale_view()
        frame(ax)
        ax.set_title(f'{NAMES[net]}: ' + ('planar (z = 10 m)' if net == 1 else 'three-dimensional'),
                     loc='left', fontsize=9, color=INK)
    cb = fig.colorbar(lc, ax=axes[1], shrink=0.7, pad=0.03)
    cb.set_label('elevation z (m)')
    cb.outline.set_visible(False)
    fig.legend(handles=[Line2D([], [], color=CRITICAL, marker='*', ls='none', ms=10, mec='white', label='source A'),
                        Line2D([], [], color=CRITICAL, marker='D', ls='none', ms=6, mec='white', label='source B (delayed)'),
                        Line2D([], [], color=INK, marker='^', ls='none', ms=7, mec='white', label='exits E1, E2'),
                        Line2D([], [], color=INK, marker='o', ls='none', ms=5, mec='white', label='miners M1-M3')],
               loc='lower center', ncol=4, frameon=False, fontsize=7.5, bbox_to_anchor=(0.5, -0.05))
    fig.savefig(OUT / 'networks.png', dpi=220, bbox_inches='tight')
    plt.close(fig)


def main():
    OUT.mkdir(exist_ok=True)
    res = {net: solve(net, cfg) for net, cfg in NETWORKS.items()}
    setup(res)
    arrival_maps(res)
    routes(res)
    replan(res)


if __name__ == '__main__':
    main()
