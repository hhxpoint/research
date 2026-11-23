---
name: analyze-results
description: Analyze ML experiment results, compute statistics, generate comparison tables and insights. Use when user says "analyze results", "compare", or needs to interpret experimental data.
argument-hint: "[results-path-or-description]"
allowed-tools: Bash(*), Read, Grep, Glob, Write, Edit
---
> **DSH 移植说明 / DSH port note**（非上游正文，仅为运行适配）
>
> - 工具名映射 / tool mapping: `Read`→`read`, `Write`→`write`, `Edit`→`edit`, `Grep`→`grep`, `Glob`→`glob`, `Bash`→`pwsh`, `WebFetch`→`web_fetch`, `Task`/agents→`subagent`, `AskUserQuestion`→`ask_user_question`.
> - Claude Code 专属的 slash commands、hooks、MCP server、`allowed-tools` 在 DSH 中不存在；遇到时按本文件的方法论执行，并使用当前会话可用的工具。
> - 上游正文中的 `$ARGUMENTS` 只是 Claude Code 的占位符，DSH 不会替换；任务参数请取用户当前消息。
> - 技能目录内的 `references/`、`scripts/`、`shared/` 等相对路径资源已随目录安装，可直接用 `read` / `pwsh` 访问。
> - 版权、许可证原文与修改说明见同目录 `NOTICE.md`、`LICENSE.txt`、`DSH-PORT.md`。
> - 来源 / source: https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep ｜ 许可证 / license: MIT ｜ commit: `4ba94ae2a1c1fbbb14858750dd8764cabf6c28bd` ｜ 导入: 2026-11-23

# Analyze Experiment Results

Analyze: $ARGUMENTS

## Workflow

### Step 1: Locate Results
Find all relevant JSON/CSV result files:
- Check `figures/`, `results/`, or project-specific output directories
- Parse JSON results into structured data

### Step 2: Build Comparison Table
Organize results by:
- **Independent variables**: model type, hyperparameters, data config
- **Dependent variables**: primary metric (e.g., perplexity, accuracy, loss), secondary metrics
- **Delta vs baseline**: always compute relative improvement

### Step 3: Statistical Analysis
- If multiple seeds: report mean +/- std, check reproducibility
- If sweeping a parameter: identify trends (monotonic, U-shaped, plateau)
- Flag outliers or suspicious results

### Step 4: Generate Insights
For each finding, structure as:
1. **Observation**: what the data shows (with numbers)
2. **Interpretation**: why this might be happening
3. **Implication**: what this means for the research question
4. **Next step**: what experiment would test the interpretation

### Step 5: Update Documentation
If findings are significant:
- Propose updates to project notes or experiment reports
- Draft a concise finding statement (1-2 sentences)

## Output Format
Always include:
1. Raw data table
2. Key findings (numbered, concise)
3. Suggested next experiments (if any)
