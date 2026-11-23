#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hhxpoint/research skill installer for DeepSeek Harness (DSH).

Every skill in this repository is a standard DSH skill bundle:
`<name>/SKILL.md` with YAML frontmatter (`name` kebab-case + `description`),
plus optional references/scripts/assets, and - for every third-party skill -
`NOTICE.md` + `LICENSE.txt` carrying attribution and the full license text.

Payloads are committed, so installation needs no network and is reproducible:

  * `skills/<name>/`                 plain skills (MIT or self-authored)
  * `vendor/ars-dsh-*.tar.gz`        CC BY-NC 4.0 academic-research-skills pack

Commands:
  list       show the catalog and which skills are installed
  install    install a preset / selection (atomic swap, backup, rollback)
  verify     check installed skills against the lock file (hashes + spec)
  uninstall  remove skills (backup kept by default; path-safe)
  doctor     read-only environment / repository health check
  selftest   validate repository content only (used by CI)

Exit codes:
  0  success
  1  verify / selftest / doctor check failed (including installed-file hash mismatch)
  2  usage or configuration error (bad arguments, unwritable paths, missing tools)
  3  install-time integrity error (archive/payload hash mismatch, unsafe archive)

`--no-backup` still performs the install transactionally inside one run
(replaced copies are staged and restored on failure); only after success they
are discarded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tarfile
import tempfile
import time
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.stderr.write("PyYAML is required: python -m pip install pyyaml\n")
    raise SystemExit(2)

try:  # make output stable on legacy Windows consoles
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

REPO_ROOT = Path(__file__).resolve().parent.parent
LOCK_PATH = REPO_ROOT / "manifests" / "skills.lock.json"
DEFAULT_DSH_HOME = Path(os.environ.get("DSH_HOME") or (Path.home() / ".dsh"))
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SCHEMA_VERSION = 1

EXIT_OK, EXIT_VERIFY, EXIT_USAGE, EXIT_INTEGRITY = 0, 1, 2, 3

# Runtime artefacts that are ignored on both sides of a hash comparison and are
# never packaged into the ARS archive (they may contain machine-specific paths).
IGNORED_DIR_NAMES = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
IGNORED_FILE_SUFFIXES = (".pyc", ".pyo")
IGNORED_FILE_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}

# DSH silently drops a skill whose frontmatter uses these camelCase keys.
CAMEL_INVOCATION_KEYS = ("disableModelInvocation", "modelInvocable", "userInvocable")

REQUIRED_NOTICE = "NOTICE.md"
REQUIRED_LICENSE = "LICENSE.txt"
REQUIRED_PORT = "DSH-PORT.md"
LICENSE_TOKEN = {"MIT": "MIT License", "CC-BY-NC-4.0": "Creative Commons"}


class SkillError(Exception):
    """Base error with a process exit code."""

    exit_code = EXIT_USAGE


class IntegrityError(SkillError):
    exit_code = EXIT_INTEGRITY


class VerifyError(SkillError):
    exit_code = EXIT_VERIFY


# --------------------------------------------------------------------------- #
# shared helpers
# --------------------------------------------------------------------------- #
def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def is_ignored(rel: str) -> bool:
    """True for runtime artefacts that must not participate in verification."""
    parts = rel.split("/")
    if any(part in IGNORED_DIR_NAMES for part in parts[:-1]):
        return True
    name = parts[-1]
    return name in IGNORED_FILE_NAMES or name.endswith(IGNORED_FILE_SUFFIXES)


def collect_files(root: Path) -> dict[str, dict]:
    """Hash every packaged file under root, ignoring runtime artefacts.

    Symlinks are rejected: the lock models a portable file tree, and a symlink
    could point outside the skill directory.
    """
    files: dict[str, dict] = {}
    for p in sorted(root.rglob("*"), key=lambda x: x.relative_to(root).as_posix()):
        rel = p.relative_to(root).as_posix()
        if is_ignored(rel):
            continue
        if p.is_symlink():
            raise IntegrityError(f"symbolic links are not allowed in a skill dir: {p}")
        if p.is_dir():
            continue
        if not p.is_file():
            raise IntegrityError(f"unsupported file type in skill dir: {p}")
        files[rel] = {"sha256": sha256_file(p), "bytes": p.stat().st_size}
    return files


