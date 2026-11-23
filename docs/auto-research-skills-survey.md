# 自动化科研（auto-research / autoresearch / AI-Scientist）Agent Skills 生态调研

- **访问日期（exact access date）**：2026-11-23（Asia/Shanghai），实际抓取时间约 19:08–19:50 CST。
- **口径说明**：所有 stars / forks / pushed_at / license 均来自当次 `api.github.com/repos/<owner>/<repo>` 的 JSON 快照，**星数只为近似值**（GitHub 实时变动，且本报告不做趋势外推）。所引 README / 文件树同理。
- **方法**：先 `web_search` 找候选，再对每个仓库用 GitHub REST API + `raw.githubusercontent.com` 原文逐一核验；**未 clone 任何仓库、未安装任何依赖、未修改工作目录以外文件**。仅阅读了本机已有的 `~/.dsh/skills/dsh-probe-zz/SKILL.md` 作为 DSH 技能格式的对照样本。
- **结论适用范围**：DSH 44.7.0（本机 `<DSH_INSTALL>\version`），技能目录约定 `%USERPROFILE%\.dsh\skills\<name>\SKILL.md`。

---

## 一、一句话结论

**有真货，但不是"装个技能就能自动科研"**：目前唯一同时满足「87 个纯 Markdown SKILL.md + 真实 Python 工具链 + MIT + 2026-11 仍在更新」的自动化科研技能生态是 **wanshuiyin/Auto-claude-code-research-in-sleep（ARIS）**；但它最值钱的环节（跨模型审稿、引用双盲核验、端到端流水线）**深度绑定 Claude Code 的 Codex MCP / slash command / hooks**，在 DSH 里只能裁剪后使用（推荐按"能力清单"挑 6–10 个纯 Markdown 技能，而不是整包搬）。**K-Dense 的 177 个科学技能**是结构上最 DSH 友好的"科研能力底座"，**uditgoenka/autoresearch** 是最容易改写成 DSH 技能的"指标驱动迭代循环"。另外（lead 追加线索，已核实）：**Imbad0202/academic-research-skills（ARS）**以 58,199★ 成为这一领域的事实标准——但它是"文献型 auto-research"：13-agent 深调研 + 10 阶段论文流水线 + 5 席位评审，**从不运行实验**，且**已有社区 DSH 移植**（TY-Cheng/dsh-academic-research-skills），证明"纯 SKILL.md 可在 DSH 复现"，代价是 CC-BY-NC 非商业许可、hooks 丢失、移植目标版本为 DSH 0.2.x。Sakana 的 AI-Scientist v1/v2、HKUDS AI-Researcher、AgentLaboratory、karpathy/autoresearch 都**不是 skill，而是 Python 框架**，不能作为 DSH 技能安装，只能作为流程设计参考或外部命令封装。

---

## 二、对比总表

> 形态判断依据：仓库里是否以 `SKILL.md` 目录为主体。DSH 兼容性按「能否原样或轻改后放进 `~/.dsh/skills/` 被加载」判定，详见第五节。

| 项目 | 链接 | stars（约） | 最近更新（pushed_at） | license | 形态 | 核心能力 | DSH 兼容性 | 推荐度 |
|---|---|---|---|---|---|---|---|---|
| **ARS**（Imbad0202/academic-research-skills） | https://github.com/Imbad0202/academic-research-skills | 58,199 | 2026-11-23 | CC-BY-NC 4.0（README 与 LICENSE；GitHub API 标 Other/NOASSERTION） | Claude Code 技能套件：5 个顶层技能目录（`deep-research` 13 agent / `academic-paper` 12 agent / `academic-paper-reviewer` 7 agent / `academic-pipeline` 10 阶段 / `sr-screener` 4 agent）+ 根 `agents/` 42 个提示文件 + `scripts/` Python 检查器 + hooks + 16 命令 | 文献调研→写作→五席位同行评审→修改→终稿的"人在环"流水线；含 Semantic Scholar 引用核验、7 类 AI 失败模式完整性闸门 | **高（已有 DSH 移植）**：社区 `TY-Cheng/dsh-academic-research-skills` 逐字节 vendor 上游并生成 DSH 命令层，5 技能 + 2 原生团队技能 + 5 原生工具；hooks 未移植 | ★★★★（偏论文写作；**非商业许可**） |
| **ARIS**（wanshuiyin/Auto-claude-code-research-in-sleep） | https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep | 19,641 | 2026-11-19 | MIT | 87 个 `skills/<name>/SKILL.md` + Python 工具 + MCP server（Markdown-only 为主） | 选题→实验→跨模型审稿→论文→rebuttal→转投→slides 全流程；含实验队列/审计/引用核验 | **中高**：纯 Markdown 技能可直拷；依赖 Codex MCP / GPU / LaTeX 的技能需改写或弃用 | ★★★★☆ |
| **uditgoenka/autoresearch** | https://github.com/uditgoenka/autoresearch | 6,855 | 2026-10-31 | MIT | 1 个路由 `SKILL.md`（约 10 KB）+ 14 个 slash command 协议 + 9 个 Claude hooks + pi 扩展 | 通用"改一次→机械验证→keep/revert→TSV 记账"指标循环（Karpathy 理念泛化） | **中**：核心循环可转写；命令文件需并入 SKILL.md，hooks 在 DSH 不生效 | ★★★☆ |
| **K-Dense scientific-agent-skills** | https://github.com/K-Dense-AI/scientific-agent-skills | 58,173 | 2026-11-23 | MIT（每个 skill 各自 license，如 BSD-3） | 177 个 `skills/<name>/SKILL.md`，遵循 agentskills.io 标准，可作单插件包 | 生物/化学/医学/物理/数据/写作等科研工具与 100+ 数据库知识 | **高**：目录级迁移，frontmatter 含 name+description；但非 auto-research 循环 | ★★★★ |
| **SakanaAI/AI-Scientist** | https://github.com/SakanaAI/AI-Scientist | 15,033 | 2025-12-19 | 自定义"The AI Scientist Source Code License"（含强制 AI 披露条款） | Python/Jupyter 框架（模板化） | nanoGPT / 2D Diffusion / Grokking 三模板的论文自动生成 + LLM 审稿 | **不可用**（框架，非技能） | ★★ |
| **SakanaAI/AI-Scientist-v2** | https://github.com/SakanaAI/AI-Scientist-v2 | 7,546 | 2025-12-19 | 同上（NOASSERTION） | Python 框架（BFTS 树搜索，基于 AIDE） | 开放式 idea→实验树搜索→写作，宣称首个全 AI 通过同行评审的 workshop 论文 | **不可用**（框架，需 Linux + NVIDIA GPU） | ★★ |
| **HKUDS/AI-Researcher** | https://github.com/HKUDS/AI-Researcher | 5,900 | 2026-11-23 | **无 LICENSE 文件**（API `license: null`） | Python 框架 + Docker + Gradio WebGUI | 文献→idea→算法实现→验证→论文全自动；NeurIPS 2025 Spotlight | **不可用**（框架）；且**无许可证不可直接复用** | ★☆ |
| **SamuelSchmidgall/AgentLaboratory** | https://github.com/SamuelSchmidgall/AgentLaboratory | 5,941 | 2025-08-20 | MIT | Python 框架（YAML 配置 + 三阶段多 agent） | 文献综述→实验→报告写作；含 AgentRxiv、copilot 模式 | **不可用**（框架） | ★★ |
| **karpathy/autoresearch** | https://github.com/karpathy/autoresearch | 100,456 | 2026-03-26 | **仓库无 LICENSE 文件**（README 自称 MIT） | Python + `program.md`（自述"super lightweight skill"） | 单卡 nanochat 5 分钟训练即验，val_bpb 单指标，一晚约 100 次实验 | **低**：只有一个 `program.md` 可当模板，实际依赖 GPU 训练环境 | ★★☆（理念价值高） |
| **brycewang-stanford/AERS** | https://github.com/brycewang-stanford/Auto-Empirical-Research-Skills | 5,106 | 2026-11-23 | GitHub 标注 Other/NOASSERTION；README 徽章写 CC BY-SA 4.0 | 社区技能聚合器：78 个合集 / 自述 1,151 个 skill（仓库描述却写 23,000+） | 社科实证研究 9 阶段流水线（Stata/R/Python、因果推断、降 AIGC、投稿） | **中**：确有 SKILL.md 可拷，但库混杂、来源与许可证需逐个审 | ★★☆ |
| **rpatrik96/research-agora** | https://github.com/rpatrik96/research-agora | 20 | 2026-11-16 | MIT | Claude Code 插件市场：4 个 plugin，约 30 个 workflow，主体是 `commands/` + `agents/` | 论文引用核验、实验-代码一致性核验、统计校验、图表/LaTeX 工具 | **低**：以 slash command / agent 定义为主，需重写成 SKILL.md | ★☆ |
| **x-roocky/ai-scientist-skills** | https://github.com/x-roocky/ai-scientist-skills | 5 | 2026-04-02 | Other/NOASSERTION | 9 个 `skills/<name>/SKILL.md` + `tools/*.py` + LaTeX 模板 | 把 AI-Scientist-v2 流程重写成 Claude Code 技能包（单人项目） | **中**：有标准 skills 目录，但依赖其 Python tools 与 Python 环境 | ★☆ |
| **MarsWise/scientific-agent-skills** | https://github.com/MarsWise/scientific-agent-skills | 0 | 2026-10-26 | MIT | K-Dense 仓库的 fork（父仓库 58,173★） | 与 K-Dense 相同 | 同 K-Dense | 直接忽略（用上游） |

