# Research restart — 25 October 2026

## Objective and preservation

Preserve `论文_04_绕行与延迟容忍_路线菜单探索/`, its reproducible results, and the delivered PDF. They are a prior working draft, not evidence that the new objective has been met. Do not write a replacement paper until a substantive result survives physical and numerical checks. Final manuscript: 10–15 pages, self-contained mine-inrush background, one central result, following academic-paper-writing.

## Current evidence

The existing flood code conserves volume but implements equal flow splitting, a parent tree at merging fronts, full-before-uphill propagation, and average tunnel depths. These choices do not constitute a hydraulic validation. Increasing its inflow alone cannot establish realistic route performance. Existing flow sensitivities did not systematically test menus.

SWMM toolkit 0.17.0 installed in `/tmp/mine-hydraulics`. Its bundled arm64 libomp had an invalid signature, confirmed by codesign and macOS crash report. Copied to `/tmp/mine-hydraulics-signed` and ad-hoc signed the local package binaries; import and simulation then succeeded. No system security settings changed.

`benchmark_swmm.py` runs EPA SWMM dynamic-wave flow on a 500 m, 4 m wide rectangular channel. Six cases use Q=0.5 or 2 m3/s and slope=0.001, 0.005, 0.02; n=0.025 is a test parameter, not an asserted mine calibration. Initialize at Manning uniform depth and impose that depth at the downstream boundary. Compare middle-link depth after 2 h to the independent Manning equation. This verifies engine integration and a steady state only; it does not validate transients, junctions, or mine data. Reports and outputs are preserved in `results/benchmark/`.

## Candidate mechanisms (hypotheses, not results)

1. **Fastest versus delayed-safe routing:** map when conflict exists under dynamic-wave hazards, realistic walking speeds, explicit physical boundaries; first ask whether useful alternatives exist at all. Reject a claim resting only on late closure times or one tuned case.
2. **A shorter connection can worsen escape:** a new cross passage helps people but also admits water into the nominal refuge/exit corridor. Separate the pedestrian-only benefit from the coupled hydraulic effect. Seek an open parameter region and explain it using competing travel/front times. Existing literature on cross passages and flood propagation must be checked before claiming novelty.
3. **Unsafe recommendations from spatial averaging:** whole-edge mean depth or entry-time speed can certify a route whose actual trajectory crosses a hazardous front. Determine whether this produces material false-safe decisions under spatial refinement and a standard hydraulic model, and whether a local certificate repairs them. A contrived discretization example alone is insufficient.

## Evidence gates before selecting a paper

- Physical parameter justification from primary sources; explicitly distinguish supplied geometry, estimated elevations, and hypothetical boundaries/inrushes.
- Dry/steady benchmarks, conservation, transient benchmark, timestep and segment refinement; inspect node flooding and artificial losses.
- Outcome-independent parameter screen including null and impossible regimes; preserve failures and complete denominators. Freeze follow-up settings before confirmation.
- Fair baselines and a mechanism, not just a better aggregate score. Separate existence of a route from an executable information-dependent policy.
- Replication over geometries/conditions; do not call a CAD-derived graph a calibrated real mine.
- Literature audit: algorithms from prior work credited; novelty must be narrower than 'use SWMM and dynamic shortest paths'.

## Primary sources located

- EPA SWMM 5.2 manual: https://www.epa.gov/system/files/documents/2022-02/storm-water-management-model-users-manual-version-5.2.pdf
- Toolkit maintainer: https://pypi.org/project/swmm-toolkit/
- 2020 earliest-arrival mine evacuation: https://www.sciencedirect.com/science/article/pii/S0925753520302332
- 2022 pipe-flow mine network model: https://iwaponline.com/wst/article/85/3/872/86237/Spatiotemporal-modeling-of-water-inrush-spreading (full text retrieval returned 403).
- 2025 VOF tunnel/cross-passage study: https://pp.bme.hu/ci/article/view/39878
- 2026 dynamic-wave dual-inrush study: https://link.springer.com/article/10.1007/s44290-026-00503-0 (has published correction; inspect before reliance). Displayed formula transcription contains suspicious expressions; do not use its abstract's validation claim as our validation.

## Next executable work

Build and verify a branching/loop dynamic-wave benchmark with explicit storage/outlet boundaries. Test mechanism 2 on a simple paired-corridor construction, then reject or expand based on a full parameter screen. In parallel conceptually, audit mine geometry for elevation and exit interpretation before exporting entire networks. No new paper yet.

