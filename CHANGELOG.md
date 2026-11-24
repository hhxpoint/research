# Changelog

本仓库遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 与语义化版本。

## [0.3.0] - 2026-11-24

### Added

- 新增原创技能 `research-craft`：从高星科研技能/方法论中提炼的可执行手艺规则，五册 references：
  **作图**（诚实编码/误差/可访问性/导出 provenance）、**写作**（故事脊柱/摘要/证据绑定/返修）、
  **实验设计**（claim→证据/反 claim/基线公平/预算终止）、**实验观察**（run 记录/sanity/异常 triage/复现）、
  **现象理解**（观察与解释分离/替代解释/探针/claim 强度）。
- `auto-research` 与 craft 绑定：各阶段指向对应手册；`RESULTS.md` 新增 `## Observations` 并要求四节齐全。
  auto-research 的 6 个模板加入 craft 手册指针（设计/观测/写作/审稿/返修/提交检查）。
- `research-stack` 增加 `research-craft` 路由；`minimal` 预设加入 `research-craft`；技能总数 16 → 17。
- 新增 `docs/research-craft.md`：星标快照、来源、提炼方法、五册索引与维护方式。
- 新增 research-craft 内容测试（五册存在/关键规则覆盖），测试总数 68 → 69。

## [0.2.1] - 2026-11-24

### Fixed / Hardened

- auto-research 反绕过加固：`state.json.history` 连续性校验（手工改 `phase` 判为状态损坏，退出码 3）；
  `citations.json` 重复 id 检测；`claim_map.json` 的 `evidence` 路径必须真实存在（支持 glob 与 http/doi/arxiv 链接）、
  `paper_section` 必须对应 `PAPER.md` 真实章节。
- `final` 门禁新增人工签核要求：`DECISIONS.md` 必须存在 `[signoff]` 记录（`log --kind signoff`）。
- 新增 `revert --to <phase> --reason ...`：审计式回退（写 `REVERT:` 历史），替代手工改状态。
- 模板完整性校验：`init` 缺少必需模板直接报错；`templates_dir` 检查 14 个模板齐全。
- `advance` 现在复核**所有已走过的阶段**（防止删掉早期证据后仍硬推到 final）；`final` 的人工签核
  不可用 `--force` 跳过；清单的 `- [ ]` / `* [ ]` / `+ [ ]` 都视为未完成；`results/` 只统计非空文件；
  `init` 拒绝在已有 `state.json` 的项目上重新初始化；`settings.*` 类型错误按状态损坏处理（退出码 3）。
- 明示已知边界：签核为流程性审计（不验证身份）、引用真实性依赖台账与 `citation-management`、判据需人工复核。
- 内容级门禁：必填 `##` 章节必须 ≥20 个非空白字符，代码围栏/HTML 注释内的标题不算；模板 `FILL:` 注释必须替换；
  引用台账要求 title + DOI/URL + 核验来源/时间；REBUTTAL 每个 `### Rn` 必须有实质回复正文。
- 状态与日志健壮性：拒绝顶层非对象的 state；坏 settings/类型错误统一退出码 3；`--reason`/`--text` 去除换行防日志注入；
  `--force` 无实际跳过时记录 `FORCE-NOOP`；advance 先写审计行再落状态；文档注明单进程使用约束。
- 新增 20 个测试（状态篡改、签核门禁与不可 force、证据缺失、章节映射、重复引用、回退、模板完整性、
  历史阶段复核、拒绝清空、设置类型、清单标记、空结果、强制签核绕过、空壳/短章节、代码围栏、FILL 注释、
  日志注入、非对象 state、空标题、force-noop）；测试总数 48 → 68。

## [0.2.0] - 2026-11-23

### Added

