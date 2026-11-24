#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""auto-research：DSH 原生的自主科研状态机（阶段门禁 + 证据审计）。

这不是"一键生成论文"的脚本，而是把**科研过程**沉淀成可恢复、可审计、带门禁的
项目状态机：agent 按阶段推进，每个阶段有明确的产物与进入下一阶段的门禁；
门禁不过就退回补证据，而不是让模型编造。

项目目录结构（`init` 自动创建）：

  <project>/
  ├─ AUTO-RESEARCH.md         项目说明与阶段地图
  ├─ state.json               阶段、设置、历史（机器可读，agent 维护）
  ├─ IDEA.md                  研究问题、假设、贡献、范围与风险
  ├─ LIT_REVIEW.md            检索策略、关键工作、空白分析
  ├─ EXPERIMENT_PLAN.md       基线、指标、消融、算力预算、成功标准
  ├─ RESULTS.md               结果表、统计校验、偏差记录
  ├─ PAPER.md                 论文/报告正文
  ├─ REVIEW.md                审稿意见（模拟或真实）
  ├─ REBUTTAL.md              逐条回复
  ├─ SUBMISSION_CHECKLIST.md  投稿前检查清单
  ├─ PROVENANCE.md            环境、数据、命令、AI 使用披露
  ├─ DECISIONS.md             决策与人工签核（append-only）
  ├─ evidence/
  │  ├─ citations.json        引用核验台账（每条 status 必须 verified）
  │  └─ claim_map.json        claim → 证据映射
  ├─ experiments/             实验代码/配置
  ├─ results/                 原始结果（json/csv）
  └─ figures/                 图表

阶段：ideation → literature → experiment_plan → experiments → writing → review → final

用法：
  python auto_research.py init <dir> --title "..." --question "..." [--venue "..."]
  python auto_research.py status <dir> [--json]
  python auto_research.py next <dir>
  python auto_research.py check <dir> [--json]
  python auto_research.py advance <dir> [--by agent|human] [--force --reason "..."]
  python auto_research.py revert <dir> --to <phase> --reason "..."   # 审计式回退
  python auto_research.py log <dir> --text "..."      # 记录决策/签核/异常

退出码：0 成功；1 门禁/审计不通过；2 用法错误；3 状态文件损坏/完整性错误。
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import sys
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parent
TEMPLATE_CANDIDATES = (
    TOOL_DIR.parent / "templates",                # skill layout: <skill>/scripts -> <skill>/templates
    TOOL_DIR.parent.parent / "skills" / "auto-research" / "templates",  # repo launcher layout
)
SCHEMA_VERSION = 1
SENTINEL = "AUTO-RESEARCH: TODO"

PHASES = [
    "ideation",
    "literature",
    "experiment_plan",
    "experiments",
    "writing",
    "review",
    "final",
]

PHASE_GUIDE = {
    "ideation": {
        "artifact": "IDEA.md",
        "skills": "research-stack / research-lit / deep-research",
        "action": "写清研究问题、可证伪的假设、贡献点、范围与风险；用 ask_user_question 与作者确认选题。",
    },
    "literature": {
        "artifact": "LIT_REVIEW.md + evidence/citations.json",
        "skills": "deep-research / research-lit / citation-management",
        "action": "做检索与综述，逐条核验引用并写入 evidence/citations.json（status 全部 verified）。",
    },
    "experiment_plan": {
        "artifact": "EXPERIMENT_PLAN.md",
        "skills": "experiment-plan",
        "action": "给出基线、指标、消融矩阵、算力预算、成功/失败判据；与作者确认后再跑。",
    },
    "experiments": {
        "artifact": "RESULTS.md + results/",
        "skills": "autoresearch / analyze-results",
        "action": "执行实验（可用 autoresearch 做指标循环），原始结果落 results/，偏差与失败运行如实记录。",
    },
    "writing": {
        "artifact": "PAPER.md + evidence/claim_map.json",
        "skills": "academic-paper / research-writing-skill / scientific-writing",
        "action": "按目标 venue 模板写作；每个 claim 在 claim_map.json 中绑定证据；引用必须已核验。",
    },
    "review": {
        "artifact": "REVIEW.md + REBUTTAL.md",
        "skills": "academic-paper-reviewer（或 subagent 模拟审稿）",
        "action": "获取审稿意见并逐条回复；先做对抗式审稿（Devil's Advocate），不要只写正面结论。",
    },
    "final": {
        "artifact": "SUBMISSION_CHECKLIST.md + PROVENANCE.md",
        "skills": "venue-templates / citation-management / office-*",
        "action": "完成投稿检查清单、复现信息、AI 使用与局限声明；人工签核后才可提交。",
    },
}