Command for current benchmark:
`PYTHONPATH=/tmp/mine-hydraulics-signed /Users/linzihong/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 实验_新增巷道与水动力验证/benchmark_swmm.py`

## Second research turn: exploratory shortcut screen

Implemented `shortcut_screen.py`, a synthetic coupled water/pedestrian loop with independently subdivided corridors. Added A–B cuts dry B–E distance from 1000 to 600 m. Water enters A; E leads to a separate downstream outfall O, preventing an invalid multiply-connected SWMM outfall. Width 4 m, height 3 m, n=.025, pedestrian speed 1 m/s. Closure uses first segment-mean depth reaching .3 m, permanently, with 2 s reporting brackets. These are explicitly exploratory assumptions, not a validated pedestrian injury criterion. Negative latest labels mean no nonnegative feasible departure, not an actual negative-time escape. Unblocked routes are censored at arrival horizon 3600 s.

The original five-flow screen (Q=.5,1,2,4,8; B elevation 1.5 m) shows no harmful shortcut. An exploratory expansion over B elevations .5,1,1.5,2,3 and Q=1.2,1.4,1.6 finds harm at low B elevations and benefit at higher elevations. All outcomes are retained; this is adaptive discovery, not a held-out confirmation. Candidate mechanism: a downslope shortcut floods a depressed origin area before its old uphill escape route becomes impassable.

Refinement at Q=1.4, B=.5: without/with shortcut latest labels in seconds are 884/373 at 25 m segments and .25 s steps; 836/271.5 at 12.5 m/.25 s; 824/193.75 at 6.25 m/.125 s; 832/162.875 at 3.125 m/.0625 s. The sign survives but numbers are NOT converged. Global continuity errors decrease below .03% at 3.125 m, no flooding loss or convergence failures in the inspected 6.25 m report; those alone do not prove transient accuracy. Final 1.5625 m runs are being completed by session 93122; inspect its live state before starting anything else. Results are incrementally stored in `results/shortcut_screen/fine-summary.json`, log `results/shortcut-fine.log`.

Reproduction: same Python/PYTHONPATH command as benchmark, replacing script with `实验_新增巷道与水动力验证/shortcut_screen.py --mode base|expanded|refinement|fine`. Current CLI stores detailed summaries as `<mode>-records.json`; original exploratory execution additionally stored compact `expanded-summary.json` and other `*-summary.json` files.

Geometry audit `results/geometry-audit.json`: supplied competition and CAD graphs each contain dozens of >10% grade edges and several >30% edges. A naive entire-network hydraulic export is inappropriate before interpreting these links (shafts, interpolation, or actual inclines). Mine exits are not automatically hydraulic outfalls.

Session 93122 subsequently completed successfully. The 1.5625 m/.03125 s pair is 845.5625/144.4375 s; continuity errors -.009%/-.010%. No process remains running. The harmful sign persists but departure values still drift, particularly for the shortcut case.

Next: inspect the binding link/route and node-depth safety, compare against an independent transient solver or analytical benchmark. Test whether first-closure irreversibility or spatial averaging causes the apparent loss. Only then freeze a confirmation grid. No new manuscript and no proven central result yet.

## Third research turn: trajectory and transient audits

`trajectory_audit.py` enumerates all simple B–E macro routes, including both directions of the added passage, and interpolates SWMM nodal depths along actual constant-speed trajectories. It permits receding water rather than permanently closing at the first crossing. Samples are at most 1 s apart with a 2 s departure grid. This is not a rigorous continuous-time bound and does not include waiting, repeated-node paths, or a calibrated pedestrian speed model.

At the finest hydraulic mesh, Q=1.4 and B elevation .5, the latest grid departure under depth .3 is 846 s without the passage and 150 s with it. The origin first exceeds .3 m at 2592 s versus 126 s. Small oscillations cause several reopening intervals in the new-passage case; keep these rather than silently enforcing monotonicity. The harmful sign therefore survives allowing receding water and local-depth trajectory checks in this synthetic scenario. Sensitivities to walking speed .7/1/1.3 m/s and depth thresholds .2/.3/.4 use .25 s trajectory sampling (`trajectory-speed-audit.json`). These parameter choices are sensitivity tests, not field-calibrated safety thresholds.