def compare_files(root: Path, expected: list[dict], *, allow_extra: bool = True) -> list[str]:
    """Return human-readable problems comparing an installed dir with the lock."""
    problems: list[str] = []
    actual = collect_files(root)
    expected_map = {f["path"]: f for f in expected}
    for rel, exp in sorted(expected_map.items()):
        got = actual.get(rel)
        if got is None:
            problems.append(f"missing file: {rel}")
        elif got["sha256"] != exp["sha256"]:
            problems.append(f"hash mismatch: {rel}")
    extra = sorted(set(actual) - set(expected_map))
    if extra and not allow_extra:
        problems.extend(f"unexpected file: {rel}" for rel in extra)
    return problems


# --------------------------------------------------------------------------- #
# lock file
# --------------------------------------------------------------------------- #
def load_lock(path: Path = LOCK_PATH) -> dict:
    if not path.is_file():
        raise SkillError(f"lock file not found: {path}")
    try:
        lock = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SkillError(f"invalid lock JSON: {exc}") from exc
    if lock.get("schemaVersion") != SCHEMA_VERSION:
        raise SkillError(f"unsupported lock schemaVersion: {lock.get('schemaVersion')!r}")
    skills = lock.get("skills")
    if not isinstance(skills, list) or not skills:
        raise SkillError("lock has no skills")
    seen: set[str] = set()
    for entry in skills:
        for key in ("name", "source", "mode", "license", "description", "files"):
            if key not in entry:
                raise SkillError(f"lock skill entry missing {key!r}: {entry.get('name')!r}")
        name = entry["name"]
        if not NAME_RE.fullmatch(name):
            raise SkillError(f"invalid skill name in lock: {name!r}")
        if name in seen:
            raise SkillError(f"duplicate skill in lock: {name!r}")
        seen.add(name)
        if entry["mode"] not in ("copy", "tar"):
            raise SkillError(f"{name}: unsupported mode {entry['mode']!r}")
        if not isinstance(entry["files"], list) or not entry["files"]:
            raise SkillError(f"{name}: empty file list")
    sources = lock.get("sources")
    if not isinstance(sources, dict):
        raise SkillError("lock has no sources")
    for entry in lock["skills"]:
        if entry["source"] not in sources:
            raise SkillError(f"{entry['name']}: unknown source {entry['source']!r}")
    presets = lock.get("presets")
    if not isinstance(presets, dict) or not presets:
        raise SkillError("lock has no presets")
    for preset, names in presets.items():
        if not isinstance(names, list) or not names:
            raise SkillError(f"preset {preset!r} is empty")
        unknown = [n for n in names if n not in seen]
        if unknown:
            raise SkillError(f"preset {preset!r} references unknown skills: {unknown}")
    return lock


def source_entry(lock: dict, source_id: str) -> dict:
    try:
        return lock["sources"][source_id]
    except KeyError as exc:
        raise SkillError(f"lock references unknown source: {source_id!r}") from exc


def skills_by_name(lock: dict) -> dict[str, dict]:
    return {e["name"]: e for e in lock["skills"]}


# --------------------------------------------------------------------------- #
# SKILL.md validation
# --------------------------------------------------------------------------- #
def parse_frontmatter(skill_md: Path) -> tuple[dict, str]:
    try:
        text = skill_md.read_text(encoding="utf-8")
    except OSError as exc:
        raise VerifyError(f"cannot read {skill_md}: {exc}") from exc
    if not text.startswith("---"):
        raise VerifyError(f"{skill_md}: does not start with '---'")
    match = re.search(r"\n---\s*\n", text[3:])
    if not match:
        raise VerifyError(f"{skill_md}: unterminated frontmatter")
    raw = text[3 : 3 + match.start()]
    try:
        meta = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise VerifyError(f"{skill_md}: YAML error: {exc}") from exc
    if not isinstance(meta, dict):
        raise VerifyError(f"{skill_md}: frontmatter is not a mapping")
    body = text[3 + match.end() :]
    return meta, body


