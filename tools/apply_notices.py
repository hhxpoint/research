#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Maintainer tool: (re)generate provenance + licence files inside skills.

For every skill in `manifests/skills.lock.json`'s source model this tool writes:

  * `NOTICE.md`     attribution, pinned commit, licence id + URL, modifications
  * `LICENSE.txt`   the full licence text (MIT / CC BY-NC 4.0)
  * `DSH-PORT.md`   provenance + modification list + uninstall hint
  * `SKILL.md`      DSH port note refreshed (third-party skills only)

For `venue-templates` it additionally writes `NOTICE-LPPL.md` and
`LICENSE-LPPL-1.3c.txt` because the bundled Elsevier elsarticle files are
distributed under LPPL 1.3, not MIT.

Modes:

  # write: update repo payloads; tar-mode skills (ARS) are written into
  # $DSH_HOME/skills, because their payload is shipped as the archive
  python tools/apply_notices.py --write [--dsh-home PATH]

  # check: verify every required file exists and is consistent
  python tools/apply_notices.py --check [--dsh-home PATH]

Run `build_lock.py --from-installed` after `--write` to refresh the lock and
the ARS archive.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLS_DIR.parent
sys.path.insert(0, str(TOOLS_DIR))

import build_lock as BL  # noqa: E402

LICENSES_DIR = REPO_ROOT / "vendor" / "licenses"
TODAY = "2026-11-23"

LICENSE_URL = {
    "MIT": "https://opensource.org/license/mit",
    "CC-BY-NC-4.0": "https://creativecommons.org/licenses/by-nc/4.0/",
    "LPPL-1.3c": "https://www.latex-project.org/lppl/lppl-1-3c/",
}

COPYRIGHT = {
    "ars": "Copyright (c) 2026 Cheng-I Wu",
    "kdense": "Copyright (c) 2025 K-Dense Inc.",
    "aris": "Copyright (c) 2026 wanshuiyin",
    "zlanqing": "Copyright (c) 2026 zLanqing",
    "uditgoenka": "Copyright (c) 2026 Udit Goenka",
    "local": "Copyright (c) 2026 hhxpoint",
}

UPSTREAM_AUTHOR = {"ars": "Cheng-I Wu"}

MODIFICATIONS = {
    "ars": [
        "DSH port note prepended to SKILL.md (tool names, `$ARGUMENTS`, notices).",
        "Upstream repository-root `shared/` merged into this skill directory so relative references resolve.",
    ],
    "kdense": ["DSH port note prepended to SKILL.md (tool names, `$ARGUMENTS`, notices)."],
    "aris": ["DSH port note prepended to SKILL.md (tool names, `$ARGUMENTS`, notices)."],
    "zlanqing": ["DSH port note prepended to SKILL.md (tool names, `$ARGUMENTS`, notices)."],
    "uditgoenka": [
        "DSH port note prepended to SKILL.md.",
        "Sub-command protocol paths rewritten to `references/commands/`.",
        "Claude Code hooks not ported (safety rules restated in SKILL.md).",
    ],
    "local": ["Original skill authored in this repository."],
}

PREAMBLE_MARKER = "> **DSH 移植说明 / DSH port note**"
PREAMBLE_RE = re.compile(
    r"^> \*\*DSH 移植说明 / DSH port note\*\*.*?^> - 来源 / source:[^\n]*\n\n?",
    re.M | re.S,
)

VENUE_LPPL_FILES = (
    "assets/journals/elsarticle-harv.bst",
    "assets/journals/elsarticle-num-names.bst",
    "assets/journals/elsarticle-num.bst",
    "assets/journals/elsarticle-template-harv.tex",
    "assets/journals/elsarticle-template-num-names.tex",
    "assets/journals/elsarticle-template-num.tex",
)


def dsh_home_default() -> Path:
    import os

    return Path(os.environ.get("DSH_HOME") or (Path.home() / ".dsh"))


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Always LF: the repository stores bytes verbatim (see .gitattributes).
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def license_text_for(source_id: str) -> str:
    license_file = REPO_ROOT / BL.SOURCES[source_id]["licenseFile"]
    if not license_file.is_file():
        raise SystemExit(f"missing licence text for {source_id}: {license_file}")
    return license_file.read_text(encoding="utf-8", errors="replace")