More importantly, the SWMM transient benchmark is NOT satisfactory. `benchmark_transient.py` initializes a flat rectangular channel with 1 m depth left of x=0 and dry bed to the right, n=.0001, inertial damping NONE, dt=.05, and compares against Ritter's frictionless solution at 60/100 s before boundary influence. At dx=6.25 and t=100, mean depth error over |x|<=700 is .0795 m; the h>.01 front is 281.25 m, versus 532.46 m for the analytic h=.01 front (zero-depth front is 626.42 m). Despite negligible continuity error and reported iterative convergence, the front is wrong. SWMM also warns of a minimum elevation drop on flat links. This diagnoses this setup, not all possible SWMM configurations; audit initialization/options before generalizing. It prevents treating the earlier shortcut simulations as sufficiently validated.

Implemented an independent per-unit-width finite-volume core `shallow_water.py`: HLL flux with dry-bed fan speeds, hydrostatic reconstruction, and semi-implicit Manning friction. This is established numerical machinery, credited to Audusse et al. (2004), not claimed novelty. No network junction model yet. Ritter mean depth errors at dx=25,12.5,6.25,3.125 decrease .01634,.01066,.00677,.00421 m; mass residual <=2.3e-13 per width. Nonflat lake-at-rest max depth error is 6.7e-16 and max discharge 3.3e-15. Thin-front location still converges slowly (495.31 vs532.46 m at dx3.125), so do not overclaim front accuracy. Results and profiles: `results/finite_volume/`.

Numerical source: Audusse et al., SIAM J Sci Comput 25(6),2050–2065 (2004), https://doi.org/10.1137/S1064827503431090 ; author PDF https://perso.math.u-pem.fr/bouchut.francois/publications/hydroproj_published.pdf . Reconstruction limitations on coarse steep beds also need consideration: https://arxiv.org/abs/1206.4986 .

Completed speed/threshold sensitivity: at .3 m, old/new latest departures are 418/150, 846/150, 1076/150 s for speeds .7,1,1.3. But at .2 m the old network has NO feasible sampled departure while the added passage permits 76–82 s. Thus the sign reverses with hazard threshold! At .4 m the old route permits >=2170 s, new282 s (some old results censored by departure grid). Preserve this qualification; no universal harmful-shortcut claim is supported. All processes in this turn finished successfully.

Next concrete work: add and separately verify a mass-conserving network-junction coupling to the independent finite-volume solver, then compare the shortcut mechanism under explicit junction/storage boundary assumptions and mesh refinement. Continue auditing SWMM settings; do not simply replace one unvalidated model with another. No central result is yet ready for a paper.

## Fourth research turn: independent network solver and matched comparisons

Implemented `network_fv.py`. Rectangular HLL/hydrostatic-reconstruction channels connect through finite-area, zero-resolved-momentum mixed chambers. Shared interface flux ensures exact mass accounting. This is an explicit, approximate junction law; it is not claimed to reproduce arbitrary 3-D intersections. It has a free transmissive downstream drain, in contrast to SWMM's outlet handling. Tested a symmetric dry-start fork (symmetry error0, mass residual7.1e-15 m3) and nonflat closed-loop lake at rest (stage/mass errors0). Saved verification JSON. Tests demonstrate implementation properties, not full physical calibration.

At Q1.4, B elevation .5, ran old/new pairs with dx12.5,6.25,3.125 and chamber area16m2, plus dx6.25 areas4/64. Exact-balance residuals around1e-11m3. `fv_trajectory.py` enumerates all simple escape paths with nodal and cell-center depth interpolation, constant1m/s, 1s trajectory samples, 2s departure grid; source runs3600s. At depth.3 FV predicts no old-network departure but new allows164s: opposite to SWMM. At depth.4 both predict harm: FV at dx3.125 old662/new320s. This material disagreement must remain in any account.

Matched exploratory flow sweep Q=.5,.8,1,1.2,1.4,1.6,2, dx6.25, bz.5, FV chamber16m2 and SWMMdt.125 completed. Outputs saved under `results/network_fv/`, `results/shortcut_screen/`, paired summary `results/matched-hydraulics.json` via `compare_hydraulics.py`. At depth.3 both solvers show harm for Q=.5,.8,1; disagree at1.2,1.4; both give a feasible route only after adding passage at1.6,2. For Q.5, FV old latest>=2600s (departure-grid censored), new680s; SWMM old>=2600,new618. This is NOT yet confirmation: flow sweep adapted after discovering disagreement. At.2 and.4 retain all outcomes; no universal sign.