def validate_skill_dir(skill_dir: Path, expected_name: str) -> dict:
    if not skill_dir.is_dir():
        raise VerifyError(f"missing skill directory: {skill_dir}")
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        raise VerifyError(f"missing SKILL.md: {skill_md}")
    meta, body = parse_frontmatter(skill_md)
    for key in CAMEL_INVOCATION_KEYS:
        if key in meta:
            raise VerifyError(
                f"{skill_md}: camelCase invocation key {key!r} is rejected by DSH; "
                "use kebab-case (disable-model-invocation / user-invocable)"
            )
    name = str(meta.get("name") or "").strip()
    desc = str(meta.get("description") or "").strip()
    if not name:
        raise VerifyError(f"{skill_md}: missing name")
    if not NAME_RE.fullmatch(name):
        raise VerifyError(f"{skill_md}: name is not kebab-case: {name!r}")
    if name != expected_name:
        raise VerifyError(f"{skill_md}: name {name!r} != directory name {expected_name!r}")
    if not desc:
        raise VerifyError(f"{skill_md}: missing description")
    if not body.strip():
        raise VerifyError(f"{skill_md}: empty body")
    return meta


def check_skill_notices(skill_dir: Path, name: str, source: dict, expected_commit: str) -> list[str]:
    """License/provenance checks shared by selftest and (optionally) verify."""
    problems: list[str] = []
    license_id = source.get("license", "")
    notice = skill_dir / REQUIRED_NOTICE
    license_file = skill_dir / REQUIRED_LICENSE
    port = skill_dir / REQUIRED_PORT
    if not notice.is_file():
        problems.append(f"{name}: missing {REQUIRED_NOTICE}")
    else:
        text = notice.read_text(encoding="utf-8", errors="replace")
        if source.get("repo") and source["repo"] not in text:
            problems.append(f"{name}: {REQUIRED_NOTICE} does not mention upstream repo")
        if expected_commit not in text:
            problems.append(f"{name}: {REQUIRED_NOTICE} does not mention pinned provenance")
        if license_id and license_id not in text:
            problems.append(f"{name}: {REQUIRED_NOTICE} does not mention license {license_id}")
    if not license_file.is_file():
        problems.append(f"{name}: missing {REQUIRED_LICENSE}")
    else:
        text = license_file.read_text(encoding="utf-8", errors="replace")
        token = LICENSE_TOKEN.get(license_id)
        if token and token not in text:
            problems.append(f"{name}: {REQUIRED_LICENSE} does not look like {license_id}")
        if len(text) < 500:
            problems.append(f"{name}: {REQUIRED_LICENSE} is suspiciously short")
    if not port.is_file():
        problems.append(f"{name}: missing {REQUIRED_PORT}")
    else:
        port_text = port.read_text(encoding="utf-8", errors="replace")
        match = re.search(r"^- commit: `([^`]+)`", port_text, re.M)
        if not match:
            problems.append(f"{name}: {REQUIRED_PORT} has no commit line")
        elif expected_commit not in match.group(1):
            problems.append(
                f"{name}: {REQUIRED_PORT} commit {match.group(1)!r} != pinned {expected_commit!r}"
            )
        if license_id and license_id not in port_text:
            problems.append(f"{name}: {REQUIRED_PORT} does not mention license {license_id}")
    return problems


# --------------------------------------------------------------------------- #
# archive handling
# --------------------------------------------------------------------------- #
def ars_archive_path(lock: dict) -> Path:
    src = source_entry(lock, "ars")
    path = REPO_ROOT / src["archive"]
    if not path.is_file():
        raise IntegrityError(f"missing ARS archive: {path}")
    actual = sha256_file(path)
    if actual != src["archiveSha256"]:
        raise IntegrityError(
            f"ARS archive sha256 mismatch (expected {src['archiveSha256']}, got {actual})"
        )
    return path


