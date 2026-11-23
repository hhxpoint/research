# THIRD-PARTY NOTICES / 第三方许可证说明

本仓库自身的代码与文档（`tools/`、`tests/`、`docs/`、`manifests/`、`skills/research-stack/`、README 等）
采用 [MIT License](LICENSE)，Copyright (c) 2026 hhxpoint。

`skills/` 下除 `research-stack` 外的技能、以及 `vendor/ars-dsh-*.tar.gz` 内的技能，
均为上游开源项目的**移植/适配版本**（仅插入 DSH 运行说明、合并 `shared/` 资源、改写命令路径，
未改动方法论正文），其版权归上游作者所有，按各自许可证再分发。

## 汇总表

| 来源 | 作者 / 版权 | 许可证 | 本仓库位置 | 固定 commit |
|---|---|---|---|---|
| [Imbad0202/academic-research-skills](https://github.com/Imbad0202/academic-research-skills)（ARS） | Copyright (c) 2026 Cheng-I Wu | **CC BY-NC 4.0**（禁止商业使用） | `vendor/ars-dsh-v3.24.4-d103b100.tar.gz` | `d103b1005bb8c9f7a597e6a7ed473b75dcf8830e` |
| [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) | Copyright (c) 2025 K-Dense Inc. | MIT | `skills/scientific-writing/`、`skills/citation-management/`、`skills/scientific-visualization/`、`skills/venue-templates/` | `c21d13b3cc2894680229ba9959a53281acb9200e` |
| [wanshuiyin/Auto-claude-code-research-in-sleep](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep)（ARIS） | Copyright (c) 2026 wanshuiyin | MIT | `skills/research-lit/`、`skills/experiment-plan/`、`skills/analyze-results/` | `4ba94ae2a1c1fbbb14858750dd8764cabf6c28bd` |
| [zLanqing/codex-claude-academic-skills](https://github.com/zLanqing/codex-claude-academic-skills) | Copyright (c) 2026 zLanqing | MIT | `skills/research-writing-skill/` | `7ed6377f0efb6a38951b48ef03b19d996e454b1f` |
| [uditgoenka/autoresearch](https://github.com/uditgoenka/autoresearch) | Copyright (c) 2026 Udit Goenka | MIT | `skills/autoresearch/`（DSH 适配版） | `7bddd056dfd0b0ded8360588d8101b1ecb5c0baa` |
| Elsevier elsarticle 模板/样式（`venue-templates` 内资产） | Copyright 2007-2026 Elsevier Ltd | **LPPL 1.3c** | `skills/venue-templates/assets/journals/`（6 个 `.tex`/`.bst`，保留原始文件头） | 随 K-Dense `c21d13b...` 快照 |

**每个技能目录（仓库内与安装后）都包含**：`NOTICE.md`（来源、固定 commit、许可证 URI、版权、修改说明）、`LICENSE.txt`（完整许可证原文）、`DSH-PORT.md`（移植记录）。ARS 技能另含完整 CC BY-NC 4.0 文本与非商业声明；`venue-templates` 另含 LPPL 披露。

完整许可证原文见 `vendor/licenses/`：

- `ARS-CC-BY-NC-4.0.txt`
- `K-Dense-scientific-agent-skills-MIT.txt`
- `ARIS-MIT.txt`
- `zLanqing-MIT.txt`
- `uditgoenka-autoresearch-MIT.txt`
- `LPPL-1.3c.txt`（Elsevier elsarticle 资产）

bundle 级别的非商业声明另见 [`vendor/ARS-NOTICE.md`](vendor/ARS-NOTICE.md)。

## 重要提示

1. **ARS 仅限非商业用途**：CC BY-NC 4.0 禁止商业使用。个人学术研究、非商业课题组内部使用可以；
   任何商业化产品、付费服务、对外商业交付使用前必须获得上游作者的另行授权。
2. MIT 技能允许再分发，但**必须保留版权声明与本许可证文本**。本仓库已保留，修改说明见各技能目录的
   `DSH-PORT.md`。
3. 本仓库对第三方技能的所有修改均可复核：`manifests/skills.lock.json` 记录了每个文件的 sha256，
   上游固定 commit 见上表；`tools/build_lock.py --check` 可验证仓库内容与锁文件一致。
4. `venue-templates` 中的 Elsevier elsarticle 文件按 **LPPL 1.3c** 分发（不是 MIT），已保留原始版权头并在技能目录内单独披露。
5. 第三方技能可能指示 agent 执行本地脚本（Python/Bash）。安装/使用前请阅读 `SECURITY.md`，
   并对高风险操作保留人工确认。
