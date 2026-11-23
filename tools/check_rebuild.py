#!/usr/bin/env python3
"""Compare a rebuilt lock file with the committed one, semantically.

`build_lock.py --from-installed` is expected to reproduce the committed lock
exactly. The ARS archive bytes themselves may legitimately differ between
platforms because Python links different zlib versions; that does not affect
the extracted skill bytes. This checker therefore compares:

  * every skill's packaged file list + sha256 (the real payload contract),
  * presets and source pins,
while ignoring `archiveSha256` / `archiveBytes`.

Used by CI after a clean-room rebuild.

Usage:
  python tools/check_rebuild.py --committed manifests/skills.lock.json \
      --rebuilt /tmp/repo/manifests/skills.lock.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def skill_map(lock: dict) -> dict:
    result = {}
    for skill in lock["skills"]:
        files = sorted(
            ({"path": f["path"], "sha256": f["sha256"], "bytes": f["bytes"]} for f in skill["files"]),
            key=lambda f: f["path"],
        )
        result[skill["name"]] = {"source": skill["source"], "mode": skill["mode"], "files": files}
    return result


def source_map(lock: dict) -> dict:
    result = {}
    for sid, source in lock["sources"].items():
        result[sid] = {
            key: source.get(key)
            for key in ("repo", "commit", "license", "licenseFile", "version", "note")
            if key in source
        }
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--committed", type=Path, required=True)
    ap.add_argument("--rebuilt", type=Path, required=True)
    args = ap.parse_args()
    committed = load(args.committed)
    rebuilt = load(args.rebuilt)
    problems = []
    if committed.get("schemaVersion") != rebuilt.get("schemaVersion"):
        problems.append("schemaVersion differs")
    if committed.get("presets") != rebuilt.get("presets"):
        problems.append("presets differ")
    if source_map(committed) != source_map(rebuilt):
        problems.append("source pins differ")
    old = skill_map(committed)
    new = skill_map(rebuilt)
    if set(old) != set(new):
        problems.append(f"skill set differs: {sorted(set(old) ^ set(new))}")
    for name in sorted(set(old) & set(new)):
        if old[name] != new[name]:
            old_files = {f["path"]: f["sha256"] for f in old[name]["files"]}
            new_files = {f["path"]: f["sha256"] for f in new[name]["files"]}
            diff = sorted(
                p for p in set(old_files) | set(new_files)
                if old_files.get(p) != new_files.get(p)
            )
            problems.append(f"{name}: payload differs ({diff[:5]})")
    if problems:
        print("REBUILD CHECK FAILED")
        for p in problems:
            print(" -", p)
        return 1
    print(
        "REBUILD OK: rebuilt lock matches committed payloads "
        f"({len(old)} skills; archive sha may differ across zlib versions)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
