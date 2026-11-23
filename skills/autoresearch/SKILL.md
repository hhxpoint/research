---
name: autoresearch
description: "Autonomous iteration loop: modify, verify, keep/discard against any metric"
version: 2.3.0
---
> **DSH 移植说明 / DSH port note**（非上游正文，仅为运行适配）
>
> - 工具名映射 / tool mapping: `Read`→`read`, `Write`→`write`, `Edit`→`edit`, `Grep`→`grep`, `Glob`→`glob`, `Bash`→`pwsh`, `WebFetch`→`web_fetch`, `Task`/agents→`subagent`, `AskUserQuestion`→`ask_user_question`.
> - Claude Code 专属的 slash commands、hooks、MCP server、`allowed-tools` 在 DSH 中不存在；遇到时按本文件的方法论执行，并使用当前会话可用的工具。
> - 上游正文中的 `$ARGUMENTS` 只是 Claude Code 的占位符，DSH 不会替换；任务参数请取用户当前消息。
> - 技能目录内的 `references/`、`scripts/`、`shared/` 等相对路径资源已随目录安装，可直接用 `read` / `pwsh` 访问。
> - 版权、许可证原文与修改说明见同目录 `NOTICE.md`、`LICENSE.txt`、`DSH-PORT.md`。
> - 来源 / source: https://github.com/uditgoenka/autoresearch ｜ 许可证 / license: MIT ｜ commit: `7bddd056dfd0b0ded8360588d8101b1ecb5c0baa` ｜ 导入: 2026-11-23

# Autoresearch — Autonomous Goal-directed Iteration

## Safety Invariants (all subcommands)
- Never push, publish, or deploy without explicit user approval.
- Bounded by default. Override with `Iterations: unlimited`.
- All results logged to `autoresearch/{subcommand}-{YYMMDD}-{HHMM}/` directory.
- Chain handoff via `handoff.json`. Evals reads `*-results.tsv`.

## Dispatch (bare `/autoresearch`)

Parse the invocation in this order:

| Condition | Mode |
|---|---|
| `Metric:` or `Verify:` present | **Classic** — existing metric loop, unchanged |
| Free-form natural-language goal, no metric/verify | **Orchestrator** — see Orchestrator section |
| Nothing | **Setup wizard** — interactive config builder |
| `--classic` flag | Force Classic regardless of goal text |
| `--auto` flag | Force Orchestrator regardless of goal text |

Print a banner on every invocation: `[autoresearch] mode: classic | orchestrator | wizard`.

## Subcommands

| Command | Does | Default Iterations |
|---|---|---|
| `/autoresearch` | Iterate against a metric: modify → verify → keep/discard | 25 |
| `/autoresearch:plan` | Convert a goal into validated Scope, Metric, Verify config | N/A |
| `/autoresearch:debug` | Hunt bugs: hypothesize → test → falsify → repeat | 15 |
| `/autoresearch:fix` | Crush errors one-by-one until zero remain | 20 |
| `/autoresearch:security` | STRIDE + OWASP audit with red-team personas | 15 |
| `/autoresearch:ship` | Ship through 8 phases: checklist → dry-run → deploy → verify | N/A |
| `/autoresearch:scenario` | Generate edge cases across 12 dimensions | 20 |
| `/autoresearch:predict` | 5 expert personas debate before implementation | N/A |
| `/autoresearch:learn` | Scout codebase → generate docs or wiki → validate → fix loop | 10 |
| `/autoresearch:reason` | Adversarial debate with blind judges until convergence | 8 |
| `/autoresearch:probe` | 8 personas interrogate requirements until saturation | 15 |
| `/autoresearch:improve` | Research ICP challenges, discover improvements, generate PRDs | 15 |
| `/autoresearch:evals` | Analyze iteration results: trends, plateaus, regressions | N/A |
| `/autoresearch:regression` | Regression stability gate: baseline vs candidate, verdict STABLE/UNSTABLE | N/A |

### Subcommand routing

