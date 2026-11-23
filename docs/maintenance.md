# 维护手册

本仓库的核心不变量：

1. `skills/` 与 `vendor/ars-dsh-*.tar.gz` 里的内容 = **安装后 `$DSH_HOME/skills/<name>/` 的字节**；
2. `manifests/skills.lock.json` 记录每个文件的 sha256 与来源 commit；
3. `python tools/build_lock.py --check` 在纯仓库内容上自洽（CI 会跑）；
4. 升级任何第三方内容都必须显式更新 `tools/build_lock.py` 的 `SOURCES` 常量并重新生成锁文件，
   以便 review 时直接 diff 出"升级了什么"。

## 工具

| 文件 | 作用 |
|---|---|
| `tools/build_lock.py --from-installed` | 从已安装的 DSH 技能重建 ARS 归档 + 锁文件（首次生成/升级时用） |
| `tools/build_lock.py --check` | 仅用仓库内容重建并比对锁文件（CI 用） |
| `tools/dsh_skills.py selftest` | 校验仓库内容：frontmatter、哈希、归档安全 |
| `tools/dsh_skills.py install/verify` | 端到端安装与校验 |

## 升级某个上游技能

以 K-Dense 为例：

1. 查上游最新 commit：`gh api repos/K-Dense-AI/scientific-agent-skills/commits/main --jq .sha`；
2. 更新 `tools/build_lock.py` 的 `SOURCES["kdense"]["commit"]`；
3. 通过 jsDelivr / git 拉取新版本技能文件到 `skills/<name>/`（保留 DSH-PORT.md 约定）：
   - 重新插入 DSH 移植说明（工具映射、`$ARGUMENTS` 说明、来源/commit/许可证）；
   - 检查正文引用的相对资源是否齐全；
4. 在开发机上把新技能安装到 `$DSH_HOME/skills/<name>`（或临时 `--dsh-home`），
   运行 `python tools/build_lock.py --from-installed` 重新生成归档与锁文件；
5. 运行 `python tools/dsh_skills.py selftest`、`build_lock.py --check`、单元测试；
6. 更新 `THIRD-PARTY.md` 的 commit 与 `CHANGELOG.md`，提交。

> 只有 ARS 需要重建归档；其余技能是明文目录，直接替换 `skills/<name>/` 后重新生成锁文件即可。

## 新增一个自有技能

1. 新建 `skills/<name>/SKILL.md`，frontmatter 至少：

   ```yaml
   ---
   name: <kebab-case-name>
   description: 做什么 + 何时用（模型靠它路由）
   metadata:
     version: "0.1.0"
   ---
   ```

2. 在 `tools/build_lock.py` 的 `SKILL_SPECS` 里登记 `("<source>", "<category>", "copy")`；
   - 自有内容用 `local` source（MIT）；
   - 第三方内容加对应的 `SOURCES` 条目并在 `THIRD-PARTY.md` 记录。
3. 把技能名加入需要的 preset（`PRESETS`）。
4. `python tools/build_lock.py --from-installed` 重新生成锁文件（普通技能直接从仓库 `skills/` 读取；
   只有 ARS 的 tar 技能需要已安装在 `$DSH_HOME/skills`，因为需要重建归档）。
5. 跑一遍 `selftest` 与测试，提交。

## 本地完整验证

```powershell
python tools\dsh_skills.py selftest
python tools\build_lock.py --check
python -m unittest discover -s tests -v

$tmp = Join-Path $env:TEMP ("dsh-skills-test-" + [guid]::NewGuid())
python tools\dsh_skills.py install --mode full --dsh-home $tmp --no-backup
python tools\dsh_skills.py verify --dsh-home $tmp --require-all
python tools\dsh_skills.py uninstall --names academic-paper --dsh-home $tmp --keep
Remove-Item -Recurse -Force $tmp
```

CI（`.github/workflows/validate.yml`）在 Linux/Windows × Python 3.10/3.12 上执行同样的检查。

## 发布流程

1. 确认 `CHANGELOG.md` 已更新，锁文件已重新生成；
2. `git tag v0.1.0 && git push --tags`；
3. 若 `git push` 因网络失败（本机到 github.com 的 443 可能被重置），使用 API 兜底：
   - 已有工具 `ai-paper-radar/scripts/publish_api.py` 的思路：把本地领先 origin 的提交用
     GitHub REST API（blobs → tree → commit → ref）发布；
   - 认证用 `gh auth token`（本机 gh 已登录 hhxpoint）或 `GITHUB_TOKEN` 环境变量；
   - 发布后必须核对远端 commit SHA 与本地一致，再删除本地临时分支。
4. 发布后检查 GitHub Actions 的 validate 是否为绿。

## 版本与兼容性

- 技能内容版本跟随上游 commit；本仓库自身用语义化版本（CHANGELOG）。
- DSH 技能规范变化时，更新 `docs/dsh-skill-spec.md` 与安装器的校验逻辑，并在 CHANGELOG 记录。
- 破坏性变更（例如技能改名、preset 调整）需要 major 版本，并在 README 写明迁移方式。

## 回滚

- 单次安装回滚：旧技能在 `$DSH_HOME/skills-backup/<时间戳>/`，移动回去即可；
- 仓库回滚：`git revert <commit>` 后重新 `install`，或 checkout 上一个 tag 再安装；
- 第三方许可证变化：同步更新 `THIRD-PARTY.md` 与 `vendor/licenses/`，必要时把技能从 preset 移除。
