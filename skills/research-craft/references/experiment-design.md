# 实验设计：每个实验都为可证伪的 claim 服务

> 提炼自 ARIS `experiment-plan`（19.7k★，claim→证据→run order / 反 claim / 预算 / 里程碑）、
> K-Dense `experimental-design`、ARS `academic-paper` 的 review-target 绑定，
> 以及 karpathy/autoresearch（100.5k★，固定预算单指标）与 uditgoenka/autoresearch（6.9k★，keep/revert）的循环纪律。

## 0. 设计前先冻结三件事

1. **主 claim**（≤2）：机制级、可检验、范围明确。写成一句可判真假的话。
2. **反 claim**（必须排除的替代解释）：例如"增益来自更多参数""来自更长训练""来自评测集泄漏""来自调参预算"。
3. **最小可信证据**：一个强审稿人看到什么就会信？把"什么结果算成功、什么算失败"提前写死。

没写这三件事就开跑，通常会在看到结果后编故事。

## 1. 实验块（storyline）——先设计主表，再决定跑什么

| 块 | 回答的问题 | 常见做法 |
|---|---|---|
| 主结果 | 方法是否解决真正的瓶颈 | 与最强基线同协议对比，主表 |
| Novelty 隔离 | 主贡献本身是否有效 | 去掉核心组件/替换为朴素版本 |
| 简洁性检查 | 是否可以用更简单方案达到 | 与更复杂/更庞大的变体对比 |
| Frontier 必要性 | 现代组件是否真的必要 | 与最强更简单/更老替代方案对比 |
| 失败分析 | 方法仍在哪里失败 | 错误分类、逐 slice、定性例 |

每个块只保留"能改变审稿人信念"的实验；其余进 appendix 或砍掉。优先**少量强基线**，不用弱基线凑数。

## 2. 变量、对照与公平性

- 明确自变量（方法/组件/超参）、因变量（指标）、控制变量（数据、模型规模、算力、调参预算、评测协议）。
- 对照必须公平：同一数据划分、同一评测脚本、同一 early-stop/调参预算；我们的方法不能偷偷多调一轮。
- 算力匹配：若方法更贵，报告成本并做同算力对照（同等 GPU-hours 的 baseline）。
- 数据泄漏检查：预训练数据/评测集重叠、时间切分、按 subject 分组、normalization 只在 train 拟合。
- 负对照/ sanity 对照：打乱标签应掉到随机；随机噪声输入应失败；空基线应接近 chance。
- 人类评估：标注指南、双盲、一致性（Cohen's κ / Krippendorff α）、抽样规则。

## 3. 指标与统计

- 主指标 1–2 个（决定 claim），次指标辅助；不要用 10 个指标挑一个显著。
- 噪声指标 ≥3 seeds；报告 mean±std 或 95% CI；给出效应量（Δ 与相对提升）。
- 预先指定统计检验与多重比较校正；不要事后换检验。
- 显著性 ≠ 实用性：说明最小有意义的提升（例如 1% WER 在业务上是否重要）。
- 小样本/人类评估给置信区间；不要用单次运行下强结论。
- 主表同时给参数量/算力/推理成本，避免"用更多资源换分数"被误读为机制优势。

## 4. 消融与机制验证

- 消融一次只动一个变量；给"删除 / 替换 / 冻结 / 打乱"多种对照。
- 关键组件做 deletion study；能全因子就全因子（看交互效应，不只看主效应）。
- 机制假设要能预测：如果机制成立，X 情况下应更明显、Y 情况下应消失；设计边界实验验证，而不是只给主结果。
- 训练曲线/表征/错误类型可以作为机制证据，但要说明它们与 claim 的逻辑关系。
- 不要用"去掉后变差"直接证明机制；可能是容量/正则/优化差异。

## 5. 预算、顺序与终止条件

推荐里程碑（来自 ARIS）：

1. **Sanity**：数据管线、指标自测、单 batch 过拟合、baseline 复现；
2. **Baseline**：复现最强基线（同协议）；
3. **Main**：在主要设定跑最终方法；
4. **Decision**：跑决定 claim 的消融/对照；
5. **Polish**：鲁棒性、定性例、appendix。

每个里程碑写清：预算（GPU-hours / 成本）、预计时间、**stop/go 判据**、风险与缓解。
must-run 与 nice-to-have 分开；appendix 想法不许拖主证据。

## 6. 预注册与偏差记录

- 把假设、分析计划、主指标、成功/失败判据、终止条件写进 `EXPERIMENT_PLAN.md`（越早越好）。
- 记录每次偏离：改了什么、为什么、对结论的影响；不许事后悄悄改分析。
- 失败/中断 run 也要登记（见 `experiment-observation.md`）；删 run 等于篡改证据。
- 预设"kill criteria"：如果 X 周内主结果不达 Y，就转向/缩小 claim，而不是无限调参。

## 7. 计划产物（可直接映射到 auto-research）

`EXPERIMENT_PLAN.md` 至少包含：

- Claim map：claim | 为什么重要 | 最小可信证据 | 对应实验块
- Paper storyline：主文必须证明什么 / appendix 支持什么 / 主动砍掉什么
- 每个 block：claim tested / why / 数据与划分 / 对比系统 / 指标 / setup / 成功判据 / 失败解释 / 目标表图 / 优先级
- Run order 与里程碑（含 stop/go、成本、风险）
- 预算：总 GPU-hours、数据准备、人类评估、瓶颈
- 风险与缓解；final checklist

Run tracker 字段：run id / milestone / purpose / system / split / metrics / priority / status / notes / commit / config hash / seed。

## 8. 反模式

- Benchmark 愿望清单：跑很多 SOTA 但没有一个服务于 claim
- 弱基线/稻草人基线；只调我们的方法不调 baseline
- 单 seed 下强结论；噪声指标不做重复
- 看到结果后再编假设（post-hoc rationalization）
- 消融只做"删除后变差"，不检查容量/优化/正则解释
- 数据泄漏/评测集污染；不同实验用不同评测协议
- 主指标偷偷换（从 WER 换到某种"综合分"）
- 预算无上限、无 stop 判据，靠不断调参碰结果
- 人类评估无双盲/无一致性检验

## 9. 与 auto-research 门禁的对应

- `experiment_plan` 阶段：本文件 + `experiment-plan` 技能；产物要含上述章节（工具会检查）。
- `experiments` 阶段：`RESULTS.md` 必须记录观察、统计与偏差；run 记录按 `experiment-observation.md`。
- `writing` 阶段：每个 claim 在 `claim_map.json` 绑定证据；没有实验支撑的 claim 不许出现在论文里。