To run a subcommand yourself (an orchestrator hop or a `--chain` target), Read its protocol file and follow it:
`references/commands/<name>.md` (relative to this skill's directory), or `references/commands/autoresearch.md` for the classic loop.
The commands are user-typed only, so the model loads them from here instead of invoking them.

## Universal Flags

| Flag | Applies To | Purpose |
|---|---|---|
| `Iterations: N` | All looping | Set iteration count |
| `Iterations: unlimited` | All looping | Opt-in unbounded |
| `--evals` | All looping | Mid-loop checkpoints + final summary |
| `--evals-interval N` | All looping | Override checkpoint frequency |
| `--chain <targets>` | All | Sequential handoff after completion |
| `--<subcommand>` | All | Shorthand for `--chain <subcommand>` |
| `--dry-run` | Orchestrator | Print derived config + planned pipeline; no execution |
| `--max-cycles N` | Orchestrator | Hard ceiling on orchestration cycles (default 50) |
| `--classic` | Bare `/autoresearch` | Force Classic metric-loop mode |
| `--auto` | Bare `/autoresearch` | Force Orchestrator mode |
| `--no-fork` | Metric loops | Disable fork-and-flush rounds |
| `Forks: K` | Metric loops | Branches per fork-and-flush round (default 4; 2 when Verify is slow or uses a shared resource) |
| `Guided: R` | Metric loops | Fraction of fork branches given an Advisor-assigned experiment (default 0.5; 0 = all random) |

## Getting Unstuck: Fork-and-Flush

Metric loops run fork-and-flush rounds on a fixed schedule: at 33% and 66% of the budget, plus early when 5
iterations pass with no `keep`. A round forks K fresh-context branches from the best commit so far, runs each
for a small budget, and keeps the winner. A fresh context means the files and results log only, with none of
the leader's reasoning. Half the branches (by default) are random and pick their own ideas; the other half are
guided, each given one distinct experiment by a stateless Advisor that reads the results log. Protocol:
`references/fork-and-flush.md` (arXiv:2610.07447, arXiv:2610.07625).

## Orchestrator

Activated when a plain-language goal is given without `Metric:`/`Verify:`. Classifies the goal into a **Goal archetype** — see `references/orchestrator-routing.md` for the archetype table and router decision table.

Resolve every `scripts/...` path below relative to this installed skill directory, never relative to the caller's working directory.

For performance, latency, throughput, runtime, CPU, memory, allocations, binary
size, power, energy, bandwidth, or compute-cost goals, read
`references/behavior-preserving-optimization.md`. The working metric ranks
candidates; independent behavior evidence decides whether a candidate survives.

**Two modes based on archetype:**
- **Orchestration loop** — predicate-bearing archetypes (ship-ready, optimize-metric, fix-broken, harden, build-feature, explore). Goal has a mechanical Success predicate; the loop runs until that predicate is met.
- **Single-pass dispatch** — subjective/terminal archetypes (document, what-to-build, decide-design). Routes once to the fitting subcommand (learn / improve / reason), lets it self-terminate, then reports. No loop, no Plateau, no ship gate.

### Orchestration Loop Steps

Backed by `scripts/orchestrate.sh` (deterministic seam — all routing logic lives there). Subcommands exposed: `classify`, `next-hop`, `units`, `plateau`, `screen-cmd`, `verdict`, `validate-state`, `screen-state-predicate`.

1. **Classify** — `scripts/orchestrate.sh classify "<goal>"` → archetype label + mode.
2. **Derive predicate** — reuse `plan` logic to produce a concrete Success predicate: exact shell command + expected output. For `optimize-metric`, run the full plan/wizard derivation internally.
3. **Confirm** — ONE `AskUserQuestion` showing: archetype, mode, concrete predicate (command + expected output), terminal choice (stop-at-verified vs proceed-to-ship). Misclassifications are caught here, not mid-run.
4. **Round-0 dry-run** — prove the predicate command runs and returns a value; safety-screen every derived command via `screen-cmd`; print projected cycle budget. Stop here if `--dry-run`.
5. **Loop** until predicate satisfied:
   a. Assess state via cheap signals (last `handoff.json`, regression verdict, error count) + affected-test verify.
   b. `scripts/orchestrate.sh next-hop orchestrator-state.json` → next subcommand.
   c. Run subcommand via Subcommand routing (its own bounded inner loop).
   d. Record per-hop outcome ∈ {progressed, no-op, failed, blocked}.
   e. Fold hop's `handoff.json` into `orchestrator-state.json`.
   f. `scripts/orchestrate.sh units` → recompute **Units remaining** and append the number or `unknown` to the state's `units_remaining` array.
6. **Stop conditions** (checked after each hop):
   - Predicate met → ship gate (only if ship is in the pipeline) else `CONVERGED`.
   - Cycles > ceiling (default 50, override `--max-cycles N`) → stop + report `CEILING`. Checked first: a reached ceiling is never extended by fork rounds.
   - `scripts/orchestrate.sh plateau orchestrator-state.json` → exit 0 (flat): unless `--no-fork` or `fork_rounds_since_progress` is already 2, run one fork-and-flush round from the incumbent (`references/fork-and-flush.md`), add 1 to `fork_rounds_since_progress`, and continue; otherwise stop + report `PLATEAU`. Exit 1: continue. Exit 3: stop + report `BLOCKED`.
   - Hop outcome `blocked`/`failed` with no alternative route → checkpoint + stop + report `BLOCKED`.

### Orchestrator State

`orchestrator-state.json` — orchestrator-owned, additive. Tracks: goal, archetype, predicate, terminal-choice, `units_remaining` history, cycle count, per-hop pipeline log with outcomes, current incumbent, `fork_rounds_since_progress` (reset to 0 whenever units improve). Each hop's `handoff.json` is unchanged (single-hop bridge); the orchestrator reads it and folds it in. Two clearly-owned state objects, no overlap.

### Orchestrator Safety Invariants

- **Never auto-approve ship/deploy/push.** The orchestrator never passes `--auto` to `ship`; deploy always requires explicit user approval.
- **Data-migration behind anchored DB-URL allowlist.** Reuses regression's allowlist — host must be `localhost`/`127.0.0.1`/container hostname, or database name carries `_test`/`_ci` suffix. Bare substring match does not qualify. Anything else refused.
- **screen-cmd on every derived command** — run before the loop starts AND on every command read from a persisted state file on resume. Persisted commands are never trusted; resume re-screens the pinned predicate via `screen-state-predicate` and refuses on `refuse`.
- **No un-screened commands mid-loop.** The autonomous loop cannot introduce new shell commands that bypass `screen-cmd`.
- **Predicate pinned, not re-derived.** Round-0 writes the derived Success predicate verbatim into `orchestrator-state.json`; every cycle and every resume reuses that exact string so "done" is reproducible across runs.
- **Validate the ledger before routing.** `validate-state` gates `orchestrator-state.json` (required fields + coarse types); a malformed ledger is not trusted to route from.
- **Independent verify before convergence.** High-impact changes accepted on the working signal set `pending_verify`; `next-hop` routes to a `verify` hop (held-out / adversarial check) before `DONE` or ship. The verify hop never auto-approves ship.
- **Unknown-units cycles excluded from Plateau counter.** A cycle where `units` returns `unknown` (e.g. runner crash) is not counted as zero-progress; repeated `unknown` routes to `BLOCKED`.

## DSH 使用说明（本地适配）

- 本技能没有 slash 命令：当用户说「用 autoresearch 把 X 优化到 Y」「反复迭代直到指标达到 Z」时，直接按本文件执行。
- 子命令协议位于本技能目录的 `references/commands/<name>.md`（plan / debug / fix / security / ship / scenario / predict / learn / reason / probe / improve / evals / regression），需要时用 `read` 读取对应文件。
- Claude Code hooks（危险命令拦截、隐私拦截、上下文注入）未移植：Safety Invariants 中的约束必须由你显式遵守，不得自动 push/deploy、不得读取 `.env` 或密钥；危险命令由 DSH 权限策略兜底。
- 每轮结果与记账写入用户指定目录（默认 `autoresearch/<subcommand>-<YYMMDD>-<HHMM>/`），并在回复里给出 keep/revert 结论。
