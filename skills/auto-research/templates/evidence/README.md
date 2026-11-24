# evidence

<!-- AUTO-RESEARCH: TODO -->

- `citations.json`：引用核验台账。每条必须 `status: verified`，并记录核验来源与时间。
- `claim_map.json`：论文 claim → 证据（`results/` 文件、`figures/`、代码路径）的映射。

这两份文件是 `writing` 阶段门禁的一部分：不允许"论文写了但证据对不上"。

- `citations.json` 的 `id` 必须唯一；重复 id 会门禁失败。
- `claim_map.json` 的 `paper_section` 必须等于 `PAPER.md` 中存在的 `##` 标题；
  `evidence` 里的每个路径必须是项目内真实存在的文件（或 http/https/doi/arxiv 链接，或用 `*` 的 glob 且能匹配到文件），不允许写不存在的证据。
