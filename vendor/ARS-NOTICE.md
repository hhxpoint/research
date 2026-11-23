# ARS bundle notice / 非商业使用声明

本目录中的 `ars-dsh-v3.24.4-d103b100.tar.gz` 打包了
[academic-research-skills（ARS）](https://github.com/Imbad0202/academic-research-skills)
的 5 个技能（`academic-paper`、`academic-paper-reviewer`、`academic-pipeline`、
`deep-research`、`sr-screener`）的 **DSH 适配版**：

- 上游 commit：`d103b1005bb8c9f7a597e6a7ed473b75dcf8830e`（ARS v3.24.4）
- 上游作者：Cheng-I Wu
- 许可证：**Creative Commons Attribution-NonCommercial 4.0 International（CC BY-NC 4.0）**
- 完整许可证原文：[`licenses/ARS-CC-BY-NC-4.0.txt`](licenses/ARS-CC-BY-NC-4.0.txt)

## 允许

- 个人学习、学术研究、非商业课题组内部使用；
- 为个人/非商业用途复制、修改、再分发（需保留署名与许可证声明，并说明修改）。

## 禁止

- **任何商业使用**：包括商业产品、付费服务、对外商业交付、以营利为目的的再分发。
  商用前必须获得上游作者的另行授权。

## 本仓库做的修改

仅为在 DeepSeek Harness 中运行所做的适配，方法论正文未改动：

1. 在每个技能的 `SKILL.md` 正文前插入 DSH 运行说明（工具名映射、`$ARGUMENTS` 说明）；
2. 把上游仓库根目录的 `shared/` 合并进每个技能目录（满足相对路径引用）；
3. 每个技能目录增加 `DSH-PORT.md`（来源、commit、许可证、修改点、卸载方式）。

安装与校验方式见仓库根目录 `README.md`、`docs/install.md`；
逐文件 sha256 见 `manifests/skills.lock.json`。
