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
    TOOL_DIR.parent.parent / "templates" / "auto-research",  # repo layout: tools/.. -> templates/auto-research
)
SCHEMA_VERSION = 1
TODAY = dt.date.today().isoformat()
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


def require_file(project: Path, rel: str, problems: list[str], optional: bool = False) -> str | None:
    path = project / rel
    if not path.is_file():
        if not optional:
            problems.append(f"missing artifact: {rel}")
        return None
    text = read_text(path)
    if SENTINEL in text:
        problems.append(f"artifact still contains placeholder sentinel: {rel}")
    if rel.endswith(".md") and not text.strip():
        problems.append(f"artifact is empty: {rel}")
    return text


def require_headings(text: str | None, rel: str, headings: list[str], problems: list[str]) -> None:
    if text is None:
        return
    for heading in headings:
        pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.M)
        if not pattern.search(text):
            problems.append(f"{rel}: missing section heading '## {heading}'")


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


def check_claim_map(project: Path, settings: dict, problems: list[str]) -> None:
    entries = claim_entries(project, problems)
    if not entries:
        if (project / "evidence" / "claim_map.json").is_file():
            problems.append("evidence/claim_map.json: no claim entries")
        return
    minimum = int(settings.get("minClaims", 5))
    if len(entries) < minimum:
        problems.append(f"evidence/claim_map.json: {len(entries)} claims < minClaims={minimum}")
    for index, entry in enumerate(entries, 1):
        if not str(entry.get("id", "")).strip():
            problems.append(f"claims[{index}]: missing id")
        if not str(entry.get("claim", "")).strip():
            problems.append(f"claims[{index}]: missing claim text")
        evidence = entry.get("evidence")
        if not evidence or not isinstance(evidence, list):
            problems.append(f"claims[{index}]: evidence must be a non-empty list")
        if str(entry.get("status", "")).lower() not in {"verified", "supported"}:
            problems.append(f"claims[{index}]: status must be verified/supported")


def count_results(project: Path) -> int:
    root = project / "results"
    if not root.is_dir():
        return 0
    count = 0
    for p in root.rglob("*"):
        if p.is_file() and p.name not in {".gitkeep"} and not any(
            part in IGNORED_NAMES for part in p.parts
        ):
            count += 1
    return count


def review_ids(text: str | None) -> set[str]:
    if not text:
        return set()
    return set(re.findall(r"^###\s+(R\d+)\b", text, re.M))


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
    check_claim_map(project, settings, problems)
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
        unchecked = len(re.findall(r"^\s*-\s*\[ \]", checklist, re.M))
        if unchecked:
            problems.append(f"SUBMISSION_CHECKLIST.md: {unchecked} unchecked item(s)")
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
    if state.get("schemaVersion") != SCHEMA_VERSION:
        raise IntegrityError(f"unsupported state schemaVersion: {state.get('schemaVersion')!r}")
    info = state.get("project") or {}
    phase = info.get("phase")
    if phase not in PHASES:
        raise IntegrityError(f"state.json: unknown phase {phase!r}")
    if not isinstance(state.get("settings"), dict):
        raise IntegrityError("state.json: settings must be an object")
    if not isinstance(state.get("history"), list):
        raise IntegrityError("state.json: history must be a list")
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
    problems = GATES[phase](project, state["settings"])
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
        reason = f"FORCED: {args.reason.strip()}"
        print(f"WARNING: overriding failed gate for {phase}: {reason}", file=sys.stderr)
    state["project"]["phase"] = target
    state["history"].append(
        {"at": now(), "from": phase, "to": target, "by": args.by, "reason": reason}
    )
    save_state(project, state)
    line = f"- {now()} advance {phase} -> {target} by {args.by}" + (f" ({reason})" if reason else "")
    append_decision(project, line)
    print(f"advanced: {phase} -> {target} by {args.by}")
    if target in PHASE_GUIDE:
        print(f"next: {PHASE_GUIDE[target]['action']}")
    return 0


def cmd_log(args) -> int:
    project = project_path(args.dir)
    load_state(project)  # validates project
    text = args.text.strip()
    if not text:
        raise AutoResearchError("--text must not be empty")
    append_decision(project, f"- {now()} [{args.kind}] {text}")
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


if __name__ == "__main__":
    raise SystemExit(main())
