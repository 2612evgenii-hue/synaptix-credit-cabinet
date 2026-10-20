"""Attack: registry soft statuses without found key remap to negative."""

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
    risk = RiskResult(score=70, factors={"forced": "ok"}, model_version="adv11")
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
def test_adv11_registry_soft_without_found_must_not_become_negative(
    profile_status, expect_check_status, expect_outcome, expect_reason
):
    """
    Cycles 9–10: soft / unknown registry statuses pass through when
    ``found: True``. If the ``found`` key is absent, ``_registry_found(None)``
    short-circuits to CheckOutcome ``negative`` *before* the soft-status
    allowlist — so ``{\"status\": \"unavailable\"}`` becomes REGISTRY_NEGATIVE.

    Incomplete profiles (no presence flag) must not invent a hard credit denial;
    soft status must still map like the constructed CheckOutcome path.
    """
    key = f"adv11_reg_nofound_{profile_status}"
    # Deliberately omit ``found`` — only status (and optional error) present.
    REGISTRY[key] = {"status": profile_status, "error": "simulator"}
    try:
        with_found = run_registry_check
        baseline_key = f"adv11_reg_found_{profile_status}"
        REGISTRY[baseline_key] = {
            "found": True,
            "status": profile_status,
            "error": "simulator",
        }
        baseline = with_found(baseline_key, "SYN-ADV11-BASE")
        assert baseline.status == expect_check_status, (
            f"precondition: found=True + {profile_status!r} → "
            f"{expect_check_status!r}; got {baseline.status!r}"
        )

        outcome = run_registry_check(key, "SYN-ADV11-NOFOUND")
        assert outcome.status == expect_check_status, (
            f"registry profile status={profile_status!r} without found key must "
            f"yield {expect_check_status!r} (not invent negative); got "
            f"{outcome.status!r} payload={outcome.payload}"
        )

        decision = _decide(outcome)
        assert decision.outcome == expect_outcome, (
            f"soft registry {profile_status!r} without found must not be a credit "
            f"reject; expected {expect_outcome}, got {decision.outcome} "
            f"{decision.reason_codes}"
        )
        assert expect_reason in decision.reason_codes
        assert "REGISTRY_NEGATIVE" not in decision.reason_codes
    finally:
        REGISTRY.pop(key, None)
        REGISTRY.pop(f"adv11_reg_found_{profile_status}", None)


def test_adv11_registry_active_without_found_must_not_become_negative():
    """
    Profile ``{\"status\": \"active\"}`` with no ``found`` key is incomplete
    (contradictory / missing presence flag), not a confirmed company-not-found.
    Must degrade to missing_data / NEEDS_INFO, not REGISTRY_NEGATIVE.
    """
    key = "adv11_reg_active_nofound"
    REGISTRY[key] = {"status": "active"}
    try:
        outcome = run_registry_check(key, "SYN-ADV11-ACTIVE-NOFOUND")
        assert outcome.status == "missing_data", (
            f"active without found is incomplete profile → missing_data; "
            f"got {outcome.status!r} payload={outcome.payload}"
        )
        decision = _decide(outcome)
        assert decision.outcome == "NEEDS_INFO", (
            f"incomplete active profile must be NEEDS_INFO not credit reject; "
            f"got {decision.outcome} {decision.reason_codes}"
        )
        assert "REGISTRY_NEGATIVE" not in decision.reason_codes
    finally:
        REGISTRY.pop(key, None)
