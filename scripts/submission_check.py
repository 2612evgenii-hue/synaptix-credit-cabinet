#!/usr/bin/env python3
"""Fail-closed artifact checklist. Does NOT execute or certify the product."""
from datetime import datetime
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {"docker", "runtime-locks", "seed-and-demo-accounts", "working-openapi-and-collection", "e2e-and-clean-pc-report", "architecture-states-data-model", "readme-runbook", "notices-and-licenses", "requirements-reviewed", "jury-access-verified"}


def readiness_errors(root=ROOT):
    errors = []
    team = json.loads((root / "config/team.json").read_text())
    try:
        deadline = datetime.fromisoformat(team.get("deadline") or "")
        if deadline.utcoffset() is None:
            raise ValueError("timezone missing")
    except ValueError:
        errors.append("Confirmed deadline with timezone is missing")
    items = json.loads((root / "config/deliverables.json").read_text())["items"]
    ids = [item["id"] for item in items]
    if set(ids) != EXPECTED or len(ids) != len(EXPECTED):
        errors.append("Deliverables must contain each required id exactly once")
    for item in items:
        if item["status"] != "complete":
            errors.append(f"Not complete: {item['id']} ({item['status']})")
        if not item["paths"]:
            errors.append(f"No evidence paths: {item['id']}")
        for name in item["paths"]:
            path = (root / name).resolve()
            if not path.is_relative_to(root.resolve()) or not path.is_file() or path.stat().st_size == 0:
                errors.append(f"Missing/empty/outside artifact: {name}")
    return errors


def main():
    errors = readiness_errors()
    for error in errors:
        print(f"NOT READY: {error}", file=sys.stderr)
    if not errors:
        print("Checklist complete. Human clean-PC/E2E validation is still required.")
    return bool(errors)


if __name__ == "__main__":
    sys.exit(main())
