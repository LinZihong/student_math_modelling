# Translation notes: 矿井水灾时巷道系统中的逃生规划 → *Escape Planning in Mine Tunnel Systems during Mine Flooding*

Output: `Escape_Planning_Mine_Flooding_EN.pdf` (built with `latexmk -xelatex Escape_Planning_Mine_Flooding_EN.tex`).
Its structure matches the original: one-page abstract, contents, sections 1–7, references and Appendices A–E. Equations (1)–(12), Figures 1–14 and Table 1 keep their original numbers. None of the code was run.

## A. Changes I made (please review)

### Mathematical / technical accuracy
1. **Eq. (8), water depth.** The original middle case was h = (t − t_arrival)·V_water/(4L_e). That gives h = 0 at t_arrival, but the model says the depth is 0.1 m at that moment. It also gives 2.9 m, not 3 m, at t_full, so it disagrees with Eq. (4). I changed it to **h = 0.1 + (t − t_arrival)·V_water/(4L_e)**. Now the function is continuous at t_full and matches Eq. (4).
2. **Eq. (12), path constraint.** The original said "∀ i, j ∈ Path, ∃ e_ij ∈ H", which requires *every* pair of path nodes to be joined by a tunnel. I changed it to "**∀ i, j adjacent in Path**, e_ij ∈ H", which is the intended meaning (consecutive nodes are connected).
3. **"速度" for water → "flow rate".** In the assumptions, the notation table (V_water) and Sections 5.1–5.2, 水流速度 is used in the sense of volumetric flow (Q = 30 m³/min; V_water appears in a volume-balance formula). I translated it as **flow rate** (volume per unit time). I did not use "velocity". The original also called V_water a "水流方向" (flow direction) in §5.2.2; that is now "flow rate".
4. **"逆Dijkstra" (reverse Dijkstra) and "逆Dijkstra+A\*" in Figure 2.** The code in Appendix C runs a forward, time-dependent Dijkstra from each worker to the exits, with no A\*. The abstract now says "a time-dependent shortest-path algorithm based on Dijkstra's algorithm". Figure 2 now says "Time-dependent Dijkstra algorithm".
5. **Share of degree-3 nodes: "约占总体的5/6" → "about 3/4".** In Figures 5 and 6, about 500 of roughly 665 nodes have degree 3, which is about 75%, not 83%. This number is read off the histograms, not computed from the data. Please confirm with the student.
6. **"混沌耦合" (chaotic coupled) → "complex, coupled".** "Chaotic" has a precise mathematical meaning that the paper does not show.

### Internal consistency / errors in the original
7. **§2:** "任务一和任务三" → "**Problems 1 and 3**". There is no Task 3; the paper defines only Tasks 1 and 2.
8. **§5.1.2:** "如图2" → "**as shown in Figure 4**". Figure 2 is the framework diagram; Figure 4 is the 3D plot of Attachment 2's inclined tunnels.
9. **§5.1.4:** "全部的答案详见附录3" → "**The complete results are in the result files produced by the code in Appendices A and B.**" There is no Appendix 3, and the paper does not print the results.
10. **§5.2.3:** "延迟几分钟" (a delay of a few minutes) → "applies the alert delay". The same paragraph and the code (`alert_delay = 1.0`) both say one minute.
11. **Typos fixed silently in meaning:** 节水点 → nodes; 排出 → exclude (排除); 出水口 → exit (出口); 群里行为 → group behavior (群体行为); 第一题/第一问 → "Problem 1" throughout; 矿工速度 v → V, to match the notation.

### Cultural / presentation
12. **"我国" → "China's"** (Introduction). The paper calls Chinese coal mines "our country's mines".
13. **Terminology:** 巷道 → "tunnel" (the student's own code comments use "tunnel"; "roadway" is the mining-industry term if you prefer it). 突水 → "water inrush". 附件 → "Attachment", the standard English rendering in CUMCM papers. 本组 → "our team".
14. **Reference [1]** is rendered in English with "(in Chinese)" added. The journal name is translated as *Management & Technology of SME (First Ten-day Issue)*.
15. **Figures 1 and 2 were redrawn in TikZ** with English labels. The originals were images with Chinese text. The other 12 figures already had English labels and are reused unchanged.
16. **Abstract spacing:** the English abstract is longer than the Chinese one. I tightened the line spacing on that page only, so the abstract and keywords still fit on one page, as competition format requires.

### Code appendices
17. **Comments, docstrings and printed messages translated** (mostly in Appendix E). The code itself is unchanged.
18. **Personal file path removed.** Appendices D and E contained `/Users/jingchaow/Downloads/CUMCM2025Problems/D题/附件/`. I replaced it with the `/Users/(*file path*)/` placeholder that Appendices A and B already use. This also keeps a personal username out of the document.
19. **Data-file and sheet names left in Chinese.** These are `附件1.xlsx`, `附件2.xlsx` and the sheets `端点` and `巷道`; translating them would break the code. A one-line note before Appendix A explains what they are.
20. Indentation was rebuilt from the PDF layout because it was lost in text extraction. Lines that the original listings package had wrapped were rejoined.

## B. Issues I noticed but did NOT change (the student's decision)
- **§5.1.4 interpretation may be backwards.** Figures 7–10 plot arrival/fill times sorted from smallest to largest. A convex curve there means each further node takes *longer* to reach. So the spread is fast at first and slows down, which makes sense because the fixed inflow is split across more and more branches. The text concludes the opposite ("starts slow, then speeds up") and builds its escape advice on that. Calling the curve "exponential" is also only a visual description.
- **§6.2 "even several years".** The largest values in Figures 7–10 are about 55,000–60,000 minutes, which is roughly 40 days. Unless the full result files contain larger values, "several years" is an overstatement.
- **Table 1 signs.** Raising the inrush flow rate by 10% *raises* t_arrival by 3.7%. Physically, more inflow should make arrival earlier. t_full also goes up (+6.6% / +6.7%) whether the flow rate goes up or down. "Path elements changed −31%" has no clear meaning as a negative number.
- **Abstract claims results "under different warning times".** The paper uses only a fixed 1-minute delay and shows no comparison across warning times.
- **Problem 4** gives a method but no results. Problem 3 likewise has no result figures beyond the setup plots.
- **Code vs. text:**
  - Appendix C reads `result1-1.xlsx`, but Appendices A and B write `final-1-*.xlsx` and `result_*_modified.xlsx`.
  - Appendix C treats `edgeFillTime` as a fill *duration*, and compares a fraction of fill to 0.3. That is not the same as h ≤ 0.3 m in Eq. (7).
  - Appendix B sets `burst_pt` twice; the first value is the Attachment 1 point.
  - None of this was run or changed.
- Tone: phrases like "计算效率极高" (very high computational efficiency) and "合理性可以肯定" (reasonableness can be affirmed) are translated faithfully ("very high", "supports the reasonableness"), but they are strong claims for the evidence shown.