REQUIRED_HEADINGS = {
    "ideation": {
        "IDEA.md": ["Research question", "Hypotheses", "Contribution", "Scope and risks"],
    },
    "literature": {
        "LIT_REVIEW.md": ["Search strategy", "Key works", "Gap analysis"],
    },
    "experiment_plan": {
        "EXPERIMENT_PLAN.md": ["Baselines", "Metrics", "Ablations", "Compute budget", "Success criteria"],
    },
    "experiments": {
        "RESULTS.md": ["Results table", "Statistical checks", "Deviations"],
    },
    "writing": {
        "PAPER.md": ["Abstract", "Introduction", "Method", "Experiments", "Related work", "Limitations"],
    },
    "review": {
        "REVIEW.md": ["Summary", "Major comments", "Minor comments"],
        "REBUTTAL.md": ["Response summary"],
    },
    "final": {
        "SUBMISSION_CHECKLIST.md": ["Checklist", "AI disclosure"],
        "PROVENANCE.md": ["Environment", "Data", "Commands", "AI disclosure"],
    },
}

IGNORED_NAMES = {"__pycache__", ".git", ".pytest_cache"}
MIN_SECTION_CHARS = 20

REQUIRED_TEMPLATES = (
    "AUTO-RESEARCH.md", "IDEA.md", "LIT_REVIEW.md", "EXPERIMENT_PLAN.md", "RESULTS.md",
    "PAPER.md", "REVIEW.md", "REBUTTAL.md", "SUBMISSION_CHECKLIST.md", "PROVENANCE.md",
    "DECISIONS.md", "evidence/README.md", "evidence/citations.json", "evidence/claim_map.json",
)


class AutoResearchError(Exception):
    exit_code = 2


class GateError(AutoResearchError):
    exit_code = 1


class IntegrityError(AutoResearchError):
    exit_code = 3


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def templates_dir() -> Path:
    for candidate in TEMPLATE_CANDIDATES:
        if (candidate / "IDEA.md").is_file():
            missing = [name for name in REQUIRED_TEMPLATES if not (candidate / name).is_file()]
            if missing:
                raise IntegrityError(
                    f"auto-research templates incomplete in {candidate}: missing {missing}"
                )
            return candidate
    raise IntegrityError(
        "auto-research templates not found; looked in: "
        + ", ".join(str(c) for c in TEMPLATE_CANDIDATES)
    )


def project_path(raw: str) -> Path:
    return Path(raw).expanduser().resolve()


def state_path(project: Path) -> Path:
    return project / "state.json"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def strip_noise(text: str) -> str:
    """Remove fenced code blocks and HTML comments before structural checks."""
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.sub(r"~~~.*?~~~", "", text, flags=re.S)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    return text


def single_line(text: str) -> str:
    """Collapse newlines/control chars so log arguments cannot inject entries."""
    text = re.sub(r"[\r\n]+", " ", text)
    text = re.sub(r"[\x00-\x1f\x7f]", "", text)
    return re.sub(r"\s{2,}", " ", text).strip()


def require_file(project: Path, rel: str, problems: list[str], optional: bool = False) -> str | None:
    path = project / rel
    if not path.is_file():
        if not optional:
            problems.append(f"missing artifact: {rel}")
        return None
    text = read_text(path)
    if SENTINEL in text:
        problems.append(f"artifact still contains placeholder sentinel: {rel}")
    if "FILL:" in text:
        problems.append(f"artifact still contains template FILL placeholders: {rel}")
    if rel.endswith(".md") and not text.strip():
        problems.append(f"artifact is empty: {rel}")
    return text


def require_headings(text: str | None, rel: str, headings: list[str], problems: list[str]) -> None:
    if text is None:
        return
    clean = strip_noise(text)
    lines = clean.splitlines()
    for heading in headings:
        pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$")
        index = next((i for i, line in enumerate(lines) if pattern.match(line)), None)
        if index is None:
            problems.append(f"{rel}: missing section heading '## {heading}'")
            continue
        body: list[str] = []
        for line in lines[index + 1 :]:
            if re.match(r"^##\s+", line):
                break
            body.append(line)
        content = re.sub(r"^\s*[-*+]\s*(\[[ xX]\]\s*)?", "", "\n".join(body), flags=re.M)
        if len(re.sub(r"\s", "", content)) < MIN_SECTION_CHARS:
            problems.append(
                f"{rel}: section '## {heading}' needs at least {MIN_SECTION_CHARS} "
                "non-whitespace characters of content"
            )


