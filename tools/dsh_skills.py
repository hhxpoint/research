#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hhxpoint/research skill installer for DeepSeek Harness (DSH).

Every skill in this repository is a standard DSH skill bundle:
`<name>/SKILL.md` with YAML frontmatter (`name` kebab-case + `description`),
plus optional references/scripts/assets. This tool installs them into
`$DSH_HOME/skills/` (default `~/.dsh/skills/`) from the committed payloads,
so installation needs no network and is reproducible:

  * `skills/<name>/`                 plain MIT-licensed skills
  * `vendor/ars-dsh-*.tar.gz`        CC BY-NC 4.0 academic-research-skills pack

Commands:
  list       show the catalog and which skills are installed
  install    install a preset / selection (with backup + rollback)
  verify     check installed skills against the lock file (hashes + spec)
  uninstall  remove skills (backup kept by default)
  doctor     environment / repository health check
  selftest   validate repository content only (used by CI)

Exit codes: 0 success, 1 verification failed, 2 usage/config error,
3 integrity error (hash mismatch / unsafe archive).
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


class SkillError(Exception):
    """Base error with a process exit code."""

    exit_code = EXIT_USAGE


class IntegrityError(SkillError):
    exit_code = EXIT_INTEGRITY


class VerifyError(SkillError):
    exit_code = EXIT_VERIFY


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
        if not NAME_RE.match(name):
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
# hashing / verification helpers
# --------------------------------------------------------------------------- #
def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_files(root: Path) -> dict[str, dict]:
    files: dict[str, dict] = {}
    for p in sorted(root.rglob("*")):
        if p.is_dir():
            continue
        if not p.is_file():
            raise IntegrityError(f"unsupported file type: {p}")
        rel = p.relative_to(root).as_posix()
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
    name = str(meta.get("name") or "").strip()
    desc = str(meta.get("description") or "").strip()
    if not name:
        raise VerifyError(f"{skill_md}: missing name")
    if not NAME_RE.match(name):
        raise VerifyError(f"{skill_md}: name is not kebab-case: {name!r}")
    if name != expected_name:
        raise VerifyError(f"{skill_md}: name {name!r} != directory name {expected_name!r}")
    if not desc:
        raise VerifyError(f"{skill_md}: missing description")
    if not body.strip():
        raise VerifyError(f"{skill_md}: empty body")
    return meta


# --------------------------------------------------------------------------- #
# payload materialization
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


def extract_archive(tar_path: Path, dest: Path) -> None:
    with tarfile.open(tar_path, "r:gz") as tar:
        members = []
        dest_resolved = dest.resolve()
        for m in tar.getmembers():
            p = Path(m.name)
            if p.is_absolute() or ".." in p.parts or m.issym() or m.islnk():
                raise IntegrityError(f"unsafe archive member: {m.name!r}")
            target = (dest_resolved / m.name).resolve()
            if target != dest_resolved and dest_resolved not in target.parents:
                raise IntegrityError(f"unsafe archive member path: {m.name!r}")
            members.append(m)
        try:
            tar.extractall(dest, members=members, filter="data")
        except TypeError:  # Python without extraction filters (<3.12 and old 3.10/3.11)
            tar.extractall(dest, members=members)


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
    if getattr(args, "only", None):
        names = [s.strip() for s in args.only.split(",") if s.strip()]
        unknown = [n for n in names if n not in catalog]
        if unknown:
            raise SkillError(f"unknown skill(s): {unknown}")
    elif getattr(args, "exclude", None):
        excluded = {s.strip() for s in args.exclude.split(",") if s.strip()}
        unknown = [n for n in excluded if n not in catalog]
        if unknown:
            raise SkillError(f"unknown skill(s) in --exclude: {unknown}")
        mode = getattr(args, "mode", "full")
        base = lock["presets"].get(mode)
        if base is None:
            raise SkillError(f"unknown preset: {mode!r} (have {sorted(lock['presets'])})")
        names = [n for n in base if n not in excluded]
    else:
        mode = getattr(args, "mode", "full")
        names = lock["presets"].get(mode)
        if names is None:
            raise SkillError(f"unknown preset: {mode!r} (have {sorted(lock['presets'])})")
    return list(names)