**一句话读表**：真正"能当技能用"的是 ARS、ARIS、K-Dense、uditgoenka，以及两个小项目（research-agora / x-roocky）；标"不可用"的四个（Sakana v1/v2、HKUDS、AgentLaboratory、karpathy）是 Python 框架，价值在于流程与 prompt 设计，而不是安装。**ARS 已有社区 DSH 移植**，是"文献型 auto-research"最接近开箱即用的一条路，但受 CC-BY-NC 与版本兼容限制。

---

## 三、逐项目详细点评（证据均来自本次 fetch）

### 1. ARIS — wanshuiyin/Auto-claude-code-research-in-sleep ★ 本次唯一"完整的自动化科研技能生态"

- **硬事实**：`stargazers_count=19641`、`forks=1572`、`created_at=2026-03-10`、`pushed_at=2026-11-19T10:40:49Z`、MIT、default branch `main`、仓库体积约 38 MB、open issues 75。GitHub 描述自述"Lightweight Markdown-only skills for autonomous ML research: cross-model review loops, idea discovery, and experiment automation. No framework, no lock-in — works with Claude Code, Codex, OpenClaw, or any LLM agent"。
- **技能是真的目录化的**：`docs/SKILLS_CATALOG.md` 明确写 "**87 skills**"，并分 12 类（Workflow Orchestrators / Literature & Search / Ideation / Proof Engineering / Experiments / Review & Audit / Paper Writing / Talks / Patents / Meta & Utilities…）。我实抓了 `skills/analyze-results/SKILL.md`（1,660 B），frontmatter 为 `name: analyze-results` + `description:` + `argument-hint:` + `allowed-tools: Bash(*), Read, Grep, Glob, Write, Edit`，正文是"定位结果→建对比表→统计→洞察→更新文档"的步骤化指令。**这是标准 SKILL.md，不是 slash command**（虽然它的 `$ARGUMENTS` 占位与 `allowed-tools` 是 Claude Code 约定）。
- **工作流是"真流水线"而非"一句话 prompt"**：`/research-pipeline` = W1 `/idea-discovery`（research-lit→idea-creator→novelty-check→research-review→research-refine-pipeline）→ W1.5 `/experiment-bridge`（读实验计划→写代码→sanity check→部署 GPU→收初步结果）→ W2 `/auto-review-loop`（审→改→再审，直到正面或达上限）→ W3 `/paper-writing`（paper-plan→figure→write→compile→auto-paper-improvement-loop）。另有 W4 rebuttal、W5 resubmit、W6 paper-talk、patent 流水线。
- **不是纯 prompt：有真工具链**。`tools/` 下有 `research_wiki.py`(78,927 B)、`verify_papers.py`(29,823 B)、`watchdog.py`(19,383 B)、`review_gate.py`(20,528 B)、`forensics_gate.py`(32,705 B)、`experiment_queue/queue_manager.py`(15,116 B)；`skills/citation-crosscheck/scripts/cx_verify.py` 84,510 B、`skills/figure-spec/scripts/figure_renderer.py` 29,876 B。CI 有 `check-skills-inventory.yml`、`lint-skills-helpers.yml`、`test-suite.yml`、`verify-codex-policy-audit.yml`，说明有工程化维护。
- **安装方式（已核实）**：`git clone … ~/aris_repo` → 在项目里 `bash ~/aris_repo/tools/install_aris.sh`（**Windows 有 `tools/install_aris.ps1`，72,113 B**），脚本把 `skills/<name>` 符号链接到 **`.claude/skills/`**，并写 `CLAUDE.md` 配置块；跨模型审稿则要求 `claude mcp add codex -s user -- python3 "$HOME/aris_repo/mcp-servers/codex-exec/server.py"`，另可选 `llm-chat`、`gemini-review`、`minimax-chat` 等 MCP。
- **代价**：默认配置是"Claude Code 当执行器 + Codex MCP(GPT) 当审稿人 + macOS 本地 + 远程 Linux GPU + LaTeX"，文档 `SETUP_GUIDE.md` 明说 Workflow 1/2 不需要 LaTeX，但 `/auto-review-loop` 等审稿技能**强依赖 Codex MCP**。对 DSH 来说，这是它最大的可用性缺口（详见第六节）。

### 2. uditgoenka/autoresearch — 最接近"Karpathy 原版循环"的技能化实现

- **硬事实**：6,855 stars、492 forks、MIT、`pushed_at=2026-10-31T13:56:11Z`、default branch `master`、SKILL.md frontmatter 版本 **2.3.0**、open issues 仅 1。
- **形态**：1 个薄路由 `SKILL.md`（10,069 B，2.1.0 起从 813 行巨型文件拆成路由 + 12 个自包含命令文件，README 称 token 消耗降 95%）+ `.claude/commands/autoresearch.md` 与 13 个子命令 md（plan/debug/fix/security/ship/scenario/predict/learn/reason/probe/improve/evals/regression）+ `.claude/hooks/autoresearch/` 下 9 个 `.cjs` 钩子 + `pi-extension/`。
- **循环本身（实测 SKILL.md 内容）**：`Safety Invariants`（绝不自动 push/deploy、默认有迭代上限、结果写 `autoresearch/{subcommand}-{YYMMDD}-{HHMM}/`）→ Dispatch 表（有 `Metric:`/`Verify:` 走 Classic，自由目标走 Orchestrator）→ 8 条硬规则（一次只改一处、机械指标、自动回滚、git 即记忆、"指标不能自证行为不变"）→ **fork-and-flush**（预算 33%/66% 或连续 5 轮无 keep 时，从最优 commit 分叉多个新上下文分支，各跑一小段取最优）。
- **安装（核实）**：`npx skills add uditgoenka/autoresearch`（推荐）、`/plugin marketplace add uditgoenka/autoresearch`、或手拷 `.claude/skills/autoresearch` + `.claude/commands/autoresearch*`。**它本质是"Claude Code 技能 + slash command + hook"三件套**，hook 负责危险命令拦截/隐私拦截/上下文注入。
- **质量信号**：有 `tests/fixtures/`（orchestrator 状态机、plateau、regression 等大量 fixture）、`preprgate` 检查脚本、release 流程；但它不是"科研"技能，而是**任意可度量目标的迭代引擎**（README 明说适用代码、内容、营销、销售、HR、DevOps），做 ML 实验时只是"自动跑实验并 keep/discard"，不含选题/文献/写作。作者 Udit Goenka 是创业者，README 带 PayPal 赞助位——商业色彩需自行判断。
- **循环定义（结论，回答 lead 追问）**：**Modify → Verify → Keep/Discard** 的准确展开是：① 读当前状态 + git 历史 + 结果日志 → ② 选下一个改动（基于什么有效/失效/未试）→ ③ 只做**一处**聚焦改动 → ④ 先 `git commit` 再验证 → ⑤ 跑**机械** verification（测试/benchmark/分数，不接受"看起来更好"）→ ⑥ 变好则 keep，变差则 `git revert`，崩溃则修复或跳过 → ⑦ 写 TSV 结果行 → ⑧ 重复至 N 轮或目标达成。它与 **Karpathy/autoresearch** 的关系是"同一套循环纪律的不同载体"：Karpathy 原版把范围锁死在"单卡 nanochat + 5 分钟训练 + val_bpb 单指标 + 只改 `train.py`"，用 `program.md` 给 agent 当指令，一晚约 100 次实验；uditgoenka 把"单文件/单指标/固定预算"泛化为"任意领域的 Scope + Metric + Verify"，并额外提供 9 条安全不变量、hooks 护栏、fork-and-flush、TSV evals、orchestrator 与 14 个子命令。**Karpathy 提供的是"研究环境 + 协议范本"，uditgoenka 提供的是可安装的循环骨架**；两者都没有科研领域知识（选题/文献/写作），这是它们与 ARIS/ARS 的根本分工差异。

