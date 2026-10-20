"""Attack: extreme term_months inside product bounds OverflowError in annuity."""

import pytest

from synaptix_api.analytics.decision import apply_decision_rules
from synaptix_api.analytics.mocks import run_bureau_check, run_registry_check
from synaptix_api.analytics.types import FinancialInput, RiskResult


def test_adv5_extreme_term_must_not_crash_annuity():
    """
    Product term bounds are checked, but there is no absolute cap. term_months
    large enough for (1+r)**n to overflow float (e.g. 100_000 with rate 0.16)
    raises OverflowError after PRODUCT_LIMIT passes — same crash class as
    cycle-4 non-finite rate, different input.
    """
    finances = FinancialInput(
        revenue_minor=900_000_00,
        expenses_minor=500_000_00,
        liabilities_minor=45_000_00,
        amount_minor=1_500_000_00,
        term_months=100_000,
    )
    registry = run_registry_check("approval", "SYN-ADV5-TERM")
    bureau = run_bureau_check("approval")
    risk = RiskResult(score=70, factors={"forced": "ok"}, model_version="adv5")

    try:
        decision = apply_decision_rules(
            finances,
            risk,
            registry=registry,
            bureau=bureau,
            product_min_minor=500_000_00,
            product_max_minor=10_000_000_00,
            product_min_term=1,
            product_max_term=100_000,
        )
    except (OverflowError, ValueError, ArithmeticError) as exc:
        pytest.fail(
            f"term_months=100000 crashed apply_decision_rules with "
            f"{type(exc).__name__}: {exc} — must return a DecisionResult"
        )

    assert decision.outcome in {
        "APPROVED",
        "REJECTED",
        "NEEDS_INFO",
        "ALTERNATIVE",
        "CHECK_UNAVAILABLE",
    }, f"unexpected outcome {decision.outcome}"
