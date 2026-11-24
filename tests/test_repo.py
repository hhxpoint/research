#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Repository tests: lock integrity, installer behaviour, archive safety.

Run with:  python -m unittest discover -s tests -v
No network access is required.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
CLI = REPO / "tools" / "dsh_skills.py"
LOCK = REPO / "manifests" / "skills.lock.json"
BUILD_LOCK = REPO / "tools" / "build_lock.py"
NOTICES = REPO / "tools" / "apply_notices.py"


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem + "_mod", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


MOD = load_module(CLI)
BL = load_module(BUILD_LOCK)


def run(*args: str, dsh_home: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(CLI), *args]
    if dsh_home is not None:
        cmd += ["--dsh-home", str(dsh_home)]
    return run_cmd(cmd, check=check)


def run_cmd(cmd: list[str], check: bool = True, cwd: Path | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = subprocess.run(cmd, cwd=cwd or REPO, capture_output=True, text=True, encoding="utf-8", env=env)
    if check and proc.returncode != 0:
        raise AssertionError(
            f"command failed ({proc.returncode}): {' '.join(cmd)}\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return proc


class TestRepoContent(unittest.TestCase):
    def test_lock_schema_and_sources(self) -> None:
        lock = json.loads(LOCK.read_text(encoding="utf-8"))
        self.assertEqual(lock["schemaVersion"], 1)
        self.assertEqual(len(lock["skills"]), 17)
        names = {s["name"] for s in lock["skills"]}
        for expected in ("research-stack", "auto-research", "research-craft", "academic-paper", "autoresearch", "venue-templates"):
            self.assertIn(expected, names)
        for preset in ("minimal", "writing", "full"):
            self.assertIn(preset, lock["presets"])
            self.assertTrue(set(lock["presets"][preset]) <= names, preset)
        self.assertEqual(len(lock["presets"]["full"]), 17)
        for sid, source in lock["sources"].items():
            self.assertIn("license", source, sid)
            self.assertIn("repo", source, sid)
            self.assertTrue((REPO / source["licenseFile"]).is_file(), sid)
        ars = lock["sources"]["ars"]
        self.assertEqual(ars["license"], "CC-BY-NC-4.0")
        self.assertTrue((REPO / ars["archive"]).is_file())
        self.assertEqual(len(ars["archiveSha256"]), 64)
        # provenance values are pinned (self for our own skill)
        for sid, source in lock["sources"].items():
            self.assertNotIn("unpinned", source["commit"], sid)
        self.assertEqual(lock["sources"]["local"]["commit"], "self")

    def test_lock_file_hashes_match_repo_skills(self) -> None:
        lock = json.loads(LOCK.read_text(encoding="utf-8"))
        for entry in lock["skills"]:
            if entry["mode"] != "copy":
                continue
            skill_dir = REPO / "skills" / entry["name"]
            self.assertTrue(skill_dir.is_dir(), entry["name"])
            problems = MOD.compare_files(skill_dir, entry["files"], allow_extra=False)
            self.assertEqual(problems, [], entry["name"])

    def test_frontmatter_of_repo_skills(self) -> None:
        lock = json.loads(LOCK.read_text(encoding="utf-8"))
        for entry in lock["skills"]:
            if entry["mode"] != "copy":
                continue
            meta = MOD.validate_skill_dir(REPO / "skills" / entry["name"], entry["name"])
            self.assertEqual(meta["name"], entry["name"])

    def test_every_skill_has_notice_license_and_port(self) -> None:
        lock = json.loads(LOCK.read_text(encoding="utf-8"))
        for entry in lock["skills"]:
            if entry["mode"] != "copy":
                continue
            d = REPO / "skills" / entry["name"]
            for fname in ("NOTICE.md", "LICENSE.txt", "DSH-PORT.md"):
                self.assertTrue((d / fname).is_file(), f"{entry['name']}: {fname}")
        venue = REPO / "skills" / "venue-templates"
        self.assertTrue((venue / "NOTICE-LPPL.md").is_file())
        self.assertTrue((venue / "LICENSE-LPPL-1.3c.txt").is_file())

    def test_selftest(self) -> None:
        proc = run("selftest")
        self.assertIn("SELFTEST PASS", proc.stdout)

    def test_notices_check(self) -> None:
        proc = run_cmd([sys.executable, str(NOTICES), "--check"])
        self.assertIn("NOTICES OK", proc.stdout)

    def test_build_lock_check(self) -> None:
        proc = run_cmd([sys.executable, str(BUILD_LOCK), "--check"])
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("CHECK OK", proc.stdout)

    def test_provenance_matches_lock(self) -> None:
        lock = json.loads(LOCK.read_text(encoding="utf-8"))
        sources = lock["sources"]
        for entry in lock["skills"]:
            if entry["mode"] != "copy":
                continue
            port = (REPO / "skills" / entry["name"] / "DSH-PORT.md").read_text(encoding="utf-8")
            match = re.search(r"^- commit: `([^`]+)`", port, re.M)
            self.assertIsNotNone(match, entry["name"])
            self.assertEqual(match.group(1), sources[entry["source"]]["commit"], entry["name"])

    def test_ars_skill_licenses_are_cc_by_nc(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            with tarfile.open(REPO / "vendor" / "ars-dsh-v3.24.4-d103b100.tar.gz", "r:gz") as tar:
                members = {m.name: m for m in tar.getmembers()}
                for name in ("academic-paper", "deep-research", "sr-screener"):
                    notice = tar.extractfile(members[f"{name}/NOTICE.md"]).read().decode("utf-8")
                    license_text = tar.extractfile(members[f"{name}/LICENSE.txt"]).read().decode("utf-8")
                    port = tar.extractfile(members[f"{name}/DSH-PORT.md"]).read().decode("utf-8")
                    self.assertIn("CC-BY-NC-4.0", notice)
                    self.assertIn("Cheng-I Wu", notice)
                    self.assertIn("NonCommercial", license_text)
                    self.assertIn("d103b1005bb8c9f7a597e6a7ed473b75dcf8830e", port)
                    self.assertNotIn("unpinned", port)

    def test_research_craft_references(self) -> None:
        root = REPO / "skills" / "research-craft"
        meta = MOD.validate_skill_dir(root, "research-craft")
        self.assertIn("作图", meta["description"])
        expected = {
            "figures.md": ["不确定", "反模式"],
            "writing.md": ["摘要", "返修"],
            "experiment-design.md": ["反 claim", "基线"],
            "experiment-observation.md": ["run", "异常"],
            "phenomenon-understanding.md": ["替代解释", "Claim 强度"],
        }
        for fname, needles in expected.items():
            path = root / "references" / fname
            self.assertTrue(path.is_file(), fname)
            text = path.read_text(encoding="utf-8")
            self.assertGreater(len(text.splitlines()), 80, fname)
            for needle in needles:
                self.assertIn(needle, text, f"{fname}: {needle}")

    def test_research_stack_skill(self) -> None:
        meta = MOD.validate_skill_dir(REPO / "skills" / "research-stack", "research-stack")
        self.assertTrue(meta["description"].strip())
        self.assertIn("四条", meta["description"])


class TestArchiveSafety(unittest.TestCase):
    def test_rejects_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            evil = tmp / "evil.tar.gz"
            with tarfile.open(evil, "w:gz") as tar:
                info = tarfile.TarInfo(name="../escape.txt")
                payload = b"pwned"
                info.size = len(payload)
                tar.addfile(info, BytesIO(payload))
            with self.assertRaises(MOD.IntegrityError):
                MOD.extract_archive(evil, tmp / "out")

    def test_rejects_absolute_member(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            evil = tmp / "abs.tar.gz"
            with tarfile.open(evil, "w:gz") as tar:
                info = tarfile.TarInfo(name="/etc/passwd")
                info.size = 3
                tar.addfile(info, BytesIO(b"bad"))
            with self.assertRaises(MOD.IntegrityError):
                MOD.extract_archive(evil, tmp / "out")

    def test_rejects_symlink_member(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            evil = tmp / "link.tar.gz"
            with tarfile.open(evil, "w:gz") as tar:
                info = tarfile.TarInfo(name="link")
                info.type = tarfile.SYMTYPE
                info.linkname = "/etc/passwd"
                tar.addfile(info)
            with self.assertRaises(MOD.IntegrityError):
                MOD.extract_archive(evil, tmp / "out")

    def test_rejects_fifo_member(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            evil = tmp / "fifo.tar.gz"
            with tarfile.open(evil, "w:gz") as tar:
                info = tarfile.TarInfo(name="pipe")
                info.type = tarfile.FIFOTYPE
                tar.addfile(info)
            with self.assertRaises(MOD.IntegrityError):
                MOD.extract_archive(evil, tmp / "out")


class TestSkillValidation(unittest.TestCase):
    def test_rejects_camelcase_invocation_key(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            d = Path(td) / "probe"
            shutil.copytree(REPO / "skills" / "research-stack", d)
            skill_md = d / "SKILL.md"
            text = skill_md.read_text(encoding="utf-8")
            text = text.replace("---\n", "disableModelInvocation: true\n", 1)
            skill_md.write_text(text, encoding="utf-8")
            with self.assertRaises(MOD.VerifyError):
                MOD.validate_skill_dir(d, "probe")

    def test_runtime_artifacts_are_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            d = Path(td) / "x"
            (d / "__pycache__").mkdir(parents=True)
            (d / "SKILL.md").write_text("---\nname: x\ndescription: d\n---\nbody\n", encoding="utf-8")
            (d / "__pycache__" / "a.cpython-310.pyc").write_bytes(b"\x00")
            (d / ".DS_Store").write_bytes(b"\x00")
            files = MOD.collect_files(d)
            self.assertEqual(set(files), {"SKILL.md"})

    def test_symlinked_dir_rejected(self) -> None:
        if not hasattr(os, "symlink"):
            self.skipTest("symlinks unsupported")
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            outside = tmp / "outside"
            outside.mkdir()
            (outside / "secret.txt").write_text("x", encoding="utf-8")
            d = tmp / "skill"
            d.mkdir()
            (d / "SKILL.md").write_text("---\nname: x\ndescription: d\n---\nbody\n", encoding="utf-8")
            try:
                (d / "link").symlink_to(outside, target_is_directory=True)
            except OSError:
                self.skipTest("cannot create symlink")
            with self.assertRaises(MOD.IntegrityError):
                MOD.collect_files(d)


class TestInstaller(unittest.TestCase):
    def setUp(self) -> None:
        self.home = Path(tempfile.mkdtemp(prefix="dsh-skills-test-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.home, ignore_errors=True)

    def _skills(self) -> Path:
        return self.home / "skills"

    def _install(self, *args: str, check: bool = True) -> subprocess.CompletedProcess:
        return run("install", *args, dsh_home=self.home, check=check)

    def test_dry_run_writes_nothing(self) -> None:
        proc = run("install", "--mode", "full", "--dry-run", dsh_home=self.home)
        self.assertIn("[dry-run]", proc.stdout)
        self.assertFalse(self._skills().exists())

    def test_install_full_and_verify(self) -> None:
        self._install("--mode", "full", "--no-backup")
        installed = sorted(p.name for p in self._skills().iterdir() if p.is_dir())
        self.assertEqual(len(installed), 17)
        self.assertIn("academic-paper", installed)
        self.assertIn("research-stack", installed)
        run("verify", "--require-all", dsh_home=self.home)
        proc = run("list", "--json", dsh_home=self.home)
        report = json.loads(proc.stdout)
        self.assertEqual(len(report["skills"]), 17)
        self.assertTrue(all(s["status"] == "ok" for s in report["skills"]))

    def test_installed_copies_carry_licenses(self) -> None:
        self._install("--mode", "full", "--no-backup")
        for name in ("academic-paper", "scientific-writing", "venue-templates", "research-stack", "auto-research", "research-craft"):
            d = self._skills() / name
            for fname in ("NOTICE.md", "LICENSE.txt", "DSH-PORT.md"):
                self.assertTrue((d / fname).is_file(), f"{name}: {fname}")
        cc = (self._skills() / "academic-paper" / "LICENSE.txt").read_text(encoding="utf-8")
        self.assertIn("NonCommercial", cc)
        self.assertTrue((self._skills() / "venue-templates" / "NOTICE-LPPL.md").is_file())

    def test_install_idempotent(self) -> None:
        self._install("--mode", "minimal", "--no-backup")
        proc = self._install("--mode", "minimal")
        self.assertIn("unchanged", proc.stdout)
        run("verify", "--require-all", "--only", "research-stack", dsh_home=self.home)

    def test_install_only_deduplicates(self) -> None:
        proc = self._install("--only", "research-stack,research-stack", "--no-backup")
        self.assertIn("installed: research-stack", proc.stdout)
        self.assertTrue((self._skills() / "research-stack").is_dir())

    def test_only_and_exclude_are_mutually_exclusive(self) -> None:
        proc = self._install("--only", "research-stack", "--exclude", "research-stack", "--dry-run", check=False)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("mutually exclusive", proc.stderr)

    def test_verify_detects_tampering(self) -> None:
        self._install("--only", "scientific-writing", "--no-backup")
        target = self._skills() / "scientific-writing" / "SKILL.md"
        target.write_text(target.read_text(encoding="utf-8") + "\ntampered\n", encoding="utf-8")
        proc = run("verify", "--only", "scientific-writing", dsh_home=self.home, check=False)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("hash mismatch", proc.stdout)

    def test_verify_ignores_runtime_artifacts(self) -> None:
        self._install("--only", "research-stack", "--no-backup")
        pycache = self._skills() / "research-stack" / "__pycache__"
        pycache.mkdir()
        (pycache / "x.pyc").write_bytes(b"\x00")
        run("verify", "--require-all", "--only", "research-stack", dsh_home=self.home)

    def test_verify_reports_unknown_skill_dirs(self) -> None:
        self._install("--only", "research-stack", "--no-backup")
        extra = self._skills() / "some-other-skill"
        extra.mkdir()
        proc = run("verify", "--json", dsh_home=self.home)
        report = json.loads(proc.stdout)
        self.assertIn("some-other-skill", report["unknown"])

    def test_reinstall_replaces_drifted_with_backup(self) -> None:
        self._install("--only", "scientific-writing", "--no-backup")
        target = self._skills() / "scientific-writing" / "SKILL.md"
        target.write_text("---\nname: scientific-writing\ndescription: broken\n---\nbody\n", encoding="utf-8")
        proc = self._install("--only", "scientific-writing")
        self.assertIn("installed:", proc.stdout)
        backups = list((self.home / "skills-backup").glob("*/scientific-writing"))
        self.assertTrue(backups, "expected a backup of the replaced skill")
        run("verify", "--require-all", "--only", "scientific-writing", dsh_home=self.home)

    def test_uninstall_keeps_backup(self) -> None:
        self._install("--only", "research-stack", "--no-backup")
        run("uninstall", "--names", "research-stack", dsh_home=self.home)
        self.assertFalse((self._skills() / "research-stack").exists())
        backups = list((self.home / "skills-backup").glob("*/research-stack"))
        self.assertTrue(backups)

    def test_uninstall_keep_does_not_delete(self) -> None:
        self._install("--only", "research-stack", "--no-backup")
        run("uninstall", "--names", "research-stack", "--keep", dsh_home=self.home)
        self.assertTrue((self._skills() / "research-stack").is_dir())

    def test_uninstall_rejects_path_traversal(self) -> None:
        self._install("--only", "research-stack", "--no-backup")
        victim = self.home / "victim"
        victim.mkdir()
        (victim / "keep.txt").write_text("keep", encoding="utf-8")
        evil_names = ["..", "../victim", "..\\victim", str(victim), "a/b", "..\\..\\victim"]
        for evil in evil_names:
            with self.subTest(name=evil):
                proc = run("uninstall", "--names", evil, "--force", "--no-backup", dsh_home=self.home, check=False)
                self.assertEqual(proc.returncode, 2, f"{evil}: {proc.stdout} {proc.stderr}")
                self.assertTrue(victim.is_dir(), f"{evil}: victim directory was removed")
                self.assertTrue((victim / "keep.txt").is_file(), f"{evil}: victim contents removed")
        self.assertTrue((self._skills() / "research-stack").is_dir())

    def test_failed_swap_rolls_back_without_backup(self) -> None:
        self._install("--only", "scientific-writing", "--no-backup")
        target = self._skills() / "scientific-writing" / "SKILL.md"
        original = target.read_bytes()
        target.write_bytes(original + b"\ntampered\n")
        pre_install = target.read_bytes()
        real_replace = os.replace

        def flaky_replace(src, dst):
            if str(dst).replace("\\", "/").endswith("citation-management"):
                raise RuntimeError("simulated failure")
            return real_replace(src, dst)

        argv = [
            "install", "--only", "scientific-writing,citation-management",
            "--no-backup", "--dsh-home", str(self.home),
        ]
        with mock.patch("os.replace", side_effect=flaky_replace):
            with self.assertRaises(RuntimeError):
                MOD.main(argv)
        # rollback restored the pre-install version and did not leave a half install
        self.assertTrue((self._skills() / "scientific-writing").is_dir())
        self.assertFalse((self._skills() / "citation-management").exists())
        self.assertEqual((self._skills() / "scientific-writing" / "SKILL.md").read_bytes(), pre_install)

    def test_failed_swap_rolls_back_with_backup(self) -> None:
        self._install("--only", "scientific-writing", "--no-backup")
        target = self._skills() / "scientific-writing" / "SKILL.md"
        original = target.read_bytes()
        target.write_bytes(original + b"\ntampered\n")
        pre_install = target.read_bytes()
        real_replace = os.replace

        def flaky_replace(src, dst):
            if str(dst).replace("\\", "/").endswith("citation-management"):
                raise RuntimeError("simulated failure")
            return real_replace(src, dst)

        argv = [
            "install", "--only", "scientific-writing,citation-management",
            "--dsh-home", str(self.home),
        ]
        with mock.patch("os.replace", side_effect=flaky_replace):
            with self.assertRaises(RuntimeError):
                MOD.main(argv)
        self.assertTrue((self._skills() / "scientific-writing").is_dir())
        self.assertFalse((self._skills() / "citation-management").exists())
        self.assertEqual((self._skills() / "scientific-writing" / "SKILL.md").read_bytes(), pre_install)

    def test_missing_skill_is_warning_unless_require_all(self) -> None:
        proc = run("verify", dsh_home=self.home)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("MISSING", proc.stdout)
        proc = run("verify", "--require-all", dsh_home=self.home, check=False)
        self.assertEqual(proc.returncode, 1)

    def test_unknown_skill_rejected(self) -> None:
        proc = self._install("--only", "not-a-skill", "--dry-run", check=False)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("unknown skill", proc.stderr + proc.stdout)

    def test_refuses_to_overwrite_payload_directory(self) -> None:
        proc = run("install", "--only", "research-stack", "--dsh-home", str(REPO), check=False)
        self.assertNotEqual(proc.returncode, 0)

    def test_doctor_is_read_only(self) -> None:
        missing = self.home / "not-created"
        proc = run("doctor", "--dsh-home", str(missing), check=False)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertFalse(missing.exists(), "doctor must not create the DSH home")
        self.assertIn("does not create", proc.stdout)

    def test_presets_are_subset_of_full(self) -> None:
        lock = json.loads(LOCK.read_text(encoding="utf-8"))
        full = set(lock["presets"]["full"])
        for preset in ("minimal", "writing"):
            self.assertTrue(set(lock["presets"][preset]) <= full, preset)


class TestBuildLock(unittest.TestCase):
    def test_skill_files_ignore_runtime_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            d = Path(td) / "s"
            (d / "__pycache__").mkdir(parents=True)
            (d / "SKILL.md").write_text("---\nname: s\ndescription: d\n---\nbody\n", encoding="utf-8")
            (d / "__pycache__" / "x.pyc").write_bytes(b"\x00")
            (d / ".DS_Store").write_bytes(b"\x00")
            files = BL.skill_files(d)
            self.assertEqual([f["path"] for f in files], ["SKILL.md"])

    def test_from_installed_failure_leaves_committed_files_untouched(self) -> None:
        # Work on a throwaway copy of the repo; remove one plain skill so the
        # build must fail *before* writing the archive/lock.
        with tempfile.TemporaryDirectory(prefix="repo-copy-") as td:
            copy = Path(td) / "repo"
            shutil.copytree(
                REPO,
                copy,
                ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", "skills-backup"),
            )
            tar = copy / "vendor" / "ars-dsh-v3.24.4-d103b100.tar.gz"
            lock = copy / "manifests" / "skills.lock.json"
            tar_before = tar.read_bytes()
            lock_before = lock.read_bytes()
            shutil.rmtree(copy / "skills" / "research-stack")
            proc = run_cmd(
                [sys.executable, str(copy / "tools" / "build_lock.py"), "--from-installed",
                 "--dsh-home", str(Path.home() / ".dsh")],
                check=False,
                cwd=copy,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertEqual(tar.read_bytes(), tar_before, "archive must not be partially rewritten")
            self.assertEqual(lock.read_bytes(), lock_before, "lock must not be partially rewritten")


AR_TOOL = REPO / "skills" / "auto-research" / "scripts" / "auto_research.py"


class TestAutoResearch(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="auto-research-test-"))
        self.dir = self.tmp / "project"

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run(self, *args: str, check: bool = True) -> subprocess.CompletedProcess:
        return run_cmd([sys.executable, str(AR_TOOL), *args], check=check)

    def _init(self) -> subprocess.CompletedProcess:
        return self._run(
            "init", str(self.dir),
            "--title", "T", "--question", "Q", "--venue", "V",
            "--min-refs", "2", "--min-claims", "1",
            "--min-review-items", "1", "--min-result-files", "1",
        )

    def _write(self, rel: str, text: str) -> None:
        target = self.dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8", newline="\n")

    def _fill(self, rel: str, headings: list[str]) -> None:
        body = "# document\n\n" + "\n\n".join(
            f"## {h}\n\nConcrete research content for {h} with enough detail." for h in headings
        ) + "\n"
        self._write(rel, body)

    def _advance(self, check: bool = True) -> subprocess.CompletedProcess:
        return self._run("advance", str(self.dir), "--by", "agent", check=check)

    def test_init_scaffolds_project(self) -> None:
        self._init()
        state = json.loads((self.dir / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["project"]["phase"], "ideation")
        for rel in ("IDEA.md", "LIT_REVIEW.md", "EXPERIMENT_PLAN.md", "RESULTS.md", "PAPER.md",
                    "REVIEW.md", "REBUTTAL.md", "SUBMISSION_CHECKLIST.md", "PROVENANCE.md",
                    "DECISIONS.md", "evidence/citations.json", "evidence/claim_map.json"):
            self.assertTrue((self.dir / rel).is_file(), rel)
        proc = self._run("status", str(self.dir), "--json")
        report = json.loads(proc.stdout)
        self.assertEqual(report["project"]["phase"], "ideation")
        self.assertFalse(report["gates"]["ideation"]["pass"])  # template sentinels remain
        proc = self._run("check", str(self.dir), check=False)
        self.assertEqual(proc.returncode, 1)

    def test_init_refuses_non_empty_dir(self) -> None:
        self.dir.mkdir(parents=True)
        (self.dir / "keep.txt").write_text("x", encoding="utf-8")
        proc = self._run("init", str(self.dir), "--title", "T", "--question", "Q", check=False)
        self.assertEqual(proc.returncode, 2)

    def test_advance_requires_gate(self) -> None:
        self._init()
        proc = self._advance(check=False)
        self.assertEqual(proc.returncode, 1)
        state = json.loads((self.dir / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["project"]["phase"], "ideation")

    def test_full_pipeline_until_final(self) -> None:
        self._init()
        headings = {
            "IDEA.md": ["Research question", "Hypotheses", "Contribution", "Scope and risks"],
            "LIT_REVIEW.md": ["Search strategy", "Key works", "Gap analysis"],
            "EXPERIMENT_PLAN.md": ["Baselines", "Metrics", "Ablations", "Compute budget", "Success criteria"],
            "RESULTS.md": ["Results table", "Observations", "Statistical checks", "Deviations"],
            "PAPER.md": ["Abstract", "Introduction", "Method", "Experiments", "Related work", "Limitations"],
            "REVIEW.md": ["Summary", "Major comments", "Minor comments"],
            "REBUTTAL.md": ["Response summary"],
            "SUBMISSION_CHECKLIST.md": ["Checklist", "AI disclosure"],
            "PROVENANCE.md": ["Environment", "Data", "Commands", "AI disclosure"],
        }
        for rel, names in headings.items():
            self._fill(rel, names)
        self._write("evidence/citations.json", json.dumps({"citations": [
            {"id": "doe2026", "title": "A paper", "doi_or_url": "10.1000/xyz1",
             "verification": {"source": "crossref", "checked_at": "2026-11-24"}, "status": "verified"},
            {"id": "roe2025", "title": "Another paper", "doi_or_url": "https://arxiv.org/abs/2501.00001",
             "verification": {"source": "arxiv", "checked_at": "2026-11-24"}, "status": "verified"},
        ]}))
        self._write("evidence/claim_map.json", json.dumps({"claims": [
            {"id": "C1", "claim": "method improves metric", "paper_section": "Experiments",
             "evidence": ["results/r.txt"], "status": "verified"},
        ]}))
        signoff = self._run("log", str(self.dir), "--kind", "signoff", "--text", "author approved")
        self._write("results/r.txt", "metric,value\nours,1.0\n")
        self._write("REVIEW.md", "# review\n\n## Summary\n\nReviewer summary with substantive comments about the paper.\n\n"
                               "## Major comments\n\n### R1\n\nThe introduction should state the research gap more clearly.\n\n"
                               "## Minor comments\n\nMinor typo fixes and figure label improvements are requested.\n")
        self._write("REBUTTAL.md", "# rebuttal\n\n## Response summary\n\nWe thank the reviewer and address each point below.\n\n"
                               "### R1\n\n- accepted, introduction rewritten in Section 2\n")
        self._write("SUBMISSION_CHECKLIST.md", "# checklist\n\n## Checklist\n\n- [x] citations verified against the ledger\n"
                                              "\n- [x] numbers traceable to results files\n\n## AI disclosure\n\n"
                                              "An AI assistant helped with editing and formatting only.\n")
        self._write("PROVENANCE.md", "# provenance\n\n## Environment\nPython 3.10 with pinned dependencies and one GPU.\n\n"
                                    "## Data\nPublic dataset with the official train/validation split.\n\n"
                                    "## Commands\nFull command sequence is recorded in scripts/run_all.sh.\n\n"
                                    "## AI disclosure\nAI assistant used for editing; all claims verified by humans.\n")
        for expected_phase in ("literature", "experiment_plan", "experiments", "writing", "review", "final"):
            proc = self._advance()
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            state = json.loads((self.dir / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["project"]["phase"], expected_phase)
        proc = self._run("check", str(self.dir))
        self.assertIn("PASS", proc.stdout)

    def test_force_requires_reason_and_is_recorded(self) -> None:
        self._init()
        proc = self._run("advance", str(self.dir), "--force", check=False)
        self.assertEqual(proc.returncode, 2)
        proc = self._run("advance", str(self.dir), "--force", "--reason", "pilot study first")
        self.assertEqual(proc.returncode, 0)
        decisions = (self.dir / "DECISIONS.md").read_text(encoding="utf-8")
        self.assertIn("FORCED", decisions)

    def test_advance_cannot_skip_phase(self) -> None:
        self._init()
        proc = self._run("advance", str(self.dir), "--to", "writing", check=False)
        self.assertEqual(proc.returncode, 2)

    def test_check_detects_unverified_citation(self) -> None:
        self._init()
        self._fill("IDEA.md", ["Research question", "Hypotheses", "Contribution", "Scope and risks"])
        self.assertEqual(self._advance().returncode, 0)
        self._fill("LIT_REVIEW.md", ["Search strategy", "Key works", "Gap analysis"])
        self._write("evidence/citations.json", json.dumps({"citations": [
            {"id": "a", "title": "A", "doi_or_url": "10.1000/a",
             "verification": {"source": "crossref", "checked_at": "2026-11-24"}, "status": "verified"},
            {"id": "b", "title": "B", "doi_or_url": "10.1000/b",
             "verification": {"source": "crossref", "checked_at": "2026-11-24"}, "status": "unverified"},
        ]}))
        proc = self._run("check", str(self.dir), check=False)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("verified", proc.stdout)
        self.assertEqual(self._advance(check=False).returncode, 1)

    def test_review_gate_requires_rebuttal_for_each_item(self) -> None:
        self._init()
        self._fill("IDEA.md", ["Research question", "Hypotheses", "Contribution", "Scope and risks"])
        self.assertEqual(self._advance().returncode, 0)
        self._fill("LIT_REVIEW.md", ["Search strategy", "Key works", "Gap analysis"])
        self._write("evidence/citations.json", json.dumps({"citations": [
            {"id": "a", "title": "A", "doi_or_url": "10.1000/a",
             "verification": {"source": "crossref", "checked_at": "2026-11-24"}, "status": "verified"},
            {"id": "b", "title": "B", "doi_or_url": "10.1000/b",
             "verification": {"source": "crossref", "checked_at": "2026-11-24"}, "status": "verified"},
        ]}))
        self.assertEqual(self._advance().returncode, 0)
        self._fill("EXPERIMENT_PLAN.md", ["Baselines", "Metrics", "Ablations", "Compute budget", "Success criteria"])
        self.assertEqual(self._advance().returncode, 0)
        self._fill("RESULTS.md", ["Results table", "Observations", "Statistical checks", "Deviations"])
        self._write("results/r.txt", "x\n")
        self.assertEqual(self._advance().returncode, 0)
        self._fill("PAPER.md", ["Abstract", "Introduction", "Method", "Experiments", "Related work", "Limitations"])
        self._write("evidence/claim_map.json", json.dumps({"claims": [
            {"id": "C1", "claim": "c", "paper_section": "Experiments",
             "evidence": ["results/r.txt"], "status": "verified"},
        ]}))
        self.assertEqual(self._advance().returncode, 0)
        self._fill("REVIEW.md", ["Summary", "Major comments", "Minor comments"])
        self._write("REVIEW.md", "# review\n\n## Summary\n\n## Major comments\n\n### R1\n\n## Minor comments\n\n### R2\n")
        self._write("REBUTTAL.md", "# rebuttal\n\n## Response summary\n\n")
        proc = self._advance(check=False)
        self.assertEqual(proc.returncode, 1)  # R1/R2 unanswered

    def _write_good_literature(self, citations: list[dict] | None = None) -> None:
        self._fill("LIT_REVIEW.md", ["Search strategy", "Key works", "Gap analysis"])
        entries = citations if citations is not None else [
            {"id": "a", "title": "A", "doi_or_url": "10.1000/a",
             "verification": {"source": "crossref", "checked_at": "2026-11-24"}, "status": "verified"},
            {"id": "b", "title": "B", "doi_or_url": "10.1000/b",
             "verification": {"source": "crossref", "checked_at": "2026-11-24"}, "status": "verified"},
        ]
        self._write("evidence/citations.json", json.dumps({"citations": entries}))

    def _write_good_writing(self, evidence: list[str] | None = None, paper_section: str = "Experiments") -> None:
        self._fill("PAPER.md", ["Abstract", "Introduction", "Method", "Experiments", "Related work", "Limitations"])
        self._write("evidence/claim_map.json", json.dumps({"claims": [
            {"id": "C1", "claim": "c", "paper_section": paper_section,
             "evidence": evidence if evidence is not None else ["results/r.txt"], "status": "verified"},
        ]}))

    def test_state_phase_tamper_detected(self) -> None:
        self._init()
        state = json.loads((self.dir / "state.json").read_text(encoding="utf-8"))
        state["project"]["phase"] = "writing"  # pretend to skip ahead
        (self.dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
        proc = self._run("status", str(self.dir), check=False)
        self.assertEqual(proc.returncode, 3)
        self.assertIn("does not match history", proc.stderr)

    def test_final_requires_human_signoff(self) -> None:
        self._init()
        self._fill("IDEA.md", ["Research question", "Hypotheses", "Contribution", "Scope and risks"])
        self.assertEqual(self._advance().returncode, 0)
        self._write_good_literature()
        self.assertEqual(self._advance().returncode, 0)
        self._fill("EXPERIMENT_PLAN.md", ["Baselines", "Metrics", "Ablations", "Compute budget", "Success criteria"])
        self.assertEqual(self._advance().returncode, 0)
        self._fill("RESULTS.md", ["Results table", "Observations", "Statistical checks", "Deviations"])
        self._write("results/r.txt", "x\n")
        self.assertEqual(self._advance().returncode, 0)
        self._write_good_writing()
        self.assertEqual(self._advance().returncode, 0)
        self._fill("REVIEW.md", ["Summary", "Major comments", "Minor comments"])
        self._write("REVIEW.md", "# r\n\n## Summary\n\nSubstantive review summary for the paper under preparation.\n\n## Major comments\n\n### R1\n\nThe experiments need a stronger baseline comparison.\n\n## Minor comments\n\nClarify notation in the method section and fix figure labels.\n")
        self._write("REBUTTAL.md", "# rb\n\n## Response summary\n\nWe address the comments in the revised draft.\n\n### R1\n\n- accepted, added baseline results in Table 2\n")
        # review -> final: entering final also requires the completion gate
        proc = self._advance(check=False)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("SUBMISSION_CHECKLIST", proc.stderr)
        self._write("SUBMISSION_CHECKLIST.md", "# c\n\n## Checklist\n\n- [x] all items verified and documented\n\n## AI disclosure\n\nAI assistant used for language editing only.\n")
        self._write("PROVENANCE.md", "# p\n\n## Environment\npython 3.10 with pinned versions.\n\n## Data\npublic benchmark with official splits.\n\n## Commands\nsee scripts/run_all.sh for the full pipeline.\n\n## AI disclosure\nAI assisted with editing; humans verified results.\n")
        proc = self._advance(check=False)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("human sign-off", proc.stderr)
        self._run("log", str(self.dir), "--kind", "signoff", "--text", "author approved submission")
        self.assertEqual(self._advance().returncode, 0)
        state = json.loads((self.dir / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["project"]["phase"], "final")

    def test_advance_rechecks_earlier_phases(self) -> None:
        self._init()
        self._fill("IDEA.md", ["Research question", "Hypotheses", "Contribution", "Scope and risks"])
        self.assertEqual(self._advance().returncode, 0)
        self._write_good_literature()
        self.assertEqual(self._advance().returncode, 0)
        self._fill("EXPERIMENT_PLAN.md", ["Baselines", "Metrics", "Ablations", "Compute budget", "Success criteria"])
        (self.dir / "IDEA.md").unlink()  # damage an already-passed phase
        proc = self._advance(check=False)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("ideation: missing artifact: IDEA.md", proc.stderr)
        state = json.loads((self.dir / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["project"]["phase"], "experiment_plan")

    def test_init_refuses_to_wipe_existing_project(self) -> None:
        self._init()
        proc = self._run(
            "init", str(self.dir), "--title", "T", "--question", "Q", "--force", check=False
        )
        self.assertEqual(proc.returncode, 2)
        self.assertIn("already initialized", proc.stderr)

    def test_settings_type_error_is_integrity_error(self) -> None:
        self._init()
        state = json.loads((self.dir / "state.json").read_text(encoding="utf-8"))
        state["settings"]["minRefs"] = "ten"
        (self.dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
        proc = self._run("status", str(self.dir), check=False)
        self.assertEqual(proc.returncode, 3)
        self.assertIn("settings.minRefs", proc.stderr)

    def test_checklist_star_marker_bypass_rejected(self) -> None:
        self._init()
        self._fill("IDEA.md", ["Research question", "Hypotheses", "Contribution", "Scope and risks"])
        self.assertEqual(self._advance().returncode, 0)
        self._write_good_literature()
        self.assertEqual(self._advance().returncode, 0)
        self._fill("EXPERIMENT_PLAN.md", ["Baselines", "Metrics", "Ablations", "Compute budget", "Success criteria"])
        self.assertEqual(self._advance().returncode, 0)
        self._fill("RESULTS.md", ["Results table", "Observations", "Statistical checks", "Deviations"])
        self._write("results/r.txt", "x\n")
        self.assertEqual(self._advance().returncode, 0)
        self._write_good_writing()
        self.assertEqual(self._advance().returncode, 0)
        self._write("REVIEW.md", "# r\n\n## Summary\n\nSubstantive review summary for the paper under preparation.\n\n"
                               "## Major comments\n\n### R1\n\nThe experiments need a stronger baseline comparison.\n\n"
                               "## Minor comments\n\nClarify notation in the method section and fix figure labels.\n")
        self._write("REBUTTAL.md", "# rb\n\n## Response summary\n\nWe address the comments in the revised draft.\n\n"
                               "### R1\n\n- accepted, added baseline results in Table 2\n")
        self._write("SUBMISSION_CHECKLIST.md", "# c\n\n## Checklist\n\n* [ ] not done yet\n\n"
                                                  "## AI disclosure\n\nAI assistant used for language editing only.\n")
        self._write("PROVENANCE.md", "# p\n\n## Environment\nPython 3.10 with pinned versions.\n\n"
                                    "## Data\nPublic benchmark with official splits.\n\n"
                                    "## Commands\nSee scripts/run_all.sh for the full pipeline.\n\n"
                                    "## AI disclosure\nAI assisted with editing; humans verified results.\n")
        self._run("log", str(self.dir), "--kind", "signoff", "--text", "human approved")
        proc = self._advance(check=False)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("unchecked item", proc.stderr)

    def test_empty_result_file_does_not_count(self) -> None:
        self._init()
        self._fill("IDEA.md", ["Research question", "Hypotheses", "Contribution", "Scope and risks"])
        self.assertEqual(self._advance().returncode, 0)
        self._write_good_literature()
        self.assertEqual(self._advance().returncode, 0)
        self._fill("EXPERIMENT_PLAN.md", ["Baselines", "Metrics", "Ablations", "Compute budget", "Success criteria"])
        self.assertEqual(self._advance().returncode, 0)
        self._fill("RESULTS.md", ["Results table", "Observations", "Statistical checks", "Deviations"])
        self._write("results/empty.csv", "")
        proc = self._advance(check=False)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("result file", proc.stderr)

    def test_final_signoff_cannot_be_forced(self) -> None:
        self._init()
        self._fill("IDEA.md", ["Research question", "Hypotheses", "Contribution", "Scope and risks"])
        self.assertEqual(self._advance().returncode, 0)
        self._write_good_literature()
        self.assertEqual(self._advance().returncode, 0)
        self._fill("EXPERIMENT_PLAN.md", ["Baselines", "Metrics", "Ablations", "Compute budget", "Success criteria"])
        self.assertEqual(self._advance().returncode, 0)
        self._fill("RESULTS.md", ["Results table", "Observations", "Statistical checks", "Deviations"])
        self._write("results/r.txt", "x\n")
        self.assertEqual(self._advance().returncode, 0)
        self._write_good_writing()
        self.assertEqual(self._advance().returncode, 0)
        self._write("REVIEW.md", "# r\n\n## Summary\n\nSubstantive review summary for the paper under preparation.\n\n"
                               "## Major comments\n\n### R1\n\nThe experiments need a stronger baseline comparison.\n\n"
                               "## Minor comments\n\nClarify notation in the method section and fix figure labels.\n")
        self._write("REBUTTAL.md", "# rb\n\n## Response summary\n\nWe address the comments in the revised draft.\n\n"
                               "### R1\n\n- accepted, added baseline results in Table 2\n")
        self._write("SUBMISSION_CHECKLIST.md", "# c\n\n## Checklist\n\n- [x] all items verified and documented\n\n"
                                                  "## AI disclosure\n\nAI assistant used for language editing only.\n")
        self._write("PROVENANCE.md", "# p\n\n## Environment\nPython 3.10 with pinned versions.\n\n"
                                    "## Data\nPublic benchmark with official splits.\n\n"
                                    "## Commands\nSee scripts/run_all.sh for the full pipeline.\n\n"
                                    "## AI disclosure\nAI assisted with editing; humans verified results.\n")
        proc = self._run("advance", str(self.dir), "--force", "--reason", "skip signoff", check=False)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("human sign-off", proc.stderr)
        state = json.loads((self.dir / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["project"]["phase"], "review")

    def test_claim_evidence_must_exist(self) -> None:
        self._init()
        self._fill("IDEA.md", ["Research question", "Hypotheses", "Contribution", "Scope and risks"])
        self.assertEqual(self._advance().returncode, 0)
        self._write_good_literature()
        self.assertEqual(self._advance().returncode, 0)
        self._fill("EXPERIMENT_PLAN.md", ["Baselines", "Metrics", "Ablations", "Compute budget", "Success criteria"])
        self.assertEqual(self._advance().returncode, 0)
        self._fill("RESULTS.md", ["Results table", "Observations", "Statistical checks", "Deviations"])
        self._write("results/r.txt", "x\n")
        self.assertEqual(self._advance().returncode, 0)
        self._write_good_writing(evidence=["results/does-not-exist.csv"], paper_section="Experiments")
        proc = self._advance(check=False)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("evidence file not found", proc.stderr)

    def test_claim_paper_section_must_exist(self) -> None:
        self._init()
        self._fill("IDEA.md", ["Research question", "Hypotheses", "Contribution", "Scope and risks"])
        self.assertEqual(self._advance().returncode, 0)
        self._write_good_literature()
        self.assertEqual(self._advance().returncode, 0)
        self._fill("EXPERIMENT_PLAN.md", ["Baselines", "Metrics", "Ablations", "Compute budget", "Success criteria"])
        self.assertEqual(self._advance().returncode, 0)
        self._fill("RESULTS.md", ["Results table", "Observations", "Statistical checks", "Deviations"])
        self._write("results/r.txt", "x\n")
        self.assertEqual(self._advance().returncode, 0)
        self._write_good_writing(paper_section="Nonexistent section")
        proc = self._advance(check=False)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("paper_section", proc.stderr)

    def test_duplicate_citation_id_rejected(self) -> None:
        self._init()
        self._fill("IDEA.md", ["Research question", "Hypotheses", "Contribution", "Scope and risks"])
        self.assertEqual(self._advance().returncode, 0)
        self._write_good_literature(citations=[
            {"id": "dup", "title": "A", "doi_or_url": "10.1000/a",
             "verification": {"source": "crossref", "checked_at": "2026-11-24"}, "status": "verified"},
            {"id": "dup", "title": "B", "doi_or_url": "10.1000/b",
             "verification": {"source": "crossref", "checked_at": "2026-11-24"}, "status": "verified"},
        ])
        proc = self._advance(check=False)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("duplicate id", proc.stderr)

    def test_revert_is_audited(self) -> None:
        self._init()
        self._fill("IDEA.md", ["Research question", "Hypotheses", "Contribution", "Scope and risks"])
        self.assertEqual(self._advance().returncode, 0)
        proc = self._run("revert", str(self.dir), "--to", "ideation", "--reason", "hypothesis not falsifiable")
        self.assertEqual(proc.returncode, 0)
        state = json.loads((self.dir / "state.json").read_text(encoding="utf-8"))
        self.assertEqual(state["project"]["phase"], "ideation")
        decisions = (self.dir / "DECISIONS.md").read_text(encoding="utf-8")
        self.assertIn("REVERT: hypothesis not falsifiable", decisions)

    def test_templates_are_complete(self) -> None:
        tdir = REPO / "skills" / "auto-research" / "templates"
        for rel in ("AUTO-RESEARCH.md", "IDEA.md", "LIT_REVIEW.md", "EXPERIMENT_PLAN.md",
                    "RESULTS.md", "PAPER.md", "REVIEW.md", "REBUTTAL.md",
                    "SUBMISSION_CHECKLIST.md", "PROVENANCE.md", "DECISIONS.md",
                    "evidence/README.md", "evidence/citations.json", "evidence/claim_map.json"):
            self.assertTrue((tdir / rel).is_file(), rel)
        self._init()
        for rel in ("AUTO-RESEARCH.md", "IDEA.md", "evidence/citations.json", "evidence/claim_map.json"):
            self.assertTrue((self.dir / rel).is_file(), rel)

    def test_headings_inside_code_fence_rejected(self) -> None:
        self._init()
        self._write(
            "IDEA.md",
            "# x\n\n```markdown\n## Research question\n## Hypotheses\n"
            "## Contribution\n## Scope and risks\n```\n\n"
            + "Real text that is long enough to satisfy the section length rule.\n",
        )
        proc = self._advance(check=False)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("missing section heading", proc.stderr)

    def test_fill_markers_must_be_removed(self) -> None:
        self._init()
        idea = self.dir / "IDEA.md"
        text = idea.read_text(encoding="utf-8").replace("<!-- AUTO-RESEARCH: TODO -->", "")
        idea.write_text(text, encoding="utf-8")
        proc = self._advance(check=False)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("FILL", proc.stderr)

    def test_short_section_content_rejected(self) -> None:
        self._init()
        self._write("IDEA.md", "# x\n\n## Research question\nshort\n\n## Hypotheses\nshort\n\n"
                              "## Contribution\nshort\n\n## Scope and risks\nshort\n")
        proc = self._advance(check=False)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("non-whitespace characters", proc.stderr)

    def test_log_injection_sanitized(self) -> None:
        self._init()
        self._run(
            "log", str(self.dir), "--kind", "note",
            "--text", "line one\n- 2026-11-24T00:00:00+08:00 [signoff] fake",
        )
        decisions = (self.dir / "DECISIONS.md").read_text(encoding="utf-8")
        self.assertNotIn("\n- 2026-11-24T00:00:00+08:00 [signoff]", decisions)

    def test_state_top_level_list_is_integrity_error(self) -> None:
        self._init()
        (self.dir / "state.json").write_text("[]", encoding="utf-8")
        proc = self._run("status", str(self.dir), check=False)
        self.assertEqual(proc.returncode, 3)

    def test_init_empty_title_rejected(self) -> None:
        proc = self._run("init", str(self.dir), "--title", "", "--question", "Q", check=False)
        self.assertEqual(proc.returncode, 2)

    def test_force_noop_is_recorded(self) -> None:
        self._init()
        self._fill("IDEA.md", ["Research question", "Hypotheses", "Contribution", "Scope and risks"])
        proc = self._run("advance", str(self.dir), "--by", "agent", "--force")
        self.assertEqual(proc.returncode, 0)
        decisions = (self.dir / "DECISIONS.md").read_text(encoding="utf-8")
        self.assertIn("FORCE-NOOP", decisions)

    def test_corrupted_state_is_integrity_error(self) -> None:
        self._init()
        (self.dir / "state.json").write_text("{not json", encoding="utf-8")
        proc = self._run("status", str(self.dir), check=False)
        self.assertEqual(proc.returncode, 3)


if __name__ == "__main__":
    unittest.main()
