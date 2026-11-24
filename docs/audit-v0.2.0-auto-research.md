# Auto Research 独立审计与 v0.2.1 处置（2026-11-24）

> 本文件是对 v0.2.0（commit `013967e`）的独立安全/正确性审计副本（已脱敏本机路径）。
> 审计结论为 NO-GO（针对"代码级门禁/可审计状态机"定位）：门禁在 v0.2.0 只能检查文件形状，
> final 不校验人工签核，历史/证据可被绕过。
>
> **v0.2.1 已按报告逐项修复**（对应关系如下），并补齐 20 个测试；仍保留的"流程性边界"也已在
> `docs/auto-research.md` 第 4 节明示（身份不可验证、引用真实性依赖外部核验、本地文件可被有意篡改）。

| 审计项 | 问题 | v0.2.1 处置 |
|---|---|---|
| M1 | final 不校验人工签核；`--by human` 可伪造 | `gate_final` 要求 `DECISIONS.md` 存在 `[signoff]` 行；`advance` 进入 final 同时跑 completion gate；签核缺失**不可 `--force` 跳过**；文档明示签核是流程审计而非身份认证 |
| M2 | 引用/claim/results 是自证 | 引用要求 id 唯一 + title + DOI/URL + verification.source/checked_at；claim 证据路径必须真实存在、paper_section 对应真实章节；results 只统计非空文件；文档注明引用真实性仍需 `citation-management` 外部核验 |
| M3 | phase/history 无连续性校验 | `load_state` 校验 history 链（from/to 连续、尾部等于 phase、by 合法、settings 类型）；手工改 phase → 退出码 3；新增 `revert` 审计式回退 |
| M4 | advance 只查当前门禁 | advance 复核所有已走过阶段；进入 final 额外跑 completion gate |
| M5 | 空壳/只删哨兵/代码围栏标题可通过 | 章节正文 ≥20 非空白字符；代码围栏/HTML 注释剥离后再匹配；模板新增 `FILL:` 注释必须替换；review/rebuttal 需实质正文 |
| M6 | 清单 `* [ ]` 可绕过 | `-/*/+` 三种标记统一识别；代码围栏剥离 |
| M7 | force/by 痕迹可伪造、日志注入 | `--reason`/`--text` 去换行防注入；force 无实际跳过记录 `FORCE-NOOP`；advance 先写审计行；文档明示本地工具不可防有意篡改 |
| M8 | `init --force` 清空审计 | 已存在 `state.json` 的项目拒绝重新初始化（不再提供清空入口） |
| M9 | 坏 state/settings traceback；advance 非原子 | state 顶层/类型校验统一退出码 3；main 捕获类型错误；先追加 DECISIONS 再写 state；文档注明单进程使用 |

---

# Auto Research 独立安全/正确性审计报告（v0.2.0）

- 审计日期：2026-11-24
- 审计对象：`<repo>`，GitHub `hhxpoint/research`，v0.2.0，16 个 DSH 技能
- 重点：`auto-research` 自主科研状态机（HEAD commit `013967e`，脚本 692 行，7 阶段门禁）
- 审计方式：只读代码审查 + 在 `%TEMP%` 的 `git archive HEAD` 快照上跑全流程/绕过实验；未联网、未推送、未修改仓库文件
- 重要基线说明：审计期间工作树被另一进程并发修改（见第七节），**本报告所有行号与结论均针对 HEAD `013967e`（v0.2.0）**，不是当前未提交的 WIP

---

## 一、结论

### 1.1 总体结论

**NO-GO（针对 v0.2.0 作为“代码级门禁 / 可审计科研状态机”的发布定位）。**

仓库的打包、锁文件、安装器、许可证与 CI 自洽性是合格的；但 `auto-research` 的核心安全承诺——"门禁是代码，不是提示词"、"不能在没有真实产物/证据的情况下推进"、"人工签核后才可提交"——在 v0.2.0 中**没有成立**。最关键的三个事实：

1. **`final` 阶段完全不检查人工签核，甚至进入 `final` 时根本不运行 `gate_final`**：删掉 `DECISIONS.md` 后 `check` 仍返回 0；清单未勾选、`PROVENANCE.md` 缺节也能 `advance` 成 `final`；`--by human` 只是命令行字符串，agent 可自行填写。
2. **证据门禁基本是自证**：引用只检查自报的 `status: verified`，claim 只要求 `evidence` 是非空 list，`results/` 只数文件个数；0 字节文件、空标题引用、指向不存在文件的 claim 全部可以通过。
3. **状态与历史可手工改写**：`phase` 与 `history` 没有连续性校验，文档甚至教用户直接改 `phase`；`check` 只检查当前及之前阶段，回退 `phase` 即可把已损坏的后续证据隐藏起来。

如果把它降级定位为"带模板的科研流程脚手架"（而不是安全/审计边界），可以发布，但必须同步修改 SKILL/README/docs 中所有"强制、审计、必须人工"的表述。按当前宣传口径，**NO-GO**。

### 1.2 做得对的部分（应保留）

- 纯标准库、无网络、无 `eval`/`subprocess`/动态导入；工具本身不执行实验代码，RCE 面很小。
- `init`/`advance`/`log` 的写入路径只有项目根下的 `state.json`、`DECISIONS.md` 和固定模板相对路径，未发现路径穿越；`state.json` 使用临时文件 + `replace` 原子替换。
- `--force` 在门禁失败时强制要求非空 `--reason`，并写入 `state.history` 与 `DECISIONS.md`（但不可防篡改，见 M7）。
- 未知 phase、`state.json` 非法 JSON 返回 3；缺文件、坏 `citations.json` 返回 1 而不是崩溃（大部分情况）。
- `--to` 拒绝越级、非空目录拒绝 `init`（无 `--force` 时）、`log --text` 为空拒绝。
- 锁文件与 HEAD 字节一致；`build_lock --check`、`apply_notices --check`、`selftest`、48 个单元测试、临时安装 + `verify --require-all` 全部通过（详见第五节）。
- `auto-research` 的 frontmatter 符合 DSH 规则，安装后自包含（从安装目录可独立 `init`，14 个模板齐全）。

