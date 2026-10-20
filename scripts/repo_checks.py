#!/usr/bin/env python3
"""Dependency-free repository checks. This is not application acceptance testing."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
TITLE = re.compile(r"^(feat|fix|docs|test|refactor|perf|build|ci|chore|revert)(\([a-z0-9][a-z0-9/-]*\))?!?: \S.+$")
BRANCH = re.compile(r"^(?:(?:feat|fix|docs|chore|test|refactor|hotfix)/[1-9][0-9]*-[a-z0-9]+(?:-[a-z0-9]+)*|codex/[a-z0-9]+(?:-[a-z0-9]+)*)$")
REQUIRED = (
    "README.md", "CONTRIBUTING.md", "SECURITY.md", "CHANGELOG.md",
    "THIRD_PARTY_NOTICES", ".github/CODEOWNERS", "docs/requirements.md",
    "docs/architecture.md", "docs/state-machine.md", "docs/data-model.md",
    "docs/test-scenarios.md", "docs/submission.md", "docs/github-status.md",
    "packages/contracts/openapi.json", "docs/api/postman_collection.json",
    "config/team.json", "config/deliverables.json",
)


def valid_title(title):
    return len(title) <= 100 and TITLE.fullmatch(title) is not None


def valid_branch(branch):
    return (BRANCH.fullmatch(branch) is not None
            or re.fullmatch(r"dependabot/github_actions/[a-zA-Z0-9_./-]+", branch) is not None)


def team_errors(team):
    members = team.get("members", [])
    logins = [m.get("login", "") for m in members]
    errors = []
    if len(members) != 3 or len(set(s.lower() for s in logins)) != 3:
        errors.append("Team must have exactly three distinct members")
    if any(not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?", s) for s in logins):
        errors.append("Invalid GitHub login")
    if sum(m.get("role") == "owner" for m in members) != 1:
        errors.append("Exactly one owner required")
    if any(m.get("role") not in ("owner", "write") for m in members):
        errors.append("Unexpected member permission")
    return errors


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--commit-msg", type=Path)
    parser.add_argument("--event-file", type=Path)
    args = parser.parse_args()
    if args.commit_msg:
        title = args.commit_msg.read_text().splitlines()[0]
        if not valid_title(title):
            print("Expected type(scope): description, at most 100 characters", file=sys.stderr)
            return 1
        return 0

    errors = []
    for name in REQUIRED:
        if not (ROOT / name).is_file():
            errors.append(f"Missing repository artifact: {name}")
    # Read all repository JSON (untracked new config included before first commit).
    for directory in ("config", "packages/contracts", "data/synthetic", "docs/api"):
        for path in (ROOT / directory).rglob("*.json"):
            try:
                json.loads(path.read_text())
            except (ValueError, OSError) as exc:
                errors.append(f"Invalid JSON: {path.relative_to(ROOT)}: {exc}")
    try:
        team = json.loads((ROOT / "config/team.json").read_text())
        errors.extend(team_errors(team))
        owners = (ROOT / ".github/CODEOWNERS").read_text()
        active = "\n".join(line for line in owners.splitlines() if not line.startswith("#"))
        for member in team["members"]:
            if f"@{member['login']}" not in active.split():
                errors.append(f"Missing code owner: {member['login']}")
    except (OSError, ValueError, KeyError) as exc:
        errors.append(f"Invalid team config: {exc}")
    # Tracked paths are authoritative. --cached is used separately by Gitleaks hooks.
    tracked = git("ls-files", "-z").split("\0")
    for name in filter(None, tracked):
        path = ROOT / name
        if not path.exists():
            continue
        if path.stat().st_size > 10 * 1024 * 1024:
            errors.append(f"Large tracked file (use reviewed release assets): {name}")
        if (path.name == ".env" or path.name.startswith(".env.")) and path.name != ".env.example":
            errors.append(f"Environment file must not be tracked: {name}")
        if path.suffix.lower() in (".pem", ".key", ".p12", ".pfx", ".db", ".sqlite", ".sqlite3"):
            errors.append(f"Sensitive/binary database file must not be tracked: {name}")
    for path in (ROOT / ".github/workflows").glob("*.yml"):
        for action in re.findall(r"uses:\s*([^\s#]+)", path.read_text()):
            if not re.fullmatch(r"[\w./-]+@[0-9a-f]{40}", action):
                errors.append(f"Action must be pinned to full SHA: {action}")
    # Verify local Markdown file links, excluding URL schemes, anchors and mail.
    for path in [ROOT / "README.md", ROOT / "CONTRIBUTING.md", *list((ROOT / "docs").rglob("*.md"))]:
        for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
            if ":" in target or target.startswith("#"):
                continue
            target = target.split("#")[0]
            if not (path.parent / target).exists():
                errors.append(f"Broken file link: {path.relative_to(ROOT)} -> {target}")
    event_file = args.event_file or (Path(os.environ["GITHUB_EVENT_PATH"]) if os.environ.get("GITHUB_EVENT_PATH") else None)
    if event_file:
        event = json.loads(event_file.read_text())
        pr = event.get("pull_request")
        if pr:
            if not valid_title(pr["title"]):
                errors.append("PR title must follow Conventional Commits (<=100 chars)")
            if not valid_branch(pr["head"]["ref"]):
                errors.append("PR branch must follow CONTRIBUTING.md")
            base, head = pr["base"]["sha"], pr["head"]["sha"]
            if not all(re.fullmatch(r"[0-9a-f]{40}", ref) for ref in (base, head)):
                errors.append("Invalid event SHA")
            else:
                for title in git("log", "--no-merges", "--format=%s", f"{base}..{head}").splitlines():
                    if not valid_title(title):
                        errors.append(f"Invalid commit title: {title}")
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if not errors:
        print("Repository policy OK (application readiness is checked separately)")
    return bool(errors)


if __name__ == "__main__":
    sys.exit(main())
