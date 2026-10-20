"""Attack: FinancialInput.currency != RUB is ignored; decision treats amounts as RUB."""

from synaptix_api.analytics.decision import apply_decision_rules
from synaptix_api.analytics.mocks import run_bureau_check, run_registry_check
from synaptix_api.analytics.risk import assess_risk
from synaptix_api.analytics.types import FinancialInput

PRODUCT_MIN = 300_000_00
PRODUCT_MAX = 5_000_000_00


def test_adv2_non_rub_currency_must_not_approve_as_rub():
    """
    OpenAPI/data-model restrict application currency to RUB. Passing USD (or other)
    must not silently run RUB annuity/coverage and APPROVE.
    """
    finances = FinancialInput(
        revenue_minor=900_000_00,
        expenses_minor=100_000_00,
        liabilities_minor=10_000_00,
        amount_minor=500_000_00,
        term_months=12,
        currency="USD",
    )
    registry = run_registry_check("approval", "SYN-ADV2")
    bureau = run_bureau_check("approval")
    risk = assess_risk(finances, bureau=bureau, registry=registry)
    decision = apply_decision_rules(
        finances,
        risk,
        registry=registry,
        bureau=bureau,
        product_min_minor=PRODUCT_MIN,
        product_max_minor=PRODUCT_MAX,
        product_min_term=1,
        product_max_term=120,
    )

    assert decision.outcome != "APPROVED", (
        f"currency={finances.currency} silently approved as RUB; "
        f"outcome={decision.outcome} reasons={decision.reason_codes}"
    )
    assert decision.outcome in ("REJECTED", "NEEDS_INFO") or "CURRENCY" in "".join(
        decision.reason_codes
    ), f"expected currency rejection signal, got {decision.outcome} {decision.reason_codes}"
