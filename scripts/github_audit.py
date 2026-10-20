#!/usr/bin/env python3
"""Read actual GitHub settings and records. No account/repository mutations."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def api(endpoint, paginate=False):
    command = ["gh", "api", endpoint]
    if paginate:
        command += ["--paginate", "--slurp"]
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    if result.returncode:
        return {"unavailable": True, "error": result.stderr.strip()}
    data = json.loads(result.stdout)
    if paginate:
        return [item for page in data for item in page]
    return data


def protection_gaps(actual):
    errors = []
    if actual.get("unavailable"):
        return ["main protection unavailable: " + actual["error"]]
    for key in ("enforce_admins", "required_linear_history", "required_conversation_resolution"):
        if actual.get(key, {}).get("enabled") is not True:
            errors.append(f"main protection missing: {key}")
    for key in ("allow_force_pushes", "allow_deletions"):
        if actual.get(key, {}).get("enabled") is not False:
            errors.append(f"main protection must disable: {key}")
    review = actual.get("required_pull_request_reviews") or {}
    if review.get("required_approving_review_count", 0) < 1:
        errors.append("Independent approving review not required")
    for key in ("dismiss_stale_reviews", "require_code_owner_reviews", "require_last_push_approval"):
        if review.get(key) is not True:
            errors.append(f"Review protection missing: {key}")
    checks = actual.get("required_status_checks") or {}
    if checks.get("strict") is not True:
        errors.append("Up-to-date main not required")
    entries = checks.get("checks", [])
    for name in ("repository-policy", "secret-scan"):
        if not any(item.get("context") == name and item.get("app_id") == 15368 for item in entries):
            errors.append(f"Required GitHub Actions check missing: {name}")
    return errors


def tag_gaps(rulesets):
    if isinstance(rulesets, dict):
        return ["Tag rulesets unavailable: " + rulesets.get("error", "unknown error")]
    for ruleset in rulesets:
        if ruleset.get("unavailable"):
            continue
        include = ruleset.get("conditions", {}).get("ref_name", {}).get("include", [])
        exclude = ruleset.get("conditions", {}).get("ref_name", {}).get("exclude", [])
        rules = {r.get("type") for r in ruleset.get("rules", [])}
        if (ruleset.get("target") == "tag" and ruleset.get("enforcement") == "active"
                and "refs/tags/v*" in include and not exclude
                and {"update", "deletion"}.issubset(rules)
                and not ruleset.get("bypass_actors")):
            return []
    return ["No active no-bypass update/deletion protection for v* tags"]


def main():
    team = json.loads((ROOT / "config/team.json").read_text())
    repo = team["repository"]
    prefix = f"repos/{repo}"
    snapshot = {"observed_at": datetime.now(timezone.utc).isoformat(), "repository": api(prefix)}
    for key, suffix, pages in (
        ("main_protection", "/branches/main/protection", False),
        ("collaborators", "/collaborators?per_page=100", True),
        ("invitations", "/invitations?per_page=100", True),
        ("actions_workflow_permissions", "/actions/permissions/workflow", False),
        ("rulesets", "/rulesets?per_page=100", True),
        ("issues_and_prs", "/issues?state=all&per_page=100", True),
        ("pull_requests", "/pulls?state=all&per_page=100", True),
    ):
        snapshot[key] = api(prefix + suffix, pages)
    rulesets = snapshot["rulesets"]
    if isinstance(rulesets, list):
        snapshot["rulesets"] = [api(prefix + f"/rulesets/{r['id']}") for r in rulesets]
    errors = protection_gaps(snapshot["main_protection"]) + tag_gaps(snapshot["rulesets"])
    actual = snapshot["repository"]
    if actual.get("private") is not True:
        errors.append("Repository is not private or metadata is unavailable")
    for key, desired in {"allow_squash_merge": True, "allow_merge_commit": False, "allow_rebase_merge": False, "delete_branch_on_merge": True}.items():
        if actual.get(key) is not desired:
            errors.append(f"Repository setting mismatch: {key}")
    permissions = snapshot["actions_workflow_permissions"]
    if permissions.get("default_workflow_permissions") != "read" or permissions.get("can_approve_pull_request_reviews") is not False:
        errors.append("Actions token/approval permissions not hardened or unavailable")
    collaborators = snapshot["collaborators"]
    if isinstance(collaborators, list):
        accepted = {c["login"].lower(): c for c in collaborators}
        for member in team["members"]:
            user = accepted.get(member["login"].lower())
            if not user or not user.get("permissions", {}).get("push"):
                errors.append(f"Team write access not accepted/available: {member['login']}")
        owner = next(m for m in team["members"] if m["role"] == "owner")
        if actual.get("owner", {}).get("login", "").lower() != owner["login"].lower():
            errors.append("Unexpected repository owner")
        for user in collaborators:
            if user["login"].lower() != owner["login"].lower() and user.get("permissions", {}).get("admin"):
                errors.append(f"Unexpected collaborator admin: {user['login']}")
    else:
        errors.append("Cannot verify accepted collaborators")
    snapshot["gaps"] = errors
    out = ROOT / "artifacts/audit/github-settings.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n")
    print(f"Read-only snapshot: {out}")
    print("Includes currently accessible issues/PRs/settings; not the full GitHub audit log.")
    for error in errors:
        print(f"GAP: {error}")
    return bool(errors)


if __name__ == "__main__":
    sys.exit(main())