def _extract_filtered(tar: tarfile.TarFile, dest: Path, members: list[tarfile.TarInfo]) -> None:
    if hasattr(tarfile, "data_filter"):
        tar.extractall(dest, members=members, filter="data")
    else:  # Python versions without the 2025 extraction filters
        tar.extractall(dest, members=members)


def extract_archive(tar_path: Path, dest: Path) -> None:
    """Extract and reject anything that is not a plain relative file/dir."""
    with tarfile.open(tar_path, "r:gz") as tar:
        members = []
        dest_resolved = dest.resolve()
        for m in tar.getmembers():
            path = Path(m.name)
            if path.is_absolute() or ".." in path.parts:
                raise IntegrityError(f"unsafe archive member: {m.name!r}")
            if m.issym() or m.islnk():
                raise IntegrityError(f"archive links are not allowed: {m.name!r}")
            if not (m.isfile() or m.isdir()):
                raise IntegrityError(f"unsupported archive member type: {m.name!r}")
            target = (dest_resolved / m.name).resolve()
            if target != dest_resolved and dest_resolved not in target.parents:
                raise IntegrityError(f"unsafe archive member path: {m.name!r}")
            members.append(m)
        _extract_filtered(tar, dest, members)


# --------------------------------------------------------------------------- #
# payload materialization
# --------------------------------------------------------------------------- #
def verify_payload(lock: dict, name: str, skill_dir: Path) -> None:
    entry = skills_by_name(lock)[name]
    problems = compare_files(skill_dir, entry["files"], allow_extra=False)
    if problems:
        raise IntegrityError(f"{name}: payload does not match lock: {problems[:5]}")


def materialize(lock: dict, name: str, dest_root: Path, ars_extract: Path | None) -> Path:
    """Copy/extract one skill into dest_root/<name>; return that directory."""
    entry = skills_by_name(lock)[name]
    target = dest_root / name
    if entry["mode"] == "copy":
        src = REPO_ROOT / "skills" / name
        if not src.is_dir():
            raise IntegrityError(f"missing repo payload: {src}")
        shutil.copytree(src, target)
    else:
        assert ars_extract is not None
        src = ars_extract / name
        if not src.is_dir():
            raise IntegrityError(f"archive does not contain skill: {name}")
        shutil.copytree(src, target)
    validate_skill_dir(target, name)
    verify_payload(lock, name, target)
    return target


# --------------------------------------------------------------------------- #
# commands
# --------------------------------------------------------------------------- #
def dsh_home_from(args) -> Path:
    home = Path(args.dsh_home).expanduser() if getattr(args, "dsh_home", None) else DEFAULT_DSH_HOME
    return home.resolve()


def skills_root_for(home: Path) -> Path:
    return home / "skills"


def select_skills(lock: dict, args) -> list[str]:
    catalog = skills_by_name(lock)
    only = getattr(args, "only", None)
    exclude = getattr(args, "exclude", None)
    if only and exclude:
        raise SkillError("--only and --exclude are mutually exclusive")
    if only:
        requested = [s.strip() for s in only.split(",") if s.strip()]
        unknown = [n for n in requested if n not in catalog]
        if unknown:
            raise SkillError(f"unknown skill(s): {unknown}")
        return list(dict.fromkeys(requested))
    mode = getattr(args, "mode", "full")
    base = lock["presets"].get(mode)
    if base is None:
        raise SkillError(f"unknown preset: {mode!r} (have {sorted(lock['presets'])})")
    if exclude:
        excluded = {s.strip() for s in exclude.split(",") if s.strip()}
        unknown = [n for n in excluded if n not in catalog]
        if unknown:
            raise SkillError(f"unknown skill(s) in --exclude: {unknown}")
        return [n for n in base if n not in excluded]
    return list(base)