def installed_status(lock: dict, skills_root: Path) -> dict[str, str]:
    status = {}
    for entry in lock["skills"]:
        d = skills_root / entry["name"]
        if not d.is_dir():
            status[entry["name"]] = "absent"
            continue
        try:
            problems = compare_files(d, entry["files"], allow_extra=False)
        except Exception:  # noqa: BLE001
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

    # Cheap source validation first (archive hash / repo payload presence).
    has_tar = any(skills_by_name(lock)[n]["mode"] == "tar" for n in selected)
    if has_tar:
        archive = ars_archive_path(lock)
    if args.dry_run:
        if has_tar:
            print(f"[dry-run] archive OK: {archive.name} ({archive.stat().st_size} B)")
        for name in selected:
            entry = skills_by_name(lock)[name]
            print(f"[dry-run] would install {name} "
                  f"({entry['mode']}, source={entry['source']}, license={entry['license']})")
        print("[dry-run] no files written")
        return EXIT_OK

    home.mkdir(parents=True, exist_ok=True)
    before = installed_status(lock, skills_root)
    ars_extract: Path | None = None
    staging = Path(tempfile.mkdtemp(prefix=".dsh-skills-staging-", dir=home))
    try:
        if has_tar:
            ars_extract = staging / ".ars"
            extract_archive(archive, ars_extract)
        prepared: list[str] = []
        for name in selected:
            materialize(lock, name, staging, ars_extract)
            prepared.append(name)

        # All payloads verified; now swap them in with rollback protection.
        backup_root = home / "skills-backup" / time.strftime("%Y%m%d-%H%M%S")
        installed, skipped, backups = [], [], []
        try:
            for name in prepared:
                target = skills_root / name
                if target.exists():
                    if before.get(name) == "ok" and not args.force:
                        skipped.append(name)
                        continue
                    if not args.no_backup:
                        backup_root.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(target), str(backup_root / name))
                        backups.append(name)
                    else:
                        shutil.rmtree(target)
                skills_root.mkdir(parents=True, exist_ok=True)
                os.replace(staging / name, target)
                installed.append(name)
        except Exception:
            # best-effort rollback of already swapped skills
            for name in installed:
                target = skills_root / name
                if target.exists():
                    shutil.rmtree(target, ignore_errors=True)
                src = staging / name
                if src.exists():
                    try:
                        os.replace(src, target)
                    except OSError:
                        pass
            for name in backups:
                src = backup_root / name
                if src.exists():
                    try:
                        os.replace(src, skills_root / name)
                    except OSError:
                        pass
            raise
        if skipped:
            print(f"unchanged (skipped): {', '.join(skipped)}")
        print(f"installed: {', '.join(installed) if installed else '(none)'}")
        if backups:
            print(f"replaced skills backed up to: {backup_root}")
        print("verify with: python tools/dsh_skills.py verify")
        return EXIT_OK
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def cmd_verify(args) -> int:
    lock = load_lock()
    home = dsh_home_from(args)
    skills_root = skills_root_for(home)
    names = select_skills(lock, args) if (args.only or args.exclude) else [e["name"] for e in lock["skills"]]
    catalog = skills_by_name(lock)
    report = {"dshHome": str(home), "ok": [], "missing": [], "errors": []}
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
    print(f"\nresult: {'FAIL' if code else 'PASS'}")
    return code


