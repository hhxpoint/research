# Changelog

本仓库遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 与语义化版本。

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