def installed_status(lock: dict, skills_root: Path) -> dict[str, str]:
    status = {}
    for entry in lock["skills"]:
        d = skills_root / entry["name"]
        if not d.is_dir():
            status[entry["name"]] = "absent"
            continue
        try:
            problems = compare_files(d, entry["files"], allow_extra=False)
        except SkillError:
            status[entry["name"]] = "broken"
            continue
        status[entry["name"]] = "ok" if not problems else "drifted"
    return status


def cmd_list(args) -> int:
    lock = load_lock()
    home = dsh_home_from(args)
    status = installed_status(lock, skills_root_for(home))
    rows = []
    for entry in lock["skills"]:
        rows.append(
            {
                "name": entry["name"],
                "category": entry["category"],
                "license": entry["license"],
                "status": status[entry["name"]],
                "description": entry["description"][:110],
            }
        )
    if args.json:
        print(json.dumps({"dshHome": str(home), "skills": rows}, ensure_ascii=False, indent=2))
        return EXIT_OK
    width = max(len(r["name"]) for r in rows)
    print(f"DSH home: {home}")
    print(f"{'skill'.ljust(width)}  {'status':8}  {'license':13}  category")
    print(f"{'-' * width}  {'-' * 8}  {'-' * 13}  ----------")
    for r in rows:
        print(f"{r['name'].ljust(width)}  {r['status']:8}  {r['license']:13}  {r['category']}")
    print(f"\n{sum(1 for s in status.values() if s == 'ok')}/{len(rows)} installed; "
          f"presets: {', '.join(sorted(lock['presets']))}")
    return EXIT_OK