def preamble_for(name: str, source_id: str) -> str:
    source = BL.SOURCES[source_id]
    lic = source["license"]
    note = source.get("note", "")
    if note:
        lic = f"{lic} — {note}"
    return f"""{PREAMBLE_MARKER}（非上游正文，仅为运行适配）
>
> - 工具名映射 / tool mapping: `Read`→`read`, `Write`→`write`, `Edit`→`edit`, `Grep`→`grep`, `Glob`→`glob`, `Bash`→`pwsh`, `WebFetch`→`web_fetch`, `Task`/agents→`subagent`, `AskUserQuestion`→`ask_user_question`.
> - Claude Code 专属的 slash commands、hooks、MCP server、`allowed-tools` 在 DSH 中不存在；遇到时按本文件的方法论执行，并使用当前会话可用的工具。
> - 上游正文中的 `$ARGUMENTS` 只是 Claude Code 的占位符，DSH 不会替换；任务参数请取用户当前消息。
> - 技能目录内的 `references/`、`scripts/`、`shared/` 等相对路径资源已随目录安装，可直接用 `read` / `pwsh` 访问。
> - 版权、许可证原文与修改说明见同目录 `NOTICE.md`、`LICENSE.txt`、`DSH-PORT.md`。
> - 来源 / source: {source['repo']} ｜ 许可证 / license: {lic} ｜ commit: `{source['commit']}` ｜ 导入: {TODAY}
"""


def refresh_skill_md(skill_md: Path, name: str, source_id: str) -> bool:
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise SystemExit(f"{skill_md}: missing frontmatter")
    end = text.find("\n---", 3)
    if end < 0:
        raise SystemExit(f"{skill_md}: unterminated frontmatter")
    head = text[: end + 4]
    body = text[end + 4 :].lstrip("\n")
    body = PREAMBLE_RE.sub("", body, count=1).lstrip("\n")
    new_text = head + "\n" + preamble_for(name, source_id) + "\n" + body
    changed = new_text != text
    if changed:
        write_text(skill_md, new_text)
    return changed


def notice_markdown(name: str, source_id: str) -> str:
    source = BL.SOURCES[source_id]
    lic = source["license"]
    lines = [
        f"# {name} — NOTICE / 第三方声明",
        "",
        f"- Upstream project: {source['repo']}",
        f"- Pinned commit: `{source['commit']}`",
        f"- License: {lic} ({LICENSE_URL.get(lic, '')})",
        f"- Copyright: {COPYRIGHT[source_id]}",
        f"- DSH adaptation date: {TODAY}; see `DSH-PORT.md` for every modification.",
        "",
        "This directory is redistributed as part of <https://github.com/hhxpoint/research>.",
        "The full licence text of the upstream project is in `LICENSE.txt` in this directory.",
    ]
    if source_id == "ars":
        lines += [
            "",
            "## Non-commercial only / 仅限非商业使用",
            "",
            "ARS is licensed under **CC BY-NC 4.0**: personal academic use and non-commercial",
            "research are allowed; **commercial use is prohibited** without a separate licence",
            f"from the upstream author ({UPSTREAM_AUTHOR.get('ars', 'the author')}).",
            "Sharing/adaptation requires attribution and an indication of changes (both provided",
            "here and in `DSH-PORT.md`).",
        ]
    if source_id == "uditgoenka":
        lines += [
            "",
            "## Notes",
            "",
            "- Claude Code hooks are not ported; the safety rules are restated in `SKILL.md`.",
            "- The `references/commands/` protocols come from the upstream repository.",
        ]
    if name == "venue-templates":
        lines += [
            "",
            "## Bundled third-party assets (LPPL 1.3)",
            "",
            "The Elsevier `elsarticle` templates/styles in `assets/journals/` are",
            f"copyright 2007-2026 Elsevier Ltd and licensed under LPPL 1.3 ({LICENSE_URL['LPPL-1.3c']}),",
            "not MIT. See `NOTICE-LPPL.md` and `LICENSE-LPPL-1.3c.txt`.",
        ]
    return "\n".join(lines) + "\n"


