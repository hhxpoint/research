# DSH 技能规范与移植指南（实测版）

> 适用：DeepSeek Harness 44.7.0（Windows / Linux）。本文结论来自对 DSH 自带
> `dsh-skill` / `dsh-skill-filesystem` 加载器源码的阅读，以及对 19+ 个真实 SKILL.md 的实测，
> 与 Claude Code / OpenAI Codex 的 skills 规范**不完全相同**。

## 1. 技能放在哪

DSH 按优先级扫描以下根（由 `dsh-skill-filesystem` 提供，provider 已内置）：

| 优先级 | 位置 | 说明 |
|---|---|---|
| 100 | `<项目根>/.dsh/skills` | 项目级；项目根 = 最近的包含 `.git` 的祖先目录，没有则用当前工作目录 |
| 200 | `<项目根>/.agents/skills` | 项目级、跨 agent 通用 |
| 300 | `customSkillDirs`（配置项） | 自定义目录 |
| 400 | `$DSH_HOME/skills`（默认 `~/.dsh/skills`） | **用户级，最常用**；`.system` 子目录会被跳过 |
| 500 | `$DSH_AGENTS_HOME/skills`（默认 `~/.agents/skills`） | 另一用户级根 |
| 600 | `bundledSkillDir` | 内置技能根（如 office 技能） |

**只扫描一层**，只有两种合法形态：

```
<root>/<name>/SKILL.md      # 目录 bundle（推荐）
<root>/<name>.md            # 扁平文件（也认，但相对资源路径会变成根目录）
```

`<root>/a/b/SKILL.md` 这种嵌套**永远不会被发现**。目录名不必等于 skill name，
但建议保持一致便于维护。

## 2. frontmatter 规则

文件第一行必须恰好是 `---`，到下一个独立 `---` 行为 frontmatter，之后是 Markdown 正文。
YAML 必须是映射（mapping）。

| 字段 | 必填 | 说明 |
|---|---|---|
| `name` | ✅ | 必须匹配 `^[a-z0-9]+(-[a-z0-9]+)*$`（小写 kebab-case） |
| `description` | ✅ | 非空字符串；模型用它判断何时加载 |
| `whenToUse` | 可选 | 额外触发说明，会进入目录摘要 |
| `metadata` | 可选 | 任意映射，原样保留（适合放 version/source） |
| `disable-model-invocation` | 可选 | `true` 时模型不会自动选中，只能用户显式调用 |
| `user-invocable` | 可选 | 是否出现在人类可用的命令面板 |

**被容忍但忽略的字段**：`license`、`compatibility`、`allowed-tools`、`argument-hint`、
`version`、`allowedTools` 等——不报错、不生效。可以保留（便于上游同步），但不要指望它们有作用。

**会被静默丢弃（只打一条 warn 日志）的情况**：

1. YAML 语法错误。最常见：`description` 里含 `: `（冒号+空格）却没有整体加引号，例如
   `description: USE only for: dashboards` → 解析失败，技能消失。
2. `name` 缺失、为空、含下划线/大写/中文。
3. `description` 缺失或为空。
4. 使用驼峰写法的调用策略键：`disableModelInvocation` / `modelInvocable` / `userInvocable`
   ——加载器显式拒绝，必须改成 kebab-case（`disable-model-invocation` / `user-invocable`）。

> 失败时模型目录里**看不到任何报错**，表现就是"技能没出现"。排查顺序：根目录对不对 →
> 目录深度 → `SKILL.md` 首行 → YAML 能否解析 → name 正则 → 描述是否为空。

## 3. 加载与资源

- 会话开始时注入技能目录（name + description 摘要），模型按需调用 `skill` 工具加载正文。
- 加载后返回 `<skill_content>`，并给出**资源基准目录**：技能目录内的 `references/`、`scripts/`、
  `assets/` 等相对路径可以用 `read` / `pwsh` 访问。
- 因此：技能正文引用的相对资源必须落在**该技能目录内部**。上游如果引用仓库根目录的 `shared/`，
  移植时要把 `shared/` 合并进每个技能目录（本仓库的 ARS 技能就是这样处理的）。
- 文件系统 provider 会 watch 这些根：新增/改名/删除技能、修改 frontmatter 会在下一步自动生效，
  不需要重启 DSH；正文修改在下次加载时读取。

## 4. 与 Claude Code skills 的差异（移植清单）

| Claude Code 资产 | 在 DSH 中 | 移植动作 |
|---|---|---|
| `.claude-plugin/marketplace.json`、`/plugin install` | 不存在 | 改为本仓库式目录 + 安装脚本 |
| `.claude/commands/*.md`（slash 命令） | 不加载、`/xxx` 不可用 | 并入 SKILL.md，或移到 `references/` 由正文指示读取 |
| `.claude/agents/*.md`（subagent 定义） | 不加载 | 写进正文角色说明；需要独立视角时用 DSH `subagent` 工具 |
| `.claude/hooks/*`（PreToolUse 等） | 不生效 | 改成正文中的硬性约束 + 由 DSH 权限策略兜底 |
| `allowed-tools` | 忽略 | 删除或保留（无效果） |
| `$ARGUMENTS`、`argument-hint` | 不替换 | 正文注明"参数取自用户当前消息" |
| MCP server（如 Codex MCP） | 本仓库未依赖 | 依赖 MCP 的流程在 DSH 中降级为人工/子代理替代 |
| `AskUserQuestion` | 无同名工具 | 改为 `ask_user_question` 或直接向用户提问 |
| 工具名 `Read/Write/Edit/Bash/WebFetch` | DSH 工具名不同 | 映射为 `read/write/edit/pwsh/web_fetch` |

## 5. 移植操作（本仓库做法）

对每个上游技能：

1. 复制整个技能目录（含 `references/`、`scripts/`、`assets/`）。
2. 保留上游 frontmatter 原样；只确认 `name` 合法且等于目录名、`description` 非空。
3. 在正文前插入一段 **DSH 移植说明**（工具映射、不支持的机制、相对资源说明、来源/commit/许可证）。
4. 合并上游仓库根目录被引用的共享资源（如 ARS 的 `shared/`）。
5. 改写指向非技能目录的路径（如 `../../commands/x.md` → `references/commands/x.md`）。
6. 写入 `DSH-PORT.md` 记录来源、commit、许可证、修改点、卸载方式。
7. 在锁文件里记录每个文件的 sha256；安装器安装的就是这份字节。

## 6. 快速自检

验证技能能被发现（会把 `PROBE_OK` 注入为技能说明）：

```powershell
$probe = Join-Path $env:DSH_HOME 'skills\dsh-probe-zz\SKILL.md'
New-Item -ItemType Directory -Force (Split-Path $probe) | Out-Null
@"
---
name: dsh-probe-zz
description: Temporary probe skill to verify DSH skill discovery. Load only when explicitly asked.
---
PROBE_OK
"@ | Set-Content -Encoding utf8 $probe
```

随后在 DSH 会话里让模型"加载 dsh-probe-zz 技能"；能读到正文即说明 provider 正常。
用完删除该目录即可（watch 会自动从目录中移除）。

校验本仓库全部技能（含归档）是否符合规范并自洽：

```powershell
python tools\dsh_skills.py selftest
```
