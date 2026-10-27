# When Does a Slower Escape Route Buy Useful Time?

Complete English working preprint, with reproducible code and local data.

## 阅读入口

- `main.tex`：完整论文源文件，包含理论、实证、讨论、附录和参考文献。
- `../阅读入口_PDF/论文_04_绕行与延迟容忍_路线菜单探索.pdf`：最终 PDF，路径相对于本文件所在目录。
- `results/paper_stats.json`：正文的主要统计。
- `results/origins.csv`：87 个起点的精确预算优化；其中 80 个是固定种子抽样，7 个是示例矿工。
- `results/menus.csv` 与 `results/menu_test_cells.csv`：菜单训练与未见突水点测试的完整分母及逐情景结果。

## 论文最后保留的问题

1. 为保证同一条路线在延迟出发后仍可通行，需要付出多少标称行程时间？
2. 这种收益是否发生在实际关心的时间范围内？
3. 不知道会在哪个位置突水时，两三条预存路线能覆盖多少新情景？

方法包括两个出发时刻的精确多标签搜索、反向最迟出发上界、预算二分，以及训练候选集内精确的有限菜单最大覆盖。数学结论与洪水预测分层：前者对给定 FIFO 路段函数成立，后者仍是未做工程校准的模拟。

## 实际发现

- 5% 额外行程预算提高了 63/80 个抽样起点的无时间上限出发余量；限制为未来 60 分钟后，基础情景中是 0/80。180 分钟内为 1/80。
- 这不是删掉负面结果后的优化故事。正文解释为何无上限收益会被数天后的模型封闭时刻主导，并保留真正不能靠绕行改善的起点。
- 三路线菜单在未参与训练的突水点上的及时覆盖率，从标称单路线的 94.77% 提高到 96.56%（竞赛网络），从 97.26% 提高到 97.89%（CAD 网络）。训练最优单路线反而比标称单路线的测试分数低。
- 菜单覆盖指存在一条可行且行程不超过情景最优值 110% 的路线；不是已经实现了矿工识别并选中它的策略，更不是实际事故的成功概率。

前一轮 `实验_早期鲁棒性探索_已被后续替代/` 中依赖旧非守恒模拟的结果已被本轮替代，尤其不能再使用“多走 2.19 分钟换来 8.07 分钟”的旧案例作为最终结果。本稿所有数字来自本目录的重新计算。

## Reproduce

Use Python 3.12 and install the versions in `requirements.txt` in a dedicated environment. From this directory:

```sh
python -m pip install -r requirements.txt
python code/reproduce.py --fresh
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build -jobname=mine_escape_preprint main.tex
```

`--fresh` removes only four named generated pickle caches and recomputes the flood schedules. It does not change the supplied workbooks. Omit it to reuse local trusted caches. Do not load pickle caches obtained from an untrusted source.

The computation runs 15 tests, two single-source base experiments, hydraulic/speed sensitivity checks, 32 source-location flood simulations, menu selection and evaluation, figure generation, and retained-path/cell-level validation. Logs are in `results/`. `results/environment.json` records the executed environment; `results/manifest.json` hashes the actual code and data.

Only input geometry and supplied extraction metadata are copied into `data/`. The original DWG, its JSON export, and the anonymization key are not included. The CAD extraction and scenario-selection source snapshots are in `audit/`; rerunning raw CAD extraction would require the original drawing and additional tooling and is not part of this 论文_02_洪水传播与动态逃生_Claude稿's reproduction command.

## Scope and authorship

This is a working preprint, not an externally submitted manuscript. No author identity, affiliation, prior discovery, publication, or field validation has been invented. New algorithms, experiments, and exposition in this package were developed with AI assistance in this chat; they must not be retroactively attributed to the original competition work. The manuscript and source data have not been published or uploaded.

The strongest current limitation is the hazard surrogate: conservation is verified, but the handling of sloped tunnels, merging fronts, and mean depth is not a calibrated hydraulic model. The CAD graph also needs engineering validation. The routing theorems remain conditional statements, and the empirical conclusions are explicitly model-relative.
