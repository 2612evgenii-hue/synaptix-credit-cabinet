"""Attack: registry mock still collapses unknown/incomplete statuses to negative."""

import pytest

from synaptix_api.analytics.decision import apply_decision_rules
from synaptix_api.analytics.mocks import REGISTRY, run_bureau_check, run_registry_check
from synaptix_api.analytics.types import CheckOutcome, FinancialInput, RiskResult


def _decide(registry: CheckOutcome):
    finances = FinancialInput(
        revenue_minor=900_000_00,
        expenses_minor=500_000_00,
        liabilities_minor=45_000_00,
        amount_minor=1_500_000_00,
        term_months=36,
    )
    bureau = run_bureau_check("approval")
    risk = RiskResult(score=70, factors={"forced": "ok"}, model_version="adv10")
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
    "profile_status",
    [
        "pending",
        "error",
        "",
        None,
    ],
)
def test_adv10_registry_unknown_profile_status_must_not_become_negative(profile_status):
    """
    Cycle 9 allowlisted only unavailable / missing_data for registry passthrough.
    Decision maps any other non-canonical CheckOutcome status → NEEDS_INFO /
    CHECKS_INCOMPLETE (cycle 5). Registry profiles with pending / error / empty /
    None still hit ``status != \"active\"`` → CheckOutcome ``negative`` →
    REGISTRY_NEGATIVE — false credit reject for incomplete / technical states.
    Bureau profiles pass the same values through unchanged.
    """
    key = f"adv10_reg_unknown_{profile_status!s}"
    REGISTRY[key] = {"found": True, "status": profile_status}
    try:
        outcome = run_registry_check(key, "SYN-ADV10-UNKNOWN")
        assert outcome.status != "negative", (
            f"registry profile status={profile_status!r} must not become "
            f"CheckOutcome negative (cycle 5/9 soft/unknown path); got "
            f"{outcome.status!r} payload={outcome.payload}"
        )

        # Constructed peer with the same status must stay non-reject when status
        # is a non-empty unknown; empty/None are incomplete → missing_data-like.
        if profile_status not in (None, ""):
            constructed = CheckOutcome(
                source="company_registry",
                status=profile_status,  # type: ignore[arg-type]
                mock_version="adv10",
                payload={},
            )
            baseline = _decide(constructed)
            assert baseline.outcome != "REJECTED", (
                f"precondition: constructed status={profile_status!r} must not "
                f"hard-reject; got {baseline.outcome} {baseline.reason_codes}"
            )

        decision = _decide(outcome)
        assert decision.outcome != "REJECTED", (
            f"unknown registry profile {profile_status!r} must not credit-reject; "
            f"got {decision.outcome} {decision.reason_codes}"
        )
        assert "REGISTRY_NEGATIVE" not in decision.reason_codes
    finally:
        REGISTRY.pop(key, None)
