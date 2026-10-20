"""Attack: NaN / Inf / overflow demo_rate_annual crashes decision instead of reject."""

import math

import pytest

from synaptix_api.analytics.decision import apply_decision_rules
from synaptix_api.analytics.mocks import run_bureau_check, run_registry_check
from synaptix_api.analytics.types import FinancialInput, RiskResult


def _decide(rate: float):
    finances = FinancialInput(
        revenue_minor=900_000_00,
        expenses_minor=500_000_00,
        liabilities_minor=45_000_00,
        amount_minor=1_500_000_00,
        term_months=36,
    )
    registry = run_registry_check("approval", "SYN-ADV4-RATE")
    bureau = run_bureau_check("approval")
    risk = RiskResult(score=70, factors={"forced": "ok"}, model_version="adv4")
    return apply_decision_rules(
        finances,
        risk,
        registry=registry,
        bureau=bureau,
        product_min_minor=500_000_00,
        product_max_minor=10_000_000_00,
        product_min_term=1,
        product_max_term=120,
        demo_rate_annual=rate,
    )


@pytest.mark.parametrize(
    "rate",
    [float("nan"), float("inf"), 1e308],
    ids=["nan", "inf", "overflow"],
)
def test_adv4_non_finite_rate_must_not_crash(rate: float):
    """
    Cycle 3 rejects demo_rate_annual < 0. Non-finite / extreme positive rates
    still reach _annuity_minor and raise ValueError / OverflowError — decision
    engine must return a DecisionResult, not dump the request.
    """
    try:
        decision = _decide(rate)
    except (ValueError, OverflowError, ArithmeticError) as exc:
        pytest.fail(
            f"demo_rate_annual={rate!r} crashed apply_decision_rules with "
            f"{type(exc).__name__}: {exc} — must reject/guard like INVALID_RATE"
        )

    assert decision.outcome != "APPROVED", (
        f"non-finite/extreme rate must not approve; got {decision.outcome} "
        f"terms={decision.offered_terms} k={decision.metrics.get('coverage_k')}"
    )
    offered = decision.offered_terms.get("rate_annual")
    if offered is not None:
        assert math.isfinite(offered) and offered >= 0, (
            f"offered non-finite/negative rate_annual={offered}"
        )
