# 顶级论文写作 Agent Skills 调研报告（DSH 适配版）

- **调研日期**：2026-11-23（Asia/Shanghai）
- **调研范围**：学术写作、文献综述、引用管理、图表可视化、LaTeX/Word 排版、审稿与返修
- **方法**：`web_search` 找候选 → 用 `api.github.com` / `raw.githubusercontent.com` 逐个核实 stars、license、最近 push、技能清单、真实 SKILL.md frontmatter → 用 **DSH 自带 YAML 解析器实测** frontmatter 是否会被接受
- **重要说明**：GitHub 未认证 API 限额 60 次/小时，调研末期已耗尽（返回 403），后期改用 `raw.githubusercontent.com`（不计限额）与 HEAD 探测补齐。下文所有 stars/license/日期均为 2026-11-23 实测值；凡未逐字读正文的地方均已标注。

---

## 一句话结论

**最值得用的是 3 个：`Imbad0202/academic-research-skills`（ARS，投稿→审稿→返修闭环最完整，5 个技能实测全部通过 DSH frontmatter 校验）+ `K-Dense-AI/scientific-agent-skills`（MIT，177 技能里精选约 10 个写作/引用/图表/审稿，与已装 office 技能零重复）+ `zLanqing/codex-claude-academic-skills`（中文母语写作/润色/返修，frontmatter 干净到零改动）。** 审稿返修再叠加 `claesbackman/AI-research-feedback`；Nature 风格可补 `LeonChaoX/qinyan-academic-skills` 的 `qinyan-nature-*` 系列。**最大坑点**：ARS 是 **CC BY-NC 4.0（禁止商用）**，且其 Claude Code 专属的 subagents / slash commands / hooks 无法迁移到 DSH，装的时候必须把 repo 根的 `shared/` 合并进每个技能目录；`TingxiYu/academic-figure-skill` 的 frontmatter **有 YAML 语法错误，会被 DSH 静默丢弃**（实测）。

---

## 对比表

