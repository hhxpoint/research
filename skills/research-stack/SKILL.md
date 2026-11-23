---
name: research-stack
description: 科研技能栈总入口：按任务路由到文献综述、实验计划、结果分析、论文写作、审稿返修、引用校验、图表、顶会模板等具体技能，并给出顶会投稿、中文期刊、系统综述四条推荐流水线。当用户要做科研（选题、读文献、做实验、写论文、润色、返修、查引用、投稿）但不确定该用哪个技能时，先加载本技能。
metadata:
  version: "0.1.0"
  generated: "2026-11-23"
  source: "https://github.com/hhxpoint/research"
---

# Research Stack：科研技能路由

本机已安装一套科研技能（DSH 用户级 `~/.dsh/skills/`，安装源：`hhxpoint/research`）。
本技能只做**路由与流水线编排**，具体方法论在对应技能里；不要在本技能里重复长篇写作指导。

## 1. 技能地图（先查表，再加载具体技能）

| 任务 | 首选技能 | 备注 |
|---|---|---|
| 找论文 / 读单篇 / related work / 文献速览 | `research-lit` | 检索与研究问题拆解 |
| 系统综述 / PRISMA / 元分析 / 事实核查 | `deep-research` | ARS 13-agent 研究团队（8 模式） |
| 系统综述的标题摘要筛选、PRISMA 计数、kappa | `sr-screener` | 需要已有 protocol / 候选文献库 |
| 把 idea 变成实验计划：消融矩阵、算力预算、运行顺序 | `experiment-plan` | claim-driven |
| 实验结果统计、对比表、趋势与下一步实验 | `analyze-results` | 先有 results 文件 |
| 英文论文成稿 / 分节起草 / 修订 / 摘要 / 格式转换 | `academic-paper` | 11 模式，含 citation-check 与 rebuttal-audit |
| 预投稿审稿 / 模拟审稿意见 / 审稿人培训 | `academic-paper-reviewer` | 5 席位评审面板 |
| 从 0 到投稿的全流程（10 阶段 + 诚信闸门） | `academic-pipeline` | 编排前四个技能 |
| 中文写作 / 润色 / 中文返修信 | `research-writing-skill` | 保留公式、术语、数字 |
| 引用校验 / BibTeX / DOI→BibTeX / OpenAlex/PubMed | `citation-management` | 有 `validate_citations.py` |
| 期刊级图表（多面板、色盲友好、导出规格） | `scientific-visualization` | matplotlib/seaborn |
| 顶刊顶会模板：Nature/Science/Cell/NeurIPS/PLOS/NIH/NSF | `venue-templates` | LaTeX 脚手架 |
| 指标驱动的迭代循环（改一处→机械验证→keep/revert） | `autoresearch` | 适用于代码、实验、写作等可度量目标 |
| 科研总入口（本技能） | `research-stack` | 不确定时先加载 |

## 2. 推荐流水线

### A. 英文顶会/顶刊投稿（推荐）
1. `deep-research` 立题 + 文献地图（产出 `IDEA.md` / `RELATED_WORK.md`）
2. `experiment-plan` → 产出实验矩阵与算力预算
3. 跑实验 → `analyze-results` 产出 `RESULTS.md`（含对比表与统计）
4. `venue-templates` 选模板 → `academic-paper` 成稿
5. `academic-paper-reviewer` 预审一轮 → `academic-paper` 的 revision 模式返修
6. `citation-management` 校验全部引用 → `scientific-visualization` 出图
7. 投稿后：`academic-paper` 的 `rebuttal-audit` 模式处理审稿意见

### B. 中文期刊 / 组会报告 / 学位论文
1. `research-lit` 或 `deep-research` 做文献与问题梳理
2. `research-writing-skill` 写作/润色/返修（保留术语与实测数字）
3. `scientific-visualization` 出图 → `office`/`office-docx` 落盘为 Word/PDF

### C. 系统综述 / PRISMA
1. `deep-research` 的 systematic review 模式
2. `sr-screener` 做双盲筛选、冲突裁决与 PRISMA 计数
3. `academic-paper` 的 `lit-review` 模式成稿

### D. 可度量的迭代优化（实验/代码/内容）
`autoresearch`：明确 `Metric:` 与 `Verify:` → 一次只改一处 → 先 commit 再验证 → keep/revert → TSV 记账。

## 3. DSH 使用注意

- 上表中的 agent 数量（13/12/7）来自上游 Claude Code 实现，在 DSH 里表现为**方法论与角色清单**，不是真正的多 agent 常驻团队。需要独立评审视角时，用 DSH 的 `subagent` 工具模拟（例如把论文交给一个"审稿人"子代理）。
- 上游的 slash commands / hooks / MCP server 未移植；遇到时按技能正文的流程用当前工具执行。
- 产出约定：中间产物放 `notes/`（如 `IDEA.md`、`EXPERIMENT_PLAN.md`、`RESULTS.md`），成稿放 `paper/`；引用校验结果与图表放 `evidence/`。
- 引用与数字必须可回溯：任何引用先过 `citation-management` 的校验脚本，任何数字注明来源文件/表格。
- 不要同时加载多个长技能正文；按流水线阶段逐个加载，避免上下文膨胀。

## 4. 交付前自检清单

- [ ] 每个 claim 有证据（实验结果文件 / 论文原文 / 数据表）
- [ ] 引用全部通过校验（无编造、作者年份一致）
- [ ] 图表有坐标轴单位、误差线说明、色盲友好
- [ ] 论文包含 limitations / ethics / data availability / AI 使用声明
- [ ] 返修回复逐条对应 reviewer comment，并给出修改位置