def port_markdown(name: str, source_id: str, file_count: int) -> str:
    source = BL.SOURCES[source_id]
    mods = "\n".join(f"- {m}" for m in MODIFICATIONS[source_id])
    return f"""# DSH port provenance — {name}

- upstream: {source['repo']}
- commit: `{source['commit']}`
- license: {source['license']}
- copyright: {COPYRIGHT[source_id]}
- imported: {TODAY}
- packaged files: {file_count}
- uninstall: remove this directory (`~/.dsh/skills/{name}`)

## Modifications

{mods}
- Added `NOTICE.md` and `LICENSE.txt` (and, for venue-templates, LPPL notices).
"""


def notice_lppl() -> str:
    return f"""# Elsevier elsarticle assets — LPPL 1.3 notice

The following files in `assets/journals/` are the Elsevier `elsarticle` LaTeX
templates and Bibliography styles:

{chr(10).join(f"- `{p}`" for p in VENUE_LPPL_FILES)}

They are Copyright 2007-2026 Elsevier Ltd and are distributed under the
**LaTeX Project Public License, version 1.3c** ({LICENSE_URL['LPPL-1.3c']}).
The full licence text is in `LICENSE-LPPL-1.3c.txt` in this directory.
They are included unmodified for journal-format preparation; the MIT licence of
this skill does **not** cover these files.
"""


def skill_dir_for(name: str, mode: str, dsh_home: Path) -> Path:
    if mode == "copy":
        return REPO_ROOT / "skills" / name
    return dsh_home / "skills" / name


def write_one(name: str, mode: str, dsh_home: Path) -> list[str]:
    source_id = BL.SKILL_SPECS[name][0]
    skill_dir = skill_dir_for(name, mode, dsh_home)
    if not (skill_dir / "SKILL.md").is_file():
        raise SystemExit(f"missing skill dir: {skill_dir}")
    changed: list[str] = []
    if source_id != "local":
        if refresh_skill_md(skill_dir / "SKILL.md", name, source_id):
            changed.append(f"{name}/SKILL.md")
    # licence text
    lic_path = skill_dir / "LICENSE.txt"
    lic_text = license_text_for(source_id)
    current = lic_path.read_text(encoding="utf-8", errors="replace") if lic_path.is_file() else None
    if current != lic_text:
        write_text(lic_path, lic_text)
        changed.append(f"{name}/LICENSE.txt")
    # notices
    notice = notice_markdown(name, source_id)
    notice_path = skill_dir / "NOTICE.md"
    if not notice_path.is_file() or notice_path.read_text(encoding="utf-8", errors="replace") != notice:
        write_text(notice_path, notice)
        changed.append(f"{name}/NOTICE.md")
    if name == "venue-templates":
        lppl_notice = notice_lppl()
        p = skill_dir / "NOTICE-LPPL.md"
        if not p.is_file() or p.read_text(encoding="utf-8", errors="replace") != lppl_notice:
            write_text(p, lppl_notice)
            changed.append(f"{name}/NOTICE-LPPL.md")
        lppl_text = (LICENSES_DIR / "LPPL-1.3c.txt").read_text(encoding="utf-8", errors="replace")
        p = skill_dir / "LICENSE-LPPL-1.3c.txt"
        if not p.is_file() or p.read_text(encoding="utf-8", errors="replace") != lppl_text:
            write_text(p, lppl_text)
            changed.append(f"{name}/LICENSE-LPPL-1.3c.txt")
    # provenance (file count excludes generated files themselves where practical)
    file_count = len(BL.payload_files(skill_dir)) + 3
    port = port_markdown(name, source_id, file_count)
    port_path = skill_dir / "DSH-PORT.md"
    if not port_path.is_file() or port_path.read_text(encoding="utf-8", errors="replace") != port:
        write_text(port_path, port)
        changed.append(f"{name}/DSH-PORT.md")
    return changed