def cmd_install(args) -> int:
    lock = load_lock()
    home = dsh_home_from(args)
    skills_root = skills_root_for(home)
    payload_root = REPO_ROOT / "skills"
    if skills_root == payload_root or payload_root in skills_root.parents:
        raise SkillError(f"refusing to overwrite the repository payload directory: {skills_root}")
    selected = select_skills(lock, args)
    if not selected:
        raise SkillError("nothing selected")
    print(f"DSH home: {home}")
    print(f"installation root: {skills_root}")
    print(f"selected: {', '.join(selected)}")

    catalog = skills_by_name(lock)
    has_tar = any(catalog[n]["mode"] == "tar" for n in selected)
    archive = ars_archive_path(lock) if has_tar else None
    if args.dry_run:
        if archive is not None:
            print(f"[dry-run] archive OK: {archive.name} ({archive.stat().st_size} B)")
        for name in selected:
            entry = catalog[name]
            print(f"[dry-run] would install {name} "
                  f"({entry['mode']}, source={entry['source']}, license={entry['license']})")
        print("[dry-run] no files written")
        return EXIT_OK

    home.mkdir(parents=True, exist_ok=True)
    before = installed_status(lock, skills_root)
    staging = Path(tempfile.mkdtemp(prefix=".dsh-skills-staging-", dir=home))
    backup_root = None if args.no_backup else (home / "skills-backup" / time.strftime("%Y%m%d-%H%M%S"))
    dropped_root = staging / ".dropped"  # keeps replaced dirs inside the transaction even with --no-backup
    installed: list[str] = []
    replaced: list[str] = []
    skipped: list[str] = []
    try:
        ars_extract: Path | None = None
        if has_tar:
            ars_extract = staging / ".ars"
            assert archive is not None
            extract_archive(archive, ars_extract)
        for name in selected:
            materialize(lock, name, staging, ars_extract)

        try:
            for name in selected:
                target = skills_root / name
                if target.exists():
                    if before.get(name) == "ok" and not args.force:
                        skipped.append(name)
                        continue
                    if backup_root is not None:
                        backup_root.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(target), str(backup_root / name))
                    else:
                        dropped_root.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(target), str(dropped_root / name))
                    replaced.append(name)
                skills_root.mkdir(parents=True, exist_ok=True)
                os.replace(staging / name, target)
                installed.append(name)
        except BaseException:
            # best-effort rollback: remove newly swapped skills, restore replacements
            for name in installed:
                shutil.rmtree(skills_root / name, ignore_errors=True)
            for name in replaced:
                candidates = [backup_root / name] if backup_root is not None else [dropped_root / name]
                for src in candidates:
                    if src.exists():
                        try:
                            os.replace(src, skills_root / name)
                        except OSError:
                            pass
                        break
            raise

        if skipped:
            print(f"unchanged (skipped): {', '.join(skipped)}")
        print(f"installed: {', '.join(installed) if installed else '(none)'}")
        if replaced:
            if backup_root is not None:
                print(f"previous versions backed up to: {backup_root}")
            else:
                print("previous versions discarded (--no-backup); the swap itself is rollback-safe")
        print("verify with: python tools/dsh_skills.py verify")
        return EXIT_OK
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def cmd_verify(args) -> int:
    lock = load_lock()
    home = dsh_home_from(args)
    skills_root = skills_root_for(home)
    catalog = skills_by_name(lock)
    if args.only or args.exclude:
        names = select_skills(lock, args)
    else:
        names = [e["name"] for e in lock["skills"]]
    report: dict = {"dshHome": str(home), "ok": [], "missing": [], "errors": [], "unknown": []}
    for name in names:
        entry = catalog[name]
        skill_dir = skills_root / name
        if not skill_dir.is_dir():
            report["missing"].append(name)
            continue
        problems: list[str] = []
        try:
            validate_skill_dir(skill_dir, name)
            problems.extend(compare_files(skill_dir, entry["files"], allow_extra=False))
        except SkillError as exc:
            problems.append(str(exc))
        if problems:
            report["errors"].append({"name": name, "problems": problems})
        else:
            report["ok"].append(name)
    if skills_root.is_dir():
        known = set(catalog)
        for child in sorted(skills_root.iterdir(), key=lambda p: p.name):
            if child.is_dir() and not child.name.startswith(".") and child.name not in known:
                report["unknown"].append(child.name)
    code = EXIT_OK
    if report["errors"]:
        code = EXIT_VERIFY
    if report["missing"] and args.require_all:
        code = EXIT_VERIFY
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return code
    print(f"DSH home: {home}")
    print(f"OK:       {len(report['ok'])}  ({', '.join(report['ok']) or '-'})")
    if report["missing"]:
        print(f"MISSING:  {len(report['missing'])}  ({', '.join(report['missing'])})"
              + ("  [failure: --require-all]" if args.require_all else "  (warning)"))
    for item in report["errors"]:
        print(f"FAILED:   {item['name']}")
        for problem in item["problems"][:8]:
            print(f"          - {problem}")
        if len(item["problems"]) > 8:
            print(f"          ... {len(item['problems']) - 8} more")
    if report["unknown"]:
        print(f"UNKNOWN:  {len(report['unknown'])}  ({', '.join(report['unknown'])})  "
              "(not managed by this repository; warning only)")
    print(f"\nresult: {'FAIL' if code else 'PASS'}")
    return code


def validate_uninstall_name(name: str) -> str:
    """Reject anything that is not a plain kebab-case skill name.

    This is intentionally applied even with --force: --force only relaxes the
    catalog check, it must never relax path safety.
    """
    if not name or not NAME_RE.fullmatch(name):
        raise SkillError(
            f"invalid skill name: {name!r}; only kebab-case names are accepted "
            "(path separators, '..' and absolute paths are rejected)"
        )
    return name


def cmd_uninstall(args) -> int:
    lock = load_lock()
    home = dsh_home_from(args)
    skills_root = skills_root_for(home)
    names = [s.strip() for s in (args.names or "").split(",") if s.strip()]
    if not names:
        raise SkillError("provide --names a,b,c")
    known = skills_by_name(lock)
    resolved_root = skills_root.resolve()
    backup_root = home / "skills-backup" / time.strftime("%Y%m%d-%H%M%S")
    removed = []
    for name in names:
        validate_uninstall_name(name)
        if name not in known and not args.force:
            raise SkillError(f"unknown skill(s): {[name]} (use --force to remove anyway)")
        target = (skills_root / name).resolve()
        if target != resolved_root and resolved_root not in target.parents:
            raise IntegrityError(f"refusing to remove path outside skills root: {target}")
        if not target.is_dir():
            print(f"not installed: {name}")
            continue
        if args.keep:
            print(f"kept (--keep): {name}")
            continue
        if not args.no_backup:
            backup_root.mkdir(parents=True, exist_ok=True)
            shutil.move(str(target), str(backup_root / name))
            print(f"removed: {name} (backup: {backup_root / name})")
        else:
            shutil.rmtree(target)
            print(f"removed: {name}")
        removed.append(name)
    print(f"removed {len(removed)} skill(s)")
    return EXIT_OK