### 3. K-Dense-AI/scientific-agent-skills — DSH 兼容性最好的"科研能力库"（但不是自动科研循环）

- **硬事实**：58,173 stars、5,097 forks、MIT（仓库级）、`created_at=2025-10-19`、`pushed_at=2026-11-23T09:18:27Z`、版本徽章 **v2.72.0**、仓库约 471 MB、open issues 98。README 明确"177 scientific and research skills"，并给出论文 arXiv:2609.00065。
- **结构已实测**：`skills/<name>/SKILL.md`，每个 skill 有 `name` + `description` + `license`（**逐 skill 不同**，如 scanpy 是 BSD-3-Clause）+ `compatibility` + `metadata.version/last-reviewed/upstream-version/skill-author`。我抓取的 `skills/scanpy/SKILL.md` 是一个 20+ KB 的完整操作手册：脚本工具箱（`run_pipeline.py`/`qc_analysis.py`/…）、参数、坑、references 目录说明。**这正符合 DSH 的 `~/.dsh/skills/<name>/SKILL.md` 目录约定**。
- **安装（核实）**：`npx skills add K-Dense-AI/scientific-agent-skills`；或 `gh skill install K-Dense-AI/scientific-agent-skills [skill] --agent …`（可 `--pin` 版本）；或 `git clone … ~/.agents/skills/scientific-agent-skills`。仓库是合法的 Agent Plugins 1.0.0 包（根 `plugin.json` + `skills/`）。
- **定位**：这是"领域知识与可执行脚本"的库（生物信息/化学/医学影像/材料/天文/数据可视化/科学写作…），**没有"选题—实验—审稿"的自治循环**，也没有多 agent 编排；它让 agent 在做科研任务时更可靠，但不会自己推进一个研究项目。
- **风险**：README 自己警告"Skills can execute code and influence your coding agent's behavior. Review what you install."；仓库有 Cisco AI Defense Skill Scanner 扫描 + CI；但**逐 skill license 不同**，商用前要逐个看 `license:` 字段。

### 4. brycewang-stanford/Auto-Empirical-Research-Skills（AERS）— 高星，但更像"营销驱动的聚合站"

- **硬事实**：5,106 stars、581 forks、`created_at=2026-04-03`、`pushed_at=2026-11-23T09:20:28Z`、语言标记 Stata、体积约 45 MB、open issues 1；API license 为 `NOASSERTION`（Other），而 README 徽章写 **CC BY-SA 4.0**——**口径不一致**。
- **口径矛盾（重要质量信号）**：GitHub 仓库描述写 "23,000+ agent skills"，README 实际写 "**78 个合集 · 1,151 个 skill**"。这不是同一量级，且 README 明说社区合集是"上游快照"，需回原仓库看 LICENSE——也就是说它是个**聚合器（awesome-list + vendored 技能）**，真正的原创只有 7 个"Stanford REAP × StatsPAI 自研"skill。
- **形态**：`skills/00-…` 到 `skills/74-…` 共 78 个合集目录，多数带 `SKILL.md`；安装方式是 `claude plugin marketplace add brycewang-stanford/Auto-Empirical-Research-Skills` 或手拷到 `~/.claude/skills/`（README 还教你"把仓库 URL 丢给 agent 让它自己装"）。能力面是**社会科学实证研究**（DID/RD/IV/SCM、Stata/R/Python、文献 PRISMA、降 AIGC、投稿），不是 ML 实验自动化。
- **商业链接**：README 顶部力推同团队的 `StatsPAI`（`pip install statspai`）和 `copaper.ai`（"20 分钟完成一篇实证论文"）。对 DSH 用户的含义：技能未必不能用，但要把它当"二手聚合 + 自家产品导流"，**不要按描述里的 23,000+ 去预期**。

### 5. rpatrik96/research-agora — 小而认真的"论文核验"插件集，但主体不是 SKILL.md

- **硬事实**：仅 20 stars、5 forks、MIT、`created_at=2026-01-29`、`pushed_at=2026-11-16T14:15:16Z`、体积约 12.5 MB；README 自述"30 public workflows"，4 个插件 discover / write / verify / toolkit。
- **结构与兼容性**：`plugins/<plugin>/SKILL.md` 是插件级路由（1–2 KB），真正的流程在 `plugins/<plugin>/commands/*.md` 与 `agents/*.md`（如 `paper-references`、`paper-verify-experiments`、`statistical-validator`、`proof-auditor`）。安装是 Claude Code 市场：`/plugin marketplace add rpatrik96/research-agora` + `/plugin install verify@research-agora`。
- **值得肯定的点**：它的产品逻辑是"**只保留'产出可被机械校验'的技能**"（引用能被解析、实验能被代码核验、统计能被复算），并带 `registry/`、`tests/`、`scripts/writing_verify.py`(29 KB) 等；这是本批候选中**最强调验证闭环**的一个。
- **减分项**：仓库里 `dissemination/` 放满 `social-copy.md`、`twitter-thread-launch.md`、`launch-strategy.md` 等营销物料；星数只有 20，说明社区验证很弱。**内容质量 > 社区热度**的典型。

### 6. x-roocky/ai-scientist-skills — 概念正确，但单人、停更、星数 5

- **硬事实**：5 stars、2 forks、`created_at=2026-04-01`、`pushed_at=2026-04-02`、license `NOASSERTION`、语言 TeX、体积约 6 MB。
- **结构**：`skills/{ai-scientist, ideation, lit-search, experiment, experiment-step, plot, review, workshop, writeup}/SKILL.md` 共 9 个技能（`ai-scientist` 是总编排），另有 `tools/state_manager.py`(31 KB)、`metric_parser.py`、`latex_compiler.py`、`pdf_reader.py`、`search.py`，以及 ICLR/ICML LaTeX 模板与 review few-shot 数据；`.claude/commands/*.md` 与 `.agents/skills/*` 都是指向 `skills/` 的**符号链接**（即同一份 SKILL.md 多 host 复用）。
- **判断**：设计思路与 ARIS 同源（把论文流水线拆成多 skill + 状态机 tools），但**单人维护、2026-04 后无更新、无社区**；依赖自己的 `tools/` 与 Python 环境，`SKILL.md` 里会引用这些脚本路径。可作"AI-Scientist-v2 转技能化"的参考实现，不建议作为主力安装。

### 7. SakanaAI/AI-Scientist（v1）与 AI-Scientist-v2 — 学术标杆，但不能当 skill 用

- **硬事实**：v1 `15,033` stars / `2,092` forks / `created_at=2024-08-12` / `pushed_at=2025-12-19T07:46:21Z` / 语言 Jupyter Notebook / 124 open issues；v2 `7,546` stars / `1,016` forks / `created_at=2025-04-08` / [同样 `pushed_at=2025-12-19`] / Python / 78 open issues。两者都是 `license: Other/NOASSERTION`，实抓 `LICENSE` 是自定义 **"The AI Scientist Source Code License"**：含"不得用于监控/合成人脸/医保预测/犯罪预测"等限制，以及著名的 **3.2.e "AI Scientist" 条款——生成或传播科学论文必须显著披露是机器生成**，否则违约。
- **形态**：v1 是 `conda create -n ai_scientist python=3.11` + `pip install -r requirements.txt` + `apt-get install texlive-full`，然后 `python launch_scientist.py --model … --experiment nanoGPT_lite --num-ideas 2`；三个模板（NanoGPT / 2D Diffusion / Grokking）；FAQ 称每篇论文成本 **< $15**（Claude Sonnet 3.5），推荐模型不低于 GPT-4 水平。
- **v2**：主打 **agentic tree search（BFTS，基于 AIDE）** + 实验管理 agent，流程为 `perform_ideation_temp_free.py` 生成 idea JSON → `launch_scientist_bfts.py --load_ideas …` 跑树搜索 → 写论文；要求 Linux + NVIDIA CUDA + PyTorch；成本 **$15–20/次 + 约 $5 写作**；README 诚实地说"v2 不一定比 v1 好，有强模板时 v1 成功率更高"。
- **对 DSH 的含义**：这两个是**外部 Python 框架**，DSH 技能层无法加载；只能用"写一个 SKILL.md，指示模型去 `uv/pip` 环境里调用这些脚本"的方式封装，且必须有 GPU、LaTeX、API key。**且在 DSH 里产出论文时，该许可证要求显著披露 AI 生成**——如果只是借用流程思路（不要代码），则不受该许可证约束，但也没有可安装物。

