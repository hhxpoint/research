# Research Craft：从高星科研技能中提炼的"手艺"

> 本文件说明 `research-craft` 技能的来源、提炼方法与使用方式。技能正文在
> [`skills/research-craft/SKILL.md`](../skills/research-craft/SKILL.md)，五份领域手册在
> `skills/research-craft/references/`。

## 1. 为什么要单独沉淀"手艺"

`auto-research` 解决的是**流程与证据**：阶段、门禁、台账。
但流程正确不等于工作好：图可能误导、写作可能空转、实验设计可能不服务 claim、观察可能只记最后指标、
解释可能把相关性写成因果。这些是**研究者的手艺**，需要单独的、可执行的规则集。

`research-craft` 因此不做流程编排，只回答："这一步怎样算做对了？"

## 2. 来源与提炼方法

2026-11-24 的星标快照（GitHub API）：

| 来源 | Stars | 主要提取内容 |
|---|---|---|
| [Imbad0202/academic-research-skills](https://github.com/Imbad0202/academic-research-skills)（ARS） | 58.3k | 论文结构/贡献写法、anti-patterns、写作质量与引用完整性、审稿/rebuttal 流程、统计可视化标准 |
| [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) | 58.3k | evidence binding、no-fabrication 清单、报告规范、作图诚信与可访问性 guardrails、导出与 provenance |
| [wanshuiyin/Auto-claude-code-research-in-sleep](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep)（ARIS） | 19.7k | claim→证据→run order 实验规划、observation→interpretation→implication 分析结构、反 claim、预算与里程碑 |
| [karpathy/autoresearch](https://github.com/karpathy/autoresearch) | 100.5k | 固定预算/单指标迭代、只改一处、git 即记忆、可机械验证 |
| [uditgoenka/autoresearch](https://github.com/uditgoenka/autoresearch) | 6.9k | Modify→Verify→Keep/Discard、TSV 记账、fork-and-flush 的循环纪律 |

提炼规则：

1. 只保留**能改变结论可信度**的条目；纯工具用法放在对应技能里，不放这里。
2. 每条尽量落到"何时会害你 + 怎么检查/修复"，避免口号。
3. 转写为 DSH 可执行动作（读什么、写什么、检查什么），而不是复制上游长文。
4. 与 `auto-research` 的阶段/门禁对齐：本技能是"手艺标准"，auto-research 是"流程状态机"。
5. 来源只做方法与观点的参考，正文为原创转写；不复制上游受版权保护的文本。

## 3. 五份手册的定位

| 手册 | 解决的问题 | 何时读 |
|---|---|---|
| [`figures.md`](../skills/research-craft/references/figures.md) | 图是否忠于证据、可读、可复现 | 画图/审图/选色/排版/导出 |
| [`writing.md`](../skills/research-craft/references/writing.md) | 论文是否有论证、claim 是否有证据、语言是否合格 | 写/改/投稿/返修 |
| [`experiment-design.md`](../skills/research-craft/references/experiment-design.md) | 实验是否服务 claim、对照是否公平、预算/顺序是否合理 | 设计实验/写计划/评审方案 |
| [`experiment-observation.md`](../skills/research-craft/references/experiment-observation.md) | 过程是否记录完整、异常是否处理、是否可复现 | 跑实验/看日志/排异常/复现 |
| [`phenomenon-understanding.md`](../skills/research-craft/references/phenomenon-understanding.md) | 解释是否超出证据、机制是否有探针、claim 强度是否匹配 | 分析结果/写 discussion/审稿/决策 |

## 4. 与仓库其它部分的关系

```
research-stack（总入口）
 ├─ research-craft（手艺标准：图/写/设计/观察/理解）
 ├─ auto-research（流程与门禁：阶段、证据台账、签核）
 ├─ 具体执行技能（scientific-writing / scientific-visualization / experiment-plan /
 │                 analyze-results / academic-paper / academic-paper-reviewer ...）
 └─ 工具（dsh_skills / auto_research / build_lock / apply_notices）
```

- `auto-research` 的 `experiments` 门禁要求 `RESULTS.md` 含 `## Observations`，对应本技能
  `experiment-observation.md` 的"观察记录"要求；统计/偏差章节对应 `phenomenon-understanding.md`。
- `writing` 阶段：本技能 `writing.md` + `academic-paper` / `scientific-writing`；claim 仍要在
  `evidence/claim_map.json` 绑证据。
- 作图：本技能 `figures.md` + `scientific-visualization`（工具与 style）。
- 返修：本技能 `writing.md` 第 10 节 + `academic-paper-reviewer` 的审稿面板。

## 5. 质量门槛（技能自检）

- 五份 references 均含：核心原则、操作清单、反模式、交付前检查表；
- 规则可被 `auto-research` 阶段/门禁引用，不依赖特定模型或工具；
- 定期回看上游（ARS/K-Dense/ARIS）更新，但只在"能改变结论可信度"时改动；
- 任何新增规则要能回答："如果违反它，会出现什么具体的坏结果？"

## 6. 维护

- 更新上游认知时，同时更新 `CHANGELOG.md` 与技能 `metadata.version`；
- 若规则导致 `auto-research` 门禁变化，需同步模板、测试与 `docs/auto-research.md`；
- 修改技能文件后运行 `python tools/apply_notices.py --write`、`python tools/build_lock.py --from-installed`、
  `python tools/dsh_skills.py install --mode full`，再跑完整测试。
