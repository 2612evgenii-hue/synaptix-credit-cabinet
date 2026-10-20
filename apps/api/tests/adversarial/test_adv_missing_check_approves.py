"""Attack: missing_data registry/bureau is not blocked; decision may APPROVE with CHECKS_OK."""

from synaptix_api.analytics.decision import apply_decision_rules
from synaptix_api.analytics.mocks import run_bureau_check, run_registry_check
from synaptix_api.analytics.risk import assess_risk
from synaptix_api.analytics.types import CheckOutcome, FinancialInput


def _strong_finances() -> FinancialInput:
    return FinancialInput(
        revenue_minor=900_000_00,
        expenses_minor=100_000_00,
        liabilities_minor=10_000_00,
        amount_minor=1_000_000_00,
        term_months=12,
    )


def test_adv_registry_missing_data_must_not_approve_as_checks_ok():
    finances = _strong_finances()
    registry = CheckOutcome(
        source="company_registry",
        status="missing_data",
        mock_version="adv",
        payload={"error": "unknown_scenario"},
    )
    bureau = run_bureau_check("approval")
    risk = assess_risk(finances, bureau=bureau, registry=registry)
    decision = apply_decision_rules(
        finances,
        risk,
        registry=registry,
        bureau=bureau,
        product_min_minor=300_000_00,
        product_max_minor=5_000_000_00,
        product_min_term=1,
        product_max_term=120,
    )

    assert decision.outcome != "APPROVED", (
        f"missing registry data approved: {decision.outcome} {decision.reason_codes}"
    )
    assert "CHECKS_OK" not in decision.reason_codes


def test_adv_bureau_missing_data_must_not_approve_as_checks_ok():
    finances = _strong_finances()
    registry = run_registry_check("approval", "SYN-ADV")
    bureau = CheckOutcome(
        source="credit_bureau",
        status="missing_data",
        mock_version="adv",
        payload={"error": "unknown_scenario"},
    )
    risk = assess_risk(finances, bureau=bureau, registry=registry)
    decision = apply_decision_rules(
        finances,
        risk,
        registry=registry,
        bureau=bureau,
        product_min_minor=300_000_00,
        product_max_minor=5_000_000_00,
        product_min_term=1,
        product_max_term=120,
    )

    assert decision.outcome != "APPROVED", (
        f"missing bureau data approved: {decision.outcome} {decision.reason_codes}"
    )
    assert "CHECKS_OK" not in decision.reason_codes
