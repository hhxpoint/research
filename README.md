# research

**hhxpoint 的科研技能栈**：把「自动科研 + 论文写作」这一套 agent skills 稳定沉淀成**可复现安装**的仓库。

[![validate](https://github.com/hhxpoint/research/actions/workflows/validate.yml/badge.svg)](https://github.com/hhxpoint/research/actions/workflows/validate.yml)

- **15 个 DSH 技能**：5 件套论文流水线（ARS）+ 4 个写作/引用/图表/顶会模板（K-Dense）+ 3 个文献/实验技能（ARIS）+ 中文写作 + 指标迭代循环 + 原创科研路由技能。
- **离线、可校验的安装器**：不依赖网络；所有文件带 sha256；安装前校验、安装时备份、失败回滚、原子替换。
- **明确的边界**：固定上游 commit、许可证分级（MIT / CC BY-NC 4.0）、DSH 技能规范实测文档。
- **调研留档**：两份生态调研报告，解释为什么选这些、放弃了哪些。

> 技能安装到 `~/.dsh/skills/`（DeepSeek Harness 用户级技能根），DSH 会在下一个模型步骤自动发现，无需重启。

---

## 快速开始

前置：Python ≥ 3.10、PyYAML、DeepSeek Harness（DSH）。

```powershell
# 1) 体检（检查 Python / 锁文件 / 归档 / DSH 目录）
python tools\dsh_skills.py doctor

# 2) 安装全部 15 个技能（有备份与回滚）
python tools\dsh_skills.py install --mode full

# 3) 校验安装结果（逐文件 sha256 + frontmatter 规则）
python tools\dsh_skills.py verify --require-all
```

Windows 也可以直接：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1   # 默认 full
powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1 --mode minimal
```

Linux / macOS：

```bash
python3 tools/dsh_skills.py install --mode full
# 或
./scripts/install.sh
```

安装后在 DSH 会话里直接说需求即可（技能会按描述自动选中），例如：
`用 research-stack 规划这条论文路线`、`用 academic-paper 按 NeurIPS 格式成稿`、
`用 citation-management 校验 references`。

---

## 技能清单

| 技能 | 来源 | 许可证 | 用途 |
|---|---|---|---|
| `research-stack` | 本仓库原创 | MIT | 科研总入口：按任务路由到其余技能 + 四条推荐流水线 |
| `academic-paper` | ARS | CC BY-NC 4.0 | 12-agent 论文写作流水线，11 模式（含 citation-check / rebuttal-audit） |
| `academic-paper-reviewer` | ARS | CC BY-NC 4.0 | 5 席位审稿面板（full / re-review / methodology / calibration） |
| `academic-pipeline` | ARS | CC BY-NC 4.0 | 10 阶段总编排，含 Stage 2.5/4.5 诚信闸门 |
| `deep-research` | ARS | CC BY-NC 4.0 | 13-agent 深度研究，8 模式（含系统综述 / PRISMA） |
| `sr-screener` | ARS | CC BY-NC 4.0 | 系统综述筛选、双盲裁决、PRISMA 2020 计数 |
| `scientific-writing` | K-Dense | MIT | 手稿撰写/修订/审计：证据溯源、reporting guideline、一致性检查 |
| `citation-management` | K-Dense | MIT | OpenAlex/PubMed/Google Scholar 检索、引用校验、BibTeX 生成 |
| `scientific-visualization` | K-Dense | MIT | 期刊级图表：多面板、色盲友好、期刊导出规格 |
| `venue-templates` | K-Dense | MIT + 内含 LPPL 1.3 资产 | Nature/Science/Cell/NeurIPS/PLOS/NIH/NSF 模板与格式规则 |
| `research-lit` | ARIS | MIT | 找论文、related work、文献精读 |
| `experiment-plan` | ARIS | MIT | claim-driven 实验计划：消融矩阵、评估协议、算力预算 |
| `analyze-results` | ARIS | MIT | 实验结果统计、对比表、趋势与下一步实验 |
| `research-writing-skill` | zLanqing | MIT | 中文优先写作/润色/返修信/审稿回应 |
| `autoresearch` | uditgoenka | MIT | 指标驱动迭代循环（改一处→机械验证→keep/revert→记账） |

**预设**（`manifests/skills.lock.json` 中定义）：

| 预设 | 内容 | 适用 |
|---|---|---|
| `minimal` | research-stack + research-lit + scientific-writing + citation-management + research-writing-skill | 日常读写，占用量小 |
| `writing` | 写作与审稿相关 9 个（含 ARS 写作/审稿/编排） | 论文冲刺 |
| `full` | 全部 15 个（默认） | 全功能 |

```powershell
python tools\dsh_skills.py install --mode minimal
python tools\dsh_skills.py install --only academic-paper,deep-research
python tools\dsh_skills.py install --mode full --exclude sr-screener,scientific-visualization
```

---

## 安装器做了什么（稳健性设计）

| 机制 | 说明 |
|---|---|
| 离线 | 技能内容都在仓库里（MIT 技能为明文目录，ARS 为 `.tar.gz` 归档），安装不需要网络 |
| 完整性 | `manifests/skills.lock.json` 记录每个技能的每个文件 sha256；安装前校验，`verify` 可复查 |
| 原子替换 | 先进临时目录装配、校验通过后再 `os.replace` 换入，避免半安装状态 |
| 备份 | 覆盖已存在的技能前，移动到 `~/.dsh/skills-backup/<时间戳>/` |
| 回滚 | 多技能安装中途失败时，已换入的技能会回滚、旧版本还原 |
| 幂等 | 内容相同则跳过；`--force` 可强制重装 |
| 防路径穿越 | 解压归档时拒绝绝对路径、`..`、符号链接/硬链接 |
| 可审计 | 每个技能目录带 `DSH-PORT.md`（来源/commit/修改点）+ `NOTICE.md`（署名/许可证 URI）+ `LICENSE.txt`（完整许可证原文）；ARS 另注明非商业限制；venue-templates 单独披露 LPPL 资产 |
| 安全边界 | 安装不执行任何技能脚本；脚本只在你/模型主动运行时才执行 |

常用命令：

```powershell
python tools\dsh_skills.py list                       # 目录 + 安装状态
python tools\dsh_skills.py install --dry-run          # 只打印计划
python tools\dsh_skills.py verify                     # 校验（缺失仅警告）
python tools\dsh_skills.py verify --require-all       # 缺失也算失败
python tools\dsh_skills.py uninstall --names deep-research --keep   # 先看再删
python tools\dsh_skills.py uninstall --names deep-research          # 删除并备份
```

退出码：`0` 成功；`1` verify/selftest/doctor 检查失败（含已安装文件哈希不符）；`2` 用法或配置错误（参数、路径不可写等）；`3` 安装阶段的来源完整性错误（归档/载荷哈希不符、归档不安全）。

---

## 目录结构

```
research/
├─ README.md                    本文件
├─ LICENSE                      MIT（本仓库原创代码与文档）
├─ THIRD-PARTY.md               第三方技能版权与许可证汇总
├─ SECURITY.md                  风险模型与供应链说明
├─ CHANGELOG.md
├─ skills/                      可再分发的技能（明文目录，MIT）
│  ├─ research-stack/           原创科研路由技能
│  ├─ autoresearch/             uditgoenka 适配版（含 14 个子命令协议）
│  ├─ research-lit/ experiment-plan/ analyze-results/       ARIS
│  ├─ scientific-writing/ citation-management/
│  │  scientific-visualization/ venue-templates/            K-Dense
│  └─ research-writing-skill/   zLanqing
├─ vendor/
│  ├─ ars-dsh-v3.24.4-d103b100.tar.gz   ARS 5 件套（CC BY-NC 4.0，单归档分发）
│  ├─ ARS-NOTICE.md             非商业限制与修改说明（bundle 级）
│  └─ licenses/                 MIT / CC BY-NC / LPPL 许可证原文
├─ manifests/skills.lock.json   技能清单 + 逐文件 sha256 + 预设 + 来源 commit
├─ tools/
│  ├─ dsh_skills.py             安装 / 校验 / 卸载 / doctor / selftest
│  ├─ build_lock.py             维护者：内存构建 + 原子写入 ARS 归档与锁文件，--check 校验自洽
│  └─ apply_notices.py          维护者：生成/校验 NOTICE、LICENSE、DSH-PORT 与 LPPL 披露
├─ tests/                       unittest：锁文件、归档安全、安装/校验/回滚
├─ scripts/install.ps1|.sh      薄封装
├─ docs/
│  ├─ auto-research-skills-survey.md   自动化科研技能生态调研（2026-11-23）
│  ├─ paper-writing-skills-survey.md   论文写作技能调研（2026-11-23）
│  ├─ dsh-skill-spec.md                DSH 技能规范与移植指南（实测）
│  ├─ install.md                       安装 / 升级 / 回滚 / 排障
│  ├─ usage.md                         组合用法与提示词示例
│  └─ maintenance.md                   升级上游、新增技能、发布流程
└─ .github/workflows/validate.yml      CI：Linux/Windows × Python 3.10/3.12
```

---

## 文档

- [安装与运维](docs/install.md)：`DSH_HOME` 自定义、备份恢复、卸载、常见问题。
- [使用指南](docs/usage.md)：顶会投稿 / 中文期刊 / 系统综述 / 指标迭代四条流水线与提示词示例。
- [DSH 技能规范](docs/dsh-skill-spec.md)：技能目录、frontmatter 规则、静默失败原因、移植检查表。
- [维护手册](docs/maintenance.md)：上游升级、重新生成锁文件、新增自有技能、发布与网络兜底。
- 调研留档：[auto-research](docs/auto-research-skills-survey.md) ｜ [论文写作](docs/paper-writing-skills-survey.md)。
- 质量记录：[v0.1.0 独立审计与 v0.1.1 处置](docs/audit-2026-11-23.md)。

---

## 许可证

- 本仓库原创部分：[MIT](LICENSE)。
- 第三方技能：按各自许可证随附（MIT 保留版权声明；**ARS 为 CC BY-NC 4.0，禁止商业使用**）。
  每个已安装技能目录都带 `NOTICE.md` + `LICENSE.txt`（ARS 另含完整 CC 文本与非商业声明）；
  `venue-templates` 内含 Elsevier elsarticle 资产，按 LPPL 1.3 单独披露。
  详见 [THIRD-PARTY.md](THIRD-PARTY.md)、`vendor/licenses/` 与 `vendor/ARS-NOTICE.md`。

## 维护

- 技能版本固定：上游 commit + 逐文件 sha256 都在锁文件里，升级必须显式重建锁文件并走 review。
- CI 会检查：`build_lock.py --check`、`selftest`、单元测试、临时目录安装与校验。
- 问题反馈：在本仓库开 issue；第三方技能内容问题请同时反馈上游并注明 commit。
