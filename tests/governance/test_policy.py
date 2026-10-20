import copy
from datetime import timedelta
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from repo_checks import valid_title, valid_branch, team_errors
from freeze import valid_tag, parse_deadline
from submission_check import readiness_errors, EXPECTED
from github_audit import protection_gaps, tag_gaps, tag_creation_gaps, sanitize


class CommitAndBranchPolicy(unittest.TestCase):
    def test_conventional_titles_and_breaking_contracts(self):
        for title in ("feat(api): persist application", "fix: исправить переход", "feat(api)!: change response"):
            self.assertTrue(valid_title(title), title)
        for title in ("update", "feat: ", "fix(): bad", "feat(api): " + "a" * 100, "feat: x\ninjected"):
            self.assertFalse(valid_title(title), title)

    def test_branch_requires_issue_or_agent_prefix(self):
        for branch in ("feat/12-draft", "hotfix/1-rbac", "codex/repository-setup", "dependabot/github_actions/actions/checkout-5"):
            self.assertTrue(valid_branch(branch))
        for branch in ("main", "feat/topic", "feat/0-topic", "codex/../../main", "fix/12-", "feat/12-Topic"):
            self.assertFalse(valid_branch(branch))

    def test_duplicate_identities_and_extra_admin_rejected(self):
        team = json.loads((ROOT / "config/team.json").read_text())
        self.assertEqual(team_errors(team), [])
        changed = copy.deepcopy(team)
        changed["members"][1]["login"] = team["members"][0]["login"].upper()
        self.assertTrue(team_errors(changed))
        changed = copy.deepcopy(team)
        changed["members"][1]["role"] = "owner"
        self.assertTrue(team_errors(changed))


class SubmissionPolicy(unittest.TestCase):
    def test_deadline_requires_explicit_timezone(self):
        with self.assertRaises(ValueError):
            parse_deadline("2026-10-20T23:59:00")
        self.assertEqual(parse_deadline("2026-10-20T23:59:00+03:00").utcoffset(), timedelta(hours=3))

    def test_tag_cannot_be_an_option_or_mutable_branch(self):
        for tag in ("v0.1.0", "v1.0.0-hackathon.1"):
            self.assertTrue(valid_tag(tag))
        for tag in ("main", "--force", "v01.0.0", "v1.0", "v1.0.0;echo", "v1.0.0-hackathon.0"):
            self.assertFalse(valid_tag(tag))

    def test_incomplete_scaffold_cannot_be_submitted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "config").mkdir()
            (root / "config/team.json").write_text(json.dumps({"deadline": None}))
            (root / "config/deliverables.json").write_text(json.dumps({"items": [{"id": "docker", "status": "pending", "paths": []}]}))
            errors = readiness_errors(root)
            self.assertTrue(any("docker" in e for e in errors))
            self.assertTrue(any("deadline" in e for e in errors))

    def test_missing_deliverable_and_path_escape_cannot_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "config").mkdir()
            (root / "evidence.txt").write_text("test evidence")
            (root / "config/team.json").write_text(json.dumps({"deadline": "2026-10-20T23:59:00+03:00"}))
            items = [{"id": name, "status": "complete", "paths": ["evidence.txt"]} for name in EXPECTED]
            config = root / "config/deliverables.json"
            config.write_text(json.dumps({"items": items}))
            self.assertEqual(readiness_errors(root), [])
            items.pop()
            config.write_text(json.dumps({"items": items}))
            self.assertTrue(any("exactly once" in e for e in readiness_errors(root)))
            items[0]["paths"] = ["../outside.txt"]
            config.write_text(json.dumps({"items": items}))
            self.assertTrue(any("outside artifact" in e for e in readiness_errors(root)))


class ServerProtectionAudit(unittest.TestCase):
    def valid_actual(self):
        desired = json.loads((ROOT / "config/github/main-protection.json").read_text())
        actual = copy.deepcopy(desired)
        for key in ("enforce_admins", "required_linear_history", "required_conversation_resolution", "allow_force_pushes", "allow_deletions"):
            actual[key] = {"enabled": desired[key]}
        return actual

    def test_github_403_is_not_reported_as_protection(self):
        self.assertTrue(protection_gaps({"unavailable": True, "error": "HTTP 403"}))

    def test_stale_reviews_admin_bypass_and_wrong_check_source_detected(self):
        actual = self.valid_actual()
        self.assertEqual(protection_gaps(actual), [])
        actual["enforce_admins"]["enabled"] = False
        actual["required_pull_request_reviews"]["dismiss_stale_reviews"] = False
        actual["required_status_checks"]["checks"][0]["app_id"] = -1
        self.assertEqual(len(protection_gaps(actual)), 3)

    def test_inactive_or_bypass_tag_rule_cannot_pass(self):
        rule = json.loads((ROOT / "config/github/tag-ruleset.json").read_text())
        self.assertEqual(tag_gaps([rule]), [])
        rule["enforcement"] = "disabled"
        self.assertTrue(tag_gaps([rule]))
        rule["enforcement"] = "active"
        rule["bypass_actors"] = [{"actor_type": "RepositoryRole", "actor_id": 5}]
        self.assertTrue(tag_gaps([rule]))


class TagCreationAudit(unittest.TestCase):
    def test_export_removes_nested_github_credentials(self):
        raw = {"visibility": "public", "temp_clone_token": "test-only-value",
               "nested": [{"access_token": "another-test-value", "password": "example"}]}
        safe = sanitize(raw)
        self.assertEqual(safe["visibility"], "public")
        self.assertNotIn("test-only-value", json.dumps(safe))
        self.assertNotIn("another-test-value", json.dumps(safe))
        self.assertNotIn('"example"', json.dumps(safe))

    def test_tag_creation_exception_cannot_allow_all_writers(self):
        rule = json.loads((ROOT / "config/github/tag-creation-ruleset.json").read_text())
        self.assertEqual(tag_creation_gaps([rule]), [])
        rule["bypass_actors"][0]["actor_id"] = 4
        self.assertTrue(tag_creation_gaps([rule]))


if __name__ == "__main__":
    unittest.main()
