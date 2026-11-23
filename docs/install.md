# 安装与运维

## 前置条件

- Python ≥ 3.10
- `PyYAML`（`python -m pip install pyyaml`）
- DeepSeek Harness（DSH）；默认技能根 `$DSH_HOME/skills`，未设置 `DSH_HOME` 时是 `~/.dsh/skills`

本仓库安装**不需要网络**：技能内容与 ARS 归档都在仓库内，安装器只做本地校验与复制。

## 快速开始

```powershell
python tools\dsh_skills.py doctor                 # 环境/锁文件/归档/DSH 目录体检
python tools\dsh_skills.py install --mode full    # 安装全部 15 个（有备份；事务失败自动回滚）
python tools\dsh_skills.py verify --require-all   # 逐文件 sha256 + frontmatter 校验
```

安装完成后 DSH 会在下一个模型步骤自动发现技能（文件系统 provider 有 watch），无需重启。

## 常用操作

### 只装一部分

```powershell
# 预设：minimal / writing / full（默认 full）
python tools\dsh_skills.py install --mode minimal

# 精确指定
python tools\dsh_skills.py install --only academic-paper,deep-research,citation-management

# 从预设里排除
python tools\dsh_skills.py install --mode full --exclude sr-screener,scientific-visualization

# 只打印计划，不写任何文件
python tools\dsh_skills.py install --mode full --dry-run
```

### 查看状态

```powershell
python tools\dsh_skills.py list          # 表格：技能 / 安装状态 / 许可证 / 类别
python tools\dsh_skills.py list --json   # 机器可读
python tools\dsh_skills.py verify        # 缺失只警告；被改动/被篡改会失败
```

状态含义：

- `ok`：已安装且与锁文件逐字节一致（技能目录内的 `__pycache__/`、`*.pyc` 等运行时文件不参与比对）；
- `drifted`：已安装但内容与锁文件不一致（可能被手动改过，或版本升级后未重装）；
- `broken`：目录存在但无法校验（缺 SKILL.md 等）；
- `absent`：未安装。

### 自定义 DSH 目录

```powershell
python tools\dsh_skills.py install --mode full --dsh-home D:\dsh-profile
# 等价环境变量：$env:DSH_HOME = 'D:\dsh-profile'
```

> 安装器拒绝把技能装进仓库自身（防止误覆盖）。

### 升级 / 重装

```powershell
# 内容有变化的技能会自动备份旧版本并替换；内容相同的会跳过
python tools\dsh_skills.py install --mode full

# 强制重装全部
python tools\dsh_skills.py install --mode full --force
```

### 备份与恢复

被替换的旧版本会移动到：

```
$DSH_HOME/skills-backup/<YYYYMMDD-HHMMSS>/<skill>/
```

恢复某个技能：

```powershell
$backup = Get-ChildItem "$env:DSH_HOME\skills-backup" | Sort-Object Name -Descending | Select-Object -First 1
Remove-Item -Recurse -Force "$env:DSH_HOME\skills\deep-research"
Move-Item "$backup\deep-research" "$env:DSH_HOME\skills\deep-research"
```

### 卸载

```powershell
python tools\dsh_skills.py uninstall --names deep-research --keep   # 演练：只打印
python tools\dsh_skills.py uninstall --names deep-research          # 删除并备份
python tools\dsh_skills.py uninstall --names a,b,c --no-backup      # 删除且不留备份
```

## 完整性模型

- `manifests/skills.lock.json` 记录 15 个技能中**每个文件**的 sha256 与字节数；
- `vendor/ars-dsh-*.tar.gz` 的 sha256 也记录在锁文件 `sources.ars` 中；
- `install` 时：先校验归档 sha256 → 解压（拒绝绝对路径/`..`/链接）→ 按锁文件校验每个技能 →
  装配到临时目录 → 再原子换入；
- `verify` 时：对已安装目录逐文件比对 sha256，并重新解析 frontmatter 检查 DSH 规则；
- 任何一步失败都会以非 0 退出码结束，且不会留下半安装状态：安装阶段会把已替换的技能回滚。
  `--no-backup` 仍是事务性的（被替换副本先暂存），只是安装成功后不再保留备份。
  进程被强制杀死时可能残留 `~/.dsh/.dsh-skills-staging-*` 临时目录，可安全删除。

退出码：`0` 成功；`1` verify/selftest/doctor 检查失败（含已安装文件哈希不符）；
`2` 用法或配置错误（参数非法、路径不可写等）；`3` 安装阶段的来源完整性错误
（归档/载荷哈希不符、归档含不安全成员）。

## 排障

| 现象 | 原因 / 处理 |
|---|---|
| `ERROR: lock file not found` | 在仓库根目录外运行了；`cd` 到仓库根再执行 |
| `missing ARS archive` / `sha256 mismatch` | 仓库文件被改动或未完整克隆（如 LFS/离线拷贝残缺）；重新 `git checkout -- vendor/` |
| 安装成功但 DSH 里看不到技能 | ① `DSH_HOME` 指错；② 装到了项目级根而当前项目不是那个目录；③ 技能 frontmatter 不合法（用 `verify` 能看到具体原因）；④ DSH 用的是别的 profile |
| `drifted` | 技能被手动修改或来自旧版本；`install --force` 重装即可，旧版本在 `skills-backup/` |
| 模型不自动选某个技能 | 该技能可能带 `disable-model-invocation: true`（本仓库所有顶层 `SKILL.md` 已移除该键；`autoresearch/references/` 下保留的上游命令文件不参与 DSH 发现）；或描述与任务不匹配 |
| `pip install pyyaml` 失败（公司网络） | 用内网源，或使用 DSH 自带的 Python 环境；安装器只依赖 PyYAML 一个第三方包 |
| Windows 下 `os.replace` 报权限错误 | 关闭占用该目录的程序/编辑器后重试；安装器会回滚 |
| `verify` 报 `UNKNOWN:` | `$DSH_HOME/skills` 下有不在本仓库清单里的技能目录（可能来自其他来源）；仅提示，不影响结果 |

## 离线 / 内网部署

1. 在可联网机器上 clone 本仓库，或直接拷贝整个目录到内网（仓库已包含全部技能内容）；
2. 内网机器装好 Python 与 PyYAML；
3. 运行 `python tools/dsh_skills.py install --mode full`，其余步骤相同。

## 与 DSH 技能的兼容性

本仓库技能遵循 DSH 技能规范（详见 [dsh-skill-spec.md](dsh-skill-spec.md)）：一层目录、
`<name>/SKILL.md`、`name` kebab-case、`description` 非空。安装器会在安装时再次校验这些规则。