def cmd_doctor(args) -> int:
    problems: list[str] = []
    warnings: list[str] = []
    print("hhxpoint/research doctor (read-only)")
    print(f"  python: {sys.version.split()[0]}")
    if sys.version_info < (3, 10):
        problems.append("python >= 3.10 required")
    print(f"  repo: {REPO_ROOT}")
    print(f"  pyyaml: {getattr(yaml, '__version__', '?')}")
    lock = None
    try:
        lock = load_lock()
        print(f"  lock: OK ({len(lock['skills'])} skills, schema {lock['schemaVersion']})")
    except SkillError as exc:
        problems.append(str(exc))
    if lock:
        try:
            archive = ars_archive_path(lock)
            print(f"  ars archive: OK ({archive.name}, {archive.stat().st_size} B)")
        except SkillError as exc:
            problems.append(str(exc))
        home = dsh_home_from(args)
        skills_root = skills_root_for(home)
        if home.exists():
            print(f"  dsh home: {home} (exists)")
            if not os.access(home, os.W_OK):
                problems.append(f"dsh home is not writable: {home}")
            else:
                print("  dsh home writable: yes")
        else:
            print(f"  dsh home: {home} (missing; doctor does not create it)")
            parent = home.parent
            if not os.access(parent, os.W_OK):
                problems.append(f"parent directory is not writable: {parent}")
        if skills_root.is_dir():
            status = installed_status(lock, skills_root)
            ok = sum(1 for v in status.values() if v == "ok")
            print(f"  installed: {ok}/{len(status)} ok")
            for name, state in status.items():
                if state not in ("ok", "absent"):
                    warnings.append(f"{name}: {state}")
            known = set(skills_by_name(lock))
            unknown = sorted(
                p.name for p in skills_root.iterdir()
                if p.is_dir() and not p.name.startswith(".") and p.name not in known
            )
            if unknown:
                warnings.append(f"unknown skill dirs (not managed here): {', '.join(unknown)}")
        else:
            print("  skills root: not created yet")
        if warnings:
            print("  warnings:")
            for w in warnings:
                print(f"    - {w}")
    if problems:
        print("\nPROBLEMS:")
        for p in problems:
            print(f"  - {p}")
        return EXIT_VERIFY
    print("\nresult: PASS")
    return EXIT_OK


