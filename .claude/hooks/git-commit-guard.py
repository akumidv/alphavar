#!/usr/bin/env python3
"""Thin shim → the keystone commit guard (source of truth).

This project's hook lives in the keystone submodule
(``_forge/keystone/hooks/git-commit-guard.py``). This file only forwards to it, so an
already-running session that wired the old ``.claude/hooks/`` path keeps working and the
logic stays single-sourced in keystone. New wiring points straight at the keystone path
(see ``.claude/settings.json``); this shim can be removed once no session references it.
"""
import runpy
import sys
from pathlib import Path

target = Path(__file__).resolve().parents[2] / "_forge" / "keystone" / "hooks" / "git-commit-guard.py"
if not target.exists():
    sys.exit(0)  # never block if the submodule isn't checked out
runpy.run_path(str(target), run_name="__main__")
