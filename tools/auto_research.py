#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Convenience launcher for the auto-research state machine.

The canonical implementation ships inside the `auto-research` skill
(`skills/auto-research/scripts/auto_research.py`) so that an installed
`~/.dsh/skills/auto-research/` directory is self-contained. This launcher
exists so the repository exposes the same command under `tools/`.
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

TARGET = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "auto-research"
    / "scripts"
    / "auto_research.py"
)

if not TARGET.is_file():
    sys.stderr.write(f"auto-research implementation not found: {TARGET}\n")
    raise SystemExit(2)

if __name__ == "__main__":
    sys.argv[0] = str(TARGET)
    runpy.run_path(str(TARGET), run_name="__main__")
