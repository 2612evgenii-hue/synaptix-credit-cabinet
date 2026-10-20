"""Attack: hard negative / overdue on one check softened by peer soft status."""

import pytest

from synaptix_api.analytics.decision import apply_decision_rules
from synaptix_api.analytics.types import CheckOutcome, FinancialInput, RiskResult


def _decide(*, registry: CheckOutcome, bureau: CheckOutcome):
    finances = FinancialInput(
        revenue_minor=900_000_00,
        expenses_minor=500_000_00,
        liabilities_minor=45_000_00,
        amount_minor=1_500_000_00,
        term_months=36,
    )
    risk = RiskResult(score=70, factors={"forced": "ok"}, model_version="adv8")
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
    "soft_status,soft_side",
    [
        ("unavailable", "registry"),
        ("missing_data", "registry"),
        ("pending", "registry"),
        ("unavailable", "bureau"),
        ("missing_data", "bureau"),
        ("pending", "bureau"),
    ],
)
def test_adv8_hard_negative_must_not_be_softened_by_peer_check(soft_status, soft_side):
    """
    Cycle 7: malformed overdue on the *same* bureau check must not mask
    status=negative into NEEDS_INFO.

    Cross-check hole: decision evaluates unavailable / missing_data / unknown
    *before* REGISTRY_NEGATIVE / BUREAU_NEGATIVE. A liquidating registry or
    negative bureau is therefore rewritten as CHECK_UNAVAILABLE / NEEDS_INFO
    whenever the peer check is soft: credit denial becomes a retry/info path.
    """
    if soft_side == "registry":
        # Peer soft, bureau already known-negative
        baseline_reg = CheckOutcome("company_registry", "ok", "adv8", {})
        baseline_bur = CheckOutcome(
            "credit_bureau", "negative", "adv8", {"overdue_days": 90}
        )
        soft_reg = CheckOutcome("company_registry", soft_status, "adv8", {})
        soft_bur = baseline_bur
        expect_reason = "BUREAU_NEGATIVE"
    else:
        # Peer soft, registry already known-negative
        baseline_reg = CheckOutcome(
            "company_registry", "negative", "adv8", {"status": "liquidating"}
        )
        baseline_bur = CheckOutcome(
            "credit_bureau", "ok", "adv8", {"overdue_days": 0}
        )
        soft_reg = baseline_reg
        soft_bur = CheckOutcome("credit_bureau", soft_status, "adv8", {})
        expect_reason = "REGISTRY_NEGATIVE"

    clean = _decide(registry=baseline_reg, bureau=baseline_bur)
    assert clean.outcome == "REJECTED", (
        f"precondition: hard negative alone must reject; got "
        f"{clean.outcome} {clean.reason_codes}"
    )
    assert expect_reason in clean.reason_codes

    decision = _decide(registry=soft_reg, bureau=soft_bur)
    assert decision.outcome == "REJECTED", (
        f"hard {expect_reason} must stay REJECTED when peer check is "
        f"{soft_status!r}; got {decision.outcome} {decision.reason_codes} "
        f"(soft peer status must not mask an explicit negative verdict)"
    )


def test_adv8_bureau_overdue_must_not_be_masked_by_registry_unavailable():
    """
    status=ok with overdue_days>0 is a hard BUREAU_OVERDUE reject (cycle 1).
    Registry unavailable is evaluated earlier and rewrites the outcome to
    CHECK_UNAVAILABLE: overdue debt becomes a technical retry.
    """
    bureau_overdue = CheckOutcome(
        "credit_bureau", "ok", "adv8", {"overdue_days": 90}
    )
    clean = _decide(
        registry=CheckOutcome("company_registry", "ok", "adv8", {}),
        bureau=bureau_overdue,
    )
    assert clean.outcome == "REJECTED"
    assert "BUREAU_OVERDUE" in clean.reason_codes

    decision = _decide(
        registry=CheckOutcome("company_registry", "unavailable", "adv8", {}),
        bureau=bureau_overdue,
    )
    assert decision.outcome == "REJECTED", (
        f"BUREAU_OVERDUE must stay REJECTED when registry is unavailable; "
        f"got {decision.outcome} {decision.reason_codes}"
    )
    assert "BUREAU_OVERDUE" in decision.reason_codes