def load_json(path: Path, problems: list[str], kind: str):
    if not path.is_file():
        problems.append(f"missing {kind}: {path.name}")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        problems.append(f"{kind} is not valid JSON: {path.name}: {exc}")
        return None


def citation_entries(project: Path, problems: list[str]) -> list[dict]:
    data = load_json(project / "evidence" / "citations.json", problems, "citation ledger")
    if data is None:
        return []
    entries = data.get("citations") if isinstance(data, dict) else data
    if not isinstance(entries, list):
        problems.append("evidence/citations.json: expected a list or {'citations': [...]}")
        return []
    return [e for e in entries if isinstance(e, dict)]


def claim_entries(project: Path, problems: list[str]) -> list[dict]:
    data = load_json(project / "evidence" / "claim_map.json", problems, "claim map")
    if data is None:
        return []
    entries = data.get("claims") if isinstance(data, dict) else data
    if not isinstance(entries, list):
        problems.append("evidence/claim_map.json: expected a list or {'claims': [...]}")
        return []
    return [e for e in entries if isinstance(e, dict)]


def check_citations(project: Path, settings: dict, problems: list[str]) -> None:
    entries = citation_entries(project, problems)
    if not entries:
        if (project / "evidence" / "citations.json").is_file():
            problems.append("evidence/citations.json: no citation entries")
        return
    minimum = int(settings.get("minRefs", 10))
    if len(entries) < minimum:
        problems.append(f"evidence/citations.json: {len(entries)} citations < minRefs={minimum}")
    for index, entry in enumerate(entries, 1):
        status = str(entry.get("status", "")).lower()
        if status != "verified":
            problems.append(
                f"citations[{index}]: status={status or 'missing'!r} (must be 'verified')"
            )
        if not str(entry.get("id", "")).strip():
            problems.append(f"citations[{index}]: missing id")
        if not str(entry.get("title", "")).strip():
            problems.append(f"citations[{index}]: missing title")
        locator = str(entry.get("doi_or_url", "")).strip()
        if not re.match(r"^(https?://|10\.\d{4,9}/)", locator):
            problems.append(f"citations[{index}]: doi_or_url must be an http(s) URL or DOI")
        verification = entry.get("verification")
        if not isinstance(verification, dict):
            problems.append(f"citations[{index}]: missing verification object")
        else:
            for field in ("source", "checked_at"):
                if not str(verification.get(field, "")).strip():
                    problems.append(f"citations[{index}]: verification.{field} is missing")
    seen: dict[str, int] = {}
    for index, entry in enumerate(entries, 1):
        cid = str(entry.get("id", "")).strip()
        if not cid:
            continue
        if cid in seen:
            problems.append(
                f"citations[{index}]: duplicate id {cid!r} (first at citations[{seen[cid]}])"
            )
        else:
            seen[cid] = index


def _external_evidence(item: str) -> bool:
    lowered = item.strip().lower()
    return lowered.startswith(("http://", "https://", "doi:", "arxiv:"))


def check_claim_map(
    project: Path, settings: dict, problems: list[str], paper_text: str | None = None
) -> None:
    entries = claim_entries(project, problems)
    if not entries:
        if (project / "evidence" / "claim_map.json").is_file():
            problems.append("evidence/claim_map.json: no claim entries")
        return
    minimum = int(settings.get("minClaims", 5))
    if len(entries) < minimum:
        problems.append(f"evidence/claim_map.json: {len(entries)} claims < minClaims={minimum}")
    seen: dict[str, int] = {}
    project_resolved = project.resolve()
    for index, entry in enumerate(entries, 1):
        cid = str(entry.get("id", "")).strip()
        if not cid:
            problems.append(f"claims[{index}]: missing id")
        elif cid in seen:
            problems.append(f"claims[{index}]: duplicate id {cid!r} (first at claims[{seen[cid]}])")
        else:
            seen[cid] = index
        if not str(entry.get("claim", "")).strip():
            problems.append(f"claims[{index}]: missing claim text")
        evidence = entry.get("evidence")
        if not evidence or not isinstance(evidence, list):
            problems.append(f"claims[{index}]: evidence must be a non-empty list")
        else:
            for item in evidence:
                if not isinstance(item, str) or not item.strip():
                    problems.append(f"claims[{index}]: evidence entries must be non-empty strings")
                    continue
                item = item.strip()
                if _external_evidence(item):
                    continue
                if "*" in item or "?" in item:
                    if not list(project.glob(item)):
                        problems.append(
                            f"claims[{index}]: evidence pattern matches nothing: {item!r}"
                        )
                    continue
                target = (project / item).resolve()
                if target != project_resolved and project_resolved not in target.parents:
                    problems.append(
                        f"claims[{index}]: evidence path escapes the project: {item!r}"
                    )
                elif not target.is_file():
                    problems.append(f"claims[{index}]: evidence file not found: {item!r}")
        if str(entry.get("status", "")).lower() not in {"verified", "supported"}:
            problems.append(f"claims[{index}]: status must be verified/supported")
        if paper_text is not None:
            section = str(entry.get("paper_section", "")).strip()
            if not section:
                problems.append(f"claims[{index}]: missing paper_section")
            else:
                heading = section[3:].strip() if section.startswith("##") else section
                pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.M)
                if not pattern.search(paper_text):
                    problems.append(
                        f"claims[{index}]: paper_section {section!r} not found as "
                        f"'## {heading}' in PAPER.md"
                    )


