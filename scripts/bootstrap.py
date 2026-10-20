#!/usr/bin/env python3
"""Install versioned hooks in this clone only; preserve an existing custom setup."""
from pathlib import Path
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
result = subprocess.run(["git", "config", "--get", "core.hooksPath"], cwd=root, text=True, capture_output=True)
existing = result.stdout.strip()
if existing and existing != ".githooks":
    sys.exit(f"Existing core.hooksPath={existing}; integrate hooks manually, no config overwritten")
subprocess.run(["git", "config", "--local", "core.hooksPath", ".githooks"], cwd=root, check=True)
for name in ("commit-msg", "pre-commit", "pre-push"):
    path = root / ".githooks" / name
    path.chmod(path.stat().st_mode | 0o111)
print("Installed .githooks for this clone. Set your own git user.name/email; enable account 2FA.")
