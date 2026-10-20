"""Attack: score <= SCORE_REJECT_MAX still yields ALTERNATIVE when K_BORDER <= k < K_PASS."""

from synaptix_api.analytics.decision import (
    K_BORDER,
    K_PASS,
    SCORE_REJECT_MAX,
    _annuity_minor,
    apply_decision_rules,
    coverage_ratio,
)
from synaptix_api.analytics.mocks import run_bureau_check, run_registry_check
from synaptix_api.analytics.types import FinancialInput, RiskResult


def test_adv3_low_risk_score_must_not_get_alternative():
    """
    SCORE_REJECT_MAX is only AND-ed with k < K_BORDER. Border coverage
    (1.0 <= k < 1.3) plus score 20 therefore falls through to ALTERNATIVE —
    a hard risk fail still mints a counter-offer.
    """
    registry = run_registry_check("approval", "SYN-ADV3-RISK")
    bureau = run_bureau_check("approval")
    # Cashflow tuned so requested 5M/12m sits in the border-k band.
    finances = FinancialInput(
        revenue_minor=500_000_00,
        expenses_minor=0,
        liabilities_minor=50_000_00,
        amount_minor=5_000_000_00,
        term_months=12,
    )
    payment = _annuity_minor(finances.amount_minor, 0.16, finances.term_months)
    k = coverage_ratio(finances, new_payment_minor=payment)
    assert k is not None and K_BORDER <= k < K_PASS, f"fixture k out of band: {k}"

    risk = RiskResult(score=20, factors={"forced": "reject_band"}, model_version="adv3")
    assert risk.score <= SCORE_REJECT_MAX

    decision = apply_decision_rules(
        finances,
        risk,
        registry=registry,
        bureau=bureau,
        product_min_minor=500_000_00,
        product_max_minor=10_000_000_00,
        product_min_term=1,
        product_max_term=120,
    )

    assert decision.outcome not in ("ALTERNATIVE", "APPROVED"), (
        f"score={risk.score} <= {SCORE_REJECT_MAX} with border k={k} must not "
        f"offer credit; got {decision.outcome} {decision.reason_codes} "
        f"terms={decision.offered_terms}"
    )