def cmd_selftest(args) -> int:
    """Validate the committed repository content without touching $DSH_HOME."""
    problems: list[str] = []
    try:
        lock = load_lock()
    except SkillError as exc:
        print(f"FAIL lock: {exc}")
        return EXIT_VERIFY
    catalog = skills_by_name(lock)

    def check_one(skill_dir: Path, name: str) -> None:
        expected_commit = source_entry(lock, catalog[name]["source"]).get("commit", "")
        try:
            validate_skill_dir(skill_dir, name)
        except SkillError as exc:
            problems.append(str(exc))
        problems.extend(f"{name}: {p}" for p in compare_files(skill_dir, catalog[name]["files"], allow_extra=False))
        problems.extend(
            f"{name}: {p}"
            for p in check_skill_notices(
                skill_dir, name, source_entry(lock, catalog[name]["source"]), expected_commit
            )
        )

    for entry in lock["skills"]:
        name = entry["name"]
        if entry["mode"] == "copy":
            skill_dir = REPO_ROOT / "skills" / name
            if not skill_dir.is_dir():
                problems.append(f"{name}: missing repo skill dir")
                continue
            check_one(skill_dir, name)

    try:
        archive = ars_archive_path(lock)
        with tempfile.TemporaryDirectory(prefix="research-selftest-") as td:
            td_path = Path(td)
            extract_archive(archive, td_path)
            expected = {
                f"{e['name']}/{f['path']}"
                for e in lock["skills"]
                if e["mode"] == "tar"
                for f in e["files"]
            }
            actual = {
                p.relative_to(td_path).as_posix()
                for p in td_path.rglob("*")
                if p.is_file()
            }
            for missing in sorted(expected - actual):
                problems.append(f"archive: missing {missing}")
            for extra in sorted(actual - expected):
                problems.append(f"archive: unexpected member {extra}")
            for entry in lock["skills"]:
                if entry["mode"] != "tar":
                    continue
                name = entry["name"]
                skill_dir = td_path / name
                if not skill_dir.is_dir():
                    problems.append(f"{name}: missing from archive")
                    continue
                check_one(skill_dir, name)
    except SkillError as exc:
        problems.append(str(exc))

    if "research-stack" not in catalog:
        problems.append("research-stack skill missing")
    for preset in ("minimal", "writing", "full"):
        if preset not in lock["presets"]:
            problems.append(f"preset {preset!r} missing")
    if "full" in lock["presets"] and len(lock["presets"]["full"]) != len(catalog):
        problems.append("preset 'full' does not contain every skill")
    for source_id, source in lock["sources"].items():
        license_file = REPO_ROOT / source.get("licenseFile", "")
        if not license_file.is_file():
            problems.append(f"source {source_id}: missing license file {source.get('licenseFile')!r}")

    if problems:
        print(f"SELFTEST FAILED ({len(problems)} problem(s)):")
        for p in problems[:60]:
            print(f"  - {p}")
        return EXIT_VERIFY
    print(f"SELFTEST PASS: {len(catalog)} skills, archive {lock['sources']['ars']['archive']}")
    return EXIT_OK


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dsh_skills.py",
        description="Install and verify the hhxpoint/research DSH skill stack.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument("--dsh-home", default=None, help="DSH home (default: $DSH_HOME or ~/.dsh)")
        p.add_argument("--json", action="store_true", help="machine-readable output")

    p = sub.add_parser("list", help="show catalog and installed status")
    add_common(p)
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("install", help="install skills into $DSH_HOME/skills")
    add_common(p)
    p.add_argument("--mode", default="full", choices=["minimal", "writing", "full"],
                   help="preset to install (default: full)")
    p.add_argument("--only", default=None, help="comma-separated skill names (overrides --mode)")
    p.add_argument("--exclude", default=None, help="comma-separated skills to drop from the preset")
    p.add_argument("--force", action="store_true", help="reinstall even when content is unchanged")
    p.add_argument("--no-backup", action="store_true",
                   help="discard replaced copies after a successful install (still transactional)")
    p.add_argument("--dry-run", action="store_true", help="print the plan only")
    p.set_defaults(func=cmd_install)

    p = sub.add_parser("verify", help="verify installed skills against the lock")
    add_common(p)
    p.add_argument("--only", default=None, help="comma-separated skill names")
    p.add_argument("--exclude", default=None, help="comma-separated skills to skip")
    p.add_argument("--require-all", action="store_true", help="fail when a skill is not installed")
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("uninstall", help="remove skills (backup kept by default)")
    add_common(p)
    p.add_argument("--names", default=None, help="comma-separated skill names")
    p.add_argument("--keep", action="store_true", help="print only, do not remove")
    p.add_argument("--no-backup", action="store_true")
    p.add_argument("--force", action="store_true", help="allow names not present in the lock")
    p.set_defaults(func=cmd_uninstall)

    p = sub.add_parser("doctor", help="read-only environment and repository health check")
    add_common(p)
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("selftest", help="validate repository content only (CI)")
    add_common(p)
    p.set_defaults(func=cmd_selftest)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except SkillError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return exc.exit_code
    except OSError as exc:
        print(f"ERROR: filesystem operation failed: {exc}", file=sys.stderr)
        return EXIT_USAGE
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
