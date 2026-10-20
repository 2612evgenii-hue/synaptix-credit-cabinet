from synaptix_api.analytics.decision import apply_decision_rules, coverage_ratio
from synaptix_api.analytics.mocks import run_bureau_check, run_registry_check
from synaptix_api.analytics.pipeline import ProductLimits, run_analytics
from synaptix_api.analytics.risk import assess_risk
from synaptix_api.analytics.types import FinancialInput


PRODUCT = ProductLimits(min_amount_minor=500_000_00, max_amount_minor=10_000_000_00)


def _fin(**kwargs):
    base = dict(
        revenue_minor=900_000_00,
        expenses_minor=500_000_00,
        liabilities_minor=45_000_00,
        amount_minor=1_500_000_00,
        term_months=36,
    )
    base.update(kwargs)
    return FinancialInput(**base)


def test_approval_scenario_pipeline():
    bundle = run_analytics(
        scenario_key="approval",
        registration_id="SYN-APPROVAL",
        finances=_fin(),
        product=PRODUCT,
    )
    assert bundle.decision.outcome == "APPROVED"
    assert "K_PASS" in bundle.decision.reason_codes
    assert bundle.risk.score >= 55


def test_rejection_overdue():
    bundle = run_analytics(
        scenario_key="rejection",
        registration_id="SYN-REJECTION",
        finances=_fin(revenue_minor=600_000_00, expenses_minor=550_000_00, liabilities_minor=150_000_000),
        product=PRODUCT,
    )
    assert bundle.decision.outcome == "REJECTED"
    # rejection mock is status=negative (and overdue>0); explicit negative wins
    assert set(bundle.decision.reason_codes) & {"BUREAU_NEGATIVE", "BUREAU_OVERDUE"}


def test_needs_info_when_revenue_missing():
    bundle = run_analytics(
        scenario_key="clarification",
        registration_id="SYN-CLARIFICATION",
        finances=_fin(revenue_minor=None),
        product=PRODUCT,
    )
    assert bundle.decision.outcome == "NEEDS_INFO"
    assert "INCOMPLETE_FINANCIALS" in bundle.decision.reason_codes


def test_bureau_unavailable_is_not_reject():
    bundle = run_analytics(
        scenario_key="approval",
        registration_id="SYN-APPROVAL",
        finances=_fin(),
        product=PRODUCT,
        force_bureau_unavailable=True,
    )
    assert bundle.decision.outcome == "CHECK_UNAVAILABLE"
    assert bundle.decision.outcome != "REJECTED"


def test_product_limit_reject():
    fin = _fin(amount_minor=100_00)
    registry = run_registry_check("approval", "x")
    bureau = run_bureau_check("approval")
    risk = assess_risk(fin, bureau=bureau, registry=registry)
    decision = apply_decision_rules(
        fin,
        risk,
        registry=registry,
        bureau=bureau,
        product_min_minor=PRODUCT.min_amount_minor,
        product_max_minor=PRODUCT.max_amount_minor,
        product_min_term=1,
        product_max_term=120,
    )
    assert decision.outcome == "REJECTED"
    assert "PRODUCT_LIMIT" in decision.reason_codes


def test_coverage_none_when_missing():
    fin = FinancialInput(None, None, None, 1_000_000_00, 12)
    assert coverage_ratio(fin, new_payment_minor=10_000_00) is None


def test_alternative_when_amount_too_high_for_k():
    # High request, modest cashflow -> alternative or reject, not silent approve
    bundle = run_analytics(
        scenario_key="approval",
        registration_id="SYN-APPROVAL",
        finances=_fin(
            revenue_minor=220_000_00,
            expenses_minor=0,
            liabilities_minor=50_000_00,
            amount_minor=5_000_000_00,
            term_months=12,
        ),
        product=PRODUCT,
    )
    assert bundle.decision.outcome in ("ALTERNATIVE", "REJECTED")
    if bundle.decision.outcome == "ALTERNATIVE":
        assert bundle.decision.offered_terms["amount_minor"] < 5_000_000_00
