"""Attack: term<=0 and missing liabilities are not rejected as invalid/incomplete inputs."""

from synaptix_api.analytics.decision import apply_decision_rules
from synaptix_api.analytics.mocks import run_bureau_check, run_registry_check
from synaptix_api.analytics.risk import assess_risk
from synaptix_api.analytics.types import FinancialInput


def test_adv_term_zero_must_not_be_needs_info_via_k_unavailable():
    """term_months=0 is invalid application data, not a cashflow K gap."""
    registry = run_registry_check("approval", "SYN-ADV")
    bureau = run_bureau_check("approval")
    finances = FinancialInput(
        revenue_minor=900_000_00,
        expenses_minor=100_000_00,
        liabilities_minor=10_000_00,
        amount_minor=1_000_000_00,
        term_months=0,
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

    assert decision.outcome == "REJECTED" or "INVALID" in "".join(decision.reason_codes), (
        f"term_months=0 produced {decision.outcome} {decision.reason_codes} "
        "(annuity collapses to 0 → K_UNAVAILABLE / NEEDS_INFO)"
    )
    assert "K_UNAVAILABLE" not in decision.reason_codes
    assert decision.outcome != "NEEDS_INFO"


def test_adv_liabilities_none_must_not_approve():
    """liabilities_minor=None is incomplete financials; approving violates None≠skip invariant."""
    registry = run_registry_check("approval", "SYN-ADV")
    bureau = run_bureau_check("approval")
    finances = FinancialInput(
        revenue_minor=900_000_00,
        expenses_minor=100_000_00,
        liabilities_minor=None,
        amount_minor=1_000_000_00,
        term_months=12,
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

    assert decision.outcome in ("NEEDS_INFO", "REJECTED"), (
        f"missing liabilities approved: {decision.outcome} score={risk.score}"
    )
    assert decision.outcome != "APPROVED"