### 8. HKUDS/AI-Researcher — 全流程框架，但**没有 LICENSE**

- **硬事实**：5,900 stars、730 forks、`created_at=2025-03-11`、`pushed_at=2026-11-23T09:44:54Z`（本批里除 K-Dense 外最活跃）、Python、体积 **约 762 MB**、open issues 55、**API `license: null`（仓库根目录无 LICENSE 文件）**；描述标注"[NeurIPS2025] AI-Researcher: Autonomous Scientific Innovation"，并给出商用版 novix.science。
- **形态**：`uv venv --python 3.11` + `uv pip install -e .` + `playwright install`，或 `docker pull tjbtech1/airesearcher:v1`；`.env` 必填 `DOCKER_WORKPLACE_NAME / BASE_IMAGES / COMPLETION_MODEL / CHEEP_MODEL / GPUS / OPENROUTER_API_KEY / GITHUB_AI_TOKEN / CATEGORY / INSTANCE_ID / TASK_LEVEL`；入口 `bash research_agent/run_infer_level_1.sh`（给定 idea）/ `run_infer_level_2.sh`（只给参考论文让它自己出 idea），另有 `web_ai_researcher.py` Gradio GUI 和 `paper_agent/writing.py`。
- **判断**：工程完整度高（Docker 容器 + benchmark（diffu_flow/gnn/reasoning/recommendation/vq）+ leaderboard + 论文），但**没有开源许可证 = 默认保留全部权利**，企业/对外交付场景不能直接复用；体积 762 MB + Docker + OpenRouter 依赖，也不适合塞进 DSH 技能层。作为"流程参考/外部服务"可看，作为"技能"不可用。

### 9. SamuelSchmidgall/AgentLaboratory — 经典三阶段框架，已约 15 个月未更新

- **硬事实**：5,941 stars、807 forks、MIT、`created_at=2025-01-08`、**`pushed_at=2025-08-20T21:46:43Z`**（距访问日约 15 个月）、Python、75 open issues。
- **形态**：python3.12 venv + `pip install -r requirements.txt`（可选 pdflatex）→ `python ai_lab_repo.py --yaml-location "experiment_configs/MATH_agentlab.yaml"`；三阶段（Literature Review / Experimentation / Report Writing），支持 copilot 模式、checkpoint 恢复、`--llm-backend` 选 `gpt-4o`/`o1`/`deepseek-chat`，并附 AgentRxiv（agent 间互传论文）。
- **判断**：代码结构清晰、MIT 友好，是"多 agent 科研流水线"的教科书实现；但 2025-08 后停更、模型列表停留在 o1/DeepSeek-v3 时代，依赖与 prompt 都可能过时。**不是技能，无法装入 DSH**；可读其 `readme/` 与 `ai_lab_repo.py` 的 prompt 组织方式。

### 10. karpathy/autoresearch — 10 万星的"原型"，但本体是训练脚本

- **硬事实**：**100,456 stars**、13,798 forks、`created_at=2026-03-06`、`pushed_at=2026-03-26T00:07:37Z`、Python、194 open issues、**API `license: null`（无 LICENSE 文件，但 README 末尾写 "## License MIT"）**——口径不一致。
- **形态**：只有三个关键文件：`prepare.py`（固定常量、数据准备、tokenizer，不许改）、`train.py`（agent 唯一可改：模型/优化器/训练循环）、`program.md`（人类写给 agent 的指令，"essentially a super lightweight skill"）。固定 **5 分钟**训练预算、单指标 **val_bpb**，一晚约 100 次实验；要求单张 NVIDIA GPU（H100 tested）、Python 3.10+、`uv`；README 给出 Mac/Windows/AMD 的社区 fork。
- **对 DSH 的含义**：这是"**给 agent 一个真实训练环境 + 一个可机械判定的指标**"的原型，而不是可安装技能。DSH 里若要复用，只能把 `program.md` 改写成 `~/.dsh/skills/autoresearch-gpu/SKILL.md`（指令内容不变），并要求本机有 GPU 与 `uv`；否则只能借鉴它的"单文件可改 + 固定预算 + 单指标 + git 记忆"设计。

### 11. 已排除 / 存疑项

- **MarsWise/scientific-agent-skills**：0 stars，`fork: true`，父仓库为 K-Dense（58,173★），`pushed_at=2026-10-26`。**直接忽略，用上游。**
- **huytieu/auto-research**：`https://api.github.com/repos/huytieu/auto-research` 返回 **404**；仅在第三方站 typingmind 有同名 skill 介绍页，**无法核实仓库真实存在**，不纳入推荐。
- （检索中还出现 docxology/template、quriosity-agent 文章等二手列表，未作为一手证据使用。）

### 12. Imbad0202/academic-research-skills（ARS）+ TY-Cheng 的 DSH 移植 ★ lead 追加线索，已专项核实

**上游硬事实**：`stargazers_count=58199`、`forks=4438`、`created_at=2026-02-26`、`pushed_at=2026-11-23T09:43:27Z`、仓库体积约 26 MB、open issues 70、版本 **v3.24.4**、DOI `10.5281/zenodo.20696614`；GitHub API license 为 `Other/NOASSERTION`，但 README 徽章与 LICENSE 正文明确为 **CC-BY-NC 4.0（禁止商业使用）**。描述："Academic Research Skills for Claude Code: research → write → review → revise → finalize"。

**形态（实测根目录）**：5 个顶层技能目录 `deep-research/`、`academic-paper/`、`academic-paper-reviewer/`、`academic-pipeline/`、`sr-screener/`（每个含 `SKILL.md`），加根级 `agents/`（agent 提示文件）、`commands/`（`ars-*.md` slash 命令）、`hooks/`、`scripts/`（Python 检查器/ledger/citation gate/adapters）、`shared/`（schema 与合同）、`tests/`、`evals/`、`examples/`、`.claude-plugin/`。**它是"技能套件（suite）"，不是单个 SKILL.md**。

**Deep Research 与 10 阶段流水线（已从 `docs/ARCHITECTURE.md` 核实）**：
- `deep-research` v2.12.1：**13 个 agent**（research_question / research_architect / bibliography / source_verification / synthesis / meta_analysis / editor_in_chief / devils_advocate / risk_of_bias / ethics_review / socratic_mentor / report_compiler / monitoring）+ 1 个 advisory observer；8 种模式（full / quick / socratic / review / lit-review / three-way-scan / fact-check / systematic-review）。
- `academic-paper`：12 agent、11 模式；`academic-paper-reviewer`：7 agent、6 模式（五席位评审：Journal-Fit + R1/R2/R3 + Devil's Advocate）。
- `academic-pipeline`：**10 个阶段** = 1 RESEARCH → 2 WRITE → 2.5 INTEGRITY → 3 REVIEW → 4 REVISE → 4.5 FINAL INTEGRITY → 5 FINALIZE → 6 PROCESS SUMMARY，加上 3′ RE-REVIEW 与 4′ RE-REVISE 两个回环阶段；**每个阶段都有强制用户确认检查点**，2.5/4.5 为强制完整性闸门（7 类 AI 失败模式清单：实现 bug、幻觉引用、幻觉实验结果、走捷径、bug 当洞见、方法编造、早期 frame-lock）。
- **它不是实验自动化**：README 明说"ARS never runs experiments"，实验只是以 `experiment_provenance[]` 形式**由研究者外部完成后录入**；因此它的"自动研究循环"= 调研→写作→评审→修改→终稿的**文献型研究闭环 + 机械验证闸门**，不是 Karpathy 式"改代码→跑实验→keep/discard"。这一点与 ARIS（真跑 GPU 实验）是互补而非替代关系。