| 项目 | 链接 | stars | 最近更新 | license | 技能数量/形态 | 覆盖阶段 | 依赖 | DSH兼容性 | 推荐度 |
|---|---|---|---|---|---|---|---|---|---|
| **Imbad0202/academic-research-skills (ARS)** | [github](https://github.com/Imbad0202/academic-research-skills) | 58,199 | 2026-11-23 | **CC BY-NC 4.0**（API 显示 NOASSERTION） | 5 个技能目录（repo 根，各自带 `SKILL.md`；`academic-paper` 等含 `references/`） | 全生命周期：选题→文献→写作→诚信→审稿→返修→定稿 | Claude Code 插件机制；Pandoc(.docx)、tectonic(PDF) 可选；Node 18+；`ANTHROPIC_API_KEY`；Python 仅可选 | ✅ 5/5 frontmatter 实测通过；❌ agents/commands/hooks 不迁移 | ★★★★★ |
| **K-Dense-AI/scientific-agent-skills**<br>（原名 claude-scientific-skills） | [github](https://github.com/K-Dense-AI/scientific-agent-skills) | 58,173 | 2026-11-23 | **MIT** | 177 个技能（`skills/<kebab>/SKILL.md`），写作相关约 10–12 个 | 写作 / 文献综述 / 引用 / 图表 / 幻灯片 / 海报 / 审稿 / venue 模板 | 部分技能需网络或 API（`parallel-web`、`paper-lookup`、`pyzotero`）；核心写作类纯提示词 | ✅ 实测通过（`license`/`compatibility`/`metadata`/`allowed-tools` 均被容忍） | ★★★★★ |
| **zLanqing/codex-claude-academic-skills** | [github](https://github.com/zLanqing/codex-claude-academic-skills) | 6,203 | 2026-05-14（约 6 个月未更新） | **MIT** | 3 个中文技能（单文件自包含）+ 内嵌 21 个 K-Dense 参考技能（嵌套 3 层，DSH 扫不到） | 中文写作 / 润色 / 返修回应 / 学术 Office / 科学计算与期刊图表 | 纯提示词；scientific-toolkit 需 MATLAB/Python 环境 | ✅ frontmatter 只有 `name`+`description`，零归一化 | ★★★★☆ |
| **claesbackman/AI-research-feedback** | [github](https://github.com/claesbackman/AI-research-feedback) | 581 | 2026-11-19 | **MIT** | 12 个技能（`Skills/review-paper` 等） | 审稿（7-agent 预投稿 referee report）/ 返修 / 论文网站 / grant 评审 | Python（部分脚本）；`review-paper` 名义上 `allowed-tools` 限 Claude 工具 | ⚠️ 通过但 `disable-model-invocation: true` 被执行 → 不会自动触发，必须删该行 | ★★★★☆ |
| **LeonChaoX/qinyan-academic-skills** | [github](https://github.com/LeonChaoX/qinyan-academic-skills) | 1,061 | 2026-07-20 | **MIT** | 187 个 `SKILL.md`，17 个中文分类；含 `沁言学术skills/` 10 个 Nature 向技能 + `nsfc-proposal` | 检索 / 写作 / Nature 风格润色与审稿 / 图表 / 国家自然科学基金本子 | 部分需网络；沁言系列为厂商提示词 | ✅ 实测 `qinyan-nature-writing` 通过 | ★★★★☆ |
| **K-Dense-AI/claude-scientific-writer** | [github](https://github.com/K-Dense-AI/claude-scientific-writer) | 2,598 | 2026-11-11 | **MIT** | 26 个去重技能（`skills/`；另有 `.claude/skills/` 与 `scientific_writer/.claude/skills/` 两份重复副本，共 80 个 SKILL.md 路径） | 写作 / 引用 / 图表 / 幻灯片 / 海报 / Office 转换 | PyPI `scientific-writer`；`pip install "scientific-writer[office]"` | ✅ 通过，但 **`docx`/`pptx`/`xlsx`/`pdf` 四件套与已装 office 技能重复** | ★★★☆☆ |
| **HughYau/AcademicForge** | [github](https://github.com/HughYau/AcademicForge) | 2,668 | 2026-11-01 | NOASSERTION（自定义，需逐条看） | 33 个技能（`skills/claude-science/*`，Claude Science 包） | 文献综述 / `paper-narrative` / `figure-composer` / `figure-style` / 生物医药模型 | 部分需 GPU / API / 模型端点 | ⚠️ 未逐字验证 frontmatter；license 不明确降低可用性 | ★★★☆☆ |
| **lingzhi227/agent-research-skills** | [github](https://github.com/lingzhi227/agent-research-skills) | 476 | 2026-02-27（约 9 个月未更新） | **无 LICENSE** | 31 个技能，粒度最细：`paper-writing-section` / `related-work-writing` / `rebuttal-writing` / `latex-formatting` / `paper-compilation` / `self-review` | 选题 → 写作 → 编译 → 自审 → 返修 全覆盖 | 纯提示词 | ✅ `paper-writing-section`/`rebuttal-writing` 实测通过 | ★★★☆☆（无 license + 停更） |
| **anthropics/skills**（官方） | [github](https://github.com/anthropics/skills) | 199,224 | 2026-11-16 | **无 LICENSE 文件（API license=null，`/LICENSE` 404）** | 20 个技能，`skills/<name>/SKILL.md` | `docx`/`pptx`/`xlsx`/`pdf`（**DSH 已内置同类**）、`doc-coauthoring`、`canvas-design`、`theme-factory`、`skill-creator` | Python（office 类） | ✅ `docx` 实测通过；但与内置 office 技能功能重复 | ★★☆☆☆（对论文写作增量小） |
| **obra/superpowers** | [github](https://github.com/obra/superpowers) | 324,565 | 2026-11-03 | **MIT** | 15 个技能，**全部为软件工程方法论**（brainstorming / writing-plans / writing-skills / TDD / systematic-debugging…） | ❌ 不含任何学术写作技能；仅 `writing-plans`/`writing-skills` 属通用流程 | 无 | ✅ 通过 | ★☆☆☆☆（不是论文写作候选） |
| **O0000-code/awesome-academic-skills** | [github](https://github.com/O0000-code/awesome-academic-skills) | 73 | 2026-11-22 | **CC0-1.0** | **索引而非技能**：222 个技能 / 14 个分类，中英双语 | 全生命周期地图（检索→阅读→分析→写作→审稿→投稿） | — | —（只做选型参考） | ★★★★☆（选型工具） |
| **TingxiYu/academic-figure-skill** | [github](https://github.com/TingxiYu/academic-figure-skill) | 664 | 2026-07-12 | **Apache-2.0** | 1 个技能（Nature/Cell/Science 期刊级图表） | 图表设计/配色/导出（`references/color-palettes.md` 等） | Python（matplotlib） | ❌ **frontmatter YAML 解析失败，DSH 静默丢弃**（需修一行） | ★★☆☆☆（修好可用） |
| **SNL-UCSB/paper-writing-skill** | [github](https://github.com/SNL-UCSB/paper-writing-skill) | 254 | 2026-11-13 | **MIT** | 1 个技能（repo 根 `SKILL.md`，35.6 KB） | 分阶段写作 + 实验室 voice profile + 压缩/润色/cover letter/rebuttal | 纯提示词（针对 `.tex`/Overleaf） | ✅ 通过（注意 repo 根就是 SKILL.md，需改成目录形式） | ★★★☆☆（单实验室文风） |
| **aipoch/medical-research-skills** | [github](https://github.com/aipoch/medical-research-skills) | 2,083 | 2026-11-20 | **MIT** | 550+ 技能（仓库约 260 MB） | 仅医学/生物医学：protocol 设计、数据分析、证据洞察、学术写作 | 大量 Python/网络；含 MedSkillAudit 审计框架 | ⚠️ 未逐字验证；体量过大不宜整体装入 | ★★☆☆☆（非医学场景不适用） |

> 说明：`stars` 为 2026-11-23 的 GitHub API 返回值。注意 `K-Dense-AI/claude-scientific-skills` **已改名**为 `scientific-agent-skills`（旧 URL 会 301 重定向）；ARS 的 36kr 报道（2026-05-17）当时是 6.4k stars、4 个技能，现已 58.2k stars、**5 个技能**（`sr-screener` 未见于该文描述，应系其后新增）。

---

## 详细点评

### 1. Imbad0202/academic-research-skills（ARS）——最完整的论文流水线

- **这就是 36kr 那篇文章所指的仓库**（[36kr 英文版](https://eu.36kr.com/en/p/3812800346742274) 原文写的是 6.4k stars 的 `academic-research-skills`）。实测 2026-11-23：**58,199 stars / 4,437 forks / 创建 2026-02-26 / 最近 push 2026-11-23（当天仍在更新）/ 语言 Python / 默认分支 main**。
- **技能形态不是 `.claude/skills/`，而是 repo 根下 5 个同名目录**：`academic-paper`、`academic-paper-reviewer`、`academic-pipeline`、`deep-research`、`sr-screener`，每个目录内自带 `SKILL.md`（`academic-paper` 另含 `references/`）。另有 `agents/`、`commands/`、`hooks/`、`shared/`、`scripts/`、`tools/`、`.claude-plugin/marketplace.json`（均已 HEAD 探测为 200 存在）——**官方安装方式是 Claude Code 插件**：`/plugin marketplace add Imbad0202/academic-research-skills` + `/plugin install academic-research-skills`（v3.7.0+）。
- **体量与质量信号**：`academic-paper/SKILL.md` 达 **69,635 字节**，frontmatter 自述 **11 种模式**（full/plan/outline/revision/revision-coach/abstract/lit-review/format-convert/citation-check/disclosure/**rebuttal-audit**）、6 种论文类型、5 种引用格式、双语摘要、Style Calibration（从你过去 3 篇论文学写作声线）。`academic-pipeline` 是 10 阶段编排器，Stage 2.5 / 4.5 设**不可跳过的诚信闸门**（7 项 AI 失败模式检查，README 称源自 2026 年 Nature 的自主科研失败模式研究）。
- **防幻觉引用**：README 与 36kr 均称用 Semantic Scholar API 做存在性确认，并用 **Levenshtein 相似度 ≥ 0.70** 阈值做模糊匹配；v3.11 又加了"确定性四索引引用闸门"。⚠️ README 自述"实测抓到 15 条伪造引用 + 3 处统计错误"属**自述数据，我未独立验证**。
- **DSH 适配成本**：5 个 SKILL.md 的 frontmatter **全部实测通过**（`name` kebab-case、`description` 783–1021 字符带引号、`metadata` 嵌套对象被 DSH 保留）。但代价有两处：① 正文用相对路径引用 `shared/style_calibration_protocol.md`、`references/writing_quality_check.md`、`shared/references/routing_core.md` 等，**必须把这些文件一并搬进技能目录**；② `agents/`、`commands/`、`hooks/`、`AskUserQuestion` 属 Claude Code 专属，**不会迁移**——README 自己也承认"导入的 skill 承载 ARS 方法论；Claude Code 专属机制不会转移"。
- **依赖**：docs/SETUP.md 明确"核心技能（研究/写作/评审）**不需要 Python**，是提示词驱动"；`Pandoc` 只用于直接生成 `.docx`，`tectonic` 只用于 PDF（都可选）；Node 18+；需 `ANTHROPIC_API_KEY`（这是 Claude Code 的事，DSH 用自己的模型即可）。**平台支持：macOS/Linux 是测试平台，Windows 属 best-effort**（脚本用 `msvcrt` 后端、无 Windows CI）。
- **license 是最大限制**：`LICENSE` 文件实测为 **CC BY-NC 4.0**（Copyright (c) 2026 Cheng-I Wu，署名-非商业性使用）。个人科研使用没问题，**任何商业/团队对外交付用途需先确认授权**。

### 2. K-Dense-AI/scientific-agent-skills ——最宽松许可下的最大弹药库

- 任务里给的 `claude-scientific-skills` **已改名为 `scientific-agent-skills`**。实测：**58,173 stars / 5,097 forks / MIT / 最近 push 2026-11-23 / 98 个 open issues / 仓库 homepage 指向 arXiv 2609.00065**，自述"177 ready-to-use validated skills plus 100+ scientific databases，250,000+ 科学家在用"。
- **`skills/` 下恰好 177 个技能目录**（用 API 精确计数，不是估的）。写作相关精选：`scientific-writing`、`literature-review`、`citation-management`、`peer-review`、`scientific-visualization`、`scientific-schematics`、`scientific-slides`、`latex-posters`、`pptx-posters`、`venue-templates`、`research-grants`、`scholar-evaluation`、`scientific-critical-thinking`、`markdown-mermaid-writing`、`infographics`，以及检索类 `paper-lookup` / `research-lookup` / `bgpt-paper-search` / `paperzilla` / `pyzotero`。
- **工程纪律明显**：仓库自带 CI —— `.github/workflows/skill-spec-validation.yml`、`skill-tests.yml`、`security-scan.yml`、`pr-skill-scan.yml`，以及 `docs/skill-guides/*.md`（每个技能一份约 4.5 KB 指南）。
- **DSH 兼容性最好的一档**：`scientific-writing` 的 frontmatter 是 `name / description / license / compatibility / metadata{version,last-reviewed,skill-author}`，我**用 DSH 自带 yaml 解析器实测 ACCEPTED**；`citation-management`、`literature-review` 还带 `allowed-tools`（被 DSH 静默忽略，无副作用）。`scientific-writing` 正文 14.9 KB，强调 evidence provenance、reporting guideline 覆盖、作者责任、保密控制。
- **关键互补点**：**这 177 个技能里没有 `docx`/`pptx`/`xlsx`/`pdf`** —— 正好避开与 DSH 已装 office 技能的重复，定位是"写与画"，落盘交给 office 技能。

### 3. zLanqing/codex-claude-academic-skills ——中文科研用户的最短路径

- 实测 **6,203 stars / 321 forks / MIT / 最近 push 2026-05-14**（约 6 个月未更新，是本清单里新鲜度较差的一个）。作者定位明确：三个技能专为中文科研用户设计，Claude Code 与 Codex 双端可调。
- 三个顶层技能：`office-academic-skill`（论文阅读报告 + 学术 PPT/Word 生成）、`research-writing-skill`（**中文母语**的论文写作/润色/分节起草/**rebuttal 与审稿回应**/学位论文行文/论证规划，明确"保留公式、英文题名、术语、引用与实测数值"）、`scientific-toolkit-skill`（MATLAB/Python 科学计算 + 期刊级图表）。
- **最省事的 DSH 迁移**：两个关键 `SKILL.md` 的 frontmatter **只有 `name` + `description`**，实测直接通过，**零归一化**；`research-writing-skill` 只有 4,227 字节，自包含无外部引用（探测过它没有 `references/` 目录）。
- **两个坑**：① `scientific-toolkit-skill/references/scientific-skills/` 下**内嵌了 21 个来自 K-Dense + anthropics 的技能副本，嵌套 3 层** —— DSH 只扫一层，所以既不会被发现（避免命名冲突，好事），也意味着**别把它展平**，否则 `docx`/`pptx`/`xlsx`/`pdf` 会与已装 office 技能撞名；② 这些内嵌副本会随上游漂移，且 provenance 混合（K-Dense 是 MIT，anthropics 的 office 四件套无 LICENSE）。
- 适合场景：**中文投稿、中文润色、中文返修信**；英文顶刊还是用 ARS / K-Dense。

### 4. claesbackman/AI-research-feedback ——审稿与返修的最佳单点

- 实测 **581 stars / 108 forks / MIT / 最近 push 2026-11-19**（很新鲜）。作者 Claes Bäckman（经济学），12 个技能全在 `Skills/` 下：`review-paper`（**7-agent 预投稿 referee report + 复核轮，剔除错误与边缘意见**）、`review-paper-light`、`review-paper-checks`、`review-paper-code`、`review-grant`、`review-pap`、`explain-diff`、`explorable-beamer`、`explorable-deck`、`paper-version`、`paper-website`、`pdf-to-markdown`。
- `review-paper/SKILL.md` 43,883 字节，frontmatter 带 `argument-hint`、`allowed-tools: Read, Write, Edit, Glob, Grep, Bash, Agent`、**`disable-model-invocation: true`**。
- **DSH 上的关键细节**：该文件**能通过解析**，但 `disable-model-invocation: true` 在 DSH 里是**被真正执行的**——技能会变成"只能用户显式调用、模型不会自动选中"。想让它参与自动选型，**必须删掉这一行**（我读过 loader 源码确认：`modelInvocable = disableModelInvocation !== true`）。
- 性价比最高的组合：**K-Dense 写 + claesbackman 审 + ARS 做返修流水线**。

### 5. LeonChaoX/qinyan-academic-skills ——顶刊风格与中文基金本子

- 实测 **1,061 stars / MIT / 最近 push 2026-07-20 / 187 个 SKILL.md**。组织方式很"中文科研"：17 个编号中文分类（`01-论文检索与文献管理` … `17-平台与基础设施`），另有一组 `沁言学术skills/` 10 个技能：`qinyan-nature-writing`、`qinyan-nature-polishing`、`qinyan-nature-review`、`qinyan-nature-figures`、`qinyan-nature-statistics`、`qinyan-citation`、`qinyan-paper-polish`、`qinyan-paper-analysis`、`qinyan-paper-search`、`qinyan-topic-analysis`。
- **这是清单里唯一直接对标 Nature 系"写作 + 润色 + 审稿 + 图表 + 统计"的一整套**，并额外提供 `nsfc-proposal` / `nssfc-proposal`（国家自然科学基金 / 国社科）——对国内课题组实用性很高。
- 实测 `qinyan-nature-writing` 的 frontmatter 只有 `name`+`description`（290 字符），DSH 直接通过。
- **须注意**：这批 `沁言学术skills` 实质是商业产品"沁言学术"的提示词库以 MIT 形式再分发，**许可证与内容所有权存在张力**；且分类目录名含中文与数字前缀（`01-论文检索与文献管理`），**目录名不参与 DSH 校验**（`name` 只看 frontmatter），但建议仍改成纯 kebab 目录名以便维护。
- 该仓库另含大量生物信息/化学/临床技能（与 K-Dense 高度重叠），**只取 `02-科学写作与学术交流`、`03-学术演示与可视化`、`沁言学术skills` 三块即可**。

### 6. K-Dense-AI/claude-scientific-writer ——好工具，但对 DSH 有重复

- 实测 **2,598 stars / 302 forks / MIT / 最近 push 2026-11-11**。它不只是技能包，而是**三合一产品**：PyPI 包 `scientific-writer`（`pip install scientific-writer`，另有 `[analysis]`、`[office]` extra）、Claude Code 插件、原生 CLI（`scientific-writer --effort high`）。
- 技能树实测 **80 个 `SKILL.md` 路径，但只有 26 个唯一技能**——因为 `skills/`、`.claude/skills/`、`scientific_writer/.claude/skills/` 是**三份重复副本**，另有 `skill-overrides/{pdf,xlsx}`。迁移时**只能取 `skills/` 这一份**，否则同一技能会出现三个同名副本互相覆盖。
- 26 个技能里含 **`docx`、`pptx`、`xlsx`、`pdf`** —— 与 DSH 已装 office 四件套**直接重复**，属净负担。
- 剩下的写作/引用/图表技能（`scientific-writing`、`literature-review`、`citation-management`、`peer-review`、`scientific-slides`、`latex-posters`、`venue-templates`、`scholar-evaluation`…）与 `scientific-agent-skills` 里的同名技能**基本同源**。**结论：装了 K-Dense 大库就不必再装它**；只有需要 PyPI CLI 做本地批量转换时才单独 `pip install`。

### 7. obra/superpowers（324,565 stars）——明确不是论文写作候选

- 实测 **324,565 stars / 28,798 forks / MIT / 最近 push 2026-11-03**，但 15 个技能**全部是软件工程方法论**：`brainstorming`、`writing-plans`、`writing-skills`、`executing-plans`、`test-driven-development`、`systematic-debugging`、`subagent-driven-development`、`requesting-code-review`、`verification-before-completion` 等。
- **没有任何学术写作、文献、引用、排版、审稿技能**。名字里的 "writing" 指的是"写计划/写技能"，不是"写论文"。唯一可借的是 `writing-plans` 的规划纪律，与论文写作只有间接关系。
- 列在这里是为了**排除**：它 star 数最高，最容易被误选。

### 8. anthropics/skills（199,224 stars）——官方但增量有限

- 实测 **199,224 stars / 23,318 forks / 最近 push 2026-11-16**，**GitHub API `license=null`，`/LICENSE` 实测 404**（无 license 文件），但个别 `SKILL.md` frontmatter 自带 `license` 字段（如 `docx`）。
- 20 个技能：`docx`、`pptx`、`xlsx`、`pdf`（**DSH 已内置 `office-docx`/`office-pptx`/`office-xlsx`/`office-export-pdf`，同源重复**）、`doc-coauthoring`、`academy-guide`、`canvas-design`、`theme-factory`、`brand-guidelines`、`skill-creator`、`mcp-builder` 等。
- 对"论文写作"真正有用的只有 `doc-coauthoring`（文档协作写作流程）和 `canvas-design`/`theme-factory`（版式与主题，可用于海报/封面）。**其余价值在于 `skill-creator` 作为写技能的方法论参考**，而非内容资产。
- **无 LICENSE 这一条值得单独标红**：可用于个人本地，但再分发进团队/产品的合规性不明。

### 9. HughYau/AcademicForge ——偏生物医药的合集

- 实测 **2,668 stars / 156 forks / 最近 push 2026-11-01 / 默认分支 `site-first`**（不是 `main`，克隆时注意）/ license 为 NOASSERTION（自定义，需逐条确认）。
- 33 个技能在 `skills/claude-science/` 与 `skills/` 下：`literature-review`、`paper-narrative`（叙事线构建）、`figure-composer`、`figure-style`、`pdf-explore`、`indication-dossier`、`scientific-visualization`，其余大量是 `alphafold2`/`boltz`/`chai1`/`esmfold2`/`proteinmpnn` 等结构生物学模型技能。
- **只有 `paper-narrative`、`figure-composer`、`figure-style` 三个对通用顶刊写作有独立价值**，其余是生物医药专用。license 不明 + 含 GPU/API 依赖，优先级放低。

### 10. lingzhi227/agent-research-skills ——粒度最细，但无 license 且停更

- 实测 **476 stars / 49 forks / 最近 push 2026-02-27（约 9 个月未更新）/ 无 LICENSE（API `license=null`）**。
- 31 个技能按论文写作的真实颗粒度切开：`paper-writing-section`（Abstract/Intro/Methods/Results/Discussion 分节，两轮 refinement）、`related-work-writing`、`rebuttal-writing`、`citation-management`、`latex-formatting`、`paper-compilation`、`paper-assembly`、`paper-revision`、`self-review`、`figure-generation`、`table-generation`、`slide-generation`、`literature-review`、`literature-search`、`deep-research`、`survey-generation`、`novelty-assessment`。
- **形态极简**：单文件 2,366 字节（`paper-writing-section`），frontmatter `name`+`description`+`argument-hint`，实测通过 DSH。
- **但它是最"骨架"的一档**：字节数小意味着指令密度低，实操深度远不如 ARS 的 69 KB 或 K-Dense 的 14.9 KB。**无 license 是硬伤**，只能当方法论参考读物。

### 11. 其余候选

- **O0000-code/awesome-academic-skills（73★, CC0, 2026-11-22）**：**不是技能包，是索引**——222 个技能 / 14 个分类 / 中英双语，按科研生命周期编排（Discover & Collect → Read & Understand → Analyze & Visualize → Write & Refine → Review & Publish → Suites），每条标注 license 与运行时（network/hooks）。这是**选型的第一入口**，装不装技能都建议先读它。
- **TingxiYu/academic-figure-skill（664★, Apache-2.0, 2026-07-12）**：Nature/Cell/Science 期刊级图表，设计原则写得很到位（"一图一结论""克制配色>丰富配色""为印刷而非屏幕设计"），正文 27.9 KB。**但 frontmatter 有致命 YAML 错误**：`description` 未加引号却含 `DO NOT trigger for: interactive dashboards...` 这样的 `": "` 序列，用 DSH 自带 yaml 实测报 `Nested mappings are not allowed in compact mappings at line 2` → **技能被静默丢弃**。改一行即可用（见下节）。
- **SNL-UCSB/paper-writing-skill（254★, MIT, 2026-11-13）**：单技能 35.6 KB，强制一套实验室编辑原则 + 可定制 voice profile + 分阶段写作工作流，触发器写得很激进（任何 `.tex`/Overleaf/投稿/润色/压缩/rebuttal/cover letter 都会触发）。**质量高但"单一实验室文风"**，适合当模板改造，不适合直接用。
- **aipoch/medical-research-skills（2,083★, MIT, 2026-11-20）**：550+ 医学技能、仓库约 260 MB、有 MedSkillAudit 审计框架，四项核心是证据洞察/方案设计/数据分析/学术写作。**非医学场景不适用**，体量也不适合整体装入 DSH 技能目录。

---

## DSH 兼容性：实测规则（不是猜的）

用两种证据交叉确认：① 从 `app.asar` 抽出 DSH 的**技能加载器源码**（`@deepseek-ai/dsh-skill-filesystem/lib/index.js` 与 `@deepseek-ai/dsh-skill/lib/index.js`）实际阅读；② 抽出 DSH **自带的 `yaml` 包**，对 19 个真实 `SKILL.md` 的 frontmatter 逐个跑了一遍。

### 装载位置与目录深度（关键！）

DSH 会扫描这几个根（源码 `roots()`）：

| 根 | 说明 |
|---|---|
| `<项目根>/.dsh/skills` | 项目级 |
| `<项目根>/.agents/skills` | 项目级（跨 agent 通用） |
| **`$DSH_HOME/skills`（即 `~/.dsh/skills`）** | **用户级，本报告推荐位置**；该根下 `.system` 目录会被跳过 |
| `<agentsHome>/skills` | 另一用户级根 |
| 自定义 `customSkillDirs` | 配置项 |

**只扫描一层**，形态仅两种：

```
~/.dsh/skills/<dir>/SKILL.md     ← 目录形式（推荐）
~/.dsh/skills/<file>.md          ← 扁平文件形式（也认）
```

源码里 `discoverRoot()` 只 `readdir` 一层，对 directory 取 `<dir>/SKILL.md`、对 file 取 `*.md`，**不会递归**。所以 K-Dense 的 `skills/<name>/SKILL.md` 复制进 `~/.dsh/skills/` 后正好是一层，**可以直接用**；而 zLanqing 那种 `scientific-toolkit-skill/references/scientific-skills/<name>/SKILL.md`（三层）**永远扫不到**。

### frontmatter 校验：哪些字段必填、哪些会被容忍

从 `parseSkillFile()` 逐行确认：

1. 文件第一行必须**恰好**是 `---`（允许行尾 `\r`），之后到下一个独立 `---` 行为 frontmatter，YAML 必须是**对象**。
2. **必填**：`name`（非空字符串）与 `description`（非空字符串）。缺任何一个 → 技能被**静默忽略**（只打一条 warn 日志，不影响会话）。
3. **`name` 必须匹配 `^[a-z0-9]+(?:-[a-z0-9]+)*$`** —— 即小写 kebab-case，字母数字与连字符。`paper_writing`（下划线）实测被判非法并丢弃。
4. **额外字段是"容忍但忽略"**：解析后只读取 `name`、`description`、`whenToUse`、`metadata`、`disable-model-invocation`、`user-invocable`，**其余键（`license`、`compatibility`、`allowed-tools`、`argument-hint`、`version`…）既不报错也不生效**。实测 `K-Dense citation-management`（含 `allowed-tools`）、`claesbackman review-paper`（含 `allowed-tools`+`argument-hint`）、`anthropics docx`（含 `license`）全部 ACCEPTED —— **`allowed-tools` 在 DSH 里没有任何作用**（全 app 的 js 里都搜不到这个字面量）。
5. **会被直接丢弃（致命）的 4 类**：
   - YAML 语法错误 → `TingxiYu/academic-figure-skill` 实测命中；
   - `name` 缺失/为空/不匹配 kebab 正则；
   - `description` 缺失/为空；
   - 使用**驼峰**写法的调用策略键 `disableModelInvocation` / `modelInvocable` / `userInvocable` → 源码 `rejectLegacyInvocationKey()` **显式抛错**并要求改用 kebab-case（`disable-model-invocation` / `user-invocable`）。
6. **`disable-model-invocation: true` 会被执行**：DSH 把 `modelInvocable` 置为 false，该技能**不会参与模型自动选型**，只能用户显式调用。布尔值接受 `true/false/1/0/yes/no/on/off`。

### 与 Claude Code 技能的差异（必须知道的边界）

`~/.dsh/skills/<name>/SKILL.md` 只是"提示词包"。以下 Claude Code 资产**在 DSH 里没有对应物，不算技能**：

| Claude Code 资产 | 在 DSH 里的处境 |
|---|---|
| `.claude-plugin/marketplace.json`、`/plugin install` | ❌ 不适用，只能手工复制文件 |
| `agents/`（subagent 定义，如 ARS 的 13/12/7 agent 团队） | ❌ 不迁移；DSH 有 `subagent` 工具但没有同名 agent 注册表 |
| `commands/`（slash commands，如 `/ars-plan`） | ❌ 不迁移 |
| `hooks/`（`PreToolUse` 写范围守卫、`hooks.json`） | ❌ 不迁移 |
| `allowed-tools` frontmatter | ⚠️ 语法合法但**被忽略**，工具权限由 DSH 自身策略管 |
| `AskUserQuestion` 工具引用 | ❌ DSH 对应的是 `ask_user_question`，正文需改写 |
| 正文里的 `Read`/`Write`/`Edit`/`Bash`/`Task` 工具名 | ⚠️ 需映射为 DSH 的 `read`/`write`/`edit`/`pwsh`/`subagent` |

**好消息**：技能目录内的**相对路径资源是可用的**——加载器把 `resourceBase` 设为技能所在目录（`locator.directory`），所以 `references/xxx.md`、`scripts/xxx.py` 这类引用照常可读。这就是为什么 ARS 的 `shared/` 必须搬进每个技能目录。

---

## 推荐安装清单

> 目标位置统一为 `~/.dsh/skills/`（即 `$DSH_HOME/skills`）。下面每一条都是"复制某个子目录"，不改动任何源仓库。

### 第一梯队（必装）

| # | 来源 | 复制哪些子目录 | frontmatter 归一化 |
|---|---|---|---|
| 1 | `Imbad0202/academic-research-skills` | `academic-paper/`、`academic-paper-reviewer/`、`academic-pipeline/`、`deep-research/`、`sr-screener/`（5 个）**＋ 把 repo 根的 `shared/` 合并复制进上述每一个技能目录内** | 0 处必改（实测通过）。可选精简：删 `metadata.status`/`data_access_level`（无害）。**不要**加 `allowed-tools`；**不要**加 `disable-model-invocation`（否则不自动触发） |
| 2 | `K-Dense-AI/scientific-agent-skills` | 只取 `skills/` 下：`scientific-writing`、`literature-review`、`citation-management`、`peer-review`、`scientific-visualization`、`scientific-schematics`、`scientific-slides`、`latex-posters`、`venue-templates`、`scholar-evaluation`、`scientific-critical-thinking`、`markdown-mermaid-writing`（约 12 个） | 0 处必改。可选：删 `license`/`compatibility`/`allowed-tools`（全被忽略，删只为洁癖）；保留 `metadata` 无害 |
| 3 | `zLanqing/codex-claude-academic-skills` | `research-writing-skill/`（必需）、`office-academic-skill/`（中文论文阅读报告，**与 office 技能部分重叠，可选**）；**不要复制** `scientific-toolkit-skill/references/`（嵌套 3 层，DSH 扫不到且会造成 `docx`/`pptx`/`xlsx`/`pdf` 撞名） | 0 处必改（只有 `name`+`description`） |

### 第二梯队（按需）

| # | 来源 | 复制哪些 | 归一化 |
|---|---|---|---|
| 4 | `claesbackman/AI-research-feedback` | `Skills/review-paper/`、`Skills/review-paper-checks/`、`Skills/review-paper-light/`、`Skills/paper-version/`、`Skills/pdf-to-markdown/` | **必改**：删除 `disable-model-invocation: true`（否则 DSH 不会自动选它）；`allowed-tools` 可留可删（无效）；正文 `Read/Write/Bash/Task` 建议映射为 DSH 工具名 |
| 5 | `LeonChaoX/qinyan-academic-skills` | `skills/沁言学术skills/` 下 `qinyan-nature-writing`、`qinyan-nature-polishing`、`qinyan-nature-review`、`qinyan-nature-figures`、`qinyan-citation`；`skills/02-科学写作与学术交流/` 下 `scientific-writing`、`peer-review`、`research-proposal`、`venue-templates`；需要本子时再加 `04-研究方法与科学思维/nsfc-proposal`、`nssfc-proposal` | 0 处必改（实测 `qinyan-nature-writing` 通过）。建议把中文目录名改为 kebab（如 `qinyan/`），纯为维护方便（不影响校验） |
| 6 | `TingxiYu/academic-figure-skill` | 整个仓库当 1 个技能（目录形式） | **必改 1 行**：`description` 加双引号包起来（内部 `"` 转义），或把 `DO NOT trigger for: ` 改成 `DO NOT trigger for — `。**不改则 DSH 静默丢弃（实测）** |
| 7 | `SNL-UCSB/paper-writing-skill` | 建目录 `paper-writing/`，把 repo 根的 `SKILL.md` 放进去 | 0 处必改（frontmatter 只有 `name`+`description`）。建议把 `name: paper-writing` 与目录名对齐 |

### 明确不建议装

- **`anthropics/skills` 的 `docx`/`pptx`/`xlsx`/`pdf`**：DSH 已有 `office-docx`/`office-pptx`/`office-xlsx`/`office-export-pdf`/`office-render`/`office-recalculate`，**同源重复**；且该 repo 无 LICENSE。
- **`K-Dense-AI/claude-scientific-writer` 的 office 四件套与重复技能**：与上同理，且与 `scientific-agent-skills` 同源；只有需要 PyPI CLI 时才 `pip install scientific-writer`。
- **`lingzhi227/agent-research-skills` 整体**：无 LICENSE + 停更 9 个月；可当文档阅读，不建议装入。
- **`aipoch/medical-research-skills` 整体**：260 MB、550+ 医学技能，非医学场景纯负担。
- **`obra/superpowers`**：与论文写作无关。

### 归一化通用检查表（照着做）

```
1. 目录放进 ~/.dsh/skills/<name>/SKILL.md（一层，别嵌套）
2. 第一行必须是 --- ，紧接着 frontmatter，再一行 ---
3. name 用小写 kebab-case：^[a-z0-9]+(-[a-z0-9]+)*$
4. description 非空；若含 ": " 必须整段加双引号（这是最常见的静默失败）
5. 删除驼峰调用键 disableModelInvocation / modelInvocable / userInvocable（会抛错）
6. 想被自动选中就别留 disable-model-invocation: true
7. 其余字段（license/compatibility/allowed-tools/argument-hint/version）可留，但都无效
8. 技能正文引用的 references/ scripts/ shared/ 必须落在该技能目录内
9. 中文目录名可用，但建议改 kebab；.system 目录会被跳过
```

---

## 与已装 office 技能的关系（互补而非重复）

DSH 当前已装：`office`、`office-docx`、`office-pptx`、`office-xlsx`、`office-export-pdf`、`office-render`、`office-recalculate`（来自 `@deepseek-ai/dsh-skill-office`，实测其 `SKILL.md` frontmatter 都是极简的 `name`+`description`）。

**结论：本报告推荐的三件套与 office 技能是"生成 → 落盘"的正交关系，只有 3 处需要避开。**

| 来源 | 重叠项 | 处理 |
|---|---|---|
| `anthropics/skills` | `docx`、`pptx`、`xlsx`、`pdf` | ❌ 不装（已被 office-* 覆盖） |
| `claude-scientific-writer` | `docx`、`pptx`、`xlsx`、`pdf` | ❌ 不装 |
| `zLanqing/.../scientific-toolkit-skill/references/scientific-skills/` | 内嵌 `docx`、`pptx`、`xlsx`、`pdf` | ❌ 别展平（嵌套 3 层本就扫不到） |
| **ARS** | 无 | ✅ 它产出 Markdown/LaTeX，DOCX/PDF 靠 Pandoc/tectonic；**在 DSH 里可以让它只出 Markdown/LaTeX，再由 `office-docx` + `office-export-pdf` 落盘**，比装 Pandoc/tectonic 更省 |
| **K-Dense（177 个）** | **无任何 docx/pptx/xlsx/pdf** | ✅ 完美互补：它负责"写/画"，office 负责"出文件" |
| **qinyan / academic-figure-skill** | 无 | ✅ 图表出 PNG/SVG/PDF，再用 `office-render` 检查版式 |

---

## 特别关注项核查结果

| 关注点 | 谁具备 | 证据强度 |
|---|---|---|
| **真实引用校验（防幻觉引用）** | **ARS 最强**：Semantic Scholar API 存在性确认 + Levenshtein ≥0.70 模糊匹配；v3.11 "确定性四索引引用闸门"；`academic-paper` 有 `citation-check` 模式；`citation-management`（K-Dense）偏格式管理而非在线校验 | ARS 机制来自 README/docs 描述 + 36kr 报道，**我未运行验证**；"抓到 15 条伪造引用"是仓库自述 |
| **诚信闸门 / 失败模式清单** | **ARS**：Stage 2.5 / 4.5 两道不可跳过硬闸门，7 项 AI 失败模式检查；`repro_lock` 记录运行配置并声明"LLM 输出非字节级可复现" | 同上，机制层面可信，效果未独立验证 |
| **顶刊/顶会写作风格** | `qinyan-nature-writing/polishing`（Nature 系）、`academic-figure-skill`（Nature/Cell/Science 图表）、K-Dense `venue-templates`（期刊/会议模板）、ARS 6 种 paper type + 5 种引用格式（APA 7 / IEEE…） | frontmatter 与正文摘要均已读 |
| **rebuttal / reviewer response** | **ARS** `academic-paper` 的 `rebuttal-audit` 模式（含"该不该 push back"判断）+ `academic-paper-reviewer`；**claesbackman** `review-paper` 7-agent referee + 复核轮；`zLanqing research-writing-skill`（中文返修信）；`lingzhi227 rebuttal-writing` | ARS 模式清单来自其 SKILL.md/description；claesbackman 已读 frontmatter 与描述 |
| **图表（期刊级）** | K-Dense `scientific-visualization`/`scientific-schematics`/`latex-posters`/`pptx-posters`；`academic-figure-skill`（需修 frontmatter）；ARS `visualization_agent`（matplotlib/seaborn/ggplot2 + 色盲友好 + APA 7.0） | 均已核实存在 |
| **LaTeX / Word 排版** | K-Dense `latex-posters`、`venue-templates`；`lingzhi227 latex-formatting`/`paper-compilation`；ARS 输出 LaTeX 并可编译 PDF；DOCX 走 Pandoc 或 **DSH 的 `office-docx`** | — |
| **中文优先** | `zLanqing research-writing-skill`（中文母语写作/润色/返修）、`qinyan-*`（中文 + Nature 风格 + 基金本子） | frontmatter description 明写 |

---

## 风险与坑点（按严重度）

1. **license 风险（最高）**：ARS 是 **CC BY-NC 4.0 → 禁止商业使用**，而它恰恰是最强的那个。商用/对外交付前必须确认授权，或退回到 MIT 的 K-Dense + zLanqing + claesbackman 组合。`lingzhi227`（无 license）、`anthropics/skills`（无 LICENSE 文件）、`AcademicForge`（NOASSERTION）同样需谨慎。
2. **frontmatter 静默失败**：DSH 对不合格技能**只打 warn 日志、不报错**，表现为"技能没出现"。最常见原因是 `description` 里未加引号的 `": "`（`TingxiYu` 已实测中招）。装完请检查技能是否出现在目录里。
3. **目录深度陷阱**：只扫一层。`skills/a/b/SKILL.md` 一律无效；`<root>/<file>.md` 这种扁平文件反而合法（但 `resourceBase` 会变成根目录，相对引用易错）。
4. **`disable-model-invocation: true`**：Claude Code 里是"防误触发"的好习惯，到 DSH 会变成"永远不自动触发"。审稿类技能（claesbackman）必须删。
5. **Claude 生态资产不迁移**：ARS 的价值有相当一部分在 13/12/7 个 agent 的编排与 slash commands 上，这些在 DSH 里**不存在**。只搬 5 个 `SKILL.md` 会拿到"方法论与清单"，拿不到"自动编排"。若真需要，得用 DSH 的 `subagent`/`workflow` 自己重建编排层。
6. **`shared/` 路径断裂**：ARS 的 `SKILL.md` 内部引用 `shared/...`，不合并进技能目录会出现"指向不存在的文件"的指令（模型会读不到而编造）。
7. **重复副本导致互相覆盖**：`claude-scientific-writer` 有 3 份同名技能树（80 个 SKILL.md 路径 / 26 个唯一技能），只能取 `skills/`。
8. **上游漂移**：`zLanqing` 内嵌 21 个 K-Dense 技能副本已 6 个月未同步；`claude-scientific-skills` 改名后旧链接 301。
9. **Windows 支持**：ARS 的 SETUP.md 明确"macOS/Linux 是测试平台，Windows best-effort"；其 hooks 依赖 `bash`/Git Bash。**不过只要不迁 hooks，纯 SKILL.md 在 DSH+Windows 上无此问题。**
10. **API 限流**：GitHub 未认证 API 60 次/小时，本调研末期触发 403（已在方法说明中记录），后续用 raw + HEAD 补齐。

---

## 引用 URL 列表（访问日期均为 2026-11-23）

### 候选仓库
1. https://github.com/Imbad0202/academic-research-skills — ARS 主仓库
2. https://api.github.com/repos/Imbad0202/academic-research-skills — stars/license/pushed_at 实测
3. https://github.com/Imbad0202/academic-research-skills/blob/main/LICENSE — CC BY-NC 4.0 实测
4. https://github.com/Imbad0202/academic-research-skills/blob/main/README.zh-CN.md — 安装方式与依赖
5. https://github.com/Imbad0202/academic-research-skills/blob/main/docs/SETUP.md — Python/Pandoc/tectonic/平台支持
6. https://github.com/Imbad0202/academic-research-skills/blob/main/academic-paper/SKILL.md — 69 KB 正文、11 模式
7. https://github.com/Imbad0202/academic-research-skills-codex — Codex 变体（14,957★）
8. https://github.com/K-Dense-AI/scientific-agent-skills — 177 技能主仓库（原名 claude-scientific-skills）
9. https://api.github.com/repos/K-Dense-AI/scientific-agent-skills — 58,173★/MIT 实测
10. https://github.com/K-Dense-AI/scientific-agent-skills/tree/main/skills/scientific-writing — 代表性技能
11. https://github.com/K-Dense-AI/claude-scientific-writer — PyPI `scientific-writer`
12. https://pypi.org/project/scientific-writer/ — PyPI 包
13. https://github.com/zLanqing/codex-claude-academic-skills — 中文三技能
14. https://github.com/claesbackman/AI-research-feedback — 审稿 12 技能
15. https://github.com/LeonChaoX/qinyan-academic-skills — 187 技能 + 沁言学术
16. https://github.com/HughYau/AcademicForge — 33 技能合集
17. https://github.com/lingzhi227/agent-research-skills — 31 技能（无 LICENSE）
18. https://github.com/TingxiYu/academic-figure-skill — Nature 级图表（frontmatter 待修）
19. https://github.com/SNL-UCSB/paper-writing-skill — 单技能 35.6 KB
20. https://github.com/aipoch/medical-research-skills — 550+ 医学技能
21. https://github.com/anthropics/skills — 官方 20 技能（无 LICENSE 文件）
22. https://github.com/obra/superpowers — 15 技能（软件工程向）
23. https://github.com/O0000-code/awesome-academic-skills — 222 技能索引（CC0）

### 索引与二手资料
24. https://eu.36kr.com/en/p/3812800346742274 — 36kr/量子位《6.4k Stars! Complete Pipeline for Writing Papers with Claude Code》（2026-05-17），指向 ARS
25. https://api.github.com/search/repositories?q=academic-research-skills&sort=stars — 用于定位 ARS 原仓库（排除 fork）

### DSH 本地证据（本机文件，非 URL）
- `<DSH_INSTALL>\resources\app.asar` → `dsh/node_modules/@deepseek-ai/dsh-skill-filesystem/lib/index.js`（装载根、目录深度、frontmatter 解析、`isSkillName` 调用）
- `<DSH_INSTALL>\resources\app.asar` → `dsh/node_modules/@deepseek-ai/dsh-skill/lib/index.js`（`SKILL_NAME = /^[a-z0-9]+(?:-[a-z0-9]+)*$/`）
- `<DSH_INSTALL>\resources\app.asar` → `dsh/node_modules/@deepseek-ai/dsh-skill-office/assets/*/SKILL.md`（内置 office 技能 frontmatter，均只有 `name`+`description`）
- `%USERPROFILE%\.dsh\skills\`（用户级技能根实测）
- 提取与实测脚本：`<scratch>/asar_probe.js`、`asar_extract.js`、`extract_yaml.js`、`audit_frontmatter.js`、`test_frontmatter.js`

### 实测结论摘要（frontmatter 审计，19 个真实文件）
- ✅ ACCEPTED：K-Dense `scientific-writing`/`peer-review`/`citation-management`/`literature-review`；ARS 全部 5 个；`claesbackman review-paper`；`zLanqing research-writing-skill`/`office-academic-skill`；`lingzhi227 paper-writing-section`/`rebuttal-writing`；`SNL-UCSB paper-writing`；`anthropics docx`；`obra writing-skills`；`qinyan-nature-writing`
- ❌ IGNORED：`TingxiYu academic-figure-skill`（YAML 报错：Nested mappings are not allowed in compact mappings at line 2, column 14）
