#!/usr/bin/env python3
"""Prepare a deadline manifest; never create/push tags or a GitHub release."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys

from submission_check import readiness_errors

ROOT = Path(__file__).resolve().parents[1]


def parse_deadline(value):
    deadline = datetime.fromisoformat(value)
    if deadline.utcoffset() is None:
        raise ValueError("Deadline must include a timezone offset")
    return deadline


def valid_tag(value):
    return re.fullmatch(r"v(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)(?:-hackathon\.[1-9]\d*)?", value) is not None


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", required=True)
    parser.add_argument("--deadline", required=True)
    args = parser.parse_args()
    try:
        deadline = parse_deadline(args.deadline)
        if not valid_tag(args.tag):
            raise ValueError("Use vX.Y.Z or vX.Y.Z-hackathon.N")
        if datetime.now(timezone.utc) >= deadline:
            raise ValueError("Deadline has passed; refusing a new submission manifest")
        team = json.loads((ROOT / "config/team.json").read_text())
        if not team.get("deadline") or parse_deadline(team["deadline"]) != deadline:
            raise ValueError("Deadline must match the confirmed value in config/team.json")
        errors = readiness_errors()
        if errors:
            raise ValueError("Submission is not ready: " + "; ".join(errors))
        if git("status", "--porcelain"):
            raise ValueError("Working tree must be clean")
        if git("branch", "--show-current") != "main":
            raise ValueError("Prepare final manifest from main")
        if git("tag", "--list", args.tag):
            raise ValueError("Tag already exists locally; never move a submission tag")
        subprocess.run([sys.executable, str(ROOT / "scripts/repo_checks.py")], check=True)
        subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests/governance"], cwd=ROOT, check=True)
        subprocess.run(["gitleaks", "git", "--redact", "--log-opts=--all"], cwd=ROOT, check=True)
        sha = git("rev-parse", "HEAD")
        commit_date = parse_deadline(git("show", "-s", "--format=%cI", "HEAD"))
        if commit_date > deadline:
            raise ValueError("Commit timestamp is after deadline")
        # Verify the CURRENT remote main, not merely a potentially stale local ref.
        remote = git("ls-remote", "origin", "refs/heads/main").split()
        if not remote or remote[0] != sha:
            raise ValueError("Remote main and local HEAD differ")
        if git("ls-remote", "--tags", "origin", f"refs/tags/{args.tag}"):
            raise ValueError("Tag already exists remotely")
        files = {}
        for name in git("ls-files", "-z").split("\0"):
            if name:
                files[name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        manifest = {"team": "SYNAPTIX", "repository": team["repository"], "commit": sha, "tag": args.tag, "confirmed_deadline": deadline.isoformat(), "prepared_at": datetime.now(timezone.utc).isoformat(), "files_sha256": files, "limit": "Local manifest does not prove upload time or jury access. Publish and verify before deadline."}
        out = ROOT / "artifacts/submission" / args.tag / "manifest.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.exists():
            raise ValueError(f"Manifest already exists: {out}; inspect it rather than overwrite")
        out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        print(f"Prepared {out}; no tag created or pushed.")
        print(f"git tag -a {shlex.quote(args.tag)} {sha} -m {shlex.quote('SYNAPTIX hackathon submission ' + sha)}")
        print(f"git push origin refs/tags/{shlex.quote(args.tag)}")
        print("Then publish a GitHub Release with this manifest and verify the remote tag SHA.")
        return 0
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f"Cannot prepare submission: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
