"""Attack: coverage_ratio round(..., 4) lifts true k < K_PASS → false APPROVED."""

from synaptix_api.analytics.decision import K_PASS, _annuity_minor, apply_decision_rules
from synaptix_api.analytics.types import CheckOutcome, FinancialInput, RiskResult


def test_adv18_rounded_k_must_not_approve_below_k_pass():
    """
    Invariant: APPROVED / K_PASS requires unrounded available/payment >= K_PASS.

    coverage_ratio returns round(available / denom, 4). apply_decision_rules then
    gates on that rounded value. Demo-scale cashflow can sit in
    [1.29995, 1.3) — true coverage fails K_PASS=1.3, but round lifts metrics
    coverage_k to 1.3 and the path returns APPROVED with reason K_PASS.
    """
    rate = 0.16
    term = 6
    amount = 300_000_00
    payment = _annuity_minor(amount, rate, term)
    # Tuned: true ratio ≈ 1.299950018 < 1.3; round(..., 4) == 1.3
    available = 6_806_420
    true_k = available / payment
    assert true_k < K_PASS, f"precondition: true k must fail gate, got {true_k}"
    assert round(true_k, 4) >= K_PASS, f"precondition: round must lift, got {round(true_k, 4)}"

    finances = FinancialInput(
        revenue_minor=available,
        expenses_minor=0,
        liabilities_minor=0,
        amount_minor=amount,
        term_months=term,
    )
    decision = apply_decision_rules(
        finances,
        RiskResult(score=70, factors={}, model_version="adv18"),
        registry=CheckOutcome("company_registry", "ok", "v", {}),
        bureau=CheckOutcome("credit_bureau", "ok", "v", {"overdue_days": 0}),
        product_min_minor=300_000_00,
        product_max_minor=5_000_000_00,
        product_min_term=6,
        product_max_term=36,
        demo_rate_annual=rate,
    )

    assert decision.outcome != "APPROVED", (
        f"true k={true_k} < K_PASS={K_PASS} but outcome=APPROVED "
        f"reasons={decision.reason_codes} metrics_k={decision.metrics.get('coverage_k')}"
    )
    assert "K_PASS" not in decision.reason_codes or (
        finances.available_cashflow_minor() / payment >= K_PASS
    )
