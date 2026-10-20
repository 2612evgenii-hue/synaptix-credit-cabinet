.PHONY: check audit github-audit backup submission-check

check:
	python3 scripts/repo_checks.py
	python3 -m unittest discover -s tests/governance -v

audit:
	python3 scripts/export_audit.py

github-audit:
	python3 scripts/github_audit.py

backup:
	python3 scripts/backup.py

submission-check:
	python3 scripts/submission_check.py
