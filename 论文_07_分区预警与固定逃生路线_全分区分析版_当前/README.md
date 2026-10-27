# When a longer route buys time

Current manuscript: `main.tex` (14 pages, including references and appendices).
PDF: `../阅读入口_PDF/论文_07_分区预警与固定逃生路线_全分区分析版_当前.pdf`.

The October 25 version, before the CAD-centered rewrite, is preserved in local commit `623b8ad`. Its PDF also remains at `../阅读入口_PDF/论文_06_分区预警与固定逃生路线_初期案例版.pdf`. This revision was written on October 26, 2026. No files in `论文_02_洪水传播与动态逃生_Claude稿/` or the Chinese source were changed.

## What changed

The CAD network now supplies the main evidence: all 1,587 candidate source nodes, all 1,587 origins, four regions, and 10/20/30-minute targets. The northwest coverage result, 720 to 1,200 of 1,243 outside-region origins at 30 minutes, is stated in the abstract and introduction. The main results then explain the walking cost, the P0036 route example, and the distinction between incompatible common routes and individually impossible scenarios.

The original competition case is retained in Appendix D. Delay-only menus and exact-search arguments are in Appendix A. Flow redesign and the restricted-source negative results remain in the main body. All guarantees are conditional on the uncalibrated flood schedules; the CAD origin is not represented as hydraulic validation.

The English in `../论文_02_洪水传播与动态逃生_Claude稿/flood_escape_article.tex` was used as a prose reference: concrete opening, short explanations before notation, and results organized around questions. Figures include a new 3D CAD view, an alarm-region plan, distance/coverage curves, an example route map, and a spatial diagnostic. The 3D plot uses the actual stored elevation proxy and explicitly marks 35× vertical exaggeration.

## Claude polishing request

A separate Claude Opus 5.5 medium revision was **not produced**. Claude.app is installed, but the computer-use tool returned “Computer Use was not approved to use Claude.” No `claude` command was found on PATH or at the standard local/Homebrew locations inspected. No model invocation occurred, no manuscript was sent, and no new tool was installed. The present draft must not be described as Claude-polished.

## Rebuild from saved results

The figures and all four numerical tables are generated from the frozen result files, not manually entered. From the repository root, using an existing Python environment with NumPy, NetworkX, and Matplotlib:

```sh
python 论文_07_分区预警与固定逃生路线_全分区分析版_当前/make_cad_figures.py
```

Then from this directory:

```sh
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build -jobname=regional_alarm main.tex
```

Copy `build/regional_alarm.pdf` to the stable PDF output path after review. `review_pdf.py` renders every page and produces contact sheets using the already available pypdfium2, pypdf and Pillow. No new packages were installed for this revision. The final build has no unresolved citations/references or overfull/underfull-box warnings.

## Experiment provenance

- `../实验_07_分区预警与固定路线_全分区分析/protocol.json`, `design.json`: design and source definitions, geometry and simulator hashes.
- `full_*.jsonl`: 19,044 primary queries.
- `near_*.jsonl`: 19,044 restricted-source queries.
- `high_flow/*.jsonl`: 6,348 doubled-inflow redesign queries.
- `stress.json`: evaluation of frozen nominal routes at changed flow.
- `engine_tests.json`, `flow_scaling_check.json`: solver and flow-scaling checks.
- `../实验_06_分区预警与固定路线_初期分析/solver_tests.json`: exhaustive small-graph tests.
- `audit/revision-2026-10-26/`: current page renders, extracted text, checks, and delivery metadata.

The figure/table rebuild needs only the saved result files. Full flood simulation uses `实验_07_分区预警与固定路线_全分区分析/prepare.py`, then `run_analysis.py REGION` for NW/SW/SE/NE, with and without `--near`, followed by `stress.py`, `high_flow.py`, `summarize.py`, and `spatial.py`. The code depends on the existing `论文_04_绕行与延迟容忍_路线菜单探索/code` implementation and anonymized inputs in `论文_04_绕行与延迟容忍_路线菜单探索/data/cad`.

`fields/` and `upper/` are local regenerable caches, not part of the manuscript snapshot. `prepare.py` regenerates missing fields; do not mistake its resumed preparation ledger length for a unique-source count. Existing result JSONL files cause solvers to skip completed queries. For an independent complete rerun, use a separate work copy with the same code/inputs and empty cache and result directories. Do not mix cached files with modified model parameters. The committed records, not a rerun with changed dependencies, are the evidence cited here.

This revision does not re-run or replace the physics investigations in other directories. It reorganizes and verifies the existing CAD regional audit.
