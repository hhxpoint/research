# 使用指南

安装完成后，在 DSH 会话里直接用自然语言描述任务即可；需要更可控时，显式点名技能。
总入口是本仓库原创的 `research-stack`（不确定用哪个技能时先加载它）。

## 全流程入口：auto-research

如果要的是「从一个想法推进到可投稿」而不是单点任务，用 `auto-research` 状态机：

```
用 auto-research 在 D:\research\my-topic 建一个课题：
题目/问题/目标会议我写在命令里，你先只完成 ideation 阶段并等我确认。
```

它把四类技能串起来，并用代码门禁强制证据：引用必须核验、claim 必须映射证据、
审稿意见必须逐条回复、投稿清单必须勾完。详见 [auto-research.md](auto-research.md)。

## 四条推荐流水线

### A. 英文顶会 / 顶刊投稿

```
deep-research  →  experiment-plan  →  （跑实验）→  analyze-results
      →  venue-templates  →  academic-paper  →  academic-paper-reviewer
      →  academic-paper（revision）  →  citation-management  →  scientific-visualization
```

提示词示例：

```
用 deep-research 帮我做「构音障碍语音克隆」这个方向的系统文献地图，
输出 IDEA.md 和 RELATED_WORK.md（含每篇的贡献、方法、可质疑点）。

基于 IDEA.md 用 experiment-plan 出一份 claim-driven 的实验计划：
消融矩阵、评估协议（客观指标 + MOS）、运行顺序、算力预算。

实验结果在 results/ 下，用 analyze-results 汇总成对比表，
报 mean±std，标出显著性与可疑点，输出 RESULTS.md。

按 NeurIPS 模板（venue-templates）把 RESULTS.md 写成 8 页论文，
用 academic-paper 的 plan → outline → full 模式，正文引用的每篇文献都要能回溯。

用 academic-paper-reviewer 按顶会标准预审一轮，给我 reviewer report 和修改优先级。

用 citation-management 校验 references.bib 里每一条文献是否存在，输出可疑条目清单。
```

投出后收到审稿意见：

```
用 academic-paper 的 rebuttal-audit 模式处理这封审稿意见：
逐条判断"接受 / 部分接受 / 礼貌 push back"，给出回复草稿与需要补的实验。
```

### B. 中文期刊 / 组会 / 学位论文

```
用 research-lit 把近三年的相关工作按方法族整理成表格。

用 research-writing-skill 把这段中文摘要润色到期刊风格：
保留术语、公式、英文题名与实测数字，不要夸大结论。

用 scientific-visualization 把 results.csv 画成期刊级多面板图（色盲友好、300dpi、APS 尺寸），
再用 office-docx 把论文落盘为 Word。
```

### C. 系统综述 / PRISMA

```
用 deep-research 的 systematic review 模式做 protocol 草案（PROSPERO 风格）。

候选文献在 refs/（RIS/nbib），用 sr-screener 按纳排标准做双盲标题摘要筛选，
输出 PRISMA 2020 计数、排除原因分布与 kappa。

用 academic-paper 的 lit-review 模式把筛选结果写成综述初稿。
```

### D. 可度量的迭代优化

```
用 autoresearch 优化 train.py：Metric 是 val_bpb，Verify 是 5 分钟训练脚本，
预算 20 轮；每轮只改一处，先 commit 再验证，结果写 autoresearch/ 目录。
```

## 组合与边界

- **单阶段加载**：技能正文很长（ARS 的 writing 技能 60KB+），一次只加载当前阶段需要的技能，
  避免上下文膨胀；`research-stack` 负责告诉你加载哪个。
- **agent 数量是方法论**：ARS 的 13/12/7-agent 团队来自 Claude Code 实现，在 DSH 中表现为角色清单。
  需要独立评审视角时，用 DSH 的 `subagent` 工具另起一个"审稿人/魔鬼代言人"：
  ```
  用 subagent 以顶会领域主席的身份，只依据 paper/draft.md 写一份苛刻的审稿意见，
  按 novelty / methodology / evidence / clarity 打分并给出必须修改项。
  ```
- **引用与数字必须可回溯**：引用先过 `citation-management` 的校验脚本；实验数字注明来源文件/表格。
  不要接受技能编造 DOI、作者或年份——这是 AI 写论文最常见的事故。
- **图表**：`scientific-visualization` 产出图片与导出计划；需要 Word/PDF 时交给 `office-*` 技能，
  不需要额外装 pandoc/tectonic（若直接用 `academic-paper` 的 DOCX/PDF 输出模式，仍可能分别需要
  Pandoc / tectonic；走 `office-*` 技能则不需要）。
- **AI 使用声明**：投顶刊/顶会时按目标 venue 政策填写 AI 使用声明；`academic-paper` 的
  `disclosure` 模式可以帮你起草。

## 证据目录约定（建议）

```
notes/IDEA.md                研究问题、假设、贡献点
notes/RELATED_WORK.md        文献地图（含可质疑点）
notes/EXPERIMENT_PLAN.md     实验矩阵、协议、预算
results/                     原始结果（json/csv）
notes/RESULTS.md             汇总表与统计
evidence/citations.json      引用校验结果
paper/                       LaTeX / Markdown 成稿
figures/                     图表（png/svg/pdf）
```

## 常见问题

**Q：技能会不会自动执行脚本？**
不会自动执行。技能只是提示词；只有模型在你请求下用 `pwsh`/`python` 运行时，脚本才会执行。
高风险操作（联网、删除、发布）应保留人工确认。

**Q：ARS 可以商用吗？**
不可以。ARS 是 CC BY-NC 4.0。个人学术使用没问题；商业产品、付费服务、对外商业交付前必须获得
上游作者授权。可商用的替代组合：K-Dense（MIT）+ ARIS（MIT）+ zLanqing（MIT）。

**Q：想加自己的技能怎么办？**
放到 `skills/<name>/SKILL.md`，在 `tools/build_lock.py` 的 `SKILL_SPECS` 登记，重新生成锁文件即可。
详见 [maintenance.md](maintenance.md)。

**Q：升级 DSH 后技能会失效吗？**
技能是 Markdown + 标准 frontmatter，通常跨版本稳定。若 DSH 改了技能规范，按
[dsh-skill-spec.md](dsh-skill-spec.md) 复核 frontmatter，并运行 `python tools/dsh_skills.py selftest`。
