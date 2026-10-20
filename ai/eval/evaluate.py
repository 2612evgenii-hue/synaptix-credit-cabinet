"""Evaluate heuristic/LLM extract against ai/eval/cases.json (P11)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API_SRC = ROOT / "apps" / "api" / "src"
sys.path.insert(0, str(API_SRC))

from synaptix_api.analytics.extract import extract_application_fields  # noqa: E402


def main() -> int:
    cases = json.loads((Path(__file__).parent / "cases.json").read_text(encoding="utf-8"))
    ok = 0
    total = 0
    for case in cases["cases"]:
        total += 1
        result = extract_application_fields(case["input_text"])
        exp = case["expect"]
        failed = []
        if exp.get("goal_code") != result.goal_code:
            failed.append(f"goal {result.goal_code!r}!={exp.get('goal_code')!r}")
        if exp.get("amount_minor") != result.amount_minor:
            failed.append(f"amount {result.amount_minor!r}!={exp.get('amount_minor')!r}")
        if exp.get("term_months") != result.term_months:
            failed.append(f"term {result.term_months!r}!={exp.get('term_months')!r}")
        for m in exp.get("must_missing") or []:
            if m not in result.missing_fields:
                failed.append(f"missing {m}")
        if exp.get("injection_detected") and not result.injection_detected:
            failed.append("injection not flagged")
        if failed:
            print(f"FAIL {case['id']}: {'; '.join(failed)}")
        else:
            ok += 1
            print(f"PASS {case['id']}")
    print(f"score={ok}/{total}")
    return 0 if ok == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