def count_results(project: Path) -> int:
    root = project / "results"
    if not root.is_dir():
        return 0
    count = 0
    for p in root.rglob("*"):
        if (
            p.is_file()
            and p.stat().st_size > 0
            and p.name not in {".gitkeep"}
            and not any(part in IGNORED_NAMES for part in p.parts)
        ):
            count += 1
    return count


def review_ids(text: str | None) -> set[str]:
    if not text:
        return set()
    return set(re.findall(r"^###\s+(R\d+)\b", strip_noise(text), re.M))


def rebuttal_body_ok(text: str | None, rid: str) -> bool:
    if not text:
        return False
    lines = strip_noise(text).splitlines()
    pattern = re.compile(rf"^###\s+{rid}\b")
    for index, line in enumerate(lines):
        if pattern.match(line):
            body: list[str] = []
            for follow in lines[index + 1 :]:
                if re.match(r"^###\s+", follow) or re.match(r"^##\s+", follow):
                    break
                body.append(follow)
            return len(re.sub(r"\s", "", "".join(body))) >= 5
    return False


# --------------------------------------------------------------------------- #
# phase gates (entry criteria for *leaving* the phase)
# --------------------------------------------------------------------------- #
def gate_ideation(project: Path, settings: dict) -> list[str]:
    problems: list[str] = []
    text = require_file(project, "IDEA.md", problems)
    require_headings(text, "IDEA.md", REQUIRED_HEADINGS["ideation"]["IDEA.md"], problems)
    return problems


def gate_literature(project: Path, settings: dict) -> list[str]:
    problems: list[str] = []
    text = require_file(project, "LIT_REVIEW.md", problems)
    require_headings(text, "LIT_REVIEW.md", REQUIRED_HEADINGS["literature"]["LIT_REVIEW.md"], problems)
    check_citations(project, settings, problems)
    return problems


def gate_experiment_plan(project: Path, settings: dict) -> list[str]:
    problems: list[str] = []
    text = require_file(project, "EXPERIMENT_PLAN.md", problems)
    require_headings(
        text,
        "EXPERIMENT_PLAN.md",
        REQUIRED_HEADINGS["experiment_plan"]["EXPERIMENT_PLAN.md"],
        problems,
    )
    return problems


def gate_experiments(project: Path, settings: dict) -> list[str]:
    problems: list[str] = []
    text = require_file(project, "RESULTS.md", problems)
    require_headings(text, "RESULTS.md", REQUIRED_HEADINGS["experiments"]["RESULTS.md"], problems)
    minimum = int(settings.get("minResultFiles", 1))
    found = count_results(project)
    if found < minimum:
        problems.append(f"results/: {found} result file(s) < minResultFiles={minimum}")
    return problems


def gate_writing(project: Path, settings: dict) -> list[str]:
    problems: list[str] = []
    text = require_file(project, "PAPER.md", problems)
    require_headings(text, "PAPER.md", REQUIRED_HEADINGS["writing"]["PAPER.md"], problems)
    check_claim_map(project, settings, problems, text)
    check_citations(project, settings, problems)
    return problems


