"""Attack: negative expenses (or negative revenue+expenses) inflate cashflow → APPROVE."""

from synaptix_api.analytics.decision import apply_decision_rules
from synaptix_api.analytics.mocks import run_bureau_check, run_registry_check
from synaptix_api.analytics.risk import assess_risk
from synaptix_api.analytics.types import FinancialInput

PRODUCT_MIN = 300_000_00
PRODUCT_MAX = 5_000_000_00


def _decide(fin: FinancialInput):
    registry = run_registry_check("approval", "SYN-ADV2")
    bureau = run_bureau_check("approval")
    risk = assess_risk(fin, bureau=bureau, registry=registry)
    return apply_decision_rules(
        fin,
        risk,
        registry=registry,
        bureau=bureau,
        product_min_minor=PRODUCT_MIN,
        product_max_minor=PRODUCT_MAX,
        product_min_term=1,
        product_max_term=120,
    )


def test_adv2_negative_expenses_must_not_approve():
    """
    expenses_minor < 0 increases available_cashflow (revenue - expenses).
    Banking money fields are non-negative; negative expenses must not mint coverage.
    """
    finances = FinancialInput(
        revenue_minor=200_000_00,
        expenses_minor=-300_000_00,  # fabricated +5M RUB cashflow
        liabilities_minor=10_000_00,
        amount_minor=500_000_00,
        term_months=12,
    )
    assert finances.available_cashflow_minor() == 500_000_00

    decision = _decide(finances)
    assert decision.outcome != "APPROVED", (
        f"negative expenses approved with k={decision.metrics.get('coverage_k')} "
        f"reasons={decision.reason_codes}"
    )


def test_adv2_negative_revenue_and_expenses_must_not_approve():
    """Both legs negative can still yield positive 'available' and APPROVE."""
    finances = FinancialInput(
        revenue_minor=-100_000_00,
        expenses_minor=-500_000_00,
        liabilities_minor=10_000_00,
        amount_minor=500_000_00,
        term_months=12,
    )
    assert finances.available_cashflow_minor() is not None
    assert finances.available_cashflow_minor() > 0

    decision = _decide(finances)
    assert decision.outcome != "APPROVED", (
        f"negative revenue/expenses approved; avail={finances.available_cashflow_minor()} "
        f"outcome={decision.outcome} reasons={decision.reason_codes}"
    )
