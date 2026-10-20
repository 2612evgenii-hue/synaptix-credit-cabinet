#!/usr/bin/env python3
"""Back up all local Git refs; ignored/uncommitted files and GitHub are excluded."""
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def main():
    out = ROOT / "artifacts/backups"
    out.mkdir(parents=True, exist_ok=True)
    name = datetime.now(timezone.utc).strftime("synaptix-%Y%m%dT%H%M%S%fZ.bundle")
    bundle = out / name
    subprocess.run(["git", "bundle", "create", str(bundle), "--all"], cwd=ROOT, check=True)
    subprocess.run(["git", "bundle", "verify", str(bundle)], cwd=ROOT, check=True)
    digest = hashlib.sha256(bundle.read_bytes()).hexdigest()
    bundle.with_suffix(".bundle.sha256").write_text(f"{digest}  {bundle.name}\n")
    print(f"Verified Git refs backup: {bundle}")
    print("Copy to independent storage. Excludes uncommitted/ignored files, DB, GitHub issues/settings.")
    print(f"Restore into a NEW directory: git clone {bundle} synaptix-restored")


if __name__ == "__main__":
    main()
