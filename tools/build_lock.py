#!/usr/bin/env python3
"""Build (or check) the skill lock file and vendored ARS tarball.

Maintainer tool. Two modes:

  # on a machine whose $DSH_HOME/skills contains the 5 ARS skills:
  python tools/build_lock.py --from-installed

  # verification / rebuild purely from what is committed in this repo:
  python tools/build_lock.py --check

The lock file `manifests/skills.lock.json` records, for every skill:

  name, source, category, license, description (from SKILL.md),
  and the sha256 of every packaged file.

Skill payloads live in two places:

  - `skills/<name>/` for skills we may redistribute under MIT (plain files)
  - `vendor/ars-dsh-<version>-<shortsha>.tar.gz` for the CC BY-NC 4.0
    academic-research-skills bundle (kept as one archive, see THIRD-PARTY.md)

Both are byte-identical to what `tools/dsh_skills.py install` puts into
`$DSH_HOME/skills/<name>/`.

Robustness rules implemented here:

  * runtime artefacts (`__pycache__/`, `*.pyc|pyo`, `.DS_Store`, `Thumbs.db`,
    `.git`) are never packaged or hashed;
  * the tarball is built in memory, validated, and only then written
    atomically together with the lock file - a failure leaves the committed
    files untouched;
  * `--check` verifies the archive hash *and* that its member set is exactly
    the set recorded in the lock, then rebuilds the lock from repo + archive
    and compares canonically.
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

# Runtime artefacts ignored on both build and check (never packaged).
IGNORED_DIR_NAMES = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
IGNORED_FILE_SUFFIXES = (".pyc", ".pyo")
IGNORED_FILE_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}

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
        "note": "venue-templates 内含 Elsevier elsarticle 资产（LPPL 1.3），见 THIRD-PARTY.md。",
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
        "commit": "self",
        "license": "MIT",
        "licenseFile": "LICENSE",
        "note": "本仓库原创技能，无上游 commit（commit=self）。",
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
    "auto-research": ("local", "auto-research", "copy"),
}

ARS_SKILLS = [n for n, s in SKILL_SPECS.items() if s[0] == "ars"]
ARS_TARBALL = VENDOR_DIR / "ars-dsh-v3.24.4-d103b100.tar.gz"

PRESETS = {
    "minimal": [
        "research-stack",
        "auto-research",
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


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def is_ignored(rel: str) -> bool:
    parts = rel.split("/")
    if any(part in IGNORED_DIR_NAMES for part in parts[:-1]):
        return True
    name = parts[-1]
    return name in IGNORED_FILE_NAMES or name.endswith(IGNORED_FILE_SUFFIXES)


def payload_files(root: Path) -> list[Path]:
    """Sorted list of packaged files under root, excluding runtime artefacts."""
    result = []
    for p in sorted(root.rglob("*"), key=lambda x: x.relative_to(root).as_posix()):
        rel = p.relative_to(root).as_posix()
        if is_ignored(rel):
            continue
        if p.is_symlink():
            raise SystemExit(f"symbolic links are not allowed: {p}")
        if p.is_file():
            result.append(p)
    return result


def skill_files(skill_dir: Path) -> list[dict]:
    files = []
    for p in payload_files(skill_dir):
        rel = p.relative_to(skill_dir).as_posix()
        files.append({"path": rel, "sha256": sha256_file(p), "bytes": p.stat().st_size})
    if not files:
        raise SystemExit(f"empty skill dir: {skill_dir}")
    return files


def parse_frontmatter(text: str) -> dict:
    import yaml  # local import keeps `--help` working without pyyaml

    if not text.startswith("---"):
        raise SystemExit("SKILL.md does not start with '---'")
    end = text.find("\n---", 3)
    if end < 0:
        raise SystemExit("unterminated frontmatter")
    data = yaml.safe_load(text[3:end])
    if not isinstance(data, dict):
        raise SystemExit("frontmatter is not a mapping")
    return data


def read_skill_meta(skill_dir: Path) -> tuple[dict, str]:
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    meta = parse_frontmatter(text)
    name = str(meta.get("name") or "")
    desc = str(meta.get("description") or "").strip()
    if not name:
        raise SystemExit(f"{skill_dir}: missing name")
    if not desc:
        raise SystemExit(f"{skill_dir}: missing description")
    return meta, " ".join(desc.split())


def iter_skill_dirs(root: Path) -> list[Path]:
    return [d for d in sorted(root.iterdir(), key=lambda p: p.name) if d.is_dir()]


def build_ars_tarball_bytes(src_root: Path) -> bytes:
    """Deterministic tar.gz of the ARS skill dirs (as installed in DSH)."""
    members: list[Path] = []
    for name in ARS_SKILLS:
        d = src_root / name
        if not (d / "SKILL.md").is_file():
            raise SystemExit(f"missing installed ARS skill: {d}")
        members.extend(payload_files(d))
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
    return buf.getvalue()


def extract_bytes(data: bytes, dest: Path) -> None:
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tar:
        members = []
        dest_resolved = dest.resolve()
        for m in tar.getmembers():
            path = Path(m.name)
            if path.is_absolute() or ".." in path.parts:
                raise SystemExit(f"unsafe archive member: {m.name!r}")
            if m.issym() or m.islnk() or not (m.isfile() or m.isdir()):
                raise SystemExit(f"unsupported archive member: {m.name!r}")
            target = (dest_resolved / m.name).resolve()
            if target != dest_resolved and dest_resolved not in target.parents:
                raise SystemExit(f"unsafe archive member path: {m.name!r}")
            members.append(m)
        tar.extractall(dest, members=members)


def repo_skill_dirs() -> dict[str, Path]:
    dirs: dict[str, Path] = {}
    for name, (_source, _category, mode) in SKILL_SPECS.items():
        if mode != "copy":
            continue
        d = SKILLS_DIR / name
        if not (d / "SKILL.md").is_file():
            raise SystemExit(f"missing repo skill: {d}")
        dirs[name] = d
    return dirs


def repo_skill_dirs_checked(problems: list[str]) -> dict[str, Path]:
    """Non-throwing variant used by --check so all issues are reported at once."""
    dirs: dict[str, Path] = {}
    for name, (_source, _category, mode) in SKILL_SPECS.items():
        if mode != "copy":
            continue
        d = SKILLS_DIR / name
        if not (d / "SKILL.md").is_file():
            problems.append(f"missing repo skill: {d}")
        else:
            dirs[name] = d
    return dirs


def build_lock(skill_dirs: dict[str, Path], archive_sha: str, archive_bytes: int) -> dict:
    skills = []
    for name in sorted(SKILL_SPECS):
        source, category, mode = SKILL_SPECS[name]
        d = skill_dirs[name]
        meta, desc = read_skill_meta(d)
        if meta.get("name") != name:
            raise SystemExit(f"{name}: frontmatter name mismatch: {meta.get('name')!r}")
        skills.append(
            {
                "name": name,
                "source": source,
                "category": category,
                "mode": mode,
                "license": SOURCES[source]["license"],
                "description": desc,
                "files": skill_files(d),
            }
        )
    return {
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
                        "archiveSha256": archive_sha,
                        "archiveBytes": archive_bytes,
                    }
                    if sid == "ars"
                    else {}
                ),
            }
            for sid, src in SOURCES.items()
        },
        "skills": skills,
    }


def canonical_lock(lock: dict) -> dict:
    result = json.loads(json.dumps(lock))
    for skill in result.get("skills", []):
        if isinstance(skill.get("files"), list):
            skill["files"] = sorted(skill["files"], key=lambda f: f.get("path", ""))
    return result


def write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)


def lock_bytes(lock: dict) -> bytes:
    return (json.dumps(lock, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def own_copy_checks(lock: dict) -> list[str]:
    problems: list[str] = []
    for entry in lock["skills"]:
        if entry["mode"] != "copy":
            continue
        skill_dir = REPO_ROOT / "skills" / entry["name"]
        for f in entry["files"]:
            p = skill_dir / f["path"]
            if not p.is_file():
                problems.append(f"{entry['name']}: missing {f['path']}")
            elif sha256_file(p) != f["sha256"]:
                problems.append(f"{entry['name']}: hash mismatch {f['path']}")
    return problems


def cmd_from_installed(args) -> int:
    dsh_home = Path(args.dsh_home).expanduser().resolve()
    src_root = dsh_home / "skills"
    # Validate every source before touching any committed file.
    copy_dirs = repo_skill_dirs()
    for name in ARS_SKILLS:
        if not (src_root / name / "SKILL.md").is_file():
            raise SystemExit(f"missing installed ARS skill: {src_root / name}")

    tar_bytes = build_ars_tarball_bytes(src_root)
    tar_sha = sha256_bytes(tar_bytes)
    print(f"built ARS archive in memory: {len(tar_bytes)} B sha256={tar_sha}")

    with tempfile.TemporaryDirectory(prefix="research-build-") as td:
        extracted = Path(td)
        extract_bytes(tar_bytes, extracted)
        names = {d.name for d in iter_skill_dirs(extracted)}
        if names != set(ARS_SKILLS):
            raise SystemExit(f"archive skill set mismatch: {sorted(names)}")
        dirs = dict(copy_dirs)
        for name in ARS_SKILLS:
            dirs[name] = extracted / name
        lock = build_lock(dirs, tar_sha, len(tar_bytes))
        problems = own_copy_checks(lock)
        if problems:
            raise SystemExit("refusing to write lock, repo content problems:\n  " + "\n  ".join(problems))
        # final self-consistency: archive members == lock paths
        expected = {
            f"{e['name']}/{f['path']}"
            for e in lock["skills"]
            if e["mode"] == "tar"
            for f in e["files"]
        }
        actual = {p.relative_to(extracted).as_posix() for p in extracted.rglob("*") if p.is_file()}
        if expected != actual:
            raise SystemExit(
                f"archive member set mismatch: missing={sorted(expected-actual)[:5]} "
                f"extra={sorted(actual-expected)[:5]}"
            )

    write_atomic(ARS_TARBALL, tar_bytes)
    write_atomic(LOCK_PATH, lock_bytes(lock))
    print(f"wrote {ARS_TARBALL.relative_to(REPO_ROOT)} and {LOCK_PATH.relative_to(REPO_ROOT)} "
          f"with {len(lock['skills'])} skills")
    return 0


def cmd_check(args) -> int:
    if not LOCK_PATH.is_file():
        raise SystemExit(f"no lock file: {LOCK_PATH}")
    committed = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    problems: list[str] = []
    ars = committed["sources"]["ars"]
    tar_path = REPO_ROOT / ars["archive"]
    if not tar_path.is_file():
        print("CHECK FAILED")
        print(f" - missing archive: {tar_path}")
        return 1
    actual_sha = sha256_file(tar_path)
    if actual_sha != ars["archiveSha256"]:
        print("CHECK FAILED")
        print(f" - archive sha256 mismatch: {actual_sha} != {ars['archiveSha256']}")
        return 1
    with tempfile.TemporaryDirectory(prefix="research-check-") as td:
        tmp = Path(td)
        try:
            extract_bytes(tar_path.read_bytes(), tmp)
        except SystemExit as exc:
            print("CHECK FAILED")
            print(f" - {exc}")
            return 1
        expected = {
            f"{e['name']}/{f['path']}"
            for e in committed["skills"]
            if e["mode"] == "tar"
            for f in e["files"]
        }
        actual = {p.relative_to(tmp).as_posix() for p in tmp.rglob("*") if p.is_file()}
        if expected != actual:
            problems.append(
                f"archive member set mismatch: missing={sorted(expected - actual)[:5]} "
                f"extra={sorted(actual - expected)[:5]}"
            )
        try:
            names = {d.name for d in iter_skill_dirs(tmp)}
        except OSError as exc:
            problems.append(f"cannot list archive extraction: {exc}")
            names = set()
        if names != set(ARS_SKILLS):
            problems.append(f"archive skill set mismatch: {sorted(names)}")
        dirs = repo_skill_dirs_checked(problems)
        for name in ARS_SKILLS:
            dirs[name] = tmp / name
        if problems:
            print("CHECK FAILED")
            for p in problems:
                print(" -", p)
            return 1
        rebuilt = build_lock(dirs, actual_sha, tar_path.stat().st_size)
        if json.dumps(canonical_lock(rebuilt), sort_keys=True) != json.dumps(
            canonical_lock(committed), sort_keys=True
        ):
            details = []
            by_name = {s["name"]: s for s in canonical_lock(rebuilt)["skills"]}
            for skill in canonical_lock(committed)["skills"]:
                other = by_name.get(skill["name"])
                if other is None:
                    details.append(f"{skill['name']}: missing from rebuilt content")
                    continue
                got = {f["path"]: f for f in other["files"]}
                want = {f["path"]: f for f in skill["files"]}
                for path in sorted(set(want) | set(got)):
                    if got.get(path) != want.get(path):
                        details.append(f"{skill['name']}: {path}")
                        break
            problems.append(
                "lock file does not match repo content (run --from-installed and commit)"
                + (f"; first differences: {details[:8]}" if details else "")
            )
    if problems:
        print("CHECK FAILED")
        for p in problems:
            print(" -", p)
        return 1
    print("CHECK OK: lock, archive, and repo skills are consistent")
    print(f"  skills: {len(committed['skills'])}")
    print(f"  ars archive: {committed['sources']['ars']['archive']} "
          f"sha256={committed['sources']['ars']['archiveSha256']}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--from-installed", action="store_true",
                    help="read ARS skills from $DSH_HOME/skills and rebuild archive + lock")
    ap.add_argument("--check", action="store_true",
                    help="rebuild from committed content and compare with the committed lock")
    ap.add_argument("--dsh-home", type=Path, default=DEFAULT_DSH_HOME)
    args = ap.parse_args()
    if args.from_installed == args.check:
        ap.error("choose exactly one of --from-installed / --check")
    if sys.version_info < (3, 10):
        raise SystemExit("python >= 3.10 required")
    if not (REPO_ROOT / "skills").is_dir():
        raise SystemExit(f"not a repository checkout: {REPO_ROOT}")
    if args.from_installed:
        return cmd_from_installed(args)
    return cmd_check(args)


if __name__ == "__main__":
    raise SystemExit(main())
