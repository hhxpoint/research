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
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CLI = REPO / "tools" / "dsh_skills.py"
LOCK = REPO / "manifests" / "skills.lock.json"


def load_module():
    spec = importlib.util.spec_from_file_location("dsh_skills", CLI)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


MOD = load_module()


def run(*args: str, dsh_home: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(CLI), *args]
    if dsh_home is not None:
        cmd += ["--dsh-home", str(dsh_home)]
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    proc = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, encoding="utf-8", env=env)
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
        self.assertEqual(len(lock["skills"]), 15)
        names = {s["name"] for s in lock["skills"]}
        self.assertIn("research-stack", names)
        self.assertIn("academic-paper", names)
        self.assertIn("autoresearch", names)
        for preset in ("minimal", "writing", "full"):
            self.assertIn(preset, lock["presets"])
            self.assertTrue(set(lock["presets"][preset]) <= names, preset)
        self.assertEqual(len(lock["presets"]["full"]), 15)
        # every source has license metadata
        for sid, source in lock["sources"].items():
            self.assertIn("license", source, sid)
            self.assertIn("repo", source, sid)
            self.assertTrue((REPO / source["licenseFile"]).is_file(), sid)
        ars = lock["sources"]["ars"]
        self.assertEqual(ars["license"], "CC-BY-NC-4.0")
        self.assertTrue((REPO / ars["archive"]).is_file())
        self.assertEqual(len(ars["archiveSha256"]), 64)

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

    def test_selftest(self) -> None:
        proc = run("selftest")
        self.assertIn("SELFTEST PASS", proc.stdout)

    def test_build_lock_check(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(REPO / "tools" / "build_lock.py"), "--check"],
            cwd=REPO,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("CHECK OK", proc.stdout)

    def test_research_stack_skill(self) -> None:
        meta = MOD.validate_skill_dir(REPO / "skills" / "research-stack", "research-stack")
        self.assertTrue(meta["description"].strip())


class TestArchiveSafety(unittest.TestCase):
    def test_rejects_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            evil = tmp / "evil.tar.gz"
            with tarfile.open(evil, "w:gz") as tar:
                info = tarfile.TarInfo(name="../escape.txt")
                payload = b"pwned"
                info.size = len(payload)
                import io

                tar.addfile(info, io.BytesIO(payload))
            with self.assertRaises(MOD.IntegrityError):
                MOD.extract_archive(evil, tmp / "out")

    def test_rejects_absolute_member(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            evil = tmp / "abs.tar.gz"
            import io

            with tarfile.open(evil, "w:gz") as tar:
                info = tarfile.TarInfo(name="/etc/passwd")
                info.size = 3
                tar.addfile(info, io.BytesIO(b"bad"))
            with self.assertRaises(MOD.IntegrityError):
                MOD.extract_archive(evil, tmp / "out")


class TestInstaller(unittest.TestCase):
    def setUp(self) -> None:
        self.home = Path(tempfile.mkdtemp(prefix="dsh-skills-test-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.home, ignore_errors=True)

    def _skills(self) -> Path:
        return self.home / "skills"

    def test_dry_run_writes_nothing(self) -> None:
        proc = run("install", "--mode", "full", "--dry-run", dsh_home=self.home)
        self.assertIn("[dry-run]", proc.stdout)
        self.assertFalse(self._skills().exists())

    def test_install_full_and_verify(self) -> None:
        run("install", "--mode", "full", "--no-backup", dsh_home=self.home)
        installed = sorted(p.name for p in self._skills().iterdir() if p.is_dir())
        self.assertEqual(len(installed), 15)
        self.assertIn("academic-paper", installed)
        self.assertIn("research-stack", installed)
        run("verify", "--require-all", dsh_home=self.home)
        proc = run("list", "--json", dsh_home=self.home)
        report = json.loads(proc.stdout)
        self.assertEqual(len(report["skills"]), 15)
        self.assertTrue(all(s["status"] == "ok" for s in report["skills"]))

    def test_install_idempotent(self) -> None:
        run("install", "--mode", "minimal", "--no-backup", dsh_home=self.home)
        proc = run("install", "--mode", "minimal", dsh_home=self.home)
        self.assertIn("unchanged", proc.stdout.replace("(skipped)", ""))
        run("verify", "--require-all", "--only", "research-stack", dsh_home=self.home)

    def test_verify_detects_tampering(self) -> None:
        run("install", "--only", "scientific-writing", "--no-backup", dsh_home=self.home)
        target = self._skills() / "scientific-writing" / "SKILL.md"
        target.write_text(target.read_text(encoding="utf-8") + "\ntampered\n", encoding="utf-8")
        proc = run("verify", "--only", "scientific-writing", dsh_home=self.home, check=False)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("hash mismatch", proc.stdout)

    def test_reinstall_replaces_drifted_with_backup(self) -> None:
        run("install", "--only", "scientific-writing", "--no-backup", dsh_home=self.home)
        target = self._skills() / "scientific-writing" / "SKILL.md"
        target.write_text("---\nname: scientific-writing\ndescription: broken\n---\nbody\n", encoding="utf-8")
        proc = run("install", "--only", "scientific-writing", dsh_home=self.home)
        self.assertIn("installed:", proc.stdout)
        backups = list((self.home / "skills-backup").glob("*/scientific-writing"))
        self.assertTrue(backups, "expected a backup of the replaced skill")
        run("verify", "--require-all", "--only", "scientific-writing", dsh_home=self.home)

    def test_uninstall_keeps_backup(self) -> None:
        run("install", "--only", "research-stack", "--no-backup", dsh_home=self.home)
        run("uninstall", "--names", "research-stack", dsh_home=self.home)
        self.assertFalse((self._skills() / "research-stack").exists())
        backups = list((self.home / "skills-backup").glob("*/research-stack"))
        self.assertTrue(backups)

    def test_uninstall_keep_does_not_delete(self) -> None:
        run("install", "--only", "research-stack", "--no-backup", dsh_home=self.home)
        run("uninstall", "--names", "research-stack", "--keep", dsh_home=self.home)
        self.assertTrue((self._skills() / "research-stack").is_dir())

    def test_missing_skill_is_warning_unless_require_all(self) -> None:
        proc = run("verify", dsh_home=self.home)
        self.assertEqual(proc.returncode, 0)
        self.assertIn("MISSING", proc.stdout)
        proc = run("verify", "--require-all", dsh_home=self.home, check=False)
        self.assertEqual(proc.returncode, 1)

    def test_unknown_skill_rejected(self) -> None:
        proc = run("install", "--only", "not-a-skill", dsh_home=self.home, check=False)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("unknown skill", proc.stderr + proc.stdout)

    def test_refuses_to_install_into_repository(self) -> None:
        proc = run("install", "--only", "research-stack", "--dsh-home", str(REPO), check=False)
        self.assertNotEqual(proc.returncode, 0)

    def test_presets_are_subset_of_full(self) -> None:
        lock = json.loads(LOCK.read_text(encoding="utf-8"))
        full = set(lock["presets"]["full"])
        for preset in ("minimal", "writing"):
            self.assertTrue(set(lock["presets"][preset]) <= full, preset)


if __name__ == "__main__":
    unittest.main()
