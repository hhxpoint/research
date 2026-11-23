# Security Policy

## 风险模型

本仓库分发的是 **agent 技能（prompt 包）**，其中部分技能自带脚本（Python / shell）。
安装技能本身不会执行代码，但**模型在加载技能后可能按正文指示运行这些脚本**，
也可能按技能要求读写项目文件。请把它们当作可执行的第三方代码对待：

- 安装前可先 `python tools/dsh_skills.py install --mode full --dry-run` 查看将安装什么；
- 每个安装文件都有 sha256 记录（`manifests/skills.lock.json`），`verify` 可发现被篡改的技能；
- 技能来源与固定 commit 见 `THIRD-PARTY.md`，可自行复核；
- 高风险操作（联网安装依赖、删除文件、发布/推送、读取密钥）应保留人工确认；
- 不要把密钥、`.env`、未公开数据放在技能要求读取的路径下。

## 支持的版本

仅维护最新 release 的技能锁文件与安装器。历史版本请 checkout 对应 tag 后自行校验。

## 报告漏洞

- 安装器 / 构建脚本 / 文档问题：在本仓库开 issue（请勿在公开 issue 中贴出利用代码细节，
  可以先只描述影响面）。
- 第三方技能内容问题：请同时反馈给上游仓库，并在本仓库 issue 中注明上游链接与 commit。

## 供应链

- 所有第三方内容在入库时固定版本（commit + sha256），升级需要显式修改 `tools/build_lock.py`
  中的 `SOURCES` 并重新生成锁文件，review 时可直接 diff。
- `tools/build_lock.py --check` 在 CI 中执行，防止提交内容与锁文件脱节。
