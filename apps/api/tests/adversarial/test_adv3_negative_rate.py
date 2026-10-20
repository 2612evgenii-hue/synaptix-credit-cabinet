"""Attack: negative demo_rate_annual still APPROVES with a negative offer rate."""

from synaptix_api.analytics.decision import apply_decision_rules
from synaptix_api.analytics.mocks import run_bureau_check, run_registry_check
from synaptix_api.analytics.risk import assess_risk
from synaptix_api.analytics.types import FinancialInput


def test_adv3_negative_annual_rate_must_not_approve():
    """
    apply_decision_rules never validates demo_rate_annual. A negative rate
    inflates coverage_k and can APPROVE with rate_annual < 0 in offered_terms.
    """
    finances = FinancialInput(
        revenue_minor=900_000_00,
        expenses_minor=500_000_00,
        liabilities_minor=45_000_00,
        amount_minor=1_500_000_00,
        term_months=36,
    )
    registry = run_registry_check("approval", "SYN-ADV3-RATE")
    bureau = run_bureau_check("approval")
    risk = assess_risk(finances, bureau=bureau, registry=registry)

    decision = apply_decision_rules(
        finances,
        risk,
        registry=registry,
        bureau=bureau,
        product_min_minor=500_000_00,
        product_max_minor=10_000_000_00,
        product_min_term=1,
        product_max_term=120,
        demo_rate_annual=-0.5,
    )

    assert decision.outcome != "APPROVED", (
        f"negative rate must not approve; got {decision.outcome} "
        f"terms={decision.offered_terms} k={decision.metrics.get('coverage_k')}"
    )
    rate = decision.offered_terms.get("rate_annual")
    assert rate is None or rate >= 0, f"offered negative rate_annual={rate}"