### 1.3 必须修数量

**9 项：Critical 2、High 4、Medium 3。** 其中 M1–M5 修复前不应按当前文案发布；M7–M9 可与文档修正一起处理。

---

## 二、必须修（按严重度）

> 行号均为 HEAD `013967e`。复现均在临时目录执行，不需要联网。
> 通用准备：`python skills/auto-research/scripts/auto_research.py init <dir> --title T --question Q --min-refs 2 --min-claims 1 --min-review-items 1 --min-result-files 1`，然后按各条填写产物。

### M1 [Critical] `final` 没有强制人工签核；`--by human` 可伪造

**位置**
- `skills/auto-research/scripts/auto_research.py:363-384`（`gate_final`）：只检查 `SUBMISSION_CHECKLIST.md`、`PROVENANCE.md`、未勾选项，并复用 `gate_writing`；**完全没有读取 `DECISIONS.md`**。
- `skills/auto-research/scripts/auto_research.py:580-615`（`cmd_advance`）：从 `review` 进入 `final` **只运行 `GATES["review"]`，完全不运行 `GATES["final"]`**，然后直接写 `phase=final`；清单/复现信息缺节也能"成功进入 final"，更没有任何"人工签核"前置条件。
- `skills/auto-research/scripts/auto_research.py:666`：`--by` 只是 `choices=["agent","human"]`，没有身份校验。
- `skills/auto-research/scripts/auto_research.py:607-611`：`history.by` 与 `DECISIONS.md` 直接采用 `args.by`。
- 文档承诺：`skills/auto-research/SKILL.md:87-90`（完成标准要求作者在 `DECISIONS.md` 最终签核）、`docs/auto-research.md:65`。

**事实/复现**
1. 按模板填完 7 阶段，`advance` 6 次到 `final`，删除整个 `DECISIONS.md`，再 `check`：返回码 **0**，输出 `result: PASS`；`state.json.project.phase == "final"`。
2. 故意把 `SUBMISSION_CHECKLIST.md` 留一个 `- [ ]` 未勾选、`PROVENANCE.md` 只写 `## Environment`，前面 5 阶段正常推进；第 6 次 `advance`（review → final）仍返回 **0**，`phase=final`；只有 `check` 才返回 1 并列出 `missing section heading` / `unchecked item`。即"进入 final"本身没有任何门禁。
3. 全新项目（门禁未过）执行：
   `advance <dir> --by human --force --reason "PI approved"`
   返回 **0**；`state.history[-1].by == "human"`，`DECISIONS.md` 写入 `advance ideation -> literature by human (FORCED: PI approved)`；全程没有任何人类动作。
4. `log --kind signoff --text "..."` 只是任意文本追加，agent 可自行写"作者已确认"；HEAD 的 `gate_final` 甚至不要求这一行。

**影响**
- SKILL 的"作者签核后才可提交"和 docs 的"人工签核落点"是**纯约定**，不是门禁；agent 可无痕（HEAD）或留一条自签文本（WIP）地完成 `final`。
- `--by human` 作为审计字段没有可信度；后续 review 无法区分人类和 agent。

**修复方向**
- `gate_final` 必须要求 `DECISIONS.md` 中存在**在最后一次 `advance` 之后**、由独立 `sign` 命令产生、包含 phase/原因/时间的 `[signoff]` 记录；`advance` 进入 `final` 时强制检查，且 `--force` 不得绕过签核本身。
- 明确文档："`--by` 是自报字段，不构成身份认证"；若要更强，使用用户提供的签名密钥/HMAC（本地工具无法真正证明"人"，但可要求外部签名文件）。

---

### M2 [Critical] 引用/claim/结果证据是自证布尔或任意文件

**位置**
- `skills/auto-research/scripts/auto_research.py:236-253`（`check_citations`）：只检查 `status.lower() == "verified"` 和非空 `id`；不要求 title/authors/year/venue/DOI/URL，不要求 `verification.source`/`checked_at`，不检查重复 id。
- `skills/auto-research/scripts/auto_research.py:255-273`（`check_claim_map`）：只要求 `evidence` 是**非空 list**；不检查元素类型、路径是否存在、是否在项目内、`paper_section` 是否真实存在，不检查重复 claim id。
- `skills/auto-research/scripts/auto_research.py:276-286`（`count_results`）：递归数 `results/` 下任意非 `.gitkeep` 文件；不要求非空、扩展名、哈希、与 `RESULTS.md` 数字的对应关系。
- `skills/auto-research/scripts/auto_research.py:329-333`、`:338-342`：experiments/writing 门禁只调用上述函数。

**事实/复现**
- 引用：`{"citations":[{"id":"same","status":"verified"},{"id":"same","status":"verified"}]}`（两条同 id、无标题、无 DOI）在 `minRefs=2` 下 `check` 返回 **0**。
- claim：`{"claims":[{"id":"C1","claim":"c","evidence":["results/does-not-exist.csv"],"status":"verified"}]}` 在 writing 阶段 `check` 返回 **0**；`evidence:[123]`、重复 `C1` 也通过。
- 结果：`results/empty.bin` 为 **0 字节**，experiments 门禁 `pass=true`；整个 `results/` 为空但 `--min-result-files 0` 时也 `pass=true`。
- 全流程只用"标题 + 空行"的 `IDEA/LIT/PLAN/RESULTS/PAPER/...` 即可 6 次 `advance` 全部成功（见 M5）。

**影响**
- "引用必须 verified"实际是"agent 把字符串改成 verified"；"claim 必须有证据"实际是"list 非空"；"数字可回溯"没有实现。伪造 10 条 `{"id":"x","status":"verified"}` 即可过 `minRefs` 默认 10。
- 这是本报告中最直接的反幻觉失效：门禁检查的是**文件形状**，不是**证据真实性**。

