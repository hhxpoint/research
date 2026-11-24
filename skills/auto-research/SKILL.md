---
name: auto-research
description: 自主科研状态机：把课题从选题、文献、实验计划、实验、写作、审稿到定稿沉淀成带门禁与证据审计的项目目录，支持 agent 自动推进与人工检查点。当用户说"开始一个课题/自动做研究/auto research/从头推进一篇论文/帮我把这个想法跑成论文"，或需要跨天恢复研究进度、审计证据链时使用。
metadata:
  version: "0.2.1"
  source: "https://github.com/hhxpoint/research"
---

# Auto Research · 自主科研状态机

本技能不是"一键生成论文"，而是把**科研过程**沉淀成可恢复、可审计、带门禁的项目状态机。
状态机由本技能目录内的 `scripts/auto_research.py` 维护（仓库内也提供 `tools/auto_research.py` 入口）。

- 工具位置：本技能目录下 `scripts/auto_research.py`；若在 hhxpoint/research 仓库中，也可用 `python tools/auto_research.py`。
- 状态文件：项目根 `state.json`（阶段、设置、历史）+ `DECISIONS.md`（append-only 决策/签核）。
- 模板：`templates/`，`init` 时复制到项目目录；模板中 `<!-- AUTO-RESEARCH: TODO -->` 是占位哨兵，**未删除则门禁不通过**。

## 一、阶段与门禁

| 阶段 | 产物 | 门禁（进入下一阶段前必须满足） | 主力技能 |
|---|---|---|---|
| ideation | `IDEA.md` | 有 Research question / Hypotheses / Contribution / Scope and risks 四节实质内容 | research-lit / deep-research |
| literature | `LIT_REVIEW.md` + `evidence/citations.json` | 三节齐全且每节有实质正文；引用条数 ≥ minRefs；**每条 status=verified，且 title、DOI/URL、verification.source/checked_at 齐全** | deep-research / citation-management |
| experiment_plan | `EXPERIMENT_PLAN.md` | Baselines / Metrics / Ablations / Compute budget / Success criteria 五节齐全 | experiment-plan |
| experiments | `RESULTS.md` + `results/` | 三节齐全；结果文件 ≥ minResultFiles；数字可回溯 | autoresearch / analyze-results |
| writing | `PAPER.md` + `evidence/claim_map.json` | 六节齐全且每节 ≥20 非空白字符；claim 数 ≥ minClaims、证据路径真实存在、paper_section 对应真实章节；引用仍全部核验 | academic-paper / scientific-writing |
| review | `REVIEW.md` + `REBUTTAL.md` | 审稿项 ≥ minReviewItems；每条 `### Rn` 都在 REBUTTAL 有回应；无 UNRESOLVED | academic-paper-reviewer / subagent |
| final | `SUBMISSION_CHECKLIST.md` + `PROVENANCE.md` + `DECISIONS.md` | 清单全部勾选；复现信息四节齐全；writing 门禁仍通过；**DECISIONS.md 有人工 `[signoff]` 签核** | venue-templates / citation-management |

门禁实现见 `scripts/auto_research.py` 的 `GATES`；阈值在 `state.json.settings`（`minRefs` 默认 10、`minClaims` 5、`minReviewItems` 3、`minResultFiles` 1）。

内容级检查：每个必填 `##` 章节必须有 ≥20 个非空白字符的正文（代码围栏/HTML 注释内的标题不算数）；
模板里的 `<!-- FILL: ... -->` 注释必须替换为真实内容；`results/` 只统计非空文件；清单 `- [ ]` / `* [ ]` / `+ [ ]` 都算未完成。

额外一致性校验：`citations.json` 的 `id` 必须唯一；`claim_map.json` 的 `paper_section` 必须是 `PAPER.md` 里真实存在的 `##` 标题，`evidence` 路径必须是项目内真实文件；`state.json` 的 `history` 链必须连续且与当前阶段一致（手工改 `phase` 会被判为状态损坏）。

## 二、标准流程

```bash
# 1) 立题：先和用户确认问题，再建项目（不要替用户决定研究问题）
python scripts/auto_research.py init <dir> --title "…" --question "…" --venue "NeurIPS 2027"

# 2) 当前阶段能做什么、还差什么证据
python scripts/auto_research.py status <dir>
python scripts/auto_research.py next <dir>

# 3) 填写/生成相应产物后，逐阶段检查并推进
python scripts/auto_research.py check <dir>
python scripts/auto_research.py advance <dir> --by agent

# 3b) 发现门禁暴露了前面阶段的问题：审计式回退（必须写原因）
python scripts/auto_research.py revert <dir> --to ideation --reason "审稿发现假设不可证伪"

# 4) 记录关键决策、人工签核、异常
python scripts/auto_research.py log <dir> --kind signoff --text "作者确认实验预算 ≤ 200 GPU-h"
```

