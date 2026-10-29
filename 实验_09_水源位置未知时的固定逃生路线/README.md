# 实验 09：报警只给区域时的固定逃生路线

论文 09 的全部证据。复用 `实验_07` 已缓存的 1,587 个单水源洪水时间表（`fields/`、`upper/`），不重算洪水。

## 设计（见 `protocol.json`）

- 四种方案：最短路、避开报警区规则、精确鲁棒路线（对区内所有水源与所有不超过目标的延迟都成立的最短路线）、已知精确水源（上限）。
- E1 延迟：四象限，0–120 分钟。
- E2 分辨率：等巷道长度递归二分 1–128 区（三个切割角度）、四象限、两种穿过井筒群的切分。
- E3 水源范围：只保留 CAD 标注水区 50–1000 m 内的节点。
- E4 双倍流量。
- 指标：区外/区内起点数；全矿（起点，水源）对的保障比例，并把未保障部分分为“信息不足”和“无路可走”。

## 运行顺序

```sh
python zones.py              # 生成 partitions.json
python run_experiments.py    # 全部任务，可中断续跑，结果写入 results/
python rerun_timeouts.py     # 以 1 小时上限重解触及时间上限的查询
python analyze.py            # summary.json
python realized.py           # realized.json：实际被困比例
python verify.py             # verification.json：回归、逻辑一致性、嵌套、独立正向行走
```

共 2,558,244 个查询。主运行中 7 个查询触及时间上限（3 秒/次搜索、30 秒/查询；均为至少覆盖四分之一矿井的大区内部起点），随后用 `rerun_timeouts.py` 以 1 小时上限重解，每个在 18 秒内完成，结论均为“无共同路线”，记录见 `timeouts_rerun.json`；所有汇总数字不变。`verification.json` 全部通过：与实验 07 的 19,044 个查询完全一致；747 对父子分区无违例；23,012 次独立正向检查无失败。

`core.py` 依赖 `实验_07/engine.py`，后者依赖 `实验_06` 与 `论文_04/code`。
