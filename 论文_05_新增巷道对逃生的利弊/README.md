# Delayed departure can reverse the exposure benefit of a mine escape connection

新论文独立于旧的 论文_04_绕行与延迟容忍_路线菜单探索/，没有覆盖原稿或原实验。

## 论文的实际结论

新增通道不仅改变人的路线，也改变水的路线。在所研究的低洼起点网络中，它先分走原逃生路线上的水，让早出发的人受益；随后向起点供水，使晚出发的人无法靠重新选路消除暴露。

- 16组事先固定的新参数组合中，12组在两种模型里均达到预设的“早期改善至少2厘米、晚期恶化至少2厘米”标准。其余4组没有被改算成成功。
- 晚期损失有一个与新路线算法无关的证据：新布局的起点水深超过旧布局一条完整逃生路线的最大水深。该比较在96组模型与步行速度检查中成立。
- 网格加密、改变交叉口蓄水面积、随水深降低步速后，所测案例仍保留正差距。某项扩大后的敏感性检查仅有约1.9厘米差距，因此不能说所有变体都通过2厘米标准。
- 这是经过数值核查的机制研究。水深是暴露指标，不是伤亡概率；没有实测矿井校准，也不建议据此关闭任何真实通道。模型分歧和适用边界在正文中报告。

## 阅读

- main.tex：自包含英文论文。
- figures/：三张正文图。
- ../阅读入口_PDF/论文_05_新增巷道对逃生的利弊.pdf：交付PDF。
- ../实验_新增巷道与水动力验证/RESEARCH_STATE.md：完整的研究决策记录，包括未保留的结果。

## 重现

代码与原始结果位于相邻的 实验_新增巷道与水动力验证/。使用Python3.12及其中的 requirements.txt。下面的命令从工作区根目录执行。建议在独立虚拟环境运行：

    python -m pip install -r 实验_新增巷道与水动力验证/requirements.txt
    python 实验_新增巷道与水动力验证/shallow_water.py
    python 实验_新增巷道与水动力验证/network_fv.py --verify
    python 实验_新增巷道与水动力验证/benchmark_swmm.py
    python 实验_新增巷道与水动力验证/benchmark_transient.py
    python 实验_新增巷道与水动力验证/run_confirmation.py
    python 实验_新增巷道与水动力验证/audit_confirmation.py
    python 实验_新增巷道与水动力验证/continuous_certificate.py
    python 实验_新增巷道与水动力验证/refine_confirmation.py
    python 实验_新增巷道与水动力验证/slowed_witness.py

保留的结果用于重现图表时不必再运行水力模拟。确认实验由 confirmation_protocol.json 定义，快照及散列在 results/confirmation_v1/protocol_snapshot.json。原始水力输出较大，不能用小型汇总文件代替它们来宣称“完整独立复现”。

代表性曲线来自探索阶段的Q=0.5情景，而不是16组确认实验之一。重新生成该曲线需先运行下列同参配对：

    PYTHONPATH=investigation python - <<'PY'
    from network_fv import experiment
    from shortcut_screen import simulate
    for added in [False, True]:
        experiment(added, dx=6.25, area=16., q=.5)
        simulate(.5, added, dx=6.25, dt=.125, bz=.5)
    PY
    python 实验_新增巷道与水动力验证/make_figures.py

make_figures.py写入 实验_新增巷道与水动力验证/figures/。论文中的图是这些图的副本。LaTeX编译命令：

    cd delay_reversal_paper
    latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build -jobname=delay_reversal main.tex

本机SWMM macOS arm64轮子中的OpenMP库最初有签名问题；修复后的临时安装位置及诊断保留在研究记录中。这是运行环境问题，不是科学结果。其他系统通常可直接使用正常安装的官方工具包。

## 边界与来源

不需要原始CAD图即可重现本论文。本文没有声称在真实矿井上验证了反转，也没有将新增算法和实验追溯归属为学生原竞赛工作。研究及写作包含AI辅助，外部使用前应由署名作者核查并承担责任。没有对外上传或投稿。
