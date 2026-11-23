# DSH port provenance — autoresearch

- upstream: https://github.com/uditgoenka/autoresearch
- commit: `7bddd056dfd0b0ded8360588d8101b1ecb5c0baa`
- license: MIT 
- imported: 2026-11-23
- upstream SKILL.md: unchanged body, DSH port note prepended
- merged dirs: ['references/commands', 'references/commands/autoresearch.md']
- files installed: 15
- extra notes: Claude Code hooks 未移植：不自动 push/deploy、不读 .env、每轮只改一处并先 commit 等安全约束已由上游正文表述，模型须自行遵守；危险命令由 DSH 权限策略兜底。
- uninstall: remove this directory (`~/.dsh/skills/autoresearch`)
