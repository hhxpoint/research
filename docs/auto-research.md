# Auto Research：把科研过程沉淀成状态机

> 这是 `auto-research` 技能的配套设计文档。技能本身在
> [`skills/auto-research/SKILL.md`](../skills/auto-research/SKILL.md)，
> 实现工具在 `skills/auto-research/scripts/auto_research.py`（仓库内入口 `tools/auto_research.py`）。

## 1. 为什么不是"一键生成论文"

2026 年这一波 auto-research（ARIS、AI-Scientist、karpathy/autoresearch 等）的共识是：

- 模型可以写代码、读文献、写草稿，但**不能对真实性负责**；
- 生成速度远快于验证速度，于是最大的风险变成**编造引用、编造实验、悄悄改口径**；
- 真正可复用的不是某段 prompt，而是**流程**：产物、门禁、证据链、可恢复的状态。

所以本仓库沉淀的是一个**可审计的科研状态机**：agent 负责推进，门禁负责让它拿出证据，
人负责关键决策。它借用 ARIS 的"阶段 + 诚信闸门"思想、Karpathy 系的"可机械验证的循环"，
但用 DSH 原生工具实现，不依赖 Claude Code 的 MCP / hooks / slash commands。

## 2. 架构

```
状态：state.json（schemaVersion / project / settings / history）
决策：DECISIONS.md（append-only，advance 与 log 自动追加）
产物：IDEA → LIT_REVIEW → EXPERIMENT_PLAN → RESULTS → PAPER → REVIEW/REBUTTAL → 清单/复现
证据：evidence/citations.json（引用核验）+ evidence/claim_map.json（claim→证据）
门禁：GATES[phase] = f(project, settings) -> problems[]
```

实现要点：

- **纯标准库**、无网络依赖；任何阶段都可以中断后从 `state.json` 恢复。
- **门禁是代码**，不是提示词：`advance` 会真的检查文件、章节、引用状态、审稿回复覆盖率、复选框。
- **强制跳过可审计**：`advance --force --reason "..."` 会把 `FORCED:` 原因写进
  `DECISIONS.md` 与 `state.json.history`，后续 review 能看到。
- **模板哨兵**：所有模板含 `<!-- AUTO-RESEARCH: TODO -->`，没删就过不了门禁，避免空壳产物糊弄。
- **阈值可配**：`init --min-refs 20 --min-claims 8 ...`；默认值见
  `state.json.settings`，工具不替用户拍板。

## 3. 阶段与门禁明细

| 阶段 | 门禁检查 | 拒绝的典型情况 |
|---|---|---|
| ideation | IDEA.md 四节齐全、无占位符 | 只有标题、没有可证伪假设 |
| literature | LIT_REVIEW.md 三节；citations.json ≥ minRefs 且全部 verified、有 id | 引用未核验、条数不足、台账格式错 |
| experiment_plan | EXPERIMENT_PLAN.md 五节齐全 | 没写预算/成功判据 |
| experiments | RESULTS.md 三节；results/ 文件 ≥ minResultFiles | 只有结论没有原始结果 |
| writing | PAPER.md 六节；claim map ≥ minClaims 且都有 evidence；引用仍 verified | 论文 claim 找不到证据、引用回退 |
| review | REVIEW.md ≥ minReviewItems 个 `### Rn`；REBUTTAL 逐条回应；无 UNRESOLVED | 漏回审稿意见、假回复 |
| final | 清单无未勾选项；PROVENANCE 四节；writing 门禁复核通过 | 没写 AI 披露/复现命令 |

`check` 会复核**当前阶段及之前所有阶段**，防止后面改坏前面的证据。

## 4. 自动模式与人工检查点

**agent 可自动**：在门禁通过、证据齐全的前提下推进阶段、补产物、跑受权限约束的工具。

**必须人工确认**：

1. 研究问题 / 假设 / 范围实质变更；
2. 花大算力或花钱之前（先确认 `EXPERIMENT_PLAN.md` 的预算）；
3. 声称"实验成功/结论成立"之前（人工抽查 `results/` 原始数据）；
4. 投稿、对外发布、公开仓库推送；
5. `--force` 跳过门禁。

这些规则写在技能正文里；`DECISIONS.md` 是人工签核的落点（`log --kind signoff`）。

## 5. 与生态里方案的对应

| 生态做法 | 本仓库的对应 | 差异 |
|---|---|---|
| ARIS 的 10 阶段 pipeline + Stage 2.5/4.5 诚信闸门 | 7 阶段状态机 + 每阶段代码门禁 + 引用/claim 台账 | 不依赖 Claude Code agents/MCP；门禁可执行、可测试 |
| Karpathy/uditgoenka 的"改一处→机械验证→keep/revert" | `autoresearch` 技能（指标循环）作为 experiments 阶段的执行器 | 循环只负责执行，真实性与写作交给门禁 |
| AI-Scientist 的模板化自动写作 | `academic-paper` / `scientific-writing` / `venue-templates` | 先有证据与 claim map，再写；不允许"先写后编" |
| 人工 PRISMA/系统综述 | `deep-research` + `sr-screener` + citations.json | 引用核验是硬门禁 |

## 6. 快速开始

```bash
# 在仓库根目录
python tools/auto_research.py init D:\research\my-topic \
  --title "Dysarthric voice cloning with style control" \
  --question "How to preserve pathological cues while cloning speaker identity?" \
  --venue "Interspeech 2027"

python tools/auto_research.py status D:\research\my-topic
python tools/auto_research.py next D:\research\my-topic
```

然后按 `next` 的指引填写产物；每完成一个阶段：

```bash
python tools/auto_research.py check D:\research\my-topic
python tools/auto_research.py advance D:\research\my-topic --by agent
```

在 DSH 会话里可以直接说：「用 auto-research 开始一个关于 X 的课题，建在 D:\research\X」，
agent 会按本技能流程执行；关键节点它会停下来问你。

## 7. 失败与恢复

- 门禁失败：`check` 会列出具体缺什么；补证据后重跑，不要用 `--force` 糊过去。
- 中断后恢复：`status` 看阶段与未过门禁；`next` 看下一步动作；历史在 `state.json.history`。
- 想回退阶段：直接改 `state.json.project.phase`（工具不提供自动回退，避免掩盖问题），
  并在 `DECISIONS.md` 记录原因。
- 状态损坏：`state.json` 无法解析时工具返回退出码 3；从 `git` 或备份恢复，不要手工猜。

## 8. 测试与门禁自身质量

`tests/test_repo.py` 中的 `TestAutoResearch` 覆盖：初始化、模板哨兵、逐阶段推进、
引用未核验/条数不足、审稿回复缺失、清单未勾选、`--force` 必须带 reason、
`check` 复核历史阶段、状态文件损坏等情况。门禁代码本身也在 CI 的 Python 3.10/3.12 上跑。