- 新增原创技能 `auto-research`：DSH 原生自主科研状态机（7 阶段、代码级门禁、证据台账、可恢复状态、强制跳过审计）。
  - `skills/auto-research/scripts/auto_research.py`：init / status / next / check / advance / log；纯标准库、离线可用。
  - 14 个模板（IDEA/LIT_REVIEW/EXPERIMENT_PLAN/RESULTS/PAPER/REVIEW/REBUTTAL/清单/复现/证据台账），占位哨兵未删则门禁不通过。
  - `docs/auto-research.md`：设计、门禁明细、自动模式与人工检查点、与 ARIS/AI-Scientist/Karpathy 方案的对应。
- 技能总数 15 → 16；`minimal` 预设加入 `auto-research`；`research-stack` 增加 auto-research 路由。
- CI 增加 auto-research 工具与模板的字节编译检查。

## [0.1.1] - 2026-11-23

### Fixed

- 修复 `uninstall --force` 可借 `..`/绝对路径删除技能根之外目录的问题；名称现在强制 kebab-case 并在解析后做目录包含校验（含测试）。
- 安装事务：`--no-backup` 下被替换副本先暂存，失败回滚不再丢旧版本；补「中途失败回滚」测试（有/无备份两条路径）。
- `build_lock --from-installed` 改为内存构建 + 校验通过后原子写入，失败不再留下半写入的 tar/锁；自动忽略 `__pycache__`/`*.pyc` 等运行时文件。
- tar 解压拒绝 FIFO/设备等特殊成员；安装器与 selftest 增加成员集合严格校验。
- `verify` 忽略 `__pycache__`/`*.pyc`、报告未管理的技能目录；拒绝驼峰调用键（DSH 会静默丢弃）。
- `--only` 去重；`--only` 与 `--exclude` 互斥；`doctor` 改为只读，不再创建 `$DSH_HOME`。
- 退出码文档与实际行为对齐（1=verify/selftest/doctor 失败，3=安装期来源完整性错误）。
- 每个技能目录新增 `NOTICE.md` + `LICENSE.txt`（ARS 含完整 CC BY-NC 文本）；`venue-templates` 的 Elsevier elsarticle 资产按 LPPL 1.3 单独披露；`vendor/licenses/` 增加 LPPL 原文。
- ARIS 3 个技能的来源已核对并固定到 commit `4ba94ae2...`；`research-stack` 补齐 DSH-PORT/NOTICE/LICENSE。
- 公开 v0.1.0 独立审计记录（`docs/audit-2026-11-23.md`）并逐项关闭 M1–M7 / S1–S8。

## [0.1.0] - 2026-11-23

### Added

- 首批 15 个 DSH 技能：
  - ARS 5 件套（`academic-paper`、`academic-paper-reviewer`、`academic-pipeline`、`deep-research`、`sr-screener`，CC BY-NC 4.0）
  - K-Dense 4 个（`scientific-writing`、`citation-management`、`scientific-visualization`、`venue-templates`，MIT）
  - ARIS 3 个（`research-lit`、`experiment-plan`、`analyze-results`，MIT）
  - `research-writing-skill`（中文写作，MIT）
  - `autoresearch`（DSH 适配版，MIT）
  - `research-stack`（原创科研路由技能，MIT）
- `tools/dsh_skills.py`：离线安装 / 校验 / 卸载 / doctor / selftest 统一 CLI，
  带备份、原子替换、失败回滚、哈希校验与路径穿越防护。
- `tools/build_lock.py`：确定性生成 `vendor/ars-dsh-*.tar.gz` 与 `manifests/skills.lock.json`，
  支持 `--check` 在 CI 中验证仓库自洽。
- `manifests/skills.lock.json`：15 个技能全部文件的 sha256、来源 commit、许可证、预设（minimal/writing/full）。
- 文档：两份生态调研（auto-research / 论文写作）、DSH 技能规范与移植指南、安装/使用/维护手册。
- CI：Linux + Windows × Python 3.10/3.12，执行 selftest、lock 校验、单元测试与临时目录安装/校验冒烟。
