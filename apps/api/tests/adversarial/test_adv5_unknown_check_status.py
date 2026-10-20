"""Attack: non-canonical check status falls through to APPROVED + CHECKS_OK."""

from synaptix_api.analytics.decision import apply_decision_rules
from synaptix_api.analytics.mocks import BUREAU, run_bureau_check, run_registry_check
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


def test_adv5_unknown_bureau_status_must_not_approve_as_checks_ok():
    """
    Cycle 1 closed missing_data / unavailable / negative. Any other status
    (e.g. pending) is treated as success: risk labels bureau ok, decision emits
    CHECKS_OK and can APPROVE. Mocks also pass profile['status'] through without
    an allowlist — same hole.
    """
    finances = _strong_finances()
    registry = run_registry_check("approval", "SYN-ADV5-STATUS")
    bureau = CheckOutcome(
        source="credit_bureau",
        status="pending",  # type: ignore[arg-type]
        mock_version="adv5",
        payload={"overdue_days": 0},
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
        f"unknown bureau status approved: {decision.outcome} {decision.reason_codes} "
        f"risk_bureau={risk.factors.get('bureau')}"
    )
    assert "CHECKS_OK" not in decision.reason_codes


def test_adv5_mock_bureau_passthrough_unknown_status_must_not_approve(monkeypatch):
    """BUREAU profile status is copied into CheckOutcome with no allowlist."""
    monkeypatch.setitem(
        BUREAU,
        "approval",
        {"status": "pending", "overdue_days": 0, "obligations": 1},
    )
    finances = _strong_finances()
    registry = run_registry_check("approval", "SYN-ADV5-MOCK")
    bureau = run_bureau_check("approval")
    assert bureau.status == "pending"
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
        f"mock-passthrough status={bureau.status!r} approved with {decision.reason_codes}"
    )
    assert "CHECKS_OK" not in decision.reason_codes
