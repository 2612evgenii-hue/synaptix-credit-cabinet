"""Attack: non-int overdue_days crashes decision/risk instead of a DecisionResult."""

import pytest

from synaptix_api.analytics.decision import apply_decision_rules
from synaptix_api.analytics.mocks import run_registry_check
from synaptix_api.analytics.risk import assess_risk
from synaptix_api.analytics.types import CheckOutcome, FinancialInput, RiskResult


def test_adv5_malformed_overdue_days_must_not_crash():
    """
    Cycle 4 closed non-finite rate crashes with INVALID_RATE. Corrupt bureau
    payload overdue_days='nope' still raises ValueError in _bureau_overdue_days
    / assess_risk — pipeline dumps instead of NEEDS_INFO / reject.
    """
    finances = FinancialInput(
        revenue_minor=900_000_00,
        expenses_minor=500_000_00,
        liabilities_minor=45_000_00,
        amount_minor=1_500_000_00,
        term_months=36,
    )
    registry = run_registry_check("approval", "SYN-ADV5-OVERDUE")
    bureau = CheckOutcome(
        source="credit_bureau",
        status="ok",
        mock_version="adv5",
        payload={"overdue_days": "nope"},
    )
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
            product_max_term=120,
        )
    except (ValueError, TypeError, OverflowError) as exc:
        pytest.fail(
            f"overdue_days='nope' crashed apply_decision_rules with "
            f"{type(exc).__name__}: {exc} — must return a DecisionResult"
        )

    assert decision.outcome != "APPROVED", (
        f"malformed overdue must not approve; got {decision.outcome} {decision.reason_codes}"
    )


def test_adv5_malformed_overdue_must_not_crash_risk():
    finances = FinancialInput(
        revenue_minor=900_000_00,
        expenses_minor=500_000_00,
        liabilities_minor=45_000_00,
        amount_minor=1_500_000_00,
        term_months=36,
    )
    registry = run_registry_check("approval", "SYN-ADV5-OVERDUE-R")
    bureau = CheckOutcome(
        source="credit_bureau",
        status="ok",
        mock_version="adv5",
        payload={"overdue_days": "nope"},
    )
    try:
        assess_risk(finances, bureau=bureau, registry=registry)
    except (ValueError, TypeError) as exc:
        pytest.fail(
            f"overdue_days='nope' crashed assess_risk with "
            f"{type(exc).__name__}: {exc}"
        )