推进规则：

- **一次只推进一个阶段**；不允许跳阶段（工具会拒绝 `--to` 越级）。
- 门禁失败时**先补证据**；确实要跳过必须 `advance --force --reason "..."`，工具会把 `FORCED:` 原因写进 `DECISIONS.md` 与 `state.json.history`。
- 每阶段结束时用 `check` 复核**已经走过的所有阶段**（防止后面改坏前面证据）。
- 进入 `final` 之前必须人工签核：`log <dir> --kind signoff --text "..."`；没有 `[signoff]` 记录 `advance` 会被拒绝，**且该检查不能用 `--force` 绕过**。
- 签核只能由用户明确授权后执行：agent 自行 `log --kind signoff` 视为违规。工具无法核验执行者身份，
  最终以 `DECISIONS.md` + git 提交历史做人工审计（见 docs/auto-research.md 的边界说明）。
- `advance` 会复核**所有已经走过的阶段**（不只当前阶段）：删掉早期 `IDEA.md`/证据后再推进会被拒绝。
- `init` 拒绝在已有 `state.json` 的项目上重新初始化，避免清空审计历史；需要新项目请换目录。
- 不要手工改 `state.json` 的 `phase`：状态历史的连续性校验会把它当作损坏（退出码 3）；回退请用 `revert`。

## 三、自动模式规则（agent 必须遵守）

**可以自动做**：在门禁通过且有证据的前提下，自动推进阶段、自动补写产物、自动跑工具/脚本（受 DSH 权限策略约束）。

**不可以自动做**：签署 `[signoff]`、替用户确认预算、替用户决定投稿、用 `--force` 掩盖缺失证据。

**必须停下等人工**：

1. 研究问题/假设/范围的实质变更；
2. 花钱或占用大算力之前（提交 `EXPERIMENT_PLAN.md` 给作者确认预算）；
3. 任何声称"实验成功/结论成立"之前，核对 `results/` 原始数据；
4. 投稿、对外发布、推送公开仓库；
5. 使用 `--force` 跳过门禁。

恢复工作时先 `status`，再从 `next` 指示的动作继续；不要重头再来，也不要覆盖已有证据。

## 四、与其它技能的协作

- 文献阶段用 `deep-research` / `research-lit`，引用核验交 `citation-management`（它的 `scripts/validate_citations.py`）。
- 实验阶段用 `experiment-plan` 出计划；跑参数搜索/指标循环用 `autoresearch`（改一处→机械验证→keep/revert）；结果汇总用 `analyze-results`。
- 写作阶段用 `academic-paper`（英文顶会）或 `research-writing-skill`（中文）；`scientific-writing` 做一致性与 reporting guideline 审计。
- 审稿阶段用 `academic-paper-reviewer`；想要独立视角就调用 DSH `subagent` 以"顶会领域主席 + 魔鬼代言人"角色写审稿意见，把结果写入 `REVIEW.md`。
- 定稿阶段用 `venue-templates` 对模板；Word/PDF 落盘用 `office-docx` / `office-export-pdf`。

## 五、反幻觉硬规则

1. **引用**：每条必须进 `evidence/citations.json` 并 `status=verified`、`id` 唯一；核验失败或不确定的条目删掉或标 `unverified`，绝不写进论文。
2. **数字**：论文/报告里的每个数字必须能指向 `results/` 里的原始文件或 `figures/` 的数据源；写进 `claim_map.json` 的 `evidence`（工具会检查路径真实存在），`paper_section` 必须对应论文真实章节。
3. **失败**：`RESULTS.md` 的 Deviations 必须如实记录失败运行、改过的设置、没跑的实验。
4. **AI 披露**：`PROVENANCE.md` 与投稿清单里写清 AI 参与范围；不要伪造"已复现"。

## 六、完成标准

- `check` 在 `final` 阶段 PASS，且 `state.json.project.phase == "final"`；
- `SUBMISSION_CHECKLIST.md` 无未勾选项，`PROVENANCE.md` 四节完整；
- `evidence/citations.json` 全部 verified、`claim_map.json` 每个 claim 有证据；
- 作者在 `DECISIONS.md` 完成最终签核（`log --kind signoff`），final 门禁会检查 `[signoff]`；
- 若中途回退过，`DECISIONS.md` 里能看到 `REVERT:` 记录与原因。