def gate_review(project: Path, settings: dict) -> list[str]:
    problems: list[str] = []
    review = require_file(project, "REVIEW.md", problems)
    rebuttal = require_file(project, "REBUTTAL.md", problems)
    require_headings(review, "REVIEW.md", REQUIRED_HEADINGS["review"]["REVIEW.md"], problems)
    require_headings(rebuttal, "REBUTTAL.md", REQUIRED_HEADINGS["review"]["REBUTTAL.md"], problems)
    ids = review_ids(review)
    minimum = int(settings.get("minReviewItems", 3))
    if len(ids) < minimum:
        problems.append(f"REVIEW.md: {len(ids)} review item(s) < minReviewItems={minimum}")
    unanswered = ids - review_ids(rebuttal)
    if ids and unanswered:
        problems.append(f"REBUTTAL.md: missing responses for {', '.join(sorted(unanswered))}")
    for rid in sorted(ids - unanswered):
        if not rebuttal_body_ok(rebuttal, rid):
            problems.append(f"REBUTTAL.md: response for {rid} has no substantive body")
    if rebuttal and "UNRESOLVED" in rebuttal:
        problems.append("REBUTTAL.md: contains UNRESOLVED token")
    return problems


def gate_final(project: Path, settings: dict) -> list[str]:
    problems: list[str] = []
    checklist = require_file(project, "SUBMISSION_CHECKLIST.md", problems)
    provenance = require_file(project, "PROVENANCE.md", problems)
    require_headings(
        checklist,
        "SUBMISSION_CHECKLIST.md",
        REQUIRED_HEADINGS["final"]["SUBMISSION_CHECKLIST.md"],
        problems,
    )
    require_headings(
        provenance,
        "PROVENANCE.md",
        REQUIRED_HEADINGS["final"]["PROVENANCE.md"],
        problems,
    )
    if checklist is not None:
        unchecked = len(re.findall(r"^\s*[-*+]\s+\[ \]", checklist, re.M))
        if unchecked:
            problems.append(f"SUBMISSION_CHECKLIST.md: {unchecked} unchecked item(s)")
    decisions_path = project / "DECISIONS.md"
    decisions = read_text(decisions_path) if decisions_path.is_file() else ""
    if not re.search(r"^\s*-\s+\S+\s+\[signoff\]\s+\S", decisions, re.M):
        problems.append(
            "DECISIONS.md: missing human sign-off entry "
            "(run: auto_research.py log <dir> --kind signoff --text '...')"
        )
    problems.extend(gate_writing(project, settings))
    return problems


GATES = {
    "ideation": gate_ideation,
    "literature": gate_literature,
    "experiment_plan": gate_experiment_plan,
    "experiments": gate_experiments,
    "writing": gate_writing,
    "review": gate_review,
    "final": gate_final,
}


# --------------------------------------------------------------------------- #
# state handling
# --------------------------------------------------------------------------- #
def load_state(project: Path) -> dict:
    path = state_path(project)
    if not path.is_file():
        raise IntegrityError(f"not an auto-research project (missing state.json): {project}")
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise IntegrityError(f"state.json is not valid JSON: {exc}") from exc
    if not isinstance(state, dict):
        raise IntegrityError("state.json: top-level value must be an object")
    if state.get("schemaVersion") != SCHEMA_VERSION:
        raise IntegrityError(f"unsupported state schemaVersion: {state.get('schemaVersion')!r}")
    info = state.get("project") or {}
    phase = info.get("phase")
    if phase not in PHASES:
        raise IntegrityError(f"state.json: unknown phase {phase!r}")
    settings = state.get("settings")
    if not isinstance(settings, dict):
        raise IntegrityError("state.json: settings must be an object")
    for key in ("minRefs", "minClaims", "minReviewItems", "minResultFiles"):
        value = settings.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise IntegrityError(
                f"state.json: settings.{key} must be an integer >= 1 (got {value!r})"
            )
    history = state.get("history")
    if not isinstance(history, list) or not history:
        raise IntegrityError("state.json: history must be a non-empty list")
    previous_to = None
    for index, entry in enumerate(history):
        if not isinstance(entry, dict):
            raise IntegrityError(f"state.json: history[{index}] must be an object")
        for key in ("at", "from", "to", "by"):
            if key not in entry:
                raise IntegrityError(f"state.json: history[{index}] missing {key!r}")
        if entry["to"] not in PHASES:
            raise IntegrityError(f"state.json: history[{index}] has unknown phase {entry['to']!r}")
        if entry["by"] not in {"init", "agent", "human"}:
            raise IntegrityError(f"state.json: history[{index}] has invalid by={entry['by']!r}")
        if index == 0:
            if entry["from"] is not None:
                raise IntegrityError("state.json: first history entry must have from=null")
        elif entry["from"] != previous_to:
            raise IntegrityError(
                f"state.json: history[{index}] starts from {entry['from']!r} "
                f"but previous phase is {previous_to!r}"
            )
        previous_to = entry["to"]
    if previous_to != phase:
        raise IntegrityError(
            f"state.json: project.phase {phase!r} does not match history tail {previous_to!r} "
            "(manual phase edits are not allowed; use advance)"
        )
    if not isinstance(info.get("title"), str) or not info["title"].strip():
        raise IntegrityError("state.json: project.title is missing")
    return state


