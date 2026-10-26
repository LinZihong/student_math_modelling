# Buying warning-delay tolerance with fixed mine escape routes

完整英文工作论文，12页。入口为 `../output/pdf/regional_alarm_escape_preprint.pdf`，源文件为 `main.tex`。

## 最终选择

主问题是区域警报下的单条固定预案：先给定10/20/30分钟通知延迟目标，再寻找对候选区域水源共同可行的路线，路程作为实现保证的代价。时间档位菜单没有加入主模型。

论文第2节区分突水开始、检测、收到警报三个时间；不假定检测时间戳等于事故起始时刻。第3.1节证明：在同一水源集合、相同路线约束及“晚出发可行则早出发也可行”的模型中，按延迟选多条路线不能提高最大共同保证，但可能减少早期报警时的行走负担。若信息同时缩小水源集合或水情不再单调，这个结论不适用。

## 证据与边界

- 两网络、8个区域、每区8设计+8未见水源；123个人员位置—区域组合。
- 重点区域113个完整候选水源节点，区外548个起点，三个延迟目标，共1644次目标检查。
- 30分钟目标：原最短路线268个起点达标，多走20%时501个，无距离限制时545个。
- P0104的67米绕行、113节点覆盖与24个新中点检查；不把它当作代表性独立确认样本。
- 原8水源预案被遗漏水源击穿；正文保留这一负结果。
- 545条固定路线在流量翻倍时只有329条仍保持目标；反转同时事件处理顺序后545条仍保持目标。没有将重新选路后的表现与固定路线敏感性混淆。
- 主算法100个小图对照全路径枚举，400次可行性/长度比较和100次截止区间验证通过。

所有保证都是有限情景、简化体积转移模型内的保证。未完成实际矿井水力校准、连续源位置覆盖或人员行为验证。这是一篇信息受限逃生预案的计算研究，不是可直接部署的安全方案。

## 文献定位

论文引用矿井动态选路、检测时延与传感器布点、有限预备策略的K-adaptability三条相关文献线索。检测时刻与物理起始时刻的区别由观测机制说明，没有将“通常知道/通常不知道总延迟”写成未经调查的行业事实。也不声称多标签搜索或鲁棒优化本身是新发明。

检索使用的主要原始来源：
- Wu et al., 2020, Safety Science, DOI 10.1016/j.ssci.2020.104836：时间变化下的最早到达路径。出版商本轮全文请求403，使用可获取摘要与此前已核查书目；没有据此声称通读全文或排除全部现有工作。
- Wu et al., 2021, Scientific Reports 11:2621, DOI 10.1038/s41598-021-82121-7：水位传感器布点与从事故发生到被监测的时间。搜索返回出版商正文/摘要；直接打开本轮认证跳转不可用。
- Hanasusanto, Kuhn and Wiesemann, K-Adaptability in Two-Stage Robust Binary Programming：读取作者公开稿 https://optimization-online.org/wp-content/uploads/2014/03/4294.pdf 。准备多种策略并在观测后选择，必须明确究竟观测了什么。

这些文献足以定位当前问题，不构成穷尽性新颖性证明。

## 重现

代码和结果在相邻的 `regional_escape/`。安装旧 `preprint/requirements.txt` 中依赖到独立Python3.12环境。完整流程从工作区根目录顺序运行：

    python regional_escape/prepare.py
    python regional_escape/test_solver.py
    python regional_escape/study.py
    python regional_escape/dense.py
    python regional_escape/dense_optimize.py
    python regional_escape/midpoint_check.py
    python regional_escape/summarize.py
    python regional_escape/longer_detours.py
    python regional_escape/target_guarantees.py
    python regional_escape/uncapped_example.py
    python regional_escape/summarize_longer.py
    python regional_escape/paper_sensitivity.py
    python regional_alarm_paper/make_figures.py

必须等prepare完成再运行study。缓存无自动协议失效机制；更改协议应在新目录执行，不能把新参数与旧文件混用。完整复现需要工作区内的原preprint代码和数据；仅复制这个LaTeX目录不等于复制完整研究包。本机通过PYTHONPATH=/tmp/mine-preprint-deps使用既有依赖，跨机器不应依赖该临时路径。

编译：

    cd regional_alarm_paper
    latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build -jobname=regional_alarm main.tex

`audit/`包含最后的页图、文本提取和交付审计；完整水源场景与路线不复制进审计文件。以前的两篇论文和原实验未覆盖。

研究、实现及写作含AI辅助。未虚构作者、机构、实际事故验证或投稿记录；外部使用前需要署名作者审阅并承担责任。
