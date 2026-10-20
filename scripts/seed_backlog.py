#!/usr/bin/env python3
"""Explicit --apply seeds unassigned Issues; reruns skip matching titles."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def gh(*args):
    return subprocess.check_output(["gh", *args], cwd=ROOT, text=True).strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Create labels, milestones and unassigned issues")
    args = parser.parse_args()
    repo = json.loads((ROOT / "config/team.json").read_text())["repository"]
    backlog = json.loads((ROOT / "config/backlog.json").read_text())
    if not args.apply:
        for item in backlog["issues"]:
            print(item["title"])
        print("Dry run. Use --apply to seed GitHub; no collaborators are invited by this script.")
        return
    for label in backlog["labels"]:
        # Do not overwrite existing label definitions.
        labels = json.loads(gh("api", f"repos/{repo}/labels?per_page=100"))
        if label["name"] not in {x["name"] for x in labels}:
            gh("api", "--method", "POST", f"repos/{repo}/labels", "-f", f"name={label['name']}", "-f", f"color={label['color']}", "-f", f"description={label['description']}")
    milestones = json.loads(gh("api", f"repos/{repo}/milestones?state=all&per_page=100"))
    names = {m["title"] for m in milestones}
    for title in backlog["milestones"]:
        if title not in names:
            gh("api", "--method", "POST", f"repos/{repo}/milestones", "-f", f"title={title}")
    # CLI paginates up to the explicit bound; initial project has only a few issues.
    existing = json.loads(gh("issue", "list", "--repo", repo, "--state", "all", "--limit", "1000", "--json", "title,number"))
    titles = {item["title"] for item in existing}
    for item in backlog["issues"]:
        if item["title"] in titles:
            print("Exists:", item["title"])
            continue
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "body.md"
            path.write_text(item["body"])
            command = ["issue", "create", "--repo", repo, "--title", item["title"], "--body-file", str(path), "--milestone", item["milestone"]]
            for label in item["labels"]:
                command += ["--label", label]
            print(gh(*command))
        titles.add(item["title"])


if __name__ == "__main__":
    main()
