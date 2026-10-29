# Planning Mine Escape Routes with Zone-Based Flood Alarms (v9)

Manuscript: `main.tex` (with `sections_model.tex`, `sections_appendix.tex`), 17 pages.
PDF: `../阅读入口_PDF/论文_09_水源位置未知时的固定逃生路线.pdf` (build: `build/mine_escape_zones.pdf`).

A new study built on the CAD mine network, centred on source-location uncertainty rather than warning delay. Evidence comes from `../实验_09_水源位置未知时的固定逃生路线/` (2,558,244 queries, all solved exactly; 7 that hit the main run's time limits were re-solved with a one-hour limit).

## Questions and headline results (quadrant alarms, 30-minute delay, 0.5 m³/s)

1. **Why shortest routes fail.** 59% of (worker, flood) pairs guaranteed. 91% of failing shortest routes fail even with no delay; they are cut a median 130 m (NW) / 280 m (SW) from a shaft, where routes converge.
2. **What a zone-wide route can do.** Robust routes 79%, avoid-the-zone rule 69%, exact source 99.8%. The rule recovers most of the gain but with far longer walks (NW median +364% vs +54%).
3. **Information or time.** 21.0% of pairs are information-limited, 0.2% have no way out. Finer zones close the gap (10% → 97% from 1 to 64 zones). Any zone holding the whole shaft area protects only 10–33%; cutting zones through the shafts is worth about as much as doubling the number of zones. Delay matters mainly through its interaction with zone uncertainty.

## Rebuild

From this folder, with an environment that has NumPy, NetworkX, Matplotlib, Shapely:

```sh
python fig_geometry.py        # Figure 1 (3D mine view) and Figure 2 (plan view)
python make_figures.py        # Figures 3–6 and all tables, from 实验_09 summary/results
python check_claims.py        # recomputes 80 numbers quoted in the text and checks they appear
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build -jobname=mine_escape_zones main.tex
```

## Submission version

Finalized on 2026-10-28 with author Jingchao Wang. Submit the single PDF linked above; the mathematical derivations, flood rules, implementation checks, and additional tables are included as appendices in that PDF. No separate attachments or external project archive are referenced as submission materials. The working-preprint label and AI-assistance statement have been removed. The flood model remains uncalibrated, and all numerical conclusions remain conditional on it.

The prior manuscript sources and PDF are preserved in `audit/finalization-2026-10-28/`, together with the base Git commit for comparison. Local experiment files and rebuild instructions are retained for internal verification.