**依赖（回答"能不能跑"）**：
- 必需：Claude Code + `ANTHROPIC_API_KEY`；
- 机器闸门依赖：**Semantic Scholar API**（Stage 1 引用 Tier-0 核验，标题 Levenshtein ≥ 0.70；无 key 可跑但限流）、Python 3.9+（确定性检查器：`scripts/check_data_access_level.py`、`check_repro_lock.py`、`cross_model_handoff.py`、citation gate 等；README 明说"core skills are prompt-driven，Python 只用于 write-scope guard 与少量 opt-in 命令"）、可选 Pandoc + tectonic（DOCX/PDF）；
- 编排依赖：Claude Code 的 **subagent（Agent/Task）+ hooks**（v3.10 加了按角色写范围 guard；SessionStart 播报）；
- 可选：跨模型核验 `ARS_CROSS_MODEL`（需另一家模型 API）。
- 成本与成熟度信号：README `docs/PERFORMANCE.md` 估 **一篇 15k 词论文约 $3–7**；14 个 CI workflow（8 个 blocking）、`tests/`、`evals/`、`examples/showcase/`（2026-03 真实运行产物，作者诚实标注"旧版本、非当前性能"）；同时作者明确自曝边界：评审 `NOT_CALIBRATED`、claim-audit 的校准 runner 用 stub judge（只验证工具、未验证真实 judge）、部分检查是抽样/LLM 中介。