def save_state(project: Path, state: dict) -> None:
    state["project"]["updatedAt"] = now()
    tmp = state_path(project).with_name("state.json.tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(state_path(project))


def current_phase(state: dict) -> str:
    return str(state["project"]["phase"])


def append_decision(project: Path, line: str) -> None:
    path = project / "DECISIONS.md"
    prefix = "" if path.is_file() else "# Decisions & sign-offs\n\n"
    with path.open("a", encoding="utf-8", newline="\n") as f:
        if prefix:
            f.write(prefix)
        f.write(line + "\n")


def gate_report(project: Path, state: dict) -> dict[str, list[str]]:
    """Run every gate; report which phases currently pass."""
    settings = state["settings"]
    return {phase: GATES[phase](project, settings) for phase in PHASES}


# --------------------------------------------------------------------------- #
# commands
# --------------------------------------------------------------------------- #
def cmd_init(args) -> int:
    project = project_path(args.dir)
    if (project / "state.json").is_file():
        raise AutoResearchError(
            f"project already initialized: {project}/state.json exists; "
            "use a new directory (refusing to wipe audit history)"
        )
    if not args.title.strip() or not args.question.strip():
        raise AutoResearchError("--title and --question must not be empty")
    thresholds = {
        "minRefs": args.min_refs,
        "minClaims": args.min_claims,
        "minReviewItems": args.min_review_items,
        "minResultFiles": args.min_result_files,
    }
    bad = {name: value for name, value in thresholds.items() if value < 1}
    if bad:
        raise AutoResearchError(f"thresholds must be >= 1: {bad}")
    if project.exists() and any(project.iterdir()) and not args.force:
        raise AutoResearchError(f"directory not empty: {project} (use --force to scaffold anyway)")
    tdir = templates_dir()
    project.mkdir(parents=True, exist_ok=True)
    copies: list[str] = []
    for src in sorted(tdir.rglob("*")):
        if src.is_dir():
            continue
        rel = src.relative_to(tdir)
        dest = project / rel
        if dest.exists() and not args.force:
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        copies.append(rel.as_posix())
    missing = [rel for rel in REQUIRED_TEMPLATES if not (project / rel).is_file()]
    if missing:
        raise IntegrityError(f"init failed to copy required templates: {missing}")
    for extra in ("evidence", "experiments", "results", "figures"):
        (project / extra).mkdir(parents=True, exist_ok=True)
    state = {
        "schemaVersion": SCHEMA_VERSION,
        "project": {
            "title": args.title,
            "question": args.question,
            "venue": args.venue or "",
            "phase": "ideation",
            "createdAt": now(),
            "updatedAt": now(),
        },
        "settings": {
            "minRefs": args.min_refs,
            "minClaims": args.min_claims,
            "minReviewItems": args.min_review_items,
            "minResultFiles": args.min_result_files,
        },
        "history": [
            {"at": now(), "from": None, "to": "ideation", "by": "init", "reason": "project scaffolded"}
        ],
    }
    save_state(project, state)
    if not (project / "DECISIONS.md").is_file():
        (project / "DECISIONS.md").write_text("# Decisions & sign-offs\n\n", encoding="utf-8")
    print(f"initialized auto-research project: {project}")
    print(f"copied {len(copies)} template file(s); phase=ideation")
    print("next: fill IDEA.md, then `python auto_research.py check <dir>`")
    return 0


def cmd_status(args) -> int:
    project = project_path(args.dir)
    state = load_state(project)
    phase = current_phase(state)
    gates = gate_report(project, state)
    data = {
        "project": state["project"],
        "phaseIndex": PHASES.index(phase),
        "phaseCount": len(PHASES),
        "gates": {name: {"pass": not problems, "problems": problems} for name, problems in gates.items()},
        "guide": PHASE_GUIDE[phase],
    }
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0
    print(f"project: {state['project']['title']}  ({project})")
    print(f"phase:   {phase}  [{PHASES.index(phase) + 1}/{len(PHASES)}]")
    print(f"next:    {PHASE_GUIDE[phase]['action']}")
    print(f"skills:  {PHASE_GUIDE[phase]['skills']}")
    print()
    for name in PHASES:
        problems = gates[name]
        mark = "PASS" if not problems else ("FAIL" if name == phase else "blocked")
        print(f"  {name:16} {mark}")
        if name == phase and problems:
            for p in problems:
                print(f"      - {p}")
    return 0


def cmd_next(args) -> int:
    project = project_path(args.dir)
    state = load_state(project)
    phase = current_phase(state)
    gates = gate_report(project, state)
    print(f"phase: {phase}")
    print(f"artifact: {PHASE_GUIDE[phase]['artifact']}")
    print(f"action: {PHASE_GUIDE[phase]['action']}")
    print(f"skills: {PHASE_GUIDE[phase]['skills']}")
    problems = gates[phase]
    if problems:
        print("gate not satisfied:")
        for p in problems:
            print(f"  - {p}")
        print("fill the artifacts, then run: python auto_research.py check <dir>")
    else:
        nxt = PHASES[PHASES.index(phase) + 1] if PHASES.index(phase) + 1 < len(PHASES) else None
        print("gate satisfied." + (f" advance with: python auto_research.py advance <dir> (-> {nxt})" if nxt else " project complete."))
    return 0


def cmd_check(args) -> int:
    project = project_path(args.dir)
    state = load_state(project)
    phase = current_phase(state)
    index = PHASES.index(phase)
    gates = gate_report(project, state)
    report: dict = {"project": str(project), "phase": phase, "ok": [], "failed": []}
    problems: list[str] = []
    for name in PHASES[: index + 1]:
        if gates[name]:
            report["failed"].append({"phase": name, "problems": gates[name]})
            problems.append(name)
        else:
            report["ok"].append(name)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"project: {project}")
        print(f"phase:   {phase}")
        print(f"clean:   {', '.join(report['ok']) or '-'}")
        if report["failed"]:
            print("failed gates:")
            for item in report["failed"]:
                print(f"  {item['phase']}:")
                for p in item["problems"]:
                    print(f"    - {p}")
        print(f"\nresult: {'FAIL' if problems else 'PASS'}")
    return 1 if problems else 0


