"""Attack: bureau status=negative + malformed overdue → NEEDS_INFO instead of REJECT."""

from synaptix_api.analytics.decision import apply_decision_rules
from synaptix_api.analytics.mocks import run_registry_check
from synaptix_api.analytics.types import CheckOutcome, FinancialInput, RiskResult


def _decide(bureau: CheckOutcome):
    finances = FinancialInput(
        revenue_minor=900_000_00,
        expenses_minor=500_000_00,
        liabilities_minor=45_000_00,
        amount_minor=1_500_000_00,
        term_months=36,
    )
    registry = run_registry_check("approval", "SYN-ADV7-NEG")
    risk = RiskResult(score=70, factors={"forced": "ok"}, model_version="adv7")
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


def test_adv7_negative_bureau_must_reject_despite_malformed_overdue():
    """
    Cycle 5 maps overdue_days='nope' on status=ok to NEEDS_INFO (no crash).
    Cycle 6 closed negative/fractional overdue on status=ok.

    When status is already explicit ``negative``, malformed overdue is parsed
    *before* the negative/overdue reject branch — outcome becomes NEEDS_INFO /
    MALFORMED_BUREAU_PAYLOAD instead of REJECTED. A known-negative bureau file
    is softened into an info request.
    """
    clean = _decide(
        CheckOutcome(
            source="credit_bureau",
            status="negative",
            mock_version="adv7",
            payload={"overdue_days": 0},
        )
    )
    assert clean.outcome == "REJECTED", (
        f"precondition: negative+clean overdue must reject; got "
        f"{clean.outcome} {clean.reason_codes}"
    )

    decision = _decide(
        CheckOutcome(
            source="credit_bureau",
            status="negative",
            mock_version="adv7",
            payload={"overdue_days": "nope"},
        )
    )
    assert decision.outcome == "REJECTED", (
        f"bureau status=negative must still REJECT when overdue_days is "
        f"malformed; got {decision.outcome} {decision.reason_codes} "
        f"(malformed overdue must not mask an explicit negative verdict)"
    )
