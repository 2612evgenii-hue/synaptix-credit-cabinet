"""Attack: max_principal_for_k hard-caps search at 50M RUB below affordable principal."""

from synaptix_api.analytics.decision import (
    K_PASS,
    _annuity_minor,
    coverage_ratio,
    max_principal_for_k,
)
from synaptix_api.analytics.types import FinancialInput

# Explicit product band above the binary-search hi=50_000_000_00 (50M RUB)
PRODUCT_MAX = 100_000_000_00  # 100M RUB
SEARCH_HI = 50_000_000_00


def test_adv2_max_principal_cap_below_affordable_and_product_max():
    """
    With cashflow that supports >50M RUB at K_PASS and product_max=100M,
    max_principal_for_k still returns at most SEARCH_HI — silent under-offer.
    """
    rate = 0.16
    term = 60
    # Cashflow sized so 60M RUB annuity still has k >= K_PASS
    probe_principal = 60_000_000_00
    pay = _annuity_minor(probe_principal, rate, term)
    available = int(K_PASS * pay) + 1_000_00
    finances = FinancialInput(
        revenue_minor=available,
        expenses_minor=0,
        liabilities_minor=0,
        amount_minor=PRODUCT_MAX,
        term_months=term,
    )
    k_at_60m = coverage_ratio(finances, new_payment_minor=pay)
    assert k_at_60m is not None and k_at_60m >= K_PASS

    alt = max_principal_for_k(
        finances,
        annual_rate=rate,
        term_months=term,
        target_k=K_PASS,
    )

    assert alt > SEARCH_HI, (
        f"max_principal capped at {alt} (hi={SEARCH_HI}) while cashflow supports "
        f">={probe_principal} (k_at_60m={k_at_60m}) and product_max={PRODUCT_MAX}"
    )
    assert alt <= PRODUCT_MAX
