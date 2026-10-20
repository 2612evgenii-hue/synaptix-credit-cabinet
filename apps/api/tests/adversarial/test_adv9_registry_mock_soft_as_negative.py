"""Attack: registry mock collapses soft statuses to negative (false credit reject)."""

import pytest

from synaptix_api.analytics.decision import apply_decision_rules
from synaptix_api.analytics.mocks import REGISTRY, run_bureau_check, run_registry_check
from synaptix_api.analytics.types import FinancialInput, RiskResult


def _decide(registry):
    finances = FinancialInput(
        revenue_minor=900_000_00,
        expenses_minor=500_000_00,
        liabilities_minor=45_000_00,
        amount_minor=1_500_000_00,
        term_months=36,
    )
    bureau = run_bureau_check("approval")
    risk = RiskResult(score=70, factors={"forced": "ok"}, model_version="adv9")
    return apply_decision_rules(
        finances,
        risk,
        registry=registry,
        bureau=bureau,
        product_min_minor=500_000_00,
        product_max_minor=10_000_000_00,
        product_min_term=1,
        product_max_term=120,
    )


@pytest.mark.parametrize(
    "profile_status,expect_check_status,expect_outcome,expect_reason",
    [
        ("unavailable", "unavailable", "CHECK_UNAVAILABLE", "CHECK_TECHNICAL_FAILURE"),
        ("missing_data", "missing_data", "NEEDS_INFO", "CHECKS_INCOMPLETE"),
    ],
)
def test_adv9_registry_soft_profile_must_not_become_negative(
    profile_status, expect_check_status, expect_outcome, expect_reason
):
    """
    Bureau profiles pass ``status`` through (``bureau_down`` → unavailable).
    Registry remaps any non-``active`` profile status to CheckOutcome ``negative``.

    Decision already maps registry unavailable → CHECK_UNAVAILABLE and
    missing_data → NEEDS_INFO. The mock therefore turns technical / incomplete
    registry outcomes into REGISTRY_NEGATIVE credit rejects — contradicting
    mocks.py: \"Technical failure is never a credit rejection.\"
    """
    key = f"adv9_reg_{profile_status}"
    REGISTRY[key] = {"found": True, "status": profile_status, "error": "simulator"}
    try:
        outcome = run_registry_check(key, "SYN-ADV9-SOFT")
        assert outcome.status == expect_check_status, (
            f"registry profile status={profile_status!r} must yield CheckOutcome "
            f"{expect_check_status!r} (mirror bureau passthrough); got "
            f"{outcome.status!r} payload={outcome.payload}"
        )

        decision = _decide(outcome)
        assert decision.outcome == expect_outcome, (
            f"soft registry {profile_status!r} must not be a credit reject; "
            f"expected {expect_outcome}, got {decision.outcome} {decision.reason_codes}"
        )
        assert expect_reason in decision.reason_codes
        assert "REGISTRY_NEGATIVE" not in decision.reason_codes
    finally:
        REGISTRY.pop(key, None)
