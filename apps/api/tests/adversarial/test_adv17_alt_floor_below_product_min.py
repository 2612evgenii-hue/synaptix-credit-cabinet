"""Attack: 10k RUB floor in max_principal_for_k drops alt below product_min → false REJECT."""

from synaptix_api.analytics.decision import (
    K_PASS,
    _annuity_minor,
    apply_decision_rules,
    max_principal_for_k,
)
from synaptix_api.analytics.types import CheckOutcome, FinancialInput, RiskResult


def _unfloored_max_principal(finances: FinancialInput, *, rate: float, term: int) -> int:
    """Same binary search as max_principal_for_k but without the 10_000_00 floor."""
    available = finances.available_cashflow_minor()
    assert available is not None
    max_pay = available / K_PASS
    lo, hi, best = 0, 10_000_000_00, 0
    while lo <= hi:
        mid = (lo + hi) // 2
        if _annuity_minor(mid, rate, term) <= max_pay:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return best


def test_adv17_floor_must_not_erase_in_band_alternative():
    """
    Invariant: if unrounded max principal at K_PASS is >= product_min and
    < requested amount, outcome must be ALTERNATIVE (affordable offer in band).

    max_principal_for_k silently floors to 10_000 RUB. When product_min is not
    on that grid (here 305_000_00), unfloored best can sit in-band while the
    floored value falls below product_min — apply_decision_rules then skips the
    alt branch and returns REJECTED / COVERAGE_OR_RISK_FAIL.
    """
    rate = 0.16
    term = 12
    # Cashflow tuned so unfloored best ∈ [305_000_00, 309_999_99]
    target = 305_000_00
    pay = _annuity_minor(target, rate, term)
    available = int(pay * K_PASS) + 100
    finances = FinancialInput(
        revenue_minor=available,
        expenses_minor=0,
        liabilities_minor=0,
        amount_minor=5_000_000_00,
        term_months=term,
    )
    product_min = 305_000_00
    unfloored = _unfloored_max_principal(finances, rate=rate, term=term)
    floored = max_principal_for_k(
        finances,
        annual_rate=rate,
        term_months=term,
        target_k=K_PASS,
        search_hi_minor=10_000_000_00,
    )
    assert unfloored >= product_min, "precondition: unfloored in product band"
    assert unfloored < finances.amount_minor
    assert floored < product_min, "precondition: floor drops below product_min"

    decision = apply_decision_rules(
        finances,
        RiskResult(score=50, factors={}, model_version="adv17"),
        registry=CheckOutcome("company_registry", "ok", "v", {}),
        bureau=CheckOutcome("credit_bureau", "ok", "v", {"overdue_days": 0}),
        product_min_minor=product_min,
        product_max_minor=10_000_000_00,
        product_min_term=6,
        product_max_term=60,
        demo_rate_annual=rate,
    )
    assert decision.outcome == "ALTERNATIVE", (
        f"in-band unfloored principal {unfloored} (floored={floored} < "
        f"product_min={product_min}) must still yield ALTERNATIVE; "
        f"got {decision.outcome} {decision.reason_codes}"
    )
    assert decision.offered_terms.get("amount_minor", 0) >= product_min