**修复方向**
- 引用：要求 id 唯一；title/authors/year/venue 至少一项非空；`doi_or_url` 必须形如 DOI/URL；`verification.source` + `checked_at` 非空；可选 `--strict` 校验 DOI 语法。
- claim：`evidence` 每项必须是字符串；相对路径必须 `resolve()` 到项目内且 `is_file()`，或显式允许 `http(s)/doi/arxiv` 前缀；`paper_section` 必须是 `PAPER.md` 的真实 `##` 标题且正文非空。
- 结果：至少要求 `results/` 文件非空；更好的做法是在 `RESULTS.md`/`claim_map.json` 中记录每个结果文件的 sha256，门禁重算并比对。
- 文档同口径：把"必须核验"改为"必须登记核验字段；工具不联网验证"。

---

### M3 [High] `phase`/`history` 没有连续性校验；回退可隐藏已损坏证据

**位置**
- `skills/auto-research/scripts/auto_research.py:401-419`（`load_state`）：只校验 `schemaVersion`、`phase in PHASES`、`settings` 是 dict、`history` 是 list；**不校验** `history[-1].to == phase`、`from/to` 链、条目字段类型、`by` 取值。
- `skills/auto-research/scripts/auto_research.py:558-560`（`cmd_check`）：只检查 `PHASES[:index+1]`；当前 phase 之后的门禁不检查。
- `docs/auto-research.md:103`：明确写"想回退阶段：直接改 `state.json.project.phase`"，且不强制在 `DECISIONS.md` 记录。

**事实/复现**
1. 完整走到 `final` 后，删除 `PAPER.md`、`REVIEW.md`、`REBUTTAL.md`，把 `state.json.project.phase` 改成 `ideation`；`check` 返回 **0**，且 `status --json` 显示 `phase=ideation [1/7]`，后续坏证据被完全隐藏；`history` 仍有 7 条，和 phase 不一致。
2. 把 `history` 截断为只有 `init` 一条、`phase` 直接改成 `final`，所有产物齐全时 `check` 返回 **0**；工具不报"跳过了 6 次推进"。
3. 把 `history` 整个设为 `[]`，`final` 的 `check` 仍返回 **0**。

**影响**
- 审计链不可信：phase 是"当前视图"，history 是"可编辑文本"，两者可以任意不一致。
- 回退（文档鼓励的操作）会绕过 `check` 对后续阶段的复核，正好掩盖"后面改坏前面证据"的风险；这与 `docs/auto-research.md:51` 的承诺相反。
- 多用户/跨天恢复时，无法证明项目真的按 7 阶段推进过。

**修复方向**
- `load_state` 强制：`history` 非空、条目字段合法、`history[0].from is None`、`history[i].from == history[i-1].to`、`history[-1].to == project.phase`、`by in {init,agent,human}`。
- 回退改为显式 `revert --to <phase> --reason`（记录 history 与 DECISIONS），禁止手工编辑 phase；`check` 在回退后仍应报告后续阶段"stale"，或至少在 `status` 显示"曾达到过更高阶段"。
- 若要防篡改，history 每条记录前一阶段产物的哈希（见建议 S4）。

---

### M4 [High] `advance` 只校验当前阶段，不复核历史门禁

**位置**
- `skills/auto-research/scripts/auto_research.py:592`：`problems = GATES[phase](project, state["settings"])`，只跑当前 phase 的 gate。
- `skills/auto-research/scripts/auto_research.py:558-560`：只有 `check` 会回看历史阶段；`advance` 不会。
- 文档承诺：`README.md:102`"门禁不通过就不能推进"、`SKILL.md:54`"每阶段结束时用 check 复核"，但 `advance` 自身不保证。

**事实/复现**
1. 正常 `advance` 到 `writing`（此时 IDEA/LIT/PLAN/RESULTS 都已过）。
2. 删除 `IDEA.md`。
3. 填好 REVIEW/REBUTTAL/CHECKLIST/PROVENANCE 后：
   - `advance`（writing → review）返回 **0**；
   - `advance`（review → final）返回 **0**；
   - `state.phase == "final"`，但 `check` 返回 **1**（`missing artifact: IDEA.md`）。
4. 也就是说，一个只依赖 `advance` 返回码的 agent 可以在 IDEA 缺失的情况下"成功"到达 final；只有额外运行 `check` 才会发现。

**影响**
- 与"门禁不通过就不能推进"直接矛盾；历史证据在推进过程中可以被删除/改坏而不阻断下一步。
- 这是"没有真实产物也能推进阶段"的现成路径，不需要 `--force`。

**修复方向**
- `cmd_advance` 在推进前运行 `PHASES[:index+1]` 的所有 gate（或至少运行上一次 `advance` 之后被修改过的阶段）；失败即拒绝，`--force` 只跳过当前失败并写明。
- 每次 `advance` 把本阶段关键产物的 sha256 写入 history，下一次推进时校验；这样删改历史证据会被发现。

---

### M5 [High] 空壳产物、只删哨兵、代码围栏标题均可通过