def cmd_advance(args) -> int:
    project = project_path(args.dir)
    state = load_state(project)
    phase = current_phase(state)
    index = PHASES.index(phase)
    if index + 1 >= len(PHASES):
        raise AutoResearchError(f"project already in final phase ({phase})")
    target = PHASES[index + 1]
    if args.to and args.to != target:
        raise AutoResearchError(
            f"can only advance one phase at a time ({phase} -> {target}); got --to {args.to}"
        )
    settings = state["settings"]
    problems: list[str] = []
    for earlier in PHASES[: index + 1]:
        for problem in GATES[earlier](project, settings):
            problems.append(f"{earlier}: {problem}")
    current_problems = [p for p in problems if p.startswith(f"{phase}: ")]
    if target == PHASES[-1]:
        # `final` is terminal: entering it means the project is done, so the
        # completion gate (checklist / provenance / human sign-off / writing
        # re-check) must pass as well as the review gate.
        final_problems = GATES["final"](project, state["settings"])
        other = [p for p in final_problems if "missing human sign-off" not in p]
        signoff_missing = any("missing human sign-off" in p for p in final_problems)
        if not current_problems and not other and signoff_missing:
            # Deliberately *not* bypassable with --force once every other
            # completion item is done: recorded human sign-off is the point.
            raise AutoResearchError(
                "refusing to enter final without a recorded human sign-off; "
                "run: auto_research.py log <dir> --kind signoff --text '<name/decision>'"
            )
        problems = problems + [f"[final] {p}" for p in final_problems]
    reason = ""
    if problems:
        if not args.force:
            print(f"gate for phase {phase} failed:", file=sys.stderr)
            for p in problems:
                print(f"  - {p}", file=sys.stderr)
            print("fix the artifacts, or use --force --reason '<why>' (recorded)", file=sys.stderr)
            return 1
        if not args.reason.strip():
            raise AutoResearchError("--force requires --reason to record the override")
        reason = f"FORCED: {single_line(args.reason)}"
        print(f"WARNING: overriding failed gate for {phase}: {reason}", file=sys.stderr)
    if args.force and not problems:
        note = f"FORCE-NOOP advance {phase} -> {target} by {args.by}"
        append_decision(project, f"- {now()} {note}")
        print(f"WARNING: --force given but gates already pass; recorded {note}", file=sys.stderr)
    state["project"]["phase"] = target
    state["history"].append(
        {"at": now(), "from": phase, "to": target, "by": args.by, "reason": reason}
    )
    line = f"- {now()} advance {phase} -> {target} by {args.by}" + (f" ({reason})" if reason else "")
    # Append the audit line first: a readable audit trail matters more than
    # state if the process dies between the two writes (single-process tool).
    append_decision(project, line)
    save_state(project, state)
    print(f"advanced: {phase} -> {target} by {args.by}")
    if target in PHASE_GUIDE:
        print(f"next: {PHASE_GUIDE[target]['action']}")
    return 0


