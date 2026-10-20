"""Attack: negative / fractional overdue_days treated as clean bureau → APPROVE."""

from synaptix_api.analytics.decision import apply_decision_rules
from synaptix_api.analytics.mocks import run_registry_check
from synaptix_api.analytics.types import CheckOutcome, FinancialInput, RiskResult


def _strong_finances() -> FinancialInput:
    return FinancialInput(
        revenue_minor=300_000_000,
        expenses_minor=50_000_000,
        liabilities_minor=10_000_000,
        amount_minor=500_000_00,
        term_months=12,
    )


def _decide(bureau: CheckOutcome):
    finances = _strong_finances()
    registry = run_registry_check("approval", "SYN-ADV6-OD")
    risk = RiskResult(score=70, factors={"forced": "ok"}, model_version="adv6")
    return apply_decision_rules(
        finances,
        risk,
        registry=registry,
        bureau=bureau,
        product_min_minor=300_000_00,
        product_max_minor=5_000_000_00,
        product_min_term=6,
        product_max_term=36,
    )


def test_adv6_negative_overdue_must_not_approve():
    """
    Cycle 1 rejects overdue_days > 0; cycle 5 maps non-int overdue to NEEDS_INFO.
    overdue_days=-5 is a valid int so it passes both gates (only `> 0` checked)
    and still APPROVES as a clean bureau — corrupt/negative obligation smuggle.
    """
    bureau = CheckOutcome(
        source="credit_bureau",
        status="ok",
        mock_version="adv6",
        payload={"overdue_days": -5},
    )
    decision = _decide(bureau)
    assert decision.outcome != "APPROVED", (
        f"negative overdue_days must not approve; got {decision.outcome} "
        f"{decision.reason_codes} metrics={decision.metrics}"
    )


def test_adv6_fractional_overdue_truncated_must_not_approve():
    """
    int(0.9) == 0, so fractional overdue in (0, 1) is truncated to 'clean' and
    APPROVES — silent under-count of bureau debt days.
    """
    bureau = CheckOutcome(
        source="credit_bureau",
        status="ok",
        mock_version="adv6",
        payload={"overdue_days": 0.9},
    )
    decision = _decide(bureau)
    assert decision.outcome != "APPROVED", (
        f"fractional overdue_days=0.9 must not approve as clean; got "
        f"{decision.outcome} {decision.reason_codes}"
    )