def check_one(name: str, mode: str, dsh_home: Path) -> list[str]:
    source_id = BL.SKILL_SPECS[name][0]
    source = BL.SOURCES[source_id]
    skill_dir = skill_dir_for(name, mode, dsh_home)
    problems: list[str] = []
    if not skill_dir.is_dir():
        return [f"{name}: missing skill dir {skill_dir}"]
    skill_md = skill_dir / "SKILL.md"
    if source_id != "local":
        text = skill_md.read_text(encoding="utf-8")
        if PREAMBLE_MARKER not in text:
            problems.append(f"{name}: SKILL.md has no DSH port note")
        else:
            match = re.search(r"commit: `([^`]+)`", text)
            if not match or match.group(1) != source["commit"]:
                problems.append(f"{name}: SKILL.md port note commit does not match pinned commit")
    notice = skill_dir / "NOTICE.md"
    if not notice.is_file():
        problems.append(f"{name}: missing NOTICE.md")
    else:
        text = notice.read_text(encoding="utf-8", errors="replace")
        for needle in (source["repo"], source["commit"], source["license"], COPYRIGHT[source_id]):
            if needle not in text:
                problems.append(f"{name}: NOTICE.md is missing {needle!r}")
    lic = skill_dir / "LICENSE.txt"
    if not lic.is_file():
        problems.append(f"{name}: missing LICENSE.txt")
    else:
        text = lic.read_text(encoding="utf-8", errors="replace")
        token = {"MIT": "MIT License", "CC-BY-NC-4.0": "Creative Commons"}.get(source["license"])
        if token and token not in text:
            problems.append(f"{name}: LICENSE.txt does not look like {source['license']}")
        if len(text) < 500:
            problems.append(f"{name}: LICENSE.txt is too short")
    port = skill_dir / "DSH-PORT.md"
    if not port.is_file():
        problems.append(f"{name}: missing DSH-PORT.md")
    else:
        text = port.read_text(encoding="utf-8", errors="replace")
        match = re.search(r"^- commit: `([^`]+)`", text, re.M)
        if not match or match.group(1) != source["commit"]:
            problems.append(f"{name}: DSH-PORT.md commit does not match pinned commit")
    if name == "venue-templates":
        for fname in ("NOTICE-LPPL.md", "LICENSE-LPPL-1.3c.txt"):
            if not (skill_dir / fname).is_file():
                problems.append(f"{name}: missing {fname}")
        if (LICENSES_DIR / "LPPL-1.3c.txt").is_file() is False:
            problems.append("vendor/licenses/LPPL-1.3c.txt is missing")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    ap.add_argument("--dsh-home", type=Path, default=dsh_home_default())
    args = ap.parse_args()
    dsh_home = args.dsh_home.expanduser().resolve()
    problems: list[str] = []
    changed: list[str] = []
    skipped: list[str] = []
    for name, (source_id, _category, mode) in sorted(BL.SKILL_SPECS.items()):
        if args.write:
            try:
                changed.extend(write_one(name, mode, dsh_home))
            except SystemExit as exc:
                problems.append(f"{name}: {exc}")
        else:
            if mode == "tar" and not (dsh_home / "skills" / name / "SKILL.md").is_file():
                # archive contents are covered by `dsh_skills.py selftest`; only
                # require the installed copy when it exists.
                skipped.append(name)
                continue
            problems.extend(check_one(name, mode, dsh_home))
    if args.write:
        print(f"updated {len(set(changed))} file(s)")
        for c in sorted(set(changed)):
            print("  -", c)
    if problems:
        print("CHECK FAILED")
        for p in problems:
            print("  -", p)
        return 1
    if args.check:
        checked = len(BL.SKILL_SPECS) - len(skipped)
        print(f"NOTICES OK: {checked} skills checked"
              + (f" (skipped not-installed tar skills: {', '.join(skipped)})" if skipped else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
