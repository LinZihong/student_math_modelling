"""Figures for the mine example.  Usage (from the project root): python -m mine_example.scripts.figures"""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.lines import Line2D
from matplotlib.ticker import MultipleLocator

from mine_example.scripts.simulate import MINERS, main as simulate

OUT = Path(__file__).resolve().parents[1] / 'figures'
INK, INK2 = '#0b0b0b', '#52514e'
DRY, WET, BLOCKED = '#c9c8c2', '#86b6ef', '#184f95'      # sequential blue steps 250 / 600
AWARE, UNAWARE, CRITICAL = '#6250d6', '#eb6834', '#d03b3b'  # validated categorical pair; status red
ELEV = LinearSegmentedColormap.from_list('elev', ['#cde2fb', '#86b6ef', '#3987e5', '#1c5cab', '#0d366b'])
HALO = [pe.withStroke(linewidth=2.5, foreground='white')]
plt.rcParams.update({'font.family': 'Arial', 'font.size': 9, 'axes.edgecolor': INK2, 'axes.labelcolor': INK2,
                     'xtick.color': INK2, 'ytick.color': INK2})


def xy(G, n):
    return G.nodes[n]['xyz'][:2]


def frame(ax, step=1000):
    ax.set_aspect('equal')
    ax.xaxis.set_major_locator(MultipleLocator(step))
    ax.yaxis.set_major_locator(MultipleLocator(step))
    ax.xaxis.set_major_formatter(lambda v, _: f'{v / 1000:g}')
    ax.yaxis.set_major_formatter(lambda v, _: f'{v / 1000:g}')
    ax.set_xlabel('x (km)')
    ax.set_ylabel('y (km)')
    for s in ('top', 'right'):
        ax.spines[s].set_visible(False)


def label(ax, p, text, off=(6, 4)):
    ax.annotate(text, p, off, textcoords='offset points', color=INK, weight='bold', path_effects=HALO, zorder=9)


def overview(G, feats, exits, A, out):
    fig, ax = plt.subplots(figsize=(7.2, 6.2))
    lc = LineCollection([[xy(G, u), xy(G, v)] for u, v in G.edges()], cmap=ELEV, linewidths=0.9)
    lc.set_array([(G.nodes[u]['xyz'][2] + G.nodes[v]['xyz'][2]) / 2 for u, v in G.edges()])
    ax.add_collection(lc)
    for ring in feats['water_outlines']:
        ax.plot(*zip(*ring), color=INK2, lw=0.5, ls=(0, (3, 2)))
    for n in exits:
        ax.plot(*xy(G, n), marker='^', color=INK, ms=7, mec='white', mew=1, ls='none', zorder=6)
    sx = sum(xy(G, n)[0] for n in exits) / len(exits)
    sy = sum(xy(G, n)[1] for n in exits) / len(exits)
    ax.annotate('shafts (exits)', (sx, sy), (sx + 900, sy - 1300), color=INK, path_effects=HALO,
                arrowprops=dict(arrowstyle='-', color=INK2, lw=0.6))
    ax.plot(*xy(G, A), marker='*', color=CRITICAL, ms=13, mec='white', mew=1, ls='none', zorder=7)
    ax.annotate('inrush point', xy(G, A), (xy(G, A)[0] + 600, xy(G, A)[1] + 1500), color=INK, path_effects=HALO,
                arrowprops=dict(arrowstyle='-', color=INK2, lw=0.6))
    for name, n in MINERS.items():
        ax.plot(*xy(G, n), 'o', color=INK, ms=6, mec='white', mew=1, zorder=8)
        label(ax, xy(G, n), name)
    ax.autoscale_view()
    frame(ax)
    cb = fig.colorbar(lc, ax=ax, shrink=0.6, pad=0.02)
    cb.set_label('roof elevation above reference level (m)')
    cb.outline.set_visible(False)
    fig.savefig(out, dpi=220, bbox_inches='tight')
    plt.close(fig)


def snapshot(G, f, exits, A, paths, t_show, out):
    fig, ax = plt.subplots(figsize=(7.2, 5.0))
    groups = {DRY: [], WET: [], BLOCKED: []}
    for e in f.E.values():
        c = BLOCKED if t_show >= e.t_block else WET if t_show >= e.t_in else DRY
        groups[c].append([xy(G, e.u), xy(G, e.v)])
    for c, lw in ((DRY, 0.8), (WET, 3.4), (BLOCKED, 3.4)):
        ax.add_collection(LineCollection(groups[c], colors=c, linewidths=lw, capstyle='round'))
    shown = []
    for name in ('M1', 'M2', 'M3'):
        p = paths[name]
        for nodes, col, ls in ((p['dry'], UNAWARE, (0, (4, 2))), (p['aware'], AWARE, '-')):
            ax.plot([xy(G, n)[0] for n in nodes], [xy(G, n)[1] for n in nodes], color=col, lw=1.7, ls=ls, zorder=5)
        shown += p['dry'] + p['aware']
        ax.plot(*xy(G, MINERS[name]), 'o', color=INK, ms=6, mec='white', mew=1, zorder=8)
        label(ax, xy(G, MINERS[name]), name)
    ax.plot(*xy(G, A), marker='*', color=CRITICAL, ms=13, mec='white', mew=1, ls='none', zorder=7)
    for n in exits:
        ax.plot(*xy(G, n), marker='^', color=INK, ms=7, mec='white', mew=1, ls='none', zorder=6)
    xs = [xy(G, n)[0] for n in shown]
    ys = [xy(G, n)[1] for n in shown]
    ax.set_xlim(min(xs) - 250, max(xs) + 250)
    ax.set_ylim(min(ys) - 250, max(ys) + 250)
    frame(ax, 500)
    handles = [Line2D([], [], color=DRY, lw=1.2, label='dry tunnel'),
               Line2D([], [], color=WET, lw=3, label='water ≤ 0.3 m'),
               Line2D([], [], color=BLOCKED, lw=3, label='impassable (> 0.3 m)'),
               Line2D([], [], color=AWARE, lw=1.7, label='earliest-arriving route'),
               Line2D([], [], color=UNAWARE, lw=1.7, ls=(0, (4, 2)), label='shortest route by length'),
               Line2D([], [], color=CRITICAL, marker='*', ls='none', ms=11, mec='white', label='inrush point'),
               Line2D([], [], color=INK, marker='^', ls='none', ms=7, mec='white', label='shaft')]
    fig.legend(handles=handles, loc='lower center', ncol=4, frameon=False, fontsize=7.5, bbox_to_anchor=(0.5, -0.07))
    ax.set_title(f'{t_show / 60:.0f} min after the inrush (alert after 1 min)', loc='left', color=INK, fontsize=10)
    fig.savefig(out, dpi=220, bbox_inches='tight')
    plt.close(fig)


def main():
    OUT.mkdir(exist_ok=True)
    G, f, exits, ring, A, paths, summary = simulate()
    feats = json.loads((OUT.parent / 'data' / 'mine_features.json').read_text())
    overview(G, feats, exits, A, OUT / 'mine_network.png')
    snapshot(G, f, exits, A, paths, 10 * 60, OUT / 'mine_flood_routes.png')


if __name__ == '__main__':
    main()