def cmd_revert(args) -> int:
    """Move the project back to an earlier phase, explicitly and auditably.

    Going back is sometimes legitimate (a gate exposed a flawed earlier artifact),
    so this is a first-class command rather than a manual state.json edit -
    manual phase edits are rejected by load_state()'s history validation.
    """
    project = project_path(args.dir)
    state = load_state(project)
    phase = current_phase(state)
    index = PHASES.index(phase)
    if args.to not in PHASES:
        raise AutoResearchError(f"unknown phase: {args.to!r}")
    target_index = PHASES.index(args.to)
    if target_index >= index:
        raise AutoResearchError(
            f"revert must move backwards ({phase} -> earlier); current={phase}, target={args.to}"
        )
    reason = single_line(args.reason)
    if not reason:
        raise AutoResearchError("--reason is required for revert")
    state["project"]["phase"] = args.to
    state["history"].append(
        {"at": now(), "from": phase, "to": args.to, "by": args.by, "reason": f"REVERT: {reason}"}
    )
    save_state(project, state)
    append_decision(project, f"- {now()} revert {phase} -> {args.to} by {args.by} (REVERT: {reason})")
    print(f"reverted: {phase} -> {args.to}")
    print(f"reason:   REVERT: {reason}")
    return 0


def cmd_log(args) -> int:
    project = project_path(args.dir)
    load_state(project)  # validates project
    text = single_line(args.text)
    if not text:
        raise AutoResearchError("--text must not be empty")
    kind = single_line(args.kind) or "note"
    if kind == "signoff":
        print(
            "NOTE: signoff is a procedural checkpoint; agents must not run it "
            "without explicit human authorization (identity is not verifiable).",
            file=sys.stderr,
        )
    append_decision(project, f"- {now()} [{kind}] {text}")
    print("logged to DECISIONS.md")
    return 0


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="auto_research.py",
        description="DSH-native autonomous research state machine with phase gates.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="scaffold a new auto-research project")
    p.add_argument("dir")
    p.add_argument("--title", required=True)
    p.add_argument("--question", required=True)
    p.add_argument("--venue", default="")
    p.add_argument("--min-refs", type=int, default=10)
    p.add_argument("--min-claims", type=int, default=5)
    p.add_argument("--min-review-items", type=int, default=3)
    p.add_argument("--min-result-files", type=int, default=1)
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_init)

    for name, func in (("status", cmd_status), ("check", cmd_check)):
        p = sub.add_parser(name)
        p.add_argument("dir")
        p.add_argument("--json", action="store_true")
        p.set_defaults(func=func)

    p = sub.add_parser("next", help="show the current phase action and gate status")
    p.add_argument("dir")
    p.set_defaults(func=cmd_next)

    p = sub.add_parser("advance", help="advance one phase when the gate passes")
    p.add_argument("dir")
    p.add_argument("--to", default=None)
    p.add_argument("--by", choices=["agent", "human"], default="agent")
    p.add_argument("--force", action="store_true")
    p.add_argument("--reason", default="")
    p.set_defaults(func=cmd_advance)

    p = sub.add_parser("revert", help="move the project back to an earlier phase (audited)")
    p.add_argument("dir")
    p.add_argument("--to", required=True, choices=PHASES)
    p.add_argument("--reason", required=True)
    p.add_argument("--by", choices=["agent", "human"], default="human")
    p.set_defaults(func=cmd_revert)

    p = sub.add_parser("log", help="append a decision/sign-off/incident to DECISIONS.md")
    p.add_argument("dir")
    p.add_argument("--text", required=True)
    p.add_argument("--kind", default="note")
    p.set_defaults(func=cmd_log)
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except AutoResearchError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return exc.exit_code
    except OSError as exc:
        print(f"ERROR: filesystem error: {exc}", file=sys.stderr)
        return 2
    except (TypeError, ValueError, AttributeError, KeyError) as exc:
        print(f"ERROR: invalid project state or input: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
