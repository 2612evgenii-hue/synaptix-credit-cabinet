"""Attack: non-integer money/term inputs approve or crash the decision pipeline."""

import pytest

from synaptix_api.analytics.decision import apply_decision_rules
from synaptix_api.analytics.mocks import run_bureau_check, run_registry_check
from synaptix_api.analytics.risk import assess_risk
from synaptix_api.analytics.types import FinancialInput

PRODUCT_MIN = 300_000_00
PRODUCT_MAX = 5_000_000_00


def _decide(fin: FinancialInput):
    registry = run_registry_check("approval", "SYN-ADV6-NUM")
    bureau = run_bureau_check("approval")
    risk = assess_risk(fin, bureau=bureau, registry=registry)
    return apply_decision_rules(
        fin,
        risk,
        registry=registry,
        bureau=bureau,
        product_min_minor=PRODUCT_MIN,
        product_max_minor=PRODUCT_MAX,
        product_min_term=6,
        product_max_term=36,
    )


def test_adv6_fractional_term_must_not_approve():
    """
    term_months is documented as integer months; product bounds are integers.
    term_months=12.5 still passes min/max term gates and yields APPROVED with a
    fractional-term annuity — not a valid credit term.
    """
    finances = FinancialInput(
        revenue_minor=300_000_000,
        expenses_minor=50_000_000,
        liabilities_minor=10_000_000,
        amount_minor=500_000_00,
        term_months=12.5,  # type: ignore[arg-type]
    )
    decision = _decide(finances)
    assert decision.outcome != "APPROVED", (
        f"fractional term_months=12.5 must not approve; got {decision.outcome} "
        f"{decision.reason_codes} offered_terms={decision.offered_terms}"
    )


def test_adv6_float_amount_must_not_approve():
    """Money fields are minor-unit integers (kopecks). Float amount must not approve."""
    finances = FinancialInput(
        revenue_minor=300_000_000,
        expenses_minor=50_000_000,
        liabilities_minor=10_000_000,
        amount_minor=500_000_00.7,  # type: ignore[arg-type]
        term_months=12,
    )
    decision = _decide(finances)
    assert decision.outcome != "APPROVED", (
        f"float amount_minor must not approve; got {decision.outcome} "
        f"{decision.reason_codes} amount={decision.offered_terms.get('amount_minor')!r}"
    )


def test_adv6_string_amount_must_not_crash():
    """
    Cycle 4/5 closed rate/overdue crashes. amount_minor='50000000' still raises
    TypeError in the product-limit comparison instead of a DecisionResult.
    """
    finances = FinancialInput(
        revenue_minor=300_000_000,
        expenses_minor=50_000_000,
        liabilities_minor=10_000_000,
        amount_minor="50000000",  # type: ignore[arg-type]
        term_months=12,
    )
    try:
        decision = _decide(finances)
    except (TypeError, ValueError) as exc:
        pytest.fail(
            f"string amount_minor crashed apply_decision_rules with "
            f"{type(exc).__name__}: {exc} — must return a DecisionResult"
        )
    assert decision.outcome != "APPROVED", (
        f"string amount must not approve; got {decision.outcome} {decision.reason_codes}"
    )