**DSH 移植（关键发现，回答"纯 SKILL.md 能否复现"）**：上游 README 就指向社区移植 **[TY-Cheng/dsh-academic-research-skills](https://github.com/TY-Cheng/dsh-academic-research-skills)**（1★，fork，`created_at=2026-11-08`、`pushed_at=2026-11-23T06:12:40Z`，CC-BY-NC-4.0，topics=`dsh-plugin`；其父仓库为 nullptr-DZF/dsh-academic-research-skills，37★）。实测其 README：版本 v0.4.7，安装方式 `dsh plugin --profile web add github:TY-Cheng/dsh-academic-research-skills#v0.4.7`，要求 **DSH 0.2.x（在 0.2.2-rc.5 上测过）+ pnpm + Python 3.9+**；提供 5 个模型可调用技能（deep-research / academic-paper / academic-paper-reviewer / academic-pipeline / sr-screener）、2 个原生团队技能（`ars-team` 用真实 `subagent` 跑五席位评审；`ars-pipeline-team` 把 10 阶段映射成 DSH Team board 的 stage task graph）、5 个原生工具（`ars_search`/`ars_lookup`/`ars_integrity`/`ars_pipeline_status`/`ars_manifest`）、16 个 DSH 命令；`skills/`、`scripts/`、`shared/`、根 `agents/` 与上游**逐字节一致**，`commands/` 为重新生成的 DSH 适配层。
- **移植明确丢失的东西**：上游 Claude Code 的 **hooks 不移植**（按角色写范围 guard、SessionStart 播报）；42 个技能内 agent 提示文件**默认内联运行**（`ars-team` 才用真实 subagent）；角色分离只是流程控制，不构成独立误差过程的证明。
- **上游对移植的审查口径**：维护者"核实了 vendored 文件与 pinned commit 一致、审阅了 README 与提交文档，但**没有审计移植自身的代码、也没有运行过该移植**"；且移植文档记录的 e2e 用的是 v0.3.0（无 0.4.4 原生层），只跑到 Stage 5、未跑 Stage 6，角色提示全部内联在单个 DSH 会话中，Stage 3/3′/5 的检查点"没有独立的用户决策记录"。
- **对 DSH 的结论**：**纯 SKILL.md 可以复现"技能内容与阶段流程"**（移植已证明 `skills/` 逐字节可用、命令可重生成），**但不能复现 hooks 强制的写范围隔离**；完整 10 阶段流水线还需要"套件目录 + `shared/` 合同 + Python 检查器 + 路径约定（`DSH_ARS_ROOT`）"，不是单文件技能。另有**版本错配**：移植自称适配 DSH 0.2.x，而本会话运行的是 **DSH 44.7.0**（`<DSH_INSTALL>\version`），插件 API（bundles/`ctx.skills`/`tools`/`agentPresets`）是否向后兼容**本次未验证**，需先小范围试装。

---

## 四、DSH 兼容性判定标准（本节是后面所有结论的依据）

**DSH 技能规范（本机实证）**：`~/.dsh/skills/<name>/SKILL.md`，YAML frontmatter 至少含 `name`（kebab-case）与 `description`，正文为 Markdown 指令；会话 skill 目录只展示 name+description 摘要，模型按需加载。本机样本 `dsh-probe-zz/SKILL.md` 只有 `name` + `description` 两个键。

**因此，以下 Claude Code 专有物在 DSH 中不可用或语义改变**：

| Claude Code 物 | 在 DSH 的情况 | 影响 |
|---|---|---|
| `.claude/commands/*.md`（slash command） | **不加载**，不能被 `/xxx` 触发 | 命令型技能（uditgoenka 的 14 个命令、research-agora 的 commands、x-roocky 的 commands）必须并入 `SKILL.md` 或改成 `references/` 由正文指示读取 |
| `.claude/agents/*.md`（subagent 定义） | **不加载**；DSH 的 subagent 由工具调用+prompt 决定 | agent 角色需写进 SKILL.md 正文，或调用 DSH subagent 时以文本传递 |
| `.claude/hooks/*.{js,cjs}`（PreToolUse 等） | **不生效** | autoresearch 的危险命令拦截/隐私拦截/上下文注入全部失效，需靠 DSH 自身权限策略 + SKILL.md 文字约束 |
| `$ARGUMENTS` / `argument-hint` / `allowed-tools` | `$ARGUMENTS` 不会被替换；后两者是 Claude 元数据，DSH 无对应校验 | 需改写为"参数取自用户消息"，并删除/改写 allowed-tools |
| MCP server（`claude mcp add codex …` 等） | 本会话工具集中**未见 MCP 工具**；DSH 能否挂 MCP 未在本次验证 | ARIS 的跨模型审稿（auto-review-loop/novelty-check/research-review/experiment-audit/kill-argument/proof-checker 等）**默认不可用** |
| 插件市场 `.claude-plugin/marketplace.json`、`npx skills add` | 安装目标是 `~/.claude/skills`、`~/.agents/skills` 等 | 需手动 `cp -r` 到 `~/.dsh/skills`，或写一次性转换脚本 |
| Claude/Codex 的 `Skill` 触发词、slash 命令 | DSH 只有 skill 目录 + description 匹配 | `description` 需改写成 DSH 模型容易匹配的中文/英文混合描述，并明确触发场景 |

**结论口径**：
- **高兼容** = 仓库本身就是 `skills/<name>/SKILL.md` 目录树，frontmatter 有 `name`+`description`，无需 slash command/hook/MCP（K-Dense 是唯一完全符合的）。
- **中高** = 大部分是 SKILL.md，少数技能依赖 MCP/GPU/LaTeX（ARIS）。
- **中** = 有 SKILL.md 但必须配套 Python 工具或命令文件（uditgoenka 核心、x-roocky）。
- **低** = 主体是 commands/agents/插件市场（research-agora）。
- **不可用** = 纯 Python 框架（Sakana v1/v2、HKUDS、AgentLaboratory、karpathy）。

---

## 五、如果要在 DSH 里用：具体落地方案

### 5.1 直接可搬（复制目录即可，约 30 秒/个）

**推荐来源：K-Dense `skills/<name>/` 与 ARIS `skills/<name>/`**

```powershell
# 以 ARIS 的 arxiv 技能为例（纯 Markdown，无 MCP 依赖）
Copy-Item -Recurse "$HOME\aris_repo\skills\arxiv" "$env:USERPROFILE\.dsh\skills\arxiv"
# 以 K-Dense 的 scanpy 技能为例（含 scripts/references，DSH 不会自动加载，需 SKILL.md 指示读取）
Copy-Item -Recurse "$HOME\kdense\skills\scanpy" "$env:USERPROFILE\.dsh\skills\scanpy"
```

装完必须做**三处改写**（否则在 DSH 里会退化或报错）：

1. **frontmatter 只留 name + description**（保守做法；DSH 是否容忍额外键未验证）：
   ```yaml
   ---
   name: arxiv
   description: 检索/下载/总结 arXiv 论文。当用户要查 arXiv、读某篇论文、做文献速览时使用。
   ---
   ```
2. **删掉 `$ARGUMENTS`**，改成"任务参数取自用户当前消息"或"若用户未提供论文 ID，先询问"。
3. **把 Claude 工具名映射为 DSH 工具**：`Read/Grep/Glob` → `read/grep/glob`；`Bash`/`Bash(*)` → `pwsh`（Windows）或 bash（WSL/Git Bash）；`Write/Edit` → `write/edit`；`WebFetch` → `web_fetch`；`Task`/subagent → 调用 DSH subagent 并传 prompt。

**ARIS 中可直接搬的"纯 Markdown、无 MCP"候选（按目录名）**：
`arxiv`、`semantic-scholar`、`openalex`、`alphaxiv`、`keenable-search`、`web-debug-search`、`research-lit`、`comm-lit-review`、`experiment-plan`、`analyze-results`、`formula-derivation`、`mermaid-diagram`、`figure-description`、`figure-spec`（需 python 画图）、`paper-plan`、`paper-write`、`paper-figure`（需 matplotlib）、`paper-compile`（需 LaTeX）、`grant-proposal`、`writing-systems-papers`、`patent` 系列（`invention-structuring`/`claims-drafting`/`specification-writing`/`jurisdiction-format`/`prior-art-search`）、`pixel-art`、`research-wiki`（需 Python）、`experiment-audit`（**但依赖 Codex MCP，不建议直搬**）。

**ARIS 中必须改写或弃用（依赖 Codex/llm-chat MCP、GPU、SSH、LaTeX、Mac Keychain）**：
`auto-review-loop`、`auto-review-loop-llm`、`auto-review-loop-minimax`、`research-review`、`novelty-check`、`result-to-claim`、`paper-claim-audit`、`kill-argument`、`proof-checker`、`citation-audit`、`citation-crosscheck`、`idea-discovery`、`research-refine`、`research-refine-pipeline`、`research-pipeline`、`experiment-bridge`、`run-experiment`、`monitor-experiment`、`experiment-queue`、`vast-gpu`、`serverless-modal`、`qzcli`、`training-check`、`system-profile`、`overleaf-sync`、`paper-slides`/`slides-polish`/`paper-talk`、`meta-optimize`/`meta-apply`、`feishu-notify`（可选 webhook）。

> 改写思路（以 `auto-review-loop` 为例）：把"调用 codex MCP 让 GPT 审稿"替换为"用 DSH `subagent` 以**对抗式审稿人**人格审稿，或由人类贴入外部模型输出"，并把 `review_gate.py` 作为可选本地脚本；**不要**保留它"必须 MCP 才能跑"的硬依赖，否则在 DSH 里会静默空转。

### 5.2 需要改写的（工作量 0.5–2 小时/个仓库）

**uditgoenka/autoresearch → 1 个 DSH 技能 `autoresearch`**

- 新建 `~/.dsh/skills/autoresearch/SKILL.md`：把原 `SKILL.md`（10 KB，路由 + dispatch + 8 条规则）作为正文，**保留循环与安全不变量**；
- 把 14 个命令文件（`plan/debug/fix/security/ship/scenario/predict/learn/reason/probe/improve/evals/regression`）复制到 `~/.dsh/skills/autoresearch/references/*.md`，并在 SKILL.md 里写："根据用户意图读取对应 references/<name>.md"（因为 DSH 不认 slash 子命令）；
- **删掉 hooks 相关整段**（scout-block/privacy-block/dangerous-cmd-block 等），改为三条文字铁律：不自动 push/deploy、不读 `.env`/密钥、每轮改一处并先 commit；危险命令控制交给 DSH 的权限策略；
- 把 `/autoresearch` 调用语法改写为"当用户说'优化 X 到 Y''反复迭代直到指标 Z'时触发"。

**research-agora → 只挑 3–5 个验证类技能**：`paper-references`、`paper-verify-experiments`、`statistical-validator`、`proof-auditor`、`notation-consistency-checker`（源文件在 `plugins/verify/commands/*.md`）。做法同上：抽正文 → 加 `name/description` frontmatter → 放 `~/.dsh/skills/<kebab-name>/SKILL.md`，并把依赖的 `registry/`、`scripts/parse_latex.py`、`writing_verify.py` 一并拷到技能目录并改写路径。

**ARIS 的编排能力 → 自建一个薄 SKILL.md**：不要搬 `research-pipeline`（它调用 N 个 MCP 技能），而是写 `~/.dsh/skills/research-pipeline-mini/SKILL.md`，用 10 行描述 W1→W1.5→W2→W3 的阶段与产物（`IDEA.md`、`EXPERIMENT_PLAN.md`、`RESULTS/`、`NARRATIVE_REPORT.md`、`paper/`），每个阶段指名调用哪些已装的技能 + 用 DSH subagent 做"审稿人/审计员"角色。这比硬搬 87 个技能更可靠。

### 5.3 不要装（框架类）

Sakana AI-Scientist / v2、HKUDS AI-Researcher、AgentLaboratory、karpathy/autoresearch：**不是技能**，没有 `SKILL.md` 树。若确实要在 DSH 里用，只能：
- 写一个 `SKILL.md` 说明"先 `uv sync` / `pip install -e .` / `docker run …`，再执行 `python launch_scientist*.py …`"，把 DSH 当终端驱动器；或
- 把它们的 prompt 组织方式（如 Sakana 的 ideation prompt JSON、AgentLab 的 task-notes）抄进自己的 SKILL.md，**不引入代码**。

### 5.4 推荐装哪几个（Top 3 + 最小可用组合）

**Top 1｜ARIS 精选子集（策略 + 文献 + 写作）**
理由：87 个 SKILL.md、MIT、19.6k★、2026-11-19 仍在推、有真实 Python 工具与 CI；是唯一覆盖"选题→实验→审稿→论文"的完整技能生态。**只装 6–10 个纯 Markdown 技能**：`research-lit`、`arxiv`、`semantic-scholar`、`novelty-check`（需改写审稿环节）、`experiment-plan`、`analyze-results`、`paper-plan`、`paper-write`、`paper-compile`、`research-wiki`。

**Top 2｜K-Dense-AI/scientific-agent-skills（科研执行底座）**
理由：58.2k★、177 个 Agent Skills 标准技能、MIT（逐 skill license 需看）、2026-11-23 仍在更新；与 DSH 目录约定天然一致，可按需只装 3–5 个（如 `scanpy`、`pydeseq2`、`database-lookup`、`scientific-writing`、`paper-lookup`）。注意每个技能自带 `scripts/`，需要自行 `uv pip install` 对应依赖。

**Top 3｜uditgoenka/autoresearch（指标循环引擎）**
理由：MIT、6.9k★、SKILL.md 瘦路由 + 14 个自包含协议、有真实测试与状态机；改写成 1 个 DSH 技能成本最低，能补上 ARIS 缺失的"机械验证 + 自动回滚 + TSV 记账"闭环（Karpathy 那套）。

**不建议装**：brycewang AERS（聚合 + 营销 + license 口径乱，只在做社科实证时挑单个 skill）、research-agora（20★、命令式、需大改）、x-roocky（5★、停更）、四个 Python 框架。

> 与另一位 teammate（论文写作方向）的分工：本报告只判断"哪些文件能变成 SKILL.md / 哪些是命令或框架"；`paper-write`、`paper-compile` 等写作类技能的具体质量评估应以其报告为准，避免重复。

### 5.5 转换检查清单（每个技能入 DSH 前过一遍）

- [ ] 目录名 = `name` = kebab-case（如 `paper-write`）
- [ ] `description` 写清"做什么 + 何时用"，不依赖 slash 触发
- [ ] frontmatter 只留 `name`/`description`（保守），或确认 DSH 忽略额外键
- [ ] 删 `$ARGUMENTS`、`argument-hint`、`allowed-tools`、`version` 等 Claude 专属键
- [ ] 正文中的工具名/路径改为 DSH 约定（`pwsh`、`read`、`web_fetch`；Windows 路径用 `%USERPROFILE%` 或绝对路径）
- [ ] 外部依赖（MCP、GPU、LaTeX、pip 包、API key）在正文开头显式列为"前置条件/降级方案"
- [ ] 若技能含 `scripts/`、`references/`，正文明确"用 read 读取/用 pwsh 运行"，不要假设自动加载
- [ ] 在 DSH 里实测一次触发（说"用 xxx 技能"），确认能被 skill 目录匹配到

### 5.6 ARS（academic-research-skills）在 DSH 里的专门方案（lead 追问的结论）

**结论先行**：ARS 是"文献型 auto-research"最完整的实现（58,199★、13-agent 调研、10 阶段、7 类失败模式闸门、真实 showcase 产物、14 个 CI workflow），**值得当作"调研 + 写作 + 评审"流水线来用**；但（a）**不跑实验**，（b）**CC-BY-NC 4.0 禁止商业使用**，（c）整套是"技能套件"而非单文件技能，（d）现成 DSH 移植面向旧版 DSH 且丢失 hooks。三条落地路线：

1. **路线 A（最省事）——装社区移植，但先验证版本兼容**：
   ```bash
   dsh plugin --profile web add github:TY-Cheng/dsh-academic-research-skills#v0.4.7
   # 若 44.7.0 上加载失败，退回 v0.3.0 观察；或只拷 skills/ 下的单技能到 ~/.dsh/skills/
   ```
   注意：该 port 要求 DSH 0.2.x（实测 0.2.2-rc.5），本机 44.7.0 属跨大版本，**必须先试装并检查 23 个注册断言**；它会把 5 个技能 + 16 个命令注册进 `ctx.skills`，但 hooks（写范围 guard/SessionStart）不会生效。
2. **路线 B（推荐给"只想用其中一段"）——只取 `deep-research` 或 `academic-pipeline` 单技能**：
   `cp -r <repo>/deep-research ~/.dsh/skills/ars-deep-research`，改 frontmatter 为 DSH 最小格式；把该技能内引用的 `agents/*.md` 一并拷到 `~/.dsh/skills/ars-deep-research/agents/` 并在正文写"按阶段 read 对应 agent 文件、以内联角色提示执行"（移植就是这么做的：42 个 agent 提示默认内联）。第二段 `academic-pipeline` 需要 `shared/`（Schema 9 Material Passport、pipeline_state_machine.md 等）与 `scripts/`，建议整目录拷 + 在正文加一行 `ARS_ROOT=<绝对路径>` 约定。
3. **路线 C（最稳，但最像 ARIS 子集）——只用"验证类"技能**：`sr-screener`（PRISMA 筛选，4 agent，Python 解析 RIS/nbib/WoS/CSV）与 `academic-paper-reviewer`（5 席位评审）相对独立、对 hooks 依赖最小；`academic-pipeline` 的 2.5/4.5 完整性闸门可当作"审稿人 prompt + 检查清单"直接借用。
4. **不要做的事**：不要以为装了 ARS 就能自动跑实验——它明确"never runs experiments"；不要在商业项目里直接用（CC-BY-NC），需要时联系作者或只借鉴其公开方法论。

**与 uditgoenka/Karpathy 循环的关系（一句话）**：ARS 的循环是"**生成→评审→修改→再评审**"（评审信号来自 LLM 评审面板 + 引用/声明核验，带人工确认闸门）；Karpathy/uditgoenka 的循环是"**改动→机械指标→keep/discard**"（信号来自测试/benchmark，可完全无人值守）。前者能产出论文但需要人拍板，后者能无人值守但只会优化一个既有指标——在 DSH 里两者应当串联使用：uditgoenka 式循环负责"把实验/指标跑好"，ARS/ARIS 式流程负责"把证据组织成论文并接受审计"。

---

## 六、质量信号与风险清单（按严重度）

1. **【最高】"Claude Code 生态 ≠ DSH 生态"的错配风险**：ARIS 最核心的差异化能力（跨模型审稿 `auto-review-loop`、双盲引用核验 `citation-crosscheck`、端到端 `research-pipeline`）都通过 **Codex MCP / llm-chat MCP / slash command / hooks** 实现；原样搬进 DSH，技能会"看起来存在、实际空转"（模型读不到 MCP 工具，只能自己编审稿意见）。**这是比 star 数更重要的判断依据。**
2. **【高】许可证陷阱**：
   - Sakana AI-Scientist v1/v2：自定义许可证 + **强制 AI 披露条款**（3.2.e），若在 DSH 里跑出论文必须显著标注机器生成；
   - HKUDS/AI-Researcher：**仓库无 LICENSE**（`license: null`）→ 默认保留所有权利，不可直接商用/再分发；
   - karpathy/autoresearch：**无 LICENSE 文件**（README 自称 MIT），法律上以仓库为准；
   - brycewang AERS：API 标注 Other、README 标 CC BY-SA 4.0，且大量 vendored 社区技能，许可证需逐个回源；
   - K-Dense：仓库 MIT 但**每个 skill 有独立 license**（如 scanpy BSD-3-Clause），必须逐目录看 `license:` 字段；
   - **Imbad0202/academic-research-skills（ARS，58,199★）：CC-BY-NC 4.0（非商业）**——GitHub API 只标 `Other/NOASSERTION`，但 README 徽章与 LICENSE 正文都是 CC-BY-NC-4.0；其 DSH 移植（TY-Cheng）同样继承该许可，**商业场景不可直接用**。
3. **【高】安全**：skills 可以指示 agent 执行任意代码。ARIS 的 `install_aris.sh/.ps1` 会写 `CLAUDE.md` 并把技能符号链接进 `~/.claude/skills`（**不要直接搬到 DSH 上跑安装脚本**）；K-Dense README 自己也警告"Skills can execute code… Review what you install"。科研流水线还会执行 LLM 写的代码（Sakana 明确警告需容器化）——在 DSH 里应限制工作目录、禁用自动联网安装。
4. **【中】star 通胀与营销**：本领域高星不等于高质量。ARIS 8 个月 19.6k★、K-Dense 58.2k★（README 自称"250,000+ scientists"）、brycewang 描述 23,000+ vs README 1,151、uditgoenka README 带赞助位——请把这些当"热度信号"，不要当"质量证明"。**用文件树、SKILL.md 内容、测试/CI、license 交叉验证**。
5. **【中】陈旧**：Sakana v1/v2（2025-12-19 最后一次 push，约 11 个月）、AgentLaboratory（2025-08-20，约 15 个月）、x-roocky（2026-04-02）——依赖版本与模型列表已落后，直接跑容易踩坑。
6. **【中】"prompt-only"与"真自动化"的分界**：ARIS 87 个技能里，纯文字 prompt 占相当比例（如 `arxiv`、`paper-plan`、`grant-proposal`），真正"自动化"的是工具型技能（`experiment-queue`、`citation-crosscheck`、`figure-spec`）与编排技能（`research-pipeline`）。uditgoenka 的"自动化"来自循环纪律 + 机械 verification，不是领域智能。**没有任何一个候选能真正端到端产出可发表成果并自我验证**——Sakana 的"AI 通过 workshop 评审"是论文宣称，需自行复现。
7. **【低】DSH 侧未验证项**：DSH 是否容忍 frontmatter 额外字段、是否支持技能内 `references/` 自动加载、是否能挂 MCP——本次均未实测（只验证了本地 `dsh-probe-zz` 的最小格式）。转换时按"最小 frontmatter + 显式 read 指令 + 不依赖 MCP"的保守路线最稳。
8. **【中】ARS 的 DSH 移植是"三手 + 跨版本"**：上游维护者明确声明"已核实 vendored 文件一致、但**未审计移植代码、未运行过该移植**"；移植本身 fork 自另一个 port（nullptr-DZF），目标 DSH 为 **0.2.x（实测 0.2.2-rc.5）**，而本会话是 **44.7.0**；其记录的 e2e 只跑到 Stage 5、角色提示全内联、Stage 3/3′/5 检查点无独立用户决策记录。→ 试装前备份 profile，先只装单技能（如 `deep-research`），确认 23 个注册断言与 skill 目录可见后再扩展。
9. **【中】ARS 的质量宣称需打折**：评审面板当前 `NOT_CALIBRATED`；v3.8 claim-audit 的校准 runner 用"返回 gold 标签的 stub judge"，只验证工具不验证真实判断；完整性闸门检查的是"报告与过程"，作者明确不保证实验真伪/可复现（POSITIONING.md 自述边界）。→ 把它当"高质量写作/评审脚手架 + 检查清单"，不要当"可发表论文的保证"。

---

## 七、验证失败 / 未能核实的项（照实记录）

| 项 | 结果 | 处理 |
|---|---|---|
| `api.github.com/repos/huytieu/auto-research` | **HTTP 404** | 判定仓库不存在或已改名，不纳入 |
| `raw.githubusercontent.com/HKUDS/AI-Researcher/main/README.md` 首次 fetch | `TypeError: fetch failed`（网络瞬断） | 重试后 HTTP 200 成功，已引用 |
| ARIS `README.md`（241,471 B）与 `README_CN.md`（203,359 B） | 单次 web_fetch 会截断 | 改用 `SETUP_GUIDE.md`、`docs/SKILLS_CATALOG.md`、`api contents/skills`、`skills/analyze-results/SKILL.md` 组合取证 |
| ARIS 完整文件树 / K-Dense 完整 skills 列表 | GitHub API 返回体超过抓取显示上限（已落盘 spill 文件，本地统计：ARIS `skills/` 下 91 个目录，K-Dense 可见 122 个 `type:"dir"` 后被截断） | 技能数量采用仓库自述（ARIS 87、K-Dense 177），并在文中标注来源 |
| 各仓库 Releases / tag 详情 | 未逐一抓取（本次用 API `pushed_at` + README 徽章代替） | 报告中"最近更新"一律指 `pushed_at` |
| ARS 的 DSH 移植（TY-Cheng/dsh-academic-research-skills）实际安装与运行 | **未执行**（本任务只读，不安装插件） | 仅核实其 README/API 与上游对它的审查口径；兼容性（DSH 0.2.x → 44.7.0）留待试装验证 |
| ARS 的 `examples/showcase/` 实际产物质量 | 未逐篇打开（只核实其存在与作者对"旧版本、非当前性能"的标注） | 报告中不对其论文质量下结论 |

---

## 八、引用 URL 列表（全部为本次实际访问）

**ARIS**
- https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep
- https://api.github.com/repos/wanshuiyin/Auto-claude-code-research-in-sleep
- https://raw.githubusercontent.com/wanshuiyin/Auto-claude-code-research-in-sleep/main/SETUP_GUIDE.md
- https://raw.githubusercontent.com/wanshuiyin/Auto-claude-code-research-in-sleep/main/docs/SKILLS_CATALOG.md
- https://api.github.com/repos/wanshuiyin/Auto-claude-code-research-in-sleep/contents/skills
- https://api.github.com/repos/wanshuiyin/Auto-claude-code-research-in-sleep/contents/tools
- https://api.github.com/repos/wanshuiyin/Auto-claude-code-research-in-sleep/git/trees/main?recursive=1
- https://raw.githubusercontent.com/wanshuiyin/Auto-claude-code-research-in-sleep/main/skills/analyze-results/SKILL.md

**Imbad0202/academic-research-skills（ARS）及其 DSH 移植（lead 追加线索）**
- https://github.com/Imbad0202/academic-research-skills
- https://api.github.com/repos/Imbad0202/academic-research-skills
- https://raw.githubusercontent.com/Imbad0202/academic-research-skills/main/README.md
- https://raw.githubusercontent.com/Imbad0202/academic-research-skills/main/docs/ARCHITECTURE.md
- https://api.github.com/repos/Imbad0202/academic-research-skills/contents/
- https://doi.org/10.5281/zenodo.20696614（README 徽章 DOI）
- https://github.com/TY-Cheng/dsh-academic-research-skills（社区 DSH 移植，1★）
- https://api.github.com/repos/TY-Cheng/dsh-academic-research-skills
- https://raw.githubusercontent.com/TY-Cheng/dsh-academic-research-skills/main/README.md
- https://github.com/nullptr-DZF/dsh-academic-research-skills（移植的上游，37★）

**uditgoenka/autoresearch**
- https://github.com/uditgoenka/autoresearch
- https://api.github.com/repos/uditgoenka/autoresearch
- https://raw.githubusercontent.com/uditgoenka/autoresearch/master/README.md
- https://raw.githubusercontent.com/uditgoenka/autoresearch/master/.claude/skills/autoresearch/SKILL.md
- https://api.github.com/repos/uditgoenka/autoresearch/git/trees/master?recursive=1

**K-Dense-AI/scientific-agent-skills**
- https://github.com/K-Dense-AI/scientific-agent-skills
- https://api.github.com/repos/K-Dense-AI/scientific-agent-skills
- https://raw.githubusercontent.com/K-Dense-AI/scientific-agent-skills/main/README.md
- https://api.github.com/repos/K-Dense-AI/scientific-agent-skills/contents/skills
- https://raw.githubusercontent.com/K-Dense-AI/scientific-agent-skills/main/skills/scanpy/SKILL.md
- https://arxiv.org/abs/2609.00065（README 所引论文）
- https://agentskills.io/
- https://agent-plugins.org/

**brycewang-stanford/Auto-Empirical-Research-Skills**
- https://github.com/brycewang-stanford/Auto-Empirical-Research-Skills
- https://api.github.com/repos/brycewang-stanford/Auto-Empirical-Research-Skills
- https://raw.githubusercontent.com/brycewang-stanford/Auto-Empirical-Research-Skills/main/README.md

**rpatrik96/research-agora**
- https://github.com/rpatrik96/research-agora
- https://api.github.com/repos/rpatrik96/research-agora
- https://raw.githubusercontent.com/rpatrik96/research-agora/main/README.md
- https://api.github.com/repos/rpatrik96/research-agora/git/trees/main?recursive=1
- https://rpatrik96.github.io/research-agora

**x-roocky/ai-scientist-skills**
- https://github.com/x-roocky/ai-scientist-skills
- https://api.github.com/repos/x-roocky/ai-scientist-skills
- https://api.github.com/repos/x-roocky/ai-scientist-skills/git/trees/main?recursive=1

**SakanaAI/AI-Scientist 与 v2**
- https://github.com/SakanaAI/AI-Scientist
- https://api.github.com/repos/SakanaAI/AI-Scientist
- https://raw.githubusercontent.com/SakanaAI/AI-Scientist/main/README.md
- https://github.com/SakanaAI/AI-Scientist-v2
- https://api.github.com/repos/SakanaAI/AI-Scientist-v2
- https://raw.githubusercontent.com/SakanaAI/AI-Scientist-v2/main/README.md
- https://raw.githubusercontent.com/SakanaAI/AI-Scientist-v2/main/LICENSE
- https://api.github.com/repos/SakanaAI/AI-Scientist-v2/contents/

**HKUDS/AI-Researcher**
- https://github.com/HKUDS/AI-Researcher
- https://api.github.com/repos/HKUDS/AI-Researcher
- https://raw.githubusercontent.com/HKUDS/AI-Researcher/main/README.md
- https://arxiv.org/abs/2505.18705（README 所引论文）
- https://novix.science/chat（README 所提商用版）

**SamuelSchmidgall/AgentLaboratory**
- https://github.com/SamuelSchmidgall/AgentLaboratory
- https://api.github.com/repos/SamuelSchmidgall/AgentLaboratory
- https://raw.githubusercontent.com/SamuelSchmidgall/AgentLaboratory/main/README.md
- https://arxiv.org/pdf/2501.04227（README 所引论文）

**karpathy/autoresearch**
- https://github.com/karpathy/autoresearch
- https://api.github.com/repos/karpathy/autoresearch
- https://raw.githubusercontent.com/karpathy/autoresearch/master/README.md

**排除项**
- https://api.github.com/repos/MarsWise/scientific-agent-skills（K-Dense 的 fork，0★）
- https://api.github.com/repos/huytieu/auto-research（404）

**DSH 侧本地依据（非 URL）**
- `%USERPROFILE%\.dsh\skills\dsh-probe-zz\SKILL.md`（唯一 frontmatter 键为 `name` + `description`）
- `<DSH_INSTALL>\version`（`44.7.0`）

---

*报告结束。所有星数、日期、license 均为 2026-11-23 抓取快照，仅供决策参考；安装任何第三方技能前请再次核对仓库当前状态与实际 license。*
