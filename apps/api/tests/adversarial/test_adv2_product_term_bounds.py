"""Attack: term outside product min/max still APPROVED — ProductLimits ignore terms."""

from synaptix_api.analytics.decision import apply_decision_rules
from synaptix_api.analytics.mocks import run_bureau_check, run_registry_check
from synaptix_api.analytics.pipeline import ProductLimits
from synaptix_api.analytics.risk import assess_risk
from synaptix_api.analytics.types import FinancialInput

# Mirrors seeded equipment amount band but term=3 is below equipment min_term=12
PRODUCT_MIN = 500_000_00
PRODUCT_MAX = 10_000_000_00
PRODUCT_MIN_TERM = 12
PRODUCT_MAX_TERM = 60


def test_adv2_term_below_product_min_must_not_approve():
    """
    Product entity has min/max_term_months; apply_decision_rules / ProductLimits
    only gate amount. term_months=3 with min_term=12 must not APPROVE.
    """
    finances = FinancialInput(
        revenue_minor=900_000_00,
        expenses_minor=100_000_00,
        liabilities_minor=10_000_00,
        amount_minor=500_000_00,
        term_months=3,
    )
    assert not (PRODUCT_MIN_TERM <= finances.term_months <= PRODUCT_MAX_TERM)

    registry = run_registry_check("approval", "SYN-ADV2")
    bureau = run_bureau_check("approval")
    risk = assess_risk(finances, bureau=bureau, registry=registry)
    decision = apply_decision_rules(
        finances,
        risk,
        registry=registry,
        bureau=bureau,
        product_min_minor=PRODUCT_MIN,
        product_max_minor=PRODUCT_MAX,
        product_min_term=PRODUCT_MIN_TERM,
        product_max_term=PRODUCT_MAX_TERM,
    )

    assert decision.outcome != "APPROVED", (
        f"term={finances.term_months} outside [{PRODUCT_MIN_TERM},{PRODUCT_MAX_TERM}] "
        f"but outcome={decision.outcome} reasons={decision.reason_codes}"
    )
    assert "PRODUCT_LIMIT" in decision.reason_codes or decision.outcome == "REJECTED"


def test_adv2_pipeline_product_limits_omit_term_fields():
    """ProductLimits dataclass carries no term bounds — structural gap."""
    product = ProductLimits(min_amount_minor=PRODUCT_MIN, max_amount_minor=PRODUCT_MAX)
    assert hasattr(product, "min_term_months") and hasattr(product, "max_term_months"), (
        f"ProductLimits fields={getattr(product, '__dataclass_fields__', {})} "
        "lack min/max_term_months — pipeline cannot enforce product term band"
    )
