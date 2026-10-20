"""Oracles from data/expected-results.json must match run_analytics (P04)."""

import json
from pathlib import Path

from synaptix_api.analytics.pipeline import ProductLimits, run_analytics
from synaptix_api.analytics.types import FinancialInput

ROOT = Path(__file__).resolve().parents[3]
SCENARIOS = json.loads((ROOT / "data" / "synthetic" / "scenarios.json").read_text(encoding="utf-8"))
EXPECTED = json.loads((ROOT / "data" / "expected-results.json").read_text(encoding="utf-8"))
PRODUCTS = json.loads((ROOT / "data" / "products.json").read_text(encoding="utf-8"))


def _product(code: str) -> ProductLimits:
    row = next(p for p in PRODUCTS["products"] if p["code"] == code)
    return ProductLimits(
        min_amount_minor=row["min_amount_minor"],
        max_amount_minor=row["max_amount_minor"],
        min_term_months=row["min_term_months"],
        max_term_months=row["max_term_months"],
        demo_rate_annual=row["demo_rate_annual"],
    )


def test_expected_results_match_pipeline():
    by_id = {c["id"]: c for c in SCENARIOS["cases"]}
    for exp in EXPECTED["cases"]:
        case = by_id[exp["scenario_key"]]
        finances = FinancialInput(
            revenue_minor=case.get("revenue_minor"),
            expenses_minor=case.get("expenses_minor"),
            liabilities_minor=case.get("liabilities_minor"),
            amount_minor=case["amount_minor"],
            term_months=case["term_months"],
        )
        bundle = run_analytics(
            scenario_key=case["id"],
            registration_id=f"SYN-{case['id'].upper()}",
            finances=finances,
            product=_product(exp["product_code"]),
        )
        assert bundle.decision.outcome == exp["intended_outcome"], (
            f"{exp['id']}: got {bundle.decision.outcome} {bundle.decision.reason_codes}"
        )
        subset = exp["expected_reason_subset"]
        # Rejection family: any listed code may be acceptable (OR).
        if exp["intended_outcome"] == "REJECTED" and len(subset) > 1:
            assert any(code in bundle.decision.reason_codes for code in subset) or any(
                c.startswith("BUREAU_") for c in bundle.decision.reason_codes
                if any(s.startswith("BUREAU_") for s in subset)
            ), (
                f"{exp['id']}: none of {subset} in {bundle.decision.reason_codes}"
            )
            continue
        for code in subset:
            if exp["intended_outcome"] == "REJECTED" and code.startswith("BUREAU_"):
                assert any(c.startswith("BUREAU_") for c in bundle.decision.reason_codes)
            else:
                assert code in bundle.decision.reason_codes, (
                    f"{exp['id']}: missing {code} in {bundle.decision.reason_codes}"
                )