Added threshold-free diagnostic to both trajectory readers: minimum over simple routes of maximum encountered water depth at prescribed departures0,60,180,300,600,900,1200. It quantifies depth exposure without choosing a universal injury threshold. It is not a complete safety measure (velocity, footing, visibility, waiting absent). Recomputed paired summary includes these curves.

Current direction: a warning-delay-dependent benefit/harm transition of a cross passage may be more defensible than a blanket harmful-shortcut claim. Need literature check, an outcome-frozen confirmation grid across geometry/roughness/junction assumptions, finer-mesh checks near a shared-model regime, and physically justified inflow and pedestrian assumptions. Still no paper-worthy central result established. All simulation batches finished; the final paired post-processing was session81515 (finished), followed by a rerun adding exposure outputs; check its handle if not yet observed terminal.

The rerun session73917 is now confirmed completed. At Q.5, minimum peak depth at departure0 changes old/new .144/.011m in FV and .132/0m in SWMM (shortcut beneficial); at departure600 changes .196/.285m in FV and .154/.296m in SWMM (harmful); at1200 .207/.381m and .155/.402m. This is a shared qualitative delay-dependent reversal in two approximate models, not yet a validated mine safety conclusion. No live processes remain.

## Fifth research turn: locally frozen confirmation and continuous certificate

Before new runs, wrote `confirmation_protocol.json`, with SHA-256 snapshot in `results/confirmation_v1/protocol_snapshot.json`. The 16-condition factorial uses Q=.4/.6, n=.02/.03, B elevation .3/.7, added passage80/120m, dx6.25m, SWMMdt.125s, FV chamber16m2. Primary prediction: in BOTH models, new-minus-old minimal peak depth <=-.02m at departure0 and >=+.02m at departure600. These are new combinations, but this is a locally frozen robustness test after adaptive discovery, not external preregistration or statistical population sampling.

`run_confirmation.py` completed all64 hydraulic runs (16 cases x2 layouts x2 models), session53794 terminal. Results are retained by case, including misses. Primary criterion passes12/16. Cases4–7 miss because SWMM early improvement is less than2cm; do not round them into successes. All16 numerical gate sets pass: no roof exceedance, no reported SWMM flooding loss/nonconvergence, mass error<1%; FV residual<1e-6m3. `audit_confirmation.py` saves audit.json. Passing these does NOT resolve the earlier dry-bed benchmark discrepancy or field calibration.

Mechanism: for old graph G0 and added-passage graph G1 with their OWN hydraulic fields, let W0(d) be peak depth along any explicit old-graph escape trajectory starting at d. Every new-graph trajectory, even allowing waiting/repeated nodes/arbitrary route choice, has peak depth >= h1(B,d), since it starts at B. Thus h1(B,d)>W0(d) proves new-graph optimum is worse than the old feasible witness, for any policy class containing that witness. The proof is elementary; its value is a model-level certificate showing the late harm is not a routing-search failure. It does not certify safety against an unknown physical field.

`continuous_certificate.py` computes W0(d) EXACTLY for bilinear spatial/temporal interpolation of saved hydraulic fields, rather than sampled trajectories: within each space-time cell the constant-speed trajectory gives a quadratic, so check endpoints and concave interior vertex. Includes analytical interior-maximum and reverse-direction tests. Witness B-C-E, d600, speeds.7/1/1.3: all96 combinations (16 cases x2 models x3 speeds) have new-origin minus old-witness margin >=.02m; minimum .03501968m. Saved `continuous_certificate.json`. Session85580 completed. This removes temporal trajectory undersampling as an explanation within saved fields, but not PDE discretization error. Speed variants and certificate are post-hoc mechanism checks, not the frozen primary endpoint.

Literature located: Pan et al.2025 VOF study analyzes cross-passage flow and gives escape guidance but inspected sections do not establish this added-connection/warning-delay comparison. Fulltext https://pp.bme.hu/ci/article/download/39878/23936 . Do not claim exhaustive novelty from a search. Walking-speed modeling precedent .6–1.2m/s: E3S Web Conf174,01053(2020), doi10.1051/e3sconf/202017401053; publisher fulltext still to retrieve (search excerpt via ResearchGate is not enough for final citation verification). USDA technical manual has excavated-channel n ranges including.02–.03: https://www.ars.usda.gov/ARSUserFiles/50201000/WEPP/usersum.pdf ; this is roughness plausibility, not calibration of a mine.