**位置**
- `skills/auto-research/scripts/auto_research.py:180-191`（`require_file`）：只检查文件存在、是否含精确字符串 `AUTO-RESEARCH: TODO`、`.md` 是否 `strip()` 为空；不检查章节正文。
- `skills/auto-research/scripts/auto_research.py:194-200`（`require_headings`）：正则 `^##\s+Heading\s*$`，不剥离代码围栏/HTML 注释；标题可以出现在 ``` 代码块里。
- `skills/auto-research/scripts/auto_research.py:298-384`：所有 gate 都只检查"标题 + 少量结构"。
- 模板事实：14 个模板中只有 11 个含哨兵；`DECISIONS.md`、`evidence/citations.json`、`evidence/claim_map.json` 不含。含哨兵的 11 个中，`AUTO-RESEARCH.md` 与 `evidence/README.md` **从未被任何 gate 读取**；其余 9 个才是被检查的产物。
- 文档承诺：`SKILL.md:16`、`docs/auto-research.md:35`、`CHANGELOG.md:11`"所有模板含哨兵，没删就过不了门禁，避免空壳产物糊弄"；`SKILL.md:22`"四节实质内容"。

**事实/复现**
1. `IDEA.md` 只写：
   ```markdown
   ## Research question
   ## Hypotheses
   ## Contribution
   ## Scope and risks
   ```
   （标题之间无任何正文）→ ideation gate `pass`；对其它 6 个阶段如法炮制，`advance` 6 次全部 **0**，`check` **0**。
2. 复制 `IDEA.md` 模板，只删除 `<!-- AUTO-RESEARCH: TODO -->` 一行，保留模板里的说明性中文（不是真实研究内容）→ ideation `check` **0**。
3. 把 `## Research question` 等四行放进 ```markdown 代码块 → `check` **0**。
4. 走到 final 后，`AUTO-RESEARCH.md` 和 `evidence/README.md` 仍保留哨兵，`check` **0**。

**影响**
- "避免空壳产物糊弄"没有实现；删除哨兵是 1 秒操作，门禁无法区分模板说明和真实内容。
- 模板哨兵覆盖不完整，给用户"已检查"的错觉。

