#!/usr/bin/env python3
"""Build (or check) the skill lock file and vendored ARS tarball.

Maintainer tool. Two modes:

  # first build on a machine that already has the skills installed in DSH
  python tools/build_lock.py --from-installed

  # verification / rebuild purely from what is committed in this repo
  python tools/build_lock.py --check

The lock file `manifests/skills.lock.json` records, for every skill:

  name, source, category, license, description (from SKILL.md),
  and the sha256 of every installed file.

Skill payloads live in two places:

  - `skills/<name>/` for skills we may redistribute under MIT (plain files)
  - `vendor/ars-dsh-<version>-<shortsha>.tar.gz` for the CC BY-NC 4.0
    academic-research-skills bundle (kept as one archive, see THIRD-PARTY.md)

Both are byte-identical to what `tools/dsh_skills.py install` puts into
`$DSH_HOME/skills/<name>/`.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import sys
import tarfile
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LOCK_PATH = REPO_ROOT / "manifests" / "skills.lock.json"
SKILLS_DIR = REPO_ROOT / "skills"
VENDOR_DIR = REPO_ROOT / "vendor"
DEFAULT_DSH_HOME = Path(os.environ.get("DSH_HOME") or (Path.home() / ".dsh"))

SCHEMA_VERSION = 1
GENERATED_AT = "2026-11-23"

SOURCES = {
    "ars": {
        "repo": "https://github.com/Imbad0202/academic-research-skills",
        "commit": "d103b1005bb8c9f7a597e6a7ed473b75dcf8830e",
        "version": "3.24.4",
        "license": "CC-BY-NC-4.0",
        "licenseFile": "vendor/licenses/ARS-CC-BY-NC-4.0.txt",
        "note": "禁止商业使用；仅限非商业学术用途，商用需另行授权。",
    },
    "kdense": {
        "repo": "https://github.com/K-Dense-AI/scientific-agent-skills",
        "commit": "c21d13b3cc2894680229ba9959a53281acb9200e",
        "license": "MIT",
        "licenseFile": "vendor/licenses/K-Dense-scientific-agent-skills-MIT.txt",
        "note": "",
    },
    "aris": {
        "repo": "https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep",
        "commit": "4ba94ae2a1c1fbbb14858750dd8764cabf6c28bd",
        "license": "MIT",
        "licenseFile": "vendor/licenses/ARIS-MIT.txt",
        "note": "",
    },
    "zlanqing": {
        "repo": "https://github.com/zLanqing/codex-claude-academic-skills",
        "commit": "7ed6377f0efb6a38951b48ef03b19d996e454b1f",
        "license": "MIT",
        "licenseFile": "vendor/licenses/zLanqing-MIT.txt",
        "note": "",
    },
    "uditgoenka": {
        "repo": "https://github.com/uditgoenka/autoresearch",
        "commit": "7bddd056dfd0b0ded8360588d8101b1ecb5c0baa",
        "license": "MIT",
        "licenseFile": "vendor/licenses/uditgoenka-autoresearch-MIT.txt",
        "note": "",
    },
    "local": {
        "repo": "https://github.com/hhxpoint/research",
        "commit": "HEAD",
        "license": "MIT",
        "licenseFile": "LICENSE",
        "note": "本仓库原创技能。",
    },
}

# name -> (source, category, install mode)
SKILL_SPECS = {
    # academic-research-skills 5-pack (CC BY-NC 4.0, shipped as tarball)
    "academic-paper": ("ars", "paper-writing", "tar"),
    "academic-paper-reviewer": ("ars", "review", "tar"),
    "academic-pipeline": ("ars", "orchestration", "tar"),
    "deep-research": ("ars", "research", "tar"),
    "sr-screener": ("ars", "systematic-review", "tar"),
    # K-Dense (MIT, plain files)
    "scientific-writing": ("kdense", "paper-writing", "copy"),
    "citation-management": ("kdense", "citations", "copy"),
    "scientific-visualization": ("kdense", "figures", "copy"),
    "venue-templates": ("kdense", "venue", "copy"),
    # ARIS (MIT)
    "research-lit": ("aris", "research", "copy"),
    "experiment-plan": ("aris", "experiments", "copy"),
    "analyze-results": ("aris", "experiments", "copy"),
    # zLanqing (MIT)
    "research-writing-skill": ("zlanqing", "paper-writing", "copy"),
    # uditgoenka (MIT, DSH-adapted)
    "autoresearch": ("uditgoenka", "tooling", "copy"),
    # our own
    "research-stack": ("local", "meta", "copy"),
}

ARS_SKILLS = [n for n, s in SKILL_SPECS.items() if s[0] == "ars"]
ARS_TARBALL = VENDOR_DIR / "ars-dsh-v3.24.4-d103b100.tar.gz"

PRESETS = {
    "minimal": [
        "research-stack",
        "research-lit",
        "scientific-writing",
        "citation-management",
        "research-writing-skill",
    ],
    "writing": [
        "research-stack",
        "academic-paper",
        "academic-paper-reviewer",
        "academic-pipeline",
        "scientific-writing",
        "research-writing-skill",
        "citation-management",
        "scientific-visualization",
        "venue-templates",
    ],
    "full": sorted(SKILL_SPECS),
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_extractall(tar: tarfile.TarFile, dest: Path) -> None:
    """Extract a tarball while rejecting absolute paths, traversal and links."""
    members = []
    for m in tar.getmembers():
        p = Path(m.name)
        if p.is_absolute() or ".." in p.parts or m.issym() or m.islnk():
            raise SystemExit(f"unsafe tar member: {m.name!r}")
        members.append(m)
    dest = dest.resolve()
    for m in members:
        target = (dest / m.name).resolve()
        if target != dest and dest not in target.parents:
            raise SystemExit(f"unsafe tar member path: {m.name!r}")
    tar.extractall(dest, members=members)


def parse_frontmatter(text: str) -> dict:
    import yaml  # local import keeps `--help` working without pyyaml

    if not text.startswith("---"):
        raise ValueError("SKILL.md does not start with '---'")
    end = text.find("\n---", 3)
    if end < 0:
        raise ValueError("unterminated frontmatter")
    data = yaml.safe_load(text[3:end])
    if not isinstance(data, dict):
        raise ValueError("frontmatter is not a mapping")
    return data


def skill_files(skill_dir: Path) -> list[dict]:
    files = []
    for p in sorted(skill_dir.rglob("*")):
        if p.is_dir():
            continue
        if not p.is_file():
            raise ValueError(f"unsupported file type in skill dir: {p}")
        rel = p.relative_to(skill_dir).as_posix()
        files.append({"path": rel, "sha256": sha256_file(p), "bytes": p.stat().st_size})
    if not files:
        raise ValueError(f"empty skill dir: {skill_dir}")
    return files


def read_skill_meta(skill_dir: Path) -> tuple[dict, str]:
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    meta = parse_frontmatter(text)
    name = str(meta.get("name") or "")
    desc = str(meta.get("description") or "").strip()
    if not name:
        raise ValueError(f"{skill_dir}: missing name")
    if not desc:
        raise ValueError(f"{skill_dir}: missing description")
    return meta, " ".join(desc.split())


def build_ars_tarball(src_root: Path, dest: Path) -> str:
    """Deterministic tar.gz of the ARS skill dirs (as installed in DSH)."""
    members: list[Path] = []
    for name in ARS_SKILLS:
        d = src_root / name
        if not (d / "SKILL.md").is_file():
            raise SystemExit(f"missing source skill: {d}")
        members.extend(sorted(p for p in d.rglob("*") if p.is_file()))
    members.sort(key=lambda p: p.relative_to(src_root).as_posix())

    buf = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buf, mtime=0, compresslevel=9) as gz:
        with tarfile.open(fileobj=gz, mode="w", format=tarfile.GNU_FORMAT) as tar:
            for p in members:
                rel = p.relative_to(src_root).as_posix()
                info = tarfile.TarInfo(name=rel)
                info.size = p.stat().st_size
                info.mtime = 0
                info.mode = 0o644
                info.uid = info.gid = 0
                info.uname = info.gname = ""
                with p.open("rb") as f:
                    tar.addfile(info, f)

    data = buf.getvalue()
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(dest)
    return hashlib.sha256(data).hexdigest()


def read_from_installed(dsh_home: Path) -> dict[str, Path]:
    root = dsh_home / "skills"
    srcs: dict[str, Path] = {}
    for name in ARS_SKILLS:
        d = root / name
        if not (d / "SKILL.md").is_file():
            raise SystemExit(f"missing installed skill: {d}")
        srcs[name] = d
    return srcs


def gather_skill_dirs(from_installed: dict[str, Path] | None) -> dict[str, Path]:
    """Return name -> directory containing the installed form of each skill."""
    dirs: dict[str, Path] = {}
    for name, (source, _category, mode) in SKILL_SPECS.items():
        if mode == "tar":
            if from_installed is None:
                raise SystemExit(
                    "repo-only mode cannot read tar skills yet; run --from-installed once"
                )
            dirs[name] = from_installed[name]
        else:
            d = SKILLS_DIR / name
            if not (d / "SKILL.md").is_file():
                raise SystemExit(f"missing repo skill: {d}")
            dirs[name] = d
    return dirs


def build_lock(skill_dirs: dict[str, Path], ars_tar: Path | None) -> dict:
    skills = []
    for name in sorted(SKILL_SPECS):
        source, category, mode = SKILL_SPECS[name]
        d = skill_dirs[name]
        meta, desc = read_skill_meta(d)
        if meta.get("name") != name:
            raise SystemExit(f"{name}: frontmatter name mismatch: {meta.get('name')!r}")
        entry = {
            "name": name,
            "source": source,
            "category": category,
            "mode": mode,
            "license": SOURCES[source]["license"],
            "description": desc,
            "files": skill_files(d),
        }
        if mode == "tar":
            entry["archivePath"] = f'{name}/SKILL.md'
        skills.append(entry)

    lock = {
        "schemaVersion": SCHEMA_VERSION,
        "generatedAt": GENERATED_AT,
        "repo": "https://github.com/hhxpoint/research",
        "dsh": {
            "minVersion": "44.7.0",
            "skillRoot": "$DSH_HOME/skills",
            "spec": "docs/dsh-skill-spec.md",
        },
        "presets": PRESETS,
        "sources": {
            sid: {
                **{k: v for k, v in src.items() if k != "note"},
                "note": src["note"],
                **(
                    {
                        "archive": ARS_TARBALL.relative_to(REPO_ROOT).as_posix(),
                        "archiveSha256": sha256_file(ARS_TARBALL),
                        "archiveBytes": ARS_TARBALL.stat().st_size,
                    }
                    if sid == "ars"
                    else {}
                ),
            }
            for sid, src in SOURCES.items()
        },
        "skills": skills,
    }
    return lock


def write_lock(lock: dict) -> None:
    text = json.dumps(lock, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    tmp = LOCK_PATH.with_suffix(".json.tmp")
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(LOCK_PATH)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--from-installed", action="store_true", help="read tar skills from $DSH_HOME/skills and rebuild the tarball")
    ap.add_argument("--check", action="store_true", help="rebuild in memory and compare with the committed lock")
    ap.add_argument("--dsh-home", type=Path, default=DEFAULT_DSH_HOME)
    args = ap.parse_args()
    if args.from_installed == args.check:
        ap.error("choose exactly one of --from-installed / --check")
    if sys.version_info < (3, 10):
        raise SystemExit("python >= 3.10 required")

    from_installed = read_from_installed(args.dsh_home) if args.from_installed else None
    if args.from_installed:
        sha = build_ars_tarball(args.dsh_home / "skills", ARS_TARBALL)
        print(f"ars tarball: {ARS_TARBALL.relative_to(REPO_ROOT)} ({ARS_TARBALL.stat().st_size} B) sha256={sha}")
        # after writing the tarball, hash skills from the installed dirs
        skill_dirs = gather_skill_dirs(from_installed)
        lock = build_lock(skill_dirs, ARS_TARBALL)
    else:
        if not LOCK_PATH.is_file():
            raise SystemExit(f"no lock file: {LOCK_PATH}")
        committed = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
        # verify repo copy skills and the tarball against the committed lock
        problems: list[str] = []
        with tempfile.TemporaryDirectory(prefix="research-lock-") as td:
            tmp = Path(td)
            ars = committed["sources"]["ars"]
            tar_path = REPO_ROOT / ars["archive"]
            if not tar_path.is_file():
                problems.append(f"missing archive: {tar_path}")
            else:
                if sha256_file(tar_path) != ars["archiveSha256"]:
                    problems.append("archive sha256 mismatch")
                with tarfile.open(tar_path, "r:gz") as tar:
                    safe_extractall(tar, tmp)
            dirs: dict[str, Path] = {}
            for name, (source, _c, mode) in SKILL_SPECS.items():
                if mode == "tar":
                    dirs[name] = tmp / name
                else:
                    dirs[name] = SKILLS_DIR / name
            rebuilt = build_lock(dirs, None)
            if json.dumps(rebuilt, sort_keys=True) != json.dumps(committed, sort_keys=True):
                problems.append("lock file does not match repo content (run --from-installed and commit)")
        if problems:
            print("CHECK FAILED")
            for p in problems:
                print(" -", p)
            return 1
        print("CHECK OK: lock, archive, and repo skills are consistent")
        print(f"  skills: {len(committed['skills'])}")
        print(f"  ars archive: {committed['sources']['ars']['archive']} sha256={committed['sources']['ars']['archiveSha256']}")
        return 0

    write_lock(lock)
    print(f"wrote {LOCK_PATH.relative_to(REPO_ROOT)} with {len(lock['skills'])} skills")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