Next gates before writing: refine representative/worst-margin confirmation cases, scrutinize junction/boundary assumptions and water-dependent walking or at least witness sensitivity, settle a precise limited novelty claim, and assess whether idealized mechanism plus supplied geometry context meets the requested credible-condition standard. Original preprint untouched. No new manuscript yet. All processes terminal. Raw retained investigation results now about2.1GB; avoid needless duplication.

## Sixth research turn: refinement, slower walking, and decision to write

`refine_confirmation.py` tested cases0 (first corner),7 (weak/missed early endpoint),15 (worst late certificate): FVdx3.125 and1.5625, SWMMdx3.125/dt.0625; additionally case15 FVarea4/64 atdx3.125. All22 hydraulic runs completed (session8144). Certificate sign remains positive. Worst case15 speed.7 margin .03502 at6.25m, .03215 at3.125m, .02948 at1.5625m. Large chamber64m2 gives .01933 at3.125m: weaker than the original2cm materiality criterion, still positive. Do not describe all expanded sensitivities as passing2cm. Results under `results/confirmation_refinement/`.

`slowed_witness.py` defines two deliberately uncalibrated stress-test gait policies: v=1/(1+k*h_current), k=2 or4 m^-1, held constant for1m spatial steps and reevaluated, using exact bilinear-reconstruction peak on each linear step. All64 witnesses (16 conditions x2models x2laws) finish within3600s; all late margins positive, minimum .04603m. This is a physically directional sensitivity test (deeper water slows walking), not an empirical human-stability model. Session53284 completed.

Crucial mechanism check: in the new layout, the old route B-C-E is early peak-depth optimal in all16 FV cases and15/16 SWMM cases. Thus early exposure improvement is usually hydraulic diversion, NOT the worker exploiting the shorter added passage. The added passage first diverts water away from the old downstream path but eventually floods the depressed origin. Paper must state this, rather than tell a misleading 'walk faster then trapped' story. Dry shortest distance nevertheless decreases1000m to580/620m across the factorial.

`make_figures.py` produced `figures/geometry.png`, `confirmation.png`, `delay_curve.png`, with numerical curve in `results/delay_curve.json`. Representative Q.5, n.025, B.5, added100m: exact-on-reconstruction path envelopes over0–20min show early benefit then persistent harm in both models; after several minutes the origin lower bound meets the added-layout simple-path optimum. Delay figure visually inspected and legible. Session25653 completed; no processes remain.

Decision: evidence now supports writing a narrowly framed mechanistic modeling paper about delay-dependent reversal of the exposure effect of an added connection, with a policy-independent late-harm certificate. It does NOT support real-mine safety validation, calibrated injury probabilities, universal advice to remove passages, or novelty of standard HLL/SWMM/routing machinery. Prior model discrepancies and failed primary cells must be reported. Treat this as an explanatory counterexample family plus controlled numerical evidence, not a mine-optimized deployment.

Remaining deliverable work: write a new self-contained10–15page paper following academic-paper-writing (one central result; mine-inrush background; formulate route and hydraulic coupling clearly; conditional certificate proof; frozen experiment; numerical validation; explicit limitations). Preserve 论文_04_绕行与延迟容忍_路线菜单探索/ and original PDF. Verify final citations using primary sources, carry evidence-generated tables/figures, include reproducibility instructions and honest AI authorship provenance, compile and visually inspect every page, then perform objective-level audit before marking goal complete. No new manuscript yet. The caveat about model-relative credibility must be explicit in the final deliverable rather than hidden in an appendix.

## Final manuscript and delivery audit

The separate manuscript `论文_05_新增巷道对逃生的利弊/main.tex` is complete and compiled to an 11-page PDF at `阅读入口_PDF/论文_05_新增巷道对逃生的利弊.pdf`. The original `论文_04_绕行与延迟容忍_路线菜单探索/` and its PDF are preserved; the old PDF hash still matches the recorded original. The final PDF was visually checked, references and result counts checked, and its build has no undefined-reference or box warnings. The appendix states AI assistance and separates competition work from new research.

`论文_05_新增巷道对逃生的利弊/audit/completion-review.md` maps the original objective to inspected evidence and limitations. `completion.json` records the deliverable hash, protocol consistency, result counts, raw confirmation file presence and selected code/result hashes. This is a mechanistic numerical preprint: early hydraulic diversion and later origin accumulation reverse the depth-exposure effect of one added connection. It is not field calibration or a deployment recommendation. Failed numerical benchmarks, primary misses and model disagreements remain in the paper and raw record.
