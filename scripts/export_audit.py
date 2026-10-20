#!/usr/bin/env python3
"""Export local Git history; never claim this is a full GitHub/account audit."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main():
    out = ROOT / "artifacts/audit"
    out.mkdir(parents=True, exist_ok=True)
    commits = []
    for sha in git("rev-list", "--all", "--date-order").splitlines():
        record = {"sha": sha}
        for field, fmt in {"author": "%an", "author_email": "%ae", "authored_at": "%aI", "committer": "%cn", "committed_at": "%cI", "subject": "%s", "body": "%b", "parents": "%P"}.items():
            record[field] = git("show", "-s", f"--format={fmt}", sha)
        record["files"] = git("diff-tree", "--root", "--no-commit-id", "--name-status", "-r", sha).splitlines()
        commits.append(record)
    payload = {"exported_at": datetime.now(timezone.utc).isoformat(), "scope": "local Git refs only; authorship dates are self-reported", "head": git("rev-parse", "HEAD"), "refs": git("show-ref"), "commits": commits}
    (out / "git-history.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    rows = ["# Local Git audit", "", "This export excludes GitHub settings, chats and unsaved actions.", ""]
    rows.extend(f"- `{c['sha']}` — {c['committed_at']} — {c['author']}: {c['subject']}" for c in commits)
    (out / "git-history.md").write_text("\n".join(rows) + "\n")
    print(out)


if __name__ == "__main__":
    main()
