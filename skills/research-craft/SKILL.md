---
name: research-craft
description: 科研手艺总纲：从高星科研技能/方法论中提炼的硬规则与检查表，覆盖作图、写作、实验设计、实验观察、现象理解五个环节。当用户要做图、写/改论文、设计或复盘实验、观察训练/评测过程、解释结果与机制，或需要"这个结论站不站得住"的质量判断时加载；按任务读取对应 references。
metadata:
  version: "1.0.0"
  source: "https://github.com/hhxpoint/research"
  distilled_from: "ARS(58.3k*), K-Dense scientific-agent-skills(58.3k*), ARIS(19.7k*), karpathy/autoresearch(100.5k*), uditgoenka/autoresearch(6.9k*), 2026-11-24 star snapshot"
---

# Research Craft · 科研手艺总纲

本技能只保留"能改变结论可信度"的经验，不写泛泛的科研鸡汤。五份 references 分别覆盖：
**作图、写作、实验设计、实验观察、现象理解**。每条规则尽量给出"什么时候会害你"和"怎么检查"。

来源说明见 [docs/research-craft.md](https://github.com/hhxpoint/research/blob/main/docs/research-craft.md)：
从 ARS（58.3k★，学术流水线+诚信闸门）、K-Dense（58.3k★，科学写作/可视化）、
ARIS（19.7k★，实验计划/结果分析）、karpathy/autoresearch（100.5k★，固定预算单指标循环）、
uditgoenka/autoresearch（6.9k★，keep/revert 纪律）中提炼，并转写为 DSH 可执行规则。

## 何时读哪份 reference

| 任务 | reference | 一句话目标 |
|---|---|---|
| 做图 / 审图 / 选配色 / 排版 | `references/figures.md` | 图先忠于证据，再谈好看 |
| 写论文 / 摘要 / intro / related work / 返修信 | `references/writing.md` | 每个 claim 有证据，读者能顺着逻辑走 |
| 设计实验 / 基线 / 指标 / 消融 / 预算 | `references/experiment-design.md` | 每个实验都为一个可证伪的 claim 服务 |
| 跑实验 / 记录 / 监控 / 排 anomalous | `references/experiment-observation.md` | 先把过程看全，再下结论 |
| 解释结果 / 找机制 / 写 discussion / 判 claim 强度 | `references/phenomenon-understanding.md` | 分清"发生了什么"和"为什么" |

## 五条跨领域铁律（先记住这些）

1. **证据先于表达**：图、表、正文里的每个数字都能指回原始文件；不能指回就删掉或标注未核验。
2. **一个 claim 一个实验**：实验必须能改变审稿人对某个具体 claim 的信念，否则砍掉；反 claim（"增益只来自更多参数"）必须有对照。
3. **观察先于解释**：先记录完整、可复现的观察（含失败运行），再做机制解释；不允许只看最后一个指标就讲故事。
4. **强度匹配措辞**：相关性不写成因果，单种子不写成稳定提升，benchmark 领先不写成机制更优。措辞升级必须伴随证据升级。
5. **反幻觉是底线**：引用必须核验；数字必须溯源；失败与偏差必须记录。宁可写"未验证"，不写"看起来合理"。

## 各领域速查（细节见 references）

### 作图
- 先写"这张图要支持哪一句 claim"，再选图型；一张图只讲一个结论。
- 条形图/面积图从 0 开始；点线图可非零但必须披露断轴；双轴优先拆成对齐面板。
- 误差线必须写明是 SD/SE/CI/分位数，并给 `n` 与重复单位；不显示不确定性的对比图不可用于强结论。
- 颜色冗余编码（颜色+形状/线型/直接标注）；不用彩虹色表示连续量；灰度可读性检查。
- 按最终物理尺寸导出（mm），字体≥7pt，矢量优先，嵌图保留来源与处理记录。
- 交付前：最终尺寸看一遍、灰度看一遍、把图里数字和源表逐个对一遍。

### 写作
- 故事脊柱：问题 → 空白 → 洞察 → 方法 → 证据 → 边界；主 claim ≤2，先写"反 claim 对照"。
- 摘要按公式写：背景一句、空白一句、做法一句、关键数字一句、意义一句、边界一句。
- 贡献句必须可检验（机制级、范围明确），不能是"我们提出了一个框架"。
- 方法按"实际做了什么"写，含数据划分、超参、算力、随机种子与失败运行。
- 结果按 claim 顺序写，先表/图后叙述；负结果与偏差照写；不把非显著写成等价。
- 每一处"novel"都要有 nearest prior work 对比；引用零孤儿、DOI 可查、引文与正文一致。
- 返修：逐条分类（editorial/scientific/statistical/policy），接受/部分接受/礼貌反驳都要给证据与修改位置；不谄媚、不 scope creep。
- 禁用 AI 腔：delve/crucial/it is important to note/throat-clearing 开场/为凑字数注水。

### 实验设计
- 先冻结 claim 与"最小可信证据"，再设计实验块：主结果、novelty 隔离、简洁性、frontier 必要性、失败分析。
- 基线选"最强且能复现"的少数族，不用弱基线凑数；同一评测协议、同一调参预算。
- 指标分主次；噪声指标至少 3 seeds，报 mean±std/CI 与效应量；预先定成功/失败/终止判据。
- 消融一次只动一个变量；关键组件做删除/替换对照；能全因子就全因子。
- 检查 confound：参数量/算力/数据量/调参预算/数据泄漏/评测集污染；公平性写进计划。
- 先 sanity（小样本过拟合、指标自测、baseline 复现）再烧大算力；must-run 与 nice-to-have 分开。
- 计划落盘为 `EXPERIMENT_PLAN.md` + run tracker；偏差与没跑的实验记录在案。

### 实验观察
- 每次 run 记录：run id、git commit、完整配置、数据版本/校验和、seed、硬件、时长、逐 step 指标、评测协议、产物路径。
- 原始日志只追加不修改；失败/中断/异常 run 也要登记，禁止删掉不利 run。
- 先做 sanity：单 batch 过拟合、打乱标签、指标单位测试、baseline 复现、泄漏探针、确定性检查。
- 训练中看曲线形状与异常（NaN、loss 尖峰、吞吐异常、eval 抖动），异常先复现再解释。
- dev/val 用于决策，test 只在最后用一次；不同实验必须同一评测协议与数据划分。
- 异常分类：bug / 方差 / 真效应 / 数据问题 / 实现差异；记录"预期 vs 实际 vs 惊讶点"。

### 现象理解
- 把结论拆成三层：观察（数字）→ 解释（机制假设）→ 推论（应用/影响）；三层措辞强度不同。
- claim 强度阶梯：相关 → 控制变量后的关联 → 干预实验 → 机制证据；不能跳级。
- 列替代解释：confound、选择偏差、测量误差、回归均值、算力/数据优势、调参优势、benchmark artifact、seed 运气。
- 用探针而非讲故事：消融、干预、表征探针、错误分类、逐 slice 指标、边界测试、scaling 曲线。
- 统计与实用显著性分开；看效应量/CI，不只看 p 值；多重比较要校正。
- 曲线形状（单调/U 型/平台/断崖）先查方差与协议差异，再给机制解释。
- 负结果与边界条件是贡献；写清"什么会推翻这个结论"，并把它变成下一个实验。

## 与自动科研流程的配合

- `auto-research` 的 `experiment_plan` 阶段：读 `experiment-design.md`，产出 claim→证据→run order。
- `experiments` 阶段：读 `experiment-observation.md`，保证 run 记录与失败日志完整；`RESULTS.md` 新增的
  `## Observations` 小节写"观察到了什么（含失败/异常/偏差）"，再写 `## Statistical checks` 与 `## Deviations`。
- `writing` 阶段：读 `writing.md`；每个 claim 在 `evidence/claim_map.json` 绑定证据。
- `review` 阶段：读 `writing.md` 的返修部分 + 本文件 anti-pattern；用 subagent 模拟魔鬼代言人。
- 图表：读 `figures.md`；产出图与数据源、导出参数、provenance 一起交付。

## 交付前总检查（任何一项不过就不要说"完成"）

- [ ] 每个结论句都能指到图/表/实验 run；每个引用都可核验
- [ ] 主要对比有不确定性、有基线、有相同评测协议
- [ ] 至少一个能推翻主 claim 的对照/反例已被考虑或排除
- [ ] 失败 run、偏差、改过的设置都记录在案
- [ ] 图在最终尺寸与灰度下可读，数字与源表一致
- [ ] 措辞强度 ≤ 证据强度；limitations 具体而非套话