**修复方向**
- 每个必填章节要求正文 ≥ N 个非空白字符（例如 80–200，按章节），且不在代码围栏/注释内；剥离 ```/`~~~`/HTML 注释后再匹配标题和正文。
- 哨兵检查覆盖所有 14 个模板；对 JSON 用 `_TODO`/`TODO-REPLACE` 占位 id 并显式检查；`AUTO-RESEARCH.md`/`evidence/README.md` 要么纳入 gate，要么从"哨兵"承诺中移除。
- 不要只检查标题字符串；至少要求每个章节有非空段落。

---

### M6 [Medium] 投稿清单只识别 `- [ ]`，`* [ ]` 可绕过"全部勾选"

**位置**
- `skills/auto-research/scripts/auto_research.py:379-382`：`re.findall(r"^\s*-\s*\[ \]", checklist, re.M)`，只匹配 `-` 列表项。
- 文档承诺：`SKILL.md:28`"清单全部勾选"、`docs/auto-research.md:49`"清单无未勾选项"。

**事实/复现**
1. 正常到 final，把 `SUBMISSION_CHECKLIST.md` 改成：
   ```markdown
   ## Checklist
   * [ ] 引用全部核验
   ## AI disclosure
   AI used
   ```
   `check` 返回 **0**（`* [ ]` 未被计数）。
2. 换成 `- [ ] 引用全部核验`，`check` 返回 **1**（说明差异确实来自列表符号，而不是其它 gate）。
3. `- [x]` 可以随意伪造；工具不验证勾选项对应的工作是否真的完成。

**影响**
- 最直观的"投稿前检查"门禁可被一个字符绕过。
- 与 M5 同源：检查的是 Markdown 形状，不是内容。

**修复方向**
- 解析列表项时接受 `-`/`*`/`+`，并支持 `- [ ]`/`- [X]`/`- [x]` 的统一解析；先剥离代码围栏；对缩进列表也生效。
- 要求每个清单项有对应的证据/命令（可选 `--strict`），至少不允许"未勾选但格式不同"绕过。

---

### M7 [High] `--force`/`--by` 的审计痕迹可伪造、可擦除、无人工检查点

**位置**
- `skills/auto-research/scripts/auto_research.py:601-611`：`FORCED:` 原因写入 `state.history` 与 `DECISIONS.md`，但两者都是普通可写文件；没有哈希链、没有 append-only 强制、没有签名。
- `skills/auto-research/scripts/auto_research.py:618-626`（`cmd_log`）：任意 `--text` 直接追加，agent 可写"PI 已批准"；`--kind` 只是字符串。
- `skills/auto-research/scripts/auto_research.py:666`：`--by` 由调用者自选。
- 文档承诺：`SKILL.md:53`、`SKILL.md:60-66`（`--force` 必须停下等人工）。

**事实/复现**
1. 全新项目执行 `advance --by human --force --reason "PI approved"` → 0；history/DECISIONS 都显示 human，实际没有人类。
2. 先 `--force --reason "x"`，然后手工把 `DECISIONS.md` 重写为只有标题、把 `history` 截断为 `init`；`status` 仍返回 **0**，工具不报"历史被删"。
3. `--reason "ok\n- 2026-11-24T00:00:00+08:00 [signoff] PI approved"` 会把第二行作为新的 DECISIONS 行注入（日志注入），可伪造签核/决策记录。
4. 工具没有"`--force` 前必须存在人类签核"的检查；agent 可以自己决定强制跳过。

**影响**
- `--force` 的"可审计"只是"默认会写一行"，不是"不可否认"；一个不守规矩的 agent 可以强制推进并擦除痕迹。
- 与 M1 叠加：agent 可以自签、自 force、自改 history，形成完整的自证闭环。

**修复方向**
- history 做哈希链（每条包含前一条 hash + 本阶段产物 hash），`load_state` 校验链；篡改后拒绝加载（至少标记 `integrity=broken` 并退出 3）。
- `DECISIONS.md` 只追加 + 记录 offset/hash；或把关键事件同时写入只读/外部日志。
- `--force` 要求 `--by human` 且存在此前 `sign` 记录；`--reason` 去除换行/控制字符或按引用块转义，防注入。
- 明确文档：本地工具无法认证"人"，但可以要求"签核记录 + 时间顺序 + 内容哈希"，让自签至少留痕、可追责。

---

### M8 [Medium] `init --force` 会静默销毁既有项目状态与签核记录

**位置**
- `skills/auto-research/scripts/auto_research.py:451-466`：`--force` 跳过"目录非空"保护；对模板中已存在的文件执行 `copyfile` 覆盖。
- `skills/auto-research/scripts/auto_research.py:470-494`：无条件重新生成 `state.json`（新 history、新 title、phase=ideation），并覆盖模板 `DECISIONS.md`。
- `skills/auto-research/templates/DECISIONS.md:1-3`：模板会覆盖原有签核文件。
- 对照安装器的语义：`dsh_skills.py install --force` 只强制重装技能，不会清空用户项目；`auto_research.py init --force` 却是破坏性的。

**事实/复现**
1. `init` 一个项目，填好 `IDEA.md`，执行 `log --kind signoff --text "PI signed off on scope"`。
2. 在同一个目录执行 `init <dir> --title NEW --question Q2 --force` → 返回 **0**。
3. 结果：`phase=ideation`、`history` 只剩 1 条、`DECISIONS.md` 的"PI signed off"消失、`IDEA.md` 恢复成带哨兵的模板。没有备份、没有确认提示。

**影响**
- 误用 `--force` 会丢失整个项目的审计历史与人工签核；这与"可恢复、append-only"的定位冲突。
- 与安装器的 `--force` 语义不一致，用户容易以为只是"允许非空目录"。

**修复方向**
- 对已存在的 `state.json`/`DECISIONS.md`，`--force` 也必须拒绝；新增显式 `--reset`（要求二次确认/`--reason`），并先备份到 `state.json.bak-<timestamp>` / `DECISIONS.md.bak-<timestamp>`。
- 若只是"在非空目录补模板"，提供 `--scaffold-missing`，不覆盖已有文件。

---

### M9 [Medium] 坏 settings/state 形状会 traceback（退出 1 而非 3）；`advance` 非原子

**位置**
- `skills/auto-research/scripts/auto_research.py:415-418`：只校验 `settings` 是 dict，不校验值是 int；`:242`、`:261`、`:329`、`:352` 直接 `int(settings.get(...))`。
- `skills/auto-research/scripts/auto_research.py:405-411`：`state` 顶层若不是 dict（如 `[]`），`state.get` 直接 `AttributeError`；`main` 只捕获 `AutoResearchError`/`OSError`（`:679-688`），不捕获 `TypeError`/`ValueError`/`AttributeError`。
- `skills/auto-research/scripts/auto_research.py:605-611`：先 `save_state` 再 `append_decision`；`:433-439` 的 append 失败时状态已推进，命令却返回 2，DECISIONS 无记录。
- `save_state`（`:422-426`）用 tmp+replace 是好的，但没有 fsync、没有文件锁；两个并发 `advance` 会读同一旧 state 并互相覆盖。

**事实/复现**
1. `state.settings.minRefs = null` → `status` 返回 **1**，stderr 为 `TypeError: int() argument ... not 'NoneType'`（文档说损坏状态返回 3）。
2. `minRefs = "abc"` → `check` 返回 **1**，`ValueError: invalid literal for int()`。
3. `state.json` 写入 `[]` → `status` 返回 **1**，`AttributeError: 'list' object has no attribute 'get'`。
4. 把 `DECISIONS.md` 改成目录后执行 `advance`：返回 **2**，但 `state.phase` 已经从 `ideation` 变成 `literature`，`history` 已追加，`DECISIONS` 无对应行。
5. 两个进程同时 `advance` 时没有锁；这是本地工具可接受的限制，但应在文档中写明"不要并发推进"。

**影响**
- 退出码约定（3=状态损坏）不成立；自动化脚本会把 traceback 误判为普通门禁失败。
- 状态与决策日志可能不一致；崩溃/权限问题会留下"已推进但无审计行"的状态。

**修复方向**
- `load_state`：要求顶层是 dict、`project` 是 dict、`title` 非空、`settings` 的四个阈值都是 `int` 且 ≥1、`history` 条目是 dict 且字段合法；所有失败抛 `IntegrityError`（3）。
- `main` 增加 `except (TypeError, ValueError, AttributeError)` 兜底为 3（或至少打印可读错误，不输出 traceback）。
- `advance` 事务化：先写 DECISIONS 临时文件并 fsync，再写 state；或写 state 前先追加 DECISIONS，失败则回滚 state；加简单文件锁（Windows `msvcrt.locking` / 跨平台 `portalocker` 可选，纯标准库可用 lock 文件 + O_EXCL）。
- 文档写明单进程使用约束。

---

## 三、建议修（不阻塞发布，但应尽快）

- **S1 模板完整性**：`templates_dir` 只检查 `IDEA.md`（`:158-165`）。删掉 `templates/PAPER.md` 后 `init` 仍返回 0（只复制 13 个模板），直到 writing 阶段才失败。建议校验 14 个必需模板（含 evidence/*.json）并计算模板哈希。
- **S2 配置校验**：`init` 接受空 `--title`/`--question`（`:470-479`）和负阈值（`:480-485`）；`--min-result-files 0` 时 experiments 可在 `results/` 为空时通过。建议 title/question 非空、四个阈值 ≥1。
- **S3 路径/证据约束**：如果按 M2 加 evidence 路径校验，必须 `resolve()` 后限制在项目内（允许显式 `http(s)/doi/arxiv`），防止 `../../` 读取项目外文件（HEAD 不读路径，所以当前不是漏洞，但加校验时容易引入）。
- **S4 哈希链/快照**：每次 `advance` 把当前阶段必需产物的 sha256 写入 history（并链到上一条），`load_state` 重算；这能把"后来改坏前面证据"变成可检测事件。比单纯校验 from/to 更强。
- **S5 原子性与锁**：见 M9；`DECISIONS.md` 追加也应 fsync；`save_state` 可加 `.tmp` 清理和失败回滚。
- **S6 清单/标题解析**：剥离代码围栏/HTML 注释后再匹配标题和清单；接受 `-/*/+`、`[ ]/[x]/[X]`；`REVIEW` 的 `### Rn` 也应在代码围栏外匹配，且 REBUTTAL 每个 Rn 下要有非空回复正文（现在只有标题也算回复）。
- **S7 日志注入**：`--reason`/`--text` 中的换行应转义为续行或单行 JSON；否则可伪造 DECISIONS 条目。
- **S8 文档/溯源修正**：见第六节；尤其 `THIRD-PARTY.md` 把 `auto-research` 误归为第三方移植、`DSH-PORT.md` 的 `packaged files: 21` 与实际 19 不符。
- **S9 CI 增强**：CI 的 clean-room 步骤用 `git clone .` 克隆 HEAD，但 `install` 读取当前工作树；若工作树脏，重建锁与提交锁可能不一致。建议在 clean-room 前加 `git diff --exit-code` / `git status --porcelain` 守卫，或明确只在干净 checkout 运行。并增加 `auto-research` 行为测试（见第四节）。
- **S10 `--force` 语义**：`--force` 若在 gate 已通过时传入，当前不会记录任何 `FORCED`（`:594-604` 只在 problems 时进入）；这不算漏洞，但会让"我 force 过"不可见。建议无论 gate 是否通过，只要传了 `--force` 就记录 `FORCE-NOOP` 或拒绝。
- **S11 `--by` 文档**：明确 `--by human` 只是自报，不能作为身份认证；如需真正的人工签核，合并 M1 的 `sign` 命令 + 外部签名。
- **S12 代码清理**：`TODAY`（`:59`）未使用；`TEMPLATE_CANDIDATES` 第二项 `TOOL_DIR.parent.parent / "templates" / "auto-research"`（`:56`）在仓库布局下不存在，属死路径，容易误导。

---

## 四、测试缺口（当前 48 个测试未覆盖，按优先级）

1. **[P0] final 签核**：无 `DECISIONS.md` / 无 `[signoff]` 时必须拒绝进入 final；agent 执行 `log --kind signoff` 后是否仍算"人工"、`--by human` 是否可伪造，应有明确断言（当前测试完全没有 final 签核用例）。
2. **[P0] phase/history 篡改矩阵**：回退 phase 隐藏坏证据、phase 跳到 final、清空 history、改 `history.by`、`from/to` 断链 → 应返回 3；当前 `test_corrupted_state_is_integrity_error` 只测非法 JSON。
3. **[P0] 证据语义**：重复 citation/claim id、空标题、无 DOI、claim evidence 指向不存在/越界路径、`evidence:[123]`、0 字节 results、只有标题的章节 → 应失败；当前 `test_full_pipeline_until_final` 用的都是"恰好能过"的最薄数据，没有反向断言。
4. **[P1] `advance` 复核历史**：到 writing 后删 `IDEA.md`，再 `advance` 两次必须失败；当前只测 `check`（而 `advance` 才是 agent 实际调用的命令）。
5. **[P1] 坏 state/settings 类型**：`settings.minRefs=null/"abc"`、`state.json=[]`、`project=[]` 应以 3 退出且无 traceback；当前没有类型鲁棒性测试。
6. **[P1] `init --force` 非破坏性**：已有 state/DECISIONS 时不得静默覆盖，或必须备份；当前只测"非空目录无 --force 拒绝"。
7. **[P2] 清单/标题格式绕过**：`* [ ]`、`+ [ ]`、`- [X]`、缩进、代码围栏内的 `##`/`### Rn`；当前 `test_full_pipeline` 只写 `- [x]`，没有"未勾选"的反向测试（尽管 docs 声称覆盖了）。
8. **[P2] 原子性与并发**：DECISIONS 追加失败时 state 不得推进；两个 `advance` 并发不丢 history；`--reason` 换行不得注入 DECISIONS。
9. **[P2] 安装后自包含 smoke**：从 `$DSH_HOME/skills/auto-research/scripts/auto_research.py` 执行 init/check，确认 templates 被正确找到；当前 `test_install_full_and_verify` 只校验哈希，不运行脚本。
10. **[P2] 模板完整性**：删除任一模板后 `init` 应失败；当前只测 IDEA 哨兵。

---

## 五、验证命令与结果

### 5.1 仓库不变量（HEAD `013967e` 的临时快照）

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$repo = '%TEMP%\ar-audit-20261124-110934\repo'   # git archive HEAD 解压
cd $repo
python tools\build_lock.py --check
python tools\apply_notices.py --check
python tools\dsh_skills.py selftest
python -m unittest discover -s tests -v
```

结果：

| 命令 | 结果 |
|---|---|
| `build_lock.py --check` | `CHECK OK: lock, archive, and repo skills are consistent`；16 skills；ARS archive sha256 `049b6eff...`；退出 0 |
| `apply_notices.py --check` | `NOTICES OK: 16 skills checked`；退出 0 |
| `dsh_skills.py selftest` | `SELFTEST PASS: 16 skills, archive vendor/ars-dsh-v3.24.4-d103b100.tar.gz`；退出 0 |
| `unittest discover` | `Ran 48 tests in 233.737s`，`OK (skipped=1)`；唯一 skip 是当前主机无法创建 symlink，不是失败 |

### 5.2 安装/校验/自包含（临时 DSH home）

在 `%TEMP%\ar-dsh-home-<guid>` 执行：

| 命令 | 结果 |
|---|---|
| `python tools\dsh_skills.py install --mode full --dsh-home <tmp> --no-backup` | 16 个技能安装成功 |
| `verify --require-all` | 16 个全部 `OK`，`result: PASS` |
| `verify --only auto-research --json` | `ok: ["auto-research"]` |
| `apply_notices.py --check --dsh-home <tmp>` | `NOTICES OK: 16 skills checked` |
| 从 `<tmp>\skills\auto-research\scripts\auto_research.py init ...` | 成功，`copied 14 template file(s)`（安装后自包含） |
| 篡改已安装的 `scripts/auto_research.py` 后 `verify --only auto-research` | `hash mismatch: scripts/auto_research.py`，退出 1（verify 覆盖 auto-research） |

### 5.3 绕过实验（HEAD 快照，关键结果）

| 用例 | 操作 | 结果 |
|---|---|---|
| 空壳全流程 | 所有产物只写 `##` 标题，6 次 `advance` | 全部 0，final `check` **0** |
| 只删哨兵 | 删除 `IDEA.md` 的 `<!-- AUTO-RESEARCH: TODO -->`，保留模板说明 | `check` **0** |
| 代码围栏标题 | 四节标题放进 ```markdown 代码块 | `check` **0** |
| final 无签核 | 删 `DECISIONS.md` | `check` **0** |
| final 入口无门禁 | 清单留 `- [ ]`、PROVENANCE 缺节，再 `advance` review→final | 返回 **0** 进入 final；`check` 才 **1** |
| 伪造 human | `advance --force --by human --reason ...` | 0，history/DECISIONS 显示 human |
| 擦除 force 痕迹 | 重写 DECISIONS + 清空 history | `status` 0，无报错 |
| 重复引用 | 2 条同 id、空标题、status=verified | literature `check` **0** |
| 假 claim | evidence 指向不存在文件；`evidence:[123]`；重复 C1 | writing `check` **0** |
| 任意结果 | `results/empty.bin` 0 字节 | experiments gate `pass=true` |
| 回退隐藏 | final 删 PAPER/REVIEW/REBUTTAL，phase 改 ideation | `check` **0**，final gate 显示 false |
| 跳阶段 | phase 直接改 final，history 只留 init | `check` **0** |
| 历史清空 | history=[] | final `check` **0** |
| 仅删早期证据 | writing 后删 IDEA，再 advance 两次 | 两次均 0，phase=final，`check` 1 |
| 清单格式 | `* [ ]` 未勾选 | final `check` **0**（换成 `- [ ]` 则 1） |
| 未删哨兵 | final 时 AUTO-RESEARCH.md/evidence README 仍含哨兵 | `check` **0** |
| init --force | 已有签核的项目被重新 init | 0，phase=ideation，history=1，签核丢失 |
| 坏 settings | `minRefs=null` / `"abc"` | 退出 1 + traceback（应为 3） |
| 坏 state | `state.json=[]` | 退出 1 + AttributeError（应为 3） |
| 非原子 | DECISIONS 变目录后 advance | 退出 2，但 phase 已变为 literature |
| 日志注入 | `--reason` 带换行 + `[signoff]` | 0，DECISIONS 出现伪造行 |

### 5.4 当前工作树（非 HEAD）

- `git status --porcelain`：10 个文件 `M`（CHANGELOG、docs/auto-research.md、lock、DSH-PORT、SKILL、脚本、DECISIONS 模板、SUBMISSION_CHECKLIST 模板、evidence/README、tests）。
- 11:18 时对工作树执行 `build_lock --check` 曾失败（`auto-research: SKILL.md`），11:19 lock 更新后再跑为 `CHECK OK`；但**这是未提交 WIP**，不能视为 v0.2.0 的验证结果。
- 工作树 WIP 的抽查见第七节；请勿从当前脏树直接 tag/发布。

---

## 六、文档不一致清单

> 以下行号均为 HEAD `013967e`。

| # | 文档:行 | 宣称 | 实际 |
|---|---|---|---|
| D1 | `skills/auto-research/SKILL.md:16`；`docs/auto-research.md:35`；`CHANGELOG.md:11` | 所有模板含哨兵，未删则门禁不通过，避免空壳 | 14 个模板中 3 个无哨兵（DECISIONS、citations、claim_map）；含哨兵的 AUTO-RESEARCH.md、evidence/README.md 从未被 gate 读取；标题即内容也可通过 |
| D2 | `SKILL.md:22`；`docs/auto-research.md:43` | IDEA 四节"实质内容"，只有标题会被拒 | 只检查 `##` 标题存在，标题下无正文也通过 |
| D3 | `SKILL.md:25`；`docs/auto-research.md:46` | 结果文件 ≥ minResultFiles，数字可回溯 | 任意 0 字节文件计数；无哈希/表格数字关联 |
| D4 | `SKILL.md:26`；`docs/auto-research.md:47`；`docs/usage.md:15` | claim 必须有证据，claim 找不到证据会被拒 | 只要求 `evidence` 非空 list；不存在的路径、整数元素都通过 |
| D5 | `SKILL.md:28`；`docs/auto-research.md:49` | 清单全部勾选；`* [ ]` 也应视为未勾选 | 只识别 `- [ ]`，`* [ ]` 未勾选可通过 |
| D6 | `SKILL.md:52`；`README.md:102` | 不允许跳阶段；门禁不通过就不能推进 | 手工改 `phase` 可跳（docs 还教用户这么做）；`advance` 只查当前 gate，删早期证据仍可推进到 final |
| D7 | `SKILL.md:87-90`；`docs/auto-research.md:65` | 作者在 DECISIONS.md 最终签核后才可提交 | `gate_final` 不读 DECISIONS；`--by human` 可伪造；删文件仍 PASS |
| D8 | `docs/auto-research.md:103` | 想回退就直接改 `state.json.project.phase`，并在 DECISIONS 记录原因 | 工具不强制记录；改 phase 后 `check` 只看新阶段，隐藏后续损坏 |
| D9 | `docs/auto-research.md:105` | 状态损坏时返回退出码 3 | 仅非法 JSON 返回 3；settings 类型错误/顶层非 dict 返回 1 + traceback |
| D10 | `docs/auto-research.md:109-110` | TestAutoResearch 覆盖"条数不足、清单未勾选、check 复核历史阶段" | 48 个测试中没有"清单未勾选"、没有"check 复核历史阶段"、没有"引用条数不足"的独立用例；`test_full_pipeline` 只测 happy path |
| D11 | `README.md:163` | tests 覆盖锁文件、归档安全、安装/校验/回滚 | 没有提 auto-research；实际新增 9 个测试，描述未更新（低） |
| D12 | `CHANGELOG.md:14` | CI 增加 auto-research 工具与模板的字节编译检查 | CI `py_compile` 只编译 `.py`，不编译/校验模板（模板是 md/json） |
| D13 | `THIRD-PARTY.md:3,6` | 仓库原创部分只列 `skills/research-stack/`；"skills/ 下除 research-stack 外均为上游移植" | `auto-research` 也是本仓库原创 MIT 技能，被错误归为第三方移植；`README.md:66` 自己写的是"本仓库原创" |
| D14 | `skills/auto-research/DSH-PORT.md:8` | `packaged files: 21` | HEAD lock 实际 19 个文件（`manifests/skills.lock.json` 的 auto-research 条目） |
| D15 | `skills/auto-research/NOTICE.md:1` | `NOTICE / 第三方声明` | 该技能是原创 MIT，不是第三方；措辞误导（低） |
| D16 | `README.md:101` | 代码门禁：引用必须 verified、claim 必须有证据、清单必须勾完 | 这三项的实现分别是"字符串等于 verified"、"list 非空"、`- [ ]` 计数；均已可绕过 |

---

## 七、附录：审计期间的并发工作树与 WIP 抽查（非 v0.2.0 结论）

### 7.1 并发修改事实

审计开始（约 11:08）时 HEAD 为 `013967e`，工作树干净；11:09:12 起 `skills/auto-research/scripts/auto_research.py` 被另一进程修改，随后 CHANGELOG/docs/SKILL/templates/tests/lock 等 10 个文件陆续变为 `M`。因此：

- 本报告全部代码行号、探测结果、NO-GO 结论均基于 **HEAD `013967e`**，不是当前工作树。
- 11:18 对工作树执行 `build_lock --check` 曾失败（`auto-research: SKILL.md`）；11:19 lock 更新后通过。说明 WIP 曾处于"锁文件与内容不一致"的中间态。
- 当前工作树未提交、未打 tag；请先完成修改、重新生成 lock、跑完整测试，再单独审计/发布。

### 7.2 WIP 已修（相对 HEAD）

从 diff 与实测看，WIP 已加入：

- `revert` 命令（带 reason/by），并拒绝手工 phase 编辑；
- `load_state` 校验 history 非空、条目 from/to 链、`history[-1].to == phase`、`by in {init,agent,human}`；
- `gate_final` 要求 DECISIONS 中存在 `[signoff]`；`advance` 进入 final 时拒绝缺失签核（且该条不可被 `--force` 绕过）；
- 重复 citation id、claim evidence 存在性/项目内路径、paper_section、必需模板、阈值 ≥1、title 非空；
- 对应用例/模板/文档更新（但未提交）。

### 7.3 WIP 仍存在的关键问题（实测）

| 问题 | WIP 实测 |
|---|---|
| 签核仍是自签 | `log --kind signoff --text "PI approved"` 后 `advance` 进入 final 成功；没有身份/外部签名，agent 可自行产生该行 |
| `advance` 仍不复核历史 | writing 后删 IDEA，`advance` 两次仍到 final；`check` 才返回 1 |
| 清单 `* [ ]` 仍绕过 | final `check` 仍 PASS |
| `init --force` 仍清空审计 | phase=ideation、history=1、签核丢失 |
| 坏 settings 仍 traceback | `minRefs=null` → exit 1 + TypeError |
| 代码围栏标题仍通过 | ideation `check` PASS |
| 历史链只校验 from/to，不校验内容 | 无法发现"产物在推进后被替换/删除"（除 from/to 外无哈希） |
| `--by human` 仍可伪造 | 仍是 CLI 字符串；WIP 的 `[signoff]` 行可由 agent 写 |
| 事务/并发仍未处理 | `save_state` 先于 DECISIONS 追加；无锁 |

结论：WIP 方向正确，但**不能把"WIP 已加 signoff 检查"误认为"人工签核已强制"**；在 WIP 上仍需完成 M4/M5/M6/M8/M9 的剩余部分，并补测试。

---

## 八、审计副作用与限制

- 本次审计**未联网、未推送、未修改仓库文件**；所有行为实验在 `%TEMP%` 的 `git archive HEAD` 快照上执行，并设置 `PYTHONDONTWRITEBYTECODE=1`。
- 仓库当前存在的 `__pycache__`（`tools/` 11:11:56，`tests/`、`skills/auto-research/scripts/` 11:18:31）是并发修改进程生成的运行时产物，已被 `.gitignore` 忽略；本次审计未写入。
- **副作用声明（需要知悉）**：一次集成测试误用了 PowerShell 只读变量 `$home`（赋值被拒绝，值仍为用户主目录），导致 `dsh_skills.py install --mode full --no-backup` 以 `%USERPROFILE%` 作为 DSH home，写入了 `%USERPROFILE%\skills`（不是仓库，也不是 `~/.dsh/skills`）。该目录此前已存在（创建于 2026-11-23），安装器按 `--no-backup` 语义替换了其中 16 个同名技能目录，**未保留旧版本**；我未删除该目录，`%USERPROFILE%\.dsh\skills` 未受影响。随后已改用独立 `$dshHome` 临时目录重跑并清理。若该目录含需要的旧版本，请从备份/版本库恢复；这是我的操作失误，特此披露。
- 未做联网的 DOI/URL 真实性验证（任务要求不联网）；因此 M2 的"引用真实性"结论是**代码层门禁缺失**，不是对具体论文的事实核查。
- 未对 ARS 归档内 5 个技能做逐文件人工内容审计；本次按锁文件/selftest/build_lock 的机械一致性验收。
