# AUTO-RESEARCH · 项目说明

<!-- AUTO-RESEARCH: TODO -->

这是由 `auto_research.py init` 创建的自主科研项目。agent 按阶段推进，每个阶段有产物与门禁；
门禁不过就补证据，不允许编造。状态机在 `state.json`，决策记录在 `DECISIONS.md`。

## 阶段

| 阶段 | 产物 | 可用技能 |
|---|---|---|
| ideation | `IDEA.md` | research-lit / deep-research |
| literature | `LIT_REVIEW.md` + `evidence/citations.json` | deep-research / citation-management |
| experiment_plan | `EXPERIMENT_PLAN.md` | experiment-plan |
| experiments | `RESULTS.md` + `results/` | autoresearch / analyze-results |
| writing | `PAPER.md` + `evidence/claim_map.json` | academic-paper / scientific-writing |
| review | `REVIEW.md` + `REBUTTAL.md` | academic-paper-reviewer / subagent |
| final | `SUBMISSION_CHECKLIST.md` + `PROVENANCE.md` | venue-templates / citation-management |

## 常用命令

```bash
python auto_research.py status <dir>
python auto_research.py next <dir>
python auto_research.py check <dir>
python auto_research.py advance <dir> --by agent
python auto_research.py log <dir> --text "..." --kind decision
```

## 人工检查点（必须停下来确认）

- 选题/研究问题变更；
- 实验方案与算力预算（花钱之前）；
- 声称"实验成功"之前核对原始结果；
- 投稿/对外发布；
- 任何 `advance --force` 的跳过决定。