def cmd_uninstall(args) -> int:
    lock = load_lock()
    home = dsh_home_from(args)
    skills_root = skills_root_for(home)
    names = [s.strip() for s in args.names.split(",") if s.strip()] if args.names else []
    if not names:
        raise SkillError("provide --names a,b,c")
    known = skills_by_name(lock)
    unknown = [n for n in names if n not in known]
    if unknown and not args.force:
        raise SkillError(f"unknown skill(s): {unknown} (use --force to remove anyway)")
    backup_root = home / "skills-backup" / time.strftime("%Y%m%d-%H%M%S")
    removed = []
    for name in names:
        target = skills_root / name
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
    print("hhxpoint/research doctor")
    print(f"  python: {sys.version.split()[0]}")
    if sys.version_info < (3, 10):
        problems.append("python >= 3.10 required")
    print(f"  repo: {REPO_ROOT}")
    print(f"  pyyaml: {getattr(yaml, '__version__', '?')}")
    try:
        lock = load_lock()
        print(f"  lock: OK ({len(lock['skills'])} skills, schema {lock['schemaVersion']})")
    except SkillError as exc:
        problems.append(str(exc))
        lock = None
    if lock:
        try:
            archive = REPO_ROOT / lock["sources"]["ars"]["archive"]
            if not archive.is_file():
                problems.append(f"missing ARS archive: {archive}")
            elif sha256_file(archive) != lock["sources"]["ars"]["archiveSha256"]:
                problems.append("ARS archive sha256 mismatch")
            else:
                print(f"  ars archive: OK ({archive.name}, {archive.stat().st_size} B)")
        except SkillError as exc:
            problems.append(str(exc))
        home = dsh_home_from(args)
        skills_root = skills_root_for(home)
        print(f"  dsh home: {home} ({'exists' if home.is_dir() else 'missing'})")
        try:
            home.mkdir(parents=True, exist_ok=True)
            probe = home / ".write-probe"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
            print("  dsh home writable: yes")
        except OSError as exc:
            problems.append(f"dsh home not writable: {exc}")
        if skills_root.is_dir():
            status = installed_status(lock, skills_root)
            ok = sum(1 for v in status.values() if v == "ok")
            print(f"  installed: {ok}/{len(status)} ok")
            for name, state in status.items():
                if state not in ("ok", "absent"):
                    warnings.append(f"{name}: {state}")
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
    # 1) every copy skill exists in repo and matches lock
    for entry in lock["skills"]:
        name = entry["name"]
        if entry["mode"] == "copy":
            skill_dir = REPO_ROOT / "skills" / name
            if not skill_dir.is_dir():
                problems.append(f"{name}: missing repo skill dir")
                continue
            try:
                meta = validate_skill_dir(skill_dir, name)
                desc = str(meta.get("description") or "")
                if len(desc) > 4000:
                    problems.append(f"{name}: description suspiciously long ({len(desc)} chars)")
            except SkillError as exc:
                problems.append(str(exc))
            problems.extend(f"{name}: {p}" for p in compare_files(skill_dir, entry["files"], allow_extra=False))
    # 2) archive exists, hash matches, members match lock, extraction is safe
    try:
        archive = ars_archive_path(lock)
        with tempfile.TemporaryDirectory(prefix="research-selftest-") as td:
            td_path = Path(td)
            extract_archive(archive, td_path)
            for name in [e["name"] for e in lock["skills"] if e["mode"] == "tar"]:
                skill_dir = td_path / name
                if not skill_dir.is_dir():
                    problems.append(f"{name}: missing from archive")
                    continue
                try:
                    validate_skill_dir(skill_dir, name)
                except SkillError as exc:
                    problems.append(str(exc))
                problems.extend(f"{name}: {p}" for p in compare_files(skill_dir, catalog[name]["files"], allow_extra=False))
    except SkillError as exc:
        problems.append(str(exc))
    # 3) presets and metadata sanity
    if "research-stack" not in catalog:
        problems.append("research-stack skill missing")
    if "full" not in lock["presets"]:
        problems.append("preset 'full' missing")
    if problems:
        print(f"SELFTEST FAILED ({len(problems)} problem(s)):")
        for p in problems[:40]:
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
    p.add_argument("--no-backup", action="store_true", help="do not keep backups of replaced skills")
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
    p.add_argument("--force", action="store_true", help="allow unknown names")
    p.set_defaults(func=cmd_uninstall)

    p = sub.add_parser("doctor", help="environment and repository health check")
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
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
