"""Attack: border coverage (K_BORDER <= k < K_PASS) can still APPROVE with reason K_PASS."""

from synaptix_api.analytics.decision import (
    K_PASS,
    apply_decision_rules,
    coverage_ratio,
    max_principal_for_k,
    _annuity_minor,
)
from synaptix_api.analytics.mocks import run_bureau_check, run_registry_check
from synaptix_api.analytics.risk import assess_risk
from synaptix_api.analytics.types import FinancialInput

PRODUCT_MIN = 300_000_00
PRODUCT_MAX = 5_000_000_00


def test_adv_border_k_approves_with_fake_k_pass_reason():
    """
    When k is between K_BORDER and K_PASS and the alternative principal falls
    below product_min, apply_decision_rules falls through to APPROVED and even
    labels the decision K_PASS — violating the documented K_PASS=1.3 gate.
    """
    registry = run_registry_check("approval", "SYN-ADV")
    bureau = run_bureau_check("approval")

    amount = PRODUCT_MIN
    term = 12
    rate = 0.16
    payment = _annuity_minor(amount, rate, term)
    # Target k ≈ 1.1 (passes border, fails K_PASS)
    available = int(1.1 * payment)
    finances = FinancialInput(
        revenue_minor=available,
        expenses_minor=0,
        liabilities_minor=10_000_00,
        amount_minor=amount,
        term_months=term,
    )
    k = coverage_ratio(finances, new_payment_minor=payment)
    assert k is not None
    assert 1.0 <= k < K_PASS

    alt = max_principal_for_k(
        finances, annual_rate=rate, term_months=term, target_k=K_PASS
    )
    assert alt < PRODUCT_MIN  # alternative path skipped

    risk = assess_risk(finances, bureau=bureau, registry=registry)
    assert risk.score >= 55

    decision = apply_decision_rules(
        finances,
        risk,
        registry=registry,
        bureau=bureau,
        product_min_minor=PRODUCT_MIN,
        product_max_minor=PRODUCT_MAX,
        product_min_term=1,
        product_max_term=120,
        demo_rate_annual=rate,
    )

    # Banking invariant: must NOT approve at k < K_PASS with reason K_PASS
    assert decision.outcome != "APPROVED", (
        f"border k={k} incorrectly APPROVED; reasons={decision.reason_codes}"
    )
    assert "K_PASS" not in decision.reason_codes or decision.metrics.get("coverage_k", 0) >= K_PASS
